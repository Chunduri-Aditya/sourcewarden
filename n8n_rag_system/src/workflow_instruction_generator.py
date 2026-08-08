from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

from .citations import format_source_grounded_facts, format_sources, unique_sources
from .prompt_builder import REQUIRED_WORKFLOW_SECTIONS, PromptBuilder
from .retriever import RagRetriever
from .schema import (
    WorkflowInstructionRequest,
    WorkflowInstructionResponse,
)
from .utils import load_dotenv


NODE_ROLES = {
    "trigger",
    "action",
    "ai_agent",
    "rag_retrieval",
    "vector_storage",
    "document_ingestion",
    "approval_gate",
    "control_flow",
    "response",
    "error_handling",
}


@dataclass(frozen=True)
class PlanningAnalysis:
    detected_start_event: str
    detected_actions: list[str]
    trigger_candidates: list[str]
    forbidden_triggers: list[str]
    recommended_workflow_split: str
    has_chatbot_intent: bool
    has_incoming_gmail_trigger: bool
    has_email_action: bool
    has_human_approval: bool

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "detected_start_event": self.detected_start_event,
            "detected_actions": self.detected_actions,
            "trigger_candidates": self.trigger_candidates,
            "forbidden_triggers": self.forbidden_triggers,
            "recommended_workflow_split": self.recommended_workflow_split,
        }


class WorkflowInstructionGenerator:
    def __init__(
        self,
        retriever: RagRetriever | None = None,
        prompt_builder: PromptBuilder | None = None,
    ) -> None:
        self.retriever = retriever or RagRetriever()
        self.prompt_builder = prompt_builder or PromptBuilder()

    def generate(
        self,
        request: WorkflowInstructionRequest | dict[str, Any] | str,
        top_k: int | None = None,
    ) -> WorkflowInstructionResponse:
        load_dotenv()
        if isinstance(request, str):
            request = WorkflowInstructionRequest(user_task=request)
        elif isinstance(request, dict):
            request = WorkflowInstructionRequest.model_validate(request)

        top_k = top_k or int(os.getenv("N8N_RAG_TOP_K", "5"))
        decision, chunks = self.retriever.retrieve_with_decision(request.user_task, top_k=top_k)
        apps = infer_apps(request.user_task, request.apps_tools_available)
        nodes = infer_nodes(request.user_task)

        sections = build_sections(
            request=request,
            apps=apps,
            nodes=nodes,
            chunks=chunks,
            selected_rags=decision.selected_rags,
        )
        content = "\n\n".join(f"# {section}\n\n{sections[section]}" for section in REQUIRED_WORKFLOW_SECTIONS)
        validate_workflow_sections(
            sections,
            require_sources=bool(chunks),
            output_mode=request.output_mode,
            user_task=request.user_task,
        )
        return WorkflowInstructionResponse(
            content=content,
            sections=sections,
            sources=unique_sources(chunks),
        )

    def build_llm_prompt(
        self,
        request: WorkflowInstructionRequest | dict[str, Any] | str,
        top_k: int | None = None,
    ) -> str:
        if isinstance(request, str):
            request = WorkflowInstructionRequest(user_task=request)
        elif isinstance(request, dict):
            request = WorkflowInstructionRequest.model_validate(request)
        top_k = top_k or int(os.getenv("N8N_RAG_TOP_K", "5"))
        _, chunks = self.retriever.retrieve_with_decision(request.user_task, top_k=top_k)
        return self.prompt_builder.build(
            user_task=request.user_task,
            retrieved_chunks=chunks,
            output_mode=request.output_mode,
            apps_tools_available=request.apps_tools_available,
            skill_level=request.skill_level,
            preferred_deployment=request.preferred_deployment,
        )


def build_sections(
    request: WorkflowInstructionRequest,
    apps: list[str],
    nodes: list[dict[str, str]],
    chunks: list[Any],
    selected_rags: list[str],
) -> dict[str, str]:
    task = request.user_task
    workflow_name = make_workflow_name(task)
    needs_ai = has_ai_need(task)
    needs_rag = has_rag_need(task)
    analysis = analyze_planning_intent(task)

    sections: dict[str, str] = {
        "Workflow Name": workflow_name,
        "What This Workflow Does": (
            f"This workflow helps with this task: {task}\n\n"
            "It breaks the work into small n8n nodes so a beginner can build and test one step at a time."
        ),
        "Assumptions": "\n".join(
            [
                "- You have access to an n8n workspace.",
                "- You can create credentials for every app used by the workflow.",
                "- Field names, folder names, sheet names, and channel names may need small changes in your account.",
                "- Start with a manual test before turning the workflow on.",
            ]
        ),
        "Apps / Tools Needed": "\n".join(f"- {app}" for app in apps),
        "Credentials Needed": credentials_for_apps(apps),
        "Trigger": trigger_description(nodes, analysis),
        "Nodes To Add": format_nodes(nodes),
        "Data Mapping": data_mapping_for_task(task, nodes),
        "AI Prompt, If Used": ai_prompt_for_task(task) if needs_ai else "- No AI prompt is needed unless you choose to add an AI node.",
        "Memory / RAG, If Used": rag_plan_for_task(task) if needs_rag else "- No memory or RAG setup is needed for this basic workflow.",
        "Error Handling": error_handling_plan(task, apps),
        "Test Steps": test_steps(nodes),
        "Final Checklist": final_checklist(apps, needs_ai, needs_rag),
        "Source-Grounded Facts": format_source_grounded_facts(chunks),
        "Design Decisions": design_decisions(task, nodes, selected_rags, request.output_mode),
        "Needs User Confirmation": needs_user_confirmation(task, apps),
        "Sources Used": format_sources(chunks),
    }
    return sections


def infer_apps(task: str, provided: list[str] | None = None) -> list[str]:
    lowered = task.lower()
    apps = list(provided or [])
    keyword_apps = [
        ("gmail", "Gmail"),
        ("email", "Email app"),
        ("google sheets", "Google Sheets"),
        ("sheet", "Google Sheets"),
        ("slack", "Slack"),
        ("notion", "Notion"),
        ("webhook", "Webhook caller"),
        ("form", "Form app"),
        ("api", "External API"),
        ("rest", "External API"),
        ("pdf", "PDF files"),
        ("invoice", "Invoice files"),
        ("pinecone", "Pinecone"),
        ("supabase", "Supabase"),
        ("document", "Document storage"),
        ("website", "Website content"),
        ("docker", "Docker"),
        ("environment", "Environment variables"),
        ("chatbot", "Chat interface"),
    ]
    for keyword, app in keyword_apps:
        if keyword in lowered and app not in apps:
            apps.append(app)
    if has_ai_need(task) and "AI model provider" not in apps:
        apps.append("AI model provider")
    if "n8n" not in apps:
        apps.insert(0, "n8n")
    return apps


def analyze_planning_intent(task: str) -> PlanningAnalysis:
    lowered = task.lower()
    chatbot_intent = has_chatbot_intent(task)
    incoming_gmail = has_incoming_gmail_trigger(task)
    email_action = has_email_action(task)
    human_approval = has_human_approval(task)
    webhook_start = has_webhook_start(task)
    schedule_start = has_schedule_start(task)
    error_start = "error trigger" in lowered
    split = "document_ingestion_and_rag_chatbot" if should_split_rag_document_chatbot(task) else "none"

    trigger_candidates: list[str] = []
    if error_start:
        trigger_candidates.append("Error Trigger")
    if chatbot_intent:
        trigger_candidates.append("Chat Trigger")
    if webhook_start:
        trigger_candidates.append("Webhook Trigger")
    if schedule_start:
        trigger_candidates.append("Schedule Trigger")
    if incoming_gmail:
        trigger_candidates.append("Gmail Trigger")
    if not trigger_candidates:
        trigger_candidates.append("Manual Trigger")

    if error_start:
        detected_start_event = "error"
    elif chatbot_intent:
        detected_start_event = "chat"
    elif webhook_start:
        detected_start_event = "webhook"
    elif schedule_start:
        detected_start_event = "schedule"
    elif incoming_gmail:
        detected_start_event = "gmail"
    else:
        detected_start_event = "manual"

    actions: list[str] = []
    if email_action:
        actions.append("email")
    if "slack" in lowered:
        actions.append("slack")
    if "google sheets" in lowered or "sheet" in lowered:
        actions.append("google_sheets")
    if "notion" in lowered:
        actions.append("notion")
    if has_rag_need(task):
        actions.append("rag")
    if human_approval:
        actions.append("human_approval")

    forbidden_triggers: list[str] = []
    if email_action and not incoming_gmail and (chatbot_intent or webhook_start or detected_start_event in {"chat", "webhook", "manual"}):
        forbidden_triggers.append("Gmail Trigger")

    return PlanningAnalysis(
        detected_start_event=detected_start_event,
        detected_actions=actions,
        trigger_candidates=trigger_candidates,
        forbidden_triggers=forbidden_triggers,
        recommended_workflow_split=split,
        has_chatbot_intent=chatbot_intent,
        has_incoming_gmail_trigger=incoming_gmail,
        has_email_action=email_action,
        has_human_approval=human_approval,
    )


def has_chatbot_intent(task: str) -> bool:
    lowered = task.lower()
    if "ai agent" in lowered and "tool" in lowered:
        return True
    terms = [
        "chatbot",
        "chat bot",
        "chat interface",
        "conversational",
        "ask questions",
        "answers from documents",
        "rag chatbot",
        "chat with my documents",
        "chat questions",
        "chat question",
    ]
    return contains_any_term(task, terms)


def has_incoming_gmail_trigger(task: str) -> bool:
    lowered = task.lower()
    incoming_terms = [
        "when i receive an email",
        "when i get a new email",
        "when i get a new gmail",
        "when a new email arrives",
        "new email arrives",
        "new gmail message",
        "incoming gmail",
        "incoming email",
        "unread gmail",
        "gmail attachment received",
        "new gmail invoice attachment",
        "watch gmail inbox",
        "monitor gmail inbox",
        "trigger from gmail",
        "gmail trigger",
        "new emails",
        "new email",
    ]
    if any(term in lowered for term in incoming_terms):
        return True
    return (
        "gmail" in lowered
        and ("attachment" in lowered or "invoice" in lowered)
        and any(term in lowered for term in ["receive", "received", "get", "new", "watch", "monitor", "download", "downloads", "workflow"])
    )


def has_webhook_start(task: str) -> bool:
    lowered = task.lower()
    return any(
        term in lowered
        for term in [
            "webhook",
            "form submission",
            "form endpoint",
            "receives a lead",
            "receives webhook data",
            "receives data",
        ]
    ) or ("receives" in lowered and "api call" in lowered) or ("returns json" in lowered and ("rest" in lowered or "api" in lowered))


def has_schedule_start(task: str) -> bool:
    lowered = task.lower()
    return any(term in lowered for term in ["schedule", "daily", "hourly", "weekday", "week day", "morning", "every day", "every weekday"])


def has_email_action(task: str) -> bool:
    lowered = task.lower()
    explicit_phrases = [
        "send email",
        "sending email",
        "sending an email",
        "sending emails",
        "email someone",
        "notify by email",
        "approval before email",
        "draft email",
        "reply by email",
        "send approved answer",
        "sends a confirmation email",
        "confirmation email",
        "emails me",
        "email me",
        "before email",
        "by email",
        "email follow-up",
    ]
    return any(phrase in lowered for phrase in explicit_phrases) or bool(re.search(r"\b(send|sends|sending|sent|draft|drafts|reply|replies|notify|notifies)\b[^.?!]{0,80}\bemail\b", lowered))


def has_human_approval(task: str) -> bool:
    lowered = task.lower()
    return any(
        term in lowered
        for term in [
            "human approval",
            "approve before sending",
            "human in the loop",
            "human-in-the-loop",
            "review before email",
            "confirmation before send",
            "before i approve",
            "after i approve",
            "after i approve it",
            "approval gate",
            "approval step",
        ]
    ) or bool(re.search(r"\bapprove[sd]?\b", lowered))


def should_split_rag_document_chatbot(task: str) -> bool:
    lowered = task.lower()
    rag_terms = [
        "rag",
        "vector store",
        "pinecone",
        "supabase",
        "qdrant",
        "redis",
        "embeddings",
        "knowledge base",
    ]
    document_terms = [
        "uploaded pdfs",
        "uploaded pdf",
        "pdfs",
        "pdf",
        "documents",
        "document",
        "knowledge base",
    ]
    return has_chatbot_intent(task) and any(term in lowered for term in rag_terms) and any(term in lowered for term in document_terms)


def vector_store_node_name_for_task(task: str) -> str:
    lowered = task.lower()
    if "pinecone" in lowered:
        return "Pinecone Vector Store"
    if "supabase" in lowered:
        return "Supabase Vector Store"
    if "qdrant" in lowered:
        return "Qdrant Vector Store"
    if "redis" in lowered:
        return "Redis Vector Store"
    return "Vector Store Search"


def infer_split_rag_document_chatbot_nodes(task: str, analysis: PlanningAnalysis) -> list[dict[str, str]]:
    lowered = task.lower()
    vector_node_name = vector_store_node_name_for_task(task)
    upload_trigger = "Webhook Trigger" if "webhook" in lowered else "Manual Trigger"
    upload_settings = (
        "Set HTTP Method to `POST`. Set Path to `<short-path-like-upload-pdf>`. Set Response Mode to `Using Respond to Webhook Node`."
        if upload_trigger == "Webhook Trigger"
        else "Use this while building, then replace it with your file-upload source such as a Webhook Trigger or form trigger."
    )
    nodes = [
        node(upload_trigger, "Workflow A starts document ingestion when a PDF is available.", upload_settings, "trigger", "Workflow A: Document Ingestion"),
        node("Extract From File", "Workflow A reads text from the uploaded PDF.", "Set Operation to `Extract From File`. Set Binary Property to `data`. Set Destination Field to `extractedText`.", "document_ingestion", "Workflow A: Document Ingestion"),
        node("Code", "Workflow A prepares document chunks before embeddings.", "Split `{{$json.extractedText}}` into chunks of about 800-1200 tokens and include metadata fields such as `sourceTitle`, `sourceUrl`, and `pageNumber` when available.", "document_ingestion", "Workflow A: Document Ingestion"),
        node("Embeddings", "Workflow A creates vector embeddings for each chunk.", "Set Model credential to `<embedding model credential>`. Set Text to `{{$json.chunkText}}`. Keep source metadata with the embedding output.", "document_ingestion", "Workflow A: Document Ingestion"),
        node(vector_node_name, "Workflow A upserts PDF chunks and metadata into the vector store.", "Set Operation to `Insert` or `Upsert`. Set Index/Table to `<document index>`. Map embedding vector, chunk text, and source metadata into the vector store record.", "vector_storage", "Workflow A: Document Ingestion"),
        node("Chat Trigger", "Workflow B starts when the user asks the chatbot a question.", "Set Mode to hosted chat or embedded chat for your deployment. Set Initial Message to one sentence explaining the bot answers from uploaded PDFs.", "trigger", "Workflow B: RAG Chatbot"),
        node("AI Agent", "Workflow B writes the answer using retrieved PDF context.", "Set Chat Model credential to `<model credential>`. Set System Message to the prompt in this guide. Tell the agent to answer only from retrieved source_context and cite sources.", "ai_agent", "Workflow B: RAG Chatbot"),
        node("Vector Store Question Answer Tool", "Workflow B lets the AI Agent retrieve relevant chunks before answering.", "Set Tool Description to `Search uploaded PDF knowledge base`. Set Query to `{{$json.chatInput || $json.question}}`. Set Top K to `5`. Return chunk text and source metadata.", "rag_retrieval", "Workflow B: RAG Chatbot"),
        node(vector_node_name, "Workflow B retrieves matching document chunks from the vector store.", "Set Operation to `Retrieve Documents` or equivalent search operation. Map Query to `{{$json.chatInput || $json.question}}`. Set Top K to `5`. Return source metadata with each match.", "rag_retrieval", "Workflow B: RAG Chatbot"),
    ]
    if "memory" in lowered:
        nodes.append(node("Simple Memory", "Workflow B keeps short chat context for follow-up questions.", "Set Session ID to `{{$json.sessionId}}`. Keep memory short and do not store secrets or full documents in memory.", "control_flow", "Workflow B: RAG Chatbot"))
    if analysis.has_human_approval:
        nodes.append(node("IF", "Workflow B checks whether a human approved the email action.", "Condition: `{{$json.approvalStatus}} equals approved`. True branch: continue to email. False branch: stop or return a safe message without sending email.", "approval_gate", "Workflow B: RAG Chatbot"))
    if analysis.has_email_action:
        nodes.append(node("Email Send", "Workflow B sends the approved answer as an email action.", "Set To to `<recipient email>`. Set Subject to `Approved chatbot answer`. Set Body to the approved AI answer plus citations. Use an email/SMTP/Gmail credential. Email is not sent until approval is received.", "action", "Workflow B: RAG Chatbot"))
    nodes.append(node("Respond to Chat", "Workflow B returns the final answer or safe rejection message to the chat user.", "Return the AI answer with citations when approved for chat display. If the email was rejected, return `Email not sent because approval was rejected`.", "response", "Workflow B: RAG Chatbot"))
    return nodes


def infer_nodes(task: str) -> list[dict[str, str]]:
    lowered = task.lower()
    analysis = analyze_planning_intent(task)
    if analysis.recommended_workflow_split != "none":
        return infer_split_rag_document_chatbot_nodes(task, analysis)

    nodes: list[dict[str, str]] = []
    if analysis.detected_start_event == "error":
        nodes.append(node("Error Trigger", "Starts an error-handling workflow when another workflow fails.", "Set this workflow as the error workflow in n8n settings or workflow settings. Use the incoming execution error fields to build the alert.", "trigger"))
    elif analysis.detected_start_event == "chat":
        nodes.append(node("Chat Trigger", "Starts the workflow when a chat message is sent.", "Set Mode to hosted chat or embedded chat for your deployment. Set Initial Message to one sentence explaining what the bot can answer.", "trigger"))
    elif analysis.detected_start_event == "webhook":
        nodes.append(node("Webhook Trigger", "Starts the workflow when another app sends data.", "Set HTTP Method to `POST`. Set Path to `<short-path-like-new-request>`. Set Response Mode to `Using Respond to Webhook Node`.", "trigger"))
    elif analysis.detected_start_event == "schedule":
        nodes.append(node("Schedule Trigger", "Starts the workflow on a time schedule.", "Set Trigger Interval to `<daily/hourly/custom>`. Set Timezone to your n8n workspace timezone.", "trigger"))
    elif analysis.detected_start_event == "gmail":
        nodes.append(node("Gmail Trigger", "Starts the workflow when a matching email arrives.", "Set Event to `New Email`. Set Search or Label to `<invoice/email filter>`. Turn Download Attachments on when files are needed.", "trigger"))
    else:
        nodes.append(node("Manual Trigger", "Lets you test the workflow by clicking Execute Workflow.", "No special settings. Use this while building.", "trigger"))

    if "attachment" in lowered or "pdf" in lowered or "invoice" in lowered or ("file" in lowered and "convert" not in lowered):
        nodes.append(node("Extract From File", "Reads text or structured data from the incoming file.", "Set Operation to `Extract From File`. Set Binary Property to `data`. Set Destination Field to `extractedText` or `extractedJson`.", "document_ingestion"))

    if "read write files" in lowered or "read and write files" in lowered or "files from disk" in lowered:
        nodes.append(node("Read/Write Files from Disk", "Reads or writes files on a self-hosted n8n filesystem.", "Set Operation to the needed read or write action. Set File Path to the exact self-hosted path. Confirm the n8n process has filesystem permission before production use.", "document_ingestion"))

    if any(term in lowered for term in ["split items", "splits items", "split out", "split item", "splits item"]):
        nodes.append(node("Split Out", "Splits an array into separate items before looping or merging.", "Set Field To Split Out to the array field from the previous node, such as `{{$json.items}}`. Keep paired item data when downstream nodes need the original record."))

    if any(term in lowered for term in ["rename incoming fields", "set/edit fields", "normalized rows", "normalize", "nested api body", "audit row", "form endpoint", "posts new rows", "downloadable file", "n8n node to call", "reusable workflow", "execute sub-workflow", "oauth2 credentials", "protected endpoint"]):
        nodes.append(node("Set", "Creates clean, predictable fields before the next action node.", "Set Mode to `Manual Mapping`. Add only the fields needed by the next node, such as `customerEmail`, `amount`, `apiBody`, or `auditStatus`."))

    if "sub-workflow" in lowered or "sub workflow" in lowered or "reusable" in lowered:
        nodes.append(node("Execute Sub-workflow", "Calls reusable workflow logic from this workflow.", "Set Source to the target workflow. Map input fields from the parent workflow. Set output handling to return the sub-workflow result."))

    if "convert" in lowered or "downloadable file" in lowered:
        nodes.append(node("Convert To File", "Turns JSON or text output into a binary file for download or storage.", "Set Operation to `Convert to File`. Set Source Field to the JSON/text field. Set Binary Property to `data`. Set File Name to `<file-name>`."))

    if "api" in lowered or "rest" in lowered or "http" in lowered or "website" in lowered:
        pagination = " Turn Pagination on and set the next-page parameter/cursor from the API response." if "pagination" in lowered or "page" in lowered else ""
        auth = " Set Authentication to `OAuth2`." if "oauth" in lowered else " Set Authentication to the matching credential."
        nodes.append(node("HTTP Request", "Calls an external API.", f"Set Method to the API method from the API docs. Set URL to `<api-endpoint>`.{auth} Set important headers/body from the API docs. Set Response Format to `JSON`.{pagination}"))

    if any(term in lowered for term in ["loop over", "loop", "batch", "batching", "line items", "500 api records", "every page", "pagination", "pages"]):
        nodes.append(node("Loop Over Items", "Processes many items safely one item or batch at a time.", "Set Batch Size to a safe value like `50`. Use the loop output for the next processing node. Stop after all items are processed."))

    if "merge" in lowered or "merges" in lowered or "two branches" in lowered:
        nodes.append(node("Merge", "Combines data from two workflow branches before the final action.", "Set Mode to the merge strategy that matches the branches, such as `Combine` by matching field or `Append` when the branches are independent. Confirm branch order with a test run."))

    if any(term in lowered for term in ["wait", "waits", "delayed", "delay", "follow-up", "48 hours"]):
        wait_setting = "Set Resume to `After Time Interval` and Amount to `48 hours`." if "48" in lowered else "Set Resume to the date/time from the previous node, such as `{{$json.followUpAt}}`."
        nodes.append(node("Wait", "Pauses the workflow until a time or condition is reached.", wait_setting))

    if "basic llm chain" in lowered:
        nodes.append(node("Basic LLM Chain", "Runs one focused AI prompt when tool use is not needed.", "Set Chat Model credential to `<model credential>`. Set Prompt to the single task you want the model to complete. Map input text from the previous node.", "ai_agent"))
    elif "information extractor" in lowered:
        nodes.append(node("Information Extractor", "Extracts structured fields from text with an AI model.", "Set Text Input to the extracted or incoming text. Define the output fields needed by the next node. Set the model credential.", "ai_agent"))
    elif "text classifier" in lowered or "classifier" in lowered or "classifies" in lowered or "classify" in lowered:
        nodes.append(node("Text Classifier", "Classifies text into named categories so the workflow can route it.", "Set Text Input to the incoming message. Add categories such as `urgent`, `normal`, and `other`. Set the model credential.", "ai_agent"))
    elif "sentiment" in lowered:
        nodes.append(node("Sentiment Analysis", "Detects whether text is positive, neutral, or negative.", "Set Text Input to the message text. Set the model credential. Use the sentiment output in an IF or Switch node.", "ai_agent"))
    elif "summarization" in lowered or "summarize" in lowered or "summarizes" in lowered:
        nodes.append(node("Summarization Chain", "Summarizes long text into a shorter result.", "Set Text Input to the email, document, or website text. Set the model credential. Set output to a concise summary field.", "ai_agent"))
    elif has_ai_need(task):
        nodes.append(node("AI Agent", "Uses an AI model to classify, extract, summarize, or answer.", "Set Chat Model credential to `<model credential>`. Set System Message to the prompt in this guide. Connect only the tools listed in this plan.", "ai_agent"))

    if any(term in lowered for term in ["summarization chain", "summarize", "summarizes"]) and not any(item["name"] == "Set" for item in nodes):
        nodes.append(node("Set", "Renames the AI summary output for the next step.", "Set Mode to `Manual Mapping`. Map `{{$json.summary || $json.text}}` to `summaryText` and keep the source email or document ID."))

    if "vector store question answer" in lowered:
        nodes.append(node("Vector Store Question Answer Tool", "Lets an AI Agent query a vector store as a tool.", "Set Tool Description to when the agent should use this knowledge source. Set Query to the agent question. Set Top K to `5` and return source metadata.", "rag_retrieval"))

    if has_rag_need(task):
        vector_node_name = vector_store_node_name_for_task(task)
        nodes.append(node(vector_node_name, "Looks up relevant document chunks before the AI answers.", "Set Operation to `Retrieve Documents` or equivalent search operation. Map Query to `{{$json.chatInput || $json.question}}`. Set Top K to `5`. Return source metadata with each match.", "rag_retrieval"))

    if "n8n node" in lowered or "n8n public api" in lowered:
        nodes.append(node("n8n", "Calls an n8n workflow or workflow-management action.", "Set Resource to `Workflow` when managing workflows. Set Operation to the exact action needed. Use an n8n API credential or owner credential with the minimum required access."))

    if "switch" in lowered or "more than two" in lowered:
        nodes.append(node("Switch", "Routes data into more than two possible paths.", "Set Mode to `Rules`. Add one rule for each status or category. Add a fallback output for unmatched data.", "control_flow"))
    elif analysis.has_human_approval:
        nodes.append(node("IF", "Checks whether a human approved the action.", "Condition: `{{$json.approvalStatus}} equals approved`. True branch: continue; False branch: stop or return a safe message. Email is not sent until approval is received.", "approval_gate"))
    elif any(term in lowered for term in ["route", "routes", "urgent", "negative", "missing", "condition", "filter", "validation", "validate", "validating", "reject", "unless", "replied", "reply", "retry", "retries", "error", "errors", "failed", "fallback", "falls back", "confidence", "low confidence", "manual review", "bad data", "bad pdf", "bad pdfs", "instead of"]):
        if "replied" in lowered or "reply" in lowered:
            nodes.append(node("IF", "Checks the reply condition before the workflow continues.", "Set Condition to `{{$json.hasReplied}} equals false`. True branch: continue to the follow-up notification. False branch: stop because the user already replied.", "control_flow"))
        elif "retry" in lowered or "retries" in lowered:
            nodes.append(node("IF", "Checks whether an API response should be retried or stopped.", "Set Condition to `{{$json.statusCode}} equals 429` or `{{$json.statusCode}} >= 500`. True branch: wait/retry; False branch: continue or stop with a clear error.", "control_flow"))
        elif "confidence" in lowered or "fallback" in lowered or "falls back" in lowered:
            nodes.append(node("IF", "Checks whether automation confidence is high enough to continue.", "Set Condition to `{{$json.confidence}} >= 0.8`. True branch: continue automatically. False branch: send to a human review path.", "control_flow"))
        else:
            nodes.append(node("IF", "Checks the condition before the workflow continues.", "Set Condition to the field you need to check, such as `{{$json.status}} equals urgent` or `{{$json.amount}} is not empty`.", "control_flow"))

    if "stop and error" in lowered or "stops with" in lowered or "stop with" in lowered:
        nodes.append(node("Stop and Error", "Stops the workflow with a clear failure when required data is missing.", "Set Error Message to the missing field name and source item, such as `Missing invoice amount for {{$json.invoiceId}}`.", "error_handling"))

    if "code node" in lowered:
        nodes.append(node("Code", "Runs custom JavaScript only when built-in mapping nodes are not enough.", "Return an array of JSON items. Preserve paired item data by reading each input item and returning one output item for each input item."))

    if "google sheets" in lowered or "sheet" in lowered:
        nodes.append(node("Google Sheets", "Saves or updates rows in a spreadsheet.", "Set Operation to `Append Row` unless updating existing data. Set Document to `<spreadsheet name>`. Set Sheet to `<tab name>`. Map each column from previous node output."))

    if "slack" in lowered:
        nodes.append(node("Slack", "Sends a message when the important work is done.", "Set Operation to `Send Message`. Set Channel to `<channel name>`. Set Text to a message built from mapped fields."))

    if analysis.has_email_action:
        nodes.append(node("Email Send", "Sends an email as an action only after earlier checks succeed.", "Set To to `<recipient email>`. Set Subject to a clear workflow subject. Set Body to the approved AI answer or mapped workflow result. Use an email/SMTP/Gmail credential. Email is not sent until approval is received when an approval gate is present.", "action"))

    if "notion" in lowered:
        nodes.append(node("Notion", "Creates or updates a Notion page or database row.", "Set Resource to `Database Page`. Set Operation to `Create` or `Update`. Set Database to `<database name>`. Map properties from previous node output."))

    if "respond to webhook" in lowered or "webhook" in lowered or "form" in lowered:
        nodes.append(node("Respond to Webhook", "Returns a clear success or error response to the caller.", "Set Respond With to `JSON`. Set Response Body to `{ \"status\": \"ok\", \"message\": \"received\" }` plus any created record ID.", "response"))

    if len(nodes) == 1:
        nodes.append(node("Set", "Creates clean fields for the next node.", "Keep only fields needed later; rename fields with beginner-friendly names.", "action"))
    return nodes


def node(name: str, why: str, settings: str, role: str = "action", workflow: str = "Main Workflow") -> dict[str, str]:
    if role not in NODE_ROLES:
        raise ValueError(f"unknown node role: {role}")
    return {
        "name": name,
        "role": role,
        "workflow": workflow,
        "why": why,
        "settings": settings,
        "input": "Use the JSON output from the previous node.",
        "output": "Clean JSON fields for the next node.",
        "expressions": "Use n8n expressions like `{{$json.fieldName}}` when mapping values.",
        "mistake": "Do not guess field names. Run the previous node once, then pick fields from the real output.",
    }


def format_nodes(nodes: list[dict[str, str]]) -> str:
    lines: list[str] = []
    for index, item in enumerate(nodes, start=1):
        lines.extend(
            [
                f"{index}. Node Name: {item['name']}",
                f"   - Workflow: {item.get('workflow', 'Main Workflow')}",
                f"   - Role: {item.get('role', 'action')}",
                f"   - Why this node is needed: {item['why']}",
                f"   - Exact settings: {item['settings']}",
                f"   - Input data: {item['input']}",
                f"   - Output data: {item['output']}",
                f"   - Expressions needed: {item['expressions']}",
                f"   - Common mistake: {item['mistake']}",
            ]
        )
    return "\n".join(lines)


def make_workflow_name(task: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", task)
    useful = [word for word in words[:8] if word.lower() not in {"make", "build", "create", "a", "an", "the"}]
    title = " ".join(useful) or "n8n Workflow"
    return title[:70].strip().title()


def has_ai_need(task: str) -> bool:
    terms = [
        "ai",
        "agent",
        "chatbot",
        "chat bot",
        "extract",
        "extracts",
        "extraction",
        "summarize",
        "summarizes",
        "summarization",
        "classify",
        "classifies",
        "classifier",
        "classification",
        "rag",
        "invoice",
        "retrieval",
        "fallback",
        "falls back",
        "sentiment",
    ]
    return contains_any_term(task, terms)


def has_rag_need(task: str) -> bool:
    lowered = task.lower()
    explicit_terms = [
        "rag",
        "vector",
        "pinecone",
        "supabase",
        "qdrant",
        "redis",
        "document retrieval",
        "knowledge base",
        "website content",
    ]
    if contains_any_term(task, explicit_terms):
        return True
    if contains_any_term(task, ["documents", "document", "pdf", "pdfs"]) and has_chatbot_intent(task):
        return True
    return "embedding" in lowered or "embeddings" in lowered


def contains_any_term(text: str, terms: list[str]) -> bool:
    lowered = text.lower()
    return any(re.search(rf"(?<![a-z0-9]){re.escape(term.lower())}(?![a-z0-9])", lowered) for term in terms)


def credentials_for_apps(apps: list[str]) -> str:
    credential_map = {
        "Gmail": "Gmail OAuth credential.",
        "Email app": "Email, IMAP, SMTP, Gmail, or Microsoft Outlook credential, depending on your mailbox.",
        "Google Sheets": "Google Sheets OAuth credential.",
        "Slack": "Slack OAuth or bot token credential.",
        "Notion": "Notion integration credential.",
        "External API": "API key, bearer token, OAuth credential, or basic auth credential for the external API.",
        "Pinecone": "Pinecone API key and index name.",
        "Supabase": "Supabase URL and service role or anon key, depending on the workflow.",
        "AI model provider": "OpenAI, Azure OpenAI, Anthropic, or another model provider credential.",
        "Docker": "Docker host access for self-hosted deployment tasks.",
        "Environment variables": "Environment variable access on the self-hosted n8n host.",
    }
    lines = ["- n8n owner or editor access."]
    for app in apps:
        if app in credential_map:
            lines.append(f"- {credential_map[app]}")
    lines.append("- For API authentication, prefer stored credentials over hardcoded OAuth tokens, bearer tokens, API keys, or secrets.")
    lines.append("- Test credentials before building the full workflow.")
    return "\n".join(lines)


def trigger_description(nodes: list[dict[str, str]], analysis: PlanningAnalysis) -> str:
    trigger_nodes = [item for item in nodes if item.get("role") == "trigger"]
    if analysis.recommended_workflow_split != "none":
        lines = [
            "- Workflow A trigger node: Manual Trigger, Webhook Trigger, or form/file-upload trigger for uploaded PDFs.",
            "- Workflow B trigger node: Chat Trigger.",
            "- Start-event classification: the chatbot/query workflow starts from chat input; email is a later action, not the trigger.",
        ]
        for trigger_node in trigger_nodes:
            lines.append(f"- {trigger_node.get('workflow', 'Workflow')} uses {trigger_node['name']}. Settings: {trigger_node['settings']}")
        return "\n".join(lines)
    trigger_node = trigger_nodes[0] if trigger_nodes else nodes[0]
    return "\n".join(
        [
            f"- Trigger node: {trigger_node['name']}",
            f"- Detected start event: {analysis.detected_start_event}",
            f"- Why: {trigger_node['why']}",
            f"- Settings: {trigger_node['settings']}",
        ]
    )


def data_mapping_for_task(task: str, nodes: list[dict[str, str]]) -> str:
    lines = [
        "- After each node runs, open its output and copy the exact field names.",
        "- Confirm field names in your n8n node output, then use expressions like `{{$json.fieldName}}`.",
        "- Likely mapping examples:",
    ]
    lowered = task.lower()
    node_names = {item["name"].lower() for item in nodes}
    if "webhook trigger" in node_names:
        lines.extend(
            [
                "  - `{{$json.body.email}}` -> validation field `email`.",
                "  - `{{$json.body.customerId}}` -> HTTP Request URL/body field `customerId`.",
                "  - `{{$json.body.requestId}}` -> Google Sheets or response field `Request ID`.",
            ]
        )
    if "chat trigger" in node_names:
        lines.extend(
            [
                "  - `{{$json.chatInput}}` -> vector store query text.",
                "  - `{{$json.sessionId}}` -> memory/session key when memory is used.",
                "  - AI answer text -> email body or chat response text.",
            ]
        )
    if "http request" in node_names:
        lines.extend(
            [
                "  - `{{$json.customerId}}` -> HTTP Request URL parameter or JSON body field.",
                "  - HTTP response `{{$json.id}}` -> downstream `External ID` field.",
                "  - HTTP response `{{$json.status}}` -> IF/Switch condition field.",
            ]
        )
    if "extract from file" in node_names:
        lines.extend(
            [
                "  - `$binary.data` -> Extract From File Binary Property `data`.",
                "  - `{{$json.extractedText}}` -> AI Agent or embedding input text.",
            ]
        )
    if any("vector store" in name for name in node_names):
        lines.extend(
            [
                "  - `{{$json.chatInput || $json.question}}` -> vector store Query.",
                "  - retrieved chunk text -> AI prompt `source_context`.",
                "  - retrieved source URL/title -> final answer citations.",
            ]
        )
    if "invoice" in lowered:
        lines.extend(
            [
                "  - AI output `{{$json.vendor}}` -> Google Sheets column `Vendor`.",
                "  - AI output `{{$json.amount}}` -> Google Sheets column `Amount`.",
                "  - AI output `{{$json.invoiceDate}}` -> Google Sheets column `Invoice Date`.",
                "  - Gmail subject or file name -> Google Sheets column `Source`.",
            ]
        )
    if "slack" in lowered:
        lines.append("  - final status text -> Slack `Text` field.")
    if "notion" in lowered:
        lines.append("  - cleaned field values -> matching Notion database properties.")
    if "api" in lowered or "http" in lowered:
        lines.append("  - API response fields from HTTP Request output -> final app fields; do not reuse request-body fields unless the response omits them.")
    if "approval" in lowered or "human" in lowered:
        lines.append("  - human review result `{{$json.approvalStatus}}` -> IF condition `equals approved`.")
    if "email" in lowered:
        lines.append("  - approved AI answer or summary -> Email Send `Body`; recipient field -> Email Send `To`.")
    if len(lines) == 3:
        lines.append("  - previous node `{{$json.name}}` -> destination field `<Name>`.")
    lines.append("- If the exact app-specific field is unknown, keep this mapping as an assumption and confirm it in the n8n node output.")
    return "\n".join(lines)


def ai_prompt_for_task(task: str) -> str:
    return "\n".join(
        [
            "Use this prompt in the AI node and adjust field names after you inspect real input data:",
            "",
            "```text",
            "You are helping build an n8n automation.",
            f"Task: {task}",
            "Read the input JSON carefully.",
            "Return only valid JSON.",
            "Include fields that the next node needs.",
            "If a value is missing, return null and add a short reason in `notes`.",
            "Do not invent facts.",
            "```",
        ]
    )


def rag_plan_for_task(task: str) -> str:
    analysis = analyze_planning_intent(task)
    if analysis.recommended_workflow_split != "none":
        return "\n".join(
            [
                "- Recommended workflow split: Workflow A: Document Ingestion and Workflow B: RAG Chatbot.",
                "- Workflow A: Document Ingestion starts from a PDF upload source, extracts PDF text, splits text into chunks, creates embeddings, and upserts chunks plus source metadata into the vector store.",
                "- Workflow B: RAG Chatbot starts with Chat Trigger, searches the vector store before the AI Agent answers, passes retrieved chunks into the AI prompt as `source_context`, and shows source titles or URLs in the final answer.",
                "- Keep ingestion separate from chat so uploaded PDFs can be indexed once and queried many times.",
            ]
        )
    return "\n".join(
        [
            "- Create a document ingestion workflow first if your documents are not already in a vector store.",
            "- Split documents into small chunks.",
            "- Create embeddings for each chunk.",
            "- Store chunks and metadata in Pinecone, Supabase, or another vector store.",
            "- In the chat workflow, search the vector store before the AI Agent answers.",
            "- Pass the retrieved chunks into the AI prompt as source context.",
            "- Show source titles or URLs in the final answer.",
        ]
    )


def error_handling_plan(task: str, apps: list[str]) -> str:
    lines = [
        "- Test each credential before connecting all nodes.",
        "- Add clear names to nodes so failed executions are easy to read.",
        "- Add an IF node when a required field is missing.",
        "- Send yourself an error message when the workflow cannot finish.",
        "- Keep failed input data so you can retry after fixing the issue.",
    ]
    if "External API" in apps:
        lines.append("- For API calls, handle 401, 403, 404, 429, and 500 responses separately.")
    if "AI model provider" in apps:
        lines.append("- For AI nodes, handle empty output, invalid JSON, and low-confidence extraction.")
    if "Slack" in apps or "Email app" in apps:
        lines.append("- Do not send final alerts until the main data save step succeeds.")
    if has_human_approval(task) and has_email_action(task):
        lines.append("- Email is not sent until approval is received; the rejected branch should stop or return a safe message.")
    return "\n".join(lines)


def test_steps(nodes: list[dict[str, str]]) -> str:
    lines = ["1. Disable the workflow so it does not run automatically while you build."]
    for index, item in enumerate(nodes, start=2):
        lines.append(f"{index}. Run `{item['name']}` with one safe test item and check the output.")
    lines.extend(
        [
            f"{len(lines) + 1}. Check that every expression uses a real field from the previous node.",
            f"{len(lines) + 2}. Run the full workflow once with test data.",
            f"{len(lines) + 3}. Confirm the final app received the expected result.",
            f"{len(lines) + 4}. Turn on the workflow only after the test run succeeds.",
        ]
    )
    return "\n".join(lines)


def final_checklist(apps: list[str], needs_ai: bool, needs_rag: bool) -> str:
    lines = [
        "- Workflow has a clear name.",
        "- Every credential is connected and tested.",
        "- Every node has been run once with test data.",
        "- Data mapping uses real field names.",
        "- Error path is tested.",
        "- Final output is checked in the target app.",
    ]
    if needs_ai:
        lines.append("- AI output is valid JSON or clearly formatted text.")
    if needs_rag:
        lines.append("- Retrieved source chunks are shown or stored for review.")
    return "\n".join(lines)


def design_decisions(task: str, nodes: list[dict[str, str]], selected_rags: list[str], output_mode: str) -> str:
    analysis = analyze_planning_intent(task)
    lines = [
        f"- Output mode: `{output_mode}`.",
        f"- RAG indexes selected: {', '.join(selected_rags)}.",
        "- The workflow is designed as a simple line of nodes so a beginner can test each step.",
        "- Node settings are written as starting settings and should be adjusted after inspecting real node output.",
    ]
    if analysis.recommended_workflow_split != "none":
        lines.append("- RAG over uploaded PDFs is split into Workflow A: Document Ingestion and Workflow B: RAG Chatbot.")
        lines.append("- Chat Trigger is selected for the chatbot/query workflow because the starting event is a user chat question.")
    if analysis.has_email_action:
        lines.append("- Email is treated as a later action, not as the workflow trigger.")
    if analysis.has_human_approval and analysis.has_email_action:
        lines.append("- Email is not sent until approval is received; the approval result controls the IF branch and the rejected branch stops or returns a safe message.")
    if has_ai_need(task):
        lines.append("- AI is used only where extraction, summarization, classification, or question answering is needed.")
    if output_mode == "workflow_json_blueprint":
        lines.append("- Workflow JSON should be treated as a blueprint and import-tested in n8n before production use.")
    if any(term in task.lower() for term in ["docker", "environment", "self-host", "queue mode", "security"]):
        lines.append("- Deployment details depend on the self-hosted environment, Docker setup, environment variables, and security policy.")
    if "fallback" in task.lower() or "falls back" in task.lower():
        lines.append("- Human fallback is used when automation should not pretend certainty.")
    if "if versus switch" in task.lower() or "if vs switch" in task.lower():
        lines.append("- IF is for simple true or false conditions; Switch is for routing more than two condition paths.")
    return "\n".join(lines)


def needs_user_confirmation(task: str, apps: list[str]) -> str:
    lines = [
        "- Exact credential names in your n8n workspace.",
        "- Exact field names after you run the trigger node once.",
    ]
    if "Google Sheets" in apps:
        lines.append("- Spreadsheet name, sheet tab name, and column names.")
    if "Slack" in apps:
        lines.append("- Slack channel name and final message format.")
    if "Notion" in apps:
        lines.append("- Notion database and property names.")
    if "External API" in apps:
        lines.append("- API endpoint, auth method, required headers, and request body.")
    if has_rag_need(task):
        lines.append("- Vector store provider, index/table name, embedding model, and source document location.")
    return "\n".join(lines)


STRICT_REQUIRED_SECTIONS = [
    "Workflow Name",
    "What This Workflow Does",
    "Assumptions",
    "Apps / Tools Needed",
    "Credentials Needed",
    "Trigger",
    "Nodes To Add",
    "Data Mapping",
    "Error Handling",
    "Test Steps",
    "Final Checklist",
    "Source-Grounded Facts",
    "Design Decisions",
    "Sources Used",
]


def validate_workflow_sections(
    sections: dict[str, str],
    require_sources: bool = False,
    output_mode: str = "full_build_plan",
    user_task: str = "",
) -> None:
    missing = [section for section in STRICT_REQUIRED_SECTIONS if not sections.get(section, "").strip()]
    if missing:
        raise ValueError(f"workflow response missing required sections: {', '.join(missing)}")
    section_checks = {
        "Credentials Needed": ["credential"],
        "Trigger": ["trigger", "settings"],
        "Nodes To Add": ["Node Name", "Exact settings", "Input data", "Output data", "Expressions needed", "Common mistake"],
        "Data Mapping": ["Map", "expression"],
        "Error Handling": ["error"],
        "Test Steps": ["Run", "test"],
        "Source-Grounded Facts": ["Source"],
        "Design Decisions": ["RAG indexes selected"],
        "Needs User Confirmation": ["Exact"],
    }
    failures: list[str] = []
    for section, keywords in section_checks.items():
        text = sections.get(section, "")
        for keyword in keywords:
            if keyword.lower() not in text.lower():
                failures.append(f"{section} missing `{keyword}`")
    if require_sources and "http" not in sections.get("Sources Used", "").lower():
        failures.append("Sources Used missing source URLs")
    if output_mode == "full_build_plan":
        node_count = count_node_steps(sections.get("Nodes To Add", ""))
        if node_count < 3 and not is_genuinely_tiny_task(user_task):
            failures.append("full_build_plan needs at least 3 node steps for non-tiny tasks")
        if mentions_external_services(user_task) and count_bullets(sections.get("Credentials Needed", "")) < 2:
            failures.append("external-service task needs at least one external credential item")
        if count_numbered_steps(sections.get("Test Steps", "")) < 1:
            failures.append("full_build_plan needs at least one test step")
        if count_bullets(sections.get("Error Handling", "")) < 1:
            failures.append("full_build_plan needs at least one error-handling item")
        if require_sources and count_bullets(sections.get("Sources Used", "")) < 1:
            failures.append("full_build_plan needs at least one citation")
    if failures:
        raise ValueError("workflow response validation failed: " + "; ".join(failures))


def count_node_steps(text: str) -> int:
    return len(re.findall(r"(?m)^\d+\.\s+Node Name:", text))


def count_bullets(text: str) -> int:
    return len(re.findall(r"(?m)^\s*[-*]\s+", text))


def count_numbered_steps(text: str) -> int:
    return len(re.findall(r"(?m)^\d+\.\s+", text))


def mentions_external_services(task: str) -> bool:
    lowered = task.lower()
    terms = [
        "gmail",
        "email",
        "slack",
        "google sheets",
        "notion",
        "api",
        "http",
        "oauth",
        "pinecone",
        "supabase",
        "qdrant",
        "redis",
        "openai",
        "anthropic",
        "webhook",
    ]
    return any(term in lowered for term in terms)


def is_genuinely_tiny_task(task: str) -> bool:
    lowered = task.lower()
    complex_terms = [
        "rag",
        "ai",
        "agent",
        "webhook",
        "api",
        "approval",
        "human",
        "invoice",
        "pdf",
        "pagination",
        "sub-workflow",
        "loop",
        "batch",
        "oauth",
        "json",
    ]
    if contains_any_term(lowered, complex_terms):
        return False
    tiny_terms = [
        "slack alert",
        "slack message when a new email arrives",
        "manual test",
        "two-node",
        "simple workflow",
        "schedule",
        "set/edit fields",
        "rename incoming fields",
    ]
    return any(term in lowered for term in tiny_terms) or len(lowered.split()) < 8
