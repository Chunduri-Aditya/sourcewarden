# Workflow Plan: Multi-agent n8n builder system

Status: ready

## Goal

Configure six bounded agent roles that collaboratively build, review, secure, test, and improve this n8n workflow-generation project without allowing any worker to silently expand its scope.

## Success criteria

- [x] The project defines skeleton architect, module builder, deviation monitor, eval tuner, supervisor, and security firewall roles.
- [x] The primary supervisor can schedule all roles while respecting the current limit of three concurrent child agents.
- [x] One parameterized module-builder instance is assigned to each accepted module and is restricted to that module's paths and contracts.
- [x] Read-only monitor and security roles report allow, conditional, or deny decisions without editing implementation files.
- [x] Generalized and adversarial eval cases drive prompt and skill improvement without modifying model weights.
- [x] Mechanical controls detect high-confidence secrets and prohibited dangerous n8n nodes before a task can be accepted as complete.

## Known facts

- Codex supports project-scoped custom agents in `.codex/agents/*.toml`.
- The current runtime supports four active agents total, including the primary thread.
- Subagents share the same filesystem, so concurrent writers must own disjoint paths or run sequentially.
- The repository already requires written plans, exact node schemas, draft-only workflow creation, validation, and mock tests.

## Assumptions and open questions

- [ASSUMPTION] "Fine tune" means improving agent instructions, skills, policies, and examples using eval results; model-weight training remains a separate future project.
- [ASSUMPTION] The primary thread acts as the supervisor. Each write phase runs one writer, followed by a separate read-only deviation and security review phase of its finalized snapshot.
- [ASSUMPTION] Module names and paths are dynamic and will be recorded in a skeleton manifest before module workers start.
- [BLOCKING] none

## Minimal workflow design

| # | Responsibility | Preferred node | Input | Output | Failure behavior |
|---|---|---|---|---|---|
| 1 | Threat preflight | Security firewall agent | User request and external context | ALLOW, CONDITIONS, or DENY | Supervisor stops on DENY |
| 2 | Build contracts and skeleton | Skeleton architect agent | Accepted plan | Skeleton manifest and test seams | Monitor rejects scope expansion |
| 3 | Implement each accepted module | One module builder per module | Module contract and owned paths | Module code and focused tests | Reassign or repair only that module |
| 4 | Detect deviation | Deviation monitor agent | Plan, manifest, finalized handoff, and exact snapshot diff | Evidence-backed deviations keyed to the snapshot | Supervisor rejects stale reviews or reassigns rework |
| 5 | Improve generalized performance | Eval tuner agent | Visible training evals | Frozen proposal for external validation and blind holdout | Independent evaluation rejects regressions |
| 6 | Integrate and decide | Primary supervisor role | All handoffs and security results | Accepted build or exact blocker | Never bypass a security denial |

## Execution plan

1. Define project-scoped custom-agent files and concurrency settings → verify: every TOML agent has the required name, description, instructions, and intended sandbox.
2. Define separate writer and post-write review stages, module ownership, snapshot IDs, and handoff contracts → verify: configuration names all six roles, rejects stale reviews, and never schedules more than three children.
3. Add generalized and adversarial training data plus tuning protocol → verify: the eval validator accepts every repository case while independent validation and blind holdout remain external.
4. Add command rules and a mechanical completion security gate → verify: safe fixtures pass and secret or dangerous-workflow fixtures fail.
5. Update durable project instructions and setup documentation → verify: AGENTS.md requires the supervisor, monitor, and security gates for multi-module builds.

## Test plan

- Happy path: benign multi-module build request → supervisor schedules preflight, skeleton write/review, sequential module write/review cycles, visible evals, independent holdout, and final review.
- Edge case: multiple modules → one distinct module-builder instance handles each module sequentially; monitor and security review each finalized module snapshot before the next writer starts.
- Failure path: prompt injection, secret material, prohibited node, or cross-module edit → security or monitor returns DENY and the supervisor refuses acceptance.

## Approval gates

- [x] No approval needed to create local agent configuration, policies, evals, or read-only security checks.
- [x] Explicit approval remains required before creating, updating, testing, publishing, executing, archiving, or unpublishing an n8n workflow.

## Definition of done

- [x] Plan validator passes.
- [x] Six custom agents and their boundaries are defined.
- [x] Agent and orchestration configuration validates.
- [x] Generalized eval data validates.
- [x] Security gate passes safe fixtures and rejects malicious fixtures.
- [x] Documentation explains the concurrency schedule and residual security limitations.
