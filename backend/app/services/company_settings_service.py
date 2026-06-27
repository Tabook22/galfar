"""Persist company branding and profile information."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import Settings
from app.exceptions import AppError, InvalidFileError

ALLOWED_LOGO_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
MAX_LOGO_BYTES = 2 * 1024 * 1024

BILINGUAL_KEYS = (
    "company_name",
    "page_title",
    "tagline",
    "address",
    "industry",
    "history",
    "introduction_html",
)

DEFAULT_BILINGUAL = {"ar": "", "en": ""}

DEFAULT_SETTINGS: dict[str, Any] = {
    "company_name": {"ar": "جلفار", "en": "Galfar"},
    "page_title": {
        "ar": "جلفار — محلل التقارير المالية",
        "en": "Galfar — Financial Report Analyzer",
    },
    "tagline": dict(DEFAULT_BILINGUAL),
    "logo_filename": None,
    "address": dict(DEFAULT_BILINGUAL),
    "industry": dict(DEFAULT_BILINGUAL),
    "history": dict(DEFAULT_BILINGUAL),
    "introduction_html": dict(DEFAULT_BILINGUAL),
    "phone": "",
    "email": "",
    "website": "",
    "updated_at": None,
}


class CompanySettingsService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def get_settings(self) -> dict:
        data = self._read_raw()
        return self._to_response(data)

    def update_settings(self, updates: dict) -> dict:
        data = self._read_raw()

        for key in BILINGUAL_KEYS:
            if key in updates and updates[key] is not None:
                data[key] = self._normalize_bilingual(updates[key], data.get(key))

        for key in ("phone", "email", "website"):
            if key in updates and updates[key] is not None:
                data[key] = updates[key]

        data["updated_at"] = datetime.utcnow().isoformat()
        self._write_raw(data)
        return self._to_response(data)

    def save_logo(self, content: bytes, original_filename: str) -> dict:
        if len(content) > MAX_LOGO_BYTES:
            raise InvalidFileError("Logo must be 2 MB or smaller.")

        ext = Path(original_filename or "").suffix.lower()
        if ext not in ALLOWED_LOGO_EXTENSIONS:
            raise InvalidFileError("Logo must be PNG, JPG, GIF, WebP, or SVG.")

        logo_dir = self.settings.company_logo_dir
        logo_dir.mkdir(parents=True, exist_ok=True)
        self._remove_logo_files(logo_dir)

        safe_name = f"logo{ext}"
        (logo_dir / safe_name).write_bytes(content)

        data = self._read_raw()
        data["logo_filename"] = safe_name
        data["updated_at"] = datetime.utcnow().isoformat()
        self._write_raw(data)
        return self._to_response(data)

    def delete_logo(self) -> dict:
        data = self._read_raw()
        self._remove_logo_files(self.settings.company_logo_dir)
        data["logo_filename"] = None
        data["updated_at"] = datetime.utcnow().isoformat()
        self._write_raw(data)
        return self._to_response(data)

    def get_logo_path(self) -> Path | None:
        data = self._read_raw()
        filename = data.get("logo_filename")
        if not filename:
            return None
        path = self.settings.company_logo_dir / filename
        return path if path.is_file() else None

    def _read_raw(self) -> dict:
        path = self.settings.company_settings_file
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            return self._copy_defaults()
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise AppError("Company settings file is corrupted.", 500) from exc
        return self._normalize_storage(loaded if isinstance(loaded, dict) else {})

    def _copy_defaults(self) -> dict:
        data = json.loads(json.dumps(DEFAULT_SETTINGS))
        for key in BILINGUAL_KEYS:
            data[key] = dict(data[key])
        return data

    def _normalize_storage(self, loaded: dict) -> dict:
        data = self._copy_defaults()
        data.update({k: v for k, v in loaded.items() if k in DEFAULT_SETTINGS or k == "logo_filename"})

        for key in BILINGUAL_KEYS:
            value = loaded.get(key, data.get(key))
            if isinstance(value, str):
                data[key] = {"ar": "", "en": value}
            elif isinstance(value, dict):
                data[key] = self._normalize_bilingual(value, data.get(key))
            else:
                data[key] = dict(DEFAULT_BILINGUAL)

        for key in ("phone", "email", "website"):
            if key in loaded and isinstance(loaded[key], str):
                data[key] = loaded[key]

        if "logo_filename" in loaded:
            data["logo_filename"] = loaded["logo_filename"]
        if "updated_at" in loaded:
            data["updated_at"] = loaded["updated_at"]

        return data

    def _normalize_bilingual(self, value: dict, fallback: Any = None) -> dict:
        base = dict(DEFAULT_BILINGUAL)
        if isinstance(fallback, dict):
            base["ar"] = str(fallback.get("ar") or "")
            base["en"] = str(fallback.get("en") or "")
        if isinstance(value, dict):
            if value.get("ar") is not None:
                base["ar"] = str(value.get("ar") or "")
            if value.get("en") is not None:
                base["en"] = str(value.get("en") or "")
        return base

    def _write_raw(self, data: dict) -> None:
        path = self.settings.company_settings_file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _to_response(self, data: dict) -> dict:
        logo_url = "/api/settings/company/logo" if data.get("logo_filename") else None
        return {
            "company_name": self._normalize_bilingual(data.get("company_name"), DEFAULT_SETTINGS["company_name"]),
            "page_title": self._normalize_bilingual(data.get("page_title"), DEFAULT_SETTINGS["page_title"]),
            "tagline": self._normalize_bilingual(data.get("tagline")),
            "logo_url": logo_url,
            "address": self._normalize_bilingual(data.get("address")),
            "industry": self._normalize_bilingual(data.get("industry")),
            "history": self._normalize_bilingual(data.get("history")),
            "introduction_html": self._normalize_bilingual(data.get("introduction_html")),
            "phone": data.get("phone") or "",
            "email": data.get("email") or "",
            "website": data.get("website") or "",
            "updated_at": data.get("updated_at"),
        }

    def _remove_logo_files(self, logo_dir: Path) -> None:
        if not logo_dir.exists():
            return
        for path in logo_dir.iterdir():
            if path.is_file() and path.suffix.lower() in ALLOWED_LOGO_EXTENSIONS:
                path.unlink()
