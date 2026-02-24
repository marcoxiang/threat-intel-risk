from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    total_risks: int
    draft_risks: int
    approved_risks: int
    rejected_risks: int
    emerging_risks: int
    severity_breakdown: dict[str, int]
