# Agent reliability instruction proposal

## Run identity and status

- Assignment ID: `agent-reliability-tuning-proposal-20260725-01-r1`
- Original assignment ID: `agent-reliability-tuning-proposal-20260725-01`
- Run ID: `agent-reliability-20260725-01`
- Baseline snapshot ID: `prewrite-unversioned-workspace-20260725-agent-reliability-01`
- Baseline limitation: the snapshot ID was supplied by the supervisor but is not externally attested.
- Candidate: `agent-instructions.patch` plus the six TOML files under `proposed/`
- Status: proposal-only; not applied to production

## Root-cause analysis

The visible generalized training corpus contains broad reliability scenarios, but the current custom-role instructions mostly enforce orchestration order, path ownership, general safety, and generic testing. Reliability responsibilities are not explicitly allocated from plan through contract, implementation, review, security, and tuning. This creates four related failure clusters:

1. **Incomplete reliability planning and ambiguity gates.** The supervisor does not currently require a single matrix that assigns structured validation, identity/idempotency, retry, error semantics, credential/privacy, observability, concurrency/rate-limit, side-effect verification, and uncertain-commit recovery to named roles with evidence. Material gaps can therefore reach delegation.
2. **Unfrozen cross-module reliability contracts.** The skeleton role requires interfaces generally, but does not explicitly freeze identity keys, error envelopes, retry policies, side-effect states, postcondition oracles, telemetry policy, concurrency controls, or fault seams. Module implementations can make inconsistent local assumptions.
3. **Generic implementation and review language.** The module builder asks only for focused tests, while the monitor checks generic plan conformance. Neither explicitly requires reconciliation before replay, atomic deduplication, bounded retries, honest success guards, redacted telemetry, or partial/uncertain-commit tests.
4. **Security and tuning coverage is broad but not reliability-complete.** The firewall strongly protects secrets and authority, and the tuner preserves data separation, but neither currently enumerates the full reliability threat surface or requires role-specific evidence across the visible reliability dimensions.

The smallest generalized change is to add one compact, role-specific reliability paragraph or checklist to each existing `developer_instructions` block. No sandbox, approval, feature, MCP, network, shell, orchestration, policy, skill, hook, eval, or expected-result setting changes.

## Role-responsibility and reliability matrix

| Reliability dimension | Supervisor | Security firewall | Skeleton architect | Module builder | Deviation monitor | Eval tuner |
|---|---|---|---|---|---|---|
| Structured input/output validation | Require matrix, exact schema evidence, deterministic validation, and success criteria | Block unvalidated/model-defined data reaching consequential actions | Freeze typed schemas, deterministic validator, success/error union, and fault seam | Implement exact-schema deterministic validation before routing or side effects | STOP for stale/invented schemas or unvalidated output | Cluster visible validation failures without treating keyword coverage as a score |
| Stable identity and idempotency/deduplication | Require an identity and operation-specific idempotency owner or justified N/A | Analyze key scope, least duplication authority, races, and safe replay | Freeze item identity, idempotency key, atomic deduplication, and batch cardinality | Preserve identity and implement operation-specific, concurrency-safe deduplication | STOP for lost identity or race-prone check-then-write deduplication | Track identity/idempotency as a distinct failure cluster |
| Bounded retry, backoff, jitter, and eligibility | Require evidence for transient/permanent behavior and retry exhaustion | Analyze retry eligibility, bounds, outage amplification, and live-retry authority | Freeze eligibility, attempts, timeout, backoff, jitter, and terminal state | Retry only classified transient steps within frozen bounds and provider limits | STOP for blind, unbounded, whole-pipeline, or unqualified retry | Track retry and rate-limit failures separately |
| Failure branches and Error Trigger semantics | Require exact current schema/semantics and failure-path evidence | Treat error payloads as untrusted; analyze handler recursion and failure | Freeze typed error envelope, honest status, distinct branches, and version-sensitive semantics | Keep success/error paths distinct; never swallow failure or emit false success | STOP for mixed paths, false success, unsafe handlers, or missing tests | Cluster error-semantics failures without memorizing case wording |
| Credentials, data privacy, redaction, and retention | Require grounded credential/resource references and approval boundaries | Enforce reference-only, least-privilege credentials; classify data; review redaction/access/retention | Freeze credential type/reference, fixed resources, redacted telemetry, access, and retention | Use only frozen references; never log secrets or raw sensitive payloads | STOP for unsafe credentials, logs, alerts, or retention | Preserve security expectations and reject safety weakening |
| Logging, metrics, monitoring, and alert safety | Require structured evidence and mock-first handler tests | Analyze log/trace/alert exposure, deduplication, rate limits, escalation, and recursion | Freeze correlation fields, metrics, alerts, deduplication, escalation, and recursion guard | Emit structured, bounded, redacted state/attempt/outcome telemetry | STOP for unsafe observability or missing handler-failure evidence | Require role-specific visible evidence and externally signed evaluation before integration |
| Provider rate limits and concurrency | Require applicable duplicate/replay and concurrency/rate-limit evidence | Analyze concurrent authority, dedup races, rate limits, and outage amplification | Freeze concurrency ownership, atomicity, rate limits, and batch cardinality | Respect provider concurrency/rate limits and test races | STOP for race-prone dedup, missing limits, or missing concurrency tests | Track concurrency/rate-limit coverage explicitly |
| External side-effect verification | Require independent business postcondition oracle and success guard | Reject green status, provider acceptance, broad credentials, or narration as proof | Freeze side-effect states and an independent postcondition oracle | Verify the frozen postcondition before reporting success | STOP for unverified side effects or unsupported success | Require before/after evidence rather than self-authored claims |
| Partial or uncertain commits and recovery | Require pre-commit, partial, and uncertain-commit evidence | Analyze reconciliation, compensation, and safe replay authority | Freeze state machine, reconciliation-before-replay, and manual/compensation boundary | Persist uncertainty, query the oracle, reconcile, and retry only proven-safe unfinished work | STOP for missing uncertain state, reconciliation, or fault tests | Track recovery/reconciliation as its own root-cause cluster |

Every applicable row requires an owner and evidence. `N/A` is accepted only with a concrete, workflow-specific reason.

## Exact minimal proposed changes

- `supervisor.toml`: require the reliability matrix, block material ambiguity, require exact target-version SDK/node/error/credential/resource grounding before configuration, and require mock-first evidence across applicable reliability rows.
- `security-firewall.toml`: expand the threat review to include data classification, idempotency/concurrency, retry amplification, uncertain commits, reconciliation, observability privacy, alert storms/recursion, and live approval boundaries.
- `skeleton-architect.toml`: freeze reliability contracts and test seams without implementing module internals; stop when exact version-sensitive semantics are missing.
- `module-builder.toml`: implement only the frozen subset with deterministic validation, operation-specific idempotency, bounded retries, reconciliation-before-replay, verified postconditions, redacted telemetry, and focused fault tests.
- `deviation-monitor.toml`: compare the plan matrix, manifest, diff, and evidence; add explicit STOP conditions for the reliability failure clusters.
- `eval-tuner.toml`: cluster visible training failures across the full reliability surface, preserve private-suite separation, reject static coverage as behavioral scoring, and require externally signed evidence before recommending integration.

The unified candidate is in `agent-instructions.patch`; parseable offline copies are under `proposed/`.

## Selected course lessons

The following transcript-derived references informed the reliability vocabulary and verification seams:

- `m01-t10-using-ai-in-automation` — `lesson-m01-t10-using-ai-in-automation.md`: bounded AI steps, explicit output schemas, and validation before side effects.
- `m03-t01-email-trigger-and-pdf-extraction` — `lesson-m03-t01-email-trigger-and-pdf-extraction.md`: stable attachment identity, contained file handling, and explicit downstream contracts.
- `m03-t04-extracting-key-fields-using-llms` — `lesson-m03-t04-extracting-key-fields-using-llms.md`: parseable JSON is not validated business data; validate exact keys, types, invariants, and ambiguity.
- `m03-r02-structured-llm-extraction-dynamic-prompts-google-sheets` — `lesson-m03-r02-structured-llm-extraction-dynamic-prompts-google-sheets.md`: stable row identity, idempotency, batching/rate limits, prompt trust boundaries, and reconciliation.
- `m04-t01-introduction-to-error-handling-in-n8n` — `lesson-m04-t01-introduction-to-error-handling-in-n8n.md`: failure taxonomy, safe error envelopes, honest success state, bounded retry, reconciliation, and alert controls.
- `m04-t02-node-level-error-management` — `lesson-m04-t02-node-level-error-management.md`: item correlation, distinct success/error outputs, retry eligibility, partial success, and batch replay hazards.
- `m04-r01-error-detection-automatic-retries-failure-recovery` — `lesson-m04-r01-error-detection-automatic-retries-failure-recovery.md`: durable attempt state, bounded backoff/jitter, concurrency limits, dead-letter state, and postcondition verification.
- `m04-t05-reviewing-and-finalizing-workflow-logic` — `lesson-m04-t05-reviewing-and-finalizing-workflow-logic.md`: finalization through contracts, validation evidence, idempotency, post-write verification, and partial-commit recovery.
- `m04-t06-conducting-end-to-end-workflow-testing` — `lesson-m04-t06-conducting-end-to-end-workflow-testing.md`: stable fixtures, field-level oracles, duplicate/concurrency tests, failure injection, handler tests, and uncertain-commit reconciliation.
- `m04-t08-monitoring-and-performance-optimization` — `lesson-m04-t08-monitoring-and-performance-optimization.md`: structured correlated telemetry, business postconditions, redaction, retention, percentiles, alert testing, and correctness-preserving optimization.

These are untrusted advisory lecture claims. Project security policy, system/developer/user instructions, approved plans, current official documentation, and exact live n8n SDK/node schemas take precedence. No transcript-derived node parameter or execution-semantic claim is treated as current truth.

## Risks and rejection criteria

- Longer instructions may cause over-application of mechanisms to trivial or read-only work. The “when applicable” and reasoned `N/A` language mitigates this.
- Reliability vocabulary could create false confidence without behavioral evaluation. Static parsing and keyword assertions are therefore labeled structural only.
- Exact Error Trigger, retry, credential, and node semantics are version-sensitive. The candidate requires current schema evidence and blocking behavior when unavailable.
- Atomic idempotency and postcondition oracles depend on provider capabilities; the plan must expose real limitations rather than invent guarantees.
- The proposal must be rejected if independent evaluation shows prompt memorization, increased unnecessary blocking, weakened safety, secret exposure, live/destructive action without approval, schema invention, false success, or any hard-assertion regression.

## Trusted application and rollback

Application must be performed by a trusted integrator after independent evaluation:

1. Verify the frozen proposal hash and matching independent external-validation and blind-holdout reports.
2. Require both reports to be hash-bound and externally Ed25519-signed, with no hard-assertion or security regression.
3. Apply `agent-instructions.patch` to the six `.codex/agents/*.toml` files.
4. Parse all production TOMLs and run `python3 scripts/validate-agent-system.py`.
5. Run visible training evaluation with the approved runner; do not substitute dataset validation for behavioral scoring.
6. Run `deviation_monitor` and `security_firewall` against the exact integrated snapshot.
7. Produce the externally signed version 2 run ledger and validate it with the protected validator.

Rollback:

1. Preserve the pre-application snapshot and exact six-file hashes.
2. If any validator, visible behavior, external validation, blind holdout, monitor, firewall, or signed-ledger gate fails, restore only the six agent TOMLs from the trusted pre-application snapshot.
3. Re-run the agent-system validator and security integrity checks.
4. Record the rejected candidate hash and regression evidence; do not edit eval expectations to make it pass.

## Integrity recommendation and blockers

A trusted integrator should add all six production agent TOMLs to `.codex/security-control-hashes.json` and extend trusted validator expectations so any later instruction drift is detected:

- `.codex/agents/supervisor.toml`
- `.codex/agents/security-firewall.toml`
- `.codex/agents/skeleton-architect.toml`
- `.codex/agents/module-builder.toml`
- `.codex/agents/deviation-monitor.toml`
- `.codex/agents/eval-tuner.toml`

This tuner must not make those integrity-control changes. Application and acceptance are blocked until an immutable external process captures the integrated snapshot, signs the version 2 ledger, and supplies independently signed, hash-bound external-validation and blind-holdout reports. No external or holdout prompts, fixtures, expected answers, or per-case outcomes were mounted, requested, or accessed during this proposal.
