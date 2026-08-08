#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.prompt_builder import REQUIRED_WORKFLOW_SECTIONS
from src.rag_router import RagRouter
from src.schema import WorkflowInstructionRequest
from src.workflow_instruction_generator import WorkflowInstructionGenerator


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate RAG routing and answer contract.")
    parser.add_argument("--questions", default=str(ROOT / "data" / "eval" / "rag_eval_questions.jsonl"))
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--fail-on-errors", action="store_true")
    args = parser.parse_args()

    questions = load_questions(Path(args.questions))
    router = RagRouter()
    generator = WorkflowInstructionGenerator()
    has_indexes = any((ROOT / "data" / "indexes").glob("*.jsonl"))

    failures: list[dict[str, object]] = []
    for item in questions:
        question = item["question"]
        expected_rags = item.get("expected_rags", [])
        required_sections = item.get("required_sections") or REQUIRED_WORKFLOW_SECTIONS
        required_keywords = item.get("required_keywords", [])
        forbidden_behavior = item.get("forbidden_behavior", [])
        mode = item.get("mode", "full_build_plan")
        decision = router.route(question, top_k=args.top_k)
        missing_rags = [rag for rag in expected_rags if rag not in decision.selected_rags]
        response = generator.generate(
            WorkflowInstructionRequest(user_task=question, output_mode=mode),
            top_k=args.top_k,
        )
        missing_sections = [
            section for section in required_sections if f"# {section}" not in response.content
        ]
        missing_keywords = [
            keyword for keyword in required_keywords if keyword.lower() not in response.content.lower()
        ]
        forbidden_hits = [
            phrase for phrase in forbidden_behavior if phrase.lower() in response.content.lower()
        ]
        checks = {
            "router_expected_rags": not missing_rags,
            "required_sections": not missing_sections,
            "required_keywords": not missing_keywords,
            "forbidden_behavior": not forbidden_hits,
            "credentials": "# Credentials Needed" in response.content and "credential" in response.sections.get("Credentials Needed", "").lower(),
            "test_steps": "# Test Steps" in response.content and bool(response.sections.get("Test Steps", "").strip()),
            "error_handling": "# Error Handling" in response.content and bool(response.sections.get("Error Handling", "").strip()),
            "citations_section": "# Sources Used" in response.content,
            "retrieved_sources_when_indexed": bool(response.sources) if has_indexes else True,
        }
        if not all(checks.values()):
            failures.append(
                {
                    "question": question,
                    "checks": checks,
                    "selected_rags": decision.selected_rags,
                    "missing_rags": missing_rags,
                    "missing_sections": missing_sections,
                    "missing_keywords": missing_keywords,
                    "forbidden_hits": forbidden_hits,
                }
            )

    passed = len(questions) - len(failures)
    print(json.dumps({"questions": len(questions), "passed": passed, "failed": len(failures)}, indent=2))
    if failures:
        print("\nFailures:")
        for failure in failures:
            print(json.dumps(failure, indent=2))
    return 1 if failures and args.fail_on_errors else 0


def load_questions(path: Path) -> list[dict[str, object]]:
    questions: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped:
            questions.append(json.loads(stripped))
    return questions


if __name__ == "__main__":
    raise SystemExit(main())
