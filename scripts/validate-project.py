#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]

CHECKS = [
    (
        "RAG unit tests",
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        ROOT / "n8n_rag_system",
    ),
    (
        "Agent configuration",
        [sys.executable, "scripts/validate-agent-system.py"],
        ROOT,
    ),
    (
        "Generalized evaluations",
        ["node", "scripts/validate-generalized-evals.mjs"],
        ROOT,
    ),
    (
        "Evaluation grader self test",
        ["node", "scripts/grade-agent-eval.mjs", "--self-test"],
        ROOT,
    ),
    (
        "Run ledger validator self test",
        ["node", "scripts/validate-agent-run.mjs", "--self-test"],
        ROOT,
    ),
    (
        "Security gate self test",
        ["node", ".codex/hooks/security-gate.mjs", "--self-test"],
        ROOT,
    ),
    (
        "Repository security controls",
        ["node", ".codex/hooks/security-gate.mjs", "--repository-check"],
        ROOT,
    ),
]


def main() -> int:
    for name, command, working_directory in CHECKS:
        print(f"\n[{name}]", flush=True)
        result = subprocess.run(command, cwd=working_directory, check=False)
        if result.returncode != 0:
            print(f"FAILED: {name} returned {result.returncode}", file=sys.stderr)
            return result.returncode
    print("\nAll merged-project checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
