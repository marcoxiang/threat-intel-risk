from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import RiskStatus, SeverityBand, SourceStatus, SourceType


class SourceDocumentOut(BaseModel):
    id: UUID
    type: SourceType
    title: str
    publisher: str | None
    published_at: datetime | None
    ingested_at: datetime
    content_hash: str | None
    status: SourceStatus
    source_url: str | None

    model_config = {"from_attributes": True}


class IngestionJobOut(BaseModel):
    id: UUID
    source_document_id: UUID
    status: SourceStatus
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class EvidenceSnippetOut(BaseModel):
    id: UUID
    source_document_id: UUID
    risk_item_id: UUID | None
    text: str
    page_or_dom_ref: str
    url: str | None
    captured_at: datetime
    confidence: float = Field(ge=0.0, le=1.0)

    model_config = {"from_attributes": True}


class RiskScoreOut(BaseModel):
    tef: int
    vulnerability: int
    primary_loss: int
    secondary_loss: int
    composite_score: float
    severity_band: SeverityBand

    model_config = {"from_attributes": True}


class EmergingSignalOut(BaseModel):
    trend_ratio: float
    novelty_score: float
    source_diversity: int
    triggered: bool
    trigger_reason: str | None

    model_config = {"from_attributes": True}


class RiskStatementOut(BaseModel):
    business_impact: str
    why_care: str
    time_horizon: str
    recommended_actions: list[str]
    confidence: float
    approved_by: str | None
    approved_at: datetime | None
    citation_snippet_ids: list[str]

    model_config = {"from_attributes": True}


class RiskItemOut(BaseModel):
    id: UUID
    source_document_id: UUID
    name: str
    taxonomy_category: str
    threat_actor: str | None
    affected_sector: list[str]
    affected_assets: list[str]
    status: RiskStatus
    extraction_confidence: float
    statement: RiskStatementOut | None
    score: RiskScoreOut | None
    emerging_signal: EmergingSignalOut | None

    model_config = {"from_attributes": True}
