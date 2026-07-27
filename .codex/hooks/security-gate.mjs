#!/usr/bin/env node

import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import {
  lstat,
  readFile,
  readdir,
  stat,
} from 'node:fs/promises';
import { dirname, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const args = new Set(process.argv.slice(2));
const hookMode = args.has('--hook');
const selfTest = args.has('--self-test');
const maximumScannedFileBytes = 10 * 1024 * 1024;

const secretPatterns = [
  ['private-key', /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/],
  ['openai-api-key', /\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}\b/],
  ['aws-access-key', /\bAKIA[0-9A-Z]{16}\b/],
  ['github-token', /\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b/],
  ['slack-token', /\bxox[baprs]-[A-Za-z0-9-]{20,}\b/],
  [
    'literal-secret-assignment',
    /\b(?:api_key|access_token|password|client_secret)\b\s*[:=]\s*["'][^"'${}<\s][^"']{11,}["']/i,
  ],
];

const prohibitedNodeTypes = new Set([
  'n8n-nodes-base.code',
  'n8n-nodes-base.dataTable',
  'n8n-nodes-base.executeCommand',
  'n8n-nodes-base.executeWorkflow',
  'n8n-nodes-base.readWriteFile',
  'n8n-nodes-base.ssh',
]);

const requiredSecurityFiles = [
  'AGENTS.md',
  '.codex/agents/security-firewall.toml',
  '.codex/hooks.json',
  '.codex/hooks/grade-agent-eval.mjs',
  '.codex/hooks/n8n-mutation-gate.mjs',
  '.codex/hooks/security-gate.mjs',
  '.codex/hooks/validate-agent-run.mjs',
  '.codex/hooks/validate-generalized-evals.mjs',
  '.codex/rules/security.rules',
  '.codex/security-control-hashes.json',
  'config/agent-policy.yaml',
  'config/agent-orchestration.json',
  'evals/EVAL_PROTOCOL.md',
  'evals/generalized-cases.jsonl',
  'scripts/validate-agent-system.py',
  'scripts/validate-n8n-config.py',
];

function projectRoot() {
  return resolve(dirname(fileURLToPath(import.meta.url)), '../..');
}

function normalizePath(root, absolutePath) {
  return relative(root, absolutePath).split(sep).join('/');
}

function isRootDependencyDirectory(pathFromRoot) {
  return pathFromRoot === 'node_modules';
}

async function walk(root, directory = root) {
  const files = [];
  let entries;

  try {
    entries = await readdir(directory, { withFileTypes: true });
  } catch (error) {
    return [{
      error: `Cannot read directory: ${error.message}`,
      pathFromRoot: normalizePath(root, directory),
    }];
  }

  for (const entry of entries) {
    const absolutePath = resolve(directory, entry.name);
    const pathFromRoot = normalizePath(root, absolutePath);
    if (pathFromRoot === '.git' || pathFromRoot.startsWith('.git/')) continue;
    if (isRootDependencyDirectory(pathFromRoot)) continue;

    if (entry.isSymbolicLink()) {
      files.push({ absolutePath, pathFromRoot, symbolicLink: true });
    } else if (entry.isDirectory()) {
      files.push(...await walk(root, absolutePath));
    } else if (entry.isFile()) {
      files.push({ absolutePath, pathFromRoot, symbolicLink: false });
    }
  }

  return files;
}

function sha256(content) {
  return createHash('sha256').update(content).digest('hex');
}

function canonicalize(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalize).join(',')}]`;
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map(
      (key) => `${JSON.stringify(key)}:${canonicalize(value[key])}`,
    ).join(',')}}`;
  }
  return JSON.stringify(value);
}

function addBlocking(blocking, rule, path, message, details = undefined) {
  blocking.push({ rule, path, message, ...(details ? { details } : {}) });
}

async function verifyControlHashes(root, blocking) {
  const manifestPath = resolve(root, '.codex/security-control-hashes.json');
  let manifest;

  try {
    manifest = JSON.parse(await readFile(manifestPath, 'utf8'));
  } catch (error) {
    addBlocking(
      blocking,
      'CONTROL_HASH_MANIFEST_INVALID',
      '.codex/security-control-hashes.json',
      error.message,
    );
    return;
  }

  if (manifest.version !== 1 || !manifest.files || typeof manifest.files !== 'object') {
    addBlocking(
      blocking,
      'CONTROL_HASH_MANIFEST_INVALID',
      '.codex/security-control-hashes.json',
      'Expected version 1 with a files object.',
    );
    return;
  }

  for (const [pathFromRoot, expectedHash] of Object.entries(manifest.files)) {
    try {
      const content = await readFile(resolve(root, pathFromRoot));
      const actualHash = sha256(content);
      if (actualHash !== expectedHash) {
        addBlocking(
          blocking,
          'SECURITY_CONTROL_CHANGED',
          pathFromRoot,
          `Expected sha256 ${expectedHash}, received ${actualHash}.`,
        );
      }
    } catch (error) {
      addBlocking(
        blocking,
        'SECURITY_CONTROL_UNREADABLE',
        pathFromRoot,
        error.message,
      );
    }
  }
}

function workflowObjects(parsed) {
  if (Array.isArray(parsed)) return parsed;
  if (parsed && Array.isArray(parsed.workflows)) return parsed.workflows;
  return [parsed];
}

function scanWorkflow(workflow, pathFromRoot, blocking) {
  if (!workflow || typeof workflow !== 'object' || !Array.isArray(workflow.nodes)) {
    addBlocking(
      blocking,
      'INVALID_WORKFLOW_JSON',
      pathFromRoot,
      'Generated workflow JSON must contain a nodes array.',
    );
    return;
  }

  if (workflow.active === true) {
    addBlocking(
      blocking,
      'ACTIVE_WORKFLOW_PROHIBITED',
      pathFromRoot,
      'Generated workflows must remain inactive drafts.',
    );
  }

  for (const [index, node] of workflow.nodes.entries()) {
    const nodePath = `${pathFromRoot}#nodes[${index}]`;
    const nodeType = node?.type;
    const parameters = node?.parameters ?? {};

    if (typeof nodeType !== 'string') {
      addBlocking(blocking, 'NODE_TYPE_MISSING', nodePath, 'Node type must be a string.');
      continue;
    }

    if (prohibitedNodeTypes.has(nodeType)) {
      addBlocking(
        blocking,
        'PROHIBITED_N8N_NODE',
        nodePath,
        `Generated workflow contains prohibited node type ${nodeType}.`,
        { nodeType },
      );
    }

    if (!nodeType.startsWith('n8n-nodes-base.')
      && !nodeType.startsWith('n8n-nodes-langchain.')) {
      addBlocking(
        blocking,
        'COMMUNITY_NODE_REQUIRES_EXTERNAL_APPROVAL',
        nodePath,
        `Node type ${nodeType} is not in the built-in allowlist.`,
      );
    }

    if (nodeType === 'n8n-nodes-base.webhook') {
      const authentication = parameters.authentication;
      if (!['basicAuth', 'headerAuth', 'jwtAuth'].includes(authentication)) {
        addBlocking(
          blocking,
          'PUBLIC_WEBHOOK_NOT_AUTHENTICATED',
          nodePath,
          'Every generated Webhook node must use an approved authentication mode.',
        );
      }
    }

    if (nodeType === 'n8n-nodes-base.httpRequest') {
      const method = String(parameters.method ?? parameters.requestMethod ?? 'GET').toUpperCase();
      if (method === 'DELETE') {
        addBlocking(
          blocking,
          'DESTRUCTIVE_HTTP_METHOD',
          nodePath,
          'Generated workflow contains an HTTP DELETE operation.',
        );
      }

      const url = parameters.url;
      if (typeof url !== 'string' || url.includes('{{')) {
        addBlocking(
          blocking,
          'DYNAMIC_HTTP_DESTINATION',
          nodePath,
          'HTTP Request destinations must be literal and externally reviewed.',
        );
      }
    }
  }
}

async function scanWorkspace(root) {
  const blocking = [];
  const warnings = [];
  const files = await walk(root);
  const paths = new Set(files.map((file) => file.pathFromRoot));

  for (const requiredPath of requiredSecurityFiles) {
    if (!paths.has(requiredPath)) {
      addBlocking(
        blocking,
        'SECURITY_CONTROL_MISSING',
        requiredPath,
        'Required security control is missing.',
      );
    }
  }

  await verifyControlHashes(root, blocking);

  for (const file of files) {
    if (file.error) {
      addBlocking(blocking, 'WORKSPACE_UNREADABLE', file.pathFromRoot, file.error);
      continue;
    }

    if (file.symbolicLink) {
      try {
        const metadata = await lstat(file.absolutePath);
        if (metadata.isSymbolicLink()) {
          addBlocking(
            blocking,
            'SYMLINK_REVIEW_REQUIRED',
            file.pathFromRoot,
            'Symlinks are blocked because they can escape path ownership.',
          );
        }
      } catch (error) {
        addBlocking(blocking, 'WORKSPACE_UNREADABLE', file.pathFromRoot, error.message);
      }
      continue;
    }

    let metadata;
    try {
      metadata = await stat(file.absolutePath);
    } catch (error) {
      addBlocking(blocking, 'WORKSPACE_UNREADABLE', file.pathFromRoot, error.message);
      continue;
    }

    if (metadata.size > maximumScannedFileBytes) {
      addBlocking(
        blocking,
        'FILE_TOO_LARGE_TO_SCAN',
        file.pathFromRoot,
        `File exceeds the ${maximumScannedFileBytes}-byte fail-closed scan limit.`,
      );
      continue;
    }

    let content;
    try {
      content = await readFile(file.absolutePath);
    } catch (error) {
      addBlocking(blocking, 'WORKSPACE_UNREADABLE', file.pathFromRoot, error.message);
      continue;
    }

    const text = content.toString('utf8');
    for (const [id, pattern] of secretPatterns) {
      if (pattern.test(text)) {
        addBlocking(
          blocking,
          'HIGH_CONFIDENCE_SECRET',
          file.pathFromRoot,
          `Detected ${id}. Replace it with a credential or environment-variable reference.`,
        );
      }
    }

    if (!file.pathFromRoot.startsWith('workflows/generated/')) continue;
    if (!file.pathFromRoot.endsWith('.json')) {
      addBlocking(
        blocking,
        'GENERATED_WORKFLOW_FORMAT_UNSUPPORTED',
        file.pathFromRoot,
        'Fail-closed workflow inspection currently accepts canonical JSON exports only.',
      );
      continue;
    }

    let parsed;
    try {
      parsed = JSON.parse(text);
    } catch (error) {
      addBlocking(blocking, 'INVALID_WORKFLOW_JSON', file.pathFromRoot, error.message);
      continue;
    }

    for (const workflow of workflowObjects(parsed)) {
      scanWorkflow(workflow, file.pathFromRoot, blocking);
    }
  }

  return { blocking, warnings };
}

async function currentWorkspaceSnapshotId(root) {
  const files = {};
  for (const file of await walk(root)) {
    if (file.error) throw new Error(file.error);
    if (file.symbolicLink) throw new Error(`Cannot snapshot symlink ${file.pathFromRoot}.`);
    if (file.pathFromRoot.startsWith('artifacts/agent-runs/')) continue;
    if (file.pathFromRoot.startsWith('.codex/authorization-consumption/')) continue;
    const content = await readFile(file.absolutePath);
    files[file.pathFromRoot] = sha256(content);
  }
  return `sha256:${sha256(canonicalize({ files }))}`;
}

async function verifyCurrentRunLedger(root, report) {
  const ledgerPath = resolve(root, 'artifacts/agent-runs/current.json');
  try {
    const output = execFileSync(
      process.execPath,
      [resolve(root, '.codex/hooks/validate-agent-run.mjs'), ledgerPath],
      { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] },
    );
    const validation = JSON.parse(output);
    if (!validation.valid) throw new Error(JSON.stringify(validation.errors));

    const ledger = JSON.parse(await readFile(ledgerPath, 'utf8'));
    const currentSnapshotId = await currentWorkspaceSnapshotId(root);
    if (ledger.integratedSnapshotId !== currentSnapshotId) {
      throw new Error(
        `Current workspace snapshot ${currentSnapshotId} does not match `
        + `signed integrated snapshot ${ledger.integratedSnapshotId}.`,
      );
    }
    return ledger;
  } catch (error) {
    addBlocking(
      report.blocking,
      'SIGNED_RUN_LEDGER_INVALID',
      'artifacts/agent-runs/current.json',
      error.stderr?.toString() || error.message,
    );
    return null;
  }
}

async function applySignedCapabilityApprovals(root, report, ledger) {
  if (!ledger || !Array.isArray(ledger.capabilityApprovals)) return;
  const approved = new Set();
  for (const approval of ledger.capabilityApprovals) {
    const artifactPath = resolve(root, approval.reviewedArtifactPath);
    try {
      const content = await readFile(artifactPath);
      if (sha256(content) === approval.reviewedArtifactSha256) {
        approved.add(`${approval.reviewedArtifactPath}\0${approval.capability}`);
      }
    } catch {
      // The original blocking finding remains fail-closed.
    }
  }
  report.blocking = report.blocking.filter((finding) => {
    if (finding.rule !== 'PROHIBITED_N8N_NODE') return true;
    const artifactPath = finding.path.split('#', 1)[0];
    return !approved.has(`${artifactPath}\0${finding.details?.nodeType}`);
  });
}

async function runSelfTest() {
  const encodedProhibitedWorkflow = JSON.parse(
    '{"nodes":[{"type":"n8n-nodes-base\\u002eexecuteCommand","parameters":{}}]}',
  );
  const blocking = [];
  scanWorkflow(encodedProhibitedWorkflow, 'synthetic.json', blocking);

  const syntheticOpenAiKey = `sk-${'A'.repeat(24)}`;
  const syntheticAwsKey = `AKIA${'B'.repeat(16)}`;
  const safe = 'bearer_token_env_var = "N8N_MCP_TOKEN"';
  const results = {
    safeReferenceAccepted: !secretPatterns.some(([, pattern]) => pattern.test(safe)),
    openAiSecretDetected: secretPatterns.some(([, pattern]) => pattern.test(syntheticOpenAiKey)),
    awsSecretDetected: secretPatterns.some(([, pattern]) => pattern.test(syntheticAwsKey)),
    escapedNodeTypeDetected: blocking.some((finding) => finding.rule === 'PROHIBITED_N8N_NODE'),
  };

  const valid = Object.values(results).every(Boolean);
  console.log(JSON.stringify({ valid, results }, null, 2));
  return valid ? 0 : 1;
}

function emitHookFailure(error) {
  console.log(JSON.stringify({
    decision: 'block',
    reason: 'Security completion gate crashed and failed closed: '
      + (error instanceof Error ? error.message : String(error)),
  }));
}

async function main() {
  if (selfTest) return runSelfTest();

  const root = projectRoot();
  const report = await scanWorkspace(root);
  const ledger = await verifyCurrentRunLedger(root, report);
  await applySignedCapabilityApprovals(root, report, ledger);
  const valid = report.blocking.length === 0;

  if (hookMode) {
    if (!valid) {
      console.log(JSON.stringify({
        decision: 'block',
        reason: `Security completion gate found blocking issues: ${JSON.stringify(report)}`,
      }));
    } else if (report.warnings.length > 0) {
      console.log(JSON.stringify({
        systemMessage: `Security completion gate warnings: ${JSON.stringify(report.warnings)}`,
      }));
    }
    return 0;
  }

  console.log(JSON.stringify({ valid, root, ...report }, null, 2));
  return valid ? 0 : 1;
}

try {
  process.exitCode = await main();
} catch (error) {
  if (hookMode) {
    emitHookFailure(error);
    process.exitCode = 0;
  } else {
    console.error(JSON.stringify({
      valid: false,
      errors: [error instanceof Error ? error.message : String(error)],
    }, null, 2));
    process.exitCode = 1;
  }
}
