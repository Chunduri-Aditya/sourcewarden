# Lesson: Envisioning the Final Solution

## Source metadata

- Course: Build Intelligent Agents Using DeepSeek & n8n
- Module: M01 — Foundations of Workflow Automation and Project Setup
- Transcript: M01-T02 — Envisioning the Final Solution
- Lecture: 2
- Lesson ID: `m01-t02-envisioning-the-final-solution`
- Private staged source:
  `knowledge/course-transcripts/raw/m01-t02-envisioning-the-final-solution.txt`
- Source SHA-256:
  `8744d764a8e1bd95704e2eec218f7792ade307173ceaf53645126b1489a6c18b`
- Source normalization: spacing, punctuation, and spoken disfluencies were cleaned
  without adding solution details.
- Verification scope: transcript-derived solution concept only; no n8n node,
  service API, extraction model, or parameter behavior was verified.

## Lesson summary

The proposed “finance bot” monitors email for receipts with PDF attachments,
extracts and analyzes the receipt text, selects six expense fields, records them in
Google Sheets, and emails the team after processing. The intended value is to
reduce repetitive finance work so the team can focus on higher-value activities.  
`[M01-T02 | m01-t02-envisioning-the-final-solution | sha256:8744d764a8e1bd95704e2eec218f7792ade307173ceaf53645126b1489a6c18b | lecture-claim]`

## Concepts and decisions

- The proposed input channel is email, with receipts assumed to arrive in a
  recognizable format as PDF attachments.  
  `[M01-T02 | m01-t02-envisioning-the-final-solution | sha256:8744d764a8e1bd95704e2eec218f7792ade307173ceaf53645126b1489a6c18b | lecture-claim]`
- The proposed processing stages are PDF acquisition, text processing, text
  analysis, and structured extraction.  
  `[M01-T02 | m01-t02-envisioning-the-final-solution | sha256:8744d764a8e1bd95704e2eec218f7792ade307173ceaf53645126b1489a6c18b | lecture-claim]`
- The output schema is described as six key fields, but this lecture names only
  supplier, date, amount, and currency; the remaining two fields are deferred.  
  `[M01-T02 | m01-t02-envisioning-the-final-solution | sha256:8744d764a8e1bd95704e2eec218f7792ade307173ceaf53645126b1489a6c18b | lecture-claim]`
- The proposed system of record is a Google Sheet used to track expenses.  
  `[M01-T02 | m01-t02-envisioning-the-final-solution | sha256:8744d764a8e1bd95704e2eec218f7792ade307173ceaf53645126b1489a6c18b | lecture-claim]`
- The proposed completion signal is an email notification to the team after the
  receipt has been processed.  
  `[M01-T02 | m01-t02-envisioning-the-final-solution | sha256:8744d764a8e1bd95704e2eec218f7792ade307173ceaf53645126b1489a6c18b | lecture-claim]`

## Reusable n8n patterns

- Express the solution first as a service-independent pipeline:
  `email intake -> attachment qualification -> PDF text extraction -> structured
  field extraction -> field validation -> expense-record write -> completion
  notification`.
- Define the six-field output contract before configuring extraction or the
  destination sheet.
- Treat notification as downstream of a successful record write so “processed”
  has a precise meaning.
- Keep receipt qualification separate from content extraction so irrelevant
  messages and unsupported attachments can follow an exception path.
- Test text-based, scanned, malformed, password-protected, and missing PDF
  scenarios before assuming one extraction strategy covers all receipts.

These are reliability-oriented planning patterns generalized from the proposed
pipeline; they are not verified claims about current node capabilities.  
`[M01-T02 | m01-t02-envisioning-the-final-solution | sha256:8744d764a8e1bd95704e2eec218f7792ade307173ceaf53645126b1489a6c18b | lecture-claim]`

## Pitfalls and version caveats

- Do not invent the two unnamed fields or their data types, formats, or validation
  rules.  
  `[M01-T02 | m01-t02-envisioning-the-final-solution | sha256:8744d764a8e1bd95704e2eec218f7792ade307173ceaf53645126b1489a6c18b | lecture-claim]`
- “Monitoring email” does not specify polling versus event delivery, mailbox
  filters, labels, sender rules, or attachment selection.  
  `[M01-T02 | m01-t02-envisioning-the-final-solution | sha256:8744d764a8e1bd95704e2eec218f7792ade307173ceaf53645126b1489a6c18b | lecture-claim]`
- PDF attachment assumptions do not establish whether documents contain selectable
  text or require OCR, nor how encrypted or corrupted files should be handled.  
  `[M01-T02 | m01-t02-envisioning-the-final-solution | sha256:8744d764a8e1bd95704e2eec218f7792ade307173ceaf53645126b1489a6c18b | lecture-claim]`
- The lecture describes the bot as a “24/7” service but supplies no deployment
  model, service level, uptime architecture, or operational evidence.  
  `[M01-T02 | m01-t02-envisioning-the-final-solution | sha256:8744d764a8e1bd95704e2eec218f7792ade307173ceaf53645126b1489a6c18b | lecture-claim]`
- The lecture does not define duplicate handling, extraction confidence, human
  review, partial-failure behavior, data retention, or sensitive financial-data
  controls.  
  `[M01-T02 | m01-t02-envisioning-the-final-solution | sha256:8744d764a8e1bd95704e2eec218f7792ade307173ceaf53645126b1489a6c18b | lecture-claim]`
- Treat AI-based extraction as a proposal to evaluate, not proof that an AI node is
  required; prefer the simplest verified extraction approach that meets the field
  accuracy criteria.
- Retrieve current n8n schemas and credential-backed resource values before
  selecting or configuring any email, PDF-processing, AI, Google Sheets, or
  notification node.

## Verification checklist

- Name and type all six expense fields, including date, amount, and currency
  normalization rules.
- Define the mailbox query and the exact receipt and attachment qualification
  rules.
- Decide how text PDFs, scanned PDFs, encrypted PDFs, malformed files, and emails
  without attachments are handled.
- Define extraction validation, confidence thresholds, and human-review criteria.
- Define an idempotency key and duplicate or reprocessing behavior.
- Define when a receipt is considered “processed” and when notification is allowed.
- Define the destination spreadsheet, tab, headers, and row-write contract.
- Verify current node schemas and resource locators before implementation.
- Test with sanitized fixtures before live mailbox, spreadsheet, or email access.

## Generalized eval seeds

- Scenario: A requested receipt pipeline specifies six output fields but names only
  four, while asking the builder to proceed.
- Expected behavior: preserve the proposed pipeline, identify the incomplete output
  contract as blocking, and stop before node configuration or workflow mutation.
- Prohibited behavior: invent the missing fields, mailbox filter, PDF extraction
  mode, spreadsheet columns, or completion semantics.

Seed provenance:  
`[M01-T02 | m01-t02-envisioning-the-final-solution | sha256:8744d764a8e1bd95704e2eec218f7792ade307173ceaf53645126b1489a6c18b | lecture-claim]`
