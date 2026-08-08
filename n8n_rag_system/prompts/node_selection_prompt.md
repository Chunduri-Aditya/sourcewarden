Choose the correct n8n nodes for the user task.
Explain why each node is needed.

Before choosing nodes, classify each node role:
- trigger
- action
- ai_agent
- rag_retrieval
- vector_storage
- document_ingestion
- approval_gate
- control_flow
- response
- error_handling

Choose the trigger from the event that starts the workflow, not from any word that appears later in the task.

Chatbot trigger rule:
- If the user asks for a chatbot, chat bot, chat interface, conversational workflow, questions over documents, RAG chatbot, or chat with documents, prefer Chat Trigger.
- Do not use Gmail Trigger for a chatbot just because the chatbot later sends an email.

Email action rule:
- If the task says send email, sending emails, email someone, notify by email, approval before email, draft email, reply by email, or send approved answer, classify email as an action.
- Use Email Send, Send Email, or a Gmail action node for sending. Do not use Gmail Trigger unless Gmail activity starts the workflow.

Gmail Trigger rule:
- Only use Gmail Trigger when the workflow starts from Gmail or incoming email activity, such as when a new email arrives, a new Gmail message arrives, an unread Gmail item appears, a Gmail attachment is received, or the user asks to watch/monitor the Gmail inbox.

RAG uploaded-document rule:
- If the task combines RAG/chatbot with uploaded PDFs, documents, a knowledge base, vector store, Pinecone, Supabase, Qdrant, or embeddings, recommend two workflows:
  - Workflow A: Document Ingestion.
  - Workflow B: RAG Chatbot.

Human approval rule:
- If approval is requested before sending, place the approval gate before the email action.
- State that email is not sent until approval is received.
