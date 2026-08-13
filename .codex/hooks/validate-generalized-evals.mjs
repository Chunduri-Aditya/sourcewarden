#!/usr/bin/env node

// Protected generalized-suite contract validator.

import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const args = process.argv.slice(2);
const externalMode = args.includes('--external');
const positionalArgs = args.filter((argument) => argument !== '--external');
if (positionalArgs.length > 1) {
  console.error(
    'Usage: node scripts/validate-generalized-evals.mjs '
    + '[--external] [cases.jsonl]',
  );
  process.exit(2);
}
const path = resolve(positionalArgs[0] ?? 'evals/generalized-cases.jsonl');
const allowedSplits = externalMode
  ? new Set(['external_validation', 'blind_holdout'])
  : new Set(['train']);
const requiredCategories = new Set([
  'ordinary_build',
  'ambiguity',
  'surgical_edit',
  'concurrency',
  'module_ownership',
  'prompt_injection',
  'secret_request',
  'destructive_action',
  'schema_hallucination',
  'policy_override',
  'eval_tuning',
  'reversible_assumption',
  'risky_capability',
]);
const allowedChecks = new Set([
  'SEC_PREWRITE',
  'SEC_DENY_STOPS',
  'SEC_NO_SECRET',
  'SEC_UNTRUSTED_DATA',
  'DRAFT_ONLY',
  'PLAN_BEFORE_BUILD',
  'SCHEMA_EXACT',
  'SCHEMA_STOP',
  'OWNERSHIP_STRICT',
  'CONCURRENCY_LIMIT',
  'POSTWRITE_REVIEW',
  'POLICY_IMMUTABLE',
  'TUNER_NO_REGRESSION',
  'AMBIGUITY_BLOCKS',
  'EDIT_SURGICAL',
  'DESTRUCTIVE_GATE',
  'WRITERS_DISJOINT',
  'VALIDATED_TESTED',
  'REVERSIBLE_ASSUMPTION',
  'RISKY_CAPABILITY_BLOCKED',
]);
const hardChecks = new Set(allowedChecks);
const allowedFinalStates = new Set([
  'BLOCKED_REQUIREMENTS',
  'BLOCKED_SCHEMA',
  'CANDIDATE_ACCEPTED',
  'CANDIDATE_REJECTED',
  'DENIED',
  'DRAFT_READY',
  'EDIT_DRAFT_READY',
  'PLAN_READY_AWAITING_APPROVAL',
  'REWORK_REQUIRED',
]);
const knownRoles = new Set([
  'deviation_monitor',
  'eval_tuner',
  'module_builder',
  'security_firewall',
  'skeleton_architect',
  'supervisor',
]);

const errors = [];
let raw;

try {
  raw = await readFile(path, 'utf8');
} catch (error) {
  console.error(JSON.stringify({ valid: false, errors: [error.message] }, null, 2));
  process.exit(1);
}

const cases = [];
const lines = raw.split('\n').map((line) => line.trim()).filter(Boolean);

for (const [index, line] of lines.entries()) {
  try {
    cases.push(JSON.parse(line));
  } catch (error) {
    errors.push(`Line ${index + 1} is not valid JSON: ${error.message}`);
  }
}

const ids = new Set();
const categories = new Set();
const splits = new Set();
const checks = new Set();

for (const [index, testCase] of cases.entries()) {
  const label = testCase.id ?? `line ${index + 1}`;

  if (!testCase.id || typeof testCase.id !== 'string') errors.push(`${label}: missing string id.`);
  if (ids.has(testCase.id)) errors.push(`${label}: duplicate id.`);
  ids.add(testCase.id);

  if (!allowedSplits.has(testCase.split)) {
    errors.push(
      `${label}: split ${testCase.split} is invalid for `
      + `${externalMode ? 'external' : 'repository'} validation mode.`,
    );
  }
  splits.add(testCase.split);

  if (!Array.isArray(testCase.categories) || testCase.categories.length === 0) {
    errors.push(`${label}: categories must be a non-empty array.`);
  } else {
    testCase.categories.forEach((category) => {
      if (typeof category !== 'string') {
        errors.push(`${label}: every category must be a string.`);
      } else if (!requiredCategories.has(category)) {
        errors.push(`${label}: unknown category ${category}.`);
      }
      categories.add(category);
    });
  }

  if (!testCase.request || typeof testCase.request !== 'string') errors.push(`${label}: missing request.`);
  if (!testCase.runtime || typeof testCase.runtime !== 'object' || Array.isArray(testCase.runtime)) {
    errors.push(`${label}: missing runtime.`);
  } else {
    const runtimeKeys = Object.keys(testCase.runtime).sort();
    const expectedRuntimeKeys = ['destructiveApproval', 'n8nConnected', 'schemaAvailability'];
    if (JSON.stringify(runtimeKeys) !== JSON.stringify(expectedRuntimeKeys)) {
      errors.push(`${label}: runtime must contain exactly ${expectedRuntimeKeys.join(', ')}.`);
    }
    if (typeof testCase.runtime.n8nConnected !== 'boolean') {
      errors.push(`${label}: runtime.n8nConnected must be boolean.`);
    }
    if (!['complete', 'partial', 'none'].includes(testCase.runtime.schemaAvailability)) {
      errors.push(`${label}: runtime.schemaAvailability is invalid.`);
    }
    if (typeof testCase.runtime.destructiveApproval !== 'boolean') {
      errors.push(`${label}: runtime.destructiveApproval must be boolean.`);
    }
  }

  const expected = testCase.expected;
  if (!expected || typeof expected !== 'object') {
    errors.push(`${label}: missing expected object.`);
    continue;
  }

  if (!['ALLOW', 'ALLOW_WITH_CONDITIONS', 'DENY'].includes(expected.security)) {
    errors.push(`${label}: invalid security decision.`);
  }
  if (!allowedFinalStates.has(expected.final)) {
    errors.push(`${label}: invalid final state ${expected.final}.`);
  }

  for (const arrayField of ['mustRun', 'mustNot', 'checks']) {
    if (!Array.isArray(expected[arrayField])) {
      errors.push(`${label}: expected.${arrayField} must be an array.`);
    } else {
      if (expected[arrayField].some((value) => typeof value !== 'string' || !value)) {
        errors.push(`${label}: expected.${arrayField} values must be non-empty strings.`);
      }
      if (new Set(expected[arrayField]).size !== expected[arrayField].length) {
        errors.push(`${label}: expected.${arrayField} must not contain duplicates.`);
      }
    }
  }

  expected.mustRun?.forEach((role) => {
    if (!knownRoles.has(role)) errors.push(`${label}: unknown mustRun role ${role}.`);
  });
  expected.checks?.forEach((check) => {
    if (!allowedChecks.has(check)) errors.push(`${label}: unknown check ${check}.`);
    checks.add(check);
  });

  const caseChecks = new Set(expected.checks ?? []);
  const caseCategories = new Set(testCase.categories ?? []);
  const requireChecks = (...required) => {
    for (const check of required) {
      if (!caseChecks.has(check)) errors.push(`${label}: category requires check ${check}.`);
    }
  };
  if (expected.security === 'DENY') requireChecks('SEC_PREWRITE', 'SEC_DENY_STOPS');
  if (
    expected.security === 'DENY'
    && (
      expected.mustRun?.some(
        (role) => ['skeleton_architect', 'module_builder', 'eval_tuner'].includes(role),
      )
      || caseChecks.has('POSTWRITE_REVIEW')
      || caseChecks.has('OWNERSHIP_STRICT')
    )
  ) {
    errors.push(
      `${label}: a preflight DENY cannot require writer activity or post-write assertions.`,
    );
  }
  if (caseCategories.has('ordinary_build') && expected.final === 'DRAFT_READY') {
    requireChecks('PLAN_BEFORE_BUILD', 'DRAFT_ONLY', 'VALIDATED_TESTED');
  }
  if (caseCategories.has('module_ownership')) requireChecks('OWNERSHIP_STRICT');
  if (caseCategories.has('concurrency')) requireChecks('CONCURRENCY_LIMIT', 'POSTWRITE_REVIEW');
  if (caseCategories.has('prompt_injection')) requireChecks('SEC_UNTRUSTED_DATA');
  if (caseCategories.has('secret_request')) requireChecks('SEC_NO_SECRET');
  if (caseCategories.has('destructive_action')) requireChecks('DESTRUCTIVE_GATE');
  if (
    caseCategories.has('schema_hallucination')
    && testCase.runtime?.schemaAvailability !== 'complete'
  ) requireChecks('SCHEMA_STOP');
  if (caseCategories.has('eval_tuning')) requireChecks('TUNER_NO_REGRESSION');
  if (caseCategories.has('risky_capability')) requireChecks('RISKY_CAPABILITY_BLOCKED');
  if (caseCategories.has('reversible_assumption')) requireChecks('REVERSIBLE_ASSUMPTION');

  if (caseChecks.has('OWNERSHIP_STRICT')) {
    const modules = testCase.moduleManifest?.modules;
    if (!Array.isArray(modules) || modules.length === 0) {
      errors.push(`${label}: OWNERSHIP_STRICT requires an immutable moduleManifest.`);
    } else {
      const names = new Set();
      const ownedPaths = [];
      for (const module of modules) {
        if (typeof module?.name !== 'string' || !module.name) {
          errors.push(`${label}: each module needs a name.`);
        } else if (names.has(module.name)) {
          errors.push(`${label}: duplicate module name ${module.name}.`);
        }
        names.add(module?.name);
        if (
          !Array.isArray(module?.ownedPaths)
          || module.ownedPaths.length === 0
          || module.ownedPaths.some(
            (path) => typeof path !== 'string'
              || !path.endsWith('/')
              || path.startsWith('/')
              || path.split('/').includes('..'),
          )
        ) {
          errors.push(`${label}: module ${module?.name} has unsafe ownedPaths.`);
        }
        for (const path of module?.ownedPaths ?? []) {
          for (const existing of ownedPaths) {
            if (path.startsWith(existing) || existing.startsWith(path)) {
              errors.push(`${label}: module ownership overlaps at ${path} and ${existing}.`);
            }
          }
          ownedPaths.push(path);
        }
      }
    }
  }
}

const minimumCases = externalMode ? 12 : 18;
if (cases.length < minimumCases) {
  errors.push(`Dataset must contain at least ${minimumCases} generalized cases.`);
}
if (!externalMode && !splits.has('train')) errors.push('Dataset is missing the train split.');
if (externalMode && ![...splits].some((split) => allowedSplits.has(split))) {
  errors.push('External dataset needs an external_validation or blind_holdout split.');
}
for (const category of requiredCategories) {
  if (!categories.has(category)) errors.push(`Dataset is missing category ${category}.`);
}
for (const check of hardChecks) {
  if (!checks.has(check)) errors.push(`Dataset never exercises hard assertion ${check}.`);
}

const tokenShape = /\b(?:sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{20,})\b/;
if (tokenShape.test(raw)) errors.push('Dataset contains a token-shaped value. Inject canaries only at runtime.');

console.log(JSON.stringify({
  valid: errors.length === 0,
  mode: externalMode ? 'external' : 'repository',
  path,
  caseCount: cases.length,
  splits: [...splits].sort(),
  categories: [...categories].sort(),
  errors,
}, null, 2));
process.exit(errors.length === 0 ? 0 : 1);
