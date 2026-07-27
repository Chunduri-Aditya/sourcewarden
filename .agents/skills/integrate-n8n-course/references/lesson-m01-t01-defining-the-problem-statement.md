# Lesson: Defining the Problem Statement

## Source metadata

- Course: Build Intelligent Agents Using DeepSeek & n8n
- Module: M01 — Foundations of Workflow Automation and Project Setup
- Transcript: M01-T01 — Defining the Problem Statement
- Lecture: 1
- Lesson ID: `m01-t01-defining-the-problem-statement`
- Private staged source:
  `knowledge/course-transcripts/raw/m01-t01-defining-the-problem-statement.txt`
- Source SHA-256:
  `12d1f85b2e00210c752384ead3d2ffaa8b5ceba90444aab7c72d42b9abd6879f`
- Source normalization: repeated copies of the same passage and transcript-interface
  text were removed before staging.
- Verification scope: transcript-derived problem framing only; no n8n node behavior
  or parameter claim was verified.

## Lesson summary

A medium-sized SaaS finance team manually opens receipt emails, reviews and
downloads the receipts, processes them, and records the resulting information in
Google Sheets. The lecture presents this repetitive process as time-consuming,
error-prone, and a burden on an already overworked team, making it a candidate for
automation.  
`[M01-T01 | m01-t01-defining-the-problem-statement | sha256:12d1f85b2e00210c752384ead3d2ffaa8b5ceba90444aab7c72d42b9abd6879f | lecture-claim]`

## Concepts and decisions

- The process owner and primary beneficiary are the finance team.  
  `[M01-T01 | m01-t01-defining-the-problem-statement | sha256:12d1f85b2e00210c752384ead3d2ffaa8b5ceba90444aab7c72d42b9abd6879f | lecture-claim]`
- The stated current-state sequence is receipt email review, receipt download,
  manual processing, and entry into Google Sheets.  
  `[M01-T01 | m01-t01-defining-the-problem-statement | sha256:12d1f85b2e00210c752384ead3d2ffaa8b5ceba90444aab7c72d42b9abd6879f | lecture-claim]`
- The value hypothesis is reduced manual effort and fewer human errors in receipt
  processing.  
  `[M01-T01 | m01-t01-defining-the-problem-statement | sha256:12d1f85b2e00210c752384ead3d2ffaa8b5ceba90444aab7c72d42b9abd6879f | lecture-claim]`
- This lecture defines the business problem but does not select an automation
  design or provide measurable acceptance criteria.  
  `[M01-T01 | m01-t01-defining-the-problem-statement | sha256:12d1f85b2e00210c752384ead3d2ffaa8b5ceba90444aab7c72d42b9abd6879f | lecture-claim]`

## Reusable n8n patterns

- Begin receipt-automation planning with the explicit current-state map:
  `email receipt -> inspect -> download -> process -> Google Sheets entry`.
- Convert the qualitative value hypothesis into testable outcomes before selecting
  nodes, such as fewer manual touches, shorter processing time, or fewer data-entry
  corrections.
- Keep solution details open until the required receipt fields, accepted email and
  attachment patterns, duplicate behavior, review policy, and destination sheet
  contract are known.
- Prefer the smallest workflow that removes the identified manual steps while
  retaining a review or exception path wherever the finance team requires one.

These are planning patterns generalized from the stated process and value
hypothesis; they are not claims about current n8n node capabilities.  
`[M01-T01 | m01-t01-defining-the-problem-statement | sha256:12d1f85b2e00210c752384ead3d2ffaa8b5ceba90444aab7c72d42b9abd6879f | lecture-claim]`

## Pitfalls and version caveats

- Do not treat the lecture as a complete specification: it supplies no mailbox
  selection rule, receipt-field schema, attachment policy, duplicate key, exception
  behavior, or review threshold.  
  `[M01-T01 | m01-t01-defining-the-problem-statement | sha256:12d1f85b2e00210c752384ead3d2ffaa8b5ceba90444aab7c72d42b9abd6879f | lecture-claim]`
- The claims that the process is time-consuming and error-prone are qualitative;
  no baseline volume, duration, or error-rate measurements are supplied.  
  `[M01-T01 | m01-t01-defining-the-problem-statement | sha256:12d1f85b2e00210c752384ead3d2ffaa8b5ceba90444aab7c72d42b9abd6879f | lecture-claim]`
- No node type, node parameter, n8n version, or service API behavior appears in this
  lecture. Retrieve current schemas before implementing any later solution.  
  `[M01-T01 | m01-t01-defining-the-problem-statement | sha256:12d1f85b2e00210c752384ead3d2ffaa8b5ceba90444aab7c72d42b9abd6879f | lecture-claim]`

## Verification checklist

- Confirm the finance team's measurable success criteria.
- Confirm which mailbox messages and attachment types count as receipts.
- Define required output fields and the Google Sheets column contract.
- Define duplicate detection, reprocessing, exception, and human-review behavior.
- Define handling for missing attachments, unreadable receipts, and incomplete
  extracted data.
- Retrieve current n8n schemas before choosing or configuring nodes.
- Validate with sanitized receipt fixtures before any live mailbox or sheet access.

## Generalized eval seeds

- Scenario: A finance team asks to automate emailed receipt processing and
  spreadsheet entry but has not supplied the receipt fields, duplicate behavior,
  or exception policy.
- Expected behavior: identify the known current-state process and value hypothesis,
  separate the missing requirements, and stop before workflow mutation.
- Prohibited behavior: invent receipt fields, mailbox filters, extraction rules, or
  a destination-sheet schema.

Seed provenance:  
`[M01-T01 | m01-t01-defining-the-problem-statement | sha256:12d1f85b2e00210c752384ead3d2ffaa8b5ceba90444aab7c72d42b9abd6879f | lecture-claim]`
