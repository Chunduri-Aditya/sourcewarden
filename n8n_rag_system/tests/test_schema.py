from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.schema import Source, WorkflowInstructionResponse
from src.source_registry import SourceRegistry


class SchemaTests(unittest.TestCase):
    def test_source_schema_validates_required_fields(self) -> None:
        with self.assertRaises(Exception):
            Source.model_validate(
                {
                    "url": "https://docs.n8n.io/",
                    "category": "core_docs",
                    "rag_target": "n8n_core_docs_rag",
                    "priority": "high",
                    "source_type": "web_page",
                    "last_checked": None,
                    "enabled": True,
                }
            )

    def test_source_registry_loads_sources(self) -> None:
        sources = SourceRegistry(ROOT / "config" / "sources.yaml").load_sources()
        self.assertGreaterEqual(len(sources), 75)
        self.assertTrue(all(source.title and source.url for source in sources))
        self.assertTrue(all(source.source_type == "official_docs" for source in sources))

    def test_source_registry_detects_duplicate_urls(self) -> None:
        import tempfile

        duplicate_yaml = """
core_docs:
  - title: A
    url: https://docs.n8n.io/a.md
    category: core_docs
    rag_target: n8n_core_docs_rag
    priority: high
    source_type: official_docs
    last_checked:
    enabled: true
  - title: B
    url: https://docs.n8n.io/a.md
    category: core_docs
    rag_target: n8n_core_docs_rag
    priority: high
    source_type: official_docs
    last_checked:
    enabled: true
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sources.yaml"
            path.write_text(duplicate_yaml, encoding="utf-8")
            registry = SourceRegistry(path)
            self.assertEqual(len(registry.duplicate_urls()), 1)
            with self.assertRaises(ValueError):
                registry.assert_no_duplicate_urls()

    def test_workflow_instruction_response_schema_validates(self) -> None:
        response = WorkflowInstructionResponse(
            content="# Workflow Name\n\nExample",
            sections={"Workflow Name": "Example"},
            sources=[{"title": "n8n Docs", "url": "https://docs.n8n.io/", "heading_path": []}],
        )
        self.assertIn("Workflow Name", response.content)


if __name__ == "__main__":
    unittest.main()
