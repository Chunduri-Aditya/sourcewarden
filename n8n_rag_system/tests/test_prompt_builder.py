from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.prompt_builder import REQUIRED_WORKFLOW_SECTIONS, PromptBuilder


class PromptBuilderTests(unittest.TestCase):
    def test_prompt_builder_includes_required_workflow_sections(self) -> None:
        prompt = PromptBuilder(ROOT / "prompts").build(
            user_task="Build a Slack alert workflow.",
            retrieved_chunks=[],
            output_mode="beginner_steps",
        )
        for section in REQUIRED_WORKFLOW_SECTIONS:
            self.assertIn(f"# {section}", prompt)
        self.assertIn("Retrieved Facts", prompt)
        self.assertIn("Design Decisions", prompt)


if __name__ == "__main__":
    unittest.main()

