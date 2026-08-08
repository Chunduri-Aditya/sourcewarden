from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.embeddings import HashEmbeddingProvider
from src.schema import Chunk
from src.vector_store import JsonVectorStore
from src.retriever import RagRetriever


class RetrieverContractTests(unittest.TestCase):
    def test_retriever_returns_chunks_with_citation_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = JsonVectorStore(tmp, embedding_provider=HashEmbeddingProvider())
            store.add_chunks(
                "n8n_nodes_rag",
                [
                    Chunk(
                        text="The HTTP Request node calls REST APIs and can use API key authentication.",
                        source_title="HTTP Request Node",
                        source_url="https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/",
                        heading_path=["HTTP Request Node"],
                        doc_category="node_docs",
                        rag_target="n8n_nodes_rag",
                        chunk_id="chunk-1",
                        chunk_type="node_reference",
                        priority="high",
                    )
                ],
            )
            retriever = RagRetriever(index_dir=tmp, embedding_provider=HashEmbeddingProvider())
            chunks = retriever.retrieve("What node should I use to call a REST API?", top_k=2)
            self.assertTrue(chunks)
            self.assertEqual(chunks[0].source_title, "HTTP Request Node")
            self.assertTrue(chunks[0].source_url)
            self.assertEqual(chunks[0].rag_name, "n8n_nodes_rag")


if __name__ == "__main__":
    unittest.main()

