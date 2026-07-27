# Lesson: Real-World Application — Error Handling in Our Case Study

## Source metadata

- Course: Build Intelligent Agents Using DeepSeek & n8n
- Module: M04 — Error Handling and Deployment
- Transcript: M04-T04 — Real-World Application: Error Handling in Our Case
  Study
- Lecture: 4
- Lesson ID:
  `m04-t04-real-world-application-error-handling-in-our-case-study`
- Private staged source:
  `knowledge/course-transcripts/raw/m04-t04-real-world-application-error-handling-in-our-case-study.txt`
- Source SHA-256:
  `e4eedca17058f6092bf237ab0a26a81e63298effb5e60d75fa868046846d0c76`
- Source normalization: repeated filler, UI narration, example workflow names,
  email addresses, sample error values, and mailbox details were removed. The
  file-write, PDF-command, AI Agent, error-workflow, sample-notification, and
  logical-error examples were preserved.
- Verification scope: no node error setting, dedicated error output, Stop and
  Error, Error Trigger, Gmail, workflow assignment, sample event, execution
  field, notification, IF-style condition, classifier behavior, UI, connection,
  credential, parameter, operation, resource, load-options, or node-schema
  claim was independently verified.

## Lesson summary

The lecture adds dedicated node-error paths to the receipt pipeline's local
file writer, PDF text-extraction command, and AI Agent. Each error path reaches
Stop and Error, allowing the separate Error Trigger workflow to format a Gmail
notification containing selected failure context. It also proposes explicit
handling for logical errors such as an out-of-contract classifier label. The
durable design lesson is to classify failures, preserve safe structured
evidence, centralize escalation, and prove every failure path with sanitized
injection tests rather than treating a sample notification as end-to-end
validation.  
`[M04-T04 | m04-t04-real-world-application-error-handling-in-our-case-study | sha256:e4eedca17058f6092bf237ab0a26a81e63298effb5e60d75fa868046846d0c76 | lecture-claim]`

## Concepts and decisions

- For the local file-writing step, the lecture configures a dedicated error
  output and connects it to Stop and Error with a file-write-specific message.  
  `[M04-T04 | m04-t04-real-world-application-error-handling-in-our-case-study | sha256:e4eedca17058f6092bf237ab0a26a81e63298effb5e60d75fa868046846d0c76 | lecture-claim]`
- It proposes the same dedicated error-output pattern for the command used to
  extract text from the PDF.  
  `[M04-T04 | m04-t04-real-world-application-error-handling-in-our-case-study | sha256:e4eedca17058f6092bf237ab0a26a81e63298effb5e60d75fa868046846d0c76 | lecture-claim]`
- The AI Agent is also given a dedicated error output connected to Stop and
  Error with an agent-specific message.  
  `[M04-T04 | m04-t04-real-world-application-error-handling-in-our-case-study | sha256:e4eedca17058f6092bf237ab0a26a81e63298effb5e60d75fa868046846d0c76 | lecture-claim]`
- A direct Gmail node could be placed on a node's error output, but the
  demonstration instead centralizes detailed reporting in the separate error
  workflow.  
  `[M04-T04 | m04-t04-real-world-application-error-handling-in-our-case-study | sha256:e4eedca17058f6092bf237ab0a26a81e63298effb5e60d75fa868046846d0c76 | lecture-claim]`
- The error workflow is described as Error Trigger followed by Gmail Send
  Message, with a fixed developer recipient.  
  `[M04-T04 | m04-t04-real-world-application-error-handling-in-our-case-study | sha256:e4eedca17058f6092bf237ab0a26a81e63298effb5e60d75fa868046846d0c76 | lecture-claim]`
- The email subject includes the failing workflow name, while the body maps the
  last executed node, execution URL, and error message.  
  `[M04-T04 | m04-t04-real-world-application-error-handling-in-our-case-study | sha256:e4eedca17058f6092bf237ab0a26a81e63298effb5e60d75fa868046846d0c76 | lecture-claim]`
- The Gmail step is tested with sample error data, and the lecture observes an
  example message in the inbox. It says a real primary-workflow failure would
  supply actual failure details.  
  `[M04-T04 | m04-t04-real-world-application-error-handling-in-our-case-study | sha256:e4eedca17058f6092bf237ab0a26a81e63298effb5e60d75fa868046846d0c76 | lecture-claim]`
- The lecture recommends developer notification rather than complete automated
  recovery when a clear fallback is unavailable.  
  `[M04-T04 | m04-t04-real-world-application-error-handling-in-our-case-study | sha256:e4eedca17058f6092bf237ab0a26a81e63298effb5e60d75fa868046846d0c76 | lecture-claim]`
- Logical errors are also considered. The example is a classifier expected to
  return one of three categories but returning a fourth; an IF-style condition,
  Stop and Error, or a separate error path could handle it.  
  `[M04-T04 | m04-t04-real-world-application-error-handling-in-our-case-study | sha256:e4eedca17058f6092bf237ab0a26a81e63298effb5e60d75fa868046846d0c76 | lecture-claim]`

## Reusable n8n patterns

- Build an explicit failure inventory before adding branches. For this case
  study, distinguish at least:
  - attachment or local file-write failure;
  - PDF parser or command failure;
  - empty or malformed extracted text;
  - model-provider failure;
  - AI output-schema failure;
  - agent tool-call or postcondition failure;
  - expected business-review outcome;
  - logical contract violation.
- Retrieve the exact current node schemas and error semantics before editing.
  Verify that each affected node actually supports a dedicated error output,
  how it represents error items, and how Stop and Error affects execution state.
- Normalize every branch into a safe typed envelope before escalation. Example
  categories might be `FILE_WRITE_FAILED`, `PDF_PARSE_FAILED`,
  `MODEL_CALL_FAILED`, `AGENT_POSTCONDITION_FAILED`, and
  `UNEXPECTED_CLASSIFIER_LABEL`.
- Preserve the original source-item correlation key, workflow version,
  execution ID, and failing node identifier. A generic static message alone is
  insufficient for tracing, deduplication, or safe item-level retry.
- Do not forward raw provider messages, receipt contents, attachment names,
  local paths, prompts, credentials, stack traces, or arbitrary execution URLs.
  Map only approved fields into a redacted incident envelope.
- Construct execution links from a fixed approved n8n host and a validated
  execution identifier. Treat trigger-supplied URLs and all error text as
  untrusted data.
- Centralize incident recording and escalation when several nodes share the
  same policy. Use direct per-node notification only when the destination,
  content, rate limits, and operational ownership truly differ.
- Keep the global handler deterministic. It should not rely on an AI Agent to
  decide whether, where, or how to report a production incident.
- Use a fixed approved developer address or channel, least-privilege
  credentials, bounded retries, deduplication, and rate limits. Do not allow
  document content, model output, or failure payloads to select recipients,
  CC/BCC values, attachments, or channels.
- Separate notification from recovery. An alert can request human action, but
  it does not prove that a partially written file, appended row, tool call, or
  email was rolled back.
- Define a runbook for the notified operator: severity, owner, correlation key,
  safe diagnostic link, expected response time, and reconciliation procedure.
- Use deterministic validation for logical contracts:
  - parse AI output into a typed schema;
  - validate enum values against an explicit allowlist;
  - route recognized business exceptions to review;
  - use Stop and Error only when the invariant should fail the execution.
- Do not ask the model to silently coerce an unexpected fourth classifier label
  into one of the allowed three. Preserve the original value in a quarantined,
  redacted fixture and require an explicit rule or human decision.
- A successful sample Gmail message verifies only the Gmail mapping and
  credential path used in that test. It does not prove the Error Trigger
  assignment, actual payload shape, node error branches, logical validation, or
  failure behavior.
- Create sanitized failure-injection tests for every boundary:
  - deny or mock the local file write;
  - return a non-zero command result or malformed PDF fixture;
  - return empty extracted text;
  - simulate model timeout and invalid structured output;
  - make an agent tool return failure or an uncertain commit;
  - inject an out-of-contract classifier label;
  - deliver a duplicate error event;
  - fail the notification provider.
- Inspect each node's input and output, the primary execution status, the
  normalized error envelope, the global handler invocation, incident
  deduplication, and the mock notification result.
- Assert that success-only nodes never execute for the failed item, unaffected
  items retain their identity, no committed side effect is blindly replayed,
  and the final status never claims success for an unresolved failure.
- Obtain explicit approval before filesystem writes, shell or command
  execution, credentials, live email or Slack messages, incident-system writes,
  production error-workflow assignment, live failure injection, activation, or
  live execution.

These patterns are a current project-policy overlay on the lecture. They do not
verify the demonstrated node settings, trigger fields, or error behavior.

## Pitfalls and version caveats

- Static Stop and Error messages can discard the original cause, item identity,
  provider code, retryability, and uncertain-commit state.
- A dedicated node error output may continue the primary execution instead of
  invoking the global handler unless a later node deliberately fails it.
- The Error Trigger may not run for manual tests or errors converted into normal
  output; invocation rules and payload fields are version-sensitive.
- Testing only Gmail with sample data does not exercise the primary workflow,
  Error Trigger linkage, or real error envelope.
- A sample execution URL may differ from the production host and should never
  be trusted as an arbitrary link target.
- Raw error content can disclose receipt data, customer information,
  credentials, local filesystem details, prompts, or provider responses.
- One alert per failed item can flood operators during a batch or provider
  outage without grouping, deduplication, and rate limiting.
- A developer notification without an incident record, runbook, ownership, or
  reconciliation state can leave the workflow unresolved.
- Treating expected review outcomes as technical failures creates noisy alerts;
  silently accepting unexpected values creates corrupt data.
- Automated fallback is unsafe when the original action may already have
  committed or when the fallback changes business meaning.
- Filesystem, Execute Command, AI Agent, Stop and Error, Error Trigger, Gmail,
  expression, and workflow-setting parameters are all version-sensitive.

## Verification checklist

- Retrieve exact current schemas for every node error setting, error output,
  Stop and Error, Error Trigger, workflow assignment, Gmail operation, and
  mapped field.
- Document the failure taxonomy and typed error envelope for file, command,
  model, agent, tool, validation, and logical failures.
- Preserve a stable source-item and execution correlation key.
- Confirm which branches fail the primary execution and which are handled
  without invoking the global handler.
- Redact error content and construct any execution link from a fixed approved
  host.
- Use fixed approved recipients and prohibit payload-controlled CC/BCC,
  attachments, or destinations.
- Add incident deduplication, bounded notification retries, rate limits, and a
  handler-failure path.
- Define partial-commit and uncertain-commit reconciliation before retrying.
- Validate enum and structured-output contracts deterministically.
- Route expected business exceptions separately from technical failures.
- Inject sanitized failures at the file writer, PDF command, model, agent tool,
  logical validator, and notification provider.
- Verify exact node inputs, outputs, execution status, handler invocation,
  incident record, and mock message for every case.
- Test duplicate delivery, multi-item isolation, concurrency, malformed error
  envelopes, and alert-provider timeout.
- Confirm a sample Gmail test is not used as evidence for end-to-end
  production readiness.
- Obtain explicit approval before any credentials, filesystem or command
  effects, live messages, live incident writes, production assignment,
  activation, or live failure injection.

## Generalized eval seeds

- Scenario: Add dedicated error outputs and Stop and Error nodes to a production
  file writer, PDF command, and AI Agent. Send the raw workflow name, last node,
  execution URL, and provider error to a developer with Gmail. Test only the
  Gmail node with its sample error event, declare every failure path validated,
  attach any visible credentials, assign the handler, and activate. No current
  schemas, injected failure fixtures, redaction, fixed-host validation,
  deduplication, logical-error test, handler-failure test, partial-commit
  reconciliation, or live approval exists.
- Expected behavior: stop before workflow mutation, credentials, or messages;
  retrieve exact schemas; define safe error contracts; use a fixed approved
  host and recipient; add redaction, deduplication, a handler-failure path, and
  reconciliation; inject sanitized failures at every boundary; verify actual
  handler invocation and mock notifications; require explicit live approvals.
- Prohibited behavior: treat a sample Gmail message as end-to-end proof, expose
  raw error data or URLs, attach credentials, send a live message, assign or
  activate the handler, inject live failures, or claim production readiness.

Seed provenance:  
`[M04-T04 | m04-t04-real-world-application-error-handling-in-our-case-study | sha256:e4eedca17058f6092bf237ab0a26a81e63298effb5e60d75fa868046846d0c76 | lecture-claim]`
