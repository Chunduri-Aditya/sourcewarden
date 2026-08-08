#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.schema import Chunk, RAG_NAMES
from src.utils import read_jsonl
from src.vector_store import JsonVectorStore


def main() -> int:
    parser = argparse.ArgumentParser(description="Build separate local RAG indexes.")
    parser.add_argument("--chunks", default=str(ROOT / "data" / "processed" / "chunks.jsonl"))
    parser.add_argument("--index-dir", default=str(ROOT / "data" / "indexes"))
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    rows = read_jsonl(args.chunks)
    if not rows:
        print(f"No chunks found at {args.chunks}. Run scripts/03_chunk_docs.py first.")
        return 0

    grouped: dict[str, list[Chunk]] = defaultdict(list)
    for row in rows:
        chunk = Chunk.model_validate(row)
        grouped[chunk.rag_target].append(chunk)

    store = JsonVectorStore(args.index_dir)
    if args.reset:
        for rag_name in sorted(RAG_NAMES):
            store.reset_collection(rag_name)

    total = 0
    for rag_name, chunks in sorted(grouped.items()):
        count = store.add_chunks(rag_name, chunks)
        total += count
        print(f"{rag_name}: indexed {count} chunks")
    print(f"Total indexed chunks: {total}")
    print(f"Embedding provider: {store.embedding_provider.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

