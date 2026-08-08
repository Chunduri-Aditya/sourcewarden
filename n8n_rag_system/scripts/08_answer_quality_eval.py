#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.quality import QualityResult, score_response, summarize_quality
from src.schema import WorkflowInstructionRequest
from src.workflow_instruction_generator import WorkflowInstructionGenerator


def main() -> int:
    parser = argparse.ArgumentParser(description="Run adversarial answer-quality checks.")
    parser.add_argument("--cases", default=str(ROOT / "data" / "eval" / "adversarial_cases.jsonl"))
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--fail-under", type=float, default=0.0, help="Return non-zero if average score is below this value.")
    args = parser.parse_args()

    cases = load_cases(Path(args.cases))
    if args.limit:
        cases = cases[: args.limit]

    generator = WorkflowInstructionGenerator()
    results: list[QualityResult] = []
    routing_failures: Counter[str] = Counter()

    for index, case in enumerate(cases, start=1):
        question = case["question"]
        try:
            decision = generator.retriever.router.route(question, top_k=args.top_k)
            response = generator.generate(
                WorkflowInstructionRequest(user_task=question, output_mode="full_build_plan"),
                top_k=args.top_k,
            )
            result = score_response(response, {"name": f"case_{index}", **case})
            missing_rags = [rag for rag in case.get("expected_rags", []) if rag not in decision.selected_rags]
            if missing_rags:
                result.failed_checks.append("expected_rags_selected")
                routing_failures.update(missing_rags)
                result.score = max(0.0, result.score - 0.05)
        except Exception as exc:
            result = QualityResult(
                case_name=f"case_{index}",
                score=0.0,
                failed_checks=[f"generation_failed:{exc}"],
            )
        results.append(result)

    summary = summarize_quality(results)
    if routing_failures:
        summary["weakest_categories"].append(
            {"check": "expected_rags_selected", "failures": sum(routing_failures.values())}
        )
        summary["recommendations"].append("Improve routing for adversarial cases with missing expected RAGs.")

    payload = {
        "case_count": summary["case_count"],
        "average_score": summary["average_score"],
        "weakest_categories": summary["weakest_categories"],
        "recommendations": summary["recommendations"],
        "cases": [result.to_dict() for result in results],
    }

    if args.as_json:
        print(json.dumps(payload, indent=2))
    else:
        print("n8n RAG Answer Quality Evaluation")
        print("=" * 38)
        for result in results:
            failed = ", ".join(result.failed_checks) if result.failed_checks else "none"
            print(f"{result.case_name}: score={result.score:.2f}; failed={failed}")
        print()
        print(f"average score: {summary['average_score']:.4f}")
        print("weakest categories:")
        if summary["weakest_categories"]:
            for item in summary["weakest_categories"]:
                print(f"  - {item['check']}: {item['failures']}")
        else:
            print("  - none")
        print("recommendations:")
        for recommendation in summary["recommendations"]:
            print(f"  - {recommendation}")

    return 1 if summary["average_score"] < args.fail_under else 0


def load_cases(path: Path) -> list[dict[str, object]]:
    cases: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped:
            cases.append(json.loads(stripped))
    return cases


if __name__ == "__main__":
    raise SystemExit(main())

