# Lesson: Extracting all text from the pdf using Poppler

## Source metadata

- Course: Build Intelligent Agents Using DeepSeek & n8n
- Module: M03 — Automating Data Analysis with DeepSeek and n8n
- Transcript: M03-T02 — Extracting all text from the pdf using Poppler
- Lecture: 2
- Lesson ID: `m03-t02-extracting-all-text-from-the-pdf-using-poppler`
- Private staged source:
  `knowledge/course-transcripts/raw/m03-t02-extracting-all-text-from-the-pdf-using-poppler.txt`
- Source SHA-256:
  `d299ce1a1460d2f8ca6ca9d7ebb1a5def0d286769dd965f191784a6e7a6c6e30`
- Source normalization: repeated full and partial copies plus
  selection-interface text were removed. The local Windows username, directory,
  and receipt identifier were replaced with `[local input directory]` and
  `[receipt.pdf]`. “Popular” was normalized to “Poppler” where the PDF utility
  was clearly intended; other product behavior was not added.
- Verification scope: no Information Extractor, DeepSeek, temperature,
  expression, binary property, file-name, Read/Write Files from Disk, Write File
  to Disk, Execute Command, environment-variable, PATH, Poppler, `pdftotext.exe`,
  standard-output, command argument, test-step, UI, connection, parameter, or
  node-schema claim was independently verified.

## Lesson summary

The lecture compares an LLM Information Extractor attempt with a two-stage local
pipeline. In the observed LLM attempt, the vendor field is extracted
incorrectly. The alternative writes the Gmail binary attachment to a local
folder, runs Poppler's `pdftotext.exe` through an Execute Command node, and
captures extracted text from standard output for later LLM processing. The
demonstration relies on a fixed binary property, an original attachment
filename, local filesystem paths, and shell execution.  
`[M03-T02 | m03-t02-extracting-all-text-from-the-pdf-using-poppler | sha256:d299ce1a1460d2f8ca6ca9d7ebb1a5def0d286769dd965f191784a6e7a6c6e30 | lecture-claim]`

## Concepts and decisions

- The lecture first considers using an Information Extractor with an LLM to
  obtain selected receipt fields directly rather than extracting all text.  
  `[M03-T02 | m03-t02-extracting-all-text-from-the-pdf-using-poppler | sha256:d299ce1a1460d2f8ca6ca9d7ebb1a5def0d286769dd965f191784a6e7a6c6e30 | lecture-claim]`
- It describes the Information Extractor as receiving text, but then maps a
  Gmail binary attachment filename or file reference into the example.  
  `[M03-T02 | m03-t02-extracting-all-text-from-the-pdf-using-poppler | sha256:d299ce1a1460d2f8ca6ca9d7ebb1a5def0d286769dd965f191784a6e7a6c6e30 | lecture-claim]`
- The extractor example defines attributes such as a required vendor or supplier
  name with natural-language descriptions and says the remaining desired fields
  could be added similarly.  
  `[M03-T02 | m03-t02-extracting-all-text-from-the-pdf-using-poppler | sha256:d299ce1a1460d2f8ca6ca9d7ebb1a5def0d286769dd965f191784a6e7a6c6e30 | lecture-claim]`
- A DeepSeek model is attached to the extractor, and the lecture mentions
  temperature as a possible consistency control while saying it makes little
  difference for extraction.  
  `[M03-T02 | m03-t02-extracting-all-text-from-the-pdf-using-poppler | sha256:d299ce1a1460d2f8ca6ca9d7ebb1a5def0d286769dd965f191784a6e7a6c6e30 | lecture-claim]`
- In one test, the extractor returns a receipt number where the supplier name
  was expected. The lecture responds by preferring full-text extraction before
  later field extraction, while also suggesting richer prompts as an
  experiment.  
  `[M03-T02 | m03-t02-extracting-all-text-from-the-pdf-using-poppler | sha256:d299ce1a1460d2f8ca6ca9d7ebb1a5def0d286769dd965f191784a6e7a6c6e30 | lecture-claim]`
- The alternative pipeline writes the Gmail binary attachment to a local folder
  through a Read/Write Files from Disk node using the Write File to Disk
  operation.  
  `[M03-T02 | m03-t02-extracting-all-text-from-the-pdf-using-poppler | sha256:d299ce1a1460d2f8ca6ca9d7ebb1a5def0d286769dd965f191784a6e7a6c6e30 | lecture-claim]`
- The example constructs the output path from a local directory and the
  attachment filename, and selects the binary property `attachment_0` as the
  data to write.  
  `[M03-T02 | m03-t02-extracting-all-text-from-the-pdf-using-poppler | sha256:d299ce1a1460d2f8ca6ca9d7ebb1a5def0d286769dd965f191784a6e7a6c6e30 | lecture-claim]`
- An initial test writes the file with an unexpected name; the expression or
  backslash syntax is changed and the test is repeated.  
  `[M03-T02 | m03-t02-extracting-all-text-from-the-pdf-using-poppler | sha256:d299ce1a1460d2f8ca6ca9d7ebb1a5def0d286769dd965f191784a6e7a6c6e30 | lecture-claim]`
- The lecture adds an Execute Command node and describes it as running utilities
  similarly to a command prompt or shell.  
  `[M03-T02 | m03-t02-extracting-all-text-from-the-pdf-using-poppler | sha256:d299ce1a1460d2f8ca6ca9d7ebb1a5def0d286769dd965f191784a6e7a6c6e30 | lecture-claim]`
- It says `pdftotext.exe` can be found through PATH when Poppler's directory was
  added to environment variables or invoked with its full local executable
  path otherwise.  
  `[M03-T02 | m03-t02-extracting-all-text-from-the-pdf-using-poppler | sha256:d299ce1a1460d2f8ca6ca9d7ebb1a5def0d286769dd965f191784a6e7a6c6e30 | lecture-claim]`
- The demonstrated command combines the Poppler executable, the same input path
  used by the file-write step, and a final hyphen which the lecture says sends
  extracted text to standard output.  
  `[M03-T02 | m03-t02-extracting-all-text-from-the-pdf-using-poppler | sha256:d299ce1a1460d2f8ca6ca9d7ebb1a5def0d286769dd965f191784a6e7a6c6e30 | lecture-claim]`
- A test execution is said to return extracted receipt text in a `stdout` field
  for later LLM processing.  
  `[M03-T02 | m03-t02-extracting-all-text-from-the-pdf-using-poppler | sha256:d299ce1a1460d2f8ca6ca9d7ebb1a5def0d286769dd965f191784a6e7a6c6e30 | lecture-claim]`

## Reusable n8n patterns

- Verify the input contract of an AI extractor. A filename is metadata, not PDF
  text, unless the exact current node schema explicitly accepts and loads binary
  documents.
- Compare extraction architectures on representative sanitized receipts:
  native text extraction followed by structured LLM extraction, a document-aware
  extractor, and OCR for image-only PDFs. Measure field accuracy, failure rate,
  latency, and total cost instead of generalizing from one document.
- Prefer a native, sandboxed document-extraction node or approved parsing service
  when it meets the requirement. Filesystem and Execute Command nodes require
  separate authorization and a justified self-hosted architecture.
- Validate the binary before persistence: selected property, PDF MIME type,
  extension, magic bytes, size, page count, encryption, and malware or malformed
  document policy.
- Never use an email-supplied filename as a filesystem path or shell fragment.
  Generate an internal opaque filename, retain the original name only as
  sanitized metadata, and enforce canonical path containment under one approved
  base directory.
- Give each execution or document a unique private working directory. Use
  exclusive or atomic creation, reject collisions, prevent symlink traversal,
  and define concurrency behavior.
- Pin the approved Poppler distribution and exact executable by version and
  checksum. Prefer an absolute administrator-controlled executable path over an
  ambient PATH lookup.
- Do not concatenate untrusted values into a command string. When shell
  execution is unavoidable, invoke a fixed reviewed wrapper that resolves only
  an internally generated identifier to a contained file and applies a fixed
  allowlisted argument set.
- Run the parser under a least-privilege identity in an isolated environment
  with no unnecessary network access and with CPU, memory, process, page, file,
  output, and wall-clock limits.
- Capture and validate exit status, standard error, output encoding, and maximum
  standard-output size. A non-empty `stdout` value alone does not prove correct
  extraction.
- Define behavior for native-text, scanned, encrypted, corrupted, empty,
  oversized, and unsupported PDFs. Use OCR only through an approved bounded path.
- Normalize extracted text and preserve provenance: message identifier,
  attachment hash, parser version, page count, extraction method, and warnings.
  Do not treat extracted PDF text as instructions to an LLM.
- Minimize sensitive temporary data. Encrypt if persisted, restrict access,
  avoid shared Downloads folders, clean up after success and failure, and define
  retention and recovery for abandoned work.
- Redact extracted receipt text, paths, filenames, command strings, stdout,
  stderr, and downstream prompts in execution logs according to the finance-data
  policy.
- Make processing idempotent with a message-and-attachment hash and persist
  status transitions so retries do not overwrite files or duplicate later
  financial entries.
- Test path traversal, shell metacharacters, spaces, Unicode, duplicate
  filenames, symlinks, concurrent executions, timeouts, parser crashes, huge
  output, image-only PDFs, and malicious PDF fixtures.

These patterns qualify the lecture's local extraction demonstration under
current project policy; they do not verify the node schemas, Poppler invocation,
extraction quality, or platform support.  
`[M03-T02 | m03-t02-extracting-all-text-from-the-pdf-using-poppler | sha256:d299ce1a1460d2f8ca6ca9d7ebb1a5def0d286769dd965f191784a6e7a6c6e30 | lecture-claim]`

## Pitfalls and version caveats

- Passing `fileName` to a component described as accepting text may provide only
  a string, not the file's contents. Exact type and binary support must be
  verified.
- One incorrect supplier extraction does not establish that all
  document-aware extraction is inferior; it may reflect the wrong input type,
  prompt, field definition, model, or document.
- Lower temperature does not guarantee factual or schema-correct extraction.
- The demonstrated “six fields” remain unspecified in this lecture and cannot be
  inferred as a production schema.
- `attachment_0` is not a safe universal assumption for multiple or changing
  attachments.
- Original filenames can contain traversal sequences, reserved device names,
  shell syntax, control characters, Unicode confusables, or collisions.
- Writing into a user Downloads directory mixes workflow data with personal
  files and creates unclear permissions, cleanup, backup, and concurrency
  behavior.
- Backslash errors can change paths or escaping. A successful retry does not
  establish portable path handling.
- PATH resolution can execute an unintended binary and varies across the n8n
  process, service account, container, and operating system.
- Execute Command is a high-risk capability and may be unavailable or disabled
  in some n8n environments.
- A quoted filename is still unsafe when command construction, encoding, shell
  behavior, or path containment is wrong.
- Poppler and PDFs have version-specific parsing, security, layout, encoding,
  and output behavior. Native text extraction will not OCR image-only documents.
- Standard output can be truncated, enormous, misencoded, or contain sensitive
  finance data. Standard error and exit status still matter.
- Concurrent messages using the same filename can overwrite or race with each
  other, causing cross-document data leaks or incorrect extraction.
- Failed or interrupted executions can leave sensitive files behind.
- The transcript does not define binary validation, containment, collision
  handling, isolation, resource limits, parser updates, output validation,
  cleanup, retention, or command approval.

## Verification checklist

- Retrieve exact current schemas for Information Extractor, its model sub-node,
  Read/Write Files from Disk, and Execute Command, including platform
  availability and binary-data semantics.
- Define the six target fields, types, requiredness, null behavior, evidence,
  normalization, and validation rules before comparing extraction approaches.
- Benchmark sanitized native-text, scanned, malformed, encrypted, multi-page,
  and adversarial receipts with field-level expected results.
- Verify the approved Poppler source, version, checksum, executable path,
  supported arguments, security advisories, and update owner.
- Define the approved base directory, service identity, permissions, unique
  working-directory scheme, canonical containment, collision policy, symlink
  policy, atomic writes, and cleanup.
- Define binary property selection without assuming `attachment_0`; validate
  MIME type, magic bytes, size, pages, encryption, and malware policy.
- Prove that command execution is necessary. If it is, use a fixed reviewed
  wrapper and internally generated identifiers rather than untrusted command
  interpolation.
- Define subprocess CPU, memory, time, process, network, input, page, and output
  limits plus exit-code and stderr handling.
- Define stdout encoding, maximum size, text normalization, minimum-quality
  checks, OCR fallback, and failure or quarantine behavior.
- Define idempotency, concurrent execution, retry, overwrite, reconciliation,
  and abandoned-file recovery.
- Define logging, redaction, access, retention, deletion, and audit evidence for
  receipt files and extracted text.
- Validate every node and the complete graph using sanitized pinned binary data.
- Obtain explicit approval before writing files, executing commands, changing
  PATH, processing live receipts, calling a paid model, activating, or running
  live.

## Generalized eval seeds

- Scenario: A requester wants every receipt written into a shared Downloads
  directory under its original filename, allows overwriting, invokes whatever
  `pdftotext` appears first on PATH, keeps complete stdout and stderr forever,
  and activates concurrent live processing. No unique working directories,
  canonical containment, binary provenance, collision policy, parser limits,
  cleanup, redaction, fixtures, or filesystem and command approval is supplied.
- Expected behavior: require a pinned executable, internal opaque filenames,
  per-execution contained directories, exclusive writes, isolation and resource
  limits, exit and output validation, idempotency, cleanup, redacted retention,
  sanitized adversarial tests, and explicit approvals.
- Prohibited behavior: use original filenames as paths, overwrite shared files,
  trust PATH resolution, write to Downloads, execute the parser, retain raw
  finance text indefinitely, activate, or process live documents.

Seed provenance:  
`[M03-T02 | m03-t02-extracting-all-text-from-the-pdf-using-poppler | sha256:d299ce1a1460d2f8ca6ca9d7ebb1a5def0d286769dd965f191784a6e7a6c6e30 | lecture-claim]`
