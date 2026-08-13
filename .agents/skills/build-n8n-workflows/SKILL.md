---
name: build-n8n-workflows
description: Plan, create, edit, validate, test, debug, review, export, and safely publish n8n workflows from natural-language requests. Use for any task involving n8n workflow design, node selection or configuration, expressions, credentials, connections, workflow JSON or SDK code, MCP workflow tools, mock executions, error handling, or production readiness.
---

# Build n8n workflows

Own the complete request-to-working-draft loop. Apply Karpathy-style discipline: surface assumptions, choose the smallest design, make surgical changes, and drive every step with a verification criterion.

## 1. Frame the goal

1. Inspect any existing workflow, plan, fixture, and project policy relevant to the request.
2. State the requested outcome in one sentence.
3. Separate:
   - known facts;
   - reversible assumptions;
   - open questions;
   - blocking unknowns that would materially change behavior, security, or external effects.
4. Ask only blocking questions. Continue with clearly labeled reversible assumptions when safe.
5. Push back when the requested automation is infeasible, unsafe, or substantially simpler another way.

## 2. Retrieve source-grounded planning context

Before writing a non-trivial plan, run the repository RAG adapter from the project root:

```bash
python3 scripts/retrieve-rag-context.py --query "<workflow request>" --top-k 5 --pretty
```

Use official documentation evidence to ground behavior and constraints. Use community workflow evidence only as a candidate pattern. Record useful source URLs in the plan. Live schemas from the target n8n instance override all retrieved documentation and examples. If no indexed evidence is returned, label the evidence gap and continue only with facts that can be verified from the target instance or project policy.

## 3. Produce a verifiable plan

For every non-trivial build or edit:

1. Read [planning-protocol.md](references/planning-protocol.md).
2. Create or update `plans/<workflow-slug>.md`.
3. Give every execution step a `verify:` condition.
4. Define happy-path, edge-case, and failure-path tests before workflow mutation.
5. Run:

```bash
node .agents/skills/build-n8n-workflows/scripts/validate-plan.mjs --ready plans/<workflow-slug>.md
```

Do not mutate an n8n workflow while the plan contains an unresolved `[BLOCKING]` item.

## 4. Discover exact capabilities

When the n8n instance-level MCP tools are available:

1. Call `get_sdk_reference` before building.
2. Call `get_workflow_best_practices` for the relevant technique when available.
3. Search native nodes with `search_nodes`.
4. Retrieve exact parameter types with `get_node_types` before configuring nodes.
5. Resolve existing credentials with `list_credentials`; never request or expose their secret values.
6. Use `explore_node_resources` only when a credential-backed dropdown value must be resolved.

If MCP is unavailable, inspect schemas from packages pinned to the target n8n version or a workflow exported from that exact version. Otherwise stop after the plan and report the missing connection instead of inventing node configuration.

## 5. Design the smallest workflow

1. Prefer native nodes.
2. Use HTTP Request only when a native operation cannot satisfy the requirement.
3. Use a Code node only for logic that ordinary nodes or expressions cannot express clearly.
4. Propose a custom node only for recurring unsupported behavior.
5. Include only the trigger, transformations, branches, side effects, and failure handling required by the success criteria.
6. Add retries, pagination, rate-limit handling, idempotency, or deduplication only when the task actually needs them.
7. Keep credentials out of parameters and artifacts.

When editing an existing workflow, retrieve it first and use the smallest targeted update. Preserve unrelated nodes, connections, positions, comments, settings, and credentials.

## 6. Validate before saving

Read [quality-gates.md](references/quality-gates.md), then:

1. Validate individual node configurations with `validate_node_config` when available.
2. Validate complete Workflow SDK code with `validate_workflow`.
3. Resolve every error.
4. Treat warnings as findings: fix them or explain why they are acceptable.
5. Do not create or update a workflow that fails validation.

## 7. Create a draft and prove it

1. Create an unpublished workflow with `create_workflow_from_code`, or apply atomic targeted changes with `update_workflow`.
2. Prepare schemas with `prepare_test_pin_data`.
3. Generate sanitized realistic fixtures.
4. Run `test_workflow`.
5. Inspect execution evidence.
6. Repair and repeat until the success criteria pass or a genuine blocker is established.

Do not mock logic nodes that need verification. Do not run shell, SSH, filesystem, destructive HTTP, or other side-effecting nodes during a mock test.

## 8. Hand off and publish safely

Report:

- workflow name, location, and link or export path;
- implemented behavior;
- assumptions;
- required credential types and manual setup;
- validation results and warnings;
- test cases and results;
- remaining risks or approval gates.

Publish or activate only when the user explicitly requests it after reviewing the draft. Run a live execution only with explicit approval and suitable non-production test data.

## Completion standard

Declare completion only when every checked success criterion is supported by validation or execution evidence. If blocked, name the exact missing fact, credential, capability, or approval and preserve the valid draft work.
