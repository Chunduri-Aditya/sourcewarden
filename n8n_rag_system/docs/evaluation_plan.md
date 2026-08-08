# Evaluation Plan

`data/eval/rag_eval_questions.jsonl` contains 25 evaluation questions. The evaluator checks:

- Router selected expected RAG collections.
- Retrieved chunks include citation metadata when indexes exist.
- Generated answer includes all required workflow sections.
- Generated answer includes credentials, node settings, data mapping, error handling, test steps, and citations.

The evaluator is intentionally lightweight. It is meant to catch regressions in contracts and routing before deeper human review or LLM-based grading.

Recommended future evaluation additions:

- Golden answers for common n8n tasks.
- Import tests for generated workflow JSON blueprints.
- Human scoring for beginner clarity.
- Source coverage checks by topic.

