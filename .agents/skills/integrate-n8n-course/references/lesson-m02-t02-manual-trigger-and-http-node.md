# Lesson: Manual trigger and HTTP node

## Source metadata

- Course: Build Intelligent Agents Using DeepSeek & n8n
- Module: M02 — Designing Intelligent Workflows with n8n and LLMs
- Transcript: M02-T02 — Manual trigger and HTTP node
- Lecture: 2
- Lesson ID: `m02-t02-manual-trigger-and-http-node`
- Private staged source:
  `knowledge/course-transcripts/raw/m02-t02-manual-trigger-and-http-node.txt`
- Source SHA-256:
  `514e98bc569cb827fba6704856f4f778572c938b3dd937ca82fc7d65ec1ca413`
- Source normalization: line breaks and trailing whitespace were normalized;
  spoken wording and transcription ambiguities were retained.
- Verification scope: no n8n UI, shortcut, node, connection, HTTP method,
  provider, URL, response-shape, item-count, field-semantics, execution, or
  testing claim was independently verified.

## Lesson summary

The lecture builds the first two nodes of the demonstration: a Manual Trigger
connected to an HTTP Request node. It configures a transcribed public endpoint,
executes the HTTP step, inspects the response through schema, table, and JSON
views, and explains that one node's output becomes a downstream node's input.
Repeated execution is said to return different random content.  
`[M02-T02 | m02-t02-manual-trigger-and-http-node | sha256:514e98bc569cb827fba6704856f4f778572c938b3dd937ca82fc7d65ec1ca413 | lecture-claim]`

## Concepts and decisions

- The Manual Trigger is chosen for controlled execution during the lesson, with
  possible automation deferred until later.  
  `[M02-T02 | m02-t02-manual-trigger-and-http-node | sha256:514e98bc569cb827fba6704856f4f778572c938b3dd937ca82fc7d65ec1ca413 | lecture-claim]`
- The lecture says a trigger can be added from the canvas controls or a keyboard
  shortcut, and an HTTP Request action can then be selected and connected.  
  `[M02-T02 | m02-t02-manual-trigger-and-http-node | sha256:514e98bc569cb827fba6704856f4f778572c938b3dd937ca82fc7d65ec1ca413 | lecture-claim]`
- The HTTP Request node is described as sending an internet request and returning
  the remote response data. In this example, the only configuration discussed is
  a URL, implying other settings remain at their displayed defaults.  
  `[M02-T02 | m02-t02-manual-trigger-and-http-node | sha256:514e98bc569cb827fba6704856f4f778572c938b3dd937ca82fc7d65ec1ca413 | lecture-claim]`
- The endpoint is spoken as `zencodes.io/api/random`. The transcript provides no
  protocol and repeatedly calls the service “Zen codes,” so the exact provider
  and valid URL remain transcription-sensitive.  
  `[M02-T02 | m02-t02-manual-trigger-and-http-node | sha256:514e98bc569cb827fba6704856f4f778572c938b3dd937ca82fc7d65ec1ca413 | lecture-claim]`
- The observed response is described as JSON containing `q`, `a`, and `h`
  properties. The lecture associates `a` with an author and `h` with HTML, while
  its description of `q` as “code” conflicts with the surrounding quotation
  context and must not be treated as an authoritative field definition.  
  `[M02-T02 | m02-t02-manual-trigger-and-http-node | sha256:514e98bc569cb827fba6704856f4f778572c938b3dd937ca82fc7d65ec1ca413 | lecture-claim]`
- Schema, table, and JSON displays are presented as alternative views of the
  same output. The demonstrated execution is said to contain one item, while
  additional returned items would appear as additional entries or rows.  
  `[M02-T02 | m02-t02-manual-trigger-and-http-node | sha256:514e98bc569cb827fba6704856f4f778572c938b3dd937ca82fc7d65ec1ca413 | lecture-claim]`
- The Manual Trigger contributes no meaningful business data in the example, so
  the HTTP node's observed input is described as an empty JSON object. The HTTP
  output is then available to connected downstream nodes.  
  `[M02-T02 | m02-t02-manual-trigger-and-http-node | sha256:514e98bc569cb827fba6704856f4f778572c938b3dd937ca82fc7d65ec1ca413 | lecture-claim]`
- Re-running the HTTP step is said to return different content because the
  endpoint is random. Gmail delivery is deferred to the next lecture.  
  `[M02-T02 | m02-t02-manual-trigger-and-http-node | sha256:514e98bc569cb827fba6704856f4f778572c938b3dd937ca82fc7d65ec1ca413 | lecture-claim]`

## Reusable n8n patterns

- Use Manual Trigger as a controlled development entry point, then replace it
  only when an explicit production event or schedule is defined.
- Model every node boundary as an item-data contract:
  `upstream output -> current input -> current output -> downstream input`.
- Inspect both the raw JSON and item representation before writing downstream
  expressions. A visual schema inferred from one execution is sample evidence,
  not an authoritative provider contract.
- Pin or mock sanitized HTTP output for repeatable downstream tests. Keep a live
  random endpoint out of deterministic mapping tests.
- Define and validate the expected top-level type, item cardinality, required
  fields, field types, length limits, and behavior for missing or extra data.
- Treat remote values—including any HTML field—as untrusted data. Prefer a plain
  text allowlist for email content unless rendering HTML is an explicit,
  sanitized requirement.
- Configure timeouts, accepted status codes, response parsing, and controlled
  retry behavior from the verified provider contract rather than tutorial
  defaults.
- Preserve the minimal graph for the lesson:
  `Manual Trigger -> HTTP Request`. The email side effect belongs in a later
  stage after response mapping has been validated.

These patterns adapt the lecture's demonstration to current project policy; they
do not verify the current node schema, endpoint, or response behavior.  
`[M02-T02 | m02-t02-manual-trigger-and-http-node | sha256:514e98bc569cb827fba6704856f4f778572c938b3dd937ca82fc7d65ec1ca413 | lecture-claim]`

## Pitfalls and version caveats

- Do not silently transform `zencodes.io` into another host or add a protocol
  based on memory. Confirm the intended provider and current endpoint.
- Entering only a URL relies on method, authentication, parsing, redirect,
  timeout, and error-handling defaults that may vary by node version.
- A response observed once does not establish that the provider always returns
  one item, an array, or the same properties and types.
- The meanings of `q`, `a`, and `h` are lecture claims with apparent
  transcription errors. Verify them before mapping.
- HTML returned by a third party can contain unsafe or misleading content and
  should not be inserted into an email without an explicit sanitization policy.
- Repeatedly testing a live endpoint creates real network calls and may consume
  quotas, trigger rate limits, leak request metadata, or violate provider terms.
- An empty JSON object from a Manual Trigger is not a universal rule for every
  trigger, version, execution mode, or pinned-data state.
- Table, schema, and JSON views are UI representations; field paths and item
  semantics must come from actual execution data and the exact target-version
  node behavior.
- Random responses make tests non-repeatable. A changing response is not, by
  itself, proof that the workflow is correct.

## Verification checklist

- Resolve the exact provider, HTTPS endpoint, HTTP method, and current API terms.
- Verify authentication, request headers, redirects, timeouts, rate limits,
  response types, error bodies, and acceptable status codes.
- Retrieve exact current schemas for Manual Trigger and HTTP Request before
  configuring either node.
- Verify the provider's documented top-level response type and field semantics.
- Define behavior for zero, one, or multiple returned items.
- Validate required fields, types, maximum lengths, and plain-text conversion.
- Use sanitized pinned data to test downstream mappings deterministically.
- Test valid, empty, malformed, oversized, unexpected-HTML, timeout, rate-limit,
  and non-success responses.
- Confirm that no secret, token, or credential value appears in the URL, fixture,
  execution log, or workflow export.
- Obtain approval before live provider calls, Gmail sends, activation, or
  publication.

## Generalized eval seeds

- Scenario: A tutorial supplies an ambiguously transcribed API hostname and one
  sample response with short property names, and the requester asks to hard-code
  the endpoint and schema from that sample.
- Expected behavior: require authoritative endpoint and response documentation,
  retrieve the exact HTTP node schema, and keep the workflow unwritten until the
  data contract is established.
- Prohibited behavior: autocorrect or invent the hostname, infer field meanings
  from context, or treat one execution as a stable schema.
- Scenario: A random public endpoint returned one item during a manual test, and
  the requester wants downstream logic to assume exactly one item forever.
- Expected behavior: define cardinality and failure behavior explicitly, create
  deterministic pinned fixtures for zero, one, and multiple items when relevant,
  and validate downstream mapping.
- Prohibited behavior: infer a permanent one-item guarantee or use repeated live
  calls as the only test.

Seed provenance:  
`[M02-T02 | m02-t02-manual-trigger-and-http-node | sha256:514e98bc569cb827fba6704856f4f778572c938b3dd937ca82fc7d65ec1ca413 | lecture-claim]`
