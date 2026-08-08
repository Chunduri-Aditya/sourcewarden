# Usage Examples

Beginner workflow recipe:

```bash
python scripts/05_query_rag.py \
  --query "Make a workflow that reads Gmail invoices, extracts the amount, saves it to Google Sheets, and alerts me on Slack" \
  --mode full_build_plan \
  --show-sources
```

Node selection question:

```bash
python scripts/05_query_rag.py \
  --query "What node should I use to call a REST API with an API key?" \
  --mode technical_steps
```

AI/RAG workflow:

```bash
python scripts/05_query_rag.py \
  --query "Build an AI chatbot in n8n that answers from my PDFs using Pinecone" \
  --mode full_build_plan
```

Workflow JSON mode:

```bash
python scripts/05_query_rag.py \
  --query "Generate workflow JSON for webhook to Slack alert" \
  --mode workflow_json_blueprint \
  --json
```

