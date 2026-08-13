# Self Improvement System Contract

Status: implemented, local promotion remains blocked

## Goal

Let the project capture failure signals, freeze a reproducible baseline, and validate bounded instruction candidates without allowing workspace code to promote its own changes.

## Constraints

- Python standard library only.
- Feedback and candidate files are untrusted data and are never executed.
- The tuner may write only under `tuning/proposals/<run-id>/` and `evals/results/<run-id>/`.
- The `record` command is invoked by the user or primary supervisor, never by `eval_tuner`; it writes one immutable signal file under the ignored feedback inbox.
- External validation and blind holdout content never enters the workspace or tuner context.
- No live n8n call, network access, dependency installation, credential access, or capability approval is allowed during tuning.
- Agent definitions, skills, security policy, hooks, rules, graders, validators, expected results, orchestration, and trust roots are not tunable targets.
- Production application is disabled. A trusted external integrator remains required.

## Success criteria

- [x] A strict CLI records secret-free feedback as explicitly untrusted signals.
- [x] Baseline preparation binds the Git commit, training corpus, policy, target files, and feedback signal identifiers by SHA-256.
- [x] Every JSON boundary follows the closed schemas, canonical encoding, exact size limits, and deterministic secret rules in the contract.
- [x] Candidate validation rejects stale baselines, unsafe paths, symlinks, extra files, secrets, and protected targets.
- [x] Candidate validation requires exact before and candidate hashes plus rollback metadata.
- [x] Evaluation checks reject unsigned, mismatched, boolean-only, incomplete, or regressing evidence using integer-only signed metric values.
- [x] Status remains `BLOCKED_EXTERNAL_INTEGRATOR`; workspace code has no apply or promote command.
- [x] Adversarial unit tests cover the implemented rejection boundaries.
- [x] The complete project validation remains green after final control-hash regeneration.

## Contract

The implementation module owns only:

- `self_improvement/`
- `tests/self_improvement/`

Shared policy and security surfaces remain maintainer owned. The CLI entry point is:

```bash
python3 -m self_improvement <command>
```

Supported commands are `record`, `prepare`, `validate-candidate`, and `status`.

## Failure modes

- Invalid or duplicate feedback returns a nonzero status without changing existing signals. Each signal uses exclusive file creation, so concurrent recorders cannot overwrite one another.
- A dirty or stale baseline blocks preparation or candidate validation.
- Any unrecognized manifest field or file blocks the candidate.
- Missing, malformed, mismatched, or cryptographically unverified external metrics, approval, replay-consumption, or rollback evidence blocks external integration readiness.
- A failed validation never changes production instructions.
- Interrupted writes use atomic replacement so the prior artifact remains intact.

## Verification

1. Validate the module manifest. Verify: owned paths are normalized, directory scoped, and disjoint.
2. Run focused unit tests. Verify: safe fixtures pass and every adversarial fixture fails closed.
3. Run `python3 scripts/validate-project.py`. Verify: all repository checks pass.
4. Run the repository security scan. Verify: protected controls remain hash bound and secret free.

## Approval boundary

This implementation prepares and validates candidates only. Applying candidate bytes to production prompt templates requires an externally signed tuning ledger, independently signed baseline and candidate metrics, an explicit one time approval bound to the candidate digest, final monitor and firewall reviews, trusted control hash regeneration, and a trusted external integrator.
