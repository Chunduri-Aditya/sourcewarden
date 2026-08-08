#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.chunker import chunk_statistics
from src.schema import Chunk
from src.source_registry import SourceRegistry
from src.utils import read_jsonl


EXPECTED_COVERAGE = {
    "workflows": ["workflow"],
    "executions": ["execution"],
    "credentials": ["credential", "oauth", "api key"],
    "expressions": ["expression"],
    "data structure": ["data structure"],
    "item linking": ["item linking", "link data"],
    "error handling": ["error"],
    "sub-workflows": ["sub workflow", "sub-workflow"],
    "scheduling": ["schedule"],
    "waiting": ["wait"],
    "conditionals": ["if", "switch", "conditional"],
    "looping": ["loop"],
    "workflow json": ["json", "export", "import"],
    "ai agent": ["ai agent"],
    "rag/vector stores": ["rag", "vector store", "pinecone", "supabase", "qdrant", "redis"],
    "deployment": ["docker", "environment", "queue mode", "security"],
}


def main() -> int:
    registry = SourceRegistry(ROOT / "config" / "sources.yaml")
    sources = registry.load_sources(enabled_only=True)
    duplicates = registry.duplicate_urls(enabled_only=True)
    raw_docs = list((ROOT / "data" / "raw").glob("*.html")) + list((ROOT / "data" / "raw").glob("*.md"))
    processed_docs = list((ROOT / "data" / "processed").glob("*.md"))
    chunk_rows = read_jsonl(ROOT / "data" / "processed" / "chunks.jsonl")
    chunks = [Chunk.model_validate(row) for row in chunk_rows]
    chunk_stats = chunk_statistics(chunks)
    indexes = list((ROOT / "data" / "indexes").glob("*.jsonl"))
    failures = read_jsonl(ROOT / "data" / "raw" / "source_failures.jsonl")

    print("n8n RAG System Quality Report")
    print("=" * 34)
    print(f"source count: {len(sources)}")
    print(f"duplicate source URLs: {len(duplicates)}")
    print(f"source failures: {len(failures)}")
    print(f"raw docs count: {len(raw_docs)}")
    print(f"processed docs count: {len(processed_docs)}")
    print(f"chunk count: {chunk_stats['total_chunks']}")
    print("chunks per RAG:")
    for rag_name, count in sorted(chunk_stats["chunks_per_rag"].items()):
        print(f"  - {rag_name}: {count}")
    print(f"average chunk tokens: {chunk_stats['average_tokens']}")
    print(f"min/max chunk tokens: {chunk_stats['min_tokens']}/{chunk_stats['max_tokens']}")
    print(f"empty chunks: {chunk_stats['empty_chunks']}")
    print(f"duplicate chunks: {chunk_stats['duplicate_chunks']}")
    print(f"index count: {len(indexes)}")

    eval_summary = run_command([sys.executable, "scripts/06_evaluate_rag.py"])
    print(f"eval status: {eval_summary['status']}")
    if eval_summary["summary"]:
        print(f"eval pass rate: {eval_summary['summary']}")
    tests_summary = run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests"])
    print(f"tests status: {tests_summary['status']}")

    missing = missing_categories(sources)
    print("top missing categories:")
    if missing:
        for item in missing[:8]:
            print(f"  - {item}")
    else:
        print("  - none detected from configured source titles and URLs")

    print("recommendations:")
    recommendations = build_recommendations(
        sources_count=len(sources),
        chunk_count=chunk_stats["total_chunks"],
        duplicates=len(duplicates),
        failures=len(failures),
        index_count=len(indexes),
        missing=missing,
    )
    for recommendation in recommendations:
        print(f"  - {recommendation}")
    return 0


def missing_categories(sources: list[object]) -> list[str]:
    searchable = "\n".join(
        f"{getattr(source, 'title', '')} {getattr(source, 'url', '')} {getattr(source, 'category', '')}"
        for source in sources
    ).lower()
    missing: list[str] = []
    for category, terms in EXPECTED_COVERAGE.items():
        if not any(term in searchable for term in terms):
            missing.append(category)
    return missing


def build_recommendations(
    sources_count: int,
    chunk_count: int,
    duplicates: int,
    failures: int,
    index_count: int,
    missing: list[str],
) -> list[str]:
    recommendations: list[str] = []
    if sources_count < 75:
        recommendations.append("Add more official n8n docs sources before production use.")
    if chunk_count < 150:
        recommendations.append("Run collection, cleaning, chunking, and indexing after expanding sources.")
    if duplicates:
        recommendations.append("Remove or intentionally route duplicate source URLs.")
    if failures:
        recommendations.append("Retry failed sources with a higher timeout or inspect source_failures.jsonl.")
    if index_count < 5:
        recommendations.append("Build all five RAG indexes with scripts/04_build_indexes.py --reset.")
    if missing:
        recommendations.append("Add sources for missing categories shown above.")
    if not recommendations:
        recommendations.append("Coverage and local quality gates look ready for deeper answer-quality review.")
    return recommendations


def run_command(command: list[str]) -> dict[str, str]:
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
        )
    except Exception as exc:
        return {"status": f"failed to run: {exc}", "summary": ""}
    output = (completed.stdout or "") + "\n" + (completed.stderr or "")
    summary = extract_summary(output)
    status = "passed" if completed.returncode == 0 else f"failed ({completed.returncode})"
    return {"status": status, "summary": summary}


def extract_summary(output: str) -> str:
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith('"questions"') or stripped.startswith('"passed"') or stripped.startswith('"failed"'):
            continue
    try:
        start = output.index("{")
        end = output.index("}", start) + 1
        data = json.loads(output[start:end])
        if "questions" in data:
            return f"{data.get('passed', 0)}/{data.get('questions', 0)} passed"
    except Exception:
        pass
    if "OK" in output:
        return "unittest OK"
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
