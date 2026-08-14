from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from web.services.dashboard_files import eval_tuning_files, manifest_summary, security_hash_status


class EvalTuningFilesTests(unittest.TestCase):
    def test_both_dirs_absent_returns_empty_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing_a = Path(tmp) / "evals-results-missing"
            missing_b = Path(tmp) / "tuning-proposals-missing"
            with (
                mock.patch("web.services.dashboard_files.EVALS_RESULTS_DIR", missing_a),
                mock.patch("web.services.dashboard_files.TUNING_PROPOSALS_DIR", missing_b),
            ):
                self.assertEqual(eval_tuning_files(), [])

    def test_real_repo_lists_known_run_files_with_size_and_mtime(self) -> None:
        files = eval_tuning_files()
        paths = {entry["path"] for entry in files}
        self.assertTrue(any("agent-reliability-20260725-01" in path for path in paths))
        for entry in files:
            self.assertIn("size", entry)
            self.assertIn("mtime", entry)


class SecurityHashStatusTests(unittest.TestCase):
    def test_manifest_missing_reports_manifest_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing_manifest = Path(tmp) / "security-control-hashes.json"
            with mock.patch(
                "web.services.dashboard_files.SECURITY_HASHES_PATH", missing_manifest
            ):
                result = security_hash_status()
        self.assertEqual(
            result,
            [
                {
                    "path": None,
                    "status": "MANIFEST_MISSING",
                    "expected_sha256": None,
                    "actual_sha256": None,
                }
            ],
        )

    def test_flipped_byte_reports_mismatch_while_others_still_match(self) -> None:
        # Proves the guard can actually fail (verification.md: "reintroduce
        # the defect, watch it go red"). Three real files are copied byte-
        # for-byte into a tmp tree with their genuine sha256 pinned in a
        # synthetic manifest. One of them is mutated by a single byte after
        # its hash was recorded. Only that exact file must report MISMATCH;
        # the untouched files must still report MATCH, not FILE_MISSING.
        real_files = {
            ".gitignore": (ROOT / ".gitignore").read_bytes(),
            "AGENTS.md": (ROOT / "AGENTS.md").read_bytes(),
            "config/module-manifest.json": (ROOT / "config" / "module-manifest.json").read_bytes(),
        }
        expected_hashes = {
            relative: hashlib.sha256(content).hexdigest()
            for relative, content in real_files.items()
        }

        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            manifest_path = tmp_root / "security-control-hashes.json"
            manifest_path.write_text(
                json.dumps({"version": 1, "algorithm": "sha256", "files": expected_hashes}),
                encoding="utf-8",
            )
            for relative, content in real_files.items():
                target = tmp_root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)

            flipped_relative = "AGENTS.md"
            flipped_path = tmp_root / flipped_relative
            mutated = bytearray(flipped_path.read_bytes())
            mutated[0] ^= 0xFF
            flipped_path.write_bytes(bytes(mutated))

            with (
                mock.patch("web.services.dashboard_files.REPO_ROOT", tmp_root),
                mock.patch("web.services.dashboard_files.SECURITY_HASHES_PATH", manifest_path),
            ):
                results = security_hash_status()

        by_path = {entry["path"]: entry["status"] for entry in results}
        self.assertEqual(by_path[flipped_relative], "MISMATCH")
        self.assertEqual(by_path[".gitignore"], "MATCH")
        self.assertEqual(by_path["config/module-manifest.json"], "MATCH")

    def test_file_listed_in_manifest_but_absent_on_disk_reports_file_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            manifest_path = tmp_root / "security-control-hashes.json"
            manifest_path.write_text(
                json.dumps(
                    {"version": 1, "algorithm": "sha256", "files": {"nope.txt": "0" * 64}}
                ),
                encoding="utf-8",
            )
            with (
                mock.patch("web.services.dashboard_files.REPO_ROOT", tmp_root),
                mock.patch("web.services.dashboard_files.SECURITY_HASHES_PATH", manifest_path),
            ):
                results = security_hash_status()
        self.assertEqual(
            results,
            [
                {
                    "path": "nope.txt",
                    "status": "FILE_MISSING",
                    "expected_sha256": "0" * 64,
                    "actual_sha256": None,
                }
            ],
        )


class ManifestSummaryTests(unittest.TestCase):
    def test_missing_manifest_returns_empty_modules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "module-manifest.json"
            with mock.patch("web.services.dashboard_files.MODULE_MANIFEST_PATH", missing):
                self.assertEqual(manifest_summary(), {"modules": []})

    def test_real_manifest_includes_self_improvement_module(self) -> None:
        summary = manifest_summary()
        names = {module["name"] for module in summary["modules"]}
        self.assertIn("self_improvement", names)


if __name__ == "__main__":
    unittest.main()
