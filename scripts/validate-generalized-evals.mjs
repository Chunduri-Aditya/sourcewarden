#!/usr/bin/env node

// Convenience entry point. Validation executes the sandbox-protected validator
// directly from .codex/hooks/validate-generalized-evals.mjs.
await import('../.codex/hooks/validate-generalized-evals.mjs');
