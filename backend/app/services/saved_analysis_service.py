"""Persist financial analysis results to disk."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import Settings
from app.database import Analysis, BatchAnalysis, Report, ReportBatch, SavedAnalysisExport
from app.exceptions import AnalysisError, BatchNotFoundError, ReportNotFoundError, SavedAnalysisNotFoundError
from app.services.analysis_service import AnalysisService
from app.services.batch_service import BatchService


class SavedAnalysisService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.analysis_service = AnalysisService(settings)
        self.batch_service = BatchService(settings)

    def list_saved(self, db: Session) -> list[SavedAnalysisExport]:
        return (
            db.query(SavedAnalysisExport)
            .order_by(SavedAnalysisExport.created_at.desc())
            .all()
        )

    def get_saved(self, db: Session, saved_id: int) -> SavedAnalysisExport:
        item = db.query(SavedAnalysisExport).filter(SavedAnalysisExport.id == saved_id).first()
        if not item:
            raise SavedAnalysisNotFoundError(saved_id)
        return item

    def get_saved_content(self, db: Session, saved_id: int) -> dict:
        item = self.get_saved(db, saved_id)
        path = Path(item.file_path)
        if not path.exists():
            raise SavedAnalysisNotFoundError(saved_id)
        return json.loads(path.read_text(encoding="utf-8"))

    def delete_saved(self, db: Session, saved_id: int) -> None:
        item = self.get_saved(db, saved_id)
        path = Path(item.file_path)
        if path.exists():
            path.unlink()
        db.delete(item)
        db.commit()

    def delete_saved_many(self, db: Session, saved_ids: list[int]) -> int:
        unique_ids = list(dict.fromkeys(saved_ids))
        deleted = 0
        for saved_id in unique_ids:
            item = db.query(SavedAnalysisExport).filter(SavedAnalysisExport.id == saved_id).first()
            if not item:
                continue
            path = Path(item.file_path)
            if path.exists():
                path.unlink()
            db.delete(item)
            deleted += 1
        if deleted:
            db.commit()
        return deleted

    def update_saved(
        self, db: Session, saved_id: int, updates: dict
    ) -> SavedAnalysisExport:
        item = self.get_saved(db, saved_id)
        path = Path(item.file_path)
        if not path.exists():
            raise SavedAnalysisNotFoundError(saved_id)

        content = json.loads(path.read_text(encoding="utf-8"))
        analysis_key = "combined_analysis" if content.get("source_type") == "batch" else "analysis"
        analysis = content.get(analysis_key)
        if not isinstance(analysis, dict):
            analysis = {}
            content[analysis_key] = analysis

        title = updates.get("title")
        if title is not None:
            title = title.strip()
            if not title:
                raise AnalysisError("Title is required.")
            content["title"] = title
            item.title = title

        section_fields = (
            "summary",
            "revenue",
            "expenses",
            "profit_loss",
            "cash_flow",
            "assets",
            "liabilities",
            "risks",
            "strengths",
            "weaknesses",
            "recommendations",
        )
        for field in section_fields:
            if field in updates and updates[field] is not None:
                analysis[field] = updates[field]

        if "custom_sections" in updates and updates["custom_sections"] is not None:
            content["custom_sections"] = [
                {"title": section["title"].strip(), "content": section.get("content", "")}
                for section in updates["custom_sections"]
                if section.get("title", "").strip()
            ]

        if "document_html" in updates and updates["document_html"] is not None:
            content["document_html"] = updates["document_html"]

        content["last_edited_at"] = datetime.utcnow().isoformat()
        path.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
        db.commit()
        db.refresh(item)
        return item

    async def reanalyze_saved(
        self,
        db: Session,
        saved_id: int,
        criteria: str,
        language: str = "en",
    ) -> SavedAnalysisExport:
        item = self.get_saved(db, saved_id)
        path = Path(item.file_path)
        if not path.exists():
            raise SavedAnalysisNotFoundError(saved_id)

        criteria = criteria.strip()
        if not criteria:
            raise AnalysisError("Criteria or questions are required.")

        content = json.loads(path.read_text(encoding="utf-8"))

        if item.source_type == "report":
            if not item.report_id:
                raise AnalysisError("Original report is no longer linked to this saved analysis.")
            analysis = await self.analysis_service.run_analysis(
                db,
                item.report_id,
                force=True,
                language=language,
                criteria=criteria,
            )
            content["analysis"] = self._analysis_dict(analysis)
            content["analysis_id"] = analysis.id
        elif item.source_type == "batch":
            if not item.batch_id:
                raise AnalysisError("Original batch is no longer linked to this saved analysis.")
            batch_analysis = await self.batch_service.run_batch_analysis(
                db,
                item.batch_id,
                language=language,
                force=True,
                criteria=criteria,
            )
            reports = self.batch_service.get_batch_reports(db, item.batch_id)
            report_analyses = []
            for report in reports:
                latest = self.analysis_service.get_latest_analysis(db, report.id)
                if latest and latest.status == "completed":
                    report_analyses.append(self._analysis_dict(latest, report.original_filename))

            content["combined_analysis"] = self._batch_analysis_dict(batch_analysis)
            content["batch_analysis_id"] = batch_analysis.id
            content["report_analyses"] = report_analyses
            content["report_count"] = batch_analysis.report_count
        else:
            raise AnalysisError("Unsupported saved analysis type.")

        content.pop("document_html", None)
        content["last_reanalyze_criteria"] = criteria
        content["last_reanalyzed_at"] = datetime.utcnow().isoformat()
        content["last_edited_at"] = datetime.utcnow().isoformat()
        path.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
        db.commit()
        db.refresh(item)
        return item

    def save_report_analysis(
        self, db: Session, report_id: int, title: str, analysis_id: int | None = None
    ) -> SavedAnalysisExport:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise ReportNotFoundError(report_id)

        analysis = (
            self.analysis_service.get_analysis(db, analysis_id)
            if analysis_id
            else self.analysis_service.get_latest_analysis(db, report_id)
        )
        if not analysis or analysis.status != "completed":
            raise AnalysisError("No completed analysis found to save.")

        payload = self._build_report_payload(title, report, analysis)
        return self._write_export(
            db,
            title=title.strip(),
            source_type="report",
            source_name=report.original_filename,
            report_id=report.id,
            batch_id=report.batch_id,
            analysis_id=analysis.id,
            batch_analysis_id=None,
            payload=payload,
        )

    def save_batch_analysis(
        self, db: Session, batch_id: int, title: str, batch_analysis_id: int | None = None
    ) -> SavedAnalysisExport:
        batch = self.batch_service.get_batch(db, batch_id)
        analysis = (
            self.batch_service.get_latest_batch_analysis(db, batch_id)
            if not batch_analysis_id
            else db.query(BatchAnalysis).filter(BatchAnalysis.id == batch_analysis_id).first()
        )
        if not analysis or analysis.batch_id != batch_id or analysis.status != "completed":
            raise AnalysisError("No completed batch analysis found to save.")

        reports = self.batch_service.get_batch_reports(db, batch_id)
        report_analyses = []
        for report in reports:
            latest = self.analysis_service.get_latest_analysis(db, report.id)
            if latest and latest.status == "completed":
                report_analyses.append(self._analysis_dict(latest, report.original_filename))

        payload = self._build_batch_payload(title, batch, analysis, report_analyses)
        return self._write_export(
            db,
            title=title.strip(),
            source_type="batch",
            source_name=batch.name,
            report_id=None,
            batch_id=batch.id,
            analysis_id=None,
            batch_analysis_id=analysis.id,
            payload=payload,
        )

    def _write_export(
        self,
        db: Session,
        *,
        title: str,
        source_type: str,
        source_name: str,
        report_id: int | None,
        batch_id: int | None,
        analysis_id: int | None,
        batch_analysis_id: int | None,
        payload: dict,
    ) -> SavedAnalysisExport:
        if not title:
            raise AnalysisError("Title is required to save an analysis.")

        self.settings.saved_analyses_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        slug = self._slugify(title) or "analysis"
        filename = f"{timestamp}_{slug}.json"
        file_path = self.settings.saved_analyses_path / filename
        file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        record = SavedAnalysisExport(
            title=title,
            filename=filename,
            file_path=str(file_path),
            source_type=source_type,
            source_name=source_name,
            report_id=report_id,
            batch_id=batch_id,
            analysis_id=analysis_id,
            batch_analysis_id=batch_analysis_id,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def _build_report_payload(self, title: str, report: Report, analysis: Analysis) -> dict:
        return {
            "title": title.strip(),
            "saved_at": datetime.utcnow().isoformat(),
            "source_type": "report",
            "source_name": report.original_filename,
            "report_id": report.id,
            "analysis_id": analysis.id,
            "report": {
                "filename": report.filename,
                "original_filename": report.original_filename,
                "file_path": report.file_path,
                "file_type": report.file_type,
                "file_size": report.file_size,
            },
            "analysis": self._analysis_dict(analysis),
        }

    def _build_batch_payload(
        self,
        title: str,
        batch: ReportBatch,
        analysis: BatchAnalysis,
        report_analyses: list[dict],
    ) -> dict:
        return {
            "title": title.strip(),
            "saved_at": datetime.utcnow().isoformat(),
            "source_type": "batch",
            "source_name": batch.name,
            "batch_id": batch.id,
            "batch_analysis_id": analysis.id,
            "report_count": analysis.report_count,
            "combined_analysis": self._batch_analysis_dict(analysis),
            "report_analyses": report_analyses,
        }

    def _analysis_dict(self, analysis: Analysis, filename: str | None = None) -> dict:
        data = {
            "id": analysis.id,
            "report_id": analysis.report_id,
            "status": analysis.status,
            "summary": analysis.summary,
            "revenue": analysis.revenue,
            "expenses": analysis.expenses,
            "profit_loss": analysis.profit_loss,
            "cash_flow": analysis.cash_flow,
            "assets": analysis.assets,
            "liabilities": analysis.liabilities,
            "risks": analysis.risks,
            "strengths": analysis.strengths,
            "weaknesses": analysis.weaknesses,
            "recommendations": analysis.recommendations,
            "created_at": analysis.created_at.isoformat(),
        }
        if filename:
            data["original_filename"] = filename
        return data

    def _batch_analysis_dict(self, analysis: BatchAnalysis) -> dict:
        return {
            "id": analysis.id,
            "batch_id": analysis.batch_id,
            "status": analysis.status,
            "report_count": analysis.report_count,
            "summary": analysis.summary,
            "revenue": analysis.revenue,
            "expenses": analysis.expenses,
            "profit_loss": analysis.profit_loss,
            "cash_flow": analysis.cash_flow,
            "assets": analysis.assets,
            "liabilities": analysis.liabilities,
            "risks": analysis.risks,
            "strengths": analysis.strengths,
            "weaknesses": analysis.weaknesses,
            "recommendations": analysis.recommendations,
            "created_at": analysis.created_at.isoformat(),
        }

    def _slugify(self, value: str) -> str:
        slug = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE).strip().lower()
        slug = re.sub(r"[\s_-]+", "-", slug)
        return slug[:60]
