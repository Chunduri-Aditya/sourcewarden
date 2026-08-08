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
from src.quality import score_response
from src.schema import WorkflowInstructionRequest, schema_to_dict
from src.workflow_instruction_generator import WorkflowInstructionGenerator, analyze_planning_intent


def main() -> int:
    parser = argparse.ArgumentParser(description="Query the n8n multi-RAG workflow instruction system.")
    parser.add_argument("--query", required=True)
    parser.add_argument(
        "--mode",
        default="beginner_steps",
        choices=[
            "beginner_steps",
            "technical_steps",
            "workflow_json_blueprint",
            "troubleshooting",
            "full_build_plan",
        ],
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--show-sources", action="store_true")
    parser.add_argument("--show-chunks", action="store_true")
    parser.add_argument("--quality-check", action="store_true")
    parser.add_argument("--save-output", default=None, help="Save the generated answer or JSON payload to this path.")
    parser.add_argument("--show-router", action="store_true")
    parser.add_argument("--show-required-sections", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    generator = WorkflowInstructionGenerator()
    planning = analyze_planning_intent(args.query)
    decision = None
    chunks = []
    if args.show_chunks or args.show_router:
        decision, chunks = generator.retriever.retrieve_with_decision(args.query, top_k=args.top_k)
    response = generator.generate(
        WorkflowInstructionRequest(user_task=args.query, output_mode=args.mode),
        top_k=args.top_k,
    )
    output_text = ""
    if args.as_json:
        output_text = json.dumps(schema_to_dict(response), indent=2)
        print(output_text)
    else:
        if args.show_required_sections:
            print("Required sections:")
            for section in REQUIRED_WORKFLOW_SECTIONS:
                print(f"- {section}")
            print()
        if args.show_router and decision:
            print("Router:")
            print(f"- selected_rags: {', '.join(decision.selected_rags)}")
            print(f"- reason: {decision.reason}")
            print(f"- intents: {', '.join(decision.retrieval_parameters.get('intents', []))}")
            print("- planning_debug:")
            for key, value in planning.to_debug_dict().items():
                if isinstance(value, list):
                    printable = ", ".join(value) if value else "none"
                else:
                    printable = str(value)
                print(f"  - {key}: {printable}")
            print()
        output_text = response.content
        print(output_text)
        if args.show_sources and response.sources:
            print("\nRetrieved source objects:")
            for source in response.sources:
                heading = " > ".join(source.get("heading_path") or [])
                print(f"- {source.get('title')} {heading}: {source.get('url')}")
        if args.show_chunks:
            print("\nRetrieved chunks:")
            if decision:
                print(f"Selected RAGs: {', '.join(decision.selected_rags)}")
                print(f"Router reason: {decision.reason}")
            for index, chunk in enumerate(chunks, start=1):
                heading = " > ".join(chunk.heading_path or [])
                preview = chunk.text.replace("\n", " ")[:320]
                print(
                    f"\n[{index}] {chunk.rag_name} score={chunk.relevance_score} "
                    f"source={chunk.source_title} heading={heading}\n{chunk.source_url}\n{preview}"
                )
        if args.quality_check:
            quality_case = {
                "name": "cli_query",
                "question": args.query,
                "required_sections": REQUIRED_WORKFLOW_SECTIONS,
                "must_cite_sources": True,
            }
            result = score_response(response, quality_case)
            print("\nQuality check:")
            print(f"- score: {result.score:.2f}")
            if result.failed_checks:
                print(f"- failed checks: {', '.join(result.failed_checks)}")
            else:
                print("- failed checks: none")
            print("- planning_debug:")
            for key, value in planning.to_debug_dict().items():
                if isinstance(value, list):
                    printable = ", ".join(value) if value else "none"
                else:
                    printable = str(value)
                print(f"  - {key}: {printable}")
    if args.save_output:
        path = Path(args.save_output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output_text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
