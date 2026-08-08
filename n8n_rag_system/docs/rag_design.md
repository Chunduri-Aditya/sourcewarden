# RAG Design

The agent uses five indexes because n8n workflow-building questions mix different types of knowledge. Keeping them separate reduces noisy retrieval and makes routing explainable.

- Core docs answer general workflow, trigger, credential, expression, execution, and debugging questions.
- Node docs answer exact node selection and parameter questions.
- AI agent docs answer AI Agent, RAG, vector store, memory, LangChain, and human fallback questions.
- Workflow JSON docs answer export, import, API, template, and blueprint questions.
- Beginner instruction docs help the final answer stay simple and testable.

Routing is rule-based in this implementation. It can later be replaced with an LLM classifier while keeping the same `RouterDecision` schema.

Retrieval combines embedding similarity, keyword overlap, and a small priority boost for official high-priority docs. Returned chunks always carry citation metadata.

