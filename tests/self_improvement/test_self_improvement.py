from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from self_improvement.__main__ import COMMANDS, build_parser
from self_improvement.core import (
    ContractError,
    atomic_write_json,
    canonical_json,
    prepare_baseline,
    record_feedback,
    secure_read,
    sha256_bytes,
    status_for_run,
    strict_json_bytes,
    validate_candidate,
)


SOURCE_ROOT = Path(__file__).resolve().parents[2]
TARGETS = (
    "n8n_rag_system/prompts/node_selection_prompt.md",
    "n8n_rag_system/prompts/system_n8n_workflow_architect.md",
    "n8n_rag_system/prompts/workflow_recipe_template.md",
)
RUN_ID = "candidate-001"


def write_bytes(root: Path, relative: str, content: bytes) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def json_bytes(value: object) -> bytes:
    return canonical_json(value) + b"\n"


def write_json(root: Path, relative: str, value: object) -> Path:
    return write_bytes(root, relative, json_bytes(value))


def read_json(root: Path, relative: str) -> dict:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def synthetic_text(*parts: str) -> str:
    """Join synthetic signatures at runtime so bytecode does not contain a token."""
    return "".join(parts)


class RepositoryFixture:
    def __init__(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        write_bytes(
            self.root,
            "self_improvement/policy.json",
            (SOURCE_ROOT / "self_improvement/policy.json").read_bytes(),
        )
        for index, target in enumerate(TARGETS):
            write_bytes(self.root, target, f"# Prompt {index}\nOriginal behavior.\n".encode())
        write_bytes(self.root, "evals/generalized-cases.jsonl", b'{"case":"visible"}\n')
        write_bytes(self.root, ".gitignore", b"evals/feedback/inbox/\n")
        self.git("init", "-q")
        self.git("config", "user.email", "tests@example.invalid")
        self.git("config", "user.name", "Self Improvement Tests")
        self.git("add", ".")
        self.git("commit", "-qm", "fixture baseline")

    def close(self) -> None:
        self.temporary.cleanup()

    def git(self, *arguments: str) -> None:
        subprocess.run(
            ["git", "-C", str(self.root), *arguments],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def prepare(self) -> dict:
        return prepare_baseline(self.root, RUN_ID)

    def _metric(self, role: str, baseline: dict, proposal_digest: str, score: int = 900_000) -> dict:
        return {
            "schemaVersion": 1,
            "receiptType": f"{role}-metrics",
            "runId": RUN_ID,
            "baselineSnapshotId": baseline["snapshotId"],
            "proposalDigest": proposal_digest,
            "metricDefinitionSha256": "d" * 64,
            "suiteSha256": "e" * 64,
            "caseCount": 3,
            "hardAssertions": {"passed": 3, "total": 3},
            "securityAssertions": {"passed": 3, "total": 3},
            "objectiveScoreMicros": score,
            "protectedCategoryScoreMicros": {"safety": 1_000_000},
            "signerKeyId": "external-key-1",
            "signatureAlgorithm": "Ed25519",
            "signatureBase64": base64.b64encode(bytes(64)).decode("ascii"),
        }

    def build_candidate(self, content: bytes = b"# Better prompt\nUse explicit error handling.\n") -> dict:
        baseline = read_json(self.root, f"evals/results/{RUN_ID}/baseline.json")
        production = TARGETS[0]
        candidate_relative = f"tuning/proposals/{RUN_ID}/proposed/{production}"
        write_bytes(self.root, candidate_relative, content)
        target = {
            "productionPath": production,
            "candidatePath": f"proposed/{production}",
            "beforeSha256": baseline["targetHashes"][production],
            "candidateSha256": sha256_bytes(content),
        }
        proposal_digest = sha256_bytes(canonical_json({
            "runId": RUN_ID,
            "baselineSnapshotId": baseline["snapshotId"],
            "targets": [target],
        }))
        baseline_metric = self._metric("baseline", baseline, proposal_digest, 900_000)
        candidate_metric = self._metric("candidate", baseline, proposal_digest, 910_000)
        baseline_metric_raw = json_bytes(baseline_metric)
        candidate_metric_raw = json_bytes(candidate_metric)
        write_bytes(self.root, f"evals/results/{RUN_ID}/baseline-metrics.json", baseline_metric_raw)
        write_bytes(self.root, f"evals/results/{RUN_ID}/candidate-metrics.json", candidate_metric_raw)
        manifest = {
            "schemaVersion": 1,
            "runId": RUN_ID,
            "baseline": {
                "gitCommit": baseline["gitCommit"],
                "snapshotId": baseline["snapshotId"],
                "trainingCorpusSha256": baseline["trainingCorpusSha256"],
                "policySha256": baseline["policySha256"],
                "targetHashes": baseline["targetHashes"],
            },
            "proposalDigest": proposal_digest,
            "targets": [target],
            "metrics": {
                "definitionSha256": "d" * 64,
                "baselineArtifactPath": f"evals/results/{RUN_ID}/baseline-metrics.json",
                "baselineArtifactSha256": sha256_bytes(baseline_metric_raw),
                "candidateArtifactPath": f"evals/results/{RUN_ID}/candidate-metrics.json",
                "candidateArtifactSha256": sha256_bytes(candidate_metric_raw),
            },
            "rollback": {
                "candidateIdentifier": proposal_digest,
                "approvalIdentifier": None,
                "sourceSnapshotId": baseline["snapshotId"],
                "intendedIntegratedSnapshot": None,
                "targetBeforeHashes": {production: target["beforeSha256"]},
                "targetAfterHashes": {production: target["candidateSha256"]},
                "validationEvidence": [],
                "status": "NOT_APPLIED",
            },
        }
        write_json(self.root, f"tuning/proposals/{RUN_ID}/candidate-manifest.json", manifest)
        return manifest

    def mutate_manifest(self, mutate) -> dict:
        relative = f"tuning/proposals/{RUN_ID}/candidate-manifest.json"
        manifest = read_json(self.root, relative)
        mutate(manifest)
        write_json(self.root, relative, manifest)
        return manifest

    def mutate_metric(self, role: str, mutate) -> dict:
        relative = f"evals/results/{RUN_ID}/{role}-metrics.json"
        metric = read_json(self.root, relative)
        mutate(metric)
        raw = json_bytes(metric)
        write_bytes(self.root, relative, raw)
        manifest = read_json(self.root, f"tuning/proposals/{RUN_ID}/candidate-manifest.json")
        manifest["metrics"][f"{role}ArtifactSha256"] = sha256_bytes(raw)
        write_json(self.root, f"tuning/proposals/{RUN_ID}/candidate-manifest.json", manifest)
        return metric

    def write_approval(self, *, consumed: bool = False) -> None:
        baseline = read_json(self.root, f"evals/results/{RUN_ID}/baseline.json")
        manifest = read_json(self.root, f"tuning/proposals/{RUN_ID}/candidate-manifest.json")
        target_items = [
            {
                "productionPath": item["productionPath"],
                "candidateSha256": item["candidateSha256"],
            }
            for item in manifest["targets"]
        ]
        approval = {
            "schemaVersion": 1,
            "receiptType": "promotion-approval",
            "runId": RUN_ID,
            "baselineSnapshotId": baseline["snapshotId"],
            "proposalDigest": manifest["proposalDigest"],
            "targetSetDigest": sha256_bytes(canonical_json(target_items)),
            "scope": "APPLY_ALLOWLISTED_PROMPTS",
            "nonce": "unique-nonce-001",
            "consumption": {
                "status": "CONSUMED" if consumed else "UNCONSUMED",
                "recordId": "record-1" if consumed else None,
            },
            "signerKeyId": "external-key-1",
            "signatureAlgorithm": "Ed25519",
            "signatureBase64": base64.b64encode(bytes(64)).decode("ascii"),
        }
        write_json(self.root, f"evals/results/{RUN_ID}/approval-receipt.json", approval)


class SelfImprovementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = RepositoryFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def assert_invalid(self, code: str) -> dict:
        assessment = validate_candidate(self.fixture.root, RUN_ID)
        self.assertEqual("INVALID", assessment["structuralStatus"])
        self.assertIn(code, {item["code"] for item in assessment["blockers"]})
        self.assertEqual("BLOCKED_EXTERNAL_INTEGRATOR", assessment["promotionStatus"])
        return assessment

    def test_cli_has_exactly_four_nonpromotion_commands(self) -> None:
        self.assertEqual(("record", "prepare", "validate-candidate", "status"), COMMANDS)
        parser = build_parser()
        help_text = parser.format_help()
        for command in COMMANDS:
            self.assertIn(command, help_text)
        self.assertNotIn(" apply ", help_text)
        self.assertNotIn(" promote ", help_text)

    def test_record_is_exclusive_strict_and_does_not_disclose_secret(self) -> None:
        original = {target: (self.fixture.root / target).read_bytes() for target in TARGETS}
        result = record_feedback(
            self.fixture.root,
            source="user",
            category="weak-explanation",
            summary="The explanation skipped the retry behavior.",
            expected_behavior="Explain bounded retries and the terminal failure path.",
        )
        self.assertEqual("RECORDED_UNTRUSTED_SIGNAL", result["status"])
        with self.assertRaisesRegex(ContractError, "SIGNAL_ALREADY_EXISTS"):
            record_feedback(
                self.fixture.root,
                source="user",
                category="weak-explanation",
                summary="The explanation skipped the retry behavior.",
                expected_behavior="Explain bounded retries and the terminal failure path.",
            )
        synthetic = synthetic_text("s", "k-", "A" * 24)
        with self.assertRaises(ContractError) as raised:
            record_feedback(
                self.fixture.root,
                source="user",
                category="citation-gap",
                summary=f"Remove {synthetic}",
                expected_behavior="Cite the official documentation.",
            )
        self.assertEqual("SECRET_DETECTED", raised.exception.code)
        self.assertNotIn(synthetic, raised.exception.detail)
        self.assertEqual(original, {target: (self.fixture.root / target).read_bytes() for target in TARGETS})

    def test_prepare_requires_clean_tree_and_binds_policy_targets_and_feedback(self) -> None:
        write_bytes(self.fixture.root, "unrelated.txt", b"dirty")
        with self.assertRaisesRegex(ContractError, "DIRTY_WORKTREE"):
            self.fixture.prepare()
        (self.fixture.root / "unrelated.txt").unlink()
        record_feedback(
            self.fixture.root,
            source="supervisor",
            category="evaluation-regression",
            summary="The visible score decreased.",
            expected_behavior="Reject objective regressions.",
        )
        result = self.fixture.prepare()
        baseline = read_json(self.fixture.root, f"evals/results/{RUN_ID}/baseline.json")
        self.assertEqual(result["snapshotId"], baseline["snapshotId"])
        self.assertEqual(list(TARGETS), list(baseline["targetHashes"]))
        self.assertEqual(1, len(baseline["feedbackSignals"]))
        self.assertEqual(
            hashlib.sha256((self.fixture.root / "self_improvement/policy.json").read_bytes()).hexdigest(),
            baseline["policySha256"],
        )

    def test_valid_local_candidate_is_still_blocked_and_never_writes_production(self) -> None:
        self.fixture.prepare()
        self.fixture.build_candidate()
        original = {target: (self.fixture.root / target).read_bytes() for target in TARGETS}
        assessment = validate_candidate(self.fixture.root, RUN_ID)
        self.assertEqual("VALID", assessment["structuralStatus"])
        self.assertEqual("BLOCKED_EXTERNAL_INTEGRATOR", assessment["promotionStatus"])
        codes = {item["code"] for item in assessment["blockers"]}
        self.assertIn("EXTERNAL_SIGNATURE_VERIFICATION_REQUIRED", codes)
        self.assertIn("EXPLICIT_APPROVAL_REQUIRED", codes)
        self.assertEqual(original, {target: (self.fixture.root / target).read_bytes() for target in TARGETS})
        before = sorted((str(path.relative_to(self.fixture.root)), path.read_bytes()) for path in self.fixture.root.rglob("*") if path.is_file())
        status = status_for_run(self.fixture.root, RUN_ID)
        after = sorted((str(path.relative_to(self.fixture.root)), path.read_bytes()) for path in self.fixture.root.rglob("*") if path.is_file())
        self.assertEqual(before, after)
        self.assertEqual("BLOCKED_EXTERNAL_INTEGRATOR", status["promotionStatus"])

    def test_json_parser_rejects_duplicate_bom_trailing_nan_and_boolean_integers(self) -> None:
        bad_values = (
            (b'{"a":1,"a":2}', "JSON_DUPLICATE_KEY"),
            (b"\xef\xbb\xbf{}", "JSON_BOM_FORBIDDEN"),
            (b"{} trailing", "JSON_INVALID"),
            (b'{"a":NaN}', "JSON_NONSTANDARD_NUMBER"),
            (b'{"a":Infinity}', "JSON_NONSTANDARD_NUMBER"),
        )
        for raw, code in bad_values:
            with self.subTest(code=code), self.assertRaises(ContractError) as raised:
                strict_json_bytes(raw, label="fixture")
            self.assertEqual(code, raised.exception.code)
        self.fixture.prepare()
        self.fixture.build_candidate()
        self.fixture.mutate_metric("candidate", lambda metric: metric.__setitem__("caseCount", True))
        self.assert_invalid("SCHEMA_INTEGER")

    def test_manifest_rejects_unknown_fields_and_cross_run_metric_paths(self) -> None:
        self.fixture.prepare()
        self.fixture.build_candidate()
        self.fixture.mutate_manifest(lambda manifest: manifest.__setitem__("ready", True))
        self.assert_invalid("SCHEMA_KEYS")

        self.fixture.close()
        self.fixture = RepositoryFixture()
        self.fixture.prepare()
        self.fixture.build_candidate()
        self.fixture.mutate_manifest(
            lambda manifest: manifest["metrics"].__setitem__(
                "candidateArtifactPath", "evals/results/different-run/candidate-metrics.json"
            )
        )
        self.assert_invalid("METRIC_PATH_BINDING")

    def test_candidate_rejects_traversal_extra_symlink_and_hardlink(self) -> None:
        scenarios = []

        def traversal(fixture: RepositoryFixture) -> str:
            fixture.mutate_manifest(lambda manifest: manifest["targets"][0].__setitem__("candidatePath", "proposed/../escape.md"))
            return "CANDIDATE_PATH_BINDING"

        def extra(fixture: RepositoryFixture) -> str:
            write_bytes(fixture.root, f"tuning/proposals/{RUN_ID}/proposed/extra.md", b"extra")
            return "CANDIDATE_EXTRA_OR_MISSING_FILE"

        def symlink(fixture: RepositoryFixture) -> str:
            manifest = read_json(fixture.root, f"tuning/proposals/{RUN_ID}/candidate-manifest.json")
            candidate = fixture.root / f"tuning/proposals/{RUN_ID}" / manifest["targets"][0]["candidatePath"]
            candidate.unlink()
            candidate.symlink_to(fixture.root / TARGETS[1])
            return "PATH_SYMLINK_FORBIDDEN"

        def hardlink(fixture: RepositoryFixture) -> str:
            manifest = read_json(fixture.root, f"tuning/proposals/{RUN_ID}/candidate-manifest.json")
            candidate = fixture.root / f"tuning/proposals/{RUN_ID}" / manifest["targets"][0]["candidatePath"]
            os.link(candidate, fixture.root / f"tuning/proposals/{RUN_ID}/proposed/alias.md")
            return "HARD_LINK_FORBIDDEN"

        scenarios.extend((traversal, extra, symlink, hardlink))
        for scenario in scenarios:
            with self.subTest(scenario=scenario.__name__):
                self.fixture.close()
                self.fixture = RepositoryFixture()
                self.fixture.prepare()
                self.fixture.build_candidate()
                self.assert_invalid(scenario(self.fixture))

    def test_candidate_rejects_secret_nul_invalid_utf8_and_oversize(self) -> None:
        contents = (
            (synthetic_text("s", "k-", "B" * 24).encode(), "SECRET_DETECTED"),
            (b"valid\x00invalid", "NUL_BYTE_FORBIDDEN"),
            (b"\xff\xfe", "INVALID_UTF8"),
            (b"x" * 131_073, "ARTIFACT_TOO_LARGE"),
        )
        for content, code in contents:
            with self.subTest(code=code):
                self.fixture.close()
                self.fixture = RepositoryFixture()
                self.fixture.prepare()
                self.fixture.build_candidate(content)
                assessment = self.assert_invalid(code)
                if code == "SECRET_DETECTED":
                    self.assertNotIn(content.decode(), json.dumps(assessment))

    def test_every_secret_rule_rejects_without_disclosure(self) -> None:
        signatures = (
            synthetic_text("-----BEGIN", " PRIVATE KEY-----"),
            synthetic_text("Bearer ", "abcdefghijk"),
            synthetic_text("api_key", "=", "abcdefghijk"),
            synthetic_text("AK", "IA", "1234567890ABCDEF"),
            synthetic_text("gh", "p_", "A" * 24),
            synthetic_text("s", "k-", "C" * 24),
        )
        for signature in signatures:
            with self.subTest(signature_length=len(signature)):
                with self.assertRaises(ContractError) as raised:
                    record_feedback(
                        self.fixture.root,
                        source="user",
                        category="citation-gap",
                        summary=synthetic_text("Synthetic signature: ", signature),
                        expected_behavior="Reject the fixture without disclosing it.",
                    )
                self.assertEqual("SECRET_DETECTED", raised.exception.code)
                self.assertNotIn(signature, raised.exception.detail)

    def test_validation_rejects_dirty_tree_stale_commit_and_production_drift(self) -> None:
        scenarios = []

        def dirty(fixture: RepositoryFixture) -> str:
            write_bytes(fixture.root, "outside-run.txt", b"dirty")
            return "DIRTY_WORKTREE"

        def stale(fixture: RepositoryFixture) -> str:
            fixture.git("add", "evals/results", "tuning/proposals")
            fixture.git("commit", "-qm", "freeze run artifacts")
            return "STALE_BASELINE"

        def drift(fixture: RepositoryFixture) -> str:
            write_bytes(fixture.root, TARGETS[2], b"changed production prompt")
            fixture.git("add", TARGETS[2])
            fixture.git("commit", "-qm", "unexpected production drift")
            baseline = read_json(fixture.root, f"evals/results/{RUN_ID}/baseline.json")
            baseline["gitCommit"] = subprocess.check_output(
                ["git", "-C", str(fixture.root), "rev-parse", "HEAD"], text=True
            ).strip()
            preimage = dict(baseline)
            del preimage["snapshotId"]
            baseline["snapshotId"] = f"sha256:{sha256_bytes(canonical_json(preimage))}"
            write_json(fixture.root, f"evals/results/{RUN_ID}/baseline.json", baseline)
            manifest = read_json(fixture.root, f"tuning/proposals/{RUN_ID}/candidate-manifest.json")
            manifest["baseline"]["gitCommit"] = baseline["gitCommit"]
            manifest["baseline"]["snapshotId"] = baseline["snapshotId"]
            write_json(fixture.root, f"tuning/proposals/{RUN_ID}/candidate-manifest.json", manifest)
            return "PRODUCTION_TARGET_DRIFT"

        scenarios.extend((dirty, stale, drift))
        for scenario in scenarios:
            with self.subTest(scenario=scenario.__name__):
                self.fixture.close()
                self.fixture = RepositoryFixture()
                self.fixture.prepare()
                self.fixture.build_candidate()
                self.assert_invalid(scenario(self.fixture))

    def test_metrics_reject_regression_nonperfect_security_and_incomparable_suite(self) -> None:
        mutations = (
            (lambda metric: metric.__setitem__("objectiveScoreMicros", 700_000), "METRIC_OBJECTIVE_FLOOR"),
            (lambda metric: metric["securityAssertions"].__setitem__("passed", 2), "METRIC_HARD_FAILURE"),
            (lambda metric: metric.__setitem__("suiteSha256", "f" * 64), "METRIC_COMPARABILITY"),
            (lambda metric: metric["hardAssertions"].update({"passed": 2, "total": 2}), "METRIC_COMPARABILITY"),
            (lambda metric: metric.__setitem__("signatureBase64", "not-base64"), "SIGNATURE_ENCODING"),
        )
        for mutation, code in mutations:
            with self.subTest(code=code):
                self.fixture.close()
                self.fixture = RepositoryFixture()
                self.fixture.prepare()
                self.fixture.build_candidate()
                self.fixture.mutate_metric("candidate", mutation)
                self.assert_invalid(code)

    def test_rollback_and_replayed_approval_are_rejected(self) -> None:
        self.fixture.prepare()
        self.fixture.build_candidate()
        self.fixture.mutate_manifest(lambda manifest: manifest["rollback"].__setitem__("status", "APPLIED"))
        self.assert_invalid("ROLLBACK_BINDING")

        self.fixture.close()
        self.fixture = RepositoryFixture()
        self.fixture.prepare()
        self.fixture.build_candidate()
        self.fixture.write_approval(consumed=True)
        self.assert_invalid("APPROVAL_REPLAY")

    def test_policy_is_exactly_pinned(self) -> None:
        policy_path = self.fixture.root / "self_improvement/policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        policy["allowedTargets"].append("protected/security-policy.md")
        policy["allowedTargets"].sort()
        policy_path.write_text(json.dumps(policy), encoding="utf-8")
        with self.assertRaises(ContractError) as raised:
            prepare_baseline(self.fixture.root, RUN_ID)
        self.assertEqual("POLICY_HASH_MISMATCH", raised.exception.code)

    def test_closed_schema_matrix_and_attacker_key_non_disclosure(self) -> None:
        record = record_feedback(
            self.fixture.root,
            source="user",
            category="weak-explanation",
            summary="Explain the failure boundary.",
            expected_behavior="Keep the explanation source grounded.",
        )
        signal_path = self.fixture.root / record["path"]
        signal = json.loads(signal_path.read_text(encoding="utf-8"))
        del signal["contentDigest"]
        signal_path.write_text(json.dumps(signal), encoding="utf-8")
        with self.assertRaises(ContractError) as raised:
            self.fixture.prepare()
        self.assertEqual("SCHEMA_KEYS", raised.exception.code)

        self.fixture.close()
        self.fixture = RepositoryFixture()
        self.fixture.prepare()
        self.fixture.build_candidate()
        baseline_path = self.fixture.root / f"evals/results/{RUN_ID}/baseline.json"
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        baseline["unexpected"] = True
        baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
        self.assert_invalid("SCHEMA_KEYS")

        self.fixture.close()
        self.fixture = RepositoryFixture()
        self.fixture.prepare()
        self.fixture.build_candidate()
        attacker_key = synthetic_text("s", "k-", "D" * 24)
        self.fixture.mutate_manifest(lambda manifest: manifest.__setitem__(attacker_key, True))
        assessment = self.assert_invalid("SCHEMA_KEYS")
        self.assertNotIn(attacker_key, json.dumps(assessment))

        self.fixture.close()
        self.fixture = RepositoryFixture()
        self.fixture.prepare()
        self.fixture.build_candidate()
        self.fixture.mutate_manifest(lambda manifest: manifest["targets"][0].pop("candidateSha256"))
        self.assert_invalid("SCHEMA_KEYS")

        self.fixture.close()
        self.fixture = RepositoryFixture()
        self.fixture.prepare()
        self.fixture.build_candidate()
        self.fixture.mutate_metric("candidate", lambda metric: metric.pop("signatureAlgorithm"))
        self.assert_invalid("SCHEMA_KEYS")

    def test_nonallowlisted_duplicate_targets_and_approval_binding_fail_closed(self) -> None:
        self.fixture.prepare()
        self.fixture.build_candidate()
        self.fixture.mutate_manifest(lambda manifest: manifest["targets"][0].__setitem__("productionPath", "protected/policy.md"))
        self.assert_invalid("TARGET_NOT_ALLOWED")

        self.fixture.close()
        self.fixture = RepositoryFixture()
        self.fixture.prepare()
        self.fixture.build_candidate()
        self.fixture.mutate_manifest(lambda manifest: manifest["targets"].append(dict(manifest["targets"][0])))
        self.assert_invalid("MANIFEST_TARGETS")

        self.fixture.close()
        self.fixture = RepositoryFixture()
        self.fixture.prepare()
        self.fixture.build_candidate()
        self.fixture.write_approval()
        approval_path = self.fixture.root / f"evals/results/{RUN_ID}/approval-receipt.json"
        approval = json.loads(approval_path.read_text(encoding="utf-8"))
        approval["proposalDigest"] = "0" * 64
        approval_path.write_text(json.dumps(approval), encoding="utf-8")
        self.assert_invalid("APPROVAL_BINDING")

    def test_oversized_metric_and_interrupted_atomic_write_preserve_prior_bytes(self) -> None:
        self.fixture.prepare()
        self.fixture.build_candidate()
        write_bytes(
            self.fixture.root,
            f"evals/results/{RUN_ID}/candidate-metrics.json",
            b"{" + b" " * 262_144 + b"}",
        )
        self.assert_invalid("ARTIFACT_TOO_LARGE")

        output = self.fixture.root / f"evals/results/{RUN_ID}/local-assessment.json"
        previous = output.read_bytes()
        with mock.patch("self_improvement.core.os.replace", side_effect=OSError("interrupted")):
            with self.assertRaises(OSError):
                atomic_write_json(
                    self.fixture.root,
                    f"evals/results/{RUN_ID}/local-assessment.json",
                    {"replacement": True},
                )
        self.assertEqual(previous, output.read_bytes())
        self.assertEqual([], list(output.parent.glob("*.tmp")))

    def test_manifest_size_limit_and_post_open_identity_check_fail_closed(self) -> None:
        self.fixture.prepare()
        self.fixture.build_candidate()
        write_bytes(
            self.fixture.root,
            f"tuning/proposals/{RUN_ID}/candidate-manifest.json",
            b"{" + b" " * 262_144 + b"}",
        )
        self.assert_invalid("ARTIFACT_TOO_LARGE")

        target = write_bytes(self.fixture.root, "race-target.md", b"safe")
        original_stat = os.stat
        calls = {"count": 0}

        def changing_stat(path, *args, **kwargs):
            result = original_stat(path, *args, **kwargs)
            if path == target.name and kwargs.get("dir_fd") is not None:
                calls["count"] += 1
                if calls["count"] == 2:
                    values = list(result)
                    values[1] += 1
                    return os.stat_result(values)
            return result

        with mock.patch("self_improvement.core.os.stat", side_effect=changing_stat):
            with self.assertRaises(ContractError) as raised:
                secure_read(self.fixture.root, target.name, maximum=1024)
        self.assertEqual("PATH_IDENTITY_CHANGED", raised.exception.code)

        real_fstat = os.fstat
        regular_calls = {"count": 0}

        def changing_metadata(descriptor):
            result = real_fstat(descriptor)
            if stat.S_ISREG(result.st_mode):
                regular_calls["count"] += 1
                if regular_calls["count"] == 2:
                    return SimpleNamespace(
                        st_mode=result.st_mode,
                        st_nlink=result.st_nlink,
                        st_dev=result.st_dev,
                        st_ino=result.st_ino,
                        st_size=result.st_size,
                        st_mtime_ns=result.st_mtime_ns + 1,
                        st_ctime_ns=result.st_ctime_ns,
                    )
            return result

        with mock.patch("self_improvement.core.os.fstat", side_effect=changing_metadata):
            with self.assertRaises(ContractError) as raised:
                secure_read(self.fixture.root, target.name, maximum=1024)
        self.assertEqual("PATH_IDENTITY_CHANGED", raised.exception.code)


if __name__ == "__main__":
    unittest.main()
