# Audit And Hardening Notes

## Starting State

Before this hardening pass, the system had:

- Sources configured: 23
- Raw docs: 23
- Processed docs: 23
- Chunks: 39
- Chunks per RAG:
  - `n8n_ai_agents_rag`: 11
  - `n8n_beginner_instruction_rag`: 6
  - `n8n_core_docs_rag`: 8
  - `n8n_nodes_rag`: 12
  - `n8n_workflow_json_rag`: 2
- Average chunk size: about 436 tokens
- Min/max chunk size: 3/1000 tokens

## Weak Spots Found

- Source coverage was too narrow for broad workflow-building support.
- `sources.yaml` did not cover enough workflow logic, deployment, credential, AI, RAG, and node reference docs.
- The collector had no retries, dry-run mode, source filters, duplicate URL report, or durable status report.
- The cleaner treated all raw files as HTML and did not explicitly support official Markdown docs.
- Chunking lacked a detailed stats report and created very small chunks for heading-heavy docs.
- Routing was mostly keyword lists and did not expose explicit intents.
- Retrieval ran only one query per RAG and did not deduplicate merged results.
- The generator did not validate required output sections after generation.
- The eval set was too small and did not include required keywords or forbidden behavior checks.

## Hardened State

After this pass:

- `config/sources.yaml` contains 117 enabled official n8n docs sources.
- Source categories now cover core workflow docs, core node docs, AI docs, workflow JSON/API/template docs, credential/API/deployment docs, and beginner docs.
- Duplicate URL detection is implemented and the expanded config has no duplicate URLs.
- Collection supports retries, timeout, custom user-agent, dry-run, RAG/category filters, force refresh, status report, and failure log.
- Cleaning supports both HTML and Markdown and preserves headings, code, tables, admonitions, page title, canonical URL, and metadata.
- Chunking supports `--stats` and reports total chunks, chunks per RAG, chunks per source, average tokens, min/max tokens, empty chunks, and duplicate chunks.
- Router exposes intents for beginner explanation, workflow build plan, node selection, API/webhook, AI agent, RAG/vector store, workflow JSON/import/export, credentials/auth, debugging/error handling, and deployment/self-hosting.
- Retrieval runs multi-query searches, boosts source priority and heading/path matches, deduplicates chunks, and always returns citation metadata.
- The generator validates required sections and citation URLs when retrieved sources exist.
- `rag_eval_questions.jsonl` has 84 eval questions with expected RAGs, required sections, required keywords, forbidden behavior, and difficulty.
- `golden_cases.jsonl` has 10 golden output contract cases.
- `scripts/07_quality_report.py` summarizes source, chunk, index, eval, and test health.

## Remaining Risks

- Hash embeddings are useful for no-key local testing but weaker than OpenAI or sentence-transformer embeddings.
- Some official docs pages are short, so chunk averages can remain below the nominal target even after small-section merging.
- The deterministic generator is a validated fallback, not a replacement for a strong LLM final answer.
- Generated workflow JSON blueprints must be import-tested in n8n.

