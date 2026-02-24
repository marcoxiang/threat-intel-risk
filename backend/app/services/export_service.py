from __future__ import annotations

import csv
import io
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.models.entities import RiskItem


def risks_to_csv(risks: list[RiskItem]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "risk_id",
            "name",
            "category",
            "status",
            "severity",
            "emerging",
            "business_impact",
            "why_care",
            "approved_by",
            "approved_at",
        ]
    )

    for risk in risks:
        writer.writerow(
            [
                str(risk.id),
                risk.name,
                risk.taxonomy_category,
                risk.status.value,
                risk.score.severity_band.value if risk.score else "",
                str(risk.emerging_signal.triggered) if risk.emerging_signal else "False",
                risk.statement.business_impact if risk.statement else "",
                risk.statement.why_care if risk.statement else "",
                risk.statement.approved_by if risk.statement else "",
                risk.statement.approved_at.isoformat() if risk.statement and risk.statement.approved_at else "",
            ]
        )

    return buf.getvalue()


def risk_to_pdf(risk: RiskItem) -> bytes:
    stream = io.BytesIO()
    pdf = canvas.Canvas(stream, pagesize=letter)
    y = 760

    def write_line(text: str, step: int = 18) -> None:
        nonlocal y
        pdf.drawString(50, y, text[:110])
        y -= step

    write_line("ThreatIntelRisk - Risk Statement")
    write_line(f"Generated: {datetime.utcnow().isoformat()} UTC")
    y -= 10
    write_line(f"Risk: {risk.name}")
    write_line(f"Category: {risk.taxonomy_category}")
    write_line(f"Status: {risk.status.value}")
    write_line(f"Emerging Risk: {risk.emerging_signal.triggered if risk.emerging_signal else False}")
    if risk.score:
        write_line(f"FAIR-lite Score: {risk.score.composite_score} ({risk.score.severity_band.value})")

    if risk.statement:
        y -= 8
        write_line("Why business should care:")
        write_line(risk.statement.why_care, step=16)
        y -= 4
        write_line("Business impact:")
        write_line(risk.statement.business_impact, step=16)

        y -= 4
        write_line("Recommended actions:")
        for action in risk.statement.recommended_actions[:6]:
            write_line(f"- {action}", step=16)

        y -= 4
        write_line(f"Citation IDs: {', '.join(risk.statement.citation_snippet_ids[:8])}")

    pdf.showPage()
    pdf.save()
    return stream.getvalue()
