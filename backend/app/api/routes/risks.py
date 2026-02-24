from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_reviewer, require_user
from app.core.security import UserContext
from app.schemas.common import EvidenceSnippetOut, RiskItemOut
from app.schemas.risk import EmergingOverrideRequest
from app.services.risk_service import approve_risk, get_risk, list_risks, override_emerging, reject_risk

router = APIRouter(tags=["risks"])


@router.get("/risks", response_model=list[RiskItemOut])
def get_risks(
    status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    emerging: bool | None = Query(default=None),
    category: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_user),
) -> list[RiskItemOut]:
    items = list_risks(
        db,
        status_filter=status,
        severity=severity,
        emerging=emerging,
        category=category,
    )
    return [RiskItemOut.model_validate(item) for item in items]


@router.get("/risks/{risk_id}")
def get_risk_detail(
    risk_id: str,
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_user),
) -> dict:
    risk = get_risk(db, risk_id)
    return {
        "risk": RiskItemOut.model_validate(risk),
        "evidence": [EvidenceSnippetOut.model_validate(e) for e in risk.evidence_snippets],
    }


@router.post("/risks/{risk_id}/approve", response_model=RiskItemOut)
def approve(
    risk_id: str,
    db: Session = Depends(get_db),
    reviewer: UserContext = Depends(require_reviewer),
) -> RiskItemOut:
    risk = approve_risk(db, risk_id, actor=reviewer.username)
    return RiskItemOut.model_validate(risk)


@router.post("/risks/{risk_id}/reject", response_model=RiskItemOut)
def reject(
    risk_id: str,
    db: Session = Depends(get_db),
    reviewer: UserContext = Depends(require_reviewer),
) -> RiskItemOut:
    risk = reject_risk(db, risk_id, actor=reviewer.username)
    return RiskItemOut.model_validate(risk)


@router.post("/risks/{risk_id}/override-emerging", response_model=RiskItemOut)
def override(
    risk_id: str,
    payload: EmergingOverrideRequest,
    db: Session = Depends(get_db),
    reviewer: UserContext = Depends(require_reviewer),
) -> RiskItemOut:
    risk = override_emerging(
        db,
        risk_id=risk_id,
        triggered=payload.triggered,
        reason=payload.reason,
        actor=reviewer.username,
    )
    return RiskItemOut.model_validate(risk)
