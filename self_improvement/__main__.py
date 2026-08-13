from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .core import (
    ContractError,
    prepare_baseline,
    record_feedback,
    status_for_run,
    validate_candidate,
)


COMMANDS = ("record", "prepare", "validate-candidate", "status")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m self_improvement",
        description="Prepare and assess bounded prompt challengers without applying them.",
    )
    parser.add_argument("--root", type=Path, default=Path.cwd(), help=argparse.SUPPRESS)
    subparsers = parser.add_subparsers(dest="command", required=True)

    record = subparsers.add_parser("record", help="record one untrusted feedback signal")
    record.add_argument("--source", required=True, choices=("user", "supervisor"))
    record.add_argument("--category", required=True)
    record.add_argument("--summary", required=True)
    record.add_argument("--expected-behavior", required=True)

    prepare = subparsers.add_parser("prepare", help="freeze a clean baseline")
    prepare.add_argument("--run-id", required=True)

    validate = subparsers.add_parser(
        "validate-candidate",
        help="validate a frozen challenger without applying it",
    )
    validate.add_argument("--run-id", required=True)

    status = subparsers.add_parser("status", help="report run artifacts and blockers")
    status.add_argument("--run-id", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "record":
            result = record_feedback(
                args.root,
                source=args.source,
                category=args.category,
                summary=args.summary,
                expected_behavior=args.expected_behavior,
            )
        elif args.command == "prepare":
            result = prepare_baseline(args.root, args.run_id)
        elif args.command == "validate-candidate":
            result = validate_candidate(args.root, args.run_id)
        else:
            result = status_for_run(args.root, args.run_id)
    except ContractError as error:
        print(json.dumps({"status": "ERROR", "code": error.code, "detail": error.detail}))
        return 2

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if result.get("structuralStatus") == "INVALID":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
