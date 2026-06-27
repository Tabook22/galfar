"""Pytest configuration — never use the production database."""

from __future__ import annotations

import os
from pathlib import Path

_TEST_ROOT = Path(__file__).resolve().parent / ".pytest_storage"
_TEST_ROOT.mkdir(exist_ok=True)

os.environ["DATABASE_URL"] = f"sqlite:///{(_TEST_ROOT / 'test_galfar.db').as_posix()}"
os.environ["UPLOAD_DIR"] = str(_TEST_ROOT / "uploads")
os.environ["SAVED_ANALYSES_DIR"] = str(_TEST_ROOT / "reports_analyzes")

import pytest

from app.config import get_settings
from app.database import Base, _bind_engine, engine, init_db


@pytest.fixture(autouse=True)
def isolated_database():
    get_settings.cache_clear()
    _bind_engine()
    Base.metadata.drop_all(bind=engine)
    init_db()
    yield
    Base.metadata.drop_all(bind=engine)
