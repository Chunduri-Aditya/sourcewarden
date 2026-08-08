from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from .prompt_builder import REQUIRED_WORKFLOW_SECTIONS
from .schema import WorkflowInstructionResponse, schema_to_dict
from .workflow_instruction_generator import analyze_planning_intent


DEFAULT_FORBIDDEN_VAGUE_PHRASES = [
    "configure the node",
    "map fields",
    "connect the api",
    "test it",
    "as needed",
    "etc.",
    "do the setup",
    "set up the integration",
]


@dataclass
class QualityResult:
    case_name: str
    score: float
    passed_checks: list[str] = field(default_factory=list)
    failed_checks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_name": self.case_name,
            "score": round(self.score, 4),
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
        }


def score_response(
    response: WorkflowInstructionResponse | dict[str, Any],
    case: dict[str, Any],
) -> QualityResult:
    data = schema_to_dict(response)
    content = data.get("content", "")
    sections = data.get("sections", {})
    sources = data.get("sources", [])
    case_name = case.get("name") or case.get("question", "case")[:80]
    required_sections = case.get("required_sections") or REQUIRED_WORKFLOW_SECTIONS
    required_nodes = case.get("required_nodes") or []
    required_keywords = case.get("required_keywords") or []
    forbidden_phrases = case.get("forbidden_vague_phrases") or []
    forbidden_phrases = list(forbidden_phrases) + DEFAULT_FORBIDDEN_VAGUE_PHRASES
    must_cite_sources = bool(case.get("must_cite_sources", False))
    expression_expected = expects_expressions(case)

    checks: list[tuple[str, bool]] = []
    checks.append(("required_sections_present", all(f"# {section}" in content for section in required_sections)))
    checks.append(("required_nodes_mentioned", all(node.lower() in content.lower() for node in required_nodes)))
    checks.append(("required_keywords_present", all(keyword.lower() in content.lower() for keyword in required_keywords)))
    checks.append(("credentials_included", "credential" in sections.get("Credentials Needed", "").lower()))
    checks.append(("data_mapping_included", has_concrete_mapping(sections.get("Data Mapping", ""))))
    checks.append(("expressions_included_when_expected", (not expression_expected) or has_expression(content)))
    checks.append(("error_handling_included", bool(sections.get("Error Handling", "").strip()) and "error" in sections.get("Error Handling", "").lower()))
    checks.append(("test_steps_included", has_numbered_step(sections.get("Test Steps", ""))))
    checks.append(("sources_cited", (not must_cite_sources) or has_citations(sections.get("Sources Used", ""), sources)))
    checks.append(("facts_separated_from_assumptions", facts_assumptions_separated(sections)))
    checks.append(("forbidden_vague_phrases_absent", not forbidden_hits(content, forbidden_phrases)))
    checks.extend(planning_role_checks(content, sections, case))

    passed = [name for name, ok in checks if ok]
    failed = [name for name, ok in checks if not ok]
    score = len(passed) / len(checks) if checks else 0.0
    hits = forbidden_hits(content, forbidden_phrases)
    if hits:
        failed.extend([f"forbidden_phrase:{phrase}" for phrase in hits])
    return QualityResult(case_name=case_name, score=score, passed_checks=passed, failed_checks=failed)


def summarize_quality(results: list[QualityResult]) -> dict[str, Any]:
    average = sum(result.score for result in results) / len(results) if results else 0.0
    failures = Counter()
    for result in results:
        for check in result.failed_checks:
            failures[check.split(":", 1)[0]] += 1
    weakest = failures.most_common(8)
    return {
        "case_count": len(results),
        "average_score": round(average, 4),
        "weakest_categories": [{"check": check, "failures": count} for check, count in weakest],
        "recommendations": recommendations_from_failures(failures),
    }


def recommendations_from_failures(failures: Counter[str]) -> list[str]:
    recommendations: list[str] = []
    if failures.get("required_nodes_mentioned"):
        recommendations.append("Improve node inference for complex workflow patterns.")
    if failures.get("data_mapping_included"):
        recommendations.append("Add source-field to destination-field mapping examples for more task types.")
    if failures.get("expressions_included_when_expected"):
        recommendations.append("Add concrete n8n expressions when the task needs data mapping or conditions.")
    if failures.get("sources_cited"):
        recommendations.append("Inspect retrieval and ensure citations are included in generated answers.")
    if failures.get("forbidden_vague_phrases_absent") or failures.get("forbidden_phrase"):
        recommendations.append("Replace vague wording with exact settings, mappings, test actions, and expected results.")
    if failures.get("chatbot_email_forbids_gmail_trigger"):
        recommendations.append("Keep incoming-email triggers separate from email-send actions for chatbot workflows.")
    if failures.get("rag_document_chatbot_uses_chat_trigger") or failures.get("rag_document_chatbot_recommends_split"):
        recommendations.append("Split uploaded-document RAG chatbots into document ingestion and chat/query workflows.")
    if failures.get("approval_before_email_action"):
        recommendations.append("Place the human approval gate before the email-send action.")
    if not recommendations:
        recommendations.append("Adversarial answer quality checks are passing; inspect lowest-scoring cases manually next.")
    return recommendations


def planning_role_checks(
    content: str,
    sections: dict[str, str],
    case: dict[str, Any],
) -> list[tuple[str, bool]]:
    question = case.get("question", "")
    analysis = analyze_planning_intent(question)
    nodes_text = sections.get("Nodes To Add", "")
    trigger_text = sections.get("Trigger", "")
    checks: list[tuple[str, bool]] = []
    if analysis.has_chatbot_intent and analysis.has_email_action and not analysis.has_incoming_gmail_trigger:
        checks.append(("chatbot_email_forbids_gmail_trigger", "Gmail Trigger" not in content))
    if analysis.detected_start_event == "webhook" and analysis.has_email_action:
        checks.append(("webhook_email_uses_webhook_trigger", "Webhook Trigger" in trigger_text or "Webhook Trigger" in nodes_text))
        checks.append(("webhook_email_has_email_action", has_email_action_node(nodes_text)))
        checks.append(("webhook_email_forbids_gmail_trigger", "Gmail Trigger" not in content))
    if analysis.recommended_workflow_split != "none":
        checks.append(("rag_document_chatbot_uses_chat_trigger", "Chat Trigger" in trigger_text or "Chat Trigger" in nodes_text))
        checks.append(("rag_document_chatbot_recommends_split", has_two_workflow_split(content)))
    if analysis.has_human_approval and analysis.has_email_action:
        checks.append(("approval_before_email_action", approval_before_email(nodes_text)))
    return checks


def expects_expressions(case: dict[str, Any]) -> bool:
    text = " ".join(
        [
            case.get("question", ""),
            " ".join(case.get("required_keywords", [])),
            " ".join(case.get("required_nodes", [])),
        ]
    ).lower()
    return any(term in text for term in ["expression", "mapping", "map", "if", "switch", "approval", "validation", "webhook", "api"])


def has_expression(text: str) -> bool:
    return "{{$json" in text or "$json." in text or "$binary" in text


def has_concrete_mapping(text: str) -> bool:
    return "->" in text or "→" in text


def has_numbered_step(text: str) -> bool:
    return bool(re.search(r"(?m)^\d+\.\s+", text))


def has_citations(sources_text: str, sources: list[dict[str, Any]]) -> bool:
    if sources and any(source.get("url") for source in sources):
        return True
    return "http" in sources_text.lower()


def has_email_action_node(text: str) -> bool:
    return any(term in text for term in ["Node Name: Email Send", "Node Name: Send Email", "Node Name: Gmail"])


def has_two_workflow_split(text: str) -> bool:
    lowered = text.lower()
    return ("workflow a" in lowered and "workflow b" in lowered) or (
        "document ingestion workflow" in lowered and "rag chatbot" in lowered
    )


def approval_before_email(nodes_text: str) -> bool:
    lowered = nodes_text.lower()
    approval_positions = [pos for pos in [lowered.find("node name: if"), lowered.find("role: approval_gate"), lowered.find("approval")] if pos >= 0]
    email_positions = [pos for pos in [lowered.find("node name: email send"), lowered.find("node name: send email"), lowered.find("node name: gmail")] if pos >= 0]
    return bool(approval_positions and email_positions and min(approval_positions) < min(email_positions))


def facts_assumptions_separated(sections: dict[str, str]) -> bool:
    return bool(sections.get("Source-Grounded Facts", "").strip()) and bool(sections.get("Assumptions", "").strip())


def forbidden_hits(content: str, phrases: list[str]) -> list[str]:
    lowered = content.lower()
    hits: list[str] = []
    for phrase in phrases:
        if not phrase:
            continue
        phrase_lower = phrase.lower()
        if re.search(r"[a-z0-9]", phrase_lower):
            pattern = r"\b" + re.escape(phrase_lower) + r"\b"
            found = re.search(pattern, lowered) is not None
        else:
            found = phrase_lower in lowered
        if found:
            hits.append(phrase)
    return sorted(set(hits))
