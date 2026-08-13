from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .schema import Chunk
from .utils import stable_id

RAG_TARGET = "n8n_workflow_examples_rag"
DEFAULT_REPO_URL = "https://github.com/Zie619/n8n-workflows.git"
BLOB_BASE_URL = "https://github.com/Zie619/n8n-workflows/blob/main"

KNOWN_TYPE_PREFIXES = (
    "@n8n/n8n-nodes-langchain.",
    "n8n-nodes-base.",
)

MAX_DISPLAYED_NODE_TYPES = 40


@dataclass
class ParseFailure:
    file_name: str
    reason: str


def clean_node_type(node_type: str) -> str:
    for prefix in KNOWN_TYPE_PREFIXES:
        if node_type.startswith(prefix):
            return node_type[len(prefix) :]
    return node_type


def is_trigger_type(node_type: str) -> bool:
    lowered = node_type.lower()
    return "trigger" in lowered or lowered.endswith("webhook")


def parse_workflow_file(path: Path, workflows_root: Path) -> tuple[Chunk | None, ParseFailure | None]:
    relative_path = path.relative_to(workflows_root).as_posix()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, ParseFailure(relative_path, str(exc))

    if not isinstance(payload, dict):
        return None, ParseFailure(relative_path, "top-level JSON is not an object")

    nodes = payload.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        return None, ParseFailure(relative_path, "no usable 'nodes' list")

    node_types: list[str] = []
    trigger_types: list[str] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        raw_type = str(node.get("type", "")).strip()
        if not raw_type:
            continue
        cleaned = clean_node_type(raw_type)
        node_types.append(cleaned)
        if is_trigger_type(raw_type):
            trigger_types.append(cleaned)

    if not node_types:
        return None, ParseFailure(relative_path, "no node had a usable 'type' field")

    fallback_name = path.stem.replace("_", " ").replace("-", " ").strip()
    name = str(payload.get("name") or fallback_name).strip() or fallback_name
    description = str(payload.get("description") or "").strip()
    unique_node_types = sorted(dict.fromkeys(node_types))
    unique_triggers = sorted(dict.fromkeys(trigger_types)) or ["manual/unspecified"]
    tags = [
        str(tag.get("name", tag)) if isinstance(tag, dict) else str(tag)
        for tag in (payload.get("tags") or [])
        if tag
    ]

    displayed_types = unique_node_types[:MAX_DISPLAYED_NODE_TYPES]
    overflow = len(unique_node_types) - len(displayed_types)
    node_list_text = ", ".join(displayed_types)
    if overflow > 0:
        node_list_text += f", and {overflow} more"

    source_url = f"{BLOB_BASE_URL}/workflows/{relative_path}"
    text_lines = [f"Workflow: {name}"]
    if description:
        text_lines.append(f"Description: {description}")
    text_lines.extend(
        [
            f"Source file: workflows/{relative_path}",
            f"Node count: {len(nodes)}",
            f"Trigger type(s): {', '.join(unique_triggers)}",
            f"Nodes used: {node_list_text}",
            f"Tags: {', '.join(tags) if tags else 'none'}",
            "This is a real community-contributed n8n workflow example from the Zie619/n8n-workflows "
            "GitHub collection. Use it as a reference pattern for similar automations, not as a "
            "guaranteed-working import.",
        ]
    )

    chunk_id = stable_id(RAG_TARGET, relative_path)
    metadata = {
        "file_name": relative_path,
        "node_count": len(nodes),
        "trigger_types": unique_triggers,
        "node_types": unique_node_types,
        "tags": tags,
    }
    chunk = Chunk(
        text="\n".join(text_lines),
        source_title=name,
        source_url=source_url,
        heading_path=unique_triggers[:1],
        doc_category="workflow_example",
        rag_target=RAG_TARGET,
        chunk_id=chunk_id,
        chunk_type="workflow_example",
        priority="medium",
        metadata=metadata,
    )
    return chunk, None


def build_workflow_example_chunks(
    workflows_root: str | Path,
    limit: int | None = None,
) -> tuple[list[Chunk], list[ParseFailure]]:
    workflows_root = Path(workflows_root)
    paths = sorted(workflows_root.rglob("*.json"))
    if limit is not None:
        paths = paths[:limit]

    chunks: list[Chunk] = []
    failures: list[ParseFailure] = []
    for path in paths:
        chunk, failure = parse_workflow_file(path, workflows_root)
        if chunk is not None:
            chunks.append(chunk)
        if failure is not None:
            failures.append(failure)
    return chunks, failures
