from datetime import datetime

from pydantic import BaseModel, HttpUrl


class URLIngestionRequest(BaseModel):
    url: HttpUrl
    title: str | None = None
    publisher: str | None = None
    published_at: datetime | None = None
    notes: str | None = None


class IngestionCreateResponse(BaseModel):
    ingestion_id: str
    source_document_id: str
    status: str
