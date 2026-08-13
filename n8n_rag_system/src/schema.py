from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Literal


RAG_NAMES = {
    "n8n_core_docs_rag",
    "n8n_nodes_rag",
    "n8n_ai_agents_rag",
    "n8n_workflow_json_rag",
    "n8n_beginner_instruction_rag",
    "n8n_workflow_examples_rag",
}

PRIORITIES = {"high", "medium", "low"}

try:
    from pydantic import BaseModel, ConfigDict, Field, field_validator

    class _StrictModel(BaseModel):
        model_config = ConfigDict(extra="forbid")

    class Source(_StrictModel):
        title: str
        url: str
        category: str
        rag_target: str
        priority: Literal["high", "medium", "low"]
        source_type: str
        last_checked: str | None = None
        enabled: bool = True

        @field_validator("title", "url", "category", "rag_target", "source_type")
        @classmethod
        def _not_empty(cls, value: str) -> str:
            if not value or not str(value).strip():
                raise ValueError("field cannot be empty")
            return value

        @field_validator("rag_target")
        @classmethod
        def _known_rag(cls, value: str) -> str:
            if value not in RAG_NAMES:
                raise ValueError(f"unknown rag_target: {value}")
            return value

    class Document(_StrictModel):
        doc_id: str
        text: str
        source_title: str
        source_url: str
        category: str
        rag_target: str
        priority: str
        metadata: dict[str, Any] = Field(default_factory=dict)

    class Chunk(_StrictModel):
        text: str
        source_title: str
        source_url: str
        heading_path: list[str] = Field(default_factory=list)
        doc_category: str
        rag_target: str
        chunk_id: str
        chunk_type: str
        priority: str
        metadata: dict[str, Any] = Field(default_factory=dict)

    class RouterDecision(_StrictModel):
        selected_rags: list[str]
        rewritten_queries: dict[str, str]
        reason: str
        retrieval_parameters: dict[str, Any] = Field(default_factory=dict)

    class RetrievedChunk(_StrictModel):
        text: str
        source_title: str
        source_url: str
        heading_path: list[str] = Field(default_factory=list)
        relevance_score: float
        rag_name: str
        chunk_id: str | None = None
        priority: str = "medium"

    class WorkflowInstructionRequest(_StrictModel):
        user_task: str
        apps_tools_available: list[str] = Field(default_factory=list)
        skill_level: str = "beginner"
        preferred_deployment: str | None = None
        output_mode: Literal[
            "beginner_steps",
            "technical_steps",
            "workflow_json_blueprint",
            "troubleshooting",
            "full_build_plan",
        ] = "full_build_plan"

    class WorkflowInstructionResponse(_StrictModel):
        content: str
        sections: dict[str, str] = Field(default_factory=dict)
        sources: list[dict[str, Any]] = Field(default_factory=list)

except Exception:

    def _require_mapping(data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise ValueError("expected a mapping")
        return data

    def _require_fields(data: dict[str, Any], fields: list[str]) -> None:
        missing = [name for name in fields if name not in data]
        if missing:
            raise ValueError(f"missing required fields: {', '.join(missing)}")

    def _not_empty(value: Any, field_name: str) -> str:
        if value is None or not str(value).strip():
            raise ValueError(f"{field_name} cannot be empty")
        return str(value)

    @dataclass
    class _SchemaMixin:
        @classmethod
        def model_validate(cls, data: Any):
            data = _require_mapping(data)
            return cls(**data)

        def model_dump(self) -> dict[str, Any]:
            return asdict(self)

        def dict(self) -> dict[str, Any]:
            return self.model_dump()

    @dataclass
    class Source(_SchemaMixin):
        title: str
        url: str
        category: str
        rag_target: str
        priority: str
        source_type: str
        last_checked: str | None = None
        enabled: bool = True

        @classmethod
        def model_validate(cls, data: Any):
            data = _require_mapping(data)
            _require_fields(
                data,
                [
                    "title",
                    "url",
                    "category",
                    "rag_target",
                    "priority",
                    "source_type",
                    "last_checked",
                    "enabled",
                ],
            )
            return cls(**data)

        def __post_init__(self) -> None:
            self.title = _not_empty(self.title, "title")
            self.url = _not_empty(self.url, "url")
            self.category = _not_empty(self.category, "category")
            self.rag_target = _not_empty(self.rag_target, "rag_target")
            self.source_type = _not_empty(self.source_type, "source_type")
            if self.rag_target not in RAG_NAMES:
                raise ValueError(f"unknown rag_target: {self.rag_target}")
            if self.priority not in PRIORITIES:
                raise ValueError(f"unknown priority: {self.priority}")

    @dataclass
    class Document(_SchemaMixin):
        doc_id: str
        text: str
        source_title: str
        source_url: str
        category: str
        rag_target: str
        priority: str
        metadata: dict[str, Any] = field(default_factory=dict)

    @dataclass
    class Chunk(_SchemaMixin):
        text: str
        source_title: str
        source_url: str
        heading_path: list[str]
        doc_category: str
        rag_target: str
        chunk_id: str
        chunk_type: str
        priority: str
        metadata: dict[str, Any] = field(default_factory=dict)

    @dataclass
    class RouterDecision(_SchemaMixin):
        selected_rags: list[str]
        rewritten_queries: dict[str, str]
        reason: str
        retrieval_parameters: dict[str, Any] = field(default_factory=dict)

    @dataclass
    class RetrievedChunk(_SchemaMixin):
        text: str
        source_title: str
        source_url: str
        heading_path: list[str]
        relevance_score: float
        rag_name: str
        chunk_id: str | None = None
        priority: str = "medium"

    @dataclass
    class WorkflowInstructionRequest(_SchemaMixin):
        user_task: str
        apps_tools_available: list[str] = field(default_factory=list)
        skill_level: str = "beginner"
        preferred_deployment: str | None = None
        output_mode: str = "full_build_plan"

        def __post_init__(self) -> None:
            self.user_task = _not_empty(self.user_task, "user_task")
            allowed = {
                "beginner_steps",
                "technical_steps",
                "workflow_json_blueprint",
                "troubleshooting",
                "full_build_plan",
            }
            if self.output_mode not in allowed:
                raise ValueError(f"unknown output_mode: {self.output_mode}")

    @dataclass
    class WorkflowInstructionResponse(_SchemaMixin):
        content: str
        sections: dict[str, str] = field(default_factory=dict)
        sources: list[dict[str, Any]] = field(default_factory=list)


def schema_to_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return value
    raise TypeError(f"cannot convert {type(value)!r} to dict")

