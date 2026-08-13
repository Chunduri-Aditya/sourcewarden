# Workflow Plan: Scheduled lead alert

Status: ready

## Goal

Send one Slack alert for each new qualified lead found by the scheduled run.

## Success criteria

- [ ] A qualified lead produces exactly one sanitized Slack message.
- [ ] A duplicate lead produces no second message.
- [ ] A Slack failure follows the documented retry and error path.

## Known facts

- The workflow runs on a schedule and uses credential references.

## Assumptions and open questions

- [ASSUMPTION] Fixture IDs are synthetic and reversible.
- [BLOCKING] none

## Minimal workflow design

| # | Responsibility | Preferred node | Input | Output | Failure behavior |
|---|---|---|---|---|---|
| 1 | Start the workflow | Schedule Trigger | Schedule | Run item | Stop on invalid schedule |
| 2 | Send the alert | Slack | Qualified lead | Message result | Retry then error path |

## Execution plan

1. Discover exact nodes and schemas → verify: type definitions match the target instance.
2. Configure and connect the workflow → verify: node validation passes.
3. Validate and create the draft → verify: workflow validation passes and draft URL exists.
4. Run mock tests and repair → verify: all three test cases satisfy expected outcomes.

## Test plan

- Happy path: one qualified lead → one Slack message.
- Edge case: duplicate lead ID → no second Slack message.
- Failure path: simulated Slack error → retry and error route.

## Approval gates

- [ ] No approval needed before draft creation.
- [ ] Explicit approval required before publishing or live execution.

## Definition of done

- [ ] Plan validator passes.
- [ ] Exact node schemas were used.
- [ ] Node and workflow validation pass.
- [ ] Mock tests satisfy the success criteria.
- [ ] Credentials and remaining manual setup are documented.
- [ ] Workflow remains a draft unless publication was explicitly approved.

