import json

from app.config import get_settings
from app.database import Report, SavedAnalysisExport, SessionLocal, _bind_engine, init_db
from app.services.persistence_service import PersistenceService


def test_sync_saved_analyses_from_disk(tmp_path, monkeypatch):
    saved_dir = tmp_path / "reports_analyzes"
    saved_dir.mkdir()
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    db_path = tmp_path / "galfar.db"

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("UPLOAD_DIR", str(upload_dir))
    monkeypatch.setenv("SAVED_ANALYSES_DIR", str(saved_dir))

    payload = {
        "title": "Payments Review",
        "saved_at": "2026-06-27T05:34:50.027153",
        "source_type": "report",
        "source_name": "PAYMENT.pdf",
        "report_id": 2,
        "analysis_id": 2,
        "analysis": {"summary": "Recovered analysis", "status": "completed"},
    }
    json_file = saved_dir / "20260627_053450_payments-review.json"
    json_file.write_text(json.dumps(payload), encoding="utf-8")

    get_settings.cache_clear()
    _bind_engine()
    init_db()
    db = SessionLocal()
    try:
        PersistenceService(get_settings()).sync_all(db)
        saved = db.query(SavedAnalysisExport).filter_by(title="Payments Review").all()
        assert len(saved) == 1
    finally:
        db.close()


def test_manifest_restores_missing_report(tmp_path, monkeypatch):
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    db_path = tmp_path / "galfar.db"
    saved_dir = tmp_path / "reports_analyzes"
    saved_dir.mkdir()

    file_path = upload_dir / "abc123.txt"
    file_path.write_text("Total Revenue: $1,000", encoding="utf-8")

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("UPLOAD_DIR", str(upload_dir))
    monkeypatch.setenv("SAVED_ANALYSES_DIR", str(saved_dir))

    get_settings.cache_clear()
    _bind_engine()
    init_db()
    settings = get_settings()
    service = PersistenceService(settings)
    service.manifest.upsert_report(
        {
            "filename": "abc123.txt",
            "original_filename": "sales.txt",
            "file_path": str(file_path),
            "file_type": "txt",
            "file_size": file_path.stat().st_size,
            "status": "uploaded",
            "created_at": "2026-06-27T10:00:00",
        }
    )

    db = SessionLocal()
    try:
        service.sync_all(db)
        report = db.query(Report).filter_by(filename="abc123.txt").first()
        assert report is not None
        assert report.original_filename == "sales.txt"
        assert report.file_path == str(file_path)
    finally:
        db.close()
