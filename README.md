# Simple AI Parser

This repository contains a small, dependency-free "AI-style" parser that turns a
short natural-language message into structured data.

It can:

- classify a message intent, such as `customer_support`, `schedule_meeting`, or
  `sales_lead`
- extract useful entities like email addresses, phone numbers, dates, money, and
  order IDs
- return keywords and an explanation showing why the parser chose an intent
- run as either a Python library or a command-line tool

## Quick start

Run the parser from the command line:

```bash
python ai_parser.py "Please help with broken order ABCD-1234. Email me at sam@example.com" --pretty
```

Abbreviated example output:

```json
{
  "original_text": "Please help with broken order ABCD-1234. Email me at sam@example.com",
  "normalized_text": "please help with broken order abcd-1234. email me at sam@example.com",
  "intent": "customer_support",
  "confidence": 0.429,
  "entities": {
    "emails": ["sam@example.com"],
    "phones": [],
    "dates": [],
    "money": [],
    "order_ids": ["ABCD-1234"]
  },
  "keywords": ["help", "broken", "order", "abcd", "1234", "email", "sam", "example", "com"],
  "explanation": "Matched intent 'customer_support' because the message contained these keywords: broken, help, order.",
  "intent_scores": [
    {
      "intent": "customer_support",
      "score": 0.429,
      "matched_keywords": ["broken", "help", "order"]
    }
  ]
}
```

The full output includes a score entry for every configured intent.

You can also import it:

```python
from ai_parser import parse

result = parse("Schedule a meeting on 2026-06-19 with alex@example.com")
print(result.intent)
print(result.entities)
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
6. **Explain the result**: includes the matched keywords so the decision is easy
   to inspect.

This is not a large language model. It is a simple explainable parser that uses
AI-inspired natural-language processing steps. It is useful for demos,
prototypes, and small routing workflows where predictable behavior matters.

## Run tests

```bash
python -m unittest
```
