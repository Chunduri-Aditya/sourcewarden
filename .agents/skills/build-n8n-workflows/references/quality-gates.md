# n8n workflow quality gates

Read `config/agent-policy.yaml` before creating or editing a workflow. Apply stricter user or organizational requirements when supplied.

## 1. Compatibility

- Identify the target n8n version.
- Prefer live node definitions from that instance.
- Never copy parameters from a different node version without verification.
- Record community-node dependencies explicitly.

## 2. Node configuration

- Retrieve exact node types and discriminators.
- Validate required parameters and display-option branches.
- Use resource IDs rather than display names when the node requires IDs.
- Keep credentials as credential references.
- Check expressions for valid node names and reachable upstream data.

## 3. Graph correctness

- Include an appropriate trigger.
- Ensure required inputs are connected.
- Remove accidental disconnected nodes.
- Check branch output indices and merge semantics.
- Check loops for termination, pagination, and item preservation.
- Preserve unrelated graph structure during edits.

## 4. Reliability

Add only the mechanisms required by the task:

- retry transient failures;
- respect rate limits;
- paginate collections;
- deduplicate non-idempotent writes;
- define behavior for empty inputs;
- route permanent failures;
- prevent duplicate alerts or records on retry.

## 5. Security

- Never embed secrets.
- Use least-privilege credentials.
- Treat public webhooks, destructive methods, arbitrary code, shell/SSH, filesystem access, and sensitive data as elevated risk.
- Keep the workflow unpublished during development.
- Sanitize fixtures and execution evidence.

## 6. Testing

Test at least:

1. expected input;
2. empty, duplicate, boundary, or malformed input relevant to the task;
3. one external-service or transformation failure.

Use pin data for credentialed and external nodes. Allow logic nodes to execute so expressions, transformations, branches, and error behavior are actually tested.

Do not use mock testing as permission to execute credential-free shell or filesystem nodes. Disable or isolate them instead.

## 7. Handoff

Provide:

- validation status and warnings;
- test inputs and outcomes;
- credential types and unresolved resource selections;
- publication state;
- explicit next approval, if any.

