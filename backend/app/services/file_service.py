import re
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import Settings
from app.exceptions import InvalidFileError

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".csv", ".xlsx", ".xls", ".docx"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "text/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/octet-stream",
}


class FileService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.upload_path = settings.upload_path
        self.upload_path.mkdir(parents=True, exist_ok=True)

    def validate_upload(self, file: UploadFile, content: bytes) -> None:
        if not file.filename:
            raise InvalidFileError("Filename is required.")

        extension = Path(file.filename).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise InvalidFileError(
                f"Unsupported file type '{extension}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

        if len(content) == 0:
            raise InvalidFileError("Uploaded file is empty.")

        if len(content) > self.settings.max_upload_size_bytes:
            raise InvalidFileError(
                f"File exceeds maximum size of {self.settings.max_upload_size_mb} MB."
            )

        if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
            # Allow if extension is valid even when MIME is generic
            if extension not in ALLOWED_EXTENSIONS:
                raise InvalidFileError(f"Unsupported content type: {file.content_type}")

    def save_upload(self, file: UploadFile, content: bytes) -> tuple[str, str, str]:
        self.validate_upload(file, content)
        extension = Path(file.filename).suffix.lower()
        stored_name = f"{uuid.uuid4().hex}{extension}"
        destination = self.upload_path / stored_name
        destination.write_bytes(content)
        return stored_name, str(destination), extension.lstrip(".")

    def delete_file(self, file_path: str) -> None:
        path = Path(file_path)
        if path.exists() and path.is_file():
            path.unlink()
