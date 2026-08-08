from __future__ import annotations

from .schema import RetrievedChunk


class Reranker:
    """Optional reranker contract.

    A production system can replace this with a cross-encoder or LLM reranker.
    The default implementation keeps vector-store ordering unchanged.
    """

    def rerank(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        return chunks

