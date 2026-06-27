"""Batch upload and multi-report analysis services."""

from __future__ import annotations

import json
import re
from datetime import datetime

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import Settings
from app.database import BatchAnalysis, Report, ReportBatch
from app.exceptions import BatchAnalysisError, BatchNotFoundError, InvalidFileError
from app.i18n.locale import normalize_language, translate
from app.services.analysis_service import AnalysisService
from app.services.file_service import FileService
from app.services.llm_service import LLMService
from app.services.report_parser import ReportParser
from app.services.report_service import ReportService


class BatchService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.file_service = FileService(settings)
        self.parser = ReportParser()
        self.report_service = ReportService(self.file_service)
        self.analysis_service = AnalysisService(settings)
        self.llm = LLMService(settings)

    async def create_batch_with_files(
        self,
        db: Session,
        files: list[UploadFile],
        name: str | None = None,
    ) -> ReportBatch:
        if not files:
            raise InvalidFileError("At least one file is required.")

        batch_name = name.strip() if name and name.strip() else f"Batch {datetime.utcnow():%Y-%m-%d %H:%M}"
        batch = ReportBatch(name=batch_name, status="uploaded")
        db.add(batch)
        db.commit()
        db.refresh(batch)

        for upload in files:
            content = await upload.read()
            stored_name, file_path, file_type = self.file_service.save_upload(upload, content)
            report = Report(
                batch_id=batch.id,
                filename=stored_name,
                original_filename=upload.filename or stored_name,
                file_path=file_path,
                file_type=file_type,
                file_size=len(content),
                status="uploaded",
            )
            db.add(report)
            db.commit()
            db.refresh(report)
            try:
                report.extracted_text = self.parser.extract_text(file_path, file_type)
                db.commit()
            except InvalidFileError:
                pass

        batch.status = "uploaded"
        db.commit()
        db.refresh(batch)
        return batch

    def list_batches(self, db: Session) -> list[ReportBatch]:
        return db.query(ReportBatch).order_by(ReportBatch.created_at.desc()).all()

    def get_batch(self, db: Session, batch_id: int) -> ReportBatch:
        batch = db.query(ReportBatch).filter(ReportBatch.id == batch_id).first()
        if not batch:
            raise BatchNotFoundError(batch_id)
        return batch

    def get_batch_reports(self, db: Session, batch_id: int) -> list[Report]:
        self.get_batch(db, batch_id)
        return db.query(Report).filter(Report.batch_id == batch_id).order_by(Report.created_at.asc()).all()

    def delete_batch(self, db: Session, batch_id: int) -> None:
        batch = self.get_batch(db, batch_id)
        reports = self.get_batch_reports(db, batch_id)
        for report in reports:
            self.report_service.delete_file_only(report)
            db.delete(report)
        db.delete(batch)
        db.commit()

    async def run_batch_analysis(
        self,
        db: Session,
        batch_id: int,
        language: str = "en",
        force: bool = False,
        criteria: str | None = None,
    ) -> BatchAnalysis:
        lang = normalize_language(language)
        batch = self.get_batch(db, batch_id)
        reports = self.get_batch_reports(db, batch_id)
        if not reports:
            raise BatchAnalysisError("This batch has no reports to analyze.")

        if not force:
            existing = self.get_latest_batch_analysis(db, batch_id)
            if existing and existing.status == "completed":
                return existing

        batch_analysis = BatchAnalysis(batch_id=batch_id, status="processing", report_count=len(reports))
        db.add(batch_analysis)
        db.commit()
        db.refresh(batch_analysis)

        try:
            individual_results = []
            for report in reports:
                analysis = await self.analysis_service.run_analysis(
                    db, report.id, force=True, language=lang, criteria=criteria
                )
                individual_results.append(
                    {
                        "report_id": report.id,
                        "filename": report.original_filename,
                        "summary": analysis.summary,
                        "revenue": analysis.revenue,
                        "expenses": analysis.expenses,
                        "profit_loss": analysis.profit_loss,
                    }
                )

            combined_text = self._build_combined_context(reports)
            llm_result = await self.llm.analyze_batch(
                combined_text, batch.name, individual_results, lang, criteria=criteria
            )

            if llm_result:
                self._apply_llm_batch_result(batch_analysis, llm_result, individual_results)
            else:
                self._apply_heuristic_batch_result(batch_analysis, batch, reports, individual_results, lang)

            batch_analysis.status = "completed"
            batch.status = "analyzed"
            db.commit()
            db.refresh(batch_analysis)
            return batch_analysis
        except Exception as exc:
            batch_analysis.status = "failed"
            batch_analysis.error_message = str(exc)
            batch.status = "analysis_failed"
            db.commit()
            db.refresh(batch_analysis)
            raise BatchAnalysisError(f"Batch analysis failed: {exc}") from exc

    def get_latest_batch_analysis(self, db: Session, batch_id: int) -> BatchAnalysis | None:
        return (
            db.query(BatchAnalysis)
            .filter(BatchAnalysis.batch_id == batch_id)
            .order_by(BatchAnalysis.created_at.desc())
            .first()
        )

    def list_batch_analyses(self, db: Session, batch_id: int) -> list[BatchAnalysis]:
        self.get_batch(db, batch_id)
        return (
            db.query(BatchAnalysis)
            .filter(BatchAnalysis.batch_id == batch_id)
            .order_by(BatchAnalysis.created_at.desc())
            .all()
        )

    def get_batch_report_analyses(self, db: Session, batch_id: int) -> list[tuple[Report, Analysis | None]]:
        reports = self.get_batch_reports(db, batch_id)
        from app.database import Analysis

        result: list[tuple[Report, Analysis | None]] = []
        for report in reports:
            analysis = (
                db.query(Analysis)
                .filter(Analysis.report_id == report.id)
                .order_by(Analysis.created_at.desc())
                .first()
            )
            result.append((report, analysis))
        return result

    def _build_combined_context(self, reports: list[Report]) -> str:
        parts = []
        for report in reports:
            excerpt = (report.extracted_text or "")[:4000]
            parts.append(f"=== {report.original_filename} ===\n{excerpt}")
        return "\n\n".join(parts)[:25000]

    def _apply_llm_batch_result(
        self, batch_analysis: BatchAnalysis, result: dict, individual_results: list[dict]
    ) -> None:
        def as_text(value: object) -> str | None:
            if value is None:
                return None
            if isinstance(value, (dict, list)):
                return json.dumps(value, ensure_ascii=False)
            return str(value)

        batch_analysis.summary = as_text(result.get("summary"))
        batch_analysis.revenue = as_text(result.get("revenue"))
        batch_analysis.expenses = as_text(result.get("expenses"))
        batch_analysis.profit_loss = as_text(result.get("profit_loss"))
        batch_analysis.cash_flow = as_text(result.get("cash_flow"))
        batch_analysis.assets = as_text(result.get("assets"))
        batch_analysis.liabilities = as_text(result.get("liabilities"))
        batch_analysis.risks = as_text(result.get("risks"))
        batch_analysis.strengths = as_text(result.get("strengths"))
        batch_analysis.weaknesses = as_text(result.get("weaknesses"))
        batch_analysis.recommendations = as_text(result.get("recommendations"))
        batch_analysis.raw_result = json.dumps({"individual": individual_results, "combined": result})

    def _apply_heuristic_batch_result(
        self,
        batch_analysis: BatchAnalysis,
        batch: ReportBatch,
        reports: list[Report],
        individual_results: list[dict],
        language: str,
    ) -> None:
        lang = normalize_language(language)
        parser = ReportParser()
        totals: dict[str, float] = {"revenue": 0.0, "expenses": 0.0, "profit_loss": 0.0}
        found_counts = {"revenue": 0, "expenses": 0, "profit_loss": 0}

        for report in reports:
            figures = parser.extract_financial_figures(report.extracted_text or "")
            for key in totals:
                raw = figures.get(key)
                if raw:
                    amount = self._parse_amount(raw)
                    if amount is not None:
                        totals[key] += amount
                        found_counts[key] += 1

        file_list = ", ".join(r.original_filename for r in reports)
        if lang == "ar":
            batch_analysis.summary = (
                f"تحليل مجمّع لـ {len(reports)} تقارير في '{batch.name}': {file_list}. "
                "يوفر هذا الملخص الصورة الكبيرة عبر جميع المستندات المرفوعة."
            )
        else:
            batch_analysis.summary = (
                f"Combined analysis of {len(reports)} reports in '{batch.name}': {file_list}. "
                "This summary provides the big picture across all uploaded documents."
            )

        batch_analysis.revenue = self._format_aggregate("revenue", totals, found_counts, lang)
        batch_analysis.expenses = self._format_aggregate("expenses", totals, found_counts, lang)
        batch_analysis.profit_loss = self._format_aggregate("profit_loss", totals, found_counts, lang)
        batch_analysis.cash_flow = self._combine_field(individual_results, "profit_loss", lang)
        batch_analysis.assets = translate("not_found_in_document", lang) if lang == "ar" else "See individual reports for asset details."
        batch_analysis.liabilities = translate("not_found_in_document", lang) if lang == "ar" else "See individual reports for liability details."

        per_report = "\n".join(
            f"- {item['filename']}: {item.get('summary') or item.get('revenue') or '—'}"
            for item in individual_results
        )
        if lang == "ar":
            batch_analysis.strengths = f"تم تحليل {len(reports)} تقارير معًا.\n{per_report}"
            batch_analysis.weaknesses = "قد تختلف تنسيقات التقارير؛ راجع كل تقرير للتفاصيل."
            batch_analysis.risks = "قارن الاتجاهات والتناقضات بين التقارير يدويًا أو فعّل LLM."
            batch_analysis.recommendations = "استخدم المحادثة المجمّعة لطرح أسئلة عن الصورة الكاملة."
        else:
            batch_analysis.strengths = f"Analyzed {len(reports)} reports together.\n{per_report}"
            batch_analysis.weaknesses = "Report formats may differ; review each report for detail."
            batch_analysis.risks = "Compare trends and inconsistencies across reports manually or enable LLM."
            batch_analysis.recommendations = "Use batch chat to ask questions about the full picture."

        batch_analysis.raw_result = json.dumps({"mode": "heuristic", "individual": individual_results, "totals": totals})

    def _parse_amount(self, value: str) -> float | None:
        match = re.search(r"[\d,]+(?:\.\d{2})?", value.replace("$", ""))
        if not match:
            return None
        try:
            return float(match.group(0).replace(",", ""))
        except ValueError:
            return None

    def _format_aggregate(self, key: str, totals: dict, counts: dict, lang: str) -> str:
        if counts[key] == 0:
            return translate("not_found_in_document", lang)
        label = key.replace("_", " ")
        if lang == "ar":
            return f"مجموع {label} عبر {counts[key]} تقارير: ${totals[key]:,.2f}"
        return f"Combined {label} across {counts[key]} reports: ${totals[key]:,.2f}"

    def _combine_field(self, individual_results: list[dict], field: str, lang: str) -> str:
        lines = [f"{i['filename']}: {i.get(field) or '—'}" for i in individual_results]
        header = "Per-report breakdown:" if lang == "en" else "تفصيل لكل تقرير:"
        return header + "\n" + "\n".join(lines)
