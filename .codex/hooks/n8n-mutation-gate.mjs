#!/usr/bin/env node

import { createHash, verify } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import {
  mkdir,
  open,
  readFile,
  realpath,
} from 'node:fs/promises';
import {
  dirname,
  relative,
  resolve,
  sep,
} from 'node:path';
import { fileURLToPath } from 'node:url';

const approvalRequiredTools = new Set([
  'mcp__n8n__archive_workflow',
  'mcp__n8n__create_workflow_from_code',
  'mcp__n8n__execute_workflow',
  'mcp__n8n__publish_workflow',
  'mcp__n8n__test_workflow',
  'mcp__n8n__unpublish_workflow',
  'mcp__n8n__update_workflow',
]);
const maximumAuthorizationLifetimeMs = 15 * 60 * 1000;

function canonicalize(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalize).join(',')}]`;
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map(
      (key) => `${JSON.stringify(key)}:${canonicalize(value[key])}`,
    ).join(',')}}`;
  }
  return JSON.stringify(value);
}

function hash(content) {
  return createHash('sha256').update(content).digest('hex');
}

function deny(reason) {
  console.log(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      permissionDecision: 'deny',
      permissionDecisionReason: reason,
    },
  }));
}

async function stdinJson() {
  let raw = '';
  for await (const chunk of process.stdin) raw += chunk;
  return JSON.parse(raw);
}

try {
  const input = await stdinJson();
  const root = await realpath(resolve(dirname(fileURLToPath(import.meta.url)), '../..'));
  const inputCwd = await realpath(resolve(input.cwd ?? ''));
  if (inputCwd !== root && !inputCwd.startsWith(`${root}${sep}`)) {
    deny('The tool request cwd is outside the protected project root.');
    process.exit(0);
  }
  const inputGitRoot = await realpath(execFileSync(
    'git',
    ['-C', inputCwd, 'rev-parse', '--show-toplevel'],
    { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] },
  ).trim());
  if (inputGitRoot !== root) {
    deny('Nested or substituted Git roots cannot authorize n8n mutations.');
    process.exit(0);
  }

  const securityReport = JSON.parse(execFileSync(
    process.execPath,
    [resolve(root, '.codex/hooks/security-gate.mjs')],
    { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] },
  ));
  if (!securityReport.valid) {
    deny('The protected workspace, workflow, and signed-ledger gate did not pass.');
    process.exit(0);
  }
  const ledgerPath = resolve(root, 'artifacts/agent-runs/current.json');
  const ledgerValidation = JSON.parse(execFileSync(
    process.execPath,
    [resolve(root, '.codex/hooks/validate-agent-run.mjs'), ledgerPath],
    { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] },
  ));
  if (!ledgerValidation.valid) {
    deny('The current signed run ledger failed the complete lifecycle validator.');
    process.exit(0);
  }
  const ledger = JSON.parse(await readFile(ledgerPath, 'utf8'));
  const publicKeyContent = await readFile(resolve(root, '.codex/agent-ledger-public-key.pem'));
  const trustedFingerprint = process.env.WORKFLOW_TRUST_ROOT_SHA256;
  if (
    !/^[a-f0-9]{64}$/.test(trustedFingerprint ?? '')
    || hash(publicKeyContent) !== trustedFingerprint
  ) {
    deny('The installed public key does not match the externally managed trust-root pin.');
    process.exit(0);
  }
  const publicKey = publicKeyContent.toString('utf8');
  const unsigned = structuredClone(ledger);
  const attestation = unsigned.attestation;
  delete unsigned.attestation;

  if (
    attestation?.algorithm !== 'ed25519'
    || !verify(
      null,
      Buffer.from(canonicalize(unsigned)),
      publicKey,
      Buffer.from(attestation.signature ?? '', 'base64'),
    )
  ) {
    deny('The current agent-run ledger has no valid external Ed25519 attestation.');
    process.exit(0);
  }
  if (ledger.finalDecision?.decision !== 'ACCEPTED') {
    deny('The externally attested run has not been accepted.');
    process.exit(0);
  }
  const issuedAt = Date.parse(ledger.issuedAt);
  const validUntil = Date.parse(ledger.validUntil);
  const now = Date.now();
  if (
    !Number.isFinite(issuedAt)
    || !Number.isFinite(validUntil)
    || issuedAt > now
    || validUntil <= now
    || validUntil - issuedAt > maximumAuthorizationLifetimeMs
  ) {
    deny('The signed run needs a current issuedAt and a validUntil no more than 15 minutes later.');
    process.exit(0);
  }

  const toolInputSha256 = hash(canonicalize(input.tool_input));
  const mutation = ledger.n8nMutations?.find(
    (entry) => entry.toolName === input.tool_name
      && entry.toolInputSha256 === toolInputSha256
      && entry.integratedSnapshotId === ledger.integratedSnapshotId,
  );
  if (!mutation) {
    deny('The exact n8n tool input is not bound to the reviewed integrated snapshot.');
    process.exit(0);
  }
  if (
    mutation.sessionId !== input.session_id
    || typeof mutation.authorizationNonce !== 'string'
    || !/^[A-Za-z0-9_-]{22,128}$/.test(mutation.authorizationNonce)
  ) {
    deny('The mutation authorization is not bound to this session and a strong one-time nonce.');
    process.exit(0);
  }

  const artifactPath = resolve(root, mutation.reviewedArtifactPath ?? '');
  const artifactRelativePath = relative(root, artifactPath).split(sep).join('/');
  if (
    artifactRelativePath.startsWith('../')
    || !artifactRelativePath.startsWith('workflows/generated/')
    || !artifactRelativePath.endsWith('.json')
  ) {
    deny('The reviewed artifact must be canonical JSON under workflows/generated/.');
    process.exit(0);
  }
  const artifact = await readFile(artifactPath);
  if (hash(artifact) !== mutation.reviewedArtifactSha256) {
    deny('The reviewed local workflow artifact hash no longer matches the signed ledger.');
    process.exit(0);
  }

  if (
    approvalRequiredTools.has(input.tool_name)
    && (
      mutation.explicitUserApproval !== true
      || mutation.approvalScope !== input.tool_name
    )
  ) {
    deny('Every n8n mutation requires exact, signed user-approval scope.');
    process.exit(0);
  }

  const consumptionDirectory = resolve(root, '.codex/authorization-consumption');
  await mkdir(consumptionDirectory, { recursive: true });
  const consumptionPath = resolve(
    consumptionDirectory,
    `${hash(mutation.authorizationNonce)}.used`,
  );
  const handle = await open(consumptionPath, 'wx', 0o600);
  await handle.writeFile(JSON.stringify({
    consumedAt: new Date().toISOString(),
    ledgerRunId: ledger.runId,
    sessionId: input.session_id,
    toolName: input.tool_name,
    toolInputSha256,
  }));
  await handle.close();
} catch (error) {
  deny(`n8n mutation gate failed closed: ${error.message}`);
}
