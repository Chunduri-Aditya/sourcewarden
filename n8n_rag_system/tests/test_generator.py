from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.workflow_instruction_generator import (
    WorkflowInstructionGenerator,
    validate_workflow_sections,
)


class GeneratorTests(unittest.TestCase):
    def test_generator_output_validation(self) -> None:
        response = WorkflowInstructionGenerator().generate(
            "Build a workflow that sends Slack alerts from a schedule.",
            top_k=1,
        )
        self.assertIn("# Workflow Name", response.content)
        self.assertIn("Exact settings", response.sections["Nodes To Add"])
        self.assertIn("credential", response.sections["Credentials Needed"].lower())
        validate_workflow_sections(response.sections, require_sources=bool(response.sources))

    def test_validation_fails_for_missing_sections(self) -> None:
        with self.assertRaises(ValueError):
            validate_workflow_sections({"Workflow Name": "Only one section"})


if __name__ == "__main__":
    unittest.main()

