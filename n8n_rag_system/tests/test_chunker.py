from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.chunker import chunk_markdown


class ChunkerTests(unittest.TestCase):
    def test_chunker_preserves_metadata(self) -> None:
        chunks = chunk_markdown(
            "# Webhook Node\n\nUse this node to receive data.\n\n## Settings\n\n- Method: POST",
            metadata={
                "source_title": "Webhook Node",
                "source_url": "https://docs.n8n.io/webhook",
                "category": "node_docs",
                "rag_target": "n8n_nodes_rag",
                "priority": "high",
            },
            max_tokens=20,
            overlap_tokens=5,
        )
        self.assertTrue(chunks)
        self.assertEqual(chunks[0].source_title, "Webhook Node")
        self.assertEqual(chunks[0].rag_target, "n8n_nodes_rag")
        self.assertTrue(chunks[0].heading_path)
        self.assertIn("token_count", chunks[0].metadata)

    def test_chunker_avoids_empty_chunks(self) -> None:
        chunks = chunk_markdown(
            "# Title\n\n\n\nSome text.",
            metadata={
                "source_title": "Doc",
                "source_url": "https://example.com",
                "category": "core_docs",
                "rag_target": "n8n_core_docs_rag",
                "priority": "medium",
            },
        )
        self.assertTrue(all(chunk.text.strip() for chunk in chunks))

    def test_chunker_merges_tiny_sections(self) -> None:
        markdown = "# A\n\nshort one\n\n## B\n\nshort two\n\n## C\n\nshort three"
        chunks = chunk_markdown(
            markdown,
            metadata={
                "source_title": "Doc",
                "source_url": "https://example.com",
                "category": "core_docs",
                "rag_target": "n8n_core_docs_rag",
                "priority": "medium",
            },
            min_tokens=6,
        )
        self.assertLessEqual(len(chunks), 2)


if __name__ == "__main__":
    unittest.main()
