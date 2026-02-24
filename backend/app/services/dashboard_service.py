from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.entities import EmergingSignal, RiskItem, RiskScore
from app.models.enums import RiskStatus, SeverityBand


def summary(db: Session) -> dict:
    total = db.execute(select(func.count(RiskItem.id))).scalar_one()
    draft = db.execute(select(func.count(RiskItem.id)).where(RiskItem.status == RiskStatus.DRAFT)).scalar_one()
    approved = db.execute(select(func.count(RiskItem.id)).where(RiskItem.status == RiskStatus.APPROVED)).scalar_one()
    rejected = db.execute(select(func.count(RiskItem.id)).where(RiskItem.status == RiskStatus.REJECTED)).scalar_one()

    emerging_count = db.execute(
        select(func.count(EmergingSignal.id)).where(EmergingSignal.triggered.is_(True))
    ).scalar_one()

    severity_breakdown = {}
    for band in SeverityBand:
        severity_breakdown[band.value] = db.execute(
            select(func.count(RiskScore.id)).where(RiskScore.severity_band == band)
        ).scalar_one()

    return {
        "total_risks": total,
        "draft_risks": draft,
        "approved_risks": approved,
        "rejected_risks": rejected,
        "emerging_risks": emerging_count,
        "severity_breakdown": severity_breakdown,
    }


def emerging_risks(db: Session) -> list[RiskItem]:
    return (
        db.execute(
            select(RiskItem)
            .join(RiskItem.emerging_signal)
            .options(
                joinedload(RiskItem.statement),
                joinedload(RiskItem.score),
                joinedload(RiskItem.emerging_signal),
            )
            .where(EmergingSignal.triggered.is_(True))
            .order_by(EmergingSignal.novelty_score.desc(), EmergingSignal.trend_ratio.desc())
        )
        .scalars()
        .all()
    )
