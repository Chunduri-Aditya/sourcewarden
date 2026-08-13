#!/usr/bin/env node

import { createHash } from "node:crypto";
import { access, mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const workspaceRoot = path.resolve(scriptDirectory, "../../../..");
const supportedExtensions = new Set([".md", ".srt", ".txt", ".vtt"]);

function usage() {
  return [
    "Usage:",
    "  node stage-transcript.mjs --input <file> [--title <title>]",
    "    [--course <course>] [--module-label <M##>] [--module <module>]",
    "    [--transcript-label <M##-T##>] [--lecture <number>]",
    "    [--slug <slug>] [--source-url <public-url>] [--dry-run]",
  ].join("\n");
}

function parseArguments(argv) {
  const options = {};
  const booleanFlags = new Set(["dry-run", "help"]);

  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (!argument.startsWith("--")) {
      throw new Error(`Unexpected argument: ${argument}`);
    }

    const key = argument.slice(2);
    if (booleanFlags.has(key)) {
      options[key] = true;
      continue;
    }

    const value = argv[index + 1];
    if (!value || value.startsWith("--")) {
      throw new Error(`Missing value for --${key}`);
    }
    options[key] = value;
    index += 1;
  }

  const allowed = new Set([
    "course",
    "dry-run",
    "help",
    "input",
    "lecture",
    "module",
    "module-label",
    "slug",
    "source-url",
    "title",
    "transcript-label",
  ]);
  for (const key of Object.keys(options)) {
    if (!allowed.has(key)) {
      throw new Error(`Unknown option: --${key}`);
    }
  }

  return options;
}

function slugify(value) {
  const slug = value
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);

  if (!slug) {
    throw new Error("Could not derive a safe slug; pass --slug explicitly");
  }
  return slug;
}

function sanitizePublicUrl(value) {
  if (!value) return null;

  const parsed = new URL(value);
  if (!["http:", "https:"].includes(parsed.protocol)) {
    throw new Error("--source-url must use http or https");
  }
  if (parsed.username || parsed.password) {
    throw new Error("--source-url must not contain embedded credentials");
  }

  parsed.search = "";
  parsed.hash = "";
  return parsed.toString();
}

function normalizeTranscript(text, extension) {
  let normalized = text
    .replace(/^\uFEFF/, "")
    .replace(/\r\n?/g, "\n")
    .split("\n")
    .map((line) => line.replace(/[ \t]+$/g, ""));

  if (extension === ".srt" || extension === ".vtt") {
    normalized = normalized.filter((line) => {
      const trimmed = line.trim();
      if (trimmed === "WEBVTT") return false;
      if (/^\d+$/.test(trimmed)) return false;
      if (/^\d{1,2}:\d{2}(?::\d{2})?[.,]\d{3}\s+-->\s+/.test(trimmed)) {
        return false;
      }
      return true;
    });
  }

  return `${normalized.join("\n").replace(/\n{3,}/g, "\n\n").trim()}\n`;
}

async function exists(targetPath) {
  try {
    await access(targetPath);
    return true;
  } catch {
    return false;
  }
}

async function main() {
  const options = parseArguments(process.argv.slice(2));
  if (options.help) {
    console.log(usage());
    return;
  }
  if (!options.input) {
    throw new Error(`--input is required\n${usage()}`);
  }

  const inputPath = path.resolve(process.cwd(), options.input);
  const extension = path.extname(inputPath).toLowerCase();
  if (!supportedExtensions.has(extension)) {
    throw new Error(
      `Unsupported transcript extension ${extension || "(none)"}; use .txt, .md, .srt, or .vtt`,
    );
  }

  const sourceText = await readFile(inputPath, "utf8");
  if (Buffer.byteLength(sourceText, "utf8") > 20 * 1024 * 1024) {
    throw new Error("Transcript exceeds the 20 MB staging limit");
  }

  const normalizedText = normalizeTranscript(sourceText, extension);
  if (!normalizedText.trim()) {
    throw new Error("Transcript is empty after normalization");
  }

  const title =
    options.title || path.basename(inputPath, path.extname(inputPath));
  const moduleLabel = options["module-label"] || null;
  const transcriptLabel = options["transcript-label"] || null;
  if ((moduleLabel && !transcriptLabel) || (!moduleLabel && transcriptLabel)) {
    throw new Error(
      "--module-label and --transcript-label must be supplied together",
    );
  }
  if (moduleLabel && !/^M\d{2}$/.test(moduleLabel)) {
    throw new Error("--module-label must match M##, for example M01");
  }
  if (
    transcriptLabel &&
    !new RegExp(`^${moduleLabel}-T\\d{2}$`).test(transcriptLabel)
  ) {
    throw new Error(
      `--transcript-label must match ${moduleLabel}-T##, for example ${moduleLabel}-T01`,
    );
  }

  const slug = slugify(
    options.slug || (transcriptLabel ? `${transcriptLabel}-${title}` : title),
  );
  const sourceSha256 = createHash("sha256")
    .update(normalizedText, "utf8")
    .digest("hex");
  const sourceUrl = sanitizePublicUrl(options["source-url"]);

  const rawDirectory = path.join(
    workspaceRoot,
    "knowledge/course-transcripts/raw",
  );
  const metadataDirectory = path.join(
    workspaceRoot,
    "knowledge/course-transcripts/metadata",
  );
  const rawPath = path.join(rawDirectory, `${slug}.txt`);
  const metadataPath = path.join(metadataDirectory, `${slug}.json`);
  const metadata = {
    lessonId: slug,
    transcriptLabel,
    title,
    course: options.course || null,
    moduleLabel,
    module: options.module || null,
    lecture: options.lecture || null,
    sourceUrl,
    sourceSha256,
    originalFilename: path.basename(inputPath),
    stagedAt: new Date().toISOString(),
  };

  if (options["dry-run"]) {
    console.log(
      JSON.stringify(
        {
          dryRun: true,
          lessonId: slug,
          transcriptLabel,
          moduleLabel,
          sourceSha256,
          rawPath: path.relative(workspaceRoot, rawPath),
          metadataPath: path.relative(workspaceRoot, metadataPath),
        },
        null,
        2,
      ),
    );
    return;
  }

  if ((await exists(rawPath)) || (await exists(metadataPath))) {
    throw new Error(
      `Lesson ${slug} is already staged; choose a new --slug instead of overwriting source evidence`,
    );
  }

  await mkdir(rawDirectory, { recursive: true });
  await mkdir(metadataDirectory, { recursive: true });
  await writeFile(rawPath, normalizedText, {
    encoding: "utf8",
    flag: "wx",
    mode: 0o600,
  });
  await writeFile(metadataPath, `${JSON.stringify(metadata, null, 2)}\n`, {
    encoding: "utf8",
    flag: "wx",
    mode: 0o600,
  });

  console.log(
    JSON.stringify(
      {
        staged: true,
        lessonId: slug,
        sourceSha256,
        rawPath: path.relative(workspaceRoot, rawPath),
        metadataPath: path.relative(workspaceRoot, metadataPath),
      },
      null,
      2,
    ),
  );
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
