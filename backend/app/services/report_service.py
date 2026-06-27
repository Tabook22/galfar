from pathlib import Path

from sqlalchemy.orm import Session

from app.database import Analysis, ChatMessage, Report
from app.exceptions import AppError, ReportNotFoundError
from app.schemas import DashboardStats, ReportDetailResponse, ReportResponse
from app.services.file_service import FileService
from app.services.persistence_service import PersistenceService


class ReportService:
    def __init__(self, file_service: FileService, persistence: PersistenceService | None = None):
        self.file_service = file_service
        self.persistence = persistence

    def list_reports(
        self,
        db: Session,
        search: str | None = None,
        category: str | None = None,
        sort_by: str = "date",
        sort_order: str = "desc",
    ) -> list[ReportResponse]:
        query = db.query(Report)

        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            query = query.filter(Report.original_filename.ilike(term))

        if category and category.strip() and category.lower() != "all":
            query = query.filter(Report.file_type == category.strip().lower())

        sort_column = {
            "name": Report.original_filename,
            "date": Report.created_at,
            "category": Report.file_type,
        }.get(sort_by, Report.created_at)

        if sort_order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        reports = query.all()
        return [self._to_response(db, r) for r in reports]

    def list_categories(self, db: Session) -> list[str]:
        rows = db.query(Report.file_type).distinct().order_by(Report.file_type.asc()).all()
        return [row[0] for row in rows if row[0]]

    def get_report_file(self, db: Session, report_id: int) -> tuple[Path, str]:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise ReportNotFoundError(report_id)
        path = Path(report.file_path)
        if not path.is_file():
            raise AppError(f"Report file for id {report_id} is missing on disk.", 404)
        return path, report.original_filename

    def get_report(self, db: Session, report_id: int) -> ReportDetailResponse:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise ReportNotFoundError(report_id)

        preview = None
        if report.extracted_text:
            preview = report.extracted_text[:500] + ("..." if len(report.extracted_text) > 500 else "")

        base = self._to_response(db, report)
        return ReportDetailResponse(
            **base.model_dump(),
            extracted_text_preview=preview,
            analysis_count=db.query(Analysis).filter(Analysis.report_id == report_id).count(),
            chat_message_count=db.query(ChatMessage).filter(ChatMessage.report_id == report_id).count(),
        )

    def delete_report(self, db: Session, report_id: int) -> None:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise ReportNotFoundError(report_id)
        file_path = report.file_path
        self.delete_file_only(report)
        if self.persistence:
            self.persistence.remove_report(file_path)
        db.delete(report)
        db.commit()

    def delete_reports(self, db: Session, report_ids: list[int]) -> int:
        unique_ids = list(dict.fromkeys(report_ids))
        deleted = 0
        for report_id in unique_ids:
            report = db.query(Report).filter(Report.id == report_id).first()
            if not report:
                continue
            file_path = report.file_path
            self.delete_file_only(report)
            if self.persistence:
                self.persistence.remove_report(file_path)
            db.delete(report)
            deleted += 1
        if deleted:
            db.commit()
        return deleted

    def delete_file_only(self, report: Report) -> None:
        self.file_service.delete_file(report.file_path)

    def get_dashboard_stats(self, db: Session) -> DashboardStats:
        total = db.query(Report).count()
        analyzed = db.query(Report).filter(Report.status == "analyzed").count()
        pending = db.query(Report).filter(Report.status.in_(["uploaded", "analysis_failed"])).count()
        chat_count = db.query(ChatMessage).count()
        return DashboardStats(
            total_reports=total,
            analyzed_reports=analyzed,
            pending_reports=pending,
            total_chat_messages=chat_count,
        )

    def _to_response(self, db: Session, report: Report) -> ReportResponse:
        latest = (
            db.query(Analysis)
            .filter(Analysis.report_id == report.id, Analysis.status == "completed")
            .order_by(Analysis.created_at.desc())
            .first()
        )
        return ReportResponse(
            id=report.id,
            filename=report.filename,
            original_filename=report.original_filename,
            file_type=report.file_type,
            file_size=report.file_size,
            status=report.status,
            created_at=report.created_at,
            updated_at=report.updated_at,
            has_analysis=latest is not None,
            latest_analysis_id=latest.id if latest else None,
            batch_id=report.batch_id,
        )
