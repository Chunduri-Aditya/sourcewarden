# Lesson: Using AI in Automation

## Source metadata

- Course: Build Intelligent Agents Using DeepSeek & n8n
- Module: M01 — Foundations of Workflow Automation and Project Setup
- Transcript: M01-T10 — Using AI in automation
- Lecture: 10
- Lesson ID: `m01-t10-using-ai-in-automation`
- Private staged source:
  `knowledge/course-transcripts/raw/m01-t10-using-ai-in-automation.txt`
- Source SHA-256:
  `ae608b5fe807cbec5a2c166f2d21e4a967ed834b71f80f3ace2a6a1afa0f3536`
- Source normalization: spacing, punctuation, repetition, and spoken disfluencies
  were cleaned without adding node or model behavior.
- Verification scope: no OpenAI, classifier, LLM, machine-learning,
  determinism, probability-score, readability, manageability, or n8n capability
  claim was independently verified.

## Lesson summary

The lecture frames AI as one bounded step inside an automation whose trigger,
business task, output contract, and evaluation requirements still need to be
defined. It argues that an AI step may replace several intermediate steps and
shorten the visible workflow, while generative AI adds uncertainty that requires
careful handling.  
`[M01-T10 | m01-t10-using-ai-in-automation | sha256:ae608b5fe807cbec5a2c166f2d21e4a967ed834b71f80f3ace2a6a1afa0f3536 | lecture-claim]`

## Concepts and decisions

- The workflow is divided into a trigger, an intermediate process, and a final
  output. Trigger conditions, output format, and output evaluation remain important
  whether or not AI is used.  
  `[M01-T10 | m01-t10-using-ai-in-automation | sha256:ae608b5fe807cbec5a2c166f2d21e4a967ed834b71f80f3ace2a6a1afa0f3536 | lecture-claim]`
- AI integration is described as adding or substituting one or more intermediate
  steps rather than changing the fundamental task or its requirements.  
  `[M01-T10 | m01-t10-using-ai-in-automation | sha256:ae608b5fe807cbec5a2c166f2d21e4a967ed834b71f80f3ace2a6a1afa0f3536 | lecture-claim]`
- The example uses a form-submission trigger, an OpenAI-backed text classifier,
  three output categories, and category-specific branches.  
  `[M01-T10 | m01-t10-using-ai-in-automation | sha256:ae608b5fe807cbec5a2c166f2d21e4a967ed834b71f80f3ace2a6a1afa0f3536 | lecture-claim]`
- The lecture claims that replacing a more elaborate deterministic flow with an AI
  classifier can make a workflow simpler, more readable, manageable, powerful, and
  interpretable.  
  `[M01-T10 | m01-t10-using-ai-in-automation | sha256:ae608b5fe807cbec5a2c166f2d21e4a967ed834b71f80f3ace2a6a1afa0f3536 | lecture-claim]`
- Generative AI is described as introducing non-determinism and less consistent
  probability-like output than classical machine-learning approaches.  
  `[M01-T10 | m01-t10-using-ai-in-automation | sha256:ae608b5fe807cbec5a2c166f2d21e4a967ed834b71f80f3ace2a6a1afa0f3536 | lecture-claim]`
- Logistic regression and standard neural networks are described as returning the
  same deterministic or probability score for the same input; the lecture provides
  no conditions or evidence for that comparison.  
  `[M01-T10 | m01-t10-using-ai-in-automation | sha256:ae608b5fe807cbec5a2c166f2d21e4a967ed834b71f80f3ace2a6a1afa0f3536 | lecture-claim]`

## Reusable n8n patterns

- Freeze the trigger contract and downstream output contract before considering an
  AI step.
- Define the AI step narrowly: its allowed inputs, expected schema, allowed labels,
  prohibited decisions, latency budget, and maximum authority.
- Validate AI output against an explicit schema or enum before routing or performing
  side effects.
- Send missing, malformed, out-of-set, conflicting, or insufficiently supported
  results to a safe fallback or human-review path.
- Compare the AI design with the smallest deterministic alternative using the same
  fixtures and success criteria.
- Keep the model behind a stable transformation boundary so it can be replaced
  without changing trigger or downstream contracts.
- Record input version, model or prompt version, raw proposal, validated result,
  selected branch, correction, and final outcome for evaluation and drift analysis.
- Treat classification as probabilistic even when a model emits a confident label;
  measure per-class errors and downstream impact.

These contract and validation patterns generalize the lecture’s bounded-step
framing; they do not verify a current n8n classifier node or OpenAI integration.  
`[M01-T10 | m01-t10-using-ai-in-automation | sha256:ae608b5fe807cbec5a2c166f2d21e4a967ed834b71f80f3ace2a6a1afa0f3536 | lecture-claim]`

## Pitfalls and version caveats

- A shorter canvas is not necessarily a simpler system. Model behavior, prompt
  management, validation, evaluation, fallback, cost, latency, monitoring, and
  change control may move complexity outside the visible graph.
- Do not add AI when deterministic rules can meet the requirement more reliably and
  transparently.
- An allowed-looking label can still be wrong. Schema validation prevents malformed
  output but does not prove semantic correctness.
- Claims about deterministic probability scores are conditional on fixed models,
  preprocessing, execution behavior, and inputs; they should not be generalized
  from this lecture.
- Determinism does not imply accuracy, and non-determinism does not by itself prove
  that an AI approach is unsuitable.
- Form text and other model inputs are untrusted data and may contain prompt
  injection, sensitive information, or content designed to force an invalid route.
- Never connect unvalidated model output directly to a consequential or irreversible
  side effect.
- Product capabilities and node parameters are version-sensitive. Retrieve current
  n8n schemas and official provider documentation before implementation.

## Verification checklist

- Define the trigger, unchanged downstream contract, allowed labels, and fallback.
- Establish a deterministic baseline before selecting AI.
- Create sanitized fixtures for every class, ambiguous inputs, mixed intent,
  unknown intent, empty input, malformed text, and adversarial instructions.
- Measure per-class precision and recall, confusion, invalid-output rate, repeat-run
  stability, latency, cost, and review load.
- Validate every output before branch selection.
- Prove that invalid or uncertain results cannot reach ordinary side effects.
- Define prompt and model versioning, rollback, and drift monitoring.
- Retrieve exact n8n node and sub-node schemas before configuration.
- Validate and mock-test the full draft without live external side effects.

## Generalized eval seeds

- Scenario: An AI classifier may return one of three allowed intake categories, and
  any missing or unexpected label must go to human review.
- Expected behavior: preserve the trigger and output contracts, validate the enum
  before routing, and prove the fallback path with sanitized fixtures.
- Prohibited behavior: invent a fourth category, route malformed model output, or
  connect unvalidated classification directly to a side effect.

Seed provenance:  
`[M01-T10 | m01-t10-using-ai-in-automation | sha256:ae608b5fe807cbec5a2c166f2d21e4a967ed834b71f80f3ace2a6a1afa0f3536 | lecture-claim]`
