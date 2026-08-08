# n8n Workflow Builder — multi-RAG system that turns plain-English tasks into source-cited n8n workflow build plans

Global rules in ~/.claude/CLAUDE.md apply. Everything below is repo-specific.

All code lives in `n8n_rag_system/`; run every command from that directory.

## Run / verify

No venv or installs needed for tests and offline retrieval — stdlib plus the committed indexes suffice (verified on system Python 3.14). Tests use stdlib `unittest`, not pytest.

- Full test suite: `python3 -m unittest discover -s tests -v`
- One module: `python3 -m unittest tests.test_router -v`
- One test: `python3 -m unittest tests.test_router.RouterTests.test_router_intent_coverage`
- Retrieval smoke test (offline): `python3 scripts/05_query_rag.py --query "your task" --top-k 3 --show-chunks`
- Retrieval eval (golden questions): `python3 scripts/06_evaluate_rag.py`
- Quality gates summary: `python3 scripts/07_quality_report.py`
- Adversarial answer-quality eval: `python3 scripts/08_answer_quality_eval.py`

`requirements.txt` is optional quality only: beautifulsoup4 for HTML cleaning, sentence-transformers/openai for real embeddings.

## Architecture

The pipeline is the numbered scripts in `scripts/` (01 collect → 02 clean → 03 chunk → 04 index → 05 query → 06–08 evals); each wraps a class in `src/`:

- `src/source_registry.py` — validates `config/sources.yaml` (required fields, duplicate-URL check); 117 enabled sources as of 2026-07-06
- `src/rag_router.py` — intent detection, picks which of the 5 RAG indexes to search
- `src/retriever.py` — multi-query retrieval, priority/heading boosts, dedup, citation metadata
- `src/vector_store.py` — `JsonVectorStore`: one JSONL file per RAG in `data/indexes/`, committed, so retrieval works clone-fresh
- `src/embeddings.py` — provider chain: OpenAI (if `OPENAI_API_KEY` set) → sentence-transformers (if installed) → deterministic hash fallback
- `src/workflow_instruction_generator.py` — deterministic offline generator plus `build_llm_prompt()` for the LLM path
- `config/` — `sources.yaml` (source of truth for docs sources), `chunking.yaml`, `rag_profiles.yaml` (per-RAG boosts)
- `prompts/` — LLM prompt templates; `docs/` — design docs (architecture, rag_design, evaluation_plan, audit)

## Key design decisions

- Stdlib-first: everything must keep working with zero installed packages (hash embeddings, unittest, JSONL store). Optional deps only improve quality — never make them required. `src/schema.py` falls back to stdlib validation when pydantic is absent.
- Baseline vs challenger: the deterministic generator is the validated baseline/fallback; LLM output must keep every required section and cite retrieved sources to replace it.

## Common tasks

- Add or refresh doc sources: edit `config/sources.yaml`, then run `01_collect_sources.py --dry-run` → same without `--dry-run` → `02_clean_docs.py --force` → `03_chunk_docs.py --stats` → `04_build_indexes.py --reset`. Script 01 fetches from the live n8n docs site — always `--dry-run` first.
- Debug weak retrieval: `05_query_rag.py --show-chunks --top-k 3`, then `07_quality_report.py`. Check which embedding provider is active first — the hash fallback silently degrades ranking quality.

## Gotchas

- Tests insert the project root into `sys.path` themselves; run them from `n8n_rag_system/`, not the git root, or discovery finds nothing.
- `chromadb` is listed in `requirements.txt` but never imported anywhere (as of 2026-07-06) — don't build on it.

## Where history lives

`n8n_rag_system/README.md` covers human onboarding (venv, install, env vars, full pipeline walkthrough). `docs/audit.md` records the hardening-pass history. No dated session entries in this file — ever.
