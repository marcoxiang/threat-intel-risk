from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.orm import Session, joinedload

from app.models.entities import EmergingSignal, RiskItem
from app.models.enums import RiskStatus
from app.services.audit import record_audit


def list_risks(
    db: Session,
    *,
    status_filter: str | None = None,
    severity: str | None = None,
    emerging: bool | None = None,
    category: str | None = None,
) -> list[RiskItem]:
    stmt = (
        select(RiskItem)
        .options(
            joinedload(RiskItem.statement),
            joinedload(RiskItem.score),
            joinedload(RiskItem.emerging_signal),
        )
        .order_by(RiskItem.created_at.desc())
    )

    filters = []
    if status_filter:
        try:
            filters.append(RiskItem.status == RiskStatus(status_filter))
        except ValueError:
            pass
    if category:
        filters.append(RiskItem.taxonomy_category == category)

    if filters:
        stmt = stmt.where(and_(*filters))

    items = db.execute(stmt).scalars().all()

    if severity:
        items = [item for item in items if item.score and item.score.severity_band.value == severity]
    if emerging is not None:
        items = [item for item in items if item.emerging_signal and item.emerging_signal.triggered == emerging]

    return items


def get_risk(db: Session, risk_id: str) -> RiskItem:
    stmt = (
        select(RiskItem)
        .where(RiskItem.id == uuid.UUID(risk_id))
        .options(
            joinedload(RiskItem.statement),
            joinedload(RiskItem.score),
            joinedload(RiskItem.emerging_signal),
            joinedload(RiskItem.evidence_snippets),
        )
    )
    risk = db.execute(stmt).scalars().first()
    if not risk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk not found")
    return risk


def approve_risk(db: Session, risk_id: str, actor: str) -> RiskItem:
    risk = get_risk(db, risk_id)
    if not risk.statement:
        raise HTTPException(status_code=400, detail="Risk statement is missing")
    if not risk.statement.citation_snippet_ids:
        raise HTTPException(status_code=400, detail="Approval blocked: citations are required")
    evidence_ids = {str(snippet.id) for snippet in risk.evidence_snippets}
    if not set(risk.statement.citation_snippet_ids).issubset(evidence_ids):
        raise HTTPException(
            status_code=400,
            detail="Approval blocked: citations must reference existing evidence snippets",
        )

    before = {"status": risk.status.value}
    risk.status = RiskStatus.APPROVED
    risk.statement.approved_by = actor
    risk.statement.approved_at = datetime.utcnow()
    record_audit(
        db,
        actor=actor,
        action="risk_approved",
        target_type="RiskItem",
        target_id=str(risk.id),
        before_json=before,
        after_json={"status": risk.status.value},
    )
    db.commit()
    db.refresh(risk)
    return risk


def reject_risk(db: Session, risk_id: str, actor: str) -> RiskItem:
    risk = get_risk(db, risk_id)
    before = {"status": risk.status.value}
    risk.status = RiskStatus.REJECTED
    record_audit(
        db,
        actor=actor,
        action="risk_rejected",
        target_type="RiskItem",
        target_id=str(risk.id),
        before_json=before,
        after_json={"status": risk.status.value},
    )
    db.commit()
    db.refresh(risk)
    return risk


def override_emerging(db: Session, risk_id: str, triggered: bool, reason: str, actor: str) -> RiskItem:
    risk = get_risk(db, risk_id)
    if not risk.emerging_signal:
        risk.emerging_signal = EmergingSignal(
            risk_item_id=risk.id,
            trend_ratio=0.0,
            novelty_score=0.0,
            source_diversity=0,
            triggered=triggered,
            trigger_reason=reason,
        )
    else:
        risk.emerging_signal.triggered = triggered
        risk.emerging_signal.trigger_reason = f"manual_override:{reason}"
        risk.emerging_signal.evaluated_at = datetime.utcnow()

    record_audit(
        db,
        actor=actor,
        action="emerging_override",
        target_type="RiskItem",
        target_id=str(risk.id),
        after_json={"triggered": triggered, "reason": reason},
    )
    db.commit()
    db.refresh(risk)
    return risk
