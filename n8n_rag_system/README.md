# n8n RAG System

This is a self-contained multi-RAG system for an n8n Workflow Instruction Agent. It converts messy human tasks into beginner-friendly, source-cited n8n workflow build plans with exact trigger, node order, settings, credentials, expressions, data mapping, testing, error handling, assumptions, design decisions, and source citations.

The system uses five separate RAG indexes:

- `n8n_core_docs_rag`: workflows, executions, credentials, expressions, data structure, item linking, flow logic, debugging, deployment, and security.
- `n8n_nodes_rag`: core nodes, trigger nodes, HTTP Request, Webhook, Respond to Webhook, Code, Edit Fields, IF, Switch, Merge, loop, Wait, file nodes, and n8n node docs.
- `n8n_ai_agents_rag`: AI Agent, chains, RAG, vector stores, embeddings, memory, human fallback, human-in-the-loop, and evaluations.
- `n8n_workflow_json_rag`: workflow JSON, export/import, n8n API, templates, examples, and reusable workflow blueprints.
- `n8n_beginner_instruction_rag`: beginner workflow concepts, simple explanations, checklists, and testing guidance.

## Architecture

1. `SourceRegistry` loads and validates `config/sources.yaml`, including duplicate URL checks.
2. `DocumentLoader` downloads official docs with retries, timeout controls, status reports, failure logs, and Markdown/HTML support.
3. `Cleaner` converts raw HTML or Markdown into clean Markdown while preserving headings, code blocks, tables, admonitions, links, page title, and canonical URL.
4. `Chunker` chunks by heading structure, keeps code/procedure blocks intact where possible, merges small sections toward the configured target, and reports stats.
5. `EmbeddingProvider` selects OpenAI embeddings, sentence-transformers, or deterministic hash embeddings.
6. `JsonVectorStore` stores one persistent local JSONL index per RAG under `data/indexes/`.
7. `RagRouter` detects intents and selects the right RAGs.
8. `RagRetriever` runs multi-query retrieval, boosts source priority and headings, deduplicates chunks, and returns citation metadata.
9. `PromptBuilder` creates an LLM-ready prompt that separates retrieved facts, assumptions, design decisions, and user requirements.
10. `WorkflowInstructionGenerator` creates a deterministic validated build plan for local testing or fallback operation.

## Install

```bash
cd /Users/chunduri/Documents/n8n_workflow_builder/n8n_rag_system
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

The package can run basic tests and hash-based retrieval with only the Python standard library. Install `requirements.txt` for better HTML parsing and optional embedding providers.

## Environment Variables

- `OPENAI_API_KEY`: enables OpenAI embeddings when set.
- `OPENAI_EMBEDDING_MODEL`: defaults to `text-embedding-3-small`.
- `LOCAL_EMBEDDING_MODEL`: defaults to `sentence-transformers/all-MiniLM-L6-v2`.
- `N8N_RAG_INDEX_DIR`: defaults to `data/indexes`.
- `N8N_RAG_TOP_K`: defaults to `5`.

Embedding provider order:

1. OpenAI if `OPENAI_API_KEY` and the OpenAI SDK are available.
2. Local `sentence-transformers` if installed.
3. Deterministic hash embeddings as a no-key fallback.

## Pipeline Commands

Collect official n8n docs:

```bash
python scripts/01_collect_sources.py --timeout 30 --retries 2
```

Filter collection:

```bash
python scripts/01_collect_sources.py --only-rag n8n_ai_agents_rag
python scripts/01_collect_sources.py --only-category node_docs
python scripts/01_collect_sources.py --dry-run
```

Clean docs:

```bash
python scripts/02_clean_docs.py --force
```

Chunk docs and inspect stats:

```bash
python scripts/03_chunk_docs.py --stats
```

Build all five indexes:

```bash
python scripts/04_build_indexes.py --reset
```

Query:

```bash
python scripts/05_query_rag.py \
  --query "Make a workflow that reads Gmail invoices, extracts the amount, saves it to Google Sheets, and alerts me on Slack" \
  --mode full_build_plan \
  --show-sources \
  --show-chunks
```

Evaluate:

```bash
python scripts/06_evaluate_rag.py
```

Quality report:

```bash
python scripts/07_quality_report.py
```

## Add Sources

Edit `config/sources.yaml`. Every source must include:

- `title`
- `url`
- `category`
- `rag_target`
- `priority`
- `source_type`
- `last_checked`
- `enabled`

Use official Markdown docs URLs from `https://docs.n8n.io/llms.txt` when possible. Run:

```bash
python scripts/01_collect_sources.py --dry-run
python scripts/01_collect_sources.py
python scripts/02_clean_docs.py --force
python scripts/03_chunk_docs.py --stats
python scripts/04_build_indexes.py --reset
```

## Evaluate Retrieval

Use `--show-chunks` to inspect selected RAGs, router reasons, chunk scores, headings, and source URLs. Good retrieval should show:

- sources from the expected RAGs,
- headings that match the task,
- chunks with official n8n URLs,
- no repeated near-identical chunks dominating the answer.

Weak retrieval usually means:

- the source category is missing,
- the router did not detect the right intent,
- the chunk is too broad or too small,
- the embedding provider is using the hash fallback,
- the user query needs a rewritten retrieval query.

Start debugging with:

```bash
python scripts/05_query_rag.py --query "your task" --show-chunks --top-k 3
python scripts/07_quality_report.py
```

## Connect PromptBuilder To An LLM

`WorkflowInstructionGenerator.generate()` returns a deterministic validated response. For production LLM generation, use:

```python
from src.schema import WorkflowInstructionRequest
from src.workflow_instruction_generator import WorkflowInstructionGenerator

generator = WorkflowInstructionGenerator()
prompt = generator.build_llm_prompt(
    WorkflowInstructionRequest(
        user_task="Build a RAG chatbot with Pinecone",
        output_mode="full_build_plan",
    )
)
```

Send `prompt` to your LLM, then validate that the answer keeps every required section, cites retrieved sources, and separates source-grounded facts from assumptions and design decisions.

## Limitations

- Hash embeddings are a fallback, not the best retrieval quality. Use OpenAI or sentence-transformers for production.
- The deterministic generator is conservative. It is meant for validation, smoke tests, and fallback operation.
- Generated workflow JSON blueprints must still be import-tested in n8n.
- Some official docs pages are short; chunk averages may stay below the nominal 800-1200 token target even with section merging.
- Exact app field names must be confirmed from real node output in the user’s n8n workspace.

