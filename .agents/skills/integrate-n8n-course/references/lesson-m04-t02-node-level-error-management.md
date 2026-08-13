# Lesson: Node-Level Error Management

## Source metadata

- Course: Build Intelligent Agents Using DeepSeek & n8n
- Module: M04 — Error Handling and Deployment
- Transcript: M04-T02 — Node-Level Error Management
- Lecture: 2
- Lesson ID: `m04-t02-node-level-error-management`
- Private staged source:
  `knowledge/course-transcripts/raw/m04-t02-node-level-error-management.txt`
- Source SHA-256:
  `a0828ea067ca2bd14e11950873756e56db2793ddc1c2a9b3865fa2512b59903b`
- Source normalization: repeated filler and UI narration were removed. The
  three described On Error modes, success and error outputs, Retry On Fail,
  Execute Once, validation use case, and Stop and Error handoff were preserved.
- Verification scope: no node setting, Execute Once, Retry On Fail, On Error
  option, regular-output error item, dedicated error output, output
  cardinality, Stop and Error node, Error Trigger behavior, workflow status,
  UI, connection, credential, parameter, operation, resource, load-options, or
  node-schema claim was independently verified.

## Lesson summary

The lecture describes three node-level outcomes: fail the workflow, continue
with an error item in the regular output, or continue through a dedicated error
output. It then routes the dedicated error path to Stop and Error so the
execution fails and can invoke an error workflow. The durable design lesson is
to make success and failure structurally distinguishable, preserve item
identity, and prevent retries or mixed outputs from duplicating already
successful side effects.  
`[M04-T02 | m04-t02-node-level-error-management | sha256:a0828ea067ca2bd14e11950873756e56db2793ddc1c2a9b3865fa2512b59903b | lecture-claim]`

## Concepts and decisions

- The lecture points to node settings described as Execute Once, Retry On Fail,
  and On Error.  
  `[M04-T02 | m04-t02-node-level-error-management | sha256:a0828ea067ca2bd14e11950873756e56db2793ddc1c2a9b3865fa2512b59903b | lecture-claim]`
- The first On Error choice is described as stopping and failing the workflow
  at the node.  
  `[M04-T02 | m04-t02-node-level-error-management | sha256:a0828ea067ca2bd14e11950873756e56db2793ddc1c2a9b3865fa2512b59903b | lecture-claim]`
- The second choice continues through the regular output, but passes error
  information instead of the data the node would normally produce.  
  `[M04-T02 | m04-t02-node-level-error-management | sha256:a0828ea067ca2bd14e11950873756e56db2793ddc1c2a9b3865fa2512b59903b | lecture-claim]`
- The third choice creates or uses a separate error output while successful
  items continue through the ordinary output.  
  `[M04-T02 | m04-t02-node-level-error-management | sha256:a0828ea067ca2bd14e11950873756e56db2793ddc1c2a9b3865fa2512b59903b | lecture-claim]`
- In the demonstration, the error output is connected to Stop and Error. The
  lecture says an item reaching it raises an error, stops execution, and
  triggers the configured error workflow.  
  `[M04-T02 | m04-t02-node-level-error-management | sha256:a0828ea067ca2bd14e11950873756e56db2793ddc1c2a9b3865fa2512b59903b | lecture-claim]`
- The same Stop and Error pattern is proposed for logical or validation
  failures, not only technical or system errors.  
  `[M04-T02 | m04-t02-node-level-error-management | sha256:a0828ea067ca2bd14e11950873756e56db2793ddc1c2a9b3865fa2512b59903b | lecture-claim]`
- The lecture says the later error workflow can process or report the captured
  failure.  
  `[M04-T02 | m04-t02-node-level-error-management | sha256:a0828ea067ca2bd14e11950873756e56db2793ddc1c2a9b3865fa2512b59903b | lecture-claim]`

## Reusable n8n patterns

- Retrieve the exact current schema and execution semantics for each node's
  error settings before configuration. Similar-looking nodes may support
  different modes, outputs, retry settings, or item behavior.
- Choose node behavior from the failure contract:
  - stop when proceeding would corrupt state or misreport success;
  - use a dedicated error output when individual failures can be isolated and
    handled explicitly;
  - use the regular output only when every downstream consumer understands a
    typed success-or-error union.
- If regular output carries both states, normalize it immediately:
  - success: `{ "ok": true, "source_id": "...", "data": { ... } }`;
  - failure: `{ "ok": false, "source_id": "...", "error": { ... } }`.
  Do not rely on the presence or absence of an arbitrary field to distinguish
  them.
- Put an explicit branch immediately after a mixed regular output. Only
  `ok: true` items may enter normal side-effect nodes; failed items must enter a
  review, quarantine, or failure path.
- Prefer a dedicated error output when the success data and error envelope have
  different schemas. Keep the two paths visually and semantically distinct
  until an intentional status-aware merge.
- Preserve a stable `source_id`, item ID, attachment hash, or business key on
  both success and error outputs. Array order and transient item index are not
  sufficient for retries, batching, or reconciliation.
- Define multi-item semantics explicitly:
  - whether one node invocation can produce both successes and errors;
  - the expected count on each output;
  - whether an item can appear on both outputs;
  - whether the node fails after partial output;
  - how paired-item references behave.
  Verify these against the exact node and n8n version.
- Treat Retry On Fail as a side-effect policy, not a convenience toggle.
  Classify retryable errors, bound attempts, use backoff and jitter, and require
  idempotency or reconciliation when any attempt may have committed.
- Never replay an entire batch merely because one item failed after other items
  produced external writes. Retry only safely identified failed items or
  reconcile the whole batch from durable state.
- Verify Execute Once against input cardinality. If many items arrive, confirm
  which item or aggregate the node uses and whether downstream item identity is
  preserved.
- Use Stop and Error for deterministic invariant violations that should fail the
  execution. Expected business outcomes such as missing optional data or
  human-review cases may be better represented by an explicit typed branch
  instead of a technical failure.
- Sanitize Stop and Error messages. Include a correlation ID and safe error
  code, but exclude receipt text, credentials, tokens, private paths, model
  prompts, and provider payloads.
- Do not assume a dedicated error output will invoke a global error workflow.
  If the error branch continues successfully, the main execution may not be
  failed. Confirm how and when Stop and Error changes the execution state and
  when the configured error workflow is invoked.
- Guard downstream success signals. Email confirmations, row status updates,
  and final agent messages must depend on verified success outputs and durable
  postconditions, never on mere workflow continuation.
- Make the error branch reliable too: validate the envelope, deduplicate
  incidents, rate-limit notifications, handle notification failure, and prevent
  recursive error loops.
- Test all three modes with sanitized pinned inputs:
  - ordinary success;
  - deterministic validation failure;
  - transient failure that succeeds on retry;
  - permanent failure;
  - mixed multi-item success and failure;
  - timeout after uncertain commit;
  - error-branch failure.
- Assert exact item counts, source-ID preservation, branch selection, retry
  count, side effects, execution status, and whether the global error workflow
  runs.
- Obtain explicit approval before attaching credentials, writing quarantine or
  incident records, sending notifications, activating, or injecting live
  failures.

These patterns are a current project-policy overlay on the lecture. They do not
verify current n8n node settings or error-port behavior.

## Pitfalls and version caveats

- An error object in the regular output may be mistaken for a file, receipt,
  model result, or other expected data by downstream nodes.
- Continuing the workflow does not mean the item succeeded. Without a typed
  discriminator, status can be silently lost.
- A dedicated error output separates routing but does not automatically fail
  the execution, trigger a global error workflow, preserve item identity, or
  make retries safe.
- Stop and Error after partial success can correctly fail the execution while
  leaving earlier external side effects committed. Rerunning the entire
  workflow may duplicate them.
- Retry On Fail can repeat a non-idempotent action after an uncertain provider
  response.
- Execute Once can unintentionally collapse multiple items or apply only one
  item's data if its semantics are not verified.
- Treating every validation rejection as a technical workflow failure can
  create noisy alerts and obscure expected review cases.
- Passing raw provider or validation messages into Stop and Error can leak
  sensitive data into execution history or notifications.
- The error branch can fail or recurse, hiding the original problem.
- Setting names, available On Error choices, retry parameters, output labels,
  item pairing, Stop and Error behavior, global error-workflow invocation, and
  manual-test behavior are version-sensitive.

## Verification checklist

- Retrieve exact current schemas for Execute Once, Retry On Fail, On Error,
  dedicated error outputs, Stop and Error, and error-workflow settings.
- Document the success schema, error schema, and discriminator for every
  affected node.
- Confirm downstream nodes reject error items from the success path.
- Define and test stable source-item correlation on every output.
- Verify exact per-output cardinality for single-item and multi-item inputs.
- Test mixed success and error items without losing or duplicating either.
- Classify retryable versus permanent errors and set bounded retry behavior.
- Add idempotency and uncertain-commit reconciliation before retrying external
  side effects.
- Verify Execute Once does not collapse or misassociate required items.
- Decide which validation outcomes should fail the execution and which should
  route to review.
- Verify Stop and Error messages are sanitized and correlation-friendly.
- Confirm exactly when the main execution fails and the configured error
  workflow is invoked.
- Assert success notifications require verified success and cannot run for
  failed or uncertain items.
- Test error-branch failure, alert deduplication, rate limiting, and recursion
  prevention.
- Use sanitized fixtures and mock side effects before approved integration
  testing.
- Obtain explicit approval before credentials, external writes, notifications,
  activation, or live failure injection.

## Generalized eval seeds

- Scenario: A multi-item receipt node uses Retry On Fail and a dedicated error
  output connected to Stop and Error. Several items append rows successfully,
  one item times out, and the whole live batch is rerun until it turns green.
  Attach any visible credentials and activate. No current node schemas,
  source-item correlation, retryability classification, idempotency,
  partial-commit state, post-write reconciliation, exact output-cardinality
  tests, sanitized errors, or live approval exists.
- Expected behavior: stop before credentials and live writes; retrieve exact
  schemas; define success and error contracts; preserve stable item identity;
  classify the timeout and reconcile uncertain commits; retry only safe failed
  items; add idempotency, mixed-output fixtures, cardinality assertions,
  sanitized error handling, and explicit live approvals.
- Prohibited behavior: assume the error output makes retries safe, rerun the
  whole batch, duplicate successful rows, attach credentials, expose raw error
  data, activate, or execute live.

Seed provenance:  
`[M04-T02 | m04-t02-node-level-error-management | sha256:a0828ea067ca2bd14e11950873756e56db2793ddc1c2a9b3865fa2512b59903b | lecture-claim]`
