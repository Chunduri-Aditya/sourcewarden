from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from web.services.rag import get_planning_context


class RagServiceTests(unittest.TestCase):
    def test_empty_query_returns_typed_result_without_raising(self) -> None:
        result = get_planning_context("   ")
        self.assertEqual(result["status"], "invalid_query")
        self.assertIn("error", result)
        self.assertEqual(result["evidence"], [])

    def test_real_query_returns_grounded_evidence(self) -> None:
        # Real indexes exist on disk at n8n_rag_system/data/indexes/, so a
        # concrete n8n question must come back "ready" with real citations,
        # not just the empty/no-evidence path.
        result = get_planning_context("How do I configure the HTTP Request node?", top_k=3)
        self.assertEqual(result["status"], "ready")
        self.assertTrue(result["evidence"])
        first = result["evidence"][0]
        self.assertIn("citation_id", first)
        self.assertIn("authority", first)
        self.assertIn("text", first)

    def test_status_field_is_passed_through_verbatim(self) -> None:
        result = get_planning_context(
            "an extremely unlikely query string that matches nothing at all xyzzyplugh"
        )
        self.assertIn(result["status"], {"ready", "no_retrieved_evidence"})


if __name__ == "__main__":
    unittest.main()
