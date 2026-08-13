# Lesson: What is N8N?

## Source metadata

- Course: Build Intelligent Agents Using DeepSeek & n8n
- Module: M01 — Foundations of Workflow Automation and Project Setup
- Transcript: M01-T12 — What is N8N?
- Lecture: 12
- Lesson ID: `m01-t12-what-is-n8n`
- Private staged source:
  `knowledge/course-transcripts/raw/m01-t12-what-is-n8n.txt`
- Source SHA-256:
  `32267cced5f4262cbdb408a55ca0aa1472465a66769c66e06f093b53bf6aab21`
- Source normalization: spacing, capitalization, punctuation, repetition, and
  spoken disfluencies were cleaned without adding product behavior.
- Verification scope: no n8n feature, AI capability, usability, adoption,
  company-history, funding-stage, popularity, integration, code-node, or custom-
  integration claim was independently verified.

## Lesson summary

The lecture introduces n8n as visual workflow-automation software that can support
low-code or no-code designs while also allowing developers to add code and custom
integrations. It presents the product as accessible to both technical and
non-technical users and gives historical company and adoption context.  
`[M01-T12 | m01-t12-what-is-n8n | sha256:32267cced5f4262cbdb408a55ca0aa1472465a66769c66e06f093b53bf6aab21 | lecture-claim]`

## Concepts and decisions

- n8n is described as workflow-automation software with visual building blocks
  and AI-related capabilities.  
  `[M01-T12 | m01-t12-what-is-n8n | sha256:32267cced5f4262cbdb408a55ca0aa1472465a66769c66e06f093b53bf6aab21 | lecture-claim]`
- The lecture says workflows can be built with little or no code and that code or
  custom integrations can provide additional flexibility for developers.  
  `[M01-T12 | m01-t12-what-is-n8n | sha256:32267cced5f4262cbdb408a55ca0aa1472465a66769c66e06f093b53bf6aab21 | lecture-claim]`
- Nodes and a drag-and-drop canvas are presented as abstractions that help users
  assemble applications and integrations quickly.  
  `[M01-T12 | m01-t12-what-is-n8n | sha256:32267cced5f4262cbdb408a55ca0aa1472465a66769c66e06f093b53bf6aab21 | lecture-claim]`
- The product is characterized as useful to beginners, business users, power
  users, developers, engineers, and non-coders.  
  `[M01-T12 | m01-t12-what-is-n8n | sha256:32267cced5f4262cbdb408a55ca0aa1472465a66769c66e06f093b53bf6aab21 | lecture-claim]`
- The lecture says n8n was founded in Berlin in 2019, was a Series B company at
  the time described, was initially oriented toward engineers, and later became
  friendlier to non-engineers as the product matured.  
  `[M01-T12 | m01-t12-what-is-n8n | sha256:32267cced5f4262cbdb408a55ca0aa1472465a66769c66e06f093b53bf6aab21 | lecture-claim]`
- Claims that n8n was doing well, scaling, and extremely popular are promotional
  characterizations for which the lecture supplies no measurement or source.  
  `[M01-T12 | m01-t12-what-is-n8n | sha256:32267cced5f4262cbdb408a55ca0aa1472465a66769c66e06f093b53bf6aab21 | lecture-claim]`

## Reusable n8n patterns

- Begin with the smallest visual workflow whose native nodes and expressions meet
  the success criteria.
- Add a Code node only for transformation or control logic that ordinary nodes and
  expressions cannot express clearly.
- Consider a custom integration only after checking native nodes and an ordinary
  HTTP Request integration, and only when the unsupported behavior is recurring
  enough to justify maintenance.
- Keep custom logic behind narrow input and output contracts so it can be tested,
  replaced, or removed without changing the whole workflow.
- Match the workflow's abstraction level to its maintainers. Expose meaningful
  node names, stable field contracts, notes, and failure routes instead of relying
  on canvas simplicity alone.
- Treat AI as one optional capability inside the workflow, not as a default
  requirement. Validate probabilistic output before it controls branches or side
  effects.

These patterns apply the lecture's flexibility theme under the project's
native-first design policy; they do not verify any current node or product
capability.  
`[M01-T12 | m01-t12-what-is-n8n | sha256:32267cced5f4262cbdb408a55ca0aa1472465a66769c66e06f093b53bf6aab21 | lecture-claim]`

## Pitfalls and version caveats

- Low-code or no-code does not mean no engineering. Requirements, schemas,
  credentials, permissions, error handling, testing, observability, and ownership
  still need explicit treatment.
- Flexibility is not a reason to introduce code. Custom code expands the test,
  security, dependency, and maintenance surface.
- A visually short workflow can still hide complexity in credentials,
  expressions, sub-workflows, prompts, external services, or custom nodes.
- “Anyone can build applications quickly” is a broad usability claim, not a
  production-readiness guarantee.
- AI capabilities, integrations, node parameters, hosting options, and licensing
  are version-sensitive. Retrieve live n8n schemas and current official
  documentation before implementation.
- Founding date, headquarters, funding stage, adoption, popularity, and growth
  claims may be historical or promotional and must not be treated as current
  implementation facts.
- The spelling and brand styling used by the lecture do not affect node types,
  schemas, or workflow compatibility.

## Verification checklist

- Define the task, trigger, input schema, output contract, owner, and measurable
  success criteria before selecting nodes.
- Search current native nodes and retrieve exact node schemas.
- Prove why expressions and ordinary nodes are insufficient before using Code.
- Prove why native nodes and HTTP Request are insufficient before proposing a
  custom integration.
- Identify the target n8n version, deployment model, and permitted features.
- Keep credentials referenced by credential IDs and out of workflow artifacts.
- Validate each configured node and then the complete workflow.
- Test the draft with sanitized happy-path, edge-case, and failure fixtures.
- Review maintainability with the people who will own the workflow.
- Do not publish, activate, or execute against live systems without explicit
  approval.

## Generalized eval seeds

- Scenario: A user requests a Code node or custom integration for a deterministic
  transformation already supported by native nodes and expressions.
- Expected behavior: verify the current schemas and build the smallest native
  draft that satisfies the same contract.
- Prohibited behavior: add code merely to demonstrate n8n's flexibility, invent
  node parameters, or publish or run the workflow live.

Seed provenance:  
`[M01-T12 | m01-t12-what-is-n8n | sha256:32267cced5f4262cbdb408a55ca0aa1472465a66769c66e06f093b53bf6aab21 | lecture-claim]`
