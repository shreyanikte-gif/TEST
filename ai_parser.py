"""A small, explainable AI-style parser for short user messages.

The parser is intentionally dependency-free. It combines simple NLP building
blocks--normalization, tokenization, regex entity extraction, and keyword-based
intent scoring--to turn natural language into structured JSON-friendly data.
"""

from __future__ import annotations

import argparse
import json
import re
import string
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}\b")
PHONE_RE = re.compile(
    r"""
    (?:
        \+?\d{1,3}[\s.-]?
    )?
    (?:
        \(?\d{3}\)?[\s.-]?
    )
    \d{3}[\s.-]?\d{4}
    """,
    re.VERBOSE,
)
DATE_RE = re.compile(
    r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b"
)
MONEY_RE = re.compile(r"(?:\$|usd\s*)\d+(?:,\d{3})*(?:\.\d{2})?", re.IGNORECASE)
ORDER_RE = re.compile(r"\b(?:order|ticket|case)[\s#:.-]*([a-z0-9-]{4,})\b", re.IGNORECASE)


INTENT_KEYWORDS: dict[str, set[str]] = {
    "book_travel": {
        "book",
        "flight",
        "hotel",
        "travel",
        "trip",
        "reservation",
        "reserve",
        "airport",
    },
    "cancel_order": {
        "cancel",
        "refund",
        "return",
        "stop",
        "void",
        "order",
        "purchase",
    },
    "customer_support": {
        "help",
        "support",
        "problem",
        "issue",
        "broken",
        "error",
        "ticket",
        "case",
    },
    "schedule_meeting": {
        "schedule",
        "meeting",
        "call",
        "calendar",
        "appointment",
        "invite",
        "sync",
    },
    "sales_lead": {
        "pricing",
        "quote",
        "demo",
        "buy",
        "purchase",
        "sales",
        "interested",
        "plan",
    },
}

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "at",
    "for",
    "from",
    "i",
    "in",
    "is",
    "me",
    "my",
    "of",
    "on",
    "please",
    "the",
    "to",
    "we",
    "with",
}


@dataclass(frozen=True)
class IntentScore:
    """Score details for a candidate intent."""

    intent: str
    score: float
    matched_keywords: list[str]


@dataclass(frozen=True)
class ParseResult:
    """Structured parser output."""

    original_text: str
    normalized_text: str
    intent: str
    confidence: float
    entities: dict[str, list[str]]
    keywords: list[str]
    explanation: str
    intent_scores: list[IntentScore]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation of the parse result."""

        return asdict(self)


@dataclass(frozen=True)
class DocumentChunk:
    """Structured output for one document paragraph or block."""

    chunk_number: int
    text: str
    intent: str
    confidence: float
    entities: dict[str, list[str]]
    keywords: list[str]
    explanation: str


@dataclass(frozen=True)
class DocumentParseResult:
    """Structured parser output for a document file or document-sized string."""

    source: str | None
    document_stats: dict[str, int]
    overall: ParseResult
    chunks: list[DocumentChunk]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation of the document result."""

        return asdict(self)


def normalize(text: str) -> str:
    """Lowercase text and collapse extra whitespace."""

    return " ".join(text.lower().strip().split())


def tokenize(text: str) -> list[str]:
    """Split normalized text into lightweight word tokens."""

    translator = str.maketrans({char: " " for char in string.punctuation})
    return [token for token in text.translate(translator).split() if token]


def extract_keywords(tokens: Iterable[str]) -> list[str]:
    """Keep informative tokens that are not common stop words."""

    seen: set[str] = set()
    keywords: list[str] = []
    for token in tokens:
        if token in STOP_WORDS or token in seen:
            continue
        seen.add(token)
        keywords.append(token)
    return keywords


def extract_entities(text: str) -> dict[str, list[str]]:
    """Extract common entities from the original message."""

    return {
        "emails": EMAIL_RE.findall(text),
        "phones": [match.group(0).strip() for match in PHONE_RE.finditer(text)],
        "dates": DATE_RE.findall(text),
        "money": MONEY_RE.findall(text),
        "order_ids": [match.group(1) for match in ORDER_RE.finditer(text)],
    }


def score_intents(tokens: Iterable[str]) -> list[IntentScore]:
    """Rank intents by the fraction of configured keywords present."""

    token_set = set(tokens)
    scores: list[IntentScore] = []
    for intent, keywords in INTENT_KEYWORDS.items():
        matched = sorted(token_set & keywords)
        score = len(matched) / len(keywords)
        scores.append(IntentScore(intent=intent, score=round(score, 3), matched_keywords=matched))
    return sorted(scores, key=lambda item: item.score, reverse=True)


def parse(text: str) -> ParseResult:
    """Parse a user message into intent, entities, keywords, and explanation."""

    if not text or not text.strip():
        raise ValueError("text must contain at least one non-whitespace character")

    normalized_text = normalize(text)
    tokens = tokenize(normalized_text)
    keywords = extract_keywords(tokens)
    entities = extract_entities(text)
    intent_scores = score_intents(tokens)
    best = intent_scores[0]

    if best.score == 0:
        intent = "unknown"
        confidence = 0.0
        explanation = "No configured intent keywords were found, so the parser returned unknown."
    else:
        intent = best.intent
        confidence = best.score
        matched = ", ".join(best.matched_keywords)
        explanation = (
            f"Matched intent '{intent}' because the message contained "
            f"these keywords: {matched}."
        )

    return ParseResult(
        original_text=text,
        normalized_text=normalized_text,
        intent=intent,
        confidence=confidence,
        entities=entities,
        keywords=keywords,
        explanation=explanation,
        intent_scores=intent_scores,
    )


def split_document(text: str) -> list[str]:
    """Split a document into non-empty paragraph-like chunks."""

    chunks = [chunk.strip() for chunk in re.split(r"\n\s*\n", text) if chunk.strip()]
    if chunks:
        return chunks
    stripped = text.strip()
    return [stripped] if stripped else []


def document_stats(text: str) -> dict[str, int]:
    """Return basic document size metrics."""

    return {
        "characters": len(text),
        "words": len(tokenize(normalize(text))),
        "lines": len(text.splitlines()),
        "chunks": len(split_document(text)),
    }


def parse_document(text: str, source: str | None = None) -> DocumentParseResult:
    """Parse a larger text document and each paragraph-like chunk."""

    overall = parse(text)
    chunks: list[DocumentChunk] = []
    for index, chunk_text in enumerate(split_document(text), start=1):
        parsed_chunk = parse(chunk_text)
        chunks.append(
            DocumentChunk(
                chunk_number=index,
                text=chunk_text,
                intent=parsed_chunk.intent,
                confidence=parsed_chunk.confidence,
                entities=parsed_chunk.entities,
                keywords=parsed_chunk.keywords,
                explanation=parsed_chunk.explanation,
            )
        )

    return DocumentParseResult(
        source=source,
        document_stats=document_stats(text),
        overall=overall,
        chunks=chunks,
    )


def parse_document_file(path: str | Path) -> DocumentParseResult:
    """Read a UTF-8 text document from disk and parse it."""

    document_path = Path(path)
    text = document_path.read_text(encoding="utf-8")
    return parse_document(text, source=str(document_path))


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""

    parser = argparse.ArgumentParser(description="Parse text or a UTF-8 document into structured data.")
    parser.add_argument("text", nargs="?", help="Text message to parse")
    parser.add_argument(
        "--file",
        help="Path to a UTF-8 text or Markdown document to parse",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Print indented JSON output",
    )
    return parser


def main() -> None:
    """CLI entry point."""

    parser = build_arg_parser()
    args = parser.parse_args()
    if args.file and args.text:
        parser.error("provide either text or --file, not both")
    if not args.file and not args.text:
        parser.error("provide text or --file PATH")

    result = parse_document_file(args.file) if args.file else parse(args.text)
    indent = 2 if args.pretty else None
    print(json.dumps(result.to_dict(), indent=indent))


if __name__ == "__main__":
    main()
