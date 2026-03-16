from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> float:
    return time.time()


# ---------------------------------------------------------------------------
# Photo-level models
# ---------------------------------------------------------------------------

class PhotoMeta(BaseModel):
    """Metadata for a single uploaded photo."""
    id: str = Field(default_factory=_uuid)
    filename: str
    mime_type: str
    b64_data: str  # base64-encoded image bytes (no data-url prefix)


class PhotoAnalysis(BaseModel):
    """Output of Stage 1 – individual photo analysis."""
    photo_id: str
    description: str = ""
    issues: list[str] = Field(default_factory=list)
    severity: str = ""  # low / medium / high / critical
    location_hint: str = ""
    tags: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Group / finding models
# ---------------------------------------------------------------------------

class PhotoGroup(BaseModel):
    """Output of Stage 2 – a cluster of related photos."""
    id: str = Field(default_factory=_uuid)
    label: str
    photo_ids: list[str]
    key_photo_ids: list[str]  # subset selected as most representative


class Finding(BaseModel):
    """Output of Stage 3 – a professional analysis for one group."""
    id: str = Field(default_factory=_uuid)
    group_id: str
    observation: str = ""
    potential_cause: str = ""
    recommendation: str = ""
    severity: str = ""


# ---------------------------------------------------------------------------
# Template models
# ---------------------------------------------------------------------------

class TemplateFieldType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    TABLE = "table"
    LIST = "list"


class TemplateField(BaseModel):
    name: str
    field_type: TemplateFieldType
    description: str = ""
    location_hint: str = ""  # e.g. "Section 3 – Findings table"


class TemplateSchema(BaseModel):
    """Output of Stage 4 – the analysed structure of the template."""
    format: str = "docx"  # "docx" | "pdf"
    sections: list[str] = Field(default_factory=list)
    fields: list[TemplateField] = Field(default_factory=list)
    findings_section: str = ""  # which section holds findings
    has_photo_placeholders: bool = False
    raw_instructions: str = ""  # free-form LLM notes on how to fill


# ---------------------------------------------------------------------------
# Pipeline status
# ---------------------------------------------------------------------------

class PipelineStage(str, Enum):
    UPLOADING = "uploading"
    ANALYZING_PHOTOS = "analyzing_photos"
    GROUPING = "grouping"
    WRITING_ANALYSES = "writing_analyses"
    ANALYZING_TEMPLATE = "analyzing_template"
    READY_FOR_REVIEW = "ready_for_review"
    GENERATING_REPORT = "generating_report"
    DONE = "done"
    ERROR = "error"


class PipelineStatus(BaseModel):
    stage: PipelineStage = PipelineStage.UPLOADING
    progress: float = 0.0  # 0-1
    message: str = ""
    error: str | None = None


# ---------------------------------------------------------------------------
# Session (holds everything for one report)
# ---------------------------------------------------------------------------

class Session(BaseModel):
    id: str = Field(default_factory=_uuid)
    created_at: float = Field(default_factory=_now)

    # Uploads
    photos: dict[str, PhotoMeta] = Field(default_factory=dict)
    template_filename: str = ""
    template_bytes: bytes = b""
    template_mime: str = ""

    # Pipeline outputs
    photo_analyses: dict[str, PhotoAnalysis] = Field(default_factory=dict)
    groups: list[PhotoGroup] = Field(default_factory=list)
    findings: dict[str, Finding] = Field(default_factory=dict)
    template_schema: TemplateSchema | None = None

    status: PipelineStatus = Field(default_factory=PipelineStatus)

    # User-selected model overrides
    vision_model: str = ""
    text_model: str = ""

    model_config = {"arbitrary_types_allowed": True}


# ---------------------------------------------------------------------------
# API request / response helpers
# ---------------------------------------------------------------------------

class UpdateFindingRequest(BaseModel):
    observation: str | None = None
    potential_cause: str | None = None
    recommendation: str | None = None
    severity: str | None = None


class MovePhotoRequest(BaseModel):
    photo_id: str
    source_group_id: str
    target_group_id: str | None = None  # None → create new group


class ReAnalyzeRequest(BaseModel):
    group_id: str
    hint: str = ""  # optional user guidance


class NewGroupFromPhotoRequest(BaseModel):
    photo_id: str
    source_group_id: str
    label: str = ""
    hint: str = ""


class SessionSummary(BaseModel):
    session_id: str
    stage: PipelineStage
    photo_count: int
    group_count: int
    template_filename: str


class AnalysisResults(BaseModel):
    groups: list[PhotoGroup]
    findings: dict[str, Finding]
    photo_analyses: dict[str, PhotoAnalysis]
    template_schema: TemplateSchema | None
    photos: dict[str, str]  # photo_id → base64 thumbnail for display
