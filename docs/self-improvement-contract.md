# Self Improvement Contract

## Trust boundary

The project may generate and inspect challengers. It cannot promote itself. Candidate content, feedback, training requests, and evaluation output are untrusted data.

Production application remains outside the workspace because the target instructions and the controls that authorize them share the same local trust boundary. A local apply command would let a compromised tuner change both behavior and its evidence.

## Command contract

| Command | Allowed effect | Forbidden effect |
|---|---|---|
| `record` | Append one validated, secret-free feedback signal to the ignored inbox | Interpret feedback as authority or edit training cases |
| `prepare` | Freeze baseline hashes and initialize run directories | Generate a candidate or access external suites |
| `validate-candidate` | Validate manifest, files, hashes, TOML invariants, evidence shape, approval binding, and rollback metadata | Apply candidate bytes or treat local results as promotion proof |
| `status` | Report deterministic readiness and blockers | Mutate any artifact |

## Paths

- Feedback inbox: `evals/feedback/inbox/<signal-id>.json`
- Baseline: `evals/results/<run-id>/baseline.json`
- Candidate manifest: `tuning/proposals/<run-id>/candidate-manifest.json`
- Candidate files: `tuning/proposals/<run-id>/proposed/`
- Local assessment: `evals/results/<run-id>/local-assessment.json`
- External approval receipt input: `evals/results/<run-id>/approval-receipt.json`

Run IDs match `^[a-z0-9][a-z0-9._-]{2,63}$`. Every resolved path must remain under its expected root and must not be a symlink.

Each signal is a closed-schema JSON object created with exclusive file creation. The recorder is the user or primary supervisor. `eval_tuner` may read signals only as untrusted failure evidence and cannot write, rewrite, or delete them.

## Shared encoding and hashing rules

Every JSON artifact is UTF-8 without a byte order mark and is limited to 262144 bytes, except the smaller signal limit below. Parsing rejects duplicate object keys, trailing content, `NaN`, infinities, and booleans in integer fields. Closed schema means every listed key is required unless its type explicitly permits `null`, and no unlisted key is accepted. A canonical JSON value is encoded with keys sorted by Unicode code point, commas and colons as the only separators, no insignificant whitespace, UTF-8 non-ASCII characters preserved, and integers written in base 10 without leading zeros. Schemas used for signed data contain no floating-point values, so Python and the external verifier share byte-exact numeric encoding. Every SHA-256 value is lowercase hexadecimal. A snapshot ID is the prefix `sha256:` followed by a SHA-256 value.

Files are read through descriptor-based, no-follow opens after path containment checks. Every component is rejected if it is a symlink, and post-open identity checks must match the opened descriptor to the expected path. The final object must be a regular file and its link count must be one. Candidate Markdown is limited to 131072 bytes. A signal file is limited to 16384 bytes. Any NUL byte is blocking.

Secret detection is deterministic. Recording and candidate validation reject text matching any of these rules:

- A PEM private-key header matching `-----BEGIN(?: [A-Z0-9]+)? PRIVATE KEY-----`.
- An authorization value matching `(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}`.
- A named credential matching `(?i)\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|password|passwd|secret)\b\s*[:=]\s*[\"']?[A-Za-z0-9_./+=-]{8,}`.
- An AWS access-key identifier matching `\bAKIA[0-9A-Z]{16}\b`.
- A GitHub token matching `\bgh[pousr]_[A-Za-z0-9]{20,}\b`.
- An OpenAI style token matching `\bsk-[A-Za-z0-9_-]{20,}\b`.

Rejection output names the matched rule only. It never echoes the matched value.

## Feedback signal schema

Each feedback file has exactly this shape:

```json
{
  "schemaVersion": 1,
  "signalId": "64-hex",
  "source": "user",
  "category": "incorrect-node-selection",
  "summary": "1 to 500 Unicode scalar values",
  "expectedBehavior": "1 to 2000 Unicode scalar values",
  "contentDigest": "64-hex"
}
```

`source` is `user` or `supervisor`. `category` is one of `incorrect-node-selection`, `missing-error-handling`, `invalid-configuration`, `weak-explanation`, `citation-gap`, or `evaluation-regression`. `contentDigest` is the canonical SHA-256 of the literal object `{"source": <source>, "category": <category>, "summary": <summary>, "expectedBehavior": <expectedBehavior>}`. `signalId` equals `contentDigest`. The file name is `<signalId>.json`; exclusive creation makes duplicate or concurrent recording fail closed.

## Baseline schema

`baseline.json` has exactly this shape:

```json
{
  "schemaVersion": 1,
  "runId": "strict-run-id",
  "gitCommit": "40-hex-commit",
  "snapshotId": "sha256:64-hex",
  "trainingCorpusSha256": "64-hex",
  "policySha256": "64-hex",
  "feedbackSignals": [
    {"signalId": "64-hex", "sha256": "64-hex"}
  ],
  "targetHashes": {
    "allowlisted/production/path.md": "64-hex"
  }
}
```

Feedback entries are sorted by signal ID and targets are sorted by production path. The snapshot ID is the canonical SHA-256 of the complete object with `snapshotId` omitted. Preparation requires a completely clean Git worktree and binds every allowlisted target, every valid feedback file present at preparation time, and `evals/generalized-cases.jsonl` as the visible training corpus. `policySha256` is the SHA-256 of the exact raw bytes of `self_improvement/policy.json`; changing whitespace changes the hash. An empty feedback list is valid.

Candidate validation permits Git status entries only under the exact active run directories `tuning/proposals/<run-id>/` and `evals/results/<run-id>/`, plus the ignored feedback inbox. Any other modified, deleted, renamed, copied, or untracked path is a dirty-worktree blocker. The validator independently verifies that the current commit and every production target still match the frozen baseline.

## Tunable targets

The initial allowlist contains only nonsecurity generation prompts:

- `n8n_rag_system/prompts/system_n8n_workflow_architect.md`
- `n8n_rag_system/prompts/node_selection_prompt.md`
- `n8n_rag_system/prompts/workflow_recipe_template.md`

Candidates are UTF-8 Markdown text. Binary data, embedded NUL bytes, secrets, symlinks, hard-linked aliases, unexpected files, and content above the policy size limit are rejected.

Every agent definition, skill, project policy, orchestration file, hook, rule, grader, validator, eval definition, expected result, trust root, security hash manifest, script, source file, and workflow artifact is excluded from self tuning.

## Candidate manifest

The candidate manifest uses this closed JSON shape:

```json
{
  "schemaVersion": 1,
  "runId": "strict-run-id",
  "baseline": {
    "gitCommit": "40-hex-commit",
    "snapshotId": "sha256:64-hex",
    "trainingCorpusSha256": "64-hex",
    "policySha256": "64-hex",
    "targetHashes": {
      "allowlisted/production/path.md": "64-hex"
    }
  },
  "proposalDigest": "64-hex",
  "targets": [
    {
      "productionPath": "allowlisted/production/path.md",
      "candidatePath": "proposed/path.md",
      "beforeSha256": "64-hex",
      "candidateSha256": "64-hex"
    }
  ],
  "metrics": {
    "definitionSha256": "64-hex",
    "baselineArtifactPath": "evals/results/run/baseline-metrics.json",
    "baselineArtifactSha256": "64-hex",
    "candidateArtifactPath": "evals/results/run/candidate-metrics.json",
    "candidateArtifactSha256": "64-hex"
  },
  "rollback": {
    "candidateIdentifier": "64-hex",
    "approvalIdentifier": null,
    "sourceSnapshotId": "sha256:64-hex",
    "intendedIntegratedSnapshot": null,
    "targetBeforeHashes": {
      "allowlisted/production/path.md": "64-hex"
    },
    "targetAfterHashes": {
      "allowlisted/production/path.md": "64-hex"
    },
    "validationEvidence": [],
    "status": "NOT_APPLIED"
  }
}
```

`candidatePath` is exactly `proposed/<productionPath>` and cannot use an alternate name. `proposalDigest` is the canonical SHA-256 of the literal object `{"runId": <runId>, "baselineSnapshotId": <snapshotId>, "targets": <targets>}`, where `<targets>` is the manifest target array sorted by `productionPath` with every target retaining exactly its four documented keys. `candidateIdentifier` equals `proposalDigest`. Before integration, `approvalIdentifier` and `intendedIntegratedSnapshot` are `null`, `validationEvidence` is an empty array, and status is `NOT_APPLIED`. A trusted integrator records non-null approval and integrated snapshot identifiers plus evidence hashes in its separate, signed integration ledger; it does not rewrite the frozen candidate manifest.

Metric artifact paths are exact and run-bound. `baselineArtifactPath` must equal `evals/results/<run-id>/baseline-metrics.json`, and `candidateArtifactPath` must equal `evals/results/<run-id>/candidate-metrics.json`. Alternate names, absolute paths, and cross-run paths are blocking.

Unknown fields, missing fields, duplicate targets, extra files, binary files, traversal, symlinks, secrets, stale production hashes, and immutable TOML changes are blocking.

## Evaluation rule

Local validation is useful for iteration but never proves promotion safety. External baseline and candidate metrics must use the same hash-bound suites and metric definitions. Every hard and security assertion must remain at 100 percent. Any protected category regression, invalid signature, mismatched run or snapshot, different suite hash, boolean-only claim, missing case count, or objective score below policy is blocking.

Each metric artifact has exactly this shape:

```json
{
  "schemaVersion": 1,
  "receiptType": "candidate-metrics",
  "runId": "strict-run-id",
  "baselineSnapshotId": "sha256:64-hex",
  "proposalDigest": "64-hex",
  "metricDefinitionSha256": "64-hex",
  "suiteSha256": "64-hex",
  "caseCount": 1,
  "hardAssertions": {"passed": 1, "total": 1},
  "securityAssertions": {"passed": 1, "total": 1},
  "objectiveScoreMicros": 1000000,
  "protectedCategoryScoreMicros": {"category-name": 1000000},
  "signerKeyId": "external-key-id",
  "signatureAlgorithm": "Ed25519",
  "signatureBase64": "base64"
}
```

`receiptType` is `baseline-metrics` or `candidate-metrics` according to the referenced file. Counts and scores are integers and cannot be booleans. Totals and `caseCount` are positive, passed counts are between zero and total, score values range from 0 through 1000000 inclusive, and protected categories use nonempty names. Both receipts must match the candidate run, baseline snapshot, proposal digest, metric definition, suite, case count, and protected-category key set. Both hard and security passed counts must equal their totals. Candidate objective score must be at least the baseline score and the policy floor of 800000 micros. Every candidate protected-category score must be at least its baseline score.

The signed payload is the canonical JSON object with `signatureBase64` omitted. A signature field is never reduced to a boolean claim.

Python standard library code cannot verify Ed25519 evidence. The local validator therefore checks only closed-schema shape, paths, hashes, bindings, and deterministic metric relationships, then reports cryptographic verification as an external blocker. It never labels a candidate promotion ready. The trusted external evaluator verifies canonically serialized Ed25519 receipts against `.codex/agent-ledger-public-key.pem` and the managed `WORKFLOW_TRUST_ROOT_SHA256` pin.

The external validation and blind holdout suites remain unmounted from tuner sessions. Only aggregate, signed evidence may return after the candidate is frozen.

`local-assessment.json` has exactly this implementation-owned output shape:

```json
{
  "schemaVersion": 1,
  "runId": "strict-run-id",
  "structuralStatus": "VALID",
  "promotionStatus": "BLOCKED_EXTERNAL_INTEGRATOR",
  "proposalDigest": "64-hex or null",
  "checks": [
    {"code": "stable-code", "status": "PASS", "detail": "nonsecret detail"}
  ],
  "blockers": [
    {"code": "EXTERNAL_SIGNATURE_VERIFICATION_REQUIRED", "detail": "nonsecret detail"}
  ]
}
```

`structuralStatus` is `VALID` or `INVALID`; check status is `PASS` or `FAIL`. Check and blocker entries use exactly `code`, `status` when applicable, and `detail`. Entries are sorted by code. The output contains no timestamp so the same inputs produce identical bytes. The external signature and approval blockers are always present even when structural status is valid.

## Approval and rollback

Approval is not supplied by the candidate manifest. A separate externally signed approval receipt must be one time, explicit, canonically serialized, and bound to the baseline snapshot, candidate digest, full target set, promotion scope, nonce, and consumption record. Supervisor acceptance alone is insufficient. Workspace code reports the receipt as externally unverified and cannot consume it.

The external approval receipt may be supplied only at the fixed path `evals/results/<run-id>/approval-receipt.json`. `validate-candidate --run-id <run-id>` has no alternate receipt argument. If the file is absent, it reports approval as missing. If present, it validates only the following closed shape and candidate bindings, then still reports external signature verification and nonce consumption as blockers.

The external approval receipt has exactly this shape:

```json
{
  "schemaVersion": 1,
  "receiptType": "promotion-approval",
  "runId": "strict-run-id",
  "baselineSnapshotId": "sha256:64-hex",
  "proposalDigest": "64-hex",
  "targetSetDigest": "64-hex",
  "scope": "APPLY_ALLOWLISTED_PROMPTS",
  "nonce": "unique-nonce",
  "consumption": {"status": "UNCONSUMED", "recordId": null},
  "signerKeyId": "external-key-id",
  "signatureAlgorithm": "Ed25519",
  "signatureBase64": "base64"
}
```

`targetSetDigest` is the canonical SHA-256 of the literal array `[{"productionPath": <path>, "candidateSha256": <hash>}, ...]` sorted by `productionPath`. The signed payload omits `signatureBase64`. Workspace validation accepts only `UNCONSUMED` with a null record ID as a well-formed input, still reports external verification as blocking, and has no command that can consume the nonce. The trusted integrator owns the one-time consumption record.

Rollback metadata must bind verified pre-apply bytes or immutable blob references, all before and after hashes, candidate and approval identifiers, the intended integrated snapshot, validation evidence, and rollback state. A trusted integrator must restore the verified baseline automatically if any post-apply check fails.

## Terminal status

The local validator always reports `BLOCKED_EXTERNAL_INTEGRATOR` for promotion. Removing this terminal blocker requires a separate human directed security design change and cannot be proposed by the tuner.
