# Self Improvement Test Fixtures

Focused tests create temporary fixture trees for:

- a valid local candidate that remains externally blocked;
- stale baselines and production hash drift;
- protected or nonallowlisted targets;
- traversal, symlinks, hard links, extra files, and duplicate targets;
- secrets, NUL bytes, oversized content, and malformed UTF-8;
- every specified secret signature, with rejection output checked for non-disclosure;
- oversized signal and evidence artifacts;
- unknown or missing manifest fields and hash mismatches;
- unknown, missing, or incorrectly typed fields in every closed schema;
- mismatched metric definitions, suites, runs, snapshots, and case counts;
- boolean-only, unsigned, or malformed external evidence;
- missing, mismatched, or replayed approval receipts;
- approval receipts with a non-null local consumption record;
- n8n mutations, capability approvals, network actions, and dependency changes;
- missing rollback bindings and interrupted artifact writes.
- rollback fields inconsistent with the frozen not-applied state.

Fixtures must not contain real secrets, private evaluation cases, or executable candidate content.
