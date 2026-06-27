import re
from typing import TYPE_CHECKING

from app.i18n.locale import analysis_field_labels, normalize_language, topic_label, translate
from app.services.report_parser import ReportParser

if TYPE_CHECKING:
    from app.database import Analysis, Report


class DocumentChatService:
    """Answers questions using extracted report text and optional analysis results."""

    TOPIC_KEYWORDS: dict[str, list[str]] = {
        "revenue": ["revenue", "sales", "income", "turnover", "إيراد", "إيرادات", "مبيعات", "دخل"],
        "expenses": ["expense", "expenses", "cost", "costs", "spending", "مصروف", "مصاريف", "نفقات"],
        "profit_loss": ["profit", "loss", "net income", "earnings", "ربح", "خسارة", "صافي"],
        "cash_flow": ["cash flow", "cashflow", "operating cash", "تدفق", "نقد"],
        "assets": ["asset", "assets", "أصول", "asset"],
        "liabilities": ["liability", "liabilities", "debt", "التزام", "خصوم", "ديون"],
        "risks": ["risk", "risks", "concern", "concerns", "مخاطر", "خطر"],
        "recommendations": ["recommend", "recommendation", "suggest", "advice", "توص", "اقتراح"],
        "total": ["total", "amount", "balance", "due", "paid", "subtotal", "grand total", "إجمالي", "مجموع", "المبلغ"],
        "date": ["date", "when", "period", "year", "month", "تاريخ", "متى", "سنة"],
        "vendor": ["vendor", "merchant", "store", "supplier", "company", "from", "بائع", "متجر", "تاجر"],
        "items": ["item", "items", "product", "products", "description", "purchase", "منتج", "عنصر", "بند"],
        "tax": ["tax", "vat", "gst", "ضريبة", "vat"],
    }

    SUMMARY_TRIGGERS = (
        "detail",
        "details",
        "about",
        "summary",
        "summarize",
        "overview",
        "explain",
        "tell me",
        "what is",
        "what's",
        "describe",
        "more info",
        "information",
        "تفاصيل",
        "ملخص",
        "لخص",
        "اشرح",
        "ما هو",
        "معلومات",
        "المزيد",
        "وصف",
        "حدثني",
    )

    STOP_WORDS = {
        "the", "and", "for", "what", "this", "that", "with", "about", "from", "can", "you", "give", "more",
        "من", "في", "على", "هل", "ما", "هذا", "ذلك", "عن", "مع",
    }

    def __init__(self) -> None:
        self.parser = ReportParser()

    def reply(
        self,
        user_message: str,
        report: "Report",
        analysis: "Analysis | None" = None,
        language: str = "en",
    ) -> str:
        lang = normalize_language(language)
        text = (report.extracted_text or "").strip()
        question = user_message.strip()
        q_lower = question.lower()

        if not text:
            return translate("doc_no_text", lang, filename=report.original_filename)

        if any(trigger in q_lower for trigger in self.SUMMARY_TRIGGERS):
            return self._summary_reply(report, text, analysis, lang)

        topic = self._detect_topic(q_lower)
        if topic:
            return self._topic_reply(topic, report, text, analysis, lang)

        snippets = self._relevant_snippets(text, question)
        if snippets:
            return self._format_snippet_answer(report.original_filename, snippets, lang)

        return self._fallback_reply(report, text, analysis, lang)

    def _summary_reply(self, report: "Report", text: str, analysis: "Analysis | None", lang: str) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        preview_lines = lines[:8]
        figures = self.parser.extract_financial_figures(text)
        not_found = translate("not_found_in_document", lang)

        parts = [
            translate(
                "doc_summary_intro",
                lang,
                filename=report.original_filename,
                file_type=report.file_type.upper(),
                lines=len(lines),
            ),
            "",
        ]

        if analysis and analysis.status == "completed":
            if analysis.summary:
                parts.extend([translate("doc_analysis_summary", lang), analysis.summary, ""])
            for field, label in analysis_field_labels(lang):
                value = getattr(analysis, field, None)
                if value and value != not_found:
                    parts.extend([f"{label}: {value}", ""])

        found_figures = {k: v for k, v in figures.items() if v}
        if found_figures:
            parts.append(translate("doc_key_figures", lang))
            for key, value in found_figures.items():
                parts.append(f"- {topic_label(key, lang)}: {value}")
            parts.append("")

        parts.append(translate("doc_excerpt", lang))
        parts.extend(f"- {line}" for line in preview_lines)
        if len(lines) > len(preview_lines):
            parts.append(f"- {translate('doc_more_lines', lang, count=len(lines) - len(preview_lines))}")

        parts.extend(["", translate("doc_ask_topics", lang)])
        return "\n".join(parts)

    def _topic_reply(
        self,
        topic: str,
        report: "Report",
        text: str,
        analysis: "Analysis | None",
        lang: str,
    ) -> str:
        not_found = translate("not_found_in_document", lang)
        analysis_field_map = {
            "revenue": "revenue",
            "expenses": "expenses",
            "profit_loss": "profit_loss",
            "cash_flow": "cash_flow",
            "assets": "assets",
            "liabilities": "liabilities",
            "risks": "risks",
            "recommendations": "recommendations",
        }

        if analysis and analysis.status == "completed" and topic in analysis_field_map:
            value = getattr(analysis, analysis_field_map[topic], None)
            if value and value != not_found:
                return f"{translate('doc_from_analysis', lang, filename=report.original_filename)}\n\n{value}"

        keywords = self.TOPIC_KEYWORDS.get(topic, [topic])
        snippets = self._lines_matching_keywords(text, keywords)
        if snippets:
            label = topic_label(topic, lang)
            body = "\n".join(f"- {s}" for s in snippets[:6])
            return translate("doc_topic_refs", lang, label=label, filename=report.original_filename) + f"\n\n{body}"

        figures = self.parser.extract_financial_figures(text)
        if topic in figures and figures[topic]:
            return translate(
                "doc_mentions",
                lang,
                topic=topic_label(topic, lang),
                value=figures[topic],
            )

        if topic == "total":
            amount_lines = self._lines_matching_amounts(text)
            if amount_lines:
                body = "\n".join(f"- {line}" for line in amount_lines[:6])
                return translate("doc_amounts_found", lang, filename=report.original_filename) + f"\n\n{body}"

        if topic == "date":
            date_lines = self._lines_matching_dates(text)
            if date_lines:
                body = "\n".join(f"- {line}" for line in date_lines[:6])
                return translate("doc_dates_found", lang, filename=report.original_filename) + f"\n\n{body}"

        return translate(
            "doc_topic_missing",
            lang,
            topic=topic_label(topic, lang),
            filename=report.original_filename,
        )

    def _fallback_reply(self, report: "Report", text: str, analysis: "Analysis | None", lang: str) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        sample = "\n".join(f"- {line}" for line in lines[:5])
        reply = translate("doc_fallback_intro", lang, filename=report.original_filename) + f"\n\n{sample}"
        if len(lines) > 5:
            reply += f"\n- {translate('doc_more_lines', lang, count=len(lines) - 5)}"
        if analysis and analysis.summary:
            reply += f"\n\n{translate('doc_analysis_summary', lang)} {analysis.summary}"
        reply += f"\n\n{translate('doc_fallback_hints', lang)}"
        return reply

    def _detect_topic(self, q_lower: str) -> str | None:
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            if any(keyword in q_lower for keyword in keywords):
                return topic
        return None

    def _relevant_snippets(self, text: str, question: str) -> list[str]:
        words = {
            w.lower()
            for w in re.findall(r"[\u0600-\u06FFa-zA-Z]{3,}", question)
            if w.lower() not in self.STOP_WORDS
        }
        if not words:
            return []
        return self._lines_matching_keywords(text, list(words), min_matches=1)

    def _lines_matching_keywords(
        self,
        text: str,
        keywords: list[str],
        min_matches: int = 1,
    ) -> list[str]:
        results: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            lower = stripped.lower()
            matches = sum(1 for kw in keywords if kw.lower() in lower or kw in stripped)
            if matches >= min_matches:
                results.append(stripped)
        return results

    def _lines_matching_amounts(self, text: str) -> list[str]:
        pattern = re.compile(r"(\$|€|£|USD|SAR|OMR|ر\.?س)?\s?\d[\d,]*(?:\.\d{2})?", re.IGNORECASE)
        results: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped and pattern.search(stripped):
                results.append(stripped)
        return results

    def _lines_matching_dates(self, text: str) -> list[str]:
        patterns = [
            r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
            r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b",
        ]
        results: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if any(re.search(p, stripped, re.IGNORECASE) for p in patterns):
                results.append(stripped)
        return results

    def _format_snippet_answer(self, filename: str, snippets: list[str], lang: str) -> str:
        body = "\n".join(f"- {s}" for s in snippets[:8])
        return translate("doc_related_snippets", lang, filename=filename) + f"\n\n{body}"
