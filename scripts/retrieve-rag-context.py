#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
RAG_ROOT = ROOT / "n8n_rag_system"
if str(RAG_ROOT) not in sys.path:
    sys.path.insert(0, str(RAG_ROOT))

from src.planning_context import build_planning_context


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Retrieve source-grounded context for an n8n workflow plan."
    )
    parser.add_argument("--query", required=True, help="The workflow request to ground.")
    parser.add_argument("--top-k", type=int, default=5, help="Maximum evidence chunks to return.")
    parser.add_argument(
        "--max-chars",
        type=int,
        default=4000,
        help="Maximum characters to include from each evidence chunk.",
    )
    parser.add_argument("--pretty", action="store_true", help="Indent the JSON output.")
    parser.add_argument(
        "--require-evidence",
        action="store_true",
        help="Return a nonzero status when no indexed evidence is available.",
    )
    args = parser.parse_args()

    try:
        context = build_planning_context(
            args.query,
            top_k=args.top_k,
            max_chars_per_evidence=args.max_chars,
        )
    except ValueError as error:
        parser.error(str(error))

    print(json.dumps(context, indent=2 if args.pretty else None, sort_keys=True))
    if args.require_evidence and context["status"] != "ready":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
