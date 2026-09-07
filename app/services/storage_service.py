"""
Storage abstraction layer.

During development, files are saved to the local filesystem under the
`media/` directory. The interface is deliberately small so a different
backend (e.g. AWS S3 + CloudFront) can be dropped in later without
touching any route code -- only `StorageService` needs a new
implementation.
"""

from __future__ import annotations

import os
import uuid
from abc import ABC, abstractmethod

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


class BaseStorageService(ABC):
    """Interface every storage backend must implement."""

    @abstractmethod
    def save(self, file: FileStorage, subfolder: str) -> str:
        """Persist `file` under `subfolder` and return a public URL/path."""

    @abstractmethod
    def delete(self, url: str) -> None:
        """Remove a previously stored file given its stored URL/path."""


class LocalStorageService(BaseStorageService):
    """Stores files on the local disk under `UPLOAD_FOLDER`."""

    def __init__(self, upload_folder: str):
        self.upload_folder = upload_folder

    def _unique_filename(self, original_name: str) -> str:
        safe_name = secure_filename(original_name)
        ext = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
        unique_id = uuid.uuid4().hex[:12]
        return f"{unique_id}.{ext}" if ext else unique_id

    def save(self, file: FileStorage, subfolder: str) -> str:
        target_dir = os.path.join(self.upload_folder, subfolder)
        os.makedirs(target_dir, exist_ok=True)

        filename = self._unique_filename(file.filename or "upload")
        full_path = os.path.join(target_dir, filename)
        file.save(full_path)

        # Public-facing relative URL served via /media/<subfolder>/<filename>
        return f"/media/{subfolder}/{filename}"

    def delete(self, url: str) -> None:
        if not url or not url.startswith("/media/"):
            return
        relative_path = url[len("/media/"):]
        full_path = os.path.join(self.upload_folder, relative_path)
        if os.path.isfile(full_path):
            try:
                os.remove(full_path)
            except OSError:
                pass


class S3StorageService(BaseStorageService):
    """
    Placeholder for a future AWS S3 / CloudFront backed implementation.

    Swapping to this backend only requires implementing `save`/`delete`
    using boto3 and updating `get_storage_service` below -- no route or
    template code needs to change because they only depend on the
    `BaseStorageService` interface.
    """

    def __init__(self, bucket_name: str, cdn_base_url: str | None = None):
        self.bucket_name = bucket_name
        self.cdn_base_url = cdn_base_url

    def save(self, file: FileStorage, subfolder: str) -> str:  # pragma: no cover
        raise NotImplementedError("Configure boto3 credentials to enable S3 storage.")

    def delete(self, url: str) -> None:  # pragma: no cover
        raise NotImplementedError("Configure boto3 credentials to enable S3 storage.")


def get_storage_service(upload_folder: str) -> BaseStorageService:
    """Factory returning the active storage backend.

    Reads `STORAGE_BACKEND` from the environment ("local" or "s3") so
    production deployments can switch backends purely via configuration.
    """
    backend = os.environ.get("STORAGE_BACKEND", "local").lower()
    if backend == "s3":
        bucket = os.environ.get("S3_BUCKET_NAME", "")
        cdn = os.environ.get("CLOUDFRONT_URL")
        return S3StorageService(bucket, cdn)
    return LocalStorageService(upload_folder)


def allowed_file(filename: str, allowed_extensions: set[str]) -> bool:
    """Validate a filename's extension against an allow-list."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in allowed_extensions
    )
