from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_user
from app.core.security import UserContext
from app.schemas.common import RiskItemOut
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard_service import emerging_risks, summary

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/summary", response_model=DashboardSummaryResponse)
def get_summary(
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_user),
) -> DashboardSummaryResponse:
    return DashboardSummaryResponse.model_validate(summary(db))


@router.get("/dashboard/emerging", response_model=list[RiskItemOut])
def get_emerging(
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_user),
) -> list[RiskItemOut]:
    items = emerging_risks(db)
    return [RiskItemOut.model_validate(item) for item in items]
