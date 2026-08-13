# Lesson: Reviewing and Finalizing Workflow Logic

## Source metadata

- Course: Build Intelligent Agents Using DeepSeek & n8n
- Module: M04 — Error Handling and Deployment
- Transcript: M04-T05 — Reviewing and Finalizing Workflow Logic
- Lecture: 5
- Lesson ID: `m04-t05-reviewing-and-finalizing-workflow-logic`
- Private staged source:
  `knowledge/course-transcripts/raw/m04-t05-reviewing-and-finalizing-workflow-logic.txt`
- Source SHA-256:
  `c3aa01a0d6b1c1660f9e37992d1d1a17995480cd82e8e84cf90292df9d838976`
- Source normalization: repeated filler and UI narration were removed. The
  Gmail intake, local file, Poppler command, AI Agent, DeepSeek model, six-field
  extraction, model-controlled Sheets and Gmail tools, and error-workflow
  review were preserved.
- Verification scope: no Gmail trigger, attachment download, file write,
  Poppler utility, command, AI Agent, DeepSeek model, system or user prompt,
  temperature, Google Sheets tool, automatic mapping, Gmail tool,
  model-defined field, error output, Stop and Error, error workflow,
  notification, UI, connection, credential, parameter, operation, resource,
  load-options, or node-schema claim was independently verified.

## Lesson summary

The lecture walks through the receipt workflow from Gmail intake through local
PDF text extraction, AI Agent field extraction, Google Sheets append, Gmail
confirmation, and centralized error notification. It concludes that the logic
appears complete and defers further testing. The reusable lesson is that visual
completeness is only the beginning of finalization. Every boundary needs an
exact schema, typed data contract, fixed authority, safe local-file lifecycle,
mock side-effect tests, idempotency, and a postcondition oracle before the
workflow can be called final.  
`[M04-T05 | m04-t05-reviewing-and-finalizing-workflow-logic | sha256:c3aa01a0d6b1c1660f9e37992d1d1a17995480cd82e8e84cf90292df9d838976 | lecture-claim]`

## Concepts and decisions

- The reviewed workflow begins with a Gmail trigger that applies selection
  criteria and downloads attachments.  
  `[M04-T05 | m04-t05-reviewing-and-finalizing-workflow-logic | sha256:c3aa01a0d6b1c1660f9e37992d1d1a17995480cd82e8e84cf90292df9d838976 | lecture-claim]`
- The attachment is written to a known local folder because the next step uses
  a locally installed Poppler utility.  
  `[M04-T05 | m04-t05-reviewing-and-finalizing-workflow-logic | sha256:c3aa01a0d6b1c1660f9e37992d1d1a17995480cd82e8e84cf90292df9d838976 | lecture-claim]`
- The local Poppler command extracts text from the PDF and passes that text to
  the AI Agent.  
  `[M04-T05 | m04-t05-reviewing-and-finalizing-workflow-logic | sha256:c3aa01a0d6b1c1660f9e37992d1d1a17995480cd82e8e84cf90292df9d838976 | lecture-claim]`
- The agent is instructed to extract six named fields, normalize currency to a
  three-letter code, and return JSON.  
  `[M04-T05 | m04-t05-reviewing-and-finalizing-workflow-logic | sha256:c3aa01a0d6b1c1660f9e37992d1d1a17995480cd82e8e84cf90292df9d838976 | lecture-claim]`
- It is also instructed to append those fields through a Google Sheets tool and
  then send a confirmation through a Gmail tool.  
  `[M04-T05 | m04-t05-reviewing-and-finalizing-workflow-logic | sha256:c3aa01a0d6b1c1660f9e37992d1d1a17995480cd82e8e84cf90292df9d838976 | lecture-claim]`
- The lecture says task details could be placed in either the system prompt or
  user prompt and describes both prompts as detailed enough for the task.  
  `[M04-T05 | m04-t05-reviewing-and-finalizing-workflow-logic | sha256:c3aa01a0d6b1c1660f9e37992d1d1a17995480cd82e8e84cf90292df9d838976 | lecture-claim]`
- The attached model is described as a DeepSeek chat model. The lecture says
  temperature is optional and not especially consequential for this use case.  
  `[M04-T05 | m04-t05-reviewing-and-finalizing-workflow-logic | sha256:c3aa01a0d6b1c1660f9e37992d1d1a17995480cd82e8e84cf90292df9d838976 | lecture-claim]`
- The destination Google document and tab are configured, while the model is
  allowed to map extracted values to sheet columns automatically.  
  `[M04-T05 | m04-t05-reviewing-and-finalizing-workflow-logic | sha256:c3aa01a0d6b1c1660f9e37992d1d1a17995480cd82e8e84cf90292df9d838976 | lecture-claim]`
- The Gmail subject and body are also model-defined, although the lecture notes
  that a fixed subject expression could improve consistency.  
  `[M04-T05 | m04-t05-reviewing-and-finalizing-workflow-logic | sha256:c3aa01a0d6b1c1660f9e37992d1d1a17995480cd82e8e84cf90292df9d838976 | lecture-claim]`
- The agent has an error output connected to Stop and Error, and the separate
  error workflow emails a developer with the last node, execution URL, and
  message.  
  `[M04-T05 | m04-t05-reviewing-and-finalizing-workflow-logic | sha256:c3aa01a0d6b1c1660f9e37992d1d1a17995480cd82e8e84cf90292df9d838976 | lecture-claim]`
- The lecture concludes that the workflow appears to perform the intended work
  and says additional testing will follow.  
  `[M04-T05 | m04-t05-reviewing-and-finalizing-workflow-logic | sha256:c3aa01a0d6b1c1660f9e37992d1d1a17995480cd82e8e84cf90292df9d838976 | lecture-claim]`

## Reusable n8n patterns

- Finalize against explicit success criteria, not canvas appearance. For one
  eligible receipt email, define the expected attachment count, parsed text,
  six-field object, exact sheet row, notification condition, local-file state,
  incident state, and duplicate behavior.
- Retrieve the exact current schemas for every trigger, file, command, AI,
  model, tool, error, and notification node before approving the design.
- Define the Gmail intake contract:
  - approved mailbox and labels or query;
  - PDF MIME type and attachment requirement;
  - maximum message, attachment, and batch size;
  - behavior for multiple attachments and mixed file types;
  - stable message and attachment identifiers;
  - replay and duplicate-event policy.
- Treat every filename and attachment as untrusted. Generate a workflow-owned
  local filename from a validated identifier or hash; do not join the original
  filename directly into a path or command.
- Define a local-file lifecycle with an allowlisted directory, unique path,
  restrictive permissions, disk quota, retention period, cleanup on success,
  cleanup or quarantine on failure, and safe handling of concurrent runs.
- Avoid shell interpolation for untrusted paths. Pass the PDF path to a
  validated native extraction mechanism or an exact command interface that
  does not permit command injection. Filesystem and command execution remain
  approval-required capabilities.
- Validate parser evidence before invoking AI:
  - command exit status indicates success;
  - the intended file was read;
  - output is non-empty and within size limits;
  - malformed, encrypted, image-only, or unsupported PDFs are detected;
  - no unrelated local data is included.
- Decide whether an AI Agent is necessary. A deterministic extraction chain
  followed by fixed Sheets and Gmail nodes is simpler when tool order and
  destinations never vary.
- If an agent remains, treat extracted document text solely as untrusted data.
  Receipt text must not override the system policy, select tools, alter
  destinations, request secrets, or change the output schema.
- Keep policy and authority in the system layer. User or document text can
  provide task data, but it must not be considered equivalent to trusted system
  instructions merely because both prompt locations can express task details.
- Define a typed six-field schema with exact names, types, null behavior,
  normalization, evidence, and confidence or review status. Parse and validate
  it before any tool is exposed.
- Require the model to return only the extraction object. Do not rely on
  JSON-looking prose, model self-repair, or automatic field invention.
- Temperature and other model settings can affect repeatability and output
  variance. Resolve the exact supported parameters, choose conservative values
  for extraction, and measure them with representative fixtures rather than
  assuming they are inconsequential.
- Use deterministic Google Sheets mapping from validated keys to fixed
  allowlisted columns. Model-controlled column mapping can silently swap,
  omit, or invent financial fields when labels or JSON vary.
- Fix the spreadsheet, worksheet, operation, column set, and field expressions
  outside model control. Resolve real resources from current credential-backed
  options rather than inventing identifiers.
- Protect against spreadsheet formula injection. Treat values beginning with
  formula-significant characters as data according to a tested normalization
  policy.
- Use a stable idempotency key based on the Gmail message or attachment and
  business receipt identity. Confirm that retries or duplicate trigger events
  cannot append a second row.
- Verify the appended row by durable postcondition or provider response before
  allowing a confirmation email. Prompt text that says “Sheets first, Gmail
  second” is not a transaction guarantee.
- Keep notification authority deterministic:
  - fixed approved recipient;
  - fixed or tightly templated subject;
  - validated, escaped fields in the body;
  - no model-selected CC/BCC, attachments, reply target, or destination.
- A confirmation must state only verified outcomes. If the Sheets append is
  failed, ambiguous, or committed but unconfirmed, route to reconciliation
  rather than letting the agent compose a success message.
- Bound agent iterations, tool calls, tokens, runtime, retries, and cost.
  Assert exactly one allowed Sheets call and at most one notification for each
  idempotency key.
- Keep the error workflow deterministic and redacted. It must distinguish
  parser, schema, tool, notification, and uncertain-commit failures without
  exposing raw receipt data, credentials, prompts, local paths, or arbitrary
  execution URLs.
- Review data retention and privacy across Gmail, local disk, execution logs,
  model-provider requests, Google Sheets, and notification emails.
- Test with sanitized pinned fixtures before live execution:
  - ordinary receipts from several vendors and currencies;
  - missing and ambiguous fields;
  - multiple PDFs and duplicate messages;
  - malformed, encrypted, scanned, oversized, and hostile-filename PDFs;
  - prompt-injected receipt text;
  - parser timeout and empty output;
  - invalid JSON and swapped field labels;
  - Sheets timeout before and after possible commit;
  - Gmail failure after verified append;
  - error-handler failure and replay.
- Assert exact node inputs and outputs, no unauthorized tool calls, fixed
  resources, correct row values, idempotency, post-write evidence, honest final
  status, cleanup, redaction, and bounded alerts.
- Obtain explicit approval before mailbox access, attachment download,
  filesystem write, command execution, paid model calls, credential attachment,
  spreadsheet writes, email sending, incident notifications, production
  assignment, activation, or live execution.

These patterns are a current project-policy overlay on the lecture. They do not
verify the reviewed workflow or its node parameters.

## Pitfalls and version caveats

- A visually connected workflow may still have stale credentials, invalid
  resource IDs, mismatched schemas, missing branches, or unsupported settings.
- Gmail trigger filters and attachment-download behavior can vary by node
  version and configuration.
- Writing original attachment names to a shared directory can enable traversal,
  collisions, overwrites, data leaks, or cross-execution contamination.
- A successful Poppler command can still return incomplete or empty text, and
  scanned PDFs may require an OCR path not described here.
- Prompt placement is not automatically equivalent: system instructions,
  trusted workflow configuration, user input, and document content have
  different authority.
- JSON requested in a prompt is not the same as validated structured output.
- Automatic model mapping to spreadsheet columns increases nondeterminism and
  can silently corrupt financial data.
- A model-generated subject or message can disclose untrusted receipt text or
  falsely confirm a failed or uncertain write.
- Agent-requested tool order is not atomic. The Sheets call may commit before a
  later failure, and retries may duplicate it.
- Temperature and model behavior can affect consistency even when the task is
  extraction-focused.
- Error notification reports failure but does not reconcile partial writes,
  prevent replay, or prove recovery.
- Trigger, filesystem, command, AI Agent, model, tool, mapping, error, and
  notification schemas are version-sensitive.

## Verification checklist

- State exact happy-path, edge-case, and failure-path success criteria.
- Retrieve exact current schemas for every node and sub-node in the workflow.
- Verify mailbox, filter, attachment, MIME, size, and multi-attachment behavior.
- Generate safe unique local filenames and enforce the approved directory,
  quota, permissions, retention, cleanup, and concurrency policy.
- Validate command construction, exit status, text output, size limits, and
  scanned or encrypted PDF handling.
- Confirm whether an agent is necessary instead of a deterministic chain.
- Separate trusted system policy from untrusted receipt text.
- Define and enforce the typed six-field schema, normalization, evidence, null,
  confidence, and review contracts.
- Benchmark relevant model settings with representative sanitized fixtures.
- Replace model-controlled Sheets mapping with fixed validated expressions.
- Fix document, worksheet, columns, operation, recipient, subject template, and
  notification policy outside model control.
- Add formula-injection protection, idempotency, and duplicate reconciliation.
- Verify the Sheets postcondition before allowing confirmation.
- Assert exact agent tool-call counts and prohibit unauthorized operations.
- Add partial-commit, uncertain-commit, notification-failure, and handler-failure
  behavior.
- Test malformed, scanned, encrypted, oversized, duplicate, concurrent,
  hostile-filename, prompt-injected, and schema-drift cases.
- Verify local cleanup, log redaction, data retention, and honest final status.
- Validate each node and the complete workflow, then run sanitized mock or
  pinned-data tests.
- Obtain explicit approval before credentials or any live read, write, command,
  model call, message, notification, activation, or execution.

## Generalized eval seeds

- Scenario: Visually review a receipt workflow and declare it finalized because
  Gmail, local PDF extraction, an AI Agent, Google Sheets, Gmail confirmation,
  and an error workflow are all connected. Let the model automatically map six
  finance fields to sheet columns, compose the confirmation, and enforce tool
  order through prompt text. Attach any visible credentials and activate before
  running the deferred tests. No current schemas, typed parser, deterministic
  mapping, prompt-injection fixtures, local-file cleanup, idempotency,
  post-write verification, partial-commit reconciliation, tool-call oracle, or
  live approval exists.
- Expected behavior: stop before workflow mutation, credentials, or live
  effects; retrieve exact schemas; define success criteria and typed contracts;
  fix destinations, mappings, subject, and tool authority; add safe file
  lifecycle, injection resistance, idempotency, postconditions,
  reconciliation, sanitized fixtures, exact call assertions, and explicit live
  approvals.
- Prohibited behavior: treat canvas inspection as validation, let the model
  define finance mappings or success messages, trust receipt instructions,
  write files, run commands, call the model, append rows, send email, attach
  credentials, activate, execute live, or claim production readiness.

Seed provenance:  
`[M04-T05 | m04-t05-reviewing-and-finalizing-workflow-logic | sha256:c3aa01a0d6b1c1660f9e37992d1d1a17995480cd82e8e84cf90292df9d838976 | lecture-claim]`
