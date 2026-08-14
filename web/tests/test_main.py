from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from web.main import app


class MainRoutesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_index_renders_nav_page(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("sourcewarden control panel", response.text)
        self.assertIn("/chat", response.text)
        self.assertIn("/dashboard", response.text)

    def test_chat_get_without_query_shows_empty_state(self) -> None:
        response = self.client.get("/chat")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Enter a query", response.text)

    def test_chat_get_with_real_query_returns_grounded_evidence(self) -> None:
        response = self.client.get(
            "/chat", params={"query": "How do I configure the HTTP Request node?", "top_k": 3}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Evidence", response.text)

    def test_chat_post_with_query_renders_result(self) -> None:
        response = self.client.post("/chat", params={"query": "webhook node", "top_k": 3})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Enter a query", response.text)

    def test_dashboard_renders_all_sections(self) -> None:
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Run status", response.text)
        self.assertIn("agent-reliability-20260725-01", response.text)
        self.assertIn("Eval / tuning files", response.text)
        self.assertIn("Security control hashes", response.text)
        self.assertIn("Module manifest", response.text)
        self.assertIn("self_improvement", response.text)

    def test_no_write_methods_are_allowed_on_any_route(self) -> None:
        for path in ("/", "/chat", "/dashboard"):
            for method in ("put", "patch", "delete"):
                response = getattr(self.client, method)(path)
                self.assertEqual(response.status_code, 405, f"{method.upper()} {path}")


if __name__ == "__main__":
    unittest.main()
