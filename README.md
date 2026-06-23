# Simple AI Parser

This repository contains a small, dependency-free "AI-style" parser that turns a
short natural-language message into structured data.

It can:

- classify a message intent, such as `customer_support`, `schedule_meeting`, or
  `sales_lead`
- extract useful entities like email addresses, phone numbers, dates, money, and
  order IDs
- return keywords and an explanation showing why the parser chose an intent
- parse a UTF-8 text or Markdown document from a file
- parse a PDF through a drag-and-drop browser website
- run as either a Python library or a command-line tool

## Where the code is

- Parser library and CLI: [`ai_parser.py`](./ai_parser.py)
- PDF drag-and-drop website: [`index.html`](./index.html)
- Website behavior: [`app.js`](./app.js)
- Website styles: [`styles.css`](./styles.css)
- Tests: [`test_ai_parser.py`](./test_ai_parser.py)
- Usage guide: this README

## Use the PDF website

Open `index.html` in a browser, then drag a PDF onto the upload area.

The website:

1. reads the PDF locally in your browser with PDF.js
2. extracts text from each page
3. runs the parser on the full extracted text
4. splits the text into paragraph-like chunks and parses each chunk
5. shows intent, confidence, entities, keywords, chunks, and a text preview

Your PDF is not uploaded by this demo. It stays in the browser. The page loads
PDF.js from a CDN, so you need an internet connection the first time you open it.

Limitations:

- works best with PDFs that already contain selectable text
- scanned image PDFs need OCR first
- encrypted or password-protected PDFs may not parse

## Quick start

Run the parser from the command line:

```bash
python3 ai_parser.py "Please help with broken order ABCD-1234. Email me at sam@example.com" --pretty
```

Abbreviated example output:

```json
{
  "original_text": "Please help with broken order ABCD-1234. Email me at sam@example.com",
  "normalized_text": "please help with broken order abcd-1234. email me at sam@example.com",
  "intent": "customer_support",
  "confidence": 0.25,
  "entities": {
    "emails": ["sam@example.com"],
    "phones": [],
    "dates": [],
    "money": [],
    "order_ids": ["ABCD-1234"]
  },
  "keywords": ["help", "broken", "order", "abcd", "1234", "email", "sam", "example", "com"],
  "explanation": "Matched intent 'customer_support' because the message contained these keywords: broken, help.",
  "intent_scores": [
    {
      "intent": "customer_support",
      "score": 0.25,
      "matched_keywords": ["broken", "help"]
    }
  ]
}
```

The full output includes a score entry for every configured intent.

## Parse a document

Put your document in a UTF-8 text file, for example `sample.md`:

```markdown
Please help with broken order ABCD-1234.

Schedule a meeting on 2026-06-19 with alex@example.com.
```

Then run:

```bash
python3 ai_parser.py --file sample.md --pretty
```

Document output includes:

- `source`: the file path that was parsed
- `document_stats`: character, word, line, and chunk counts
- `overall`: one parse result for the whole document
- `chunks`: parse results for each paragraph-like block separated by blank lines

The command-line file parser supports plain UTF-8 text, including `.txt` and
`.md`. Use the browser website above for PDFs. For scanned PDFs, Word documents,
or images, first extract/OCR the text and then parse that text.

You can also import it:

```python
from ai_parser import parse, parse_document_file

result = parse("Schedule a meeting on 2026-06-19 with alex@example.com")
print(result.intent)
print(result.entities)

document_result = parse_document_file("sample.md")
print(document_result.overall.intent)
print(document_result.document_stats)
```

## How it works

The parser uses a transparent pipeline:

1. **Normalize text**: lowercases the message and collapses extra spaces.
2. **Tokenize**: splits the normalized message into word-like tokens.
3. **Extract entities**: uses regular expressions to find common structured
   values such as emails, phone numbers, dates, money amounts, and order IDs.
4. **Score intents**: compares tokens with intent keyword sets. Each intent gets
   a score based on how many of its keywords appear in the message.
5. **Pick the best intent**: returns the highest-scoring intent. If no intent
   keywords match, it returns `unknown`.
6. **Split documents**: for file input, splits the document into paragraph-like
   chunks and parses each chunk separately.
7. **Explain the result**: includes the matched keywords so the decision is easy
   to inspect.

This is not a large language model. It is a simple explainable parser that uses
AI-inspired natural-language processing steps. It is useful for demos,
prototypes, and small routing workflows where predictable behavior matters.

## Run tests

```bash
python3 -m unittest
```
