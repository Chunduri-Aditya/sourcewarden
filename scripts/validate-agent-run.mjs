#!/usr/bin/env node

// Convenience entry point. Enforcement executes the sandbox-protected validator
// directly from .codex/hooks/validate-agent-run.mjs.
await import('../.codex/hooks/validate-agent-run.mjs');
