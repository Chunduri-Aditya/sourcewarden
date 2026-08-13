from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.rag_router import RagRouter, detect_intents


class RouterTests(unittest.TestCase):
    def test_router_selects_ai_rag_for_ai_chatbot_questions(self) -> None:
        decision = RagRouter().route("How do I build an AI chatbot in n8n?")
        self.assertIn("n8n_ai_agents_rag", decision.selected_rags)
        self.assertIn("n8n_core_docs_rag", decision.selected_rags)
        self.assertIn("n8n_nodes_rag", decision.selected_rags)

    def test_router_selects_node_rag_for_api_questions(self) -> None:
        decision = RagRouter().route("What node should I use to call an API?")
        self.assertIn("n8n_nodes_rag", decision.selected_rags)
        self.assertIn("n8n_core_docs_rag", decision.selected_rags)

    def test_router_intent_coverage(self) -> None:
        cases = {
            "Explain this like I am five": "beginner_explanation",
            "Build a workflow for Slack alerts": "workflow_build_plan",
            "Which node should call an API?": "node_selection",
            "Create a webhook endpoint": "api_webhook",
            "Build an AI Agent workflow": "ai_agent",
            "Use Pinecone for RAG": "rag_vector_store",
            "Export workflow JSON": "workflow_json_import_export",
            "Set up OAuth credentials": "credentials_auth",
            "Debug a failed execution": "debugging_error_handling",
            "Deploy n8n with Docker": "deployment_self_hosting",
            "Show me an existing example workflow for this": "workflow_examples",
        }
        for query, intent in cases.items():
            with self.subTest(query=query):
                self.assertIn(intent, detect_intents(query))

    def test_router_selects_workflow_examples_rag_for_example_requests(self) -> None:
        decision = RagRouter().route("Is there a real example workflow that already does this?")
        self.assertIn("n8n_workflow_examples_rag", decision.selected_rags)

    def test_router_exposes_multi_queries(self) -> None:
        decision = RagRouter().route("Build an AI chatbot with Pinecone")
        self.assertIn("n8n_ai_agents_rag", decision.selected_rags)
        self.assertTrue(any(key.endswith(":settings") for key in decision.rewritten_queries))
        self.assertIn("intents", decision.retrieval_parameters)


if __name__ == "__main__":
    unittest.main()
