# Sourcewarden — showcase

One-paragraph version, a 2-minute demo, and an honest read on what is and is not finished.

## What it is

A plain-language automation request goes in; the smallest reliable n8n workflow comes out, with every non-trivial node parameter backed by a cited source and every live mutation held behind a fail-closed, externally signed approval gate. Two upstream repositories (a source-cited multi-RAG workflow builder and an n8n workflow generator with orchestration and security controls) were merged into one tree before any new code was written on top.

The interesting parts:

- **Evidence has a fixed precedence order** — live target-instance schema, official docs, community examples, then untrusted course transcripts. A lower source never overrides a higher one, and a documentation excerpt is never accepted as proof of an exact node schema.
- **The web layer is a read-only reviewer, not an agent driver.** It renders retrieval results, security hash status, and self-improvement run state. No route accepts a write method (there is a test that asserts exactly this).
- **The hash check for protected control files is reimplemented in Python** rather than shelling out, so the gate has no dependency on an external binary and no shell-injection surface.
- **The integrity gate is real and it fails closed.** `.codex/security-control-hashes.json` pins the sha256 of 34 control files (agent definitions, hooks, policy, the validators themselves). Change any one and `scripts/validate-project.py` returns non-zero with `SECURITY_CONTROL_CHANGED` naming the file. This was confirmed live: a one-word edit to `AGENTS.md` tripped it immediately.
- **Self-improvement cannot self-apply.** The local loop records untrusted failure signals, freezes a clean baseline, and scores a bounded prompt challenger, then always stops at `BLOCKED_EXTERNAL_INTEGRATOR`. Applying a candidate needs independently signed non-regression evidence and a trusted integrator outside the workspace.

## 2-minute demo (no n8n instance needed)

```bash
cd ~/Desktop/Projects/sourcewarden
pip install -r web/requirements.txt        # fastapi, uvicorn, jinja2, httpx

# 1. integrity + security-control validator — exit 0 means all merged-project checks pass
python3 scripts/validate-project.py

# 2. grounded planning evidence for a request: bounded JSON, ranked, with a citation trail
python3 scripts/retrieve-rag-context.py \
  --query "Build a webhook that validates input and returns the weather" \
  --top-k 3 --pretty

# 3. read-only review dashboard
uvicorn web.main:app --reload              # open http://127.0.0.1:8000
```

To show the integrity gate catching a change: `echo "" >> AGENTS.md` then re-run step 1 — it now exits 1 and names `AGENTS.md`. `git checkout -- AGENTS.md` to restore.

## Tests

```bash
make test
```

Runs three offline suites, no network and no vector database:

| Suite | Count | Covers |
|---|---|---|
| `web/tests` | 20 | read-only web layer, security hash status rendering, no-write-methods invariant |
| `n8n_rag_system/tests` | 34 | retrieval contract, router intent coverage, deterministic planning, workflow-example parsing |
| `tests/self_improvement` | 17 | secret-rejection rules, fail-closed manifest and approval binding, no-disclosure on reject |

Last run 2026-09-08: 71 passed, 0 failed. `scripts/validate-project.py` exits 0.

## Done

- Retrieval, citation, and deterministic fallback planning — standard-library-first, runs with no optional deps
- Read-only web dashboard, 9 routes, write-method rejection enforced by test
- Protected-control hash manifest + fail-closed validator, verified catching a real edit
- Self-improvement record / prepare / validate-candidate / status loop, terminating at the external-integrator boundary
- Multi-agent orchestration definitions (`supervisor`, `security_firewall`, `skeleton_architect`, `module_builder`, `deviation_monitor`, `eval_tuner`) with single-writer / separate-reviewer scheduling

## Known gaps

- **Live n8n mutation is not exercised end to end here.** It needs a connected n8n instance with instance-level MCP, plus the Ed25519 signed run ledger produced by an external broker. The gate correctly denies by default until that ledger exists; there is no in-repo demo of a successful signed mutation.
- **RAG indexes are built locally and Git ignored.** A fresh clone has no `n8n_rag_system/data/indexes/`; the retrieval demo needs an index build first (`n8n_rag_system/` scripts `01`–`09`). The copy on this machine is already indexed.
- `chromadb` is listed in `n8n_rag_system/requirements.txt` but is deliberately not imported; the deterministic path is the baseline and an LLM output only replaces it when every required section and citation is preserved.
- No CI workflow committed; `make test` + `scripts/validate-project.py` are the gate and are run by hand.

## Layout

`~/Desktop/Projects/sourcewarden` · branch `main` · <https://github.com/Chunduri-Aditya/sourcewarden>
