#!/usr/bin/env node

// Convenience entry point. Regenerates the manifest from the sandbox-protected
// generator directly at .codex/hooks/generate-security-control-hashes.mjs.
await import('../.codex/hooks/generate-security-control-hashes.mjs');
