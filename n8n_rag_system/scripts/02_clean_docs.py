#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.cleaner import clean_all


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean raw n8n docs into markdown-like text.")
    parser.add_argument("--raw-dir", default=str(ROOT / "data" / "raw"))
    parser.add_argument("--processed-dir", default=str(ROOT / "data" / "processed"))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    results = clean_all(args.raw_dir, args.processed_dir, force=args.force)
    counts = Counter(result["status"] for result in results)
    print(f"Raw files processed: {len(results)}")
    for status, count in sorted(counts.items()):
        print(f"{status}: {count}")
    for result in results:
        if result["status"] == "failed":
            print(f"- failed: {result.get('raw_path')} {result.get('error')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

