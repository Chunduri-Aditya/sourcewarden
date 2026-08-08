#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.chunker import chunk_all, chunk_statistics, format_chunk_statistics
from src.utils import load_yaml_config


def main() -> int:
    parser = argparse.ArgumentParser(description="Chunk cleaned n8n documentation.")
    parser.add_argument("--processed-dir", default=str(ROOT / "data" / "processed"))
    parser.add_argument("--output", default=str(ROOT / "data" / "processed" / "chunks.jsonl"))
    parser.add_argument("--chunking-config", default=str(ROOT / "config" / "chunking.yaml"))
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument("--overlap-tokens", type=int, default=None)
    parser.add_argument("--min-tokens", type=int, default=None)
    parser.add_argument("--stats", action="store_true", help="Print detailed chunk statistics.")
    args = parser.parse_args()

    config = load_yaml_config(args.chunking_config) or {}
    max_tokens = args.max_tokens or int(config.get("max_tokens", 1000))
    overlap_tokens = args.overlap_tokens or int(config.get("overlap_tokens", 150))
    min_tokens = args.min_tokens or int(config.get("min_chunk_tokens", 80))
    chunks = chunk_all(
        processed_dir=args.processed_dir,
        output_path=args.output,
        max_tokens=max_tokens,
        overlap_tokens=overlap_tokens,
        min_tokens=min_tokens,
    )
    stats = chunk_statistics(chunks)
    print(f"Chunks written: {len(chunks)}")
    if args.stats:
        print(format_chunk_statistics(stats))
    else:
        for rag_name, count in sorted(stats["chunks_per_rag"].items()):
            print(f"{rag_name}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
