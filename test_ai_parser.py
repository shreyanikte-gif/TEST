import unittest

from ai_parser import parse


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


if __name__ == "__main__":
    unittest.main()
