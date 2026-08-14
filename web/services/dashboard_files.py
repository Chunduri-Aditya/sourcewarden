from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from web.paths import (
    EVALS_RESULTS_DIR,
    MODULE_MANIFEST_PATH,
    REPO_ROOT,
    SECURITY_HASHES_PATH,
    TUNING_PROPOSALS_DIR,
)


def eval_tuning_files() -> list[dict[str, Any]]:
    """Recursive listing of every file under evals/results/ and
    tuning/proposals/. Either directory may be absent; both absent returns
    an empty list.
    """
    files: list[dict[str, Any]] = []
    for directory in (EVALS_RESULTS_DIR, TUNING_PROPOSALS_DIR):
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*")):
            if not path.is_file():
                continue
            info = path.stat()
            files.append(
                {
                    "path": str(path.relative_to(REPO_ROOT)),
                    "size": info.st_size,
                    "mtime": datetime.fromtimestamp(info.st_mtime, tz=UTC).isoformat(),
                }
            )
    return files


def security_hash_status() -> list[dict[str, Any]]:
    """Live sha256 comparison against .codex/security-control-hashes.json.

    Each pinned file is classified MATCH, MISMATCH, or FILE_MISSING. If the
    manifest itself is absent, returns a single MANIFEST_MISSING entry
    instead of raising. Read-only: never calls the Node.js hash generator.
    """
    if not SECURITY_HASHES_PATH.is_file():
        return [
            {
                "path": None,
                "status": "MANIFEST_MISSING",
                "expected_sha256": None,
                "actual_sha256": None,
            }
        ]

    manifest = json.loads(SECURITY_HASHES_PATH.read_text(encoding="utf-8"))
    results: list[dict[str, Any]] = []
    for relative_path, expected_hash in manifest.get("files", {}).items():
        target = REPO_ROOT / relative_path
        if not target.is_file():
            results.append(
                {
                    "path": relative_path,
                    "status": "FILE_MISSING",
                    "expected_sha256": expected_hash,
                    "actual_sha256": None,
                }
            )
            continue
        actual_hash = hashlib.sha256(target.read_bytes()).hexdigest()
        status = "MATCH" if actual_hash == expected_hash else "MISMATCH"
        results.append(
            {
                "path": relative_path,
                "status": status,
                "expected_sha256": expected_hash,
                "actual_sha256": actual_hash,
            }
        )
    return results


def manifest_summary() -> dict[str, Any]:
    """Summary of config/module-manifest.json. Missing file returns an
    empty module list rather than raising.
    """
    if not MODULE_MANIFEST_PATH.is_file():
        return {"modules": []}
    manifest = json.loads(MODULE_MANIFEST_PATH.read_text(encoding="utf-8"))
    modules = manifest.get("modules", [])
    return {
        "modules": [
            {
                "name": module.get("name"),
                "ownedPaths": module.get("ownedPaths", []),
                "testCommand": module.get("testCommand"),
            }
            for module in modules
        ]
    }
