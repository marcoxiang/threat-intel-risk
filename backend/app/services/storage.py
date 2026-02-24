from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import UploadFile
from minio import Minio
from minio.error import S3Error

from app.core.config import get_settings


class StorageClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.upload_dir = Path(self.settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        self.minio = Minio(
            endpoint=self.settings.minio_endpoint,
            access_key=self.settings.minio_access_key,
            secret_key=self.settings.minio_secret_key,
            secure=self.settings.minio_secure,
        )
        self.bucket = self.settings.minio_bucket

    def _ensure_bucket(self) -> None:
        try:
            if not self.minio.bucket_exists(self.bucket):
                self.minio.make_bucket(self.bucket)
        except Exception:
            # Allow local fallback if MinIO is not available in dev environments.
            pass

    async def save_upload(self, file: UploadFile, object_key: str) -> str:
        local_path = self.upload_dir / object_key
        local_path.parent.mkdir(parents=True, exist_ok=True)

        with local_path.open("wb") as handle:
            shutil.copyfileobj(file.file, handle)

        self._ensure_bucket()
        try:
            self.minio.fput_object(self.bucket, object_key, str(local_path))
        except (S3Error, OSError):
            pass

        return str(local_path)

    def save_text_blob(self, text: str, object_key: str) -> str:
        local_path = self.upload_dir / object_key
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(text, encoding="utf-8")

        self._ensure_bucket()
        try:
            self.minio.fput_object(self.bucket, object_key, str(local_path))
        except (S3Error, OSError):
            pass

        return str(local_path)


def safe_filename(name: str) -> str:
    keep = [c if c.isalnum() or c in {"-", "_", "."} else "_" for c in name]
    return "".join(keep).strip(".") or "artifact"
