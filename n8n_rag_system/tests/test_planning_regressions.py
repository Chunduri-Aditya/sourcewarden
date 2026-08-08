from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.rag_router import RagRouter
from src.workflow_instruction_generator import WorkflowInstructionGenerator, analyze_planning_intent


class PlanningRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.generator = WorkflowInstructionGenerator()

    def test_rag_chatbot_pdf_email_uses_chat_trigger_and_split(self) -> None:
        query = "Build an n8n RAG chatbot that answers from uploaded PDFs using Pinecone and has human approval before sending emails"
        decision = RagRouter().route(query)
        self.assertIn("n8n_ai_agents_rag", decision.selected_rags)
        self.assertIn("n8n_nodes_rag", decision.selected_rags)

        response = self.generator.generate(query, top_k=3)
        nodes_text = response.sections["Nodes To Add"]
        self.assertIn("Chat Trigger", response.sections["Trigger"])
        self.assertNotIn("Gmail Trigger", response.content)
        self.assertIn("Email Send", nodes_text)
        self.assertLess(nodes_text.index("Node Name: IF"), nodes_text.index("Node Name: Email Send"))
        self.assertIn("Workflow A", response.content)
        self.assertIn("Workflow B", response.content)

        planning = analyze_planning_intent(query)
        self.assertEqual(planning.detected_start_event, "chat")
        self.assertIn("Gmail Trigger", planning.forbidden_triggers)
        self.assertEqual(planning.recommended_workflow_split, "document_ingestion_and_rag_chatbot")

    def test_gmail_invoice_attachment_uses_gmail_trigger(self) -> None:
        query = "When I get a new Gmail invoice attachment, extract the PDF total and save it to Google Sheets"
        response = self.generator.generate(query, top_k=3)
        self.assertIn("Gmail Trigger", response.sections["Trigger"])
        self.assertIn("Extract From File", response.sections["Nodes To Add"])
        self.assertIn("Google Sheets", response.sections["Nodes To Add"])
        self.assertNotIn("Chat Trigger", response.sections["Trigger"])

    def test_chatbot_email_after_approval_does_not_use_gmail_trigger(self) -> None:
        query = "Make a chatbot that emails me the answer after I approve it"
        response = self.generator.generate(query, top_k=3)
        nodes_text = response.sections["Nodes To Add"]
        self.assertIn("Chat Trigger", response.sections["Trigger"])
        self.assertNotIn("Gmail Trigger", response.content)
        self.assertIn("Email Send", nodes_text)
        self.assertLess(nodes_text.index("Node Name: IF"), nodes_text.index("Node Name: Email Send"))

    def test_watch_gmail_inbox_uses_gmail_trigger(self) -> None:
        query = "Watch my Gmail inbox and summarize every new email"
        response = self.generator.generate(query, top_k=3)
        self.assertIn("Gmail Trigger", response.sections["Trigger"])

    def test_webhook_confirmation_email_keeps_webhook_trigger(self) -> None:
        query = "Build a webhook workflow that receives a lead and sends a confirmation email"
        response = self.generator.generate(query, top_k=3)
        nodes_text = response.sections["Nodes To Add"]
        self.assertIn("Webhook Trigger", response.sections["Trigger"])
        self.assertIn("Email Send", nodes_text)
        self.assertNotIn("Gmail Trigger", response.content)


if __name__ == "__main__":
    unittest.main()
