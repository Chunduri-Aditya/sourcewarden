from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.document_loader import DocumentLoader
from src.schema import Source


class CliAndOfflineTests(unittest.TestCase):
    def test_query_cli_smoke(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/05_query_rag.py",
                "--query",
                "Build a Slack alert workflow",
                "--top-k",
                "1",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=60,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("# Workflow Name", completed.stdout)
        self.assertIn("# Sources Used", completed.stdout)

    def test_offline_mode_graceful_failure(self) -> None:
        source = Source(
            title="Offline",
            url="http://127.0.0.1:9/missing.md",
            category="core_docs",
            rag_target="n8n_core_docs_rag",
            priority="high",
            source_type="official_docs",
            last_checked=None,
            enabled=True,
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = DocumentLoader(tmp).fetch_source(source, timeout=1, retries=0)
            self.assertEqual(result.status, "failed")
            self.assertTrue(result.error)


if __name__ == "__main__":
    unittest.main()
