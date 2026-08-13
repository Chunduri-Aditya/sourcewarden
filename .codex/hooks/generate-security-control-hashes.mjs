#!/usr/bin/env node

// Maintainer-run tool. Recomputes .codex/security-control-hashes.json from
// the current content of every file in hashPinnedSecurityFiles.
//
// This is deliberately NOT wired into any agent-writable path: writer roles
// (skeleton_architect, module_builder, eval_tuner) are already blocked from
// touching .codex/ or scripts/ by validate-agent-run.mjs's protectedPrefixes,
// so an agent cannot tamper with a security file and then launder it through
// this generator. Only a human maintainer runs this, after reviewing the diff.

import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { hashPinnedSecurityFiles } from './security-gate.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');

function sha256(content) {
  return createHash('sha256').update(content).digest('hex');
}

const files = {};
for (const pathFromRoot of [...hashPinnedSecurityFiles].sort()) {
  const content = await readFile(resolve(root, pathFromRoot));
  files[pathFromRoot] = sha256(content);
}

const manifest = { version: 1, algorithm: 'sha256', files };
const manifestPath = resolve(root, '.codex/security-control-hashes.json');
await writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
console.log(`Wrote ${Object.keys(files).length} pinned hashes to .codex/security-control-hashes.json`);
