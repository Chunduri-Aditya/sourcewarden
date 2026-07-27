#!/usr/bin/env node

import {
  createHash,
  generateKeyPairSync,
  sign,
  verify,
} from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const workspaceRoot = resolve(dirname(fileURLToPath(import.meta.url)), '../..');

const childRoles = new Set([
  'deviation_monitor',
  'eval_tuner',
  'module_builder',
  'security_firewall',
  'skeleton_architect',
]);
const writerRoles = new Set(['eval_tuner', 'module_builder', 'skeleton_architect']);
const n8nMutationTools = new Set([
  'mcp__n8n__archive_workflow',
  'mcp__n8n__create_workflow_from_code',
  'mcp__n8n__execute_workflow',
  'mcp__n8n__publish_workflow',
  'mcp__n8n__test_workflow',
  'mcp__n8n__unpublish_workflow',
  'mcp__n8n__update_workflow',
]);
const approvableNodeCapabilities = new Set([
  'n8n-nodes-base.code',
  'n8n-nodes-base.dataTable',
  'n8n-nodes-base.executeWorkflow',
]);
const maximumAuthorizationLifetimeMs = 15 * 60 * 1000;
const protectedPrefixes = [
  '.agents/',
  '.codex/',
  'AGENTS.md',
  'config/agent-policy.yaml',
  'config/agent-orchestration.json',
  'evals/EVAL_PROTOCOL.md',
  'evals/generalized-cases.jsonl',
  'evals/workflow-cases.yaml',
  'evals/fixtures/',
  'scripts/',
];
const handoffFields = [
  'assignmentId',
  'agentInstanceId',
  'baselineSnapshotId',
  'finalSnapshotId',
  'status',
  'scopeCompleted',
  'filesChanged',
  'verificationEvidence',
  'assumptions',
  'risks',
  'requestedNextAction',
];

function canonicalize(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalize).join(',')}]`;
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map(
      (key) => `${JSON.stringify(key)}:${canonicalize(value[key])}`,
    ).join(',')}}`;
  }
  return JSON.stringify(value);
}

function withoutAttestation(ledger) {
  const copy = structuredClone(ledger);
  delete copy.attestation;
  return copy;
}

function ledgerSignature(ledger, privateKey) {
  return sign(
    null,
    Buffer.from(canonicalize(withoutAttestation(ledger))),
    privateKey,
  ).toString('base64');
}

function snapshotId(snapshot) {
  return `sha256:${createHash('sha256').update(canonicalize(snapshot)).digest('hex')}`;
}

function fileHash(content) {
  return createHash('sha256').update(content).digest('hex');
}

function normalizedRelativePath(value) {
  if (typeof value !== 'string') return null;
  const path = value.replaceAll('\\', '/').replace(/^\.\/+/, '');
  if (!path || path.startsWith('/') || path.split('/').includes('..')) return null;
  return path;
}

function pathMatchesPrefix(path, prefix) {
  const normalizedPrefix = prefix.replaceAll('\\', '/').replace(/^\.\/+/, '');
  return normalizedPrefix.endsWith('/')
    ? path.startsWith(normalizedPrefix)
    : path === normalizedPrefix;
}

function pathsEqual(left, right) {
  return JSON.stringify([...left].sort()) === JSON.stringify([...right].sort());
}

function changedPaths(before, after) {
  const paths = new Set([
    ...Object.keys(before.files ?? {}),
    ...Object.keys(after.files ?? {}),
  ]);
  return [...paths].filter((path) => before.files?.[path] !== after.files?.[path]).sort();
}

function safeSnapshot(snapshot) {
  if (!snapshot || typeof snapshot !== 'object' || Array.isArray(snapshot)) return false;
  if (!snapshot.files || typeof snapshot.files !== 'object' || Array.isArray(snapshot.files)) {
    return false;
  }
  return Object.entries(snapshot.files).every(
    ([path, hash]) => normalizedRelativePath(path) === path
      && typeof hash === 'string'
      && /^[a-f0-9]{64}$/.test(hash),
  );
}

function verifyAttestation(ledger, publicKey, errors) {
  const attestation = ledger.attestation;
  if (attestation?.algorithm !== 'ed25519') {
    errors.push('Ledger attestation algorithm must be ed25519.');
    return;
  }
  if (typeof attestation.keyId !== 'string' || !attestation.keyId) {
    errors.push('Ledger attestation needs a non-empty keyId.');
  }
  if (typeof attestation.signature !== 'string' || !/^[A-Za-z0-9+/]+={0,2}$/.test(attestation.signature)) {
    errors.push('Ledger attestation signature must be base64.');
    return;
  }
  if (!publicKey) {
    errors.push('A trusted agent-ledger public key is required.');
    return;
  }

  const valid = verify(
    null,
    Buffer.from(canonicalize(withoutAttestation(ledger))),
    publicKey,
    Buffer.from(attestation.signature, 'base64'),
  );
  if (!valid) {
    errors.push('Ledger attestation signature is invalid.');
  }
}

function moduleMap(manifest, errors) {
  const modules = new Map();
  const ownerships = [];
  for (const module of manifest?.modules ?? []) {
    if (
      typeof module?.name === 'string'
      && module.name
      && Array.isArray(module.ownedPaths)
      && module.ownedPaths.length > 0
      && module.ownedPaths.every(
        (path) => normalizedRelativePath(path) === path && path.endsWith('/'),
      )
    ) {
      if (modules.has(module.name)) {
        errors.push(`Module manifest contains duplicate name ${module.name}.`);
        continue;
      }
      for (const path of module.ownedPaths) {
        for (const existing of ownerships) {
          if (
            pathMatchesPrefix(path, existing.path)
            || pathMatchesPrefix(existing.path, path)
          ) {
            errors.push(
              `Module ownership overlaps: ${module.name}:${path} and `
              + `${existing.moduleName}:${existing.path}.`,
            );
          }
        }
        ownerships.push({ moduleName: module.name, path });
      }
      modules.set(module.name, module);
    } else {
      errors.push('Every manifest module needs a unique non-empty name and safe directory ownedPaths.');
    }
  }
  return modules;
}

function verifyIndependentEvaluation(ledger, publicKey, errors) {
  const reports = ledger.independentEvaluation?.reports;
  if (!Array.isArray(reports) || reports.length !== 2) {
    errors.push('Tuning requires exactly two independently signed evaluation reports.');
    return;
  }

  const expectedSplits = new Set(['external_validation', 'blind_holdout']);
  const observedSplits = new Set();
  for (const [index, report] of reports.entries()) {
    const label = `independentEvaluation.reports[${index}]`;
    if (report?.version !== 1 || report?.kind !== 'independent-evaluation') {
      errors.push(`${label} has an unsupported evidence contract.`);
    }
    if (!expectedSplits.has(report?.split) || observedSplits.has(report?.split)) {
      errors.push(`${label} has an invalid or duplicate split.`);
    }
    observedSplits.add(report?.split);
    if (
      report?.runId !== ledger.runId
      || report?.candidateSnapshotId !== ledger.integratedSnapshotId
    ) {
      errors.push(`${label} is not bound to this run and candidate snapshot.`);
    }
    for (const field of ['caseSetSha256', 'resultArtifactSha256']) {
      if (!/^[a-f0-9]{64}$/.test(report?.[field] ?? '')) {
        errors.push(`${label}.${field} must be a SHA-256 digest.`);
      }
    }
    if (!Number.isInteger(report?.caseCount) || report.caseCount < 12) {
      errors.push(`${label}.caseCount must cover at least 12 external cases.`);
    }
    if (
      report?.valid !== true
      || report?.hardAssertionsPassed !== true
      || report?.securityRegression !== false
    ) {
      errors.push(`${label} does not prove a passing, regression-free evaluation.`);
    }
    const attestation = report?.attestation;
    if (
      attestation?.algorithm !== 'ed25519'
      || typeof attestation?.keyId !== 'string'
      || !attestation.keyId
      || typeof attestation?.signature !== 'string'
      || !publicKey
    ) {
      errors.push(`${label} lacks a valid external Ed25519 attestation contract.`);
      continue;
    }
    const unsigned = structuredClone(report);
    delete unsigned.attestation;
    if (!verify(
      null,
      Buffer.from(canonicalize(unsigned)),
      publicKey,
      Buffer.from(attestation.signature, 'base64'),
    )) {
      errors.push(`${label} has an invalid external signature.`);
    }

    const receipt = report?.suiteValidationReceipt;
    if (
      receipt?.version !== 1
      || receipt?.kind !== 'external-suite-validation'
      || receipt?.mode !== 'external'
      || receipt?.split !== report?.split
      || receipt?.caseSetSha256 !== report?.caseSetSha256
      || receipt?.caseCount !== report?.caseCount
      || receipt?.requiredCategoriesComplete !== true
      || receipt?.hardAssertionsComplete !== true
      || receipt?.valid !== true
    ) {
      errors.push(`${label} lacks a passing, hash-bound external-suite validation receipt.`);
      continue;
    }
    const receiptAttestation = receipt.attestation;
    if (
      receiptAttestation?.algorithm !== 'ed25519'
      || typeof receiptAttestation?.keyId !== 'string'
      || !receiptAttestation.keyId
      || typeof receiptAttestation?.signature !== 'string'
    ) {
      errors.push(`${label} external-suite receipt is not independently signed.`);
      continue;
    }
    const unsignedReceipt = structuredClone(receipt);
    delete unsignedReceipt.attestation;
    if (!verify(
      null,
      Buffer.from(canonicalize(unsignedReceipt)),
      publicKey,
      Buffer.from(receiptAttestation.signature, 'base64'),
    )) {
      errors.push(`${label} external-suite receipt signature is invalid.`);
    }
  }
  for (const split of expectedSplits) {
    if (!observedSplits.has(split)) errors.push(`Missing independent evaluation split ${split}.`);
  }
}

function reviewFor(handoff, role, decisions, stopSequence) {
  return decisions.find(
    (decision) => decision.role === role
      && decision.phase === 'review'
      && decision.assignmentId === handoff.assignmentId
      && decision.finalSnapshotId === handoff.finalSnapshotId
      && decision.seq > stopSequence,
  );
}

function validateLedger(ledger, manifest, publicKey) {
  const errors = [];
  if (ledger?.version !== 2) errors.push('Ledger version must be 2.');
  if (!['build', 'tuning'].includes(ledger?.runType)) {
    errors.push('runType must be build or tuning.');
  }
  if (typeof ledger?.runId !== 'string' || !ledger.runId) errors.push('Ledger needs a runId.');
  if (!Array.isArray(ledger?.events) || ledger.events.length === 0) {
    return [...errors, 'Ledger needs a non-empty events array.'];
  }
  verifyAttestation(ledger, publicKey, errors);

  const mutations = ledger.n8nMutations ?? [];
  if (!Array.isArray(mutations)) {
    errors.push('n8nMutations must be an array when present.');
  } else if (mutations.length > 0) {
    const issuedAt = Date.parse(ledger.issuedAt);
    const validUntil = Date.parse(ledger.validUntil);
    if (
      !Number.isFinite(issuedAt)
      || !Number.isFinite(validUntil)
      || validUntil <= issuedAt
      || validUntil - issuedAt > maximumAuthorizationLifetimeMs
      || validUntil <= Date.now()
    ) {
      errors.push('n8n mutation authorization must have a current lifetime of at most 15 minutes.');
    }
    if (typeof ledger.sessionId !== 'string' || !ledger.sessionId) {
      errors.push('n8n mutation authorization must be bound to a sessionId.');
    }
    const nonces = new Set();
    for (const [index, mutation] of mutations.entries()) {
      const label = `n8nMutations[${index}]`;
      if (!n8nMutationTools.has(mutation?.toolName)) {
        errors.push(`${label}.toolName is not an approved mutation tool.`);
      }
      for (const field of ['toolInputSha256', 'reviewedArtifactSha256']) {
        if (!/^[a-f0-9]{64}$/.test(mutation?.[field] ?? '')) {
          errors.push(`${label}.${field} must be a SHA-256 digest.`);
        }
      }
      if (
        mutation?.integratedSnapshotId !== ledger.integratedSnapshotId
        || mutation?.sessionId !== ledger.sessionId
      ) {
        errors.push(`${label} is not bound to the integrated snapshot and session.`);
      }
      if (
        typeof mutation?.authorizationNonce !== 'string'
        || !/^[A-Za-z0-9_-]{22,128}$/.test(mutation.authorizationNonce)
        || nonces.has(mutation.authorizationNonce)
      ) {
        errors.push(`${label}.authorizationNonce must be strong and unique.`);
      }
      nonces.add(mutation?.authorizationNonce);
      if (
        typeof mutation?.reviewedArtifactPath !== 'string'
        || normalizedRelativePath(mutation.reviewedArtifactPath) !== mutation.reviewedArtifactPath
        || !mutation.reviewedArtifactPath.startsWith('workflows/generated/')
        || !mutation.reviewedArtifactPath.endsWith('.json')
      ) {
        errors.push(`${label}.reviewedArtifactPath must name canonical generated workflow JSON.`);
      }
      if (
        mutation?.explicitUserApproval !== true
        || mutation?.approvalScope !== mutation?.toolName
      ) {
        errors.push(`${label} lacks exact user-approval scope.`);
      }
    }
  }

  const capabilityApprovals = ledger.capabilityApprovals ?? [];
  if (!Array.isArray(capabilityApprovals)) {
    errors.push('capabilityApprovals must be an array when present.');
  } else {
    const approvalKeys = new Set();
    for (const [index, approval] of capabilityApprovals.entries()) {
      const label = `capabilityApprovals[${index}]`;
      if (!approvableNodeCapabilities.has(approval?.capability)) {
        errors.push(`${label}.capability is not eligible for a signed exception.`);
      }
      if (
        typeof approval?.reviewedArtifactPath !== 'string'
        || normalizedRelativePath(approval.reviewedArtifactPath) !== approval.reviewedArtifactPath
        || !approval.reviewedArtifactPath.startsWith('workflows/generated/')
        || !approval.reviewedArtifactPath.endsWith('.json')
      ) {
        errors.push(`${label}.reviewedArtifactPath must name generated workflow JSON.`);
      }
      if (!/^[a-f0-9]{64}$/.test(approval?.reviewedArtifactSha256 ?? '')) {
        errors.push(`${label}.reviewedArtifactSha256 must be a SHA-256 digest.`);
      }
      if (
        approval?.integratedSnapshotId !== ledger.integratedSnapshotId
        || approval?.explicitUserApproval !== true
        || approval?.approvalScope !== approval?.capability
      ) {
        errors.push(`${label} is not bound to the snapshot and exact user-approval scope.`);
      }
      const key = `${approval?.reviewedArtifactPath}\0${approval?.capability}`;
      if (approvalKeys.has(key)) errors.push(`${label} duplicates a capability approval.`);
      approvalKeys.add(key);
    }
  }

  const snapshots = ledger.snapshots ?? {};
  for (const [id, snapshot] of Object.entries(snapshots)) {
    if (!safeSnapshot(snapshot)) {
      errors.push(`Snapshot ${id} is malformed.`);
    } else if (snapshotId(snapshot) !== id) {
      errors.push(`Snapshot ${id} does not match its recomputed content hash.`);
    }
  }
  if (!snapshots[ledger.initialSnapshotId]) errors.push('initialSnapshotId is missing.');
  if (!snapshots[ledger.integratedSnapshotId]) errors.push('integratedSnapshotId is missing.');

  const modules = moduleMap(manifest, errors);
  if (ledger.runType === 'build' && modules.size === 0) {
    errors.push('A build ledger requires at least one manifest module.');
  }
  const skeletonOwnedPaths = ledger.skeletonOwnedPaths ?? [];
  if (
    ledger.runType === 'build'
    && (
      !Array.isArray(skeletonOwnedPaths)
      || skeletonOwnedPaths.length === 0
      || skeletonOwnedPaths.some((path) => normalizedRelativePath(path) !== path)
    )
  ) {
    errors.push('A build ledger requires safe, non-empty skeletonOwnedPaths.');
  }
  for (const skeletonPath of skeletonOwnedPaths) {
    for (const module of modules.values()) {
      for (const modulePath of module.ownedPaths) {
        if (
          pathMatchesPrefix(skeletonPath, modulePath)
          || pathMatchesPrefix(modulePath, skeletonPath)
        ) {
          errors.push(
            `Skeleton ownership ${skeletonPath} overlaps module `
            + `${module.name}:${modulePath}.`,
          );
        }
      }
    }
  }

  const active = new Map();
  const starts = new Map();
  const stops = new Map();
  const handoffs = [];
  const monitorDecisions = [];
  const securityDecisions = [];
  const seenAgentInstances = new Set();
  let previousSequence = -1;

  for (const [index, event] of ledger.events.entries()) {
    const label = `events[${index}]`;
    if (!Number.isInteger(event.seq) || event.seq <= previousSequence) {
      errors.push(`${label}: seq must be a strictly increasing integer.`);
    }
    previousSequence = event.seq;

    if (event.event === 'agent_start') {
      if (!childRoles.has(event.role)) errors.push(`${label}: unknown child role ${event.role}.`);
      if (typeof event.agentInstanceId !== 'string' || !event.agentInstanceId) {
        errors.push(`${label}: missing agentInstanceId.`);
        continue;
      }
      if (active.has(event.agentInstanceId) || seenAgentInstances.has(event.agentInstanceId)) {
        errors.push(`${label}: agentInstanceId must identify exactly one lifecycle.`);
      }
      seenAgentInstances.add(event.agentInstanceId);
      active.set(event.agentInstanceId, event);
      starts.set(event.agentInstanceId, event);
      if (active.size > 3) errors.push(`${label}: more than three child agents are active.`);

      const activeWriters = [...active.values()].filter((item) => writerRoles.has(item.role));
      if (activeWriters.length > 1) errors.push(`${label}: concurrent writers are forbidden.`);
      if (
        writerRoles.has(event.role)
        && [...active.values()].some(
          (item) => ['deviation_monitor', 'security_firewall'].includes(item.role),
        )
      ) errors.push(`${label}: writer and post-write reviewers may not overlap.`);
      if (
        ['deviation_monitor', 'security_firewall'].includes(event.role)
        && activeWriters.length > 0
      ) errors.push(`${label}: reviewer started before the writer stopped.`);
      continue;
    }

    if (event.event === 'agent_stop') {
      const start = active.get(event.agentInstanceId);
      if (!start) errors.push(`${label}: stop has no matching active agent.`);
      else if (start.role !== event.role) errors.push(`${label}: stop role does not match start.`);
      active.delete(event.agentInstanceId);
      stops.set(event.agentInstanceId, event);
      continue;
    }

    if (event.event === 'writer_handoff') {
      if (!writerRoles.has(event.role)) errors.push(`${label}: invalid writer role.`);
      const start = active.get(event.agentInstanceId);
      if (!start || start.role !== event.role) {
        errors.push(`${label}: writer handoff must occur during its lifecycle.`);
      }
      for (const field of handoffFields) {
        if (!(field in event)) errors.push(`${label}: missing handoff field ${field}.`);
      }
      if (event.status !== 'COMPLETE') errors.push(`${label}: handoff status must be COMPLETE.`);
      if (
        !Array.isArray(event.verificationEvidence)
        || event.verificationEvidence.length === 0
        || event.verificationEvidence.some((item) => typeof item !== 'string' || !item)
      ) errors.push(`${label}: verificationEvidence must contain non-empty strings.`);

      const before = snapshots[event.baselineSnapshotId];
      const after = snapshots[event.finalSnapshotId];
      if (!before || !after) {
        errors.push(`${label}: handoff references an unknown snapshot.`);
      } else {
        const actualChanged = changedPaths(before, after);
        if (!Array.isArray(event.filesChanged) || !pathsEqual(event.filesChanged, actualChanged)) {
          errors.push(`${label}: filesChanged does not match the recomputed snapshot diff.`);
        }
        for (const path of actualChanged) {
          if (protectedPrefixes.some((prefix) => pathMatchesPrefix(path, prefix))) {
            errors.push(`${label}: writer changed protected path ${path}.`);
          }
        }

        let ownedPaths = [];
        if (event.role === 'skeleton_architect') {
          ownedPaths = ledger.skeletonOwnedPaths ?? [];
        } else if (event.role === 'module_builder') {
          const module = modules.get(event.moduleId);
          if (!module) errors.push(`${label}: unknown moduleId ${event.moduleId}.`);
          ownedPaths = module?.ownedPaths ?? [];
        } else if (event.role === 'eval_tuner') {
          ownedPaths = [
            `tuning/proposals/${ledger.runId}/`,
            `evals/results/${ledger.runId}/`,
          ];
        }
        for (const path of actualChanged) {
          if (!ownedPaths.some((prefix) => pathMatchesPrefix(path, prefix))) {
            errors.push(`${label}: ${path} is outside ${event.role} ownership.`);
          }
        }
      }
      handoffs.push(event);
      continue;
    }

    if (event.event === 'monitor_decision') {
      const reviewer = active.get(event.agentInstanceId);
      if (!reviewer || reviewer.role !== 'deviation_monitor' || event.role !== 'deviation_monitor') {
        errors.push(`${label}: monitor decision must occur during its matching lifecycle.`);
      }
      if (!['ALIGNED', 'WARNING', 'STOP', 'SECURITY_ESCALATION'].includes(event.decision)) {
        errors.push(`${label}: invalid monitor decision.`);
      }
      monitorDecisions.push(event);
      continue;
    }

    if (event.event === 'security_decision') {
      const reviewer = active.get(event.agentInstanceId);
      if (!reviewer || reviewer.role !== 'security_firewall' || event.role !== 'security_firewall') {
        errors.push(`${label}: security decision must occur during its matching lifecycle.`);
      }
      if (!['ALLOW', 'ALLOW_WITH_CONDITIONS', 'DENY'].includes(event.decision)) {
        errors.push(`${label}: invalid security decision.`);
      }
      if (event.decision === 'ALLOW_WITH_CONDITIONS' && event.conditionsSatisfied !== true) {
        errors.push(`${label}: security conditions are not satisfied.`);
      }
      securityDecisions.push(event);
      continue;
    }

    errors.push(`${label}: unknown event type ${event.event}.`);
  }

  if (active.size > 0) errors.push('Every agent_start must have a matching agent_stop.');

  const writerStarts = [...starts.values()]
    .filter((event) => writerRoles.has(event.role))
    .sort((left, right) => left.seq - right.seq);
  const preflights = securityDecisions.filter((event) => event.phase === 'preflight');
  if (preflights.length !== 1) errors.push('Exactly one security preflight is required.');
  const preflight = preflights[0];
  if (preflight?.decision === 'DENY') errors.push('A preflight DENY invalidates the run.');
  if (
    preflight
    && writerStarts[0]
    && (
      preflight.seq >= writerStarts[0].seq
      || !['ALLOW', 'ALLOW_WITH_CONDITIONS'].includes(preflight.decision)
    )
  ) errors.push('An acceptable security preflight must precede every writer.');

  const skeletonHandoffs = handoffs.filter((handoff) => handoff.role === 'skeleton_architect');
  const moduleHandoffs = handoffs.filter((handoff) => handoff.role === 'module_builder');
  const tunerHandoffs = handoffs.filter((handoff) => handoff.role === 'eval_tuner');
  if (ledger.runType === 'build') {
    if (skeletonHandoffs.length !== 1) errors.push('A build requires exactly one skeleton handoff.');
    if (tunerHandoffs.length !== 0) errors.push('A build ledger cannot contain eval-tuner writes.');
    const counts = new Map();
    for (const handoff of moduleHandoffs) {
      counts.set(handoff.moduleId, (counts.get(handoff.moduleId) ?? 0) + 1);
    }
    for (const moduleName of modules.keys()) {
      if (counts.get(moduleName) !== 1) {
        errors.push(`Manifest module ${moduleName} requires exactly one builder handoff.`);
      }
    }
    for (const moduleName of counts.keys()) {
      if (!modules.has(moduleName)) errors.push(`Unknown implemented module ${moduleName}.`);
    }
    if (moduleHandoffs.length !== modules.size) {
      errors.push('Module handoff count must equal the manifest module count.');
    }
    if (
      new Set(moduleHandoffs.map((handoff) => handoff.agentInstanceId)).size
      !== moduleHandoffs.length
    ) errors.push('Each module requires a fresh builder agent instance.');
  }
  if (ledger.runType === 'tuning') {
    if (tunerHandoffs.length !== 1) errors.push('A tuning run requires exactly one tuner handoff.');
    if (skeletonHandoffs.length || moduleHandoffs.length) {
      errors.push('A tuning ledger cannot contain skeleton or module writes.');
    }
    verifyIndependentEvaluation(ledger, publicKey, errors);
  }

  const orderedHandoffs = [...handoffs].sort((left, right) => left.seq - right.seq);
  const postWriteReviewSequences = [];
  let expectedBaseline = ledger.initialSnapshotId;
  for (const [index, handoff] of orderedHandoffs.entries()) {
    if (handoff.baselineSnapshotId !== expectedBaseline) {
      errors.push(`Writer ${handoff.assignmentId} baseline does not continue the snapshot chain.`);
    }
    expectedBaseline = handoff.finalSnapshotId;
    const stop = stops.get(handoff.agentInstanceId);
    if (!stop || stop.seq <= handoff.seq) {
      errors.push(`Writer ${handoff.assignmentId} must stop after finalizing its handoff.`);
      continue;
    }

    const monitor = reviewFor(handoff, 'deviation_monitor', monitorDecisions, stop.seq);
    const security = reviewFor(handoff, 'security_firewall', securityDecisions, stop.seq);
    if (!monitor) errors.push(`Writer ${handoff.assignmentId} lacks a matching monitor review.`);
    else if (monitor.decision !== 'ALIGNED') {
      errors.push(`Writer ${handoff.assignmentId} monitor decision is ${monitor.decision}.`);
    }
    if (!security) errors.push(`Writer ${handoff.assignmentId} lacks a matching security review.`);
    else if (security.decision === 'DENY') {
      errors.push(`Writer ${handoff.assignmentId} was denied by security.`);
    }
    if (monitor) {
      postWriteReviewSequences.push(
        monitor.seq,
        stops.get(monitor.agentInstanceId)?.seq ?? monitor.seq,
      );
    }
    if (security) {
      postWriteReviewSequences.push(
        security.seq,
        stops.get(security.agentInstanceId)?.seq ?? security.seq,
      );
    }

    const nextStart = starts.get(orderedHandoffs[index + 1]?.agentInstanceId);
    if (nextStart && (monitor?.seq >= nextStart.seq || security?.seq >= nextStart.seq)) {
      errors.push(`Next writer started before ${handoff.assignmentId} reviews completed.`);
    }
  }
  if (orderedHandoffs.at(-1)?.finalSnapshotId !== ledger.integratedSnapshotId) {
    errors.push('integratedSnapshotId must equal the last writer snapshot.');
  }

  const finalMonitor = monitorDecisions.find(
    (event) => event.phase === 'final'
      && event.role === 'deviation_monitor'
      && event.assignmentId === ledger.runId
      && event.finalSnapshotId === ledger.integratedSnapshotId,
  );
  const finalSecurity = securityDecisions.find(
    (event) => event.phase === 'final'
      && event.role === 'security_firewall'
      && event.assignmentId === ledger.runId
      && event.finalSnapshotId === ledger.integratedSnapshotId,
  );
  if (finalMonitor?.decision !== 'ALIGNED') {
    errors.push('Final integrated snapshot needs an ALIGNED monitor decision.');
  }
  if (!finalSecurity || !['ALLOW', 'ALLOW_WITH_CONDITIONS'].includes(finalSecurity.decision)) {
    errors.push('Final integrated snapshot needs an acceptable security decision.');
  }
  const lastWriterStopSequence = Math.max(
    -1,
    ...orderedHandoffs.map((handoff) => stops.get(handoff.agentInstanceId)?.seq ?? -1),
  );
  const finalReviewThreshold = Math.max(
    lastWriterStopSequence,
    ...postWriteReviewSequences,
  );
  if (
    !finalMonitor
    || !finalSecurity
    || finalMonitor.seq <= finalReviewThreshold
    || finalSecurity.seq <= finalReviewThreshold
  ) {
    errors.push('Final reviews must occur after every writer and post-write review.');
  }

  for (const decision of securityDecisions) {
    if (decision.decision === 'DENY') {
      errors.push(`Security DENY blocks acceptance at seq ${decision.seq}.`);
    }
  }
  for (const decision of monitorDecisions) {
    if (['STOP', 'SECURITY_ESCALATION'].includes(decision.decision)) {
      errors.push(`Monitor ${decision.decision} blocks acceptance at seq ${decision.seq}.`);
    }
  }
  if (ledger.finalDecision?.role !== 'supervisor') {
    errors.push('finalDecision.role must be supervisor.');
  }
  if (ledger.finalDecision?.decision !== 'ACCEPTED') {
    errors.push('finalDecision.decision must be ACCEPTED for a passing ledger.');
  }
  const lastEventSequence = Math.max(...ledger.events.map((event) => event.seq));
  if (
    !Number.isInteger(ledger.finalDecision?.seq)
    || ledger.finalDecision.seq <= lastEventSequence
  ) {
    errors.push('The supervisor finalDecision must be sequenced after every lifecycle event.');
  }

  return errors;
}

function makeSnapshot(files) {
  const snapshot = { files };
  return [snapshotId(snapshot), snapshot];
}

function selfTestLedger(privateKey) {
  const [initialId, initial] = makeSnapshot({
    'README.md': fileHash('initial'),
  });
  const [skeletonId, skeleton] = makeSnapshot({
    'README.md': fileHash('initial'),
    'config/module-manifest.json': fileHash('manifest'),
    'src/contracts/workflow.ts': fileHash('contract'),
  });
  const [moduleId, module] = makeSnapshot({
    'README.md': fileHash('initial'),
    'config/module-manifest.json': fileHash('manifest'),
    'src/contracts/workflow.ts': fileHash('contract'),
    'src/modules/alpha/index.ts': fileHash('module'),
    'tests/alpha/index.test.ts': fileHash('test'),
  });
  const ledger = {
    version: 2,
    runType: 'build',
    runId: 'self-test',
    moduleManifestPath: 'config/module-manifest.json',
    moduleManifestSha256: fileHash('manifest-source'),
    skeletonOwnedPaths: ['src/contracts/', 'config/module-manifest.json'],
    initialSnapshotId: initialId,
    integratedSnapshotId: moduleId,
    snapshots: {
      [initialId]: initial,
      [skeletonId]: skeleton,
      [moduleId]: module,
    },
    events: [],
    finalDecision: { role: 'supervisor', decision: 'ACCEPTED', seq: 0 },
  };
  let seq = 0;
  const push = (event) => ledger.events.push({ seq: ++seq, ...event });
  push({ event: 'agent_start', role: 'security_firewall', agentInstanceId: 'sec-pre' });
  push({
    event: 'security_decision',
    phase: 'preflight',
    role: 'security_firewall',
    agentInstanceId: 'sec-pre',
    decision: 'ALLOW',
  });
  push({ event: 'agent_stop', role: 'security_firewall', agentInstanceId: 'sec-pre' });

  const writeAndReview = ({
    role,
    instance,
    assignmentId,
    baselineSnapshotId,
    finalSnapshotId,
    filesChanged,
    moduleName,
  }) => {
    push({ event: 'agent_start', role, agentInstanceId: instance, assignmentId });
    push({
      event: 'writer_handoff',
      role,
      moduleId: moduleName,
      assignmentId,
      agentInstanceId: instance,
      baselineSnapshotId,
      finalSnapshotId,
      status: 'COMPLETE',
      scopeCompleted: [assignmentId],
      filesChanged,
      verificationEvidence: ['tests passed'],
      assumptions: [],
      risks: [],
      requestedNextAction: 'review',
    });
    push({ event: 'agent_stop', role, agentInstanceId: instance });
    push({
      event: 'agent_start',
      role: 'deviation_monitor',
      agentInstanceId: `mon-${assignmentId}`,
    });
    push({
      event: 'agent_start',
      role: 'security_firewall',
      agentInstanceId: `sec-${assignmentId}`,
    });
    push({
      event: 'monitor_decision',
      phase: 'review',
      role: 'deviation_monitor',
      agentInstanceId: `mon-${assignmentId}`,
      assignmentId,
      finalSnapshotId,
      decision: 'ALIGNED',
    });
    push({
      event: 'security_decision',
      phase: 'review',
      role: 'security_firewall',
      agentInstanceId: `sec-${assignmentId}`,
      assignmentId,
      finalSnapshotId,
      decision: 'ALLOW',
    });
    push({
      event: 'agent_stop',
      role: 'deviation_monitor',
      agentInstanceId: `mon-${assignmentId}`,
    });
    push({
      event: 'agent_stop',
      role: 'security_firewall',
      agentInstanceId: `sec-${assignmentId}`,
    });
  };

  writeAndReview({
    role: 'skeleton_architect',
    instance: 'skeleton-1',
    assignmentId: 'skeleton',
    baselineSnapshotId: initialId,
    finalSnapshotId: skeletonId,
    filesChanged: ['config/module-manifest.json', 'src/contracts/workflow.ts'],
  });
  writeAndReview({
    role: 'module_builder',
    instance: 'builder-alpha',
    assignmentId: 'module-alpha',
    moduleName: 'alpha',
    baselineSnapshotId: skeletonId,
    finalSnapshotId: moduleId,
    filesChanged: ['src/modules/alpha/index.ts', 'tests/alpha/index.test.ts'],
  });

  push({ event: 'agent_start', role: 'deviation_monitor', agentInstanceId: 'mon-final' });
  push({ event: 'agent_start', role: 'security_firewall', agentInstanceId: 'sec-final' });
  push({
    event: 'monitor_decision',
    phase: 'final',
    role: 'deviation_monitor',
    agentInstanceId: 'mon-final',
    assignmentId: ledger.runId,
    finalSnapshotId: moduleId,
    decision: 'ALIGNED',
  });
  push({
    event: 'security_decision',
    phase: 'final',
    role: 'security_firewall',
    agentInstanceId: 'sec-final',
    assignmentId: ledger.runId,
    finalSnapshotId: moduleId,
    decision: 'ALLOW',
  });
  push({ event: 'agent_stop', role: 'deviation_monitor', agentInstanceId: 'mon-final' });
  push({ event: 'agent_stop', role: 'security_firewall', agentInstanceId: 'sec-final' });
  ledger.finalDecision.seq = ++seq;
  ledger.attestation = {
    algorithm: 'ed25519',
    keyId: 'self-test',
    signature: ledgerSignature(ledger, privateKey),
  };
  return ledger;
}

const args = process.argv.slice(2);
if (args.includes('--self-test')) {
  const { privateKey, publicKey } = generateKeyPairSync('ed25519');
  const manifest = {
    modules: [{ name: 'alpha', ownedPaths: ['src/modules/alpha/', 'tests/alpha/'] }],
  };
  const safe = selfTestLedger(privateKey);
  const safeErrors = validateLedger(safe, manifest, publicKey);

  const preflightDeny = structuredClone(safe);
  preflightDeny.events.find(
    (event) => event.event === 'security_decision' && event.phase === 'preflight',
  ).decision = 'DENY';
  preflightDeny.attestation.signature = ledgerSignature(preflightDeny, privateKey);
  const denyErrors = validateLedger(preflightDeny, manifest, publicKey);

  const hiddenChange = structuredClone(safe);
  const moduleHandoff = hiddenChange.events.find(
    (event) => event.event === 'writer_handoff' && event.role === 'module_builder',
  );
  hiddenChange.snapshots[moduleHandoff.finalSnapshotId].files['AGENTS.md'] = fileHash('tamper');
  const oldFinalId = moduleHandoff.finalSnapshotId;
  const newFinalId = snapshotId(hiddenChange.snapshots[oldFinalId]);
  hiddenChange.snapshots[newFinalId] = hiddenChange.snapshots[oldFinalId];
  delete hiddenChange.snapshots[oldFinalId];
  moduleHandoff.finalSnapshotId = newFinalId;
  hiddenChange.integratedSnapshotId = newFinalId;
  for (const event of hiddenChange.events) {
    if (event.finalSnapshotId === oldFinalId) event.finalSnapshotId = newFinalId;
  }
  hiddenChange.attestation.signature = ledgerSignature(hiddenChange, privateKey);
  const hiddenErrors = validateLedger(hiddenChange, manifest, publicKey);

  const earlyFinal = structuredClone(safe);
  const isFinalLifecycle = (event) => event.phase === 'final'
    || ['mon-final', 'sec-final'].includes(event.agentInstanceId);
  const finalEvents = earlyFinal.events.filter(isFinalLifecycle);
  const nonFinalEvents = earlyFinal.events.filter((event) => !isFinalLifecycle(event));
  earlyFinal.events = [
    ...nonFinalEvents.slice(0, 3),
    ...finalEvents,
    ...nonFinalEvents.slice(3),
  ];
  earlyFinal.events.forEach((event, index) => {
    event.seq = index + 1;
  });
  earlyFinal.finalDecision.seq = earlyFinal.events.length + 1;
  earlyFinal.attestation.signature = ledgerSignature(earlyFinal, privateKey);
  const earlyFinalErrors = validateLedger(earlyFinal, manifest, publicKey);

  const overlappingManifestErrors = validateLedger(
    safe,
    {
      modules: [
        { name: 'alpha', ownedPaths: ['src/modules/alpha/', 'tests/alpha/'] },
        { name: 'beta', ownedPaths: ['src/modules/alpha/'] },
      ],
    },
    publicKey,
  );

  const unsafeCapability = structuredClone(safe);
  unsafeCapability.capabilityApprovals = [{
    capability: 'n8n-nodes-base.executeCommand',
    reviewedArtifactPath: 'workflows/generated/unsafe.json',
    reviewedArtifactSha256: fileHash('unsafe'),
    integratedSnapshotId: unsafeCapability.integratedSnapshotId,
    explicitUserApproval: true,
    approvalScope: 'n8n-nodes-base.executeCommand',
  }];
  unsafeCapability.attestation.signature = ledgerSignature(unsafeCapability, privateKey);
  const unsafeCapabilityErrors = validateLedger(unsafeCapability, manifest, publicKey);

  const evidenceLedger = {
    runId: 'tuning-self-test',
    integratedSnapshotId: safe.integratedSnapshotId,
    independentEvaluation: {
      reports: ['external_validation', 'blind_holdout'].map((split) => {
        const receipt = {
          version: 1,
          kind: 'external-suite-validation',
          mode: 'external',
          split,
          caseSetSha256: fileHash(`${split}-cases`),
          caseCount: 12,
          requiredCategoriesComplete: true,
          hardAssertionsComplete: true,
          valid: true,
        };
        receipt.attestation = {
          algorithm: 'ed25519',
          keyId: 'self-test',
          signature: sign(
            null,
            Buffer.from(canonicalize(receipt)),
            privateKey,
          ).toString('base64'),
        };
        const report = {
          version: 1,
          kind: 'independent-evaluation',
          runId: 'tuning-self-test',
          split,
          candidateSnapshotId: safe.integratedSnapshotId,
          caseSetSha256: fileHash(`${split}-cases`),
          resultArtifactSha256: fileHash(`${split}-results`),
          caseCount: 12,
          valid: true,
          hardAssertionsPassed: true,
          securityRegression: false,
          suiteValidationReceipt: receipt,
        };
        report.attestation = {
          algorithm: 'ed25519',
          keyId: 'self-test',
          signature: sign(
            null,
            Buffer.from(canonicalize(report)),
            privateKey,
          ).toString('base64'),
        };
        return report;
      }),
    },
  };
  const evidenceErrors = [];
  verifyIndependentEvaluation(evidenceLedger, publicKey, evidenceErrors);
  const booleanOnlyEvidenceErrors = [];
  verifyIndependentEvaluation(
    {
      ...evidenceLedger,
      independentEvaluation: {
        publicValidationPassed: true,
        blindHoldoutPassed: true,
        securityRegression: false,
      },
    },
    publicKey,
    booleanOnlyEvidenceErrors,
  );

  const valid = safeErrors.length === 0
    && denyErrors.some((error) => error.includes('preflight DENY'))
    && hiddenErrors.some((error) => error.includes('filesChanged does not match'))
    && hiddenErrors.some((error) => error.includes('protected path AGENTS.md'))
    && earlyFinalErrors.some((error) => error.includes('Final reviews must occur after'))
    && overlappingManifestErrors.some((error) => error.includes('Module ownership overlaps'))
    && unsafeCapabilityErrors.some((error) => error.includes('not eligible'))
    && evidenceErrors.length === 0
    && booleanOnlyEvidenceErrors.some(
      (error) => error.includes('exactly two independently signed evaluation reports'),
    );
  console.log(JSON.stringify({
    valid,
    safeErrors,
    denyErrors,
    hiddenErrors,
    earlyFinalErrors,
    overlappingManifestErrors,
    unsafeCapabilityErrors,
    evidenceErrors,
    booleanOnlyEvidenceErrors,
  }, null, 2));
  process.exit(valid ? 0 : 1);
}

if (args.length !== 1) {
  console.error('Usage: node scripts/validate-agent-run.mjs <ledger.json>');
  process.exit(2);
}

try {
  const ledger = JSON.parse(await readFile(resolve(workspaceRoot, args[0]), 'utf8'));
  if (ledger.moduleManifest && !ledger.moduleManifestPath) {
    throw new Error('Embedded moduleManifest is forbidden; use a hash-bound moduleManifestPath.');
  }
  if (ledger.moduleManifestPath !== 'config/module-manifest.json') {
    throw new Error('moduleManifestPath must be config/module-manifest.json.');
  }
  const manifestPath = resolve(workspaceRoot, ledger.moduleManifestPath);
  const manifestContent = await readFile(manifestPath);
  if (fileHash(manifestContent) !== ledger.moduleManifestSha256) {
    throw new Error('moduleManifestSha256 does not match the actual manifest.');
  }
  const manifest = JSON.parse(manifestContent.toString('utf8'));
  const publicKeyContent = await readFile(
    resolve(workspaceRoot, '.codex/agent-ledger-public-key.pem'),
  );
  const trustedFingerprint = process.env.WORKFLOW_TRUST_ROOT_SHA256;
  if (!/^[a-f0-9]{64}$/.test(trustedFingerprint ?? '')) {
    throw new Error('WORKFLOW_TRUST_ROOT_SHA256 must be supplied by managed external policy.');
  }
  if (fileHash(publicKeyContent) !== trustedFingerprint) {
    throw new Error('The installed ledger public key does not match the external trust-root pin.');
  }
  const publicKey = publicKeyContent.toString('utf8');
  const errors = validateLedger(ledger, manifest, publicKey);
  console.log(JSON.stringify({
    valid: errors.length === 0,
    runId: ledger.runId,
    errors,
  }, null, 2));
  process.exit(errors.length === 0 ? 0 : 1);
} catch (error) {
  console.error(JSON.stringify({ valid: false, errors: [error.message] }, null, 2));
  process.exit(1);
}
