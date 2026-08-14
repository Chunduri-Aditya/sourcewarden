from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from web.services.self_improvement_status import discover_run_ids, status_for_all_runs


class DiscoverRunIdsTests(unittest.TestCase):
    def test_discovers_exactly_one_real_run(self) -> None:
        run_ids = discover_run_ids()
        self.assertEqual(run_ids, ["agent-reliability-20260725-01"])

    def test_zero_runs_returns_empty_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty_dir = Path(tmp) / "nothing-here"
            with (
                mock.patch("web.services.self_improvement_status.EVALS_RESULTS_DIR", empty_dir),
                mock.patch("web.services.self_improvement_status.TUNING_PROPOSALS_DIR", empty_dir),
            ):
                self.assertEqual(discover_run_ids(), [])


class StatusForAllRunsTests(unittest.TestCase):
    def test_reports_known_partial_artifact_state_for_the_real_run(self) -> None:
        results = status_for_all_runs()
        self.assertEqual(len(results), 1)
        entry = results[0]
        self.assertEqual(entry["run_id"], "agent-reliability-20260725-01")
        self.assertTrue(entry["ok"], entry.get("error"))
        artifacts = entry["data"]["artifacts"]
        # The real repo state has evals/results/<run>/baseline.json but no
        # tuning/proposals/<run>/candidate-manifest.json (and none of the
        # later-stage artifacts), so this run is genuinely partial: some
        # artifacts present, some absent. Do not assert all-True.
        self.assertTrue(any(artifacts.values()))
        self.assertFalse(all(artifacts.values()))
        self.assertTrue(artifacts["baseline"])
        self.assertFalse(artifacts["candidateManifest"])

    def test_zero_runs_returns_empty_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty_dir = Path(tmp) / "nothing-here"
            with (
                mock.patch("web.services.self_improvement_status.EVALS_RESULTS_DIR", empty_dir),
                mock.patch("web.services.self_improvement_status.TUNING_PROPOSALS_DIR", empty_dir),
            ):
                self.assertEqual(status_for_all_runs(), [])


if __name__ == "__main__":
    unittest.main()
