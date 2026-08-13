from __future__ import annotations

import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.planning_context import build_planning_context
from src.schema import RetrievedChunk, RouterDecision


class FakeRetriever:
    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        self.chunks = chunks

    def retrieve_with_decision(self, query: str, top_k: int):
        return (
            RouterDecision(
                selected_rags=["n8n_nodes_rag", "n8n_workflow_examples_rag"],
                rewritten_queries={"n8n_nodes_rag": query},
                reason="test route",
                retrieval_parameters={"top_k_per_rag": top_k},
            ),
            self.chunks,
        )


def make_chunk(rag_name: str, title: str) -> RetrievedChunk:
    return RetrievedChunk(
        text=f"Evidence from {title}",
        source_title=title,
        source_url=f"https://example.com/{title.lower()}",
        heading_path=["Configuration"],
        relevance_score=0.9,
        rag_name=rag_name,
        chunk_id=title,
        priority="high",
    )


class PlanningContextTests(unittest.TestCase):
    def test_context_labels_authority_and_bounds_evidence(self) -> None:
        chunks = [
            make_chunk("n8n_nodes_rag", "Official"),
            make_chunk("n8n_workflow_examples_rag", "Community"),
        ]
        context = build_planning_context(
            "Build a webhook workflow",
            top_k=2,
            max_chars_per_evidence=10,
            retriever=FakeRetriever(chunks),
        )

        self.assertEqual(context["status"], "ready")
        self.assertEqual(context["authority_order"][0]["source"], "live_n8n_schema")
        self.assertEqual(context["evidence"][0]["authority"], "official_n8n_documentation")
        self.assertEqual(context["evidence"][1]["authority"], "community_workflow_example")
        self.assertEqual(len(context["evidence"]), 2)
        self.assertTrue(context["evidence"][0]["truncated"])
        self.assertLessEqual(len(context["evidence"][0]["text"]), 13)

    def test_context_reports_missing_evidence(self) -> None:
        context = build_planning_context(
            "Build a webhook workflow",
            retriever=FakeRetriever([]),
        )
        self.assertEqual(context["status"], "no_retrieved_evidence")
        self.assertEqual(context["evidence"], [])

    def test_context_rejects_invalid_input(self) -> None:
        with self.assertRaises(ValueError):
            build_planning_context("   ", retriever=FakeRetriever([]))
        with self.assertRaises(ValueError):
            build_planning_context("valid", top_k=0, retriever=FakeRetriever([]))
        with self.assertRaises(ValueError):
            build_planning_context(
                "valid",
                max_chars_per_evidence=0,
                retriever=FakeRetriever([]),
            )


if __name__ == "__main__":
    unittest.main()
