from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_user
from app.core.config import get_settings
from app.core.security import UserContext
from app.models.entities import IngestionJob
from app.schemas.common import IngestionJobOut
from app.schemas.ingestion import IngestionCreateResponse, URLIngestionRequest
from app.services.ingestion_service import create_pdf_ingestion, create_url_ingestion, process_ingestion_job
from app.services.storage import StorageClient, safe_filename
from app.worker.tasks import process_ingestion

router = APIRouter(tags=["ingestion"])


@router.post("/sources/pdf", response_model=IngestionCreateResponse)
async def ingest_pdf(
    file: UploadFile = File(...),
    title: str = Form("Untitled PDF report"),
    publisher: str | None = Form(default=None),
    published_at: datetime | None = Form(default=None),
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_user),
) -> IngestionCreateResponse:
    storage = StorageClient()
    object_key = f"pdf/{uuid.uuid4()}_{safe_filename(file.filename or 'report.pdf')}"
    path = await storage.save_upload(file, object_key)

    job = create_pdf_ingestion(
        db,
        artifact_path=path,
        title=title,
        publisher=publisher,
        published_at=published_at,
        actor=user.username,
    )

    settings = get_settings()
    if settings.ingestion_sync:
        job = await process_ingestion_job(db, job_id=str(job.id), actor=user.username)
    else:
        process_ingestion.delay(str(job.id))

    return IngestionCreateResponse(
        ingestion_id=str(job.id),
        source_document_id=str(job.source_document_id),
        status=job.status.value,
    )


@router.post("/sources/url", response_model=IngestionCreateResponse)
async def ingest_url(
    payload: URLIngestionRequest,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_user),
) -> IngestionCreateResponse:
    job = create_url_ingestion(
        db,
        url=str(payload.url),
        title=payload.title,
        publisher=payload.publisher,
        published_at=payload.published_at,
        actor=user.username,
    )

    settings = get_settings()
    if settings.ingestion_sync:
        job = await process_ingestion_job(db, job_id=str(job.id), actor=user.username)
    else:
        process_ingestion.delay(str(job.id))

    return IngestionCreateResponse(
        ingestion_id=str(job.id),
        source_document_id=str(job.source_document_id),
        status=job.status.value,
    )


@router.get("/ingestions/{ingestion_id}", response_model=IngestionJobOut)
def get_ingestion_status(ingestion_id: str, db: Session = Depends(get_db)) -> IngestionJobOut:
    job = db.get(IngestionJob, uuid.UUID(ingestion_id))
    if not job:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Ingestion job not found")
    return IngestionJobOut.model_validate(job)


@router.get("/ingestions", response_model=list[IngestionJobOut])
def list_ingestions(
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_user),
) -> list[IngestionJobOut]:
    jobs = db.execute(select(IngestionJob).order_by(IngestionJob.created_at.desc()).limit(200)).scalars().all()
    return [IngestionJobOut.model_validate(j) for j in jobs]
