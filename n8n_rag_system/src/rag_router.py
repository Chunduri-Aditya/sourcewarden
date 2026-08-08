from __future__ import annotations

import re

from .schema import RouterDecision
from .utils import unique_preserve_order


RAG_PURPOSES = {
    "n8n_core_docs_rag": "n8n basics, workflows, credentials, expressions, executions, and debugging",
    "n8n_nodes_rag": "node types, node settings, app nodes, HTTP Request, Webhook, Code, and file extraction",
    "n8n_ai_agents_rag": "AI Agent, RAG, vector stores, LangChain concepts, memory, and human fallback",
    "n8n_workflow_json_rag": "workflow JSON, export/import, workflow templates, and reusable blueprints",
    "n8n_beginner_instruction_rag": "simple English explanations, common mistakes, test steps, and checklists",
}

INTENT_RULES = {
    "beginner_explanation": [
        "beginner",
        "simple",
        "explain",
        "like i am five",
        "eli5",
        "recipe",
        "checklist",
        "step by step",
        "how do i",
    ],
    "workflow_build_plan": [
        "build",
        "make",
        "create",
        "workflow",
        "automation",
        "automate",
        "send",
        "save",
        "update",
        "sync",
        "alert",
    ],
    "node_selection": [
        "node",
        "which node",
        "what node",
        "manual trigger",
        "schedule trigger",
        "set",
        "edit fields",
        "if",
        "switch",
        "merge",
        "split",
        "loop",
        "wait",
        "code",
        "file",
        "binary",
        "n8n node",
        "execute sub",
        "sub-workflow",
        "sub workflow",
        "gmail",
        "slack",
        "google sheets",
        "sheets",
        "notion",
    ],
    "api_webhook": ["api", "rest", "http", "webhook", "respond to webhook", "endpoint", "headers"],
    "ai_agent": [
        "ai",
        "agent",
        "chatbot",
        "chat bot",
        "llm",
        "prompt",
        "chain",
        "summarize",
        "summarizes",
        "summarization",
        "summary",
        "extract",
        "extracts",
        "extraction",
        "invoice",
        "invoices",
        "classify",
        "classifies",
        "classifier",
        "classification",
        "sentiment",
        "fallback",
        "human",
        "approval",
        "approve",
    ],
    "rag_vector_store": [
        "rag",
        "vector",
        "vector store",
        "pinecone",
        "supabase",
        "qdrant",
        "redis",
        "embedding",
        "retriever",
        "documents",
        "document retrieval",
        "pdf",
        "website content",
        "knowledge base",
        "memory",
    ],
    "workflow_json_import_export": ["workflow json", "json", "export", "import", "blueprint", "template", "templates"],
    "credentials_auth": [
        "credential",
        "credentials",
        "auth",
        "authentication",
        "oauth",
        "oauth2",
        "api key",
        "bearer",
        "token",
        "secret",
    ],
    "debugging_error_handling": [
        "debug",
        "failed",
        "failure",
        "error",
        "retry",
        "execution",
        "troubleshoot",
        "stop and error",
        "error trigger",
    ],
    "deployment_self_hosting": [
        "deploy",
        "deployment",
        "self-host",
        "self hosted",
        "docker",
        "environment variable",
        "env var",
        "queue mode",
        "security",
        "ssl",
        "cloud",
    ],
}


class RagRouter:
    def route(self, query: str, top_k: int = 5) -> RouterDecision:
        lowered = query.lower()
        selected: list[str] = []
        reasons: list[str] = []
        intents = detect_intents(query)

        if "workflow_json_import_export" in intents:
            selected.extend(["n8n_workflow_json_rag", "n8n_nodes_rag", "n8n_core_docs_rag"])
            reasons.append("workflow JSON, export/import, or blueprint language was detected")

        if "ai_agent" in intents:
            selected.extend(["n8n_ai_agents_rag", "n8n_nodes_rag"])
            reasons.append("AI agent, LLM, extraction, summarization, classification, or human approval language was detected")
            if "chatbot" in lowered or "chat bot" in lowered or "workflow_build_plan" in intents:
                selected.extend(["n8n_core_docs_rag", "n8n_nodes_rag"])

        if "rag_vector_store" in intents:
            selected.extend(["n8n_ai_agents_rag", "n8n_nodes_rag", "n8n_workflow_json_rag"])
            reasons.append("RAG, vector store, embedding, retriever, memory, or document search language was detected")

        if "node_selection" in intents:
            selected.extend(["n8n_nodes_rag", "n8n_core_docs_rag"])
            reasons.append("node selection or app integration language was detected")

        if "api_webhook" in intents:
            selected.extend(["n8n_nodes_rag", "n8n_core_docs_rag"])
            reasons.append("API, HTTP, webhook, endpoint, or header language was detected")

        if "credentials_auth" in intents:
            selected.extend(["n8n_core_docs_rag", "n8n_nodes_rag"])
            reasons.append("credential, auth, OAuth, token, or API key language was detected")

        if "debugging_error_handling" in intents:
            selected.extend(["n8n_core_docs_rag", "n8n_nodes_rag"])
            reasons.append("debugging, failed execution, retry, or error handling language was detected")

        if "deployment_self_hosting" in intents:
            selected.extend(["n8n_core_docs_rag", "n8n_workflow_json_rag"])
            reasons.append("deployment, self-hosting, Docker, environment variable, queue mode, or security language was detected")

        if "workflow_build_plan" in intents:
            selected.extend(["n8n_workflow_json_rag", "n8n_nodes_rag", "n8n_core_docs_rag", "n8n_beginner_instruction_rag"])
            if "ai_agent" in intents or "rag_vector_store" in intents:
                selected.append("n8n_ai_agents_rag")
            if _has_any(lowered, ["json", "template", "blueprint", "import", "export", "webhook", "api", "form", "notion", "sheets", "slack", "gmail"]):
                selected.extend(["n8n_nodes_rag", "n8n_workflow_json_rag"])
            reasons.append("workflow build-plan language was detected")

        if "beginner_explanation" in intents:
            selected.extend(["n8n_beginner_instruction_rag", "n8n_core_docs_rag"])
            reasons.append("beginner or simple-explanation language was detected")

        if not selected:
            selected.extend(["n8n_core_docs_rag", "n8n_nodes_rag", "n8n_beginner_instruction_rag"])
            reasons.append("defaulted to core, node, and beginner RAGs")

        selected = _order_rags(unique_preserve_order(selected))
        rewritten_queries = {
            rag_name: f"{query}\nFocus on: {RAG_PURPOSES[rag_name]}."
            for rag_name in selected
        }
        for rag_name in selected:
            rewritten_queries[f"{rag_name}:settings"] = (
                f"{query}\nFind exact n8n node settings, parameters, credentials, expressions, and common mistakes."
            )
            rewritten_queries[f"{rag_name}:testing"] = (
                f"{query}\nFind testing, debugging, error handling, and validation guidance."
            )
        return RouterDecision(
            selected_rags=selected,
            rewritten_queries=rewritten_queries,
            reason="; ".join(reasons),
            retrieval_parameters={
                "top_k_per_rag": top_k,
                "metadata_filters": {},
                "priority_boost": True,
                "keyword_fallback": True,
                "reranker": "optional_stub",
                "intents": intents,
            },
        )


def _has_any(text: str, terms: list[str]) -> bool:
    for term in terms:
        if " " in term:
            if term in text:
                return True
            continue
        if re.search(rf"\b{re.escape(term)}\b", text):
            return True
    return False


def detect_intents(query: str) -> list[str]:
    lowered = query.lower()
    intents = [
        intent
        for intent, terms in INTENT_RULES.items()
        if _has_any(lowered, terms)
    ]
    if "workflow" in lowered and "workflow_build_plan" not in intents:
        intents.append("workflow_build_plan")
    if "rag_vector_store" in intents and "ai_agent" not in intents:
        intents.append("ai_agent")
    return unique_preserve_order(intents)


def _order_rags(rags: list[str]) -> list[str]:
    order = [
        "n8n_ai_agents_rag",
        "n8n_workflow_json_rag",
        "n8n_nodes_rag",
        "n8n_beginner_instruction_rag",
        "n8n_core_docs_rag",
    ]
    if "n8n_workflow_json_rag" in rags and "n8n_ai_agents_rag" not in rags:
        order = [
            "n8n_workflow_json_rag",
            "n8n_nodes_rag",
            "n8n_core_docs_rag",
            "n8n_beginner_instruction_rag",
        ]
    if "n8n_ai_agents_rag" in rags and "n8n_workflow_json_rag" not in rags:
        order = [
            "n8n_ai_agents_rag",
            "n8n_core_docs_rag",
            "n8n_nodes_rag",
            "n8n_beginner_instruction_rag",
        ]
    return [rag for rag in order if rag in rags]
