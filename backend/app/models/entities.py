from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import RiskStatus, SeverityBand, SourceStatus, SourceType


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


class SourceDocument(Base, TimestampMixin):
    __tablename__ = "source_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type: Mapped[SourceType] = mapped_column(Enum(SourceType), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    publisher: Mapped[str | None] = mapped_column(String(255))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    status: Mapped[SourceStatus] = mapped_column(Enum(SourceStatus), default=SourceStatus.QUEUED)
    source_url: Mapped[str | None] = mapped_column(Text)
    artifact_path: Mapped[str | None] = mapped_column(Text)

    jobs: Mapped[list[IngestionJob]] = relationship(back_populates="source_document")
    evidence_snippets: Mapped[list[EvidenceSnippet]] = relationship(back_populates="source_document")
    risk_items: Mapped[list[RiskItem]] = relationship(back_populates="source_document")


class IngestionJob(Base, TimestampMixin):
    __tablename__ = "ingestion_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_documents.id"), nullable=False
    )
    status: Mapped[SourceStatus] = mapped_column(Enum(SourceStatus), default=SourceStatus.QUEUED)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    source_document: Mapped[SourceDocument] = relationship(back_populates="jobs")


class EvidenceSnippet(Base, TimestampMixin):
    __tablename__ = "evidence_snippets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_documents.id"), nullable=False
    )
    risk_item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("risk_items.id"))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    page_or_dom_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(Text)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    confidence: Mapped[float] = mapped_column(Float, default=0.9)

    source_document: Mapped[SourceDocument] = relationship(back_populates="evidence_snippets")
    risk_item: Mapped[RiskItem | None] = relationship(back_populates="evidence_snippets")


class RiskItem(Base, TimestampMixin):
    __tablename__ = "risk_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_documents.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    taxonomy_category: Mapped[str] = mapped_column(String(255), nullable=False)
    threat_actor: Mapped[str | None] = mapped_column(String(255))
    affected_sector: Mapped[list[str]] = mapped_column(JSON, default=list)
    affected_assets: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[RiskStatus] = mapped_column(Enum(RiskStatus), default=RiskStatus.DRAFT)
    extraction_confidence: Mapped[float] = mapped_column(Float, default=0.7)

    source_document: Mapped[SourceDocument] = relationship(back_populates="risk_items")
    statement: Mapped[RiskStatement | None] = relationship(back_populates="risk_item", uselist=False)
    score: Mapped[RiskScore | None] = relationship(back_populates="risk_item", uselist=False)
    emerging_signal: Mapped[EmergingSignal | None] = relationship(back_populates="risk_item", uselist=False)
    evidence_snippets: Mapped[list[EvidenceSnippet]] = relationship(back_populates="risk_item")


class RiskStatement(Base, TimestampMixin):
    __tablename__ = "risk_statements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    risk_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("risk_items.id"), nullable=False, unique=True
    )
    business_impact: Mapped[str] = mapped_column(Text, nullable=False)
    why_care: Mapped[str] = mapped_column(Text, nullable=False)
    time_horizon: Mapped[str] = mapped_column(String(255), nullable=False)
    recommended_actions: Mapped[list[str]] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=0.7)
    approved_by: Mapped[str | None] = mapped_column(String(255))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    citation_snippet_ids: Mapped[list[str]] = mapped_column(JSON, default=list)

    risk_item: Mapped[RiskItem] = relationship(back_populates="statement")


class RiskScore(Base, TimestampMixin):
    __tablename__ = "risk_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    risk_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("risk_items.id"), nullable=False, unique=True
    )
    tef: Mapped[int] = mapped_column(Integer, nullable=False)
    vulnerability: Mapped[int] = mapped_column(Integer, nullable=False)
    primary_loss: Mapped[int] = mapped_column(Integer, nullable=False)
    secondary_loss: Mapped[int] = mapped_column(Integer, nullable=False)
    composite_score: Mapped[float] = mapped_column(Float, nullable=False)
    severity_band: Mapped[SeverityBand] = mapped_column(Enum(SeverityBand), nullable=False)

    risk_item: Mapped[RiskItem] = relationship(back_populates="score")


class EmergingSignal(Base, TimestampMixin):
    __tablename__ = "emerging_signals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    risk_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("risk_items.id"), nullable=False, unique=True
    )
    trend_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    novelty_score: Mapped[float] = mapped_column(Float, default=0.0)
    source_diversity: Mapped[int] = mapped_column(Integer, default=0)
    triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    trigger_reason: Mapped[str | None] = mapped_column(Text)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    risk_item: Mapped[RiskItem] = relationship(back_populates="emerging_signal")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    target_type: Mapped[str] = mapped_column(String(255), nullable=False)
    target_id: Mapped[str] = mapped_column(String(255), nullable=False)
    before_json: Mapped[dict | None] = mapped_column(JSON)
    after_json: Mapped[dict | None] = mapped_column(JSON)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
