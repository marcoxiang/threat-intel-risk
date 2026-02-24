from __future__ import annotations

import io
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import httpx
import fitz
from bs4 import BeautifulSoup
from readability import Document

try:
    import pytesseract
    from PIL import Image
except Exception:  # pragma: no cover - optional runtime dependency
    pytesseract = None
    Image = None

from openai import OpenAI

from app.core.config import get_settings

try:
    from playwright.async_api import async_playwright
except Exception:  # pragma: no cover - optional runtime dependency
    async_playwright = None


@dataclass
class ExtractedContent:
    title: str
    publisher: str | None
    published_at: datetime | None
    text: str
    snippets: list[dict[str, Any]]


@dataclass
class RiskCandidate:
    name: str
    taxonomy_category: str
    threat_actor: str | None
    affected_sector: list[str]
    affected_assets: list[str]
    summary: str
    business_impact: str
    why_care: str
    time_horizon: str
    recommended_actions: list[str]
    confidence: float
    claims: list[str]


DEFAULT_ACTIONS = [
    "Harden exposed internet-facing services and enforce MFA",
    "Review and patch vulnerable assets referenced by this threat pattern",
    "Run tabletop incident scenario for affected business process",
]


def _redact_pii(text: str) -> str:
    text = re.sub(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", "[REDACTED_EMAIL]", text)
    text = re.sub(r"\b\+?\d[\d\-\s]{7,}\b", "[REDACTED_PHONE]", text)
    return text


def _split_snippets(text: str, ref_prefix: str) -> list[dict[str, Any]]:
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    snippets = []
    for i, paragraph in enumerate(paragraphs[:300], start=1):
        snippets.append(
            {
                "text": paragraph[:2000],
                "page_or_dom_ref": f"{ref_prefix}:{i}",
                "confidence": 0.9,
            }
        )
    return snippets


def extract_text_from_pdf(path: str) -> ExtractedContent:
    doc = fitz.open(path)
    texts: list[str] = []
    snippets: list[dict[str, Any]] = []

    for i, page in enumerate(doc, start=1):
        content = page.get_text("text").strip()
        if not content and pytesseract and Image:
            pix = page.get_pixmap()
            image = Image.open(io.BytesIO(pix.tobytes("png")))
            content = pytesseract.image_to_string(image).strip()
        if content:
            texts.append(content)
            snippets.append(
                {
                    "text": content[:2500],
                    "page_or_dom_ref": f"page:{i}",
                    "confidence": 0.9 if page.get_text("text").strip() else 0.75,
                }
            )

    full_text = "\n\n".join(texts).strip()
    if not snippets and full_text:
        snippets = _split_snippets(full_text, "page")

    metadata = doc.metadata or {}
    title = metadata.get("title") or "Untitled PDF report"
    publisher = metadata.get("author")

    return ExtractedContent(
        title=title,
        publisher=publisher,
        published_at=None,
        text=_redact_pii(full_text),
        snippets=snippets,
    )


async def extract_text_from_url(url: str) -> ExtractedContent:
    raw_html: str | None = None
    if async_playwright is not None:
        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle", timeout=30000)
                raw_html = await page.content()
                await browser.close()
        except Exception:
            raw_html = None

    if raw_html is None:
        try:
            async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            message = str(exc).lower()
            if "certificate verify failed" not in message:
                raise

            # Fallback for environments with missing/intercepted CA roots.
            async with httpx.AsyncClient(timeout=25.0, follow_redirects=True, verify=False) as insecure_client:
                response = await insecure_client.get(url)
                response.raise_for_status()
        raw_html = response.text
    doc = Document(raw_html)
    summary_html = doc.summary(html_partial=True)
    soup = BeautifulSoup(summary_html, "html.parser")
    text = soup.get_text("\n", strip=True)
    if len(text) < 300:
        fallback_soup = BeautifulSoup(raw_html, "html.parser")
        text = fallback_soup.get_text("\n", strip=True)

    parsed = urlparse(url)
    publisher = parsed.netloc
    short_title = doc.short_title()
    html_title = soup.title.string if soup.title else None
    title = short_title or html_title or url

    return ExtractedContent(
        title=title,
        publisher=publisher,
        published_at=None,
        text=_redact_pii(text),
        snippets=_split_snippets(text, "dom"),
    )


def _heuristic_candidates(text: str) -> list[RiskCandidate]:
    lower = text.lower()

    taxonomy = "Cyber Threat"
    name = "General Cyber Threat Escalation"
    actor = None
    sectors: list[str] = []
    assets: list[str] = []

    if "ransomware" in lower:
        taxonomy = "Ransomware"
        name = "Ransomware Campaign Expansion"
        assets.extend(["Endpoints", "File servers", "Backup systems"])
    if "phishing" in lower:
        taxonomy = "Phishing"
        name = "Credential Theft via Phishing"
        assets.extend(["Identity providers", "Email infrastructure"])
    if "supply chain" in lower:
        taxonomy = "Supply Chain"
        name = "Third-Party Software Supply Chain Compromise"
        assets.extend(["Build systems", "Software repositories"])

    for sector in ["finance", "health", "energy", "retail", "government", "manufacturing"]:
        if sector in lower:
            sectors.append(sector.title())
    if not sectors:
        sectors.append("Cross-Sector")

    actor_match = re.search(r"\b(apt\s*\d+|lazarus|lockbit|clop|sandworm)\b", lower)
    if actor_match:
        actor = actor_match.group(1).upper()

    lines = [line.strip() for line in text.split(".") if len(line.strip()) > 40]
    claims = lines[:4] if lines else ["Threat activity is increasing and impacting business operations."]

    return [
        RiskCandidate(
            name=name,
            taxonomy_category=taxonomy,
            threat_actor=actor,
            affected_sector=sorted(set(sectors)),
            affected_assets=sorted(set(assets)) if assets else ["Core business applications"],
            summary=claims[0][:240],
            business_impact="Potential downtime, service disruption, and unplanned recovery costs.",
            why_care="This threat can interrupt revenue-generating operations and increase regulatory exposure.",
            time_horizon="0-90 days",
            recommended_actions=DEFAULT_ACTIONS,
            confidence=0.72,
            claims=claims,
        )
    ]


def extract_risk_candidates(text: str) -> list[RiskCandidate]:
    settings = get_settings()
    if not settings.openai_api_key:
        return _heuristic_candidates(text)

    schema_hint = {
        "type": "object",
        "properties": {
            "risks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "taxonomy_category": {"type": "string"},
                        "threat_actor": {"type": ["string", "null"]},
                        "affected_sector": {"type": "array", "items": {"type": "string"}},
                        "affected_assets": {"type": "array", "items": {"type": "string"}},
                        "summary": {"type": "string"},
                        "business_impact": {"type": "string"},
                        "why_care": {"type": "string"},
                        "time_horizon": {"type": "string"},
                        "recommended_actions": {"type": "array", "items": {"type": "string"}},
                        "confidence": {"type": "number"},
                        "claims": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": [
                        "name",
                        "taxonomy_category",
                        "affected_sector",
                        "affected_assets",
                        "business_impact",
                        "why_care",
                        "time_horizon",
                        "recommended_actions",
                        "confidence",
                        "claims",
                    ],
                },
            }
        },
        "required": ["risks"],
    }

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {
                    "role": "system",
                    "content": "Extract cyber risk candidates for business risk statements. Return strict JSON.",
                },
                {
                    "role": "user",
                    "content": f"Schema: {schema_hint}\n\nText:\n{text[:12000]}",
                },
            ],
            max_output_tokens=1800,
            temperature=0.1,
        )

        raw = response.output_text
        import json

        payload = json.loads(raw)
        risks: list[RiskCandidate] = []
        for item in payload.get("risks", []):
            risks.append(RiskCandidate(**item))
        return risks if risks else _heuristic_candidates(text)
    except Exception:
        return _heuristic_candidates(text)
