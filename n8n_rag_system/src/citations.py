from __future__ import annotations

from typing import Any

from .schema import RetrievedChunk, schema_to_dict


def unique_sources(chunks: list[RetrievedChunk | dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    sources: list[dict[str, Any]] = []
    for chunk in chunks:
        data = schema_to_dict(chunk)
        heading_path = data.get("heading_path") or []
        heading_text = " > ".join(heading_path)
        key = (data.get("source_title", ""), data.get("source_url", ""), heading_text)
        if key in seen:
            continue
        seen.add(key)
        sources.append(
            {
                "title": data.get("source_title", ""),
                "url": data.get("source_url", ""),
                "heading_path": heading_path,
            }
        )
    return sources


def format_sources(chunks: list[RetrievedChunk | dict[str, Any]]) -> str:
    sources = unique_sources(chunks)
    if not sources:
        return "- No retrieved sources available. Run collection, chunking, and indexing first."
    lines: list[str] = []
    for index, source in enumerate(sources, start=1):
        heading = " > ".join(source.get("heading_path") or [])
        suffix = f" - {heading}" if heading else ""
        lines.append(f"- [{index}] {source['title']}{suffix}: {source['url']}")
    return "\n".join(lines)


def format_source_grounded_facts(chunks: list[RetrievedChunk | dict[str, Any]], limit: int = 8) -> str:
    if not chunks:
        return "- No retrieved docs were available. Treat the workflow recipe as a draft and run indexing before production use."
    lines: list[str] = []
    for index, chunk in enumerate(chunks[:limit], start=1):
        data = schema_to_dict(chunk)
        first_sentence = data.get("text", "").strip().split("\n", 1)[0]
        first_sentence = first_sentence[:240].strip()
        source = data.get("source_title", "source")
        lines.append(f"- [{index}] {first_sentence} (Source: {source})")
    return "\n".join(lines)

