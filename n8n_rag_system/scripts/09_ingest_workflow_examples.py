#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.schema import schema_to_dict
from src.utils import ensure_dir, write_jsonl
from src.vector_store import JsonVectorStore
from src.workflow_examples import RAG_TARGET, DEFAULT_REPO_URL, build_workflow_example_chunks


def clone_or_update_repo(clone_dir: Path, repo_url: str) -> None:
    if (clone_dir / ".git").exists():
        subprocess.run(["git", "-C", str(clone_dir), "pull", "--ff-only"], check=True)
        return
    ensure_dir(clone_dir.parent)
    subprocess.run(["git", "clone", "--depth", "1", repo_url, str(clone_dir)], check=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Clone Zie619/n8n-workflows locally and index it as the n8n_workflow_examples_rag "
            "collection: real community workflow JSON exports, retrievable as cited example patterns."
        )
    )
    parser.add_argument("--clone-dir", default=str(ROOT / "data" / "raw" / "n8n-workflows"))
    parser.add_argument("--repo-url", default=DEFAULT_REPO_URL)
    parser.add_argument(
        "--skip-clone",
        action="store_true",
        help="Reuse an existing local clone instead of running git clone/pull.",
    )
    parser.add_argument("--output", default=str(ROOT / "data" / "processed" / "workflow_examples_chunks.jsonl"))
    parser.add_argument("--index-dir", default=str(ROOT / "data" / "indexes"))
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N workflow files.")
    args = parser.parse_args()

    clone_dir = Path(args.clone_dir)
    if not args.skip_clone:
        clone_or_update_repo(clone_dir, args.repo_url)

    workflows_root = clone_dir / "workflows"
    if not workflows_root.is_dir():
        print(f"No workflows/ directory found at {workflows_root}")
        return 1

    chunks, failures = build_workflow_example_chunks(workflows_root, limit=args.limit)
    write_jsonl(args.output, [schema_to_dict(chunk) for chunk in chunks])

    store = JsonVectorStore(args.index_dir)
    if args.reset:
        store.reset_collection(RAG_TARGET)
    indexed = store.add_chunks(RAG_TARGET, chunks)

    print(f"Workflow files found: {len(chunks) + len(failures)}")
    print(f"Indexed as {RAG_TARGET}: {indexed}")
    print(f"Skipped: {len(failures)}")
    for failure in failures[:5]:
        print(f"  - {failure.file_name}: {failure.reason}")
    print(f"Embedding provider: {store.embedding_provider.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
