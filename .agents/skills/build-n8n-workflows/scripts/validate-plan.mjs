#!/usr/bin/env node

import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const args = process.argv.slice(2);
const readyIndex = args.indexOf('--ready');
const requireReady = readyIndex !== -1;

if (requireReady) {
  args.splice(readyIndex, 1);
}

if (args.length !== 1) {
  console.error('Usage: node validate-plan.mjs [--ready] <plan.md>');
  process.exit(2);
}

const planPath = resolve(args[0]);
let markdown;

try {
  markdown = await readFile(planPath, 'utf8');
} catch (error) {
  console.error(JSON.stringify({
    valid: false,
    path: planPath,
    errors: [`Unable to read plan: ${error.message}`],
  }, null, 2));
  process.exit(1);
}

const requiredSections = [
  'Goal',
  'Success criteria',
  'Known facts',
  'Assumptions and open questions',
  'Minimal workflow design',
  'Execution plan',
  'Test plan',
  'Approval gates',
  'Definition of done',
];

const errors = [];
const warnings = [];
const headingPattern = /^##\s+(.+?)\s*$/gm;
const headings = [...markdown.matchAll(headingPattern)].map((match) => ({
  name: match[1],
  index: match.index,
  contentStart: match.index + match[0].length,
}));

if (!/^# Workflow Plan:\s+\S.+$/m.test(markdown)) {
  errors.push('Missing title in the form "# Workflow Plan: <name>".');
}

for (const section of requiredSections) {
  if (!headings.some((heading) => heading.name === section)) {
    errors.push(`Missing required section: "${section}".`);
  }
}

const headingPositions = requiredSections
  .map((section) => headings.findIndex((heading) => heading.name === section))
  .filter((index) => index !== -1);

if (headingPositions.some((position, index) => index > 0 && position <= headingPositions[index - 1])) {
  errors.push('Required sections are out of order.');
}

function sectionContent(name) {
  const headingIndex = headings.findIndex((heading) => heading.name === name);
  if (headingIndex === -1) return '';
  const start = headings[headingIndex].contentStart;
  const end = headings[headingIndex + 1]?.index ?? markdown.length;
  return markdown.slice(start, end).trim();
}

for (const section of requiredSections) {
  if (headings.some((heading) => heading.name === section) && !sectionContent(section)) {
    errors.push(`Section "${section}" is empty.`);
  }
}

const successCriteria = sectionContent('Success criteria');
if (!/^\s*-\s+\[[ xX]\]\s+\S/m.test(successCriteria)) {
  errors.push('Success criteria must contain at least one Markdown checkbox.');
}

const executionPlan = sectionContent('Execution plan');
if (!/verify\s*:/i.test(executionPlan)) {
  errors.push('Execution plan must include at least one "verify:" condition.');
}

const testPlan = sectionContent('Test plan');
for (const testType of ['Happy path', 'Edge case', 'Failure path']) {
  if (!new RegExp(testType, 'i').test(testPlan)) {
    errors.push(`Test plan must define a ${testType.toLowerCase()}.`);
  }
}

const assumptions = sectionContent('Assumptions and open questions');
const blockers = assumptions
  .split('\n')
  .map((line) => line.trim())
  .filter((line) => /\[BLOCKING\]/i.test(line))
  .filter((line) => {
    const value = line.replace(/^[-*]\s*/, '').replace(/\[BLOCKING\]/i, '').trim();
    return !/^(none|n\/a|no|none[.!])$/i.test(value);
  });

if (requireReady && blockers.length > 0) {
  errors.push(`Unresolved blocking items: ${blockers.join(' | ')}`);
}

if (!/^Status:\s+(draft|ready|blocked|validated)\s*$/mi.test(markdown)) {
  warnings.push('Add a status: draft, ready, blocked, or validated.');
}

const result = {
  valid: errors.length === 0,
  readyCheck: requireReady,
  path: planPath,
  errors,
  warnings,
};

console.log(JSON.stringify(result, null, 2));
process.exit(result.valid ? 0 : 1);

