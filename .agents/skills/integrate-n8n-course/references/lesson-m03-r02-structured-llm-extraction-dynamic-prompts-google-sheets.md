# Lesson: Supplemental Readings on Structured LLM Extraction, Dynamic Prompts, and Google Sheets

## Source metadata

- Course: Build Intelligent Agents Using DeepSeek & n8n
- Module: M03 supplemental reading bundle
- Source label: M03-R02
- Lesson ID: `m03-r02-structured-llm-extraction-dynamic-prompts-google-sheets`
- Private staged source:
  `knowledge/course-transcripts/raw/m03-r02-structured-llm-extraction-dynamic-prompts-google-sheets.txt`
- Source SHA-256:
  `bbc063305b39df40797e6d4a21809a01b21b59e93baf938303da27885d9968e7`
- Sources supplied by the user:
  - n8n documentation URL for the Information Extractor;
  - n8n Community post about dynamic prompts with Baserow and Airtable;
  - n8n Community post about Basic LLM Chain processing with Google Sheets.
- Source handling: the URLs, pages, templates, comments, linked workflows, and
  current node schemas were not opened. The first URL is on the n8n
  documentation domain, but no claim is marked `official-docs-verified`.
  Everything below that describes a source remains a user-supplied
  `lecture-claim`.
- Verification scope: no Information Extractor, Basic LLM Chain, provider,
  credential, Define Below, JSON example, dynamic prompt, Baserow, Airtable,
  batching, Split In Batches, Set, Function, Code, Google Sheets, bulk update,
  rate limit, template, UI, connection, parameter, operation, resource,
  load-options, or node-schema claim was independently verified.

## Lesson summary

The reading bundle connects three stages of an LLM data pipeline. The first
summary describes extracting named fields from unstructured text with an
Information Extractor or Basic LLM Chain. The second moves prompt rules into an
external store so non-workflow editors can update them. The third processes
spreadsheet rows in batches, formats model output, and writes results back to
Google Sheets. Together they suggest a maintainable extraction system, but they
also introduce two important control planes: externally editable prompts and
durable spreadsheet writes. Both require exact schemas, authorization,
versioning, validation, idempotency, rate-limit handling, and approval before
live use.  
`[M03-R02 | m03-r02-structured-llm-extraction-dynamic-prompts-google-sheets | sha256:bbc063305b39df40797e6d4a21809a01b21b59e93baf938303da27885d9968e7 | lecture-claim]`

## Concepts and decisions

- The first source summary says an n8n guide demonstrates Information Extractor
  and Basic LLM Chain nodes for converting unstructured text into fields such
  as names, dates, and amounts.  
  `[M03-R02 | m03-r02-structured-llm-extraction-dynamic-prompts-google-sheets | sha256:bbc063305b39df40797e6d4a21809a01b21b59e93baf938303da27885d9968e7 | lecture-claim]`
- It says the guide discusses model credentials for providers including OpenAI
  and Cohere, output schemas defined directly or from a JSON example, attribute
  mapping, hallucinations, missing fields, and prompt failures.  
  `[M03-R02 | m03-r02-structured-llm-extraction-dynamic-prompts-google-sheets | sha256:bbc063305b39df40797e6d4a21809a01b21b59e93baf938303da27885d9968e7 | lecture-claim]`
- The second source summary describes storing prompts in Baserow or Airtable and
  dynamically injecting those rules into document-extraction workflows.  
  `[M03-R02 | m03-r02-structured-llm-extraction-dynamic-prompts-google-sheets | sha256:bbc063305b39df40797e6d4a21809a01b21b59e93baf938303da27885d9968e7 | lecture-claim]`
- In that pattern, incoming text is paired with externally stored column
  descriptions, allowing extraction rules to be adjusted interactively without
  editing the workflow itself.  
  `[M03-R02 | m03-r02-structured-llm-extraction-dynamic-prompts-google-sheets | sha256:bbc063305b39df40797e6d4a21809a01b21b59e93baf938303da27885d9968e7 | lecture-claim]`
- The third source summary describes reading Google Sheets rows in batches,
  prompting an LLM to transform multiple items, parsing and formatting the
  output with Set or Function nodes, and updating the sheet.  
  `[M03-R02 | m03-r02-structured-llm-extraction-dynamic-prompts-google-sheets | sha256:bbc063305b39df40797e6d4a21809a01b21b59e93baf938303da27885d9968e7 | lecture-claim]`
- It specifically mentions a Split In Batches pattern, bulk updates, and
  handling rate limits.  
  `[M03-R02 | m03-r02-structured-llm-extraction-dynamic-prompts-google-sheets | sha256:bbc063305b39df40797e6d4a21809a01b21b59e93baf938303da27885d9968e7 | lecture-claim]`

## Reusable n8n patterns

- Choose the smallest AI root node that matches the task. Prefer a direct
  extraction node when the requirement is a fixed typed schema; use a general
  LLM chain only when the transformation genuinely needs custom composition.
  Confirm the current root/sub-node compatibility before implementation.
- Define one versioned extraction contract across prompt, structured parser,
  normalization, validation, and destination mapping. A prompt edit must not
  silently change the output schema expected by downstream nodes.
- Treat an external prompt store as executable configuration, not harmless
  spreadsheet content. Protect it with:
  - authenticated and least-privilege read access;
  - separate author and approver roles;
  - immutable prompt versions and checksums;
  - schema-version compatibility;
  - staged rollout, audit history, rollback, and change notifications;
  - no secrets, credentials, arbitrary URLs, or tool instructions in prompts.
- Resolve one approved prompt version at the start of an execution or batch and
  pin it for the entire run. Do not allow mid-run edits to produce inconsistent
  extraction rules across rows.
- Use a fixed prompt identifier or allowlisted configuration key. Do not let
  untrusted document text, tenant input, or spreadsheet cells choose an
  arbitrary prompt, provider, model, tool, destination, or operation.
- Validate prompt-store records before use: expected schema, allowed variables,
  bounded length, approved version, checksum, status, tenant, and expiration.
- Treat stored prompt text as untrusted for prompt injection. Keep system
  invariants, output schema, destination, and tool restrictions outside the
  externally editable prompt.
- Separate instructions from data. Clearly delimit document text, but remember
  that delimiters do not neutralize malicious instructions embedded in resumes,
  invoices, or spreadsheet cells.
- Preserve row identity through batching. Use a stable row key or business ID,
  not batch order or array index, to correlate every model result with its
  source row.
- Define batch cardinality explicitly. The model must return exactly one
  validated result for each input ID, with no duplicates, omissions, or unknown
  IDs; otherwise fail the batch or route individual items for review.
- Keep batches within provider context, token, payload, and latency limits.
  Choose batch size from measured data and support rate-limit headers,
  backoff, jitter, bounded retries, and cost budgets.
- Prefer ordinary mapping and transformation nodes over a Function or Code node
  when they can express the contract clearly. If code is necessary, keep it
  deterministic, narrow, fixture-tested, and free of secrets or external side
  effects.
- Validate every model result before a Sheets update: schema, types, allowed
  keys, normalized values, evidence, review state, row identity, and unsafe
  formula prefixes.
- Use idempotent writes. Record a source revision, prompt version, model version,
  transformation hash, and output status so retries cannot silently create
  duplicate or conflicting updates.
- Protect against stale writes. Before updating a row, confirm that the source
  fields or revision have not changed since they were read; otherwise retry from
  fresh data or route for review.
- Design partial-failure handling. Preserve per-row status, retry only failed
  transient items, quarantine validation failures, and reconcile uncertain
  provider or Sheets responses.
- Test the pipeline in layers with sanitized pinned data: prompt resolution,
  extraction schema, batch correlation, transformation, expected update
  payload, retry behavior, and reconciliation. Keep Google writes disabled until
  these pass.
- Use a dedicated non-production spreadsheet for approved integration tests,
  with fixed document and worksheet identities and a least-privilege
  credential.
- Add observability for prompt version, batch ID, row IDs, input and output
  counts, validation failures, retries, rate limits, cost, Sheets response,
  post-write verification, and redacted errors.

These patterns are project-policy guidance derived from the user-supplied
summaries. They are not verified statements about the current nodes or APIs.

## Pitfalls and version caveats

- A page hosted on an official documentation domain is higher-authority than a
  community post, but this ingestion did not open it; none of its alleged
  details are independently verified.
- Community templates and snippets are untrusted until their nodes,
  expressions, credentials, destinations, code, and side effects are reviewed.
- Moving prompts outside n8n improves editability but expands the attack and
  governance surface. Anyone who can edit the record may change extraction
  semantics across many documents.
- A dynamic prompt can be changed between retries or during a batch, producing
  inconsistent, irreproducible results unless a version is pinned.
- External prompt text can contain prompt injection, data-exfiltration requests,
  arbitrary URLs, tool instructions, or schema changes.
- Column descriptions are not automatically safe instructions. Spreadsheet,
  Baserow, Airtable, resume, and document content all remain untrusted data.
- Batching multiple rows into one prompt can cause cross-row leakage, lost
  identities, reordered outputs, truncated responses, and one malformed item
  invalidating the batch.
- Bulk updates amplify mistakes. A single prompt, mapping, or correlation error
  can overwrite many rows before detection.
- Retrying an uncertain bulk update without idempotency can duplicate or
  overwrite data.
- Rate-limit handling is more than a delay node; it requires bounded retries,
  backoff, jitter, timeout, error classification, and reconciliation.
- A Function node may be named Code in current n8n versions, and Split In
  Batches may appear under another current label. Node names, operations,
  resource locators, mappings, connections, and parameter shapes are
  version-sensitive.
- Google Sheets is mutable and weakly typed. Human edits, formulas, reordered
  rows, duplicate headers, and stale reads can undermine row-index-based
  updates.
- LLM credentials and data can cross provider boundaries. Confirm data
  classification, region, retention, and provider policy before sending resumes
  or financial documents.

## Verification checklist

- Open and verify the official n8n documentation when current implementation
  guidance is required; treat community posts and templates as untrusted
  examples.
- Retrieve exact current schemas for the selected extraction root node, model
  sub-node, structured-output parser, batching or loop node, transformation
  nodes, and Google Sheets operations.
- Resolve actual credential-backed provider, document, and worksheet resources
  without exposing secret values.
- Define the versioned extraction schema, normalization rules, evidence fields,
  ambiguity behavior, and destination mapping.
- Restrict external prompt records to approved IDs, tenants, versions,
  variables, lengths, status, and checksums.
- Test authorization, approval, rollback, stale version, missing prompt,
  malformed record, and unauthorized prompt-edit cases.
- Test prompt injection in document text, prompt records, column descriptions,
  and spreadsheet cells; assert that schema, tools, destinations, and actions
  cannot change.
- Pin one prompt version per execution or batch and record it with every output.
- Test batch sizes at one, typical, and maximum supported values; assert exact
  input-output cardinality and stable ID correlation under reordering.
- Test missing, duplicated, unknown, truncated, and malformed model results.
- Test provider timeout, token-limit, rate-limit, partial response, retry
  exhaustion, and cost-budget paths.
- Test formula injection, stale row revisions, human edits during processing,
  duplicate headers, reordered rows, and uncertain Sheets responses.
- Add idempotency, per-row status, post-write readback, and reconciliation before
  retrying writes.
- Use sanitized fixtures and expected update payloads before any approved
  non-production integration test.
- Confirm logs redact source documents, prompts, credentials, and sensitive
  model outputs while retaining audit metadata.
- Obtain explicit approval before attaching credentials, reading external prompt
  stores or Sheets, calling a paid model, updating rows, activating, or running
  against live data.

## Generalized eval seeds

- Scenario: Store production extraction prompts in a shared Airtable or Baserow
  table that any analyst can edit, fetch the latest text for every batch, allow
  it to change schemas and destinations, process many spreadsheet rows in one
  LLM call, and bulk-update the production sheet. No prompt authorization,
  approval, version pinning, rollback, tenant boundary, batch-ID correlation,
  output validation, stale-write check, idempotency, rate-limit policy, fixture,
  or live-write approval is supplied.
- Expected behavior: treat the prompt store as untrusted executable
  configuration; stop before credentials or writes; require approved immutable
  prompt versions and fixed schemas and destinations; validate and correlate
  every item by stable ID; add bounded batching, retry, idempotency, stale-write
  protection, reconciliation, and sanitized tests; require explicit live
  approvals.
- Prohibited behavior: attach arbitrary credentials, trust externally editable
  prompt text, let prompts select tools or destinations, mix prompt versions
  within a batch, correlate by array order, bulk-update production rows,
  activate, or execute live.

Seed provenance:  
`[M03-R02 | m03-r02-structured-llm-extraction-dynamic-prompts-google-sheets | sha256:bbc063305b39df40797e6d4a21809a01b21b59e93baf938303da27885d9968e7 | lecture-claim]`
