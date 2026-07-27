# Workflow Plan: Destructive CRM cleanup

Status: blocked

## Goal

Remove stale CRM contacts.

## Success criteria

- [ ] Only approved stale contacts are removed.

## Known facts

- Contact deletion is irreversible.

## Assumptions and open questions

- [BLOCKING] The user has not defined how a contact qualifies as stale.

## Minimal workflow design

| # | Responsibility | Preferred node | Input | Output | Failure behavior |
|---|---|---|---|---|---|
| 1 | Select stale contacts | CRM | Contacts | Candidate contacts | Stop |

## Execution plan

1. Resolve the deletion rule → verify: the user confirms the exact predicate.

## Test plan

- Happy path: approved stale contact → selected for dry-run review.
- Edge case: recent contact → excluded.
- Failure path: CRM request fails → no deletion and an error is reported.

## Approval gates

- [ ] Explicit approval required before deletion.

## Definition of done

- [ ] Deletion criteria and approval are documented.

