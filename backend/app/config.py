from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"


def _resolve_sqlite_url(url: str) -> str:
    if url.startswith("sqlite:///./"):
        rel = url.removeprefix("sqlite:///./")
        path = (_BACKEND_DIR / rel).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{path.as_posix()}"
    return url


def _resolve_relative_path(path_value: str) -> str:
    if path_value.startswith("./"):
        return str((_BACKEND_DIR / path_value.removeprefix("./")).resolve())
    return path_value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )

    app_name: str = "Galfar Financial Reports"
    debug: bool = True
    database_url: str = "sqlite:///./storage/galfar.db"
    upload_dir: str = "./uploads"
    saved_analyses_dir: str = "./storage/reports_analyzes"
    max_upload_size_mb: int = 25
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    llm_enabled: bool = False
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def llm_ready(self) -> bool:
        return self.llm_enabled and bool(self.openai_api_key.strip())

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def upload_path(self) -> Path:
        return Path(self.upload_dir)

    @property
    def saved_analyses_path(self) -> Path:
        return Path(self.saved_analyses_dir)

    @property
    def company_logo_dir(self) -> Path:
        return self.storage_path / "company"

    @property
    def company_settings_file(self) -> Path:
        return self.storage_path / "company_settings.json"

    @property
    def storage_path(self) -> Path:
        return Path(self.database_url.removeprefix("sqlite:///")).parent

    @model_validator(mode="after")
    def resolve_storage_paths(self) -> "Settings":
        object.__setattr__(self, "database_url", _resolve_sqlite_url(self.database_url))
        object.__setattr__(self, "upload_dir", _resolve_relative_path(self.upload_dir))
        object.__setattr__(self, "saved_analyses_dir", _resolve_relative_path(self.saved_analyses_dir))
        return self


@lru_cache
def get_settings() -> Settings:
    from dotenv import load_dotenv

    load_dotenv(_ENV_FILE, override=False)
    return Settings()
