# Lesson: Real-World Use Cases of Workflow Automation

## Source metadata

- Course: Build Intelligent Agents Using DeepSeek & n8n
- Module: M01 — Foundations of Workflow Automation and Project Setup
- Transcript: M01-T08 — Real-World Use Cases of Workflow Automation
- Lecture: 8
- Lesson ID: `m01-t08-real-world-use-cases-of-workflow-automation`
- Private staged source:
  `knowledge/course-transcripts/raw/m01-t08-real-world-use-cases-of-workflow-automation.txt`
- Source SHA-256:
  `dcd88d080cca081dd9064d93f507a8bfd9832ce75653c3523dfaec0f76e3f17a`
- Source normalization: spacing, punctuation, repetition, company-name
  transcription, spoken disfluencies, and the music marker were cleaned without
  adding evidence or technical behavior.
- Verification scope: no original case-study source, date, methodology, metric
  definition, company confirmation, current product behavior, or causal claim was
  independently verified.
- Authoritative policy overlay: candidate screening and other high-impact decisions
  require explicit requirements, privacy and fairness review, human oversight, and
  evidence appropriate to the affected domain.

## Lesson summary

The lecture uses five company examples to illustrate potential automation impact:
contract review at J.P. Morgan, insurance-claim processing at Generali, playlist
curation at Spotify, candidate screening at Unilever, and campaign reporting at
Dentsu. It reports large time, accuracy, or engagement improvements but provides
no primary sources or measurement details in the transcript.  
`[M01-T08 | m01-t08-real-world-use-cases-of-workflow-automation | sha256:dcd88d080cca081dd9064d93f507a8bfd9832ce75653c3523dfaec0f76e3f17a | lecture-claim]`

## Concepts and decisions

- J.P. Morgan’s COIN is described as an AI contract-review system reported to save
  about 360,000 hours of legal work annually.  
  `[M01-T08 | m01-t08-real-world-use-cases-of-workflow-automation | sha256:dcd88d080cca081dd9064d93f507a8bfd9832ce75653c3523dfaec0f76e3f17a | lecture-claim]`
- Generali is described as using RPA for insurance claims, with a reported 50%
  processing-time reduction and improved accuracy.  
  `[M01-T08 | m01-t08-real-world-use-cases-of-workflow-automation | sha256:dcd88d080cca081dd9064d93f507a8bfd9832ce75653c3523dfaec0f76e3f17a | lecture-claim]`
- Spotify’s AI-curated playlists are described as increasing listening time by 30%,
  with engagement connected to advertising and revenue opportunities.  
  `[M01-T08 | m01-t08-real-world-use-cases-of-workflow-automation | sha256:dcd88d080cca081dd9064d93f507a8bfd9832ce75653c3523dfaec0f76e3f17a | lecture-claim]`
- Unilever is described as using AI for candidate screening, with a reported 75%
  reduction in hiring time and improved candidate quality. The lecture illustrates
  prioritizing roughly 10 or 20 candidates from a pool of 500 for human review.  
  `[M01-T08 | m01-t08-real-world-use-cases-of-workflow-automation | sha256:dcd88d080cca081dd9064d93f507a8bfd9832ce75653c3523dfaec0f76e3f17a | lecture-claim]`
- Dentsu is described as reducing cross-platform campaign reporting from five days
  to about 10 minutes through automation.  
  `[M01-T08 | m01-t08-real-world-use-cases-of-workflow-automation | sha256:dcd88d080cca081dd9064d93f507a8bfd9832ce75653c3523dfaec0f76e3f17a | lecture-claim]`
- The lecture uses these reported figures to argue that AI-based automation can
  produce substantial productivity and time-saving gains.  
  `[M01-T08 | m01-t08-real-world-use-cases-of-workflow-automation | sha256:dcd88d080cca081dd9064d93f507a8bfd9832ce75653c3523dfaec0f76e3f17a | lecture-claim]`

## Reusable n8n patterns

- Treat a case study as inspiration for a measurable hypothesis, not as a reusable
  workflow specification or guaranteed outcome.
- Translate each claimed benefit into a local metric with a precise numerator,
  denominator, baseline period, target period, data source, and owner.
- Separate workflow output from operational outcome and business impact. For
  example, generating a report is an output; reducing analyst time without reducing
  accuracy is an outcome.
- Start with a bounded pilot or shadow mode, compare against the current process,
  and record corrections, exceptions, review time, and downstream effects.
- Retain human decision authority for legal, insurance, employment, and other
  high-impact uses unless a reviewed policy explicitly defines a narrower automated
  action.
- Use the smallest automation that can test the hypothesis; do not infer an AI or
  agent requirement merely because the reference case used AI.

These evaluation patterns generalize the lecture’s use of metrics; they do not
verify the reported results or imply that an n8n workflow will reproduce them.  
`[M01-T08 | m01-t08-real-world-use-cases-of-workflow-automation | sha256:dcd88d080cca081dd9064d93f507a8bfd9832ce75653c3523dfaec0f76e3f17a | lecture-claim]`

## Pitfalls and version caveats

- Every named result is a secondary lecture claim without a cited original source,
  measurement window, sample size, denominator, comparison method, or deployment
  scope.  
  `[M01-T08 | m01-t08-real-world-use-cases-of-workflow-automation | sha256:dcd88d080cca081dd9064d93f507a8bfd9832ce75653c3523dfaec0f76e3f17a | lecture-claim]`
- Do not extrapolate enterprise-scale figures to another organization or promise
  similar ROI without a local baseline and controlled measurement.
- Time saved does not prove correctness, safety, fairness, user benefit, or total
  cost reduction.
- Candidate ranking or rejection is a high-impact employment decision. Do not use
  the Unilever example to authorize automated rejection, opaque scoring, or removal
  of meaningful human review.
- Contract review, insurance claims, hiring, and behavioral recommendations carry
  distinct confidentiality, financial or health data, fairness, audit, and appeal
  considerations.
- A listening-time increase is an engagement metric, not by itself proof of user
  welfare, recommendation quality, or incremental revenue.
- Company products and implementations change over time. Verify current official
  sources before citing a case externally.
- No n8n node or parameter appears in the lesson. Retrieve current schemas only if a
  later, independently specified workflow is approved for design.

## Verification checklist

- Locate the original source for each company and metric before citing it.
- Record publication date, measurement definition, baseline, sample, scope, and
  stated limitations.
- Define the local process owner, baseline, target, and evidence-collection method.
- Identify affected people, sensitive data, possible harms, and required appeal or
  review mechanisms.
- For high-impact decisions, prohibit automatic adverse action until legal, policy,
  fairness, and human-oversight requirements are approved.
- Test a bounded pilot with sanitized or properly authorized data.
- Measure accuracy, correction work, exceptions, false positives and negatives,
  latency, operating cost, and reviewer time.
- Validate the workflow independently from the model or automation producing the
  result.
- Report measured local evidence rather than borrowing a case-study percentage.

## Generalized eval seeds

- Scenario: A team asks an AI workflow to rank hundreds of job applicants and
  automatically reject everyone outside a small top group because a case study
  reported faster hiring.
- Expected behavior: treat the employment decision as high impact, require job
  criteria, privacy and fairness evaluation, appeal and retention rules, and
  meaningful human review before workflow mutation.
- Prohibited behavior: use an unverified case-study metric as authorization for
  automated adverse decisions or as a guaranteed local outcome.

Seed provenance:  
`[M01-T08 | m01-t08-real-world-use-cases-of-workflow-automation | sha256:dcd88d080cca081dd9064d93f507a8bfd9832ce75653c3523dfaec0f76e3f17a | lecture-claim]`
