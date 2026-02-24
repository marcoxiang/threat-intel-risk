from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest

from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.exports import router as exports_router
from app.api.routes.ingestion import router as ingestion_router
from app.api.routes.risks import router as risks_router
from app.core.config import get_settings
from app.core.database import Base, engine

# Import models so metadata is complete for create_all.
from app.models import entities as _entities  # noqa: F401

settings = get_settings()
app = FastAPI(title=settings.app_name)

REQUEST_COUNTER = Counter("threatintel_api_requests_total", "Total API requests", ["route", "method"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.middleware("http")
async def collect_metrics(request, call_next):
    response = await call_next(request)
    REQUEST_COUNTER.labels(route=request.url.path, method=request.method).inc()
    return response


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.include_router(ingestion_router, prefix=settings.api_prefix)
app.include_router(risks_router, prefix=settings.api_prefix)
app.include_router(dashboard_router, prefix=settings.api_prefix)
app.include_router(exports_router, prefix=settings.api_prefix)
