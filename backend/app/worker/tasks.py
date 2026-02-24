import asyncio

from app.core.database import SessionLocal
from app.services.ingestion_service import process_ingestion_job
from app.worker.celery_app import celery_app


@celery_app.task(name="app.worker.tasks.process_ingestion")
def process_ingestion(job_id: str) -> None:
    db = SessionLocal()
    try:
        asyncio.run(process_ingestion_job(db, job_id=job_id, actor="celery-worker"))
    finally:
        db.close()
