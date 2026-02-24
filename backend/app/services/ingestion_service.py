from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.entities import (
    EmergingSignal,
    EvidenceSnippet,
    IngestionJob,
    RiskItem,
    RiskScore,
    RiskStatement,
    SourceDocument,
)
from app.models.enums import SourceStatus, SourceType
from app.services.audit import record_audit
from app.services.citation import link_claims_to_snippets
from app.services.dedup import content_hash
from app.services.emerging import EmergingInputs, evaluate_emerging
from app.services.extraction import extract_risk_candidates, extract_text_from_pdf, extract_text_from_url
from app.services.scoring import calculate_composite_score, severity_band


def _derive_fair_factors(candidate_name: str, confidence: float) -> tuple[int, int, int, int]:
    name = candidate_name.lower()
    tef = 4 if any(k in name for k in ["ransomware", "phishing", "compromise"]) else 3
    vulnerability = 3 if confidence < 0.8 else 4
    primary_loss = 4 if any(k in name for k in ["ransomware", "supply", "outage"]) else 3
    secondary_loss = 3
    return tef, vulnerability, primary_loss, secondary_loss


def create_pdf_ingestion(
    db: Session,
    *,
    artifact_path: str,
    title: str,
    publisher: str | None,
    published_at: datetime | None,
    actor: str,
) -> IngestionJob:
    source = SourceDocument(
        type=SourceType.PDF,
        title=title,
        publisher=publisher,
        published_at=published_at,
        artifact_path=artifact_path,
        status=SourceStatus.QUEUED,
    )
    db.add(source)
    db.flush()

    job = IngestionJob(source_document_id=source.id, status=SourceStatus.QUEUED)
    db.add(job)
    record_audit(
        db,
        actor=actor,
        action="ingestion_created_pdf",
        target_type="IngestionJob",
        target_id=str(job.id),
        after_json={"source_document_id": str(source.id)},
    )
    db.commit()
    db.refresh(job)
    return job


def create_url_ingestion(
    db: Session,
    *,
    url: str,
    title: str | None,
    publisher: str | None,
    published_at: datetime | None,
    actor: str,
) -> IngestionJob:
    source = SourceDocument(
        type=SourceType.URL,
        title=title or url,
        publisher=publisher,
        published_at=published_at,
        source_url=url,
        status=SourceStatus.QUEUED,
    )
    db.add(source)
    db.flush()

    job = IngestionJob(source_document_id=source.id, status=SourceStatus.QUEUED)
    db.add(job)
    record_audit(
        db,
        actor=actor,
        action="ingestion_created_url",
        target_type="IngestionJob",
        target_id=str(job.id),
        after_json={"source_document_id": str(source.id), "url": url},
    )
    db.commit()
    db.refresh(job)
    return job


async def process_ingestion_job(db: Session, job_id: str, actor: str = "system") -> IngestionJob:
    job = db.get(IngestionJob, uuid.UUID(job_id))
    if not job:
        raise ValueError(f"Ingestion job {job_id} not found")

    source = job.source_document
    job.status = SourceStatus.PROCESSING
    job.started_at = datetime.utcnow()
    source.status = SourceStatus.PROCESSING
    db.commit()

    try:
        if source.type == SourceType.PDF:
            if not source.artifact_path:
                raise ValueError("Missing artifact path for PDF ingestion")
            extracted = extract_text_from_pdf(source.artifact_path)
        else:
            if not source.source_url:
                raise ValueError("Missing source URL for URL ingestion")
            extracted = await extract_text_from_url(source.source_url)

        normalized_text = extracted.text.strip()
        if not normalized_text:
            raise ValueError("No text could be extracted from source")

        source.title = source.title or extracted.title
        source.publisher = source.publisher or extracted.publisher
        source.published_at = source.published_at or extracted.published_at
        source.content_hash = content_hash(normalized_text)

        # Deduplicate exact matches by content hash.
        existing = db.execute(
            select(SourceDocument).where(
                and_(
                    SourceDocument.id != source.id,
                    SourceDocument.content_hash.is_not(None),
                )
            )
        ).scalars().all()

        for doc in existing:
            if doc.content_hash and doc.content_hash == source.content_hash:
                job.status = SourceStatus.COMPLETED
                job.completed_at = datetime.utcnow()
                source.status = SourceStatus.COMPLETED
                job.error_message = f"Duplicate exact hash of source {doc.id}"
                db.commit()
                return job

        snippet_records: list[EvidenceSnippet] = []
        for snippet in extracted.snippets[:500]:
            snippet_row = EvidenceSnippet(
                source_document_id=source.id,
                text=snippet["text"],
                page_or_dom_ref=snippet["page_or_dom_ref"],
                url=source.source_url,
                confidence=float(snippet.get("confidence", 0.9)),
            )
            db.add(snippet_row)
            snippet_records.append(snippet_row)
        db.flush()

        candidates = extract_risk_candidates(normalized_text)
        if not candidates:
            candidates = extract_risk_candidates("generic threat activity")

        now = datetime.utcnow()
        recent_start = now - timedelta(days=14)
        baseline_start = now - timedelta(days=70)
        baseline_end = recent_start

        for candidate in candidates:
            risk = RiskItem(
                source_document_id=source.id,
                name=candidate.name,
                taxonomy_category=candidate.taxonomy_category,
                threat_actor=candidate.threat_actor,
                affected_sector=candidate.affected_sector,
                affected_assets=candidate.affected_assets,
                extraction_confidence=max(0.0, min(1.0, candidate.confidence)),
            )
            db.add(risk)
            db.flush()

            link_inputs = [{"id": s.id, "text": s.text} for s in snippet_records]
            links = link_claims_to_snippets(candidate.claims, link_inputs)
            citation_ids = sorted({link.snippet_id for link in links})

            for snippet in snippet_records:
                if str(snippet.id) in citation_ids:
                    snippet.risk_item_id = risk.id

            statement = RiskStatement(
                risk_item_id=risk.id,
                business_impact=candidate.business_impact,
                why_care=candidate.why_care,
                time_horizon=candidate.time_horizon,
                recommended_actions=candidate.recommended_actions,
                confidence=candidate.confidence,
                citation_snippet_ids=citation_ids,
            )
            db.add(statement)

            tef, vulnerability, primary_loss, secondary_loss = _derive_fair_factors(
                candidate.name, candidate.confidence
            )
            composite = calculate_composite_score(tef, vulnerability, primary_loss, secondary_loss)
            score_row = RiskScore(
                risk_item_id=risk.id,
                tef=tef,
                vulnerability=vulnerability,
                primary_loss=primary_loss,
                secondary_loss=secondary_loss,
                composite_score=composite,
                severity_band=severity_band(composite),
            )
            db.add(score_row)

            recent_mentions = db.execute(
                select(func.count(RiskItem.id)).where(
                    and_(
                        RiskItem.name == candidate.name,
                        RiskItem.created_at >= recent_start,
                    )
                )
            ).scalar_one()

            baseline_mentions = db.execute(
                select(func.count(RiskItem.id)).where(
                    and_(
                        RiskItem.name == candidate.name,
                        RiskItem.created_at >= baseline_start,
                        RiskItem.created_at < baseline_end,
                    )
                )
            ).scalar_one()

            recent_rows = db.execute(
                select(RiskItem, SourceDocument)
                .join(SourceDocument, RiskItem.source_document_id == SourceDocument.id)
                .where(
                    and_(
                        RiskItem.name == candidate.name,
                        RiskItem.created_at >= recent_start,
                    )
                )
            ).all()
            baseline_rows = db.execute(
                select(RiskItem, SourceDocument)
                .join(SourceDocument, RiskItem.source_document_id == SourceDocument.id)
                .where(
                    and_(
                        RiskItem.name == candidate.name,
                        RiskItem.created_at >= baseline_start,
                        RiskItem.created_at < baseline_end,
                    )
                )
            ).all()

            recent_sectors = [
                sector
                for row in recent_rows
                for sector in (row[0].affected_sector or [])
            ]
            baseline_sectors = [
                sector
                for row in baseline_rows
                for sector in (row[0].affected_sector or [])
            ]

            recent_actor_techniques = [
                f"{row[0].threat_actor or 'unknown'}:{row[0].taxonomy_category}"
                for row in recent_rows
            ]
            baseline_actor_techniques = [
                f"{row[0].threat_actor or 'unknown'}:{row[0].taxonomy_category}"
                for row in baseline_rows
            ]

            recent_publishers = {
                row[1].publisher
                for row in recent_rows
                if row[1].publisher
            }

            emerging = evaluate_emerging(
                EmergingInputs(
                    recent_mentions=recent_mentions,
                    baseline_mentions=baseline_mentions,
                    recent_sectors=recent_sectors,
                    baseline_sectors=baseline_sectors,
                    recent_actor_techniques=recent_actor_techniques,
                    baseline_actor_techniques=baseline_actor_techniques,
                    source_diversity=len(recent_publishers),
                    confidence=candidate.confidence,
                )
            )

            db.add(
                EmergingSignal(
                    risk_item_id=risk.id,
                    trend_ratio=emerging.trend_ratio,
                    novelty_score=emerging.novelty_score,
                    source_diversity=emerging.source_diversity,
                    triggered=emerging.triggered,
                    trigger_reason=emerging.trigger_reason,
                )
            )

        source.status = SourceStatus.COMPLETED
        job.status = SourceStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        record_audit(
            db,
            actor=actor,
            action="ingestion_completed",
            target_type="IngestionJob",
            target_id=str(job.id),
            after_json={"source_document_id": str(source.id), "risk_count": len(candidates)},
        )
        db.commit()
        db.refresh(job)
        return job

    except Exception as exc:
        source.status = SourceStatus.FAILED
        job.status = SourceStatus.FAILED
        job.error_message = str(exc)
        job.completed_at = datetime.utcnow()
        record_audit(
            db,
            actor=actor,
            action="ingestion_failed",
            target_type="IngestionJob",
            target_id=str(job.id),
            after_json={"error": str(exc)},
        )
        db.commit()
        db.refresh(job)
        return job
