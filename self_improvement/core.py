from __future__ import annotations

import base64
import errno
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
from typing import Any, Iterable
import uuid


RUN_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")
HEX_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SNAPSHOT_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
SIGNAL_FILE_RE = re.compile(r"^[0-9a-f]{64}\.json$")
SAFE_LABEL_RE = re.compile(r"^[A-Za-z0-9._:/-]{1,128}$")
MAX_JSON_BYTES = 262_144
EXPECTED_POLICY_SHA256 = "b0757a26f28f359588a0a229bbc4d44ca7b409f05767073f5c18c5a6f10c0b72"

POLICY_PATH = "self_improvement/policy.json"
FEEDBACK_ROOT = "evals/feedback/inbox"
PROPOSAL_ROOT = "tuning/proposals"
RESULT_ROOT = "evals/results"

POLICY_KEYS = {
    "schemaVersion",
    "terminalStatus",
    "allowedTargets",
    "trainingCorpusPath",
    "maxJsonBytes",
    "maxSignalBytes",
    "maxCandidateBytes",
    "maxTrainingCorpusBytes",
    "objectiveFloorMicros",
    "feedbackSources",
    "feedbackCategories",
    "secretPatterns",
    "digestPreimages",
}
SIGNAL_KEYS = {
    "schemaVersion",
    "signalId",
    "source",
    "category",
    "summary",
    "expectedBehavior",
    "contentDigest",
}
BASELINE_KEYS = {
    "schemaVersion",
    "runId",
    "gitCommit",
    "snapshotId",
    "trainingCorpusSha256",
    "policySha256",
    "feedbackSignals",
    "targetHashes",
}
MANIFEST_KEYS = {
    "schemaVersion",
    "runId",
    "baseline",
    "proposalDigest",
    "targets",
    "metrics",
    "rollback",
}
MANIFEST_BASELINE_KEYS = {
    "gitCommit",
    "snapshotId",
    "trainingCorpusSha256",
    "policySha256",
    "targetHashes",
}
TARGET_KEYS = {
    "productionPath",
    "candidatePath",
    "beforeSha256",
    "candidateSha256",
}
METRIC_BINDING_KEYS = {
    "definitionSha256",
    "baselineArtifactPath",
    "baselineArtifactSha256",
    "candidateArtifactPath",
    "candidateArtifactSha256",
}
ROLLBACK_KEYS = {
    "candidateIdentifier",
    "approvalIdentifier",
    "sourceSnapshotId",
    "intendedIntegratedSnapshot",
    "targetBeforeHashes",
    "targetAfterHashes",
    "validationEvidence",
    "status",
}
METRIC_KEYS = {
    "schemaVersion",
    "receiptType",
    "runId",
    "baselineSnapshotId",
    "proposalDigest",
    "metricDefinitionSha256",
    "suiteSha256",
    "caseCount",
    "hardAssertions",
    "securityAssertions",
    "objectiveScoreMicros",
    "protectedCategoryScoreMicros",
    "signerKeyId",
    "signatureAlgorithm",
    "signatureBase64",
}
APPROVAL_KEYS = {
    "schemaVersion",
    "receiptType",
    "runId",
    "baselineSnapshotId",
    "proposalDigest",
    "targetSetDigest",
    "scope",
    "nonce",
    "consumption",
    "signerKeyId",
    "signatureAlgorithm",
    "signatureBase64",
}


class ContractError(RuntimeError):
    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ContractError("JSON_CANONICALIZATION_FAILED", str(error)) from error


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _reject_constant(value: str) -> None:
    raise ContractError("JSON_NONSTANDARD_NUMBER", f"Nonstandard numeric constant {value} is forbidden.")


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError("JSON_DUPLICATE_KEY", "A JSON object contains a duplicate key.")
        result[key] = value
    return result


def strict_json_bytes(content: bytes, *, label: str, maximum: int = MAX_JSON_BYTES) -> Any:
    if len(content) > maximum:
        raise ContractError("ARTIFACT_TOO_LARGE", f"{label} exceeds {maximum} bytes.")
    if content.startswith(b"\xef\xbb\xbf"):
        raise ContractError("JSON_BOM_FORBIDDEN", f"{label} starts with a UTF-8 byte order mark.")
    if b"\x00" in content:
        raise ContractError("NUL_BYTE_FORBIDDEN", f"{label} contains a NUL byte.")
    try:
        text = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ContractError("INVALID_UTF8", f"{label} is not valid UTF-8.") from error
    try:
        return json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except ContractError:
        raise
    except json.JSONDecodeError as error:
        raise ContractError("JSON_INVALID", f"{label} is invalid JSON at character {error.pos}.") from error


def _parts(relative_path: str) -> tuple[str, ...]:
    if not isinstance(relative_path, str) or not relative_path:
        raise ContractError("PATH_INVALID", "Artifact path must be a nonempty string.")
    pure = PurePosixPath(relative_path)
    if pure.is_absolute() or str(pure) != relative_path:
        raise ContractError("PATH_INVALID", f"Path {relative_path!r} is not normalized and relative.")
    parts = pure.parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise ContractError("PATH_TRAVERSAL", f"Path {relative_path!r} leaves its expected root.")
    return parts


def _root_path(root: Path | str) -> Path:
    try:
        path = Path(root).resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ContractError("ROOT_UNAVAILABLE", "Repository root is unavailable.") from error
    if not path.is_dir():
        raise ContractError("ROOT_INVALID", "Repository root is not a directory.")
    return path


def _directory_fd(root: Path | str, parts: Iterable[str], *, create: bool = False) -> int:
    resolved_root = _root_path(root)
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    current = os.open(resolved_root, flags)
    try:
        for part in parts:
            try:
                child = os.open(part, flags, dir_fd=current)
            except FileNotFoundError:
                if not create:
                    raise
                os.mkdir(part, mode=0o700, dir_fd=current)
                child = os.open(part, flags, dir_fd=current)
            except OSError as error:
                if error.errno in {errno.ELOOP, errno.ENOTDIR}:
                    raise ContractError("PATH_SYMLINK_OR_NON_DIRECTORY", "A directory path is unsafe.") from error
                raise
            opened = os.fstat(child)
            named = os.stat(part, dir_fd=current, follow_symlinks=False)
            if not stat.S_ISDIR(opened.st_mode) or (opened.st_dev, opened.st_ino) != (named.st_dev, named.st_ino):
                os.close(child)
                raise ContractError("PATH_IDENTITY_CHANGED", "A directory changed during validation.")
            os.close(current)
            current = child
        return current
    except Exception:
        os.close(current)
        raise


def secure_read(root: Path | str, relative_path: str, *, maximum: int) -> bytes:
    parts = _parts(relative_path)
    try:
        parent = _directory_fd(root, parts[:-1])
    except FileNotFoundError as error:
        raise ContractError("ARTIFACT_MISSING", f"Required artifact {relative_path} is missing.") from error
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = -1
    try:
        try:
            descriptor = os.open(parts[-1], flags, dir_fd=parent)
        except FileNotFoundError as error:
            raise ContractError("ARTIFACT_MISSING", f"Required artifact {relative_path} is missing.") from error
        except OSError as error:
            if error.errno in {errno.ELOOP, errno.ENOTDIR}:
                raise ContractError("PATH_SYMLINK_FORBIDDEN", f"Artifact {relative_path} uses a symlink.") from error
            raise
        before = os.fstat(descriptor)
        named = os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
        if not stat.S_ISREG(before.st_mode):
            raise ContractError("ARTIFACT_NOT_REGULAR", f"Artifact {relative_path} is not a regular file.")
        if before.st_nlink != 1:
            raise ContractError("HARD_LINK_FORBIDDEN", f"Artifact {relative_path} has multiple hard links.")
        if (before.st_dev, before.st_ino) != (named.st_dev, named.st_ino):
            raise ContractError("PATH_IDENTITY_CHANGED", f"Artifact {relative_path} changed during validation.")
        if before.st_size > maximum:
            raise ContractError("ARTIFACT_TOO_LARGE", f"Artifact {relative_path} exceeds {maximum} bytes.")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(65_536, maximum + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > maximum:
                raise ContractError("ARTIFACT_TOO_LARGE", f"Artifact {relative_path} exceeds {maximum} bytes.")
        after = os.fstat(descriptor)
        named_after = os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
        identities = {
            (before.st_dev, before.st_ino),
            (after.st_dev, after.st_ino),
            (named_after.st_dev, named_after.st_ino),
        }
        metadata_changed = (
            after.st_size != before.st_size
            or after.st_mtime_ns != before.st_mtime_ns
            or after.st_ctime_ns != before.st_ctime_ns
            or named_after.st_size != before.st_size
            or named_after.st_mtime_ns != before.st_mtime_ns
            or named_after.st_ctime_ns != before.st_ctime_ns
        )
        if len(identities) != 1 or metadata_changed:
            raise ContractError("PATH_IDENTITY_CHANGED", f"Artifact {relative_path} changed during validation.")
        return b"".join(chunks)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(parent)


def _write_all(descriptor: int, content: bytes) -> None:
    offset = 0
    while offset < len(content):
        offset += os.write(descriptor, content[offset:])
    os.fsync(descriptor)


def atomic_write_json(root: Path | str, relative_path: str, value: Any) -> None:
    content = canonical_json(value) + b"\n"
    if len(content) > MAX_JSON_BYTES:
        raise ContractError("ARTIFACT_TOO_LARGE", f"Output {relative_path} exceeds {MAX_JSON_BYTES} bytes.")
    parts = _parts(relative_path)
    directory = _directory_fd(root, parts[:-1], create=True)
    temporary = f".{parts[-1]}.{uuid.uuid4().hex}.tmp"
    descriptor = -1
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        try:
            existing = os.stat(parts[-1], dir_fd=directory, follow_symlinks=False)
        except FileNotFoundError:
            existing = None
        if existing is not None and (not stat.S_ISREG(existing.st_mode) or existing.st_nlink != 1):
            raise ContractError("OUTPUT_PATH_UNSAFE", f"Output {relative_path} is not a single-link regular file.")
        descriptor = os.open(temporary, flags, 0o600, dir_fd=directory)
        _write_all(descriptor, content)
        os.close(descriptor)
        descriptor = -1
        os.replace(temporary, parts[-1], src_dir_fd=directory, dst_dir_fd=directory)
        os.fsync(directory)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            os.unlink(temporary, dir_fd=directory)
        except FileNotFoundError:
            pass
        os.close(directory)


def exclusive_write_json(root: Path | str, relative_path: str, value: Any, *, maximum: int) -> None:
    content = canonical_json(value) + b"\n"
    if len(content) > maximum:
        raise ContractError("ARTIFACT_TOO_LARGE", f"Output {relative_path} exceeds {maximum} bytes.")
    parts = _parts(relative_path)
    directory = _directory_fd(root, parts[:-1], create=True)
    descriptor = -1
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        try:
            descriptor = os.open(parts[-1], flags, 0o600, dir_fd=directory)
        except FileExistsError as error:
            raise ContractError("SIGNAL_ALREADY_EXISTS", "An identical feedback signal already exists.") from error
        _write_all(descriptor, content)
        os.close(descriptor)
        descriptor = -1
        os.fsync(directory)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(directory)


def _closed_object(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("SCHEMA_TYPE", f"{label} must be an object.")
    actual = set(value)
    if actual != keys:
        raise ContractError("SCHEMA_KEYS", f"{label} does not match its closed schema.")
    return value


def _integer(value: Any, label: str, minimum: int, maximum: int | None = None) -> int:
    if type(value) is not int:
        raise ContractError("SCHEMA_INTEGER", f"{label} must be an integer and cannot be a boolean.")
    if value < minimum or (maximum is not None and value > maximum):
        raise ContractError("SCHEMA_RANGE", f"{label} is outside its allowed range.")
    return value


def _string(value: Any, label: str, *, minimum: int = 1, maximum: int = 10_000) -> str:
    if not isinstance(value, str) or not minimum <= len(value) <= maximum:
        raise ContractError("SCHEMA_STRING", f"{label} must contain {minimum} through {maximum} characters.")
    return value


def _hex(value: Any, label: str) -> str:
    text = _string(value, label, minimum=64, maximum=64)
    if not HEX_RE.fullmatch(text):
        raise ContractError("SCHEMA_HASH", f"{label} must be a lowercase SHA-256 value.")
    return text


def _snapshot(value: Any, label: str) -> str:
    text = _string(value, label, minimum=71, maximum=71)
    if not SNAPSHOT_RE.fullmatch(text):
        raise ContractError("SCHEMA_SNAPSHOT", f"{label} must be a sha256 snapshot ID.")
    return text


def _run_id(value: Any) -> str:
    if not isinstance(value, str) or not RUN_ID_RE.fullmatch(value):
        raise ContractError("RUN_ID_INVALID", "Run ID must match ^[a-z0-9][a-z0-9._-]{2,63}$.")
    return value


def _load_policy(root: Path | str) -> tuple[dict[str, Any], bytes]:
    raw = secure_read(root, POLICY_PATH, maximum=MAX_JSON_BYTES)
    if sha256_bytes(raw) != EXPECTED_POLICY_SHA256:
        raise ContractError("POLICY_HASH_MISMATCH", "Policy bytes differ from the frozen implementation policy.")
    policy = _closed_object(strict_json_bytes(raw, label=POLICY_PATH), POLICY_KEYS, "policy")
    if policy["schemaVersion"] != 1 or policy["terminalStatus"] != "BLOCKED_EXTERNAL_INTEGRATOR":
        raise ContractError("POLICY_INVALID", "Policy version or terminal status is invalid.")
    targets = policy["allowedTargets"]
    if not isinstance(targets, list) or not targets or targets != sorted(set(targets)):
        raise ContractError("POLICY_INVALID", "Allowed targets must be a nonempty sorted unique list.")
    for target in targets:
        _parts(target)
        if not target.endswith(".md"):
            raise ContractError("POLICY_INVALID", "Allowed targets must be Markdown files.")
    for key in (
        "maxJsonBytes",
        "maxSignalBytes",
        "maxCandidateBytes",
        "maxTrainingCorpusBytes",
        "objectiveFloorMicros",
    ):
        _integer(policy[key], f"policy.{key}", 1)
    if policy["maxJsonBytes"] != MAX_JSON_BYTES:
        raise ContractError("POLICY_INVALID", "Policy JSON size limit differs from the frozen contract.")
    if policy["objectiveFloorMicros"] > 1_000_000:
        raise ContractError("POLICY_INVALID", "Objective floor exceeds one million micros.")
    for key in ("feedbackSources", "feedbackCategories"):
        values = policy[key]
        if not isinstance(values, list) or values != sorted(set(values)) or not all(isinstance(item, str) for item in values):
            raise ContractError("POLICY_INVALID", f"policy.{key} must be a sorted unique string list.")
    patterns = policy["secretPatterns"]
    if not isinstance(patterns, list) or not patterns:
        raise ContractError("POLICY_INVALID", "Secret patterns must be a nonempty list.")
    for pattern in patterns:
        _closed_object(pattern, {"name", "pattern", "ignoreCase"}, "secret pattern")
        _string(pattern["name"], "secret pattern name", maximum=64)
        _string(pattern["pattern"], "secret pattern", maximum=512)
        if type(pattern["ignoreCase"]) is not bool:
            raise ContractError("POLICY_INVALID", "Secret ignoreCase must be boolean.")
        try:
            re.compile(pattern["pattern"], re.IGNORECASE if pattern["ignoreCase"] else 0)
        except re.error as error:
            raise ContractError("POLICY_INVALID", "A secret pattern is invalid.") from error
    preimages = _closed_object(
        policy["digestPreimages"],
        {"contentDigestKeys", "proposalDigestKeys", "targetSetItemKeys"},
        "digest preimages",
    )
    if preimages != {
        "contentDigestKeys": ["source", "category", "summary", "expectedBehavior"],
        "proposalDigestKeys": ["runId", "baselineSnapshotId", "targets"],
        "targetSetItemKeys": ["productionPath", "candidateSha256"],
    }:
        raise ContractError("POLICY_INVALID", "Digest preimage keys differ from the frozen contract.")
    return policy, raw


def _detect_secret(text: str, policy: dict[str, Any]) -> None:
    for item in policy["secretPatterns"]:
        flags = re.IGNORECASE if item["ignoreCase"] else 0
        if re.search(item["pattern"], text, flags):
            raise ContractError("SECRET_DETECTED", f"Text matched secret rule {item['name']}.")


def _validate_signal(value: Any, policy: dict[str, Any], *, expected_file_id: str | None = None) -> dict[str, Any]:
    signal = _closed_object(value, SIGNAL_KEYS, "feedback signal")
    if signal["schemaVersion"] != 1:
        raise ContractError("SCHEMA_VERSION", "Feedback schemaVersion must be 1.")
    source = _string(signal["source"], "feedback source", maximum=32)
    category = _string(signal["category"], "feedback category", maximum=64)
    if source not in policy["feedbackSources"] or category not in policy["feedbackCategories"]:
        raise ContractError("FEEDBACK_ENUM", "Feedback source or category is not allowed.")
    summary = _string(signal["summary"], "feedback summary", maximum=500)
    expected = _string(signal["expectedBehavior"], "expected behavior", maximum=2_000)
    _detect_secret(f"{summary}\n{expected}", policy)
    preimage = {
        "source": source,
        "category": category,
        "summary": summary,
        "expectedBehavior": expected,
    }
    digest = sha256_bytes(canonical_json(preimage))
    if signal["contentDigest"] != digest or signal["signalId"] != digest:
        raise ContractError("SIGNAL_DIGEST_MISMATCH", "Feedback signal digest does not match its content.")
    if expected_file_id is not None and digest != expected_file_id:
        raise ContractError("SIGNAL_FILENAME_MISMATCH", "Feedback signal file name does not match its digest.")
    return signal


def record_feedback(
    root: Path | str,
    *,
    source: str,
    category: str,
    summary: str,
    expected_behavior: str,
) -> dict[str, Any]:
    policy, _ = _load_policy(root)
    preimage = {
        "source": source,
        "category": category,
        "summary": summary,
        "expectedBehavior": expected_behavior,
    }
    digest = sha256_bytes(canonical_json(preimage))
    signal = {
        "schemaVersion": 1,
        "signalId": digest,
        **preimage,
        "contentDigest": digest,
    }
    _validate_signal(signal, policy)
    relative = f"{FEEDBACK_ROOT}/{digest}.json"
    exclusive_write_json(root, relative, signal, maximum=policy["maxSignalBytes"])
    return {"status": "RECORDED_UNTRUSTED_SIGNAL", "signalId": digest, "path": relative}


def _git(root: Path | str, *arguments: str) -> bytes:
    try:
        result = subprocess.run(
            ["git", "-C", str(_root_path(root)), *arguments],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise ContractError("GIT_UNAVAILABLE", "Git could not inspect the repository.") from error
    if result.returncode != 0:
        raise ContractError("GIT_FAILED", "Git could not inspect the repository.")
    return result.stdout


def _status_paths(root: Path | str) -> list[str]:
    raw = _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    records = raw.split(b"\x00")
    paths: list[str] = []
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        try:
            text = record.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise ContractError("GIT_STATUS_INVALID", "Git status contains a non-UTF-8 path.") from error
        if len(text) < 4:
            raise ContractError("GIT_STATUS_INVALID", "Git status output is malformed.")
        code = text[:2]
        paths.append(text[3:])
        if "R" in code or "C" in code:
            if index >= len(records) or not records[index]:
                raise ContractError("GIT_STATUS_INVALID", "Git rename status is incomplete.")
            paths.append(records[index].decode("utf-8", errors="strict"))
            index += 1
    return paths


def _require_prepare_clean(root: Path | str) -> None:
    if _status_paths(root):
        raise ContractError("DIRTY_WORKTREE", "Baseline preparation requires a completely clean Git worktree.")


def _require_validation_clean(root: Path | str, run_id: str) -> None:
    allowed = (
        f"{PROPOSAL_ROOT}/{run_id}/",
        f"{RESULT_ROOT}/{run_id}/",
        f"{FEEDBACK_ROOT}/",
    )
    unexpected = [path for path in _status_paths(root) if not path.startswith(allowed)]
    if unexpected:
        raise ContractError("DIRTY_WORKTREE", "Candidate validation found changes outside the active run artifacts.")


def _git_commit(root: Path | str) -> str:
    commit = _git(root, "rev-parse", "--verify", "HEAD").decode("ascii", errors="strict").strip()
    if not COMMIT_RE.fullmatch(commit):
        raise ContractError("GIT_COMMIT_INVALID", "Git HEAD is not a 40-character commit.")
    return commit


def _feedback_entries(root: Path | str, policy: dict[str, Any]) -> list[dict[str, str]]:
    parts = _parts(FEEDBACK_ROOT)
    try:
        directory = _directory_fd(root, parts)
    except FileNotFoundError:
        return []
    try:
        names = sorted(os.listdir(directory))
    finally:
        os.close(directory)
    entries: list[dict[str, str]] = []
    for name in names:
        if not SIGNAL_FILE_RE.fullmatch(name):
            raise ContractError("FEEDBACK_FILE_UNEXPECTED", "Feedback inbox contains an unexpected entry.")
        relative = f"{FEEDBACK_ROOT}/{name}"
        raw = secure_read(root, relative, maximum=policy["maxSignalBytes"])
        signal = strict_json_bytes(raw, label=relative, maximum=policy["maxSignalBytes"])
        _validate_signal(signal, policy, expected_file_id=name[:-5])
        entries.append({"signalId": name[:-5], "sha256": sha256_bytes(raw)})
    return entries


def _validate_baseline(value: Any, policy: dict[str, Any], *, run_id: str) -> dict[str, Any]:
    baseline = _closed_object(value, BASELINE_KEYS, "baseline")
    if baseline["schemaVersion"] != 1 or baseline["runId"] != run_id:
        raise ContractError("BASELINE_BINDING", "Baseline version or run ID is incorrect.")
    if not isinstance(baseline["gitCommit"], str) or not COMMIT_RE.fullmatch(baseline["gitCommit"]):
        raise ContractError("BASELINE_COMMIT", "Baseline Git commit is invalid.")
    _snapshot(baseline["snapshotId"], "baseline snapshotId")
    _hex(baseline["trainingCorpusSha256"], "baseline trainingCorpusSha256")
    _hex(baseline["policySha256"], "baseline policySha256")
    signals = baseline["feedbackSignals"]
    if not isinstance(signals, list):
        raise ContractError("BASELINE_SIGNALS", "Baseline feedbackSignals must be a list.")
    identifiers: list[str] = []
    for entry in signals:
        item = _closed_object(entry, {"signalId", "sha256"}, "baseline feedback entry")
        identifiers.append(_hex(item["signalId"], "feedback signalId"))
        _hex(item["sha256"], "feedback sha256")
    if identifiers != sorted(set(identifiers)):
        raise ContractError("BASELINE_SIGNALS", "Baseline feedback signals must be sorted and unique.")
    hashes = baseline["targetHashes"]
    if not isinstance(hashes, dict) or list(hashes) != sorted(policy["allowedTargets"]):
        raise ContractError("BASELINE_TARGETS", "Baseline must bind every allowlisted target in sorted order.")
    for target, digest in hashes.items():
        if target not in policy["allowedTargets"]:
            raise ContractError("BASELINE_TARGETS", "Baseline contains a nonallowlisted target.")
        _hex(digest, f"baseline target {target}")
    preimage = dict(baseline)
    del preimage["snapshotId"]
    expected = f"sha256:{sha256_bytes(canonical_json(preimage))}"
    if baseline["snapshotId"] != expected:
        raise ContractError("BASELINE_SNAPSHOT_MISMATCH", "Baseline snapshot ID does not match its content.")
    return baseline


def prepare_baseline(root: Path | str, run_id: str) -> dict[str, Any]:
    run_id = _run_id(run_id)
    policy, policy_raw = _load_policy(root)
    _require_prepare_clean(root)
    target_hashes: dict[str, str] = {}
    for target in policy["allowedTargets"]:
        content = secure_read(root, target, maximum=policy["maxCandidateBytes"])
        target_hashes[target] = sha256_bytes(content)
    corpus_path = policy["trainingCorpusPath"]
    corpus = secure_read(root, corpus_path, maximum=policy["maxTrainingCorpusBytes"])
    preimage = {
        "schemaVersion": 1,
        "runId": run_id,
        "gitCommit": _git_commit(root),
        "trainingCorpusSha256": sha256_bytes(corpus),
        "policySha256": sha256_bytes(policy_raw),
        "feedbackSignals": _feedback_entries(root, policy),
        "targetHashes": target_hashes,
    }
    baseline = dict(preimage)
    baseline["snapshotId"] = f"sha256:{sha256_bytes(canonical_json(preimage))}"
    baseline = {
        "schemaVersion": baseline["schemaVersion"],
        "runId": baseline["runId"],
        "gitCommit": baseline["gitCommit"],
        "snapshotId": baseline["snapshotId"],
        "trainingCorpusSha256": baseline["trainingCorpusSha256"],
        "policySha256": baseline["policySha256"],
        "feedbackSignals": baseline["feedbackSignals"],
        "targetHashes": baseline["targetHashes"],
    }
    atomic_write_json(root, f"{RESULT_ROOT}/{run_id}/baseline.json", baseline)
    proposal_directory = _directory_fd(root, _parts(f"{PROPOSAL_ROOT}/{run_id}/proposed"), create=True)
    os.close(proposal_directory)
    return {
        "status": "BASELINE_PREPARED",
        "runId": run_id,
        "snapshotId": baseline["snapshotId"],
        "promotionStatus": policy["terminalStatus"],
    }


def _list_candidate_files(root: Path | str, relative_directory: str) -> set[str]:
    base_parts = _parts(relative_directory)
    try:
        base_fd = _directory_fd(root, base_parts)
    except FileNotFoundError as error:
        raise ContractError("CANDIDATE_DIRECTORY_MISSING", "Candidate proposed directory is missing.") from error
    found: set[str] = set()

    def visit(directory_fd: int, prefix: tuple[str, ...]) -> None:
        with os.scandir(directory_fd) as entries:
            for entry in entries:
                name = entry.name
                if name in {".", ".."}:
                    continue
                path = prefix + (name,)
                item = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
                if stat.S_ISLNK(item.st_mode):
                    raise ContractError("PATH_SYMLINK_FORBIDDEN", "Candidate tree contains a symlink.")
                if stat.S_ISDIR(item.st_mode):
                    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
                    child = os.open(name, flags, dir_fd=directory_fd)
                    try:
                        opened = os.fstat(child)
                        named = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
                        if (opened.st_dev, opened.st_ino) != (named.st_dev, named.st_ino):
                            raise ContractError("PATH_IDENTITY_CHANGED", "Candidate directory changed during validation.")
                        visit(child, path)
                    finally:
                        os.close(child)
                elif stat.S_ISREG(item.st_mode):
                    if item.st_nlink != 1:
                        raise ContractError("HARD_LINK_FORBIDDEN", "Candidate tree contains a hard-linked file.")
                    found.add(PurePosixPath(*path).as_posix())
                else:
                    raise ContractError("ARTIFACT_NOT_REGULAR", "Candidate tree contains a special file.")

    try:
        visit(base_fd, ())
    finally:
        os.close(base_fd)
    return found


def _validate_assertions(value: Any, label: str) -> dict[str, int]:
    assertions = _closed_object(value, {"passed", "total"}, label)
    total = _integer(assertions["total"], f"{label}.total", 1)
    passed = _integer(assertions["passed"], f"{label}.passed", 0, total)
    return {"passed": passed, "total": total}


def _validate_signature_fields(receipt: dict[str, Any], label: str) -> None:
    if receipt["signatureAlgorithm"] != "Ed25519":
        raise ContractError("SIGNATURE_ALGORITHM", f"{label} signatureAlgorithm must be Ed25519.")
    signer = _string(receipt["signerKeyId"], f"{label} signerKeyId", maximum=128)
    if not SAFE_LABEL_RE.fullmatch(signer):
        raise ContractError("SIGNER_KEY_ID", f"{label} signerKeyId is invalid.")
    signature = _string(receipt["signatureBase64"], f"{label} signatureBase64", maximum=128)
    try:
        decoded = base64.b64decode(signature, validate=True)
    except (ValueError, base64.binascii.Error) as error:
        raise ContractError("SIGNATURE_ENCODING", f"{label} signature is not valid base64.") from error
    if len(decoded) != 64:
        raise ContractError("SIGNATURE_LENGTH", f"{label} Ed25519 signature must decode to 64 bytes.")


def _validate_metric(value: Any, *, role: str, run_id: str, snapshot_id: str, proposal_digest: str) -> dict[str, Any]:
    metric = _closed_object(value, METRIC_KEYS, f"{role} metrics")
    if metric["schemaVersion"] != 1 or metric["receiptType"] != f"{role}-metrics":
        raise ContractError("METRIC_ROLE", f"{role} metric version or receiptType is invalid.")
    if metric["runId"] != run_id or metric["baselineSnapshotId"] != snapshot_id:
        raise ContractError("METRIC_BINDING", f"{role} metric run or baseline snapshot is mismatched.")
    if metric["proposalDigest"] != proposal_digest:
        raise ContractError("METRIC_BINDING", f"{role} metric proposal digest is mismatched.")
    _hex(metric["metricDefinitionSha256"], f"{role} metricDefinitionSha256")
    _hex(metric["suiteSha256"], f"{role} suiteSha256")
    _integer(metric["caseCount"], f"{role} caseCount", 1)
    metric["hardAssertions"] = _validate_assertions(metric["hardAssertions"], f"{role} hardAssertions")
    metric["securityAssertions"] = _validate_assertions(metric["securityAssertions"], f"{role} securityAssertions")
    _integer(metric["objectiveScoreMicros"], f"{role} objectiveScoreMicros", 0, 1_000_000)
    categories = metric["protectedCategoryScoreMicros"]
    if not isinstance(categories, dict) or not categories:
        raise ContractError("METRIC_CATEGORIES", f"{role} protected categories must be a nonempty object.")
    for category, score in categories.items():
        if not isinstance(category, str) or not category or len(category) > 128:
            raise ContractError("METRIC_CATEGORIES", f"{role} protected category name is invalid.")
        _integer(score, f"{role} protected category score", 0, 1_000_000)
    _validate_signature_fields(metric, f"{role} metrics")
    return metric


def _compare_metrics(baseline: dict[str, Any], candidate: dict[str, Any], policy: dict[str, Any]) -> None:
    for key in (
        "runId",
        "baselineSnapshotId",
        "proposalDigest",
        "metricDefinitionSha256",
        "suiteSha256",
        "caseCount",
    ):
        if baseline[key] != candidate[key]:
            raise ContractError("METRIC_COMPARABILITY", f"Metric field {key} differs between baseline and candidate.")
    if set(baseline["protectedCategoryScoreMicros"]) != set(candidate["protectedCategoryScoreMicros"]):
        raise ContractError("METRIC_COMPARABILITY", "Protected metric category sets differ.")
    for kind in ("hardAssertions", "securityAssertions"):
        if baseline[kind]["total"] != candidate[kind]["total"]:
            raise ContractError("METRIC_COMPARABILITY", "Baseline and candidate assertion totals differ.")
    for role, metric in (("baseline", baseline), ("candidate", candidate)):
        for kind in ("hardAssertions", "securityAssertions"):
            if metric[kind]["passed"] != metric[kind]["total"]:
                raise ContractError("METRIC_HARD_FAILURE", f"{role} {kind} is not 100 percent.")
    if candidate["objectiveScoreMicros"] < policy["objectiveFloorMicros"]:
        raise ContractError("METRIC_OBJECTIVE_FLOOR", "Candidate objective score is below the policy floor.")
    if candidate["objectiveScoreMicros"] < baseline["objectiveScoreMicros"]:
        raise ContractError("METRIC_REGRESSION", "Candidate objective score regressed.")
    for category, baseline_score in baseline["protectedCategoryScoreMicros"].items():
        if candidate["protectedCategoryScoreMicros"][category] < baseline_score:
            raise ContractError("METRIC_REGRESSION", "A candidate protected category regressed.")


def _target_set_digest(targets: list[dict[str, Any]]) -> str:
    preimage = [
        {"productionPath": item["productionPath"], "candidateSha256": item["candidateSha256"]}
        for item in sorted(targets, key=lambda item: item["productionPath"])
    ]
    return sha256_bytes(canonical_json(preimage))


def _validate_approval(value: Any, *, run_id: str, snapshot_id: str, proposal_digest: str, target_digest: str) -> dict[str, Any]:
    approval = _closed_object(value, APPROVAL_KEYS, "approval receipt")
    if approval["schemaVersion"] != 1 or approval["receiptType"] != "promotion-approval":
        raise ContractError("APPROVAL_SCHEMA", "Approval version or receiptType is invalid.")
    if approval["runId"] != run_id or approval["baselineSnapshotId"] != snapshot_id:
        raise ContractError("APPROVAL_BINDING", "Approval run or baseline snapshot is mismatched.")
    if approval["proposalDigest"] != proposal_digest or approval["targetSetDigest"] != target_digest:
        raise ContractError("APPROVAL_BINDING", "Approval candidate or target set is mismatched.")
    if approval["scope"] != "APPLY_ALLOWLISTED_PROMPTS":
        raise ContractError("APPROVAL_SCOPE", "Approval scope is invalid.")
    nonce = _string(approval["nonce"], "approval nonce", minimum=8, maximum=128)
    if not SAFE_LABEL_RE.fullmatch(nonce):
        raise ContractError("APPROVAL_NONCE", "Approval nonce is invalid.")
    consumption = _closed_object(approval["consumption"], {"status", "recordId"}, "approval consumption")
    if consumption != {"status": "UNCONSUMED", "recordId": None}:
        raise ContractError("APPROVAL_REPLAY", "Approval must be unconsumed with no local record ID.")
    _validate_signature_fields(approval, "approval")
    return approval


def _validate_manifest(
    root: Path | str,
    manifest: Any,
    baseline: dict[str, Any],
    policy: dict[str, Any],
    run_id: str,
) -> str:
    value = _closed_object(manifest, MANIFEST_KEYS, "candidate manifest")
    if value["schemaVersion"] != 1 or value["runId"] != run_id:
        raise ContractError("MANIFEST_BINDING", "Manifest version or run ID is incorrect.")
    manifest_baseline = _closed_object(value["baseline"], MANIFEST_BASELINE_KEYS, "manifest baseline")
    expected_baseline = {
        "gitCommit": baseline["gitCommit"],
        "snapshotId": baseline["snapshotId"],
        "trainingCorpusSha256": baseline["trainingCorpusSha256"],
        "policySha256": baseline["policySha256"],
        "targetHashes": baseline["targetHashes"],
    }
    if manifest_baseline != expected_baseline:
        raise ContractError("MANIFEST_BASELINE_MISMATCH", "Manifest baseline differs from the frozen baseline.")
    targets = value["targets"]
    if not isinstance(targets, list) or not targets:
        raise ContractError("MANIFEST_TARGETS", "Manifest targets must be a nonempty list.")
    validated_targets: list[dict[str, Any]] = []
    production_paths: list[str] = []
    expected_candidate_files: set[str] = set()
    for target_value in targets:
        target = _closed_object(target_value, TARGET_KEYS, "candidate target")
        production = _string(target["productionPath"], "productionPath", maximum=512)
        _parts(production)
        if production not in policy["allowedTargets"]:
            raise ContractError("TARGET_NOT_ALLOWED", "Candidate target is not on the prompt allowlist.")
        candidate_path = _string(target["candidatePath"], "candidatePath", maximum=600)
        expected_path = f"proposed/{production}"
        if candidate_path != expected_path:
            raise ContractError("CANDIDATE_PATH_BINDING", "Candidate path does not match its production path.")
        before = _hex(target["beforeSha256"], "target beforeSha256")
        candidate_digest = _hex(target["candidateSha256"], "target candidateSha256")
        if before != baseline["targetHashes"][production]:
            raise ContractError("TARGET_BASELINE_MISMATCH", "Target before hash differs from the baseline.")
        relative_candidate = f"{PROPOSAL_ROOT}/{run_id}/{candidate_path}"
        candidate_raw = secure_read(root, relative_candidate, maximum=policy["maxCandidateBytes"])
        if b"\x00" in candidate_raw:
            raise ContractError("NUL_BYTE_FORBIDDEN", "Candidate Markdown contains a NUL byte.")
        try:
            candidate_text = candidate_raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise ContractError("INVALID_UTF8", "Candidate Markdown is not valid UTF-8.") from error
        _detect_secret(candidate_text, policy)
        if sha256_bytes(candidate_raw) != candidate_digest:
            raise ContractError("CANDIDATE_HASH_MISMATCH", "Candidate content hash does not match the manifest.")
        production_paths.append(production)
        expected_candidate_files.add(production)
        validated_targets.append(dict(target))
    if production_paths != sorted(set(production_paths)):
        raise ContractError("MANIFEST_TARGETS", "Candidate targets must be sorted and unique.")
    actual_files = _list_candidate_files(root, f"{PROPOSAL_ROOT}/{run_id}/proposed")
    if actual_files != expected_candidate_files:
        raise ContractError("CANDIDATE_EXTRA_OR_MISSING_FILE", "Candidate tree differs from the manifest target set.")
    preimage = {
        "runId": run_id,
        "baselineSnapshotId": baseline["snapshotId"],
        "targets": validated_targets,
    }
    proposal_digest = sha256_bytes(canonical_json(preimage))
    if value["proposalDigest"] != proposal_digest:
        raise ContractError("PROPOSAL_DIGEST_MISMATCH", "Proposal digest does not match its frozen inputs.")

    metrics = _closed_object(value["metrics"], METRIC_BINDING_KEYS, "metric bindings")
    if metrics["definitionSha256"] is None:
        raise ContractError("METRIC_DEFINITION", "Metric definition hash is required.")
    definition = _hex(metrics["definitionSha256"], "metrics definitionSha256")
    expected_baseline_path = f"{RESULT_ROOT}/{run_id}/baseline-metrics.json"
    expected_candidate_path = f"{RESULT_ROOT}/{run_id}/candidate-metrics.json"
    if metrics["baselineArtifactPath"] != expected_baseline_path or metrics["candidateArtifactPath"] != expected_candidate_path:
        raise ContractError("METRIC_PATH_BINDING", "Metric artifact paths must use the exact active run paths.")
    baseline_metric_raw = secure_read(root, expected_baseline_path, maximum=policy["maxJsonBytes"])
    candidate_metric_raw = secure_read(root, expected_candidate_path, maximum=policy["maxJsonBytes"])
    if sha256_bytes(baseline_metric_raw) != _hex(metrics["baselineArtifactSha256"], "baselineArtifactSha256"):
        raise ContractError("METRIC_HASH_MISMATCH", "Baseline metric artifact hash is mismatched.")
    if sha256_bytes(candidate_metric_raw) != _hex(metrics["candidateArtifactSha256"], "candidateArtifactSha256"):
        raise ContractError("METRIC_HASH_MISMATCH", "Candidate metric artifact hash is mismatched.")
    baseline_metric = _validate_metric(
        strict_json_bytes(baseline_metric_raw, label=expected_baseline_path),
        role="baseline",
        run_id=run_id,
        snapshot_id=baseline["snapshotId"],
        proposal_digest=proposal_digest,
    )
    candidate_metric = _validate_metric(
        strict_json_bytes(candidate_metric_raw, label=expected_candidate_path),
        role="candidate",
        run_id=run_id,
        snapshot_id=baseline["snapshotId"],
        proposal_digest=proposal_digest,
    )
    if baseline_metric["metricDefinitionSha256"] != definition or candidate_metric["metricDefinitionSha256"] != definition:
        raise ContractError("METRIC_DEFINITION", "Metric receipt definition hash differs from the manifest.")
    _compare_metrics(baseline_metric, candidate_metric, policy)

    rollback = _closed_object(value["rollback"], ROLLBACK_KEYS, "rollback")
    before_hashes = {item["productionPath"]: item["beforeSha256"] for item in validated_targets}
    after_hashes = {item["productionPath"]: item["candidateSha256"] for item in validated_targets}
    expected_rollback = {
        "candidateIdentifier": proposal_digest,
        "approvalIdentifier": None,
        "sourceSnapshotId": baseline["snapshotId"],
        "intendedIntegratedSnapshot": None,
        "targetBeforeHashes": before_hashes,
        "targetAfterHashes": after_hashes,
        "validationEvidence": [],
        "status": "NOT_APPLIED",
    }
    if rollback != expected_rollback:
        raise ContractError("ROLLBACK_BINDING", "Rollback metadata does not match the frozen not-applied state.")

    approval_path = f"{RESULT_ROOT}/{run_id}/approval-receipt.json"
    try:
        approval_raw = secure_read(root, approval_path, maximum=policy["maxJsonBytes"])
    except ContractError as error:
        if error.code != "ARTIFACT_MISSING":
            raise
    else:
        approval = strict_json_bytes(approval_raw, label=approval_path)
        _validate_approval(
            approval,
            run_id=run_id,
            snapshot_id=baseline["snapshotId"],
            proposal_digest=proposal_digest,
            target_digest=_target_set_digest(validated_targets),
        )
    return proposal_digest


def _assessment(run_id: str, structural: str, proposal_digest: str | None, error: ContractError | None, approval_present: bool) -> dict[str, Any]:
    checks: list[dict[str, str]] = []
    blockers: list[dict[str, str]] = [
        {
            "code": "EXTERNAL_SIGNATURE_VERIFICATION_REQUIRED",
            "detail": "Workspace code does not verify Ed25519 promotion evidence.",
        },
        {
            "code": "EXTERNAL_INTEGRATOR_REQUIRED",
            "detail": "Workspace code has no apply, approval-consumption, or rollback-execution capability.",
        },
    ]
    if error is None:
        checks.append({"code": "LOCAL_STRUCTURE", "status": "PASS", "detail": "Local closed-schema and deterministic checks passed."})
    else:
        safe_detail = "Local validation failed closed at the named contract boundary."
        checks.append({"code": error.code, "status": "FAIL", "detail": safe_detail})
        blockers.append({"code": error.code, "detail": safe_detail})
    if not approval_present:
        blockers.append({"code": "EXPLICIT_APPROVAL_REQUIRED", "detail": "The fixed-path external approval receipt is absent."})
    else:
        blockers.append({"code": "APPROVAL_SIGNATURE_AND_NONCE_CONSUMPTION_REQUIRED", "detail": "A trusted integrator must verify and consume approval exactly once."})
    return {
        "schemaVersion": 1,
        "runId": run_id,
        "structuralStatus": structural,
        "promotionStatus": "BLOCKED_EXTERNAL_INTEGRATOR",
        "proposalDigest": proposal_digest,
        "checks": sorted(checks, key=lambda item: item["code"]),
        "blockers": sorted(blockers, key=lambda item: item["code"]),
    }


def _artifact_present(root: Path | str, relative_path: str, maximum: int = MAX_JSON_BYTES) -> bool:
    try:
        secure_read(root, relative_path, maximum=maximum)
        return True
    except ContractError as error:
        if error.code == "ARTIFACT_MISSING":
            return False
        raise


def validate_candidate(root: Path | str, run_id: str) -> dict[str, Any]:
    run_id = _run_id(run_id)
    policy, policy_raw = _load_policy(root)
    proposal_digest: str | None = None
    error: ContractError | None = None
    approval_path = f"{RESULT_ROOT}/{run_id}/approval-receipt.json"
    try:
        approval_present = _artifact_present(root, approval_path, policy["maxJsonBytes"])
    except ContractError as approval_error:
        approval_present = True
        error = approval_error
    try:
        if error is not None:
            raise error
        _require_validation_clean(root, run_id)
        baseline_path = f"{RESULT_ROOT}/{run_id}/baseline.json"
        baseline_raw = secure_read(root, baseline_path, maximum=policy["maxJsonBytes"])
        baseline = _validate_baseline(strict_json_bytes(baseline_raw, label=baseline_path), policy, run_id=run_id)
        if baseline["gitCommit"] != _git_commit(root):
            raise ContractError("STALE_BASELINE", "Current Git commit differs from the frozen baseline.")
        if baseline["policySha256"] != sha256_bytes(policy_raw):
            raise ContractError("POLICY_DRIFT", "Self-improvement policy differs from the frozen baseline.")
        corpus = secure_read(root, policy["trainingCorpusPath"], maximum=policy["maxTrainingCorpusBytes"])
        if baseline["trainingCorpusSha256"] != sha256_bytes(corpus):
            raise ContractError("TRAINING_CORPUS_DRIFT", "Visible training corpus differs from the frozen baseline.")
        for target, expected_hash in baseline["targetHashes"].items():
            current = secure_read(root, target, maximum=policy["maxCandidateBytes"])
            if sha256_bytes(current) != expected_hash:
                raise ContractError("PRODUCTION_TARGET_DRIFT", "A production prompt differs from the frozen baseline.")
        manifest_path = f"{PROPOSAL_ROOT}/{run_id}/candidate-manifest.json"
        manifest_raw = secure_read(root, manifest_path, maximum=policy["maxJsonBytes"])
        manifest = strict_json_bytes(manifest_raw, label=manifest_path)
        proposal_digest = _validate_manifest(root, manifest, baseline, policy, run_id)
    except ContractError as validation_error:
        error = validation_error

    assessment = _assessment(
        run_id,
        "VALID" if error is None else "INVALID",
        proposal_digest,
        error,
        approval_present,
    )
    atomic_write_json(root, f"{RESULT_ROOT}/{run_id}/local-assessment.json", assessment)
    return assessment


def status_for_run(root: Path | str, run_id: str) -> dict[str, Any]:
    run_id = _run_id(run_id)
    policy, _ = _load_policy(root)
    paths = {
        "baseline": f"{RESULT_ROOT}/{run_id}/baseline.json",
        "candidateManifest": f"{PROPOSAL_ROOT}/{run_id}/candidate-manifest.json",
        "baselineMetrics": f"{RESULT_ROOT}/{run_id}/baseline-metrics.json",
        "candidateMetrics": f"{RESULT_ROOT}/{run_id}/candidate-metrics.json",
        "approvalReceipt": f"{RESULT_ROOT}/{run_id}/approval-receipt.json",
        "localAssessment": f"{RESULT_ROOT}/{run_id}/local-assessment.json",
    }
    return {
        "schemaVersion": 1,
        "runId": run_id,
        "promotionStatus": policy["terminalStatus"],
        "artifacts": {name: _artifact_present(root, path, policy["maxJsonBytes"]) for name, path in paths.items()},
        "blockers": [
            "EXTERNAL_SIGNATURE_VERIFICATION_REQUIRED",
            "EXPLICIT_ONE_TIME_APPROVAL_REQUIRED",
            "EXTERNAL_INTEGRATOR_REQUIRED",
        ],
    }
