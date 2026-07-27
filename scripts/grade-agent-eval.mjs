#!/usr/bin/env node

// Convenience entry point. Evaluation executes the sandbox-protected grader
// directly from .codex/hooks/grade-agent-eval.mjs.
await import('../.codex/hooks/grade-agent-eval.mjs');
