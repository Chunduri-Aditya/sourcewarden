from __future__ import annotations

from typing import Any

from src.planning_context import build_planning_context

import web.paths  # noqa: F401  (import side effect: puts n8n_rag_system on sys.path)


def get_planning_context(query: str, top_k: int = 5) -> dict[str, Any]:
    """Retrieve source-grounded planning context for a chat query.

    Thin wrapper over build_planning_context(): an empty/blank query never
    raises past this layer. On success the function's own `status` field
    ("ready" or "no_retrieved_evidence") is passed through verbatim so the
    template can render it directly.
    """
    try:
        return build_planning_context(query, top_k=top_k)
    except ValueError as error:
        return {
            "status": "invalid_query",
            "query": query,
            "error": str(error),
            "authority_order": [],
            "retrieval": {},
            "evidence": [],
            "planning_rule": "",
        }
