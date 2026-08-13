# n8n Workflow System

This repository combines the source-cited multi-RAG workflow builder with the planning, orchestration, validation, and security controls of the n8n workflow generator.

| Area | Location | Responsibility |
|---|---|---|
| Workflow engineering | repository root | Plans, agent roles, policy, security gates, evaluations, and generated workflow JSON |
| Retrieval and citations | `n8n_rag_system/` | Official documentation, node guidance, community examples, routing, citations, and deterministic fallback planning |
| Integration adapter | `scripts/retrieve-rag-context.py` | Bounded JSON evidence for every non-trivial workflow plan |

Evidence has one explicit precedence order: live target-instance schemas, official documentation, community workflow examples, then untrusted course references. Documentation and examples inform the plan but never prove an exact node parameter for the target instance.

Validate the complete project from the repository root:

```bash
python3 scripts/validate-project.py
```

This validates repository security controls without pretending that an externally signed run ledger exists. Live n8n mutations still require the separate signed ledger and approval flow documented below.

Retrieve planning evidence:

```bash
python3 scripts/retrieve-rag-context.py \
  --query "Build a webhook that validates input and returns the weather" \
  --top-k 5 \
  --pretty
```

Local RAG indexes live under `n8n_rag_system/data/indexes/` and are Git ignored. See [`n8n_rag_system/README.md`](n8n_rag_system/README.md) for collection, indexing, retrieval, and evaluation commands.

The workflow agent owns the full loop:

1. Clarify material ambiguity.
2. Define measurable success criteria.
3. Design the smallest viable workflow.
4. Retrieve exact node types from the target n8n instance.
5. Validate node configurations and workflow structure.
6. Create an unpublished draft.
7. Test it with sanitized mock data.
8. Repair failures and report evidence.
9. Publish only after explicit approval.

The planning discipline is adapted from the four principles in [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills): surface assumptions, keep the solution simple, make surgical changes, and execute against verifiable goals.

## Multi-agent architecture

The primary thread acts as supervisor and schedules six logical roles. Project defaults keep the primary filesystem read-only; local elevation and every n8n mutation remain approval-gated.

| Role | Responsibility | Write access |
|---|---|---|
| `supervisor` | Decompose work, assign ownership, enforce gates, accept or reject | Read-only |
| `security_firewall` | Threat preflight and final allow/deny review | Read-only |
| `skeleton_architect` | Create shared contracts, module manifest, stubs, and test seams | Workspace |
| `module_builder` | One fresh agent instance per manifest module | Assigned module by contract |
| `deviation_monitor` | Compare plans, ownership, diffs, and evidence | Read-only |
| `eval_tuner` | Propose instruction improvements from generalized evals | Proposal/result paths |

Only one module builder writes at a time. Once its handoff and snapshot are final, the deviation monitor and security firewall review that exact snapshot before the next writer starts. This respects the current three-child limit, avoids concurrent writes, and prevents reviewers from racing ahead of writers.

Custom roles are spawned with `fork_turns = "none"` and a self-contained assignment prompt. This is required because full-history forks inherit the parent agent type instead of loading the selected role definition.

Agent definitions live in `.codex/agents/`; scheduling and handoff gates live in `config/agent-orchestration.json`.

## Prerequisites

- Codex with repository skills support.
- An n8n Cloud or self-hosted instance. n8n 2.27 or newer is recommended for the complete MCP workflow-building toolset.
- Instance-level MCP enabled in n8n.

The local skill works without the official n8n skills plugin, but installing [n8n-io/skills](https://github.com/n8n-io/skills) adds detailed node and workflow guidance maintained by n8n.

## Connect Codex to n8n

In n8n, open **Settings → Instance-level MCP**, enable access, and copy the MCP server URL. OAuth is preferred. For access-token authentication:

1. Merge the n8n block from `.codex/config.toml.example` into the existing `.codex/config.toml`.
2. Replace the example host with the MCP URL shown by n8n.
3. Set `N8N_MCP_TOKEN` in the environment that launches Codex.
4. Validate the active configuration with `python3 scripts/validate-n8n-config.py`.
5. Restart Codex.

Never place the token directly in repository files.

Every custom child agent disables the inherited `n8n` MCP server and removes token-, secret-, password-, and key-shaped variables from its shell environment. The primary thread alone uses the allowlisted n8n tools, retrieves sanitized schemas, and performs approval-gated n8n mutations after child output passes review.

Project hooks require a one-time trust review. After restarting Codex, open `/hooks`, inspect `.codex/hooks.json`, and trust it. The completion hook runs from sandbox-protected `.codex/hooks/`, fails closed on scan errors, verifies protected-control hashes, and scans canonical workflow JSON for high-confidence secrets and prohibited capabilities. The n8n PreToolUse hook blocks create, update, test, publish, execute, unpublish, or archive unless the exact tool input and reviewed artifact hash appear in the externally signed current ledger.

## Activate signed orchestration

Agents and workspace code must never possess the signing private key. Use an immutable external broker, CI service, or HSM-backed signer whose executable and event capture are outside every agent-writable path:

1. Generate the Ed25519 keypair entirely outside the workspace. For example, from a secured external runner:

   ```bash
   umask 077
   openssl genpkey -algorithm ED25519 -out /secure/n8n-ledger-private.pem
   openssl pkey -in /secure/n8n-ledger-private.pem -pubout \
     -out /secure/n8n-ledger-public.pem
   ```

2. Compute the SHA-256 fingerprint of the complete public-key file, pin it as `WORKFLOW_TRUST_ROOT_SHA256` in the managed environment that launches Codex and the evaluator, then install only the public key as `.codex/agent-ledger-public-key.pem`. The gates fail closed if the environment pin is absent or mismatched.
3. Let the external broker capture lifecycle events and complete workspace snapshots. Snapshot IDs are SHA-256 hashes of recursively key-sorted canonical JSON file-hash maps; exclude only `artifacts/agent-runs/` and `.codex/authorization-consumption/`.
4. Have that broker assemble and sign the version 2 ledger. It must include the frozen manifest hash, ordered lifecycles, snapshot chain, post-write and final reviews, a sequenced supervisor verdict, and any exact n8n authorization inputs.
5. For each n8n call, bind the exact tool-input hash, session ID, reviewed workflow artifact, explicit approval scope, a strong one-time nonce, `issuedAt`, and a `validUntil` no more than 15 minutes later. The protected hook atomically consumes the nonce before the call.
6. Promote the signed ledger to `artifacts/agent-runs/current.json`, then validate it with `node scripts/validate-agent-run.mjs artifacts/agent-runs/current.json`.

Do not run a workspace copy of any key-generation, capture, canonicalization, or signing utility with the production private key. Until the pinned public key and a matching signed current ledger exist, the Stop and n8n mutation hooks intentionally deny by default.

## Use

Ask for the outcome in ordinary language:

> Every weekday at 8 AM, get new high-priority HubSpot deals, deduplicate them, append them to Google Sheets, and alert Slack. Retry transient failures and send a failure notification.

For non-trivial work, the agent creates `plans/<name>.md` first. Validate a plan directly with:

```bash
node .agents/skills/build-n8n-workflows/scripts/validate-plan.mjs --ready plans/<name>.md
```

The final handoff includes the workflow link or JSON, required credentials, assumptions, test fixtures, validation results, and any remaining approval gates.

Validate the agent system and generalized eval data with:

```bash
python3 scripts/validate-agent-system.py
node scripts/validate-generalized-evals.mjs
node scripts/validate-generalized-evals.mjs --external /secure/private-cases.jsonl
node scripts/grade-agent-eval.mjs --self-test
node scripts/validate-agent-run.mjs --self-test
node .codex/hooks/security-gate.mjs --self-test
node .codex/hooks/security-gate.mjs
```

## Safety defaults

- Draft-only creation.
- Credential references instead of secret values.
- Mock testing before external calls.
- Explicit approval for publishing and live execution.
- Extra review for destructive requests, public webhooks, shell/SSH, filesystem operations, and arbitrary Code nodes.
- Code, Data Table, and Execute Workflow nodes pass the static scanner only through an exact externally signed capability approval bound to the reviewed artifact and integrated snapshot.

The security agent is defense in depth, not a mathematical guarantee against prompt injection. The local sandbox protects `.codex` controls, and this project explicitly disables known inherited child MCP/app surfaces, but higher-precedence settings can still disable project hooks. Production-grade assurance requires a managed hook and external broker, separate module worktrees or containers, an immutable merge gate, a non-production n8n instance without production credentials, and network egress controls outside the agents' writable environment.
