Use the required workflow output structure.

Concrete output rules:
- Each node must include exact settings, input data, output data, expressions, and a common mistake.
- Each node must identify its role: trigger, action, ai_agent, rag_retrieval, vector_storage, document_ingestion, approval_gate, control_flow, response, or error_handling.
- Choose the trigger from the event that starts the workflow. Do not choose a trigger only because a word appears later in the user task.
- For chatbot, chat interface, RAG chatbot, or chat-with-documents tasks, prefer Chat Trigger.
- Treat send email, sending emails, email someone, notify by email, draft email, reply by email, and approval-before-email as email actions, not Gmail triggers.
- Only use Gmail Trigger when incoming Gmail/email activity starts the workflow.
- For RAG chatbots over uploaded PDFs/documents, recommend Workflow A: Document Ingestion and Workflow B: RAG Chatbot.
- For human approval before email, put the approval gate before the email action and state that email is not sent until approval is received.
- Data mapping must use `source field -> destination field` examples.
- API steps must include method, URL placeholder, auth type, important headers/body, and expected response shape when possible.
- Test steps must say what to run and what result should appear.
- If a field name depends on the user's account or app schema, write "confirm in your n8n node output" and then give a likely mapping.
- Keep Source-Grounded Facts separate from Design Decisions and Assumptions.

Required sections:
# Workflow Name
# What This Workflow Does
# Assumptions
# Apps / Tools Needed
# Credentials Needed
# Trigger
# Nodes To Add
# Data Mapping
# AI Prompt, If Used
# Memory / RAG, If Used
# Error Handling
# Test Steps
# Final Checklist
# Source-Grounded Facts
# Design Decisions
# Needs User Confirmation
# Sources Used
