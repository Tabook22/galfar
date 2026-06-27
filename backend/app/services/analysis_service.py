import json

from sqlalchemy.orm import Session

from app.config import Settings
from app.database import Analysis, Report
from app.exceptions import AnalysisError, ReportNotFoundError
from app.i18n.locale import normalize_language, translate
from app.services.llm_service import LLMService
from app.services.report_parser import ReportParser


class AnalysisService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.parser = ReportParser()
        self.llm = LLMService(settings)

    def get_analysis(self, db: Session, analysis_id: int) -> Analysis:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            raise ReportNotFoundError(analysis_id)
        return analysis

    def get_latest_analysis(self, db: Session, report_id: int) -> Analysis | None:
        return (
            db.query(Analysis)
            .filter(Analysis.report_id == report_id)
            .order_by(Analysis.created_at.desc())
            .first()
        )

    def list_analyses(self, db: Session, report_id: int) -> list[Analysis]:
        return (
            db.query(Analysis)
            .filter(Analysis.report_id == report_id)
            .order_by(Analysis.created_at.desc())
            .all()
        )

    async def run_analysis(
        self,
        db: Session,
        report_id: int,
        force: bool = False,
        language: str = "en",
        criteria: str | None = None,
    ) -> Analysis:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise ReportNotFoundError(report_id)

        if not force:
            existing = self.get_latest_analysis(db, report_id)
            if existing and existing.status == "completed":
                return existing

        analysis = Analysis(report_id=report_id, status="processing")
        db.add(analysis)
        db.commit()
        db.refresh(analysis)

        try:
            if not report.extracted_text:
                report.extracted_text = self.parser.extract_text(report.file_path, report.file_type)
                db.commit()

            text = report.extracted_text or ""
            llm_result = await self.llm.analyze_report(
                text, report.original_filename, language, criteria=criteria
            )

            if llm_result:
                self._apply_llm_result(analysis, llm_result)
            else:
                self._apply_heuristic_analysis(
                    analysis, text, report.original_filename, language, criteria=criteria
                )

            analysis.status = "completed"
            report.status = "analyzed"
            db.commit()
            db.refresh(analysis)
            return analysis
        except Exception as exc:
            analysis.status = "failed"
            analysis.error_message = str(exc)
            report.status = "analysis_failed"
            db.commit()
            db.refresh(analysis)
            raise AnalysisError(f"Analysis failed: {exc}") from exc

    def _apply_llm_result(self, analysis: Analysis, result: dict) -> None:
        def as_text(value: object) -> str | None:
            if value is None:
                return None
            if isinstance(value, (dict, list)):
                return json.dumps(value, ensure_ascii=False)
            return str(value)

        analysis.summary = as_text(result.get("summary"))
        analysis.revenue = as_text(result.get("revenue"))
        analysis.expenses = as_text(result.get("expenses"))
        analysis.profit_loss = as_text(result.get("profit_loss"))
        analysis.cash_flow = as_text(result.get("cash_flow"))
        analysis.assets = as_text(result.get("assets"))
        analysis.liabilities = as_text(result.get("liabilities"))
        analysis.risks = as_text(result.get("risks"))
        analysis.strengths = as_text(result.get("strengths"))
        analysis.weaknesses = as_text(result.get("weaknesses"))
        analysis.recommendations = as_text(result.get("recommendations"))
        analysis.raw_result = json.dumps(result, ensure_ascii=False)

    def _apply_heuristic_analysis(
        self,
        analysis: Analysis,
        text: str,
        filename: str,
        language: str = "en",
        criteria: str | None = None,
    ) -> None:
        lang = normalize_language(language)
        figures = self.parser.extract_financial_figures(text)
        word_count = len(text.split())
        not_found = translate("not_found_in_document", lang)

        analysis.summary = translate(
            "analysis_summary_heuristic", lang, filename=filename, words=word_count
        )
        if criteria and criteria.strip():
            focus_label = "Analysis focus" if lang == "en" else "محور التحليل"
            analysis.summary = f"{focus_label}: {criteria.strip()}\n\n{analysis.summary}"
        analysis.revenue = figures.get("revenue") or self._infer_section(text, "revenue", lang, not_found)
        analysis.expenses = figures.get("expenses") or self._infer_section(text, "expense", lang, not_found)
        analysis.profit_loss = figures.get("profit_loss") or self._infer_section(text, "profit", lang, not_found)
        analysis.cash_flow = figures.get("cash_flow") or self._infer_section(text, "cash flow", lang, not_found)
        analysis.assets = figures.get("assets") or self._infer_section(text, "asset", lang, not_found)
        analysis.liabilities = figures.get("liabilities") or self._infer_section(text, "liabilit", lang, not_found)
        analysis.risks = self._build_risks(text, figures, lang)
        analysis.strengths = self._build_strengths(figures, lang)
        analysis.weaknesses = self._build_weaknesses(figures, lang)
        analysis.recommendations = self._build_recommendations(figures, lang)
        analysis.raw_result = json.dumps({"mode": "heuristic", "figures": figures, "language": lang})

    def _infer_section(self, text: str, keyword: str, language: str, not_found: str) -> str:
        lines = text.splitlines()
        matches = [line.strip() for line in lines if keyword.lower() in line.lower()]
        if matches:
            return "; ".join(matches[:3])
        return not_found

    def _build_risks(self, text: str, figures: dict, language: str) -> str:
        lang = normalize_language(language)
        risks = []
        lower = text.lower()
        if "debt" in lower or figures.get("liabilities"):
            risks.append(
                "Elevated liabilities or debt references detected."
                if lang == "en"
                else "تم رصد التزامات أو ديون مرتفعة."
            )
        if "loss" in lower or "خسارة" in text:
            risks.append(
                "Report mentions losses — review profitability trends."
                if lang == "en"
                else "يشير التقرير إلى خسائر — راجع اتجاهات الربحية."
            )
        if ("cash flow" in lower or "تدفق" in text) and ("negative" in lower or "سلبي" in text):
            risks.append(
                "Potential negative cash flow indicators."
                if lang == "en"
                else "مؤشرات محتملة على تدفق نقدي سلبي."
            )
        if not risks:
            risks.append(
                "No major risk keywords detected; manual review recommended."
                if lang == "en"
                else "لم يتم رصد مخاطر رئيسية؛ يُنصح بالمراجعة اليدوية."
            )
        return " ".join(risks)

    def _build_strengths(self, figures: dict, language: str) -> str:
        lang = normalize_language(language)
        strengths = []
        if figures.get("revenue"):
            strengths.append(
                f"Revenue figure identified: {figures['revenue']}."
                if lang == "en"
                else f"تم تحديد رقم الإيرادات: {figures['revenue']}."
            )
        if figures.get("assets"):
            strengths.append(
                f"Asset base reported: {figures['assets']}."
                if lang == "en"
                else f"تم الإبلاغ عن قاعدة أصول: {figures['assets']}."
            )
        if not strengths:
            strengths.append(
                "Upload structured reports (PDF/CSV) for better automated extraction."
                if lang == "en"
                else "ارفع تقارير منظمة (PDF/CSV) لاستخراج أفضل."
            )
        return " ".join(strengths)

    def _build_weaknesses(self, figures: dict, language: str) -> str:
        lang = normalize_language(language)
        weaknesses = []
        if not figures.get("revenue"):
            weaknesses.append(
                "Revenue not clearly labeled in the document."
                if lang == "en"
                else "الإيرادات غير مذكورة بوضوح في المستند."
            )
        if not figures.get("profit_loss"):
            weaknesses.append(
                "Profit/loss figures not found with standard labels."
                if lang == "en"
                else "لم يتم العثور على أرقام الربح/الخسارة بمسميات قياسية."
            )
        if not weaknesses:
            weaknesses.append(
                "Limited structured financial data for automated parsing."
                if lang == "en"
                else "بيانات مالية منظمة محدودة للتحليل الآلي."
            )
        return " ".join(weaknesses)

    def _build_recommendations(self, figures: dict, language: str) -> str:
        lang = normalize_language(language)
        if lang == "ar":
            recs = [
                "فعّل تكامل LLM للتحليل السردي والأسئلة والأجوبة.",
                "تأكد من استخدام مسميات قياسية (الإيرادات، المصروفات، صافي الدخل).",
            ]
            if not any(figures.values()):
                recs.append("فكّر في رفع تقارير CSV أو نصية لاستخراج أفضل.")
        else:
            recs = [
                "Enable LLM integration for narrative analysis and Q&A.",
                "Ensure reports use standard financial statement labels (Revenue, Expenses, Net Income).",
            ]
            if not any(figures.values()):
                recs.append("Consider uploading CSV or text-based reports for better extraction.")
        return " ".join(recs)
