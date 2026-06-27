"""Track uploaded files so reports can be restored if the database is reset."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


class StorageManifest:
    def __init__(self, path: Path):
        self.path = path

    def _load(self) -> list[dict]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
        return data if isinstance(data, list) else []

    def _save(self, entries: list[dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")

    def upsert_report(self, entry: dict) -> None:
        entries = self._load()
        file_path = entry["file_path"]
        entries = [item for item in entries if item.get("file_path") != file_path]
        entries.append(entry)
        self._save(entries)

    def remove_report(self, file_path: str) -> None:
        entries = [item for item in self._load() if item.get("file_path") != file_path]
        self._save(entries)

    def list_reports(self) -> list[dict]:
        return self._load()


def build_manifest_entry(
    *,
    report_id: int,
    filename: str,
    original_filename: str,
    file_path: str,
    file_type: str,
    file_size: int,
    status: str,
    created_at: datetime,
) -> dict:
    return {
        "report_id": report_id,
        "filename": filename,
        "original_filename": original_filename,
        "file_path": file_path,
        "file_type": file_type,
        "file_size": file_size,
        "status": status,
        "created_at": created_at.isoformat(),
    }
