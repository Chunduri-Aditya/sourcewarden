from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from .embeddings import EmbeddingProvider
from .rag_router import RagRouter
from .reranker import Reranker
from .schema import RetrievedChunk, RouterDecision
from .utils import PROJECT_ROOT
from .vector_store import JsonVectorStore


class RagRetriever:
    def __init__(
        self,
        index_dir: str | Path | None = None,
        embedding_provider: EmbeddingProvider | None = None,
        router: RagRouter | None = None,
        vector_store: JsonVectorStore | None = None,
        reranker: Reranker | None = None,
    ) -> None:
        self.router = router or RagRouter()
        self.vector_store = vector_store or JsonVectorStore(
            index_dir or PROJECT_ROOT / "data" / "indexes",
            embedding_provider=embedding_provider,
        )
        self.reranker = reranker or Reranker()

    def retrieve_with_decision(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> tuple[RouterDecision, list[RetrievedChunk]]:
        decision = self.router.route(query, top_k=top_k)
        chunks = self.retrieve(
            query=query,
            top_k=top_k,
            filters=filters,
            decision=decision,
        )
        return decision, chunks

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
        decision: RouterDecision | None = None,
        selected_rags: list[str] | None = None,
    ) -> list[RetrievedChunk]:
        decision = decision or self.router.route(query, top_k=top_k)
        rag_names = selected_rags or decision.selected_rags
        results: list[RetrievedChunk] = []
        per_rag_top_k = int(decision.retrieval_parameters.get("top_k_per_rag", top_k))
        for rag_name in rag_names:
            rag_queries = [
                value
                for key, value in decision.rewritten_queries.items()
                if key == rag_name or key.startswith(f"{rag_name}:")
            ]
            if query not in rag_queries:
                rag_queries.append(query)
            for rag_query in rag_queries:
                results.extend(
                    self.vector_store.query(
                        collection_name=rag_name,
                        query=rag_query,
                        top_k=per_rag_top_k,
                        filters=filters,
                    )
                )
        deduped = deduplicate_chunks(results)
        reranked = self.reranker.rerank(query, deduped)
        return ensure_citation_metadata(reranked)


def deduplicate_chunks(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    by_key: dict[str, RetrievedChunk] = {}
    for chunk in chunks:
        key = chunk.chunk_id or normalize_chunk_text(chunk.text)
        existing = by_key.get(key)
        if existing is None or chunk.relevance_score > existing.relevance_score:
            by_key[key] = chunk
    near_seen: set[str] = set()
    deduped: list[RetrievedChunk] = []
    for chunk in sorted(by_key.values(), key=lambda item: item.relevance_score, reverse=True):
        near_key = normalize_chunk_text(chunk.text)[:600]
        if near_key in near_seen:
            continue
        near_seen.add(near_key)
        deduped.append(chunk)
    return deduped


def normalize_chunk_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def ensure_citation_metadata(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    valid: list[RetrievedChunk] = []
    for chunk in chunks:
        if not chunk.source_title:
            chunk.source_title = "Unknown source"
        if chunk.heading_path is None:
            chunk.heading_path = []
        if chunk.source_url is None:
            chunk.source_url = ""
        valid.append(chunk)
    return valid
