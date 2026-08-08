#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.document_loader import DocumentLoader
from src.source_registry import SourceRegistry


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect configured n8n documentation sources.")
    parser.add_argument("--config", default=str(ROOT / "config" / "sources.yaml"))
    parser.add_argument("--raw-dir", default=str(ROOT / "data" / "raw"))
    parser.add_argument("--force", action="store_true", help="Download even when local files already exist.")
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N enabled sources.")
    parser.add_argument("--only-rag", default=None, help="Only collect sources for this RAG target.")
    parser.add_argument("--only-category", default=None, help="Only collect sources in this source category.")
    parser.add_argument("--dry-run", action="store_true", help="Show the sources that would be collected.")
    parser.add_argument("--timeout", type=int, default=25)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--user-agent", default="n8n-rag-system/0.2 (+local official docs ingestion)")
    args = parser.parse_args()

    registry = SourceRegistry(args.config)
    sources = registry.load_sources(enabled_only=True)
    duplicates = registry.duplicate_urls(enabled_only=True)
    if duplicates:
        print("Duplicate source URLs detected:")
        for url, duplicate_sources in sorted(duplicates.items()):
            titles = ", ".join(f"{source.category}/{source.title}" for source in duplicate_sources)
            print(f"- {url}: {titles}")
        print()

    if args.only_rag:
        sources = [source for source in sources if source.rag_target == args.only_rag]
    if args.only_category:
        sources = [source for source in sources if source.category == args.only_category]
    if args.limit:
        sources = sources[: args.limit]

    loader = DocumentLoader(args.raw_dir)
    results = loader.fetch_all(
        sources,
        force=args.force,
        timeout=args.timeout,
        retries=args.retries,
        user_agent=args.user_agent,
        dry_run=args.dry_run,
    )
    counts = Counter(result.status for result in results)

    print(f"Sources configured: {len(sources)}")
    for status, count in sorted(counts.items()):
        print(f"{status}: {count}")
    print(f"Status report: {loader.status_report_path}")

    failures = [result for result in results if result.status == "failed"]
    if failures:
        print("\nFailed sources:")
        for result in failures:
            print(f"- {result.source_title}: {result.error}")
        print(f"\nFailure log: {loader.failure_log_path}")
        print("\nCollection failed gracefully. You can rerun when internet access is available.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
