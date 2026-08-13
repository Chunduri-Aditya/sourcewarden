from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.workflow_examples import (
    build_workflow_example_chunks,
    clean_node_type,
    is_trigger_type,
    parse_workflow_file,
)


class WorkflowExamplesTests(unittest.TestCase):
    def test_clean_node_type_strips_known_prefixes(self) -> None:
        self.assertEqual(clean_node_type("n8n-nodes-base.slack"), "slack")
        self.assertEqual(clean_node_type("@n8n/n8n-nodes-langchain.agent"), "agent")
        self.assertEqual(clean_node_type("some-custom-node"), "some-custom-node")

    def test_is_trigger_type_detects_triggers_and_webhook(self) -> None:
        self.assertTrue(is_trigger_type("n8n-nodes-base.manualTrigger"))
        self.assertTrue(is_trigger_type("n8n-nodes-base.webhook"))
        self.assertFalse(is_trigger_type("n8n-nodes-base.slack"))

    def test_parse_workflow_file_extracts_nodes_and_trigger(self) -> None:
        payload = {
            "name": "Send a Slack alert",
            "description": "Posts a message to Slack.",
            "tags": [{"name": "automation"}, "n8n"],
            "nodes": [
                {"type": "n8n-nodes-base.manualTrigger", "name": "On click"},
                {"type": "n8n-nodes-base.slack", "name": "Slack"},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            workflows_root = Path(tmp)
            workflow_dir = workflows_root / "Slack"
            workflow_dir.mkdir()
            path = workflow_dir / "0001_test.json"
            path.write_text(json.dumps(payload), encoding="utf-8")

            chunk, failure = parse_workflow_file(path, workflows_root)

            self.assertIsNone(failure)
            assert chunk is not None
            self.assertEqual(chunk.rag_target, "n8n_workflow_examples_rag")
            self.assertEqual(chunk.source_title, "Send a Slack alert")
            self.assertEqual(
                chunk.source_url,
                "https://github.com/Zie619/n8n-workflows/blob/main/workflows/Slack/0001_test.json",
            )
            self.assertIn("manualTrigger", chunk.metadata["trigger_types"])
            self.assertIn("slack", chunk.metadata["node_types"])
            self.assertIn("Posts a message to Slack.", chunk.text)

    def test_parse_workflow_file_reports_failure_on_malformed_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workflows_root = Path(tmp)
            path = workflows_root / "broken.json"
            path.write_text("{not valid json", encoding="utf-8")

            chunk, failure = parse_workflow_file(path, workflows_root)

            self.assertIsNone(chunk)
            assert failure is not None
            self.assertEqual(failure.file_name, "broken.json")

    def test_parse_workflow_file_reports_failure_on_missing_nodes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workflows_root = Path(tmp)
            path = workflows_root / "no_nodes.json"
            path.write_text(json.dumps({"name": "Empty"}), encoding="utf-8")

            chunk, failure = parse_workflow_file(path, workflows_root)

            self.assertIsNone(chunk)
            assert failure is not None
            self.assertIn("nodes", failure.reason)

    def test_build_workflow_example_chunks_skips_bad_files_and_keeps_good_ones(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workflows_root = Path(tmp)
            good = {
                "name": "Good workflow",
                "nodes": [{"type": "n8n-nodes-base.webhook", "name": "Webhook"}],
            }
            (workflows_root / "good.json").write_text(json.dumps(good), encoding="utf-8")
            (workflows_root / "bad.json").write_text("not json", encoding="utf-8")

            chunks, failures = build_workflow_example_chunks(workflows_root)

            self.assertEqual(len(chunks), 1)
            self.assertEqual(len(failures), 1)
            self.assertEqual(chunks[0].source_title, "Good workflow")


if __name__ == "__main__":
    unittest.main()
