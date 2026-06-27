import mimetypes

from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import Report, SessionLocal, get_db
from app.exceptions import AppError, InvalidFileError
from app.schemas import (
    BulkDeleteReportsRequest,
    BulkDeleteReportsResponse,
    DashboardStats,
    ReportDetailResponse,
    ReportResponse,
)
from app.services.file_service import FileService
from app.services.persistence_service import PersistenceService
from app.services.report_parser import ReportParser
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])
settings = get_settings()
file_service = FileService(settings)
persistence_service = PersistenceService(settings)
report_service = ReportService(file_service, persistence_service)
parser = ReportParser()


def _extract_and_record_report(report_id: int) -> None:
    db = SessionLocal()
    try:
        report = db.get(Report, report_id)
        if not report:
            return
        try:
            report.extracted_text = parser.extract_text(report.file_path, report.file_type)
        except InvalidFileError:
            pass
        db.commit()
        db.refresh(report)
        persistence_service.record_report(report)
    finally:
        db.close()


@router.get("/stats/dashboard", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db)):
    return report_service.get_dashboard_stats(db)


@router.get("", response_model=list[ReportResponse])
def list_reports(
    db: Session = Depends(get_db),
    search: str | None = Query(default=None, max_length=200),
    category: str | None = Query(default=None, max_length=50),
    sort_by: str = Query(default="date", pattern="^(name|date|category)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
):
    return report_service.list_reports(
        db, search=search, category=category, sort_by=sort_by, sort_order=sort_order
    )


@router.get("/categories", response_model=list[str])
def list_report_categories(db: Session = Depends(get_db)):
    return report_service.list_categories(db)


@router.post("", response_model=ReportResponse, status_code=201)
async def upload_report(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    content = await file.read()
    try:
        stored_name, file_path, file_type = file_service.save_upload(file, content)
    except InvalidFileError:
        raise
    except Exception as exc:
        raise AppError(f"Failed to save upload: {exc}", 500) from exc

    report = Report(
        filename=stored_name,
        original_filename=file.filename or stored_name,
        file_path=file_path,
        file_type=file_type,
        file_size=len(content),
        status="uploaded",
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    background_tasks.add_task(_extract_and_record_report, report.id)
    return report_service._to_response(db, report)


@router.post("/bulk-delete", response_model=BulkDeleteReportsResponse)
def bulk_delete_reports(body: BulkDeleteReportsRequest, db: Session = Depends(get_db)):
    deleted_count = report_service.delete_reports(db, body.report_ids)
    return BulkDeleteReportsResponse(deleted_count=deleted_count)


@router.get("/{report_id}", response_model=ReportDetailResponse)
def get_report(report_id: int, db: Session = Depends(get_db)):
    return report_service.get_report(db, report_id)


@router.get("/{report_id}/download")
def download_report(report_id: int, db: Session = Depends(get_db)):
    path, filename = report_service.get_report_file(db, report_id)
    media_type, _ = mimetypes.guess_type(filename)
    return FileResponse(
        path=path,
        filename=filename,
        media_type=media_type or "application/octet-stream",
    )


@router.delete("/{report_id}", status_code=204)
def delete_report(report_id: int, db: Session = Depends(get_db)):
    report_service.delete_report(db, report_id)
