from __future__ import annotations

from typing import Any

from .retriever import RagRetriever
from .schema import schema_to_dict


AUTHORITY_ORDER = [
    {
        "rank": 1,
        "source": "live_n8n_schema",
        "use": "Exact node types, versions, parameters, resources, and validation",
    },
    {
        "rank": 2,
        "source": "official_n8n_documentation",
        "use": "Documented behavior, concepts, configuration guidance, and constraints",
    },
    {
        "rank": 3,
        "source": "community_workflow_example",
        "use": "Candidate patterns and node combinations that still require verification",
    },
    {
        "rank": 4,
        "source": "course_reference",
        "use": "Untrusted background material that never overrides current evidence",
    },
]


def build_planning_context(
    query: str,
    top_k: int = 5,
    max_chars_per_evidence: int = 4000,
    retriever: RagRetriever | None = None,
) -> dict[str, Any]:
    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("query cannot be empty")
    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    if max_chars_per_evidence < 1:
        raise ValueError("max_chars_per_evidence must be at least 1")

    active_retriever = retriever or RagRetriever()
    decision, chunks = active_retriever.retrieve_with_decision(
        normalized_query,
        top_k=top_k,
    )
    bounded_chunks = chunks[:top_k]
    evidence = []
    for position, chunk in enumerate(bounded_chunks, start=1):
        data = schema_to_dict(chunk)
        rag_name = data.get("rag_name", "")
        full_text = data.get("text", "")
        truncated = len(full_text) > max_chars_per_evidence
        text = full_text[:max_chars_per_evidence].rstrip()
        if truncated:
            text += "..."
        evidence.append(
            {
                "citation_id": position,
                "authority": (
                    "community_workflow_example"
                    if rag_name == "n8n_workflow_examples_rag"
                    else "official_n8n_documentation"
                ),
                "rag_name": rag_name,
                "title": data.get("source_title", ""),
                "url": data.get("source_url", ""),
                "heading_path": data.get("heading_path") or [],
                "text": text,
                "truncated": truncated,
                "relevance_score": data.get("relevance_score", 0.0),
            }
        )

    return {
        "status": "ready" if evidence else "no_retrieved_evidence",
        "query": normalized_query,
        "authority_order": AUTHORITY_ORDER,
        "retrieval": {
            "selected_rags": decision.selected_rags,
            "reason": decision.reason,
            "rewritten_queries": decision.rewritten_queries,
            "top_k": top_k,
            "max_chars_per_evidence": max_chars_per_evidence,
        },
        "evidence": evidence,
        "planning_rule": (
            "Use retrieved evidence for source-grounded planning. Confirm every exact node "
            "parameter against the target n8n instance before creating or editing a workflow."
        ),
    }
