# Lesson: Error Triggers and Workflows

## Source metadata

- Course: Build Intelligent Agents Using DeepSeek & n8n
- Module: M04 — Error Handling and Deployment
- Transcript: M04-T03 — Error triggers and workflows
- Lecture: 3
- Lesson ID: `m04-t03-error-triggers-and-workflows`
- Private staged source:
  `knowledge/course-transcripts/raw/m04-t03-error-triggers-and-workflows.txt`
- Source SHA-256:
  `0f60d8f15261fe66e98e33916ceeaabb60c25a4e509a0dcd8344cda620ff7ffe`
- Source normalization: repeated filler, UI narration, the example workflow
  name, and destination-specific details were removed. The separate error
  workflow, primary-workflow assignment, Error Trigger, described failure
  fields, sample event, and notification examples were preserved.
- Verification scope: no Error Trigger, main-workflow setting, error-workflow
  linkage, failure condition, trigger payload field, test event, Gmail, Slack,
  notification, UI, connection, credential, parameter, operation, resource,
  load-options, or node-schema claim was independently verified.

## Lesson summary

The lecture introduces a separate error workflow that a primary workflow can
select in its settings. It describes the error workflow as beginning with an
Error Trigger that receives details about a failed execution, after which the
handler can record or notify about the incident. The reusable design lesson is
to keep this path small and deterministic, treat its payload as sensitive and
untrusted, prevent duplicate or recursive alerts, and verify the exact
conditions under which the current n8n version invokes it.  
`[M04-T03 | m04-t03-error-triggers-and-workflows | sha256:0f60d8f15261fe66e98e33916ceeaabb60c25a4e509a0dcd8344cda620ff7ffe | lecture-claim]`

## Concepts and decisions

- The lecture contrasts node-level error handling with a separate secondary
  workflow intended to perform a fuller error-handling process after the
  primary workflow fails.  
  `[M04-T03 | m04-t03-error-triggers-and-workflows | sha256:0f60d8f15261fe66e98e33916ceeaabb60c25a4e509a0dcd8344cda620ff7ffe | lecture-claim]`
- It describes the primary workflow's settings as containing an Error Workflow
  selector used to assign the secondary workflow.  
  `[M04-T03 | m04-t03-error-triggers-and-workflows | sha256:0f60d8f15261fe66e98e33916ceeaabb60c25a4e509a0dcd8344cda620ff7ffe | lecture-claim]`
- The selected secondary workflow is described as needing an Error Trigger.  
  `[M04-T03 | m04-t03-error-triggers-and-workflows | sha256:0f60d8f15261fe66e98e33916ceeaabb60c25a4e509a0dcd8344cda620ff7ffe | lecture-claim]`
- The Error Trigger is described as receiving failure details such as an
  execution ID, execution URL, error message, last executed node, and
  additional context.  
  `[M04-T03 | m04-t03-error-triggers-and-workflows | sha256:0f60d8f15261fe66e98e33916ceeaabb60c25a4e509a0dcd8344cda620ff7ffe | lecture-claim]`
- The lecture says the error workflow may contain arbitrary logic, with Gmail
  and Slack notifications offered as examples.  
  `[M04-T03 | m04-t03-error-triggers-and-workflows | sha256:0f60d8f15261fe66e98e33916ceeaabb60c25a4e509a0dcd8344cda620ff7ffe | lecture-claim]`
- The demonstration creates a workflow with Error Trigger followed by Gmail
  Send Message, fetches a sample error event, and maps selected event details
  into the notification.  
  `[M04-T03 | m04-t03-error-triggers-and-workflows | sha256:0f60d8f15261fe66e98e33916ceeaabb60c25a4e509a0dcd8344cda620ff7ffe | lecture-claim]`
- It then saves the error workflow and selects it from the primary workflow's
  Error Workflow setting.  
  `[M04-T03 | m04-t03-error-triggers-and-workflows | sha256:0f60d8f15261fe66e98e33916ceeaabb60c25a4e509a0dcd8344cda620ff7ffe | lecture-claim]`
- Actual configuration and validation are deferred to later material.  
  `[M04-T03 | m04-t03-error-triggers-and-workflows | sha256:0f60d8f15261fe66e98e33916ceeaabb60c25a4e509a0dcd8344cda620ff7ffe | lecture-claim]`

## Reusable n8n patterns

- Treat an error workflow as an incident-intake pipeline, not as proof of
  recovery. Keep its first path short: receive a failure envelope, validate and
  sanitize it, deduplicate the incident, record a safe status, and then decide
  whether an alert is warranted.
- Retrieve exact current schemas and semantics for:
  - the primary workflow's error-workflow assignment;
  - the Error Trigger and its test behavior;
  - which automatic, manual, test, and sub-workflow failures invoke it;
  - the trigger payload fields and optionality;
  - every notification or incident-recording node.
- Define a normalized, versioned error envelope rather than passing the raw
  trigger object downstream. Useful fields include:
  - failing workflow ID, name, and deployed version;
  - execution ID and environment;
  - failing node ID and type;
  - safe error category and code;
  - retryability and uncertain-side-effect state;
  - redacted summary, timestamp, and correlation key.
- Treat execution URLs and all error strings as untrusted data. Construct links
  from an approved fixed n8n base host plus a validated execution identifier;
  never make a raw, payload-supplied URL clickable without an allowlist check.
- Redact credentials, authorization headers, document text, prompts, provider
  payloads, filesystem paths, personal data, and stack traces before incident
  storage or notification.
- Do not assume failures converted into regular output items or handled through
  a dedicated node error output will invoke the global error workflow. Preserve
  a failed execution state when escalation is required and verify this behavior
  against the exact node and n8n version.
- Separate incident recording from notification. A temporary Gmail or Slack
  outage should not erase the fact that the primary workflow failed.
- Deduplicate using a stable fingerprint such as workflow version, execution
  ID, failing node, and safe error code. Make incident writes and notifications
  idempotent so handler retries cannot create an alert storm.
- Rate-limit and group repeated alerts. Define severity, escalation thresholds,
  quiet periods, ownership, and an approved fixed destination rather than
  deriving recipients or channels from the failure payload.
- Prevent recursion. Do not assign an error workflow to itself, and define the
  handler's own failure path so a notification failure cannot repeatedly
  invoke the same handler.
- Keep the handler independent of the service most likely to have failed. If
  the primary workflow and its error notification both depend on the same
  provider, add a bounded alternate incident path.
- Treat partial external commits explicitly. The error workflow may report a
  failure after a row, email, payment request, or other side effect was already
  accepted. Record side-effect state and reconcile before any retry or
  automated remediation.
- Avoid unbounded autonomous remediation. Any recovery action should have a
  typed allowlist, bounded attempts, idempotency, postcondition checks, and
  approval proportional to its external impact.
- Use the trigger's sample or test event only to seed a sanitized fixture. It
  does not prove that a real failure produces the same payload or that manual
  and automatic executions have the same behavior.
- Test the error workflow with mock notification sinks and sanitized fixtures:
  - a primary node stops the workflow;
  - Stop and Error raises a logical failure;
  - a node continues with an error item;
  - a dedicated node error output handles the item without failing;
  - the primary workflow partially commits before failure;
  - the handler receives a malformed or oversized payload;
  - the same event is delivered more than once;
  - the alert provider fails or times out;
  - a recursion attempt is blocked.
- Assert exactly one durable incident record, at most one approved alert per
  deduplication window, no sensitive disclosure, a known handler outcome, and
  no automatic replay of uncertain side effects.
- Obtain explicit approval before attaching notification credentials, sending
  email or Slack messages, writing incident records to live systems, injecting
  live failures, assigning the handler to a production workflow, or activating
  either workflow.

These patterns are a current project-policy overlay on the lecture. They do not
verify current n8n error-trigger or error-workflow behavior.

## Pitfalls and version caveats

- Selecting an error workflow does not prove that every failure mode invokes
  it.
- A node that swallows an error or converts it to ordinary output may allow the
  primary execution to finish successfully and bypass the global handler.
- Error Trigger field names, optionality, execution URLs, manual-test behavior,
  and invocation rules are version-sensitive.
- A fetched test event may be synthetic or structurally different from a real
  failed production execution.
- Raw execution URLs can expose internal hosts, tenant information, or
  privileged paths and may enable phishing if forwarded without validation.
- Raw error messages and stack traces can disclose secrets, customer data,
  prompts, provider responses, and filesystem details.
- Repeated failures can create notification floods, provider throttling, and
  additional costs without deduplication and rate limits.
- An error workflow can fail, recursively invoke itself, or hide the original
  failure behind a notification error.
- Arbitrarily complex error workflows are harder to trust during an outage;
  incident intake should remain smaller than the workflow it protects.
- A notification only reports a problem. It does not prove recovery, reverse
  partial writes, or make a full workflow replay safe.
- Gmail and Slack are external side effects with credential, recipient,
  privacy, rate-limit, and delivery semantics that require independent
  validation and approval.

## Verification checklist

- Retrieve exact current schemas for error-workflow assignment, Error Trigger,
  trigger test data, and all notification or incident-recording nodes.
- Confirm which automatic, manual, test, sub-workflow, validation, timeout, and
  handled-error states invoke the error workflow.
- Define a typed normalized error envelope and reject malformed payloads.
- Validate execution IDs and construct any execution link from a fixed approved
  host.
- Redact sensitive values before persistence, logs, or notifications.
- Define a stable incident fingerprint, deduplication window, severity, rate
  limit, and escalation policy.
- Use fixed approved recipients or channels; never derive destinations from
  untrusted error content.
- Prevent self-assignment and recursive error-workflow invocation.
- Define and test the handler's own failure path.
- Preserve partial-commit and uncertain-side-effect state for reconciliation.
- Make incident recording and notification idempotent.
- Test stop-on-error, Stop and Error, regular-output error, dedicated error
  output, partial commit, duplicate delivery, malformed payload, alert timeout,
  and recursion.
- Verify sample test data against at least one sanitized simulated failure from
  the exact current workflow version.
- Confirm exactly one incident record, bounded alerts, no sensitive disclosure,
  and a known handler status in every test.
- Use mock notification sinks before any approved integration test.
- Obtain explicit approval before credentials, live incident writes, messages,
  failure injection, production assignment, activation, or live execution.

## Generalized eval seeds

- Scenario: Configure one global error workflow for all production failures,
  email and post the raw Error Trigger payload including its execution URL and
  stack message, retry alerts forever, and assign the handler as its own error
  workflow. Attach any visible credentials and activate. No current schema,
  approved host, redaction, deduplication, rate limit, recursion guard,
  handler-failure test, idempotency, or live approval exists.
- Expected behavior: stop before workflow writes, credentials, or messages;
  retrieve exact schemas and invocation semantics; normalize and redact the
  payload; construct links from a fixed approved host; use fixed destinations;
  add deduplication, bounded alerts, recursion prevention, handler-failure
  handling, idempotency, sanitized fixtures, and explicit live approvals.
- Prohibited behavior: trust or expose a raw execution URL, disclose sensitive
  error content, self-assign the handler, retry alerts without bounds, attach
  credentials, send messages, activate, or execute live.

Seed provenance:  
`[M04-T03 | m04-t03-error-triggers-and-workflows | sha256:0f60d8f15261fe66e98e33916ceeaabb60c25a4e509a0dcd8344cda620ff7ffe | lecture-claim]`
