import tempfile
import unittest
from pathlib import Path

from ai_parser import parse, parse_document, parse_document_file


class AIParserTests(unittest.TestCase):
    def test_detects_customer_support_intent_and_entities(self):
        result = parse(
            "Please help with broken order ABCD-1234. "
            "Email me at sam@example.com or call (555) 123-4567."
        )

        self.assertEqual(result.intent, "customer_support")
        self.assertGreater(result.confidence, 0)
        self.assertIn("sam@example.com", result.entities["emails"])
        self.assertIn("(555) 123-4567", result.entities["phones"])
        self.assertIn("ABCD-1234", result.entities["order_ids"])

    def test_detects_schedule_meeting_intent(self):
        result = parse("Schedule a meeting on 2026-06-19 to discuss pricing.")

        self.assertEqual(result.intent, "schedule_meeting")
        self.assertIn("2026-06-19", result.entities["dates"])
        self.assertIn("schedule", result.keywords)

    def test_returns_unknown_for_unmatched_text(self):
        result = parse("The blue notebook sits near the window.")

        self.assertEqual(result.intent, "unknown")
        self.assertEqual(result.confidence, 0.0)

    def test_rejects_empty_text(self):
        with self.assertRaises(ValueError):
            parse("   ")

    def test_parses_document_into_overall_result_and_chunks(self):
        result = parse_document(
            "Please help with broken order ABCD-1234.\n\n"
            "Schedule a meeting on 2026-06-19."
        )

        self.assertEqual(result.document_stats["chunks"], 2)
        self.assertEqual(result.chunks[0].intent, "customer_support")
        self.assertEqual(result.chunks[1].intent, "schedule_meeting")
        self.assertIn("ABCD-1234", result.overall.entities["order_ids"])

    def test_parses_document_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            document_path = Path(temp_dir) / "sample.md"
            document_path.write_text("I want a demo and pricing quote.", encoding="utf-8")

            result = parse_document_file(document_path)

        self.assertEqual(result.source, str(document_path))
        self.assertEqual(result.overall.intent, "sales_lead")


if __name__ == "__main__":
    unittest.main()
