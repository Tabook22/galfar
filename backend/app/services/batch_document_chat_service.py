"""Document-grounded chat for multi-report batches using saved analyses."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.i18n.locale import analysis_field_labels, normalize_language, topic_label, translate
from app.services.document_chat_service import DocumentChatService

if TYPE_CHECKING:
    from app.database import Analysis, BatchAnalysis, Report


class BatchDocumentChatService:
    BATCH_FIELD_MAP = {
        "revenue": "revenue",
        "expenses": "expenses",
        "profit_loss": "profit_loss",
        "cash_flow": "cash_flow",
        "assets": "assets",
        "liabilities": "liabilities",
        "risks": "risks",
        "recommendations": "recommendations",
        "strengths": "strengths",
        "weaknesses": "weaknesses",
    }

    def __init__(self) -> None:
        self.document_chat = DocumentChatService()

    def reply(
        self,
        user_message: str,
        batch_name: str,
        reports: list["Report"],
        batch_analysis: "BatchAnalysis | None" = None,
        report_analyses: dict[int, "Analysis"] | None = None,
        language: str = "en",
    ) -> str:
        lang = normalize_language(language)
        report_analyses = report_analyses or {}
        question = user_message.strip()
        q_lower = question.lower()

        if any(trigger in q_lower for trigger in self.document_chat.SUMMARY_TRIGGERS):
            return self._summary_reply(batch_name, reports, batch_analysis, report_analyses, lang)

        topic = self.document_chat._detect_topic(q_lower)
        if topic:
            return self._topic_reply(topic, batch_name, reports, batch_analysis, report_analyses, lang)

        matched_report = self._match_report_by_name(q_lower, reports)
        if matched_report:
            analysis = report_analyses.get(matched_report.id)
            return self.document_chat.reply(question, matched_report, analysis, lang)

        combined_text = self._build_combined_text(reports)
        snippets = self.document_chat._relevant_snippets(combined_text, question)
        if snippets:
            body = "\n".join(f"- {s}" for s in snippets[:8])
            return translate("batch_doc_related_snippets", lang, batch_name=batch_name) + f"\n\n{body}"

        return self._fallback_reply(batch_name, reports, batch_analysis, report_analyses, lang)

    def build_analysis_context(
        self,
        batch_name: str,
        reports: list["Report"],
        batch_analysis: "BatchAnalysis | None",
        report_analyses: dict[int, "Analysis"],
        language: str = "en",
    ) -> str:
        lang = normalize_language(language)
        parts = [translate("batch_doc_context_intro", lang, batch_name=batch_name, count=len(reports))]

        if batch_analysis and batch_analysis.status == "completed":
            if batch_analysis.summary:
                parts.append(f"{translate('doc_analysis_summary', lang)} {batch_analysis.summary}")
            for field, label in analysis_field_labels(lang):
                value = getattr(batch_analysis, field, None)
                if value:
                    parts.append(f"{label}: {value}")

        for report in reports:
            analysis = report_analyses.get(report.id)
            if analysis and analysis.status == "completed" and analysis.summary:
                parts.append(
                    translate(
                        "batch_doc_report_analysis",
                        lang,
                        filename=report.original_filename,
                        summary=analysis.summary,
                    )
                )

        return "\n\n".join(parts)[:12000]

    def _summary_reply(
        self,
        batch_name: str,
        reports: list["Report"],
        batch_analysis: "BatchAnalysis | None",
        report_analyses: dict[int, "Analysis"],
        lang: str,
    ) -> str:
        parts = [
            translate(
                "batch_doc_summary_intro",
                lang,
                batch_name=batch_name,
                count=len(reports),
            ),
            "",
        ]

        if batch_analysis and batch_analysis.status == "completed":
            parts.append(translate("batch_doc_combined_analysis", lang))
            if batch_analysis.summary:
                parts.extend([batch_analysis.summary, ""])
            for field, label in analysis_field_labels(lang):
                value = getattr(batch_analysis, field, None)
                if value:
                    parts.extend([f"{label}: {value}", ""])

        per_report = []
        for report in reports:
            analysis = report_analyses.get(report.id)
            if analysis and analysis.status == "completed":
                per_report.append(f"- {report.original_filename}: {analysis.summary or '—'}")
            else:
                per_report.append(f"- {report.original_filename}: {translate('batch_doc_no_analysis', lang)}")

        if per_report:
            parts.extend([translate("batch_doc_per_report", lang), *per_report, ""])

        parts.append(translate("batch_doc_ask_topics", lang))
        return "\n".join(parts)

    def _topic_reply(
        self,
        topic: str,
        batch_name: str,
        reports: list["Report"],
        batch_analysis: "BatchAnalysis | None",
        report_analyses: dict[int, "Analysis"],
        lang: str,
    ) -> str:
        not_found = translate("not_found_in_document", lang)
        label = topic_label(topic, lang)

        if batch_analysis and batch_analysis.status == "completed" and topic in self.BATCH_FIELD_MAP:
            value = getattr(batch_analysis, self.BATCH_FIELD_MAP[topic], None)
            if value and value != not_found:
                return translate("batch_doc_from_combined", lang, batch_name=batch_name, topic=label) + f"\n\n{value}"

        lines = []
        for report in reports:
            analysis = report_analyses.get(report.id)
            if analysis and analysis.status == "completed" and topic in self.BATCH_FIELD_MAP:
                value = getattr(analysis, self.BATCH_FIELD_MAP[topic], None)
                if value and value != not_found:
                    lines.append(f"- {report.original_filename}: {value}")

        if lines:
            header = translate("batch_doc_topic_per_report", lang, topic=label, batch_name=batch_name)
            return header + "\n\n" + "\n".join(lines)

        combined_text = self._build_combined_text(reports)
        keywords = self.document_chat.TOPIC_KEYWORDS.get(topic, [topic])
        snippets = self.document_chat._lines_matching_keywords(combined_text, keywords)
        if snippets:
            body = "\n".join(f"- {s}" for s in snippets[:6])
            return translate("batch_doc_topic_refs", lang, topic=label, batch_name=batch_name) + f"\n\n{body}"

        return translate("batch_doc_topic_missing", lang, topic=label, batch_name=batch_name)

    def _fallback_reply(
        self,
        batch_name: str,
        reports: list["Report"],
        batch_analysis: "BatchAnalysis | None",
        report_analyses: dict[int, "Analysis"],
        lang: str,
    ) -> str:
        file_list = ", ".join(r.original_filename for r in reports)
        reply = translate("batch_doc_fallback_intro", lang, batch_name=batch_name, files=file_list)

        if batch_analysis and batch_analysis.summary:
            reply += f"\n\n{translate('doc_analysis_summary', lang)} {batch_analysis.summary}"

        analyzed = sum(1 for r in reports if report_analyses.get(r.id) and report_analyses[r.id].status == "completed")
        if analyzed:
            reply += f"\n\n{translate('batch_doc_analyzed_count', lang, analyzed=analyzed, total=len(reports))}"
        else:
            reply += f"\n\n{translate('batch_doc_run_analysis', lang)}"

        reply += f"\n\n{translate('batch_doc_ask_topics', lang)}"
        return reply

    def _match_report_by_name(self, q_lower: str, reports: list["Report"]) -> "Report | None":
        for report in reports:
            name = report.original_filename.lower()
            stem = name.rsplit(".", 1)[0]
            if stem in q_lower or name in q_lower:
                return report
        return None

    def _build_combined_text(self, reports: list["Report"]) -> str:
        parts = []
        for report in reports:
            excerpt = (report.extracted_text or "")[:3000]
            parts.append(f"=== {report.original_filename} ===\n{excerpt}")
        return "\n\n".join(parts)
