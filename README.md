# ThreatIntelRisk v1

ThreatIntelRisk is an internal threat-intelligence web application that:
- Ingests PDF reports and analyst-submitted web URLs
- Extracts evidence snippets with strict citation linkage
- Drafts business risk statements with FAIR-lite scoring
- Auto-tags rising issues as **Emerging Risks** using trend + novelty logic
- Enforces analyst review gates before risk publication

## Stack
- Frontend: Next.js (TypeScript)
- Backend API: FastAPI
- Worker: Celery + Redis
- Database: PostgreSQL (pgvector image)
- Object storage: MinIO
- Reverse proxy: Caddy

## Quickstart (Docker)
1. Copy environment defaults:
   ```bash
   cp .env.example .env
   ```
2. Start all services:
   ```bash
   docker compose --env-file .env up --build
   ```
3. Open:
   - Frontend: `http://localhost:3000`
   - API docs: `http://localhost:8000/docs`
   - Caddy entrypoint: `http://localhost`

Note: when running in Docker, server-rendered frontend pages use `API_INTERNAL_URL` (defaults to `http://api:8000/api/v1` in compose), while browser-side calls use `NEXT_PUBLIC_API_URL`.

## API Authentication Model (v1)
Use headers on all API calls:
- `X-User: <username>`
- `X-Role: Analyst | Reviewer | Admin`

## Key Endpoints
- `POST /api/v1/sources/pdf`
- `POST /api/v1/sources/url`
- `GET /api/v1/ingestions/{id}`
- `GET /api/v1/risks`
- `GET /api/v1/risks/{id}`
- `POST /api/v1/risks/{id}/approve`
- `POST /api/v1/risks/{id}/reject`
- `POST /api/v1/risks/{id}/override-emerging`
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/dashboard/emerging`
- `GET /api/v1/exports/risks.csv`
- `GET /api/v1/exports/risk/{id}.pdf`

## FAIR-lite Scoring
`score = 20 * (0.30*TEF + 0.25*Vulnerability + 0.30*PrimaryLoss + 0.15*SecondaryLoss)`

Severity bands:
- 0-39 Low
- 40-59 Moderate
- 60-79 High
- 80-100 Critical

## Emerging Risk Trigger
A risk auto-tags as emerging when all conditions hold:
- `trend_ratio >= 1.8`
- `novelty_score >= 0.35`
- `source_diversity >= 3`
- extraction confidence `>= 0.70`

Analysts can override with required rationale.

## Testing
Run backend tests locally:
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest
```

## Notes
- PDF OCR fallback requires `tesseract`.
- URL ingestion uses readability extraction from fetched HTML.
- If `OPENAI_API_KEY` is absent, the system falls back to deterministic heuristic extraction.
