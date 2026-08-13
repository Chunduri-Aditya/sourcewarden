# Merged Project Reaudit

Audit date: 2026-08-13

Status: `DONE_WITH_CONCERNS`

## Executive result

The merged project passes every local validation gate and now has a bounded self improvement loop. The loop can record untrusted feedback, freeze a reproducible baseline, validate prompt-only challengers, and compare deterministic baseline and candidate metrics. It cannot apply a candidate or certify its own promotion.

Production acceptance remains intentionally blocked because this workspace does not contain the external signer, private validation suites, one time approval consumer, or trusted integration service required by the project policy.

## Scope reviewed

- Root agent definitions, orchestration, evaluation protocol, grader, signed run ledger validator, security hooks, and control hash manifest.
- Self improvement command surface, policy, filesystem handling, schemas, hash bindings, metrics, approval shape, and rollback metadata.
- Merged RAG package, deterministic fallback behavior, tests, and offline operation.
- Existing tuning proposal `agent-reliability-20260725-01`.

## Findings remediated

| Finding | Resolution | Evidence |
|---|---|---|
| The project had proposal artifacts but no reusable feedback to challenger loop | Added `record`, `prepare`, `validate-candidate`, and `status` | CLI and 17 focused tests |
| A local tuner could otherwise target security-sensitive instructions | Tunable scope is pinned to exactly three nonsecurity Markdown prompts | Exact policy byte hash plus target allowlist tests |
| Local code could overstate self approval | No apply or promote command exists; every assessment reports `BLOCKED_EXTERNAL_INTEGRATOR` | Command surface and production-byte invariance tests |
| Untrusted JSON and files needed fail-closed handling | Added closed schemas, duplicate-key rejection, size bounds, no-follow descriptor reads, hard-link rejection, and post-read identity checks | Parser, traversal, symlink, hard-link, race, and oversize tests |
| Candidate or feedback text could contain secrets | Added six deterministic secret rules and non-disclosing error persistence | All-rule secret tests and clean repository scan |
| Metric evidence relied on coarse boolean claims | Tuning acceptance now requires signed baseline and candidate integer metrics, identical assertion totals, 100 percent hard and security passes, objective floor, and no protected-category regression | Run ledger self test |
| Tuning ledgers could carry unrelated workflow authority | Tuning now rejects n8n mutation authorization and workflow capability approvals | Run ledger self test |
| Explicit promotion approval was not required | Added an externally signed, nonce-bound, unconsumed approval receipt tied to baseline, candidate, proposal, target set, and scope | Run ledger self test and local approval-shape tests |
| Only part of the production agent surface was hash pinned | Expanded the manifest to 33 files, including all six agents and the self improvement controls | Repository security check |
| The complete project validator omitted the new module | Added the focused self improvement suite to `scripts/validate-project.py` | Complete validation run |

## Verification evidence

The complete validation command passed:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-project.py
```

Observed results:

- 17 self improvement adversarial tests passed.
- 34 RAG unit tests passed.
- All 6 agent definitions validated.
- All 74 visible generalized evaluation cases validated structurally.
- Evaluation grader self test passed.
- Signed run ledger validator self test passed, including deterministic regression, approval replay, and tuning authority rejection cases.
- Security gate self test passed.
- Repository security check passed with zero blocking findings and zero warnings.
- Independent module review returned `ALLOW` from security and `ALIGNED` from deviation review for snapshot `sha256:8fcc477fce20125d944cd9b8e152ab7a5f34f9e80025115986e78ce3cefbfcba`.

## Remaining blockers and concerns

1. No externally signed version 2 run ledger is installed for this change. Under the repository's own acceptance model, local checks do not constitute production acceptance.
2. External validation and blind holdout suites are intentionally absent. No claim about their outcomes is made.
3. The workspace cannot verify or consume the one time approval and cannot execute integration or rollback. Those operations require the external evaluator and trusted integrator described in `README.md`.
4. The existing `agent-reliability-20260725-01` proposal is not eligible for promotion. It executed zero behavioral cases and has no independently signed external-validation, blind-holdout, approval, or trusted-integration evidence. Its status remains hold only.
5. Hash fallback retrieval remains lower quality than optional semantic embeddings. It is an availability fallback, not evidence that semantic ranking quality is equivalent.

## Acceptance rule

Treat local status as development-ready, not production-promoted. A prompt challenger may advance only after the external evaluator supplies matching signed reports, the user supplies a digest-bound one time approval, final read-only reviews match the exact integrated snapshot, and the trusted integrator applies or rolls back exact verified bytes.
