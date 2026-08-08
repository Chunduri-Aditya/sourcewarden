from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

from .embeddings import EmbeddingProvider, build_embedding_provider
from .schema import Chunk, RetrievedChunk, schema_to_dict
from .utils import ensure_dir, read_jsonl, stable_id, write_jsonl


class JsonVectorStore:
    """Simple persistent local vector store with one JSONL file per RAG collection."""

    def __init__(
        self,
        index_dir: str | Path,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        self.index_dir = ensure_dir(index_dir)
        self.embedding_provider = embedding_provider or build_embedding_provider()

    def collection_path(self, collection_name: str) -> Path:
        return self.index_dir / f"{collection_name}.jsonl"

    def reset_collection(self, collection_name: str) -> None:
        path = self.collection_path(collection_name)
        if path.exists():
            path.unlink()

    def add_chunks(self, collection_name: str, chunks: list[Chunk | dict[str, Any]]) -> int:
        if not chunks:
            return 0
        rows = []
        texts = [schema_to_dict(chunk)["text"] for chunk in chunks]
        embeddings = self.embedding_provider.embed_texts(texts)
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            data = schema_to_dict(chunk)
            chunk_id = data.get("chunk_id") or stable_id(collection_name, data["text"][:120])
            metadata = {
                key: value
                for key, value in data.items()
                if key not in {"text", "metadata"}
            }
            metadata.update(data.get("metadata") or {})
            rows.append(
                {
                    "id": chunk_id,
                    "text": data["text"],
                    "embedding": embedding,
                    "metadata": metadata,
                }
            )
        existing = read_jsonl(self.collection_path(collection_name))
        write_jsonl(self.collection_path(collection_name), existing + rows)
        return len(rows)

    def query(
        self,
        collection_name: str,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedChunk]:
        records = read_jsonl(self.collection_path(collection_name))
        if not records:
            return []
        query_embedding = self.embedding_provider.embed_query(query)
        scored: list[RetrievedChunk] = []
        for record in records:
            metadata = record.get("metadata", {})
            if filters and not _matches_filters(metadata, filters):
                continue
            vector_score = cosine_similarity(query_embedding, record.get("embedding", []))
            keyword_score = lexical_overlap(query, record.get("text", ""))
            heading_score = lexical_overlap(query, " ".join(metadata.get("heading_path") or []))
            priority_score = {"high": 0.15, "medium": 0.07, "low": 0.0}.get(
                str(metadata.get("priority", "medium")), 0.0
            )
            final_score = vector_score + (0.25 * keyword_score) + (0.15 * heading_score) + priority_score
            scored.append(
                RetrievedChunk(
                    text=record.get("text", ""),
                    source_title=metadata.get("source_title", ""),
                    source_url=metadata.get("source_url", ""),
                    heading_path=metadata.get("heading_path") or [],
                    relevance_score=round(float(final_score), 6),
                    rag_name=collection_name,
                    chunk_id=record.get("id"),
                    priority=metadata.get("priority", "medium"),
                )
            )
        scored.sort(key=lambda item: item.relevance_score, reverse=True)
        return scored[:top_k]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    length = min(len(left), len(right))
    dot = sum(left[i] * right[i] for i in range(length))
    left_norm = math.sqrt(sum(value * value for value in left[:length]))
    right_norm = math.sqrt(sum(value * value for value in right[:length]))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def lexical_overlap(query: str, text: str) -> float:
    query_terms = set(re.findall(r"[a-z0-9_]+", query.lower()))
    text_terms = set(re.findall(r"[a-z0-9_]+", text.lower()))
    if not query_terms or not text_terms:
        return 0.0
    return len(query_terms & text_terms) / len(query_terms)


def _matches_filters(metadata: dict[str, Any], filters: dict[str, Any]) -> bool:
    for key, expected in filters.items():
        actual = metadata.get(key)
        if isinstance(expected, (list, tuple, set)):
            if actual not in expected:
                return False
        elif actual != expected:
            return False
    return True
