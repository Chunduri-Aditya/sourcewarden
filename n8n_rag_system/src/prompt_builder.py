from __future__ import annotations

from pathlib import Path
from typing import Any

from .citations import format_sources, format_source_grounded_facts
from .schema import RetrievedChunk, schema_to_dict
from .utils import PROJECT_ROOT


REQUIRED_WORKFLOW_SECTIONS = [
    "Workflow Name",
    "What This Workflow Does",
    "Assumptions",
    "Apps / Tools Needed",
    "Credentials Needed",
    "Trigger",
    "Nodes To Add",
    "Data Mapping",
    "AI Prompt, If Used",
    "Memory / RAG, If Used",
    "Error Handling",
    "Test Steps",
    "Final Checklist",
    "Source-Grounded Facts",
    "Design Decisions",
    "Needs User Confirmation",
    "Sources Used",
]


class PromptBuilder:
    def __init__(self, prompts_dir: str | Path | None = None) -> None:
        self.prompts_dir = Path(prompts_dir or PROJECT_ROOT / "prompts")

    def build(
        self,
        user_task: str,
        retrieved_chunks: list[RetrievedChunk | dict[str, Any]],
        output_mode: str = "full_build_plan",
        apps_tools_available: list[str] | None = None,
        skill_level: str = "beginner",
        preferred_deployment: str | None = None,
    ) -> str:
        system_prompt = self._read_prompt("system_n8n_workflow_architect.md")
        template_prompt = self._read_prompt("workflow_recipe_template.md")
        facts = format_source_grounded_facts(retrieved_chunks)
        context = self._format_context(retrieved_chunks)
        sources = format_sources(retrieved_chunks)
        apps = ", ".join(apps_tools_available or []) or "Not provided"
        deployment = preferred_deployment or "Not provided"
        sections = "\n".join(f"# {section}" for section in REQUIRED_WORKFLOW_SECTIONS)
        return "\n\n".join(
            [
                system_prompt,
                "## User-Provided Requirements\n"
                f"Task: {user_task}\n"
                f"Skill level: {skill_level}\n"
                f"Output mode: {output_mode}\n"
                f"Apps/tools available: {apps}\n"
                f"Preferred deployment: {deployment}",
                "## Retrieved Facts\n" + facts,
                "## Retrieved Context\n" + context,
                "## Design Decisions\n"
                "- Choose the simplest workflow that satisfies the user task.\n"
                "- Label any settings that depend on the user's account or data.\n"
                "- Do not invent source-backed facts when retrieved context is missing.",
                "## Assumptions\n"
                "- The user can create needed n8n credentials.\n"
                "- Exact account, folder, channel, and field names may need confirmation.",
                "## Required Output Structure\n" + sections,
                "## Template Reminder\n" + template_prompt,
                "## Sources\n" + sources,
            ]
        )

    def _read_prompt(self, file_name: str) -> str:
        path = self.prompts_dir / file_name
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8").strip()

    def _format_context(self, chunks: list[RetrievedChunk | dict[str, Any]]) -> str:
        if not chunks:
            return "No retrieved context is available."
        lines: list[str] = []
        for index, chunk in enumerate(chunks, start=1):
            data = schema_to_dict(chunk)
            heading = " > ".join(data.get("heading_path") or [])
            lines.append(
                f"[{index}] RAG: {data.get('rag_name', '')}\n"
                f"Source: {data.get('source_title', '')} {data.get('source_url', '')}\n"
                f"Heading: {heading}\n"
                f"Text:\n{data.get('text', '').strip()}"
            )
        return "\n\n".join(lines)

