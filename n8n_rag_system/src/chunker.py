from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .schema import Chunk, schema_to_dict
from .utils import (
    approx_token_count,
    compact_blank_lines,
    ensure_dir,
    read_json,
    stable_id,
    strip_front_matter,
    write_jsonl,
)


@dataclass
class MarkdownSection:
    heading_path: list[str]
    text: str


def split_markdown_sections(markdown: str) -> list[MarkdownSection]:
    markdown = strip_front_matter(markdown)
    lines = markdown.splitlines()
    sections: list[MarkdownSection] = []
    heading_stack: list[tuple[int, str]] = []
    current_lines: list[str] = []
    current_path: list[str] = []
    in_code = False

    def flush() -> None:
        nonlocal current_lines, current_path
        text = compact_blank_lines("\n".join(current_lines))
        if text:
            sections.append(MarkdownSection(heading_path=list(current_path), text=text))
        current_lines = []

    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
        heading_match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if heading_match and not in_code:
            flush()
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            heading_stack = [(lvl, text) for lvl, text in heading_stack if lvl < level]
            heading_stack.append((level, title))
            current_path = [text for _, text in heading_stack]
            current_lines = [line]
        else:
            current_lines.append(line)
    flush()
    return sections


def iter_markdown_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    in_code = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            current.append(line)
            in_code = not in_code
            continue
        if not in_code and not line.strip():
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            continue
        current.append(line)
    if current:
        blocks.append("\n".join(current).strip())
    return [block for block in blocks if block.strip()]


def split_long_block(block: str, max_tokens: int, overlap_tokens: int) -> list[str]:
    if block.lstrip().startswith("```") or approx_token_count(block) <= max_tokens:
        return [block]
    words = re.findall(r"\S+", block)
    pieces: list[str] = []
    start = 0
    step = max(1, max_tokens - overlap_tokens)
    while start < len(words):
        piece = " ".join(words[start : start + max_tokens]).strip()
        if piece:
            pieces.append(piece)
        start += step
    return pieces


def infer_chunk_type(text: str, metadata: dict[str, Any] | None = None) -> str:
    lowered = text.lower()
    metadata = metadata or {}
    rag_target = str(metadata.get("rag_target", "")).lower()
    category = str(metadata.get("category", "")).lower()

    if "```" in text or "code node" in lowered:
        return "code_example"
    if "credential" in lowered or "api key" in lowered or "oauth" in lowered:
        return "credential_setup"
    if "troubleshoot" in lowered or "debug" in lowered or "failed execution" in lowered or "error" in lowered:
        return "troubleshooting"
    if "workflow json" in lowered or "export" in lowered or "import" in lowered or "template" in lowered:
        return "workflow_json"
    if "rag" in lowered or "retrieval" in lowered or "vector store" in lowered or "embedding" in lowered:
        return "rag"
    if "ai agent" in lowered or "langchain" in lowered or "chat trigger" in lowered or "advanced ai" in lowered:
        return "ai_agent"
    if "node" in lowered or "parameter" in lowered or "n8n_nodes" in rag_target or "node_docs" in category:
        return "node_reference"
    if re.search(r"\b(step|steps|first|then|finally)\b", lowered) or re.search(r"^\d+\.", text, re.MULTILINE):
        return "workflow_steps"
    if "beginner" in lowered or "simple" in lowered or "glossary" in lowered:
        return "beginner_explanation"
    return "concept"


def chunk_markdown(
    markdown: str,
    metadata: dict[str, Any],
    max_tokens: int = 1000,
    overlap_tokens: int = 150,
    min_tokens: int = 80,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    sections = split_markdown_sections(markdown)
    source_title = metadata.get("source_title") or metadata.get("title") or "Untitled source"
    source_url = metadata.get("source_url") or metadata.get("url") or ""
    doc_category = metadata.get("category") or metadata.get("doc_category") or ""
    rag_target = metadata.get("rag_target") or "n8n_core_docs_rag"
    priority = metadata.get("priority") or "medium"
    target_tokens = max(min_tokens, int(max_tokens * 0.65))

    pending_small: list[tuple[MarkdownSection, str]] = []

    def emit_text(section: MarkdownSection, text: str, section_index: int) -> None:
        text = compact_blank_lines(text)
        if not text:
            return
        chunk_index = len(chunks)
        chunk_id = stable_id(source_url, str(section_index), str(chunk_index), text[:120])
        chunk_type = infer_chunk_type(text, metadata)
        chunk_metadata = {
            "source_title": source_title,
            "source_url": source_url,
            "heading_path": section.heading_path,
            "doc_category": doc_category,
            "rag_target": rag_target,
            "chunk_id": chunk_id,
            "chunk_type": chunk_type,
            "priority": priority,
            "token_count": approx_token_count(text),
        }
        chunks.append(
            Chunk(
                text=text,
                source_title=source_title,
                source_url=source_url,
                heading_path=section.heading_path,
                doc_category=doc_category,
                rag_target=rag_target,
                chunk_id=chunk_id,
                chunk_type=chunk_type,
                priority=priority,
                metadata=chunk_metadata,
            )
        )

    def flush_pending(section_index: int) -> None:
        nonlocal pending_small
        if not pending_small:
            return
        first_section = pending_small[0][0]
        text = compact_blank_lines("\n\n".join(item[1] for item in pending_small))
        emit_text(first_section, text, section_index)
        pending_small = []

    for section_index, section in enumerate(sections):
        blocks: list[str] = []
        for block in iter_markdown_blocks(section.text):
            blocks.extend(split_long_block(block, max_tokens=max_tokens, overlap_tokens=overlap_tokens))

        current_blocks: list[str] = []
        current_tokens = 0

        def flush_current() -> None:
            nonlocal current_blocks, current_tokens
            text = compact_blank_lines("\n\n".join(current_blocks))
            if not text:
                current_blocks = []
                current_tokens = 0
                return
            if approx_token_count(text) < min_tokens:
                pending_small.append((section, text))
                pending_tokens = sum(approx_token_count(item[1]) for item in pending_small)
                if pending_tokens >= target_tokens:
                    flush_pending(section_index)
            else:
                if approx_token_count(text) < target_tokens:
                    pending_small.append((section, text))
                    pending_tokens = sum(approx_token_count(item[1]) for item in pending_small)
                    if pending_tokens >= target_tokens:
                        flush_pending(section_index)
                else:
                    flush_pending(section_index)
                    emit_text(section, text, section_index)
            if overlap_tokens > 0:
                words = re.findall(r"\S+", text)
                overlap = " ".join(words[-overlap_tokens:])
                current_blocks = [overlap] if overlap and approx_token_count(overlap) > 5 else []
                current_tokens = approx_token_count(overlap) if current_blocks else 0
            else:
                current_blocks = []
                current_tokens = 0

        for block in blocks:
            block_tokens = approx_token_count(block)
            if current_blocks and current_tokens + block_tokens > max_tokens:
                flush_current()
            current_blocks.append(block)
            current_tokens += block_tokens
        flush_current()

    flush_pending(len(sections))
    return [chunk for chunk in chunks if chunk.text.strip()]


def chunk_processed_file(
    processed_path: str | Path,
    max_tokens: int = 1000,
    overlap_tokens: int = 150,
    min_tokens: int = 80,
) -> list[Chunk]:
    processed_path = Path(processed_path)
    metadata_path = processed_path.with_suffix(".metadata.json")
    if not metadata_path.exists():
        metadata_path = processed_path.with_name(processed_path.stem + ".metadata.json")
    metadata = read_json(metadata_path, default={}) or {}
    markdown = processed_path.read_text(encoding="utf-8")
    return chunk_markdown(
        markdown,
        metadata=metadata,
        max_tokens=max_tokens,
        overlap_tokens=overlap_tokens,
        min_tokens=min_tokens,
    )


def chunk_all(
    processed_dir: str | Path,
    output_path: str | Path | None = None,
    max_tokens: int = 1000,
    overlap_tokens: int = 150,
    min_tokens: int = 80,
) -> list[Chunk]:
    processed_dir = Path(processed_dir)
    all_chunks: list[Chunk] = []
    for path in sorted(processed_dir.glob("*.md")):
        all_chunks.extend(
            chunk_processed_file(
                path,
                max_tokens=max_tokens,
                overlap_tokens=overlap_tokens,
                min_tokens=min_tokens,
            )
        )
    if output_path:
        ensure_dir(Path(output_path).parent)
        write_jsonl(output_path, [schema_to_dict(chunk) for chunk in all_chunks])
    return all_chunks


def chunk_statistics(chunks: list[Chunk]) -> dict[str, Any]:
    token_counts = [approx_token_count(chunk.text) for chunk in chunks]
    text_counts = Counter(compact_blank_lines(chunk.text).lower() for chunk in chunks)
    chunks_per_source: dict[str, int] = defaultdict(int)
    for chunk in chunks:
        chunks_per_source[chunk.source_title] += 1
    return {
        "total_chunks": len(chunks),
        "chunks_per_rag": dict(Counter(chunk.rag_target for chunk in chunks)),
        "chunks_per_source": dict(sorted(chunks_per_source.items())),
        "average_tokens": round(sum(token_counts) / len(token_counts), 2) if token_counts else 0,
        "min_tokens": min(token_counts) if token_counts else 0,
        "max_tokens": max(token_counts) if token_counts else 0,
        "empty_chunks": sum(1 for chunk in chunks if not chunk.text.strip()),
        "duplicate_chunks": sum(count - 1 for count in text_counts.values() if count > 1),
    }


def format_chunk_statistics(stats: dict[str, Any]) -> str:
    lines = [
        f"total chunks: {stats['total_chunks']}",
        "chunks per RAG:",
    ]
    for rag_name, count in sorted(stats["chunks_per_rag"].items()):
        lines.append(f"  - {rag_name}: {count}")
    lines.extend(
        [
            "chunks per source:",
        ]
    )
    for source_title, count in sorted(stats["chunks_per_source"].items()):
        lines.append(f"  - {source_title}: {count}")
    lines.extend(
        [
            f"average tokens: {stats['average_tokens']}",
            f"min tokens: {stats['min_tokens']}",
            f"max tokens: {stats['max_tokens']}",
            f"empty chunks: {stats['empty_chunks']}",
            f"duplicate chunks: {stats['duplicate_chunks']}",
        ]
    )
    return "\n".join(lines)
