# Planning protocol

Use this protocol for every non-trivial n8n build or edit. It adapts four planning behaviors: expose assumptions, minimize the design, limit change scope, and attach verification to each step.

## Decision rules

### Ask or assume

Ask before building when an unknown changes:

- the trigger or schedule;
- the system of record;
- recipient, destination, or external side effect;
- destructive versus additive behavior;
- data sensitivity or authorization boundary;
- deduplication identity;
- acceptable failure behavior;
- production publication.

Make a labeled reversible assumption when it affects only names, layout, draft metadata, fixture values, or another easily changed choice.

### Keep the design minimal

Include a node only when it maps to a success criterion, required data transformation, explicit failure path, or necessary platform boundary. Do not add speculative configuration, generic abstraction, or unused branches.

### Keep edits surgical

For an existing workflow:

1. State which nodes, connections, or settings must change.
2. State which behavior must remain unchanged.
3. Prefer targeted update operations.
4. Retest the changed path and any directly affected error path.

## Plan template

```markdown
# Workflow Plan: <name>

Status: draft

## Goal

<One observable outcome.>

## Success criteria

- [ ] <Observable behavior with expected result.>
- [ ] <Failure or edge behavior with expected result.>

## Known facts

- <Fact supplied by the user or discovered from the target instance.>

## Assumptions and open questions

- [ASSUMPTION] <Reversible assumption and why it is safe.>
- [OPEN] <Non-blocking question, if any.>
- [BLOCKING] none

## Minimal workflow design

| # | Responsibility | Preferred node | Input | Output | Failure behavior |
|---|---|---|---|---|---|
| 1 | <trigger> | <exact type after discovery> | <data> | <data> | <behavior> |

## Execution plan

1. <Discover exact nodes and schemas> → verify: <evidence>
2. <Configure and connect the minimal workflow> → verify: <evidence>
3. <Validate and create the draft> → verify: <evidence>
4. <Run mock tests and repair> → verify: <evidence>

## Test plan

- Happy path: <input> → <expected output and side effect>
- Edge case: <input> → <expected output>
- Failure path: <failure> → <expected retry, branch, or alert>

## Approval gates

- [ ] No approval needed before draft creation.
- [ ] Explicit approval required before <publish/live/destructive action>.

## Definition of done

- [ ] Plan validator passes.
- [ ] Exact node schemas were used.
- [ ] Node and workflow validation pass.
- [ ] Mock tests satisfy the success criteria.
- [ ] Credentials and remaining manual setup are documented.
- [ ] Workflow remains a draft unless publication was explicitly approved.
```

## Plan readiness

Set `Status: ready` only when:

- no unresolved `[BLOCKING]` item remains;
- success criteria are observable;
- each execution step has a `verify:` check;
- tests cover happy, edge, and failure paths;
- approval boundaries are explicit.

