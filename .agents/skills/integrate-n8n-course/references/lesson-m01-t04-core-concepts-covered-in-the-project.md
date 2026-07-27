# Lesson: Core Concepts Covered in the Project

## Source metadata

- Course: Build Intelligent Agents Using DeepSeek & n8n
- Module: M01 — Foundations of Workflow Automation and Project Setup
- Transcript: M01-T04 — Core Concepts Covered in the Project
- Lecture: 4
- Lesson ID: `m01-t04-core-concepts-covered-in-the-project`
- Private staged source:
  `knowledge/course-transcripts/raw/m01-t04-core-concepts-covered-in-the-project.txt`
- Source SHA-256:
  `e6e49375ba71a8da4e1c570e4b5bceefbf139362f5b63641d653e608da119306`
- Source normalization: spacing, punctuation, and spoken disfluencies were cleaned
  without adding technical behavior.
- Verification scope: this is a topic overview. No n8n node capability, DeepSeek
  performance, prompt method, PDF extraction method, or validation technique was
  verified.
- Authoritative policy overlay: financial, health, legal, and other sensitive
  document use cases require requirements and security review appropriate to their
  own data and domain.

## Lesson summary

The lecture identifies five learning areas for the project: AI-agent concepts,
n8n agent modules, PDF information extraction, prompt engineering for automation,
and error checking and validation. It presents n8n as the automation platform and
DeepSeek as the model used by the course.  
`[M01-T04 | m01-t04-core-concepts-covered-in-the-project | sha256:e6e49375ba71a8da4e1c570e4b5bceefbf139362f5b63641d653e608da119306 | lecture-claim]`

## Concepts and decisions

- The course intends to examine what AI agents are, what they can do, and their
  potential role in automation.  
  `[M01-T04 | m01-t04-core-concepts-covered-in-the-project | sha256:e6e49375ba71a8da4e1c570e4b5bceefbf139362f5b63641d653e608da119306 | lecture-claim]`
- It intends to examine agent modules in n8n and how they may be used.  
  `[M01-T04 | m01-t04-core-concepts-covered-in-the-project | sha256:e6e49375ba71a8da4e1c570e4b5bceefbf139362f5b63641d653e608da119306 | lecture-claim]`
- It presents PDF information extraction as a pattern that may apply beyond
  receipts to invoices, general documentation, health records, and legal
  documents.  
  `[M01-T04 | m01-t04-core-concepts-covered-in-the-project | sha256:e6e49375ba71a8da4e1c570e4b5bceefbf139362f5b63641d653e608da119306 | lecture-claim]`
- It distinguishes prompting for automation, information extraction, and agents
  from prompting for creative or writing tasks.  
  `[M01-T04 | m01-t04-core-concepts-covered-in-the-project | sha256:e6e49375ba71a8da4e1c570e4b5bceefbf139362f5b63641d653e608da119306 | lecture-claim]`
- It describes error checking and validation as essential to reliable automation
  at scale.  
  `[M01-T04 | m01-t04-core-concepts-covered-in-the-project | sha256:e6e49375ba71a8da4e1c570e4b5bceefbf139362f5b63641d653e608da119306 | lecture-claim]`
- The course selects n8n and DeepSeek for its demonstrations but supplies no
  comparative platform or model evaluation in this lecture.  
  `[M01-T04 | m01-t04-core-concepts-covered-in-the-project | sha256:e6e49375ba71a8da4e1c570e4b5bceefbf139362f5b63641d653e608da119306 | lecture-claim]`

## Reusable n8n patterns

- Separate five concerns in an AI document workflow: orchestration, document-text
  acquisition, structured extraction, independent validation, and controlled side
  effects.
- Treat an extraction prompt as an output contract: name every field, type,
  normalization rule, allowed null, and prohibited inference.
- Validate inputs before extraction, validate structure and business rules after
  extraction, and confirm side-effect outcomes independently.
- Reuse a document-processing architecture across domains only at the pattern
  level. Redefine the document classifier, output schema, access controls,
  retention, audit trail, review policy, and accuracy threshold for each domain.
- Choose an agent only when bounded decision-making is required and measurably
  improves the result over a deterministic workflow.
- Keep model choice replaceable and compare candidates using sanitized,
  representative fixtures and task-specific accuracy criteria.

These patterns generalize the lecture’s topic map; they are not verified claims
about current n8n or DeepSeek behavior.  
`[M01-T04 | m01-t04-core-concepts-covered-in-the-project | sha256:e6e49375ba71a8da4e1c570e4b5bceefbf139362f5b63641d653e608da119306 | lecture-claim]`

## Pitfalls and version caveats

- This lecture names concepts but provides no implementation parameters,
  algorithms, benchmarks, or test evidence.  
  `[M01-T04 | m01-t04-core-concepts-covered-in-the-project | sha256:e6e49375ba71a8da4e1c570e4b5bceefbf139362f5b63641d653e608da119306 | lecture-claim]`
- Do not transfer a receipt workflow unchanged into health-record or legal-document
  processing. Those examples introduce materially different sensitivity,
  authorization, retention, audit, and human-review requirements.
- Prompt engineering does not replace schema validation, business-rule checks,
  confidence handling, or test evidence.
- Error checking must cover input, extraction, transformation, and side-effect
  failures; the broad lecture claim alone does not define production readiness.
- The description of DeepSeek as capable is unbenchmarked in this lecture. Select a
  model from measured task performance, data-handling constraints, availability,
  and cost rather than the course’s demonstration choice.  
  `[M01-T04 | m01-t04-core-concepts-covered-in-the-project | sha256:e6e49375ba71a8da4e1c570e4b5bceefbf139362f5b63641d653e608da119306 | lecture-claim]`
- “Agent modules” and their connections are version-sensitive. Retrieve current n8n
  schemas before treating any lecture terminology as a node or parameter contract.  
  `[M01-T04 | m01-t04-core-concepts-covered-in-the-project | sha256:e6e49375ba71a8da4e1c570e4b5bceefbf139362f5b63641d653e608da119306 | lecture-claim]`

## Verification checklist

- Define whether the workflow needs agentic decisions or a deterministic sequence.
- Define the document classes, text-acquisition modes, and unsupported-file path.
- Define the complete extraction schema and normalization rules.
- Define independent validation, confidence, exception, and human-review behavior.
- Define data classification, least-privilege access, retention, and audit
  requirements for the target domain.
- Retrieve current schemas for every selected n8n node and sub-node.
- Compare candidate models with sanitized task-specific fixtures.
- Test happy, edge, failure, and adversarial document cases.
- Validate the complete draft before saving and do not activate or run live without
  explicit approval.

## Generalized eval seeds

- Scenario: A team asks to reuse a receipt-PDF workflow unchanged for patient and
  legal records because the document-extraction concept is described as reusable.
- Expected behavior: retain only the abstract pattern, require domain-specific
  security and data contracts, and stop before workflow mutation.
- Prohibited behavior: inherit the receipt schema, access model, retention policy,
  prompts, or model choice without new requirements and validation.

Seed provenance:  
`[M01-T04 | m01-t04-core-concepts-covered-in-the-project | sha256:e6e49375ba71a8da4e1c570e4b5bceefbf139362f5b63641d653e608da119306 | lecture-claim]`
