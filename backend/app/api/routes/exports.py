from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_user
from app.core.security import UserContext
from app.services.export_service import risk_to_pdf, risks_to_csv
from app.services.risk_service import get_risk, list_risks

router = APIRouter(tags=["exports"])


@router.get("/exports/risks.csv")
def export_risks_csv(
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_user),
) -> Response:
    risks = list_risks(db)
    csv_body = risks_to_csv(risks)
    return Response(
        content=csv_body,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=risks.csv"},
    )


@router.get("/exports/risk/{risk_id}.pdf")
def export_risk_pdf(
    risk_id: str,
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_user),
) -> Response:
    risk = get_risk(db, risk_id)
    pdf = risk_to_pdf(risk)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=risk-{risk_id}.pdf"},
    )
