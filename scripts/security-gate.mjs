#!/usr/bin/env node

// Convenience entry point. The trusted Stop hook executes the sandbox-protected
// implementation directly from .codex/hooks/security-gate.mjs.
await import('../.codex/hooks/security-gate.mjs');
