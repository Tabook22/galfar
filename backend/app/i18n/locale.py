"""Backend localization helpers."""

from __future__ import annotations

SUPPORTED_LANGUAGES = {"en", "ar"}


def normalize_language(value: str | None) -> str:
    if not value:
        return "en"
    lang = value.strip().lower().split(",")[0].split("-")[0]
    return lang if lang in SUPPORTED_LANGUAGES else "en"


def language_instruction(language: str) -> str:
    if language == "ar":
        return "Respond entirely in Modern Standard Arabic."
    return "Respond entirely in English."


MESSAGES: dict[str, dict[str, str]] = {
    "analysis_summary_heuristic": {
        "en": "Heuristic analysis of '{filename}' ({words} words extracted). Connect an LLM provider for deeper insights.",
        "ar": "تحليل استرشادي لـ '{filename}' (تم استخراج {words} كلمة). فعّل مزود LLM للحصول على رؤى أعمق.",
    },
    "not_found_in_document": {
        "en": "Not explicitly found in the document.",
        "ar": "غير موجود بوضوح في المستند.",
    },
    "report_not_found": {
        "en": "Report with id {report_id} not found.",
        "ar": "لم يتم العثور على التقرير برقم {report_id}.",
    },
    "no_analysis_found": {
        "en": "No analysis found for this report.",
        "ar": "لم يتم العثور على تحليل لهذا التقرير.",
    },
    "analysis_labels": {
        "en": "summary,revenue,expenses,profit_loss,cash_flow,assets,liabilities,risks,strengths,weaknesses,recommendations",
        "ar": "الملخص,الإيرادات,المصروفات,الربح / الخسارة,التدفق النقدي,الأصول,الالتزامات,المخاطر,نقاط القوة,نقاط الضعف,التوصيات",
    },
    "doc_no_text": {
        "en": "I could not read text from '{filename}'. The file may be scanned/image-only. Try uploading a text-based PDF or run Analysis first.",
        "ar": "تعذر قراءة النص من '{filename}'. قد يكون الملف ممسوحًا ضوئيًا أو صورة فقط. جرّب رفع PDF نصي أو نفّذ التحليل أولًا.",
    },
    "doc_summary_intro": {
        "en": "Here are details from {filename} ({file_type}, {lines} lines extracted):",
        "ar": "إليك تفاصيل {filename} ({file_type}، تم استخراج {lines} سطرًا):",
    },
    "doc_analysis_summary": {
        "en": "Analysis summary:",
        "ar": "ملخص التحليل:",
    },
    "doc_key_figures": {
        "en": "Key figures detected in the document:",
        "ar": "الأرقام الرئيسية المكتشفة في المستند:",
    },
    "doc_excerpt": {
        "en": "Document excerpt:",
        "ar": "مقتطف من المستند:",
    },
    "doc_more_lines": {
        "en": "... and {count} more lines",
        "ar": "... و {count} سطرًا إضافيًا",
    },
    "doc_ask_topics": {
        "en": "Ask about specific topics like totals, dates, vendor, revenue, expenses, risks, or recommendations.",
        "ar": "اسأل عن مواضيع محددة مثل الإجمالي أو التاريخ أو البائع أو الإيرادات أو المصروفات أو المخاطر أو التوصيات.",
    },
    "doc_from_analysis": {
        "en": "From the analysis of '{filename}':",
        "ar": "من تحليل '{filename}':",
    },
    "doc_topic_refs": {
        "en": "{label} references in '{filename}':",
        "ar": "مراجع {label} في '{filename}':",
    },
    "doc_mentions": {
        "en": "The document mentions {topic}: {value}",
        "ar": "يذكر المستند {topic}: {value}",
    },
    "doc_amounts_found": {
        "en": "Amounts found in '{filename}':",
        "ar": "المبالغ الموجودة في '{filename}':",
    },
    "doc_dates_found": {
        "en": "Dates found in '{filename}':",
        "ar": "التواريخ الموجودة في '{filename}':",
    },
    "doc_topic_missing": {
        "en": "I did not find clear {topic} information in '{filename}'. Try running Analysis from the report page, or ask for a general summary.",
        "ar": "لم أجد معلومات واضحة عن {topic} في '{filename}'. جرّب تشغيل التحليل من صفحة التقرير، أو اطلب ملخصًا عامًا.",
    },
    "doc_fallback_intro": {
        "en": "I searched '{filename}' for your question. Here is what the document contains:",
        "ar": "بحثت في '{filename}' عن سؤالك. إليك ما يحتويه المستند:",
    },
    "doc_fallback_hints": {
        "en": "Try asking: \"Give me more details\", \"What is the total?\", \"What are the expenses?\", or \"Summarize this report\".",
        "ar": "جرّب أن تسأل: \"أعطني المزيد من التفاصيل\"، \"ما هو الإجمالي؟\"، \"ما هي المصروفات؟\"، أو \"لخص هذا التقرير\".",
    },
    "doc_related_snippets": {
        "en": "From '{filename}', related to your question:",
        "ar": "من '{filename}'، متعلق بسؤالك:",
    },
    "batch_doc_summary_intro": {
        "en": "Summary for batch '{batch_name}' ({count} reports):",
        "ar": "ملخص المجموعة '{batch_name}' ({count} تقارير):",
    },
    "batch_doc_combined_analysis": {
        "en": "Combined big-picture analysis:",
        "ar": "التحليل المجمّع — الصورة الكاملة:",
    },
    "batch_doc_per_report": {
        "en": "Saved analysis per report:",
        "ar": "التحليل المحفوظ لكل تقرير:",
    },
    "batch_doc_no_analysis": {
        "en": "Not analyzed yet",
        "ar": "لم يُحلَّل بعد",
    },
    "batch_doc_ask_topics": {
        "en": "Ask about combined revenue, expenses, risks, trends, or a specific report by filename.",
        "ar": "اسأل عن الإيرادات أو المصروفات أو المخاطر أو الاتجاهات المجمّعة، أو عن تقرير محدد باسم الملف.",
    },
    "batch_doc_from_combined": {
        "en": "From the combined analysis of '{batch_name}' — {topic}:",
        "ar": "من التحليل المجمّع لـ '{batch_name}' — {topic}:",
    },
    "batch_doc_topic_per_report": {
        "en": "{topic} across reports in '{batch_name}':",
        "ar": "{topic} عبر التقارير في '{batch_name}':",
    },
    "batch_doc_topic_refs": {
        "en": "{topic} references across '{batch_name}':",
        "ar": "مراجع {topic} عبر '{batch_name}':",
    },
    "batch_doc_topic_missing": {
        "en": "I did not find clear {topic} information in batch '{batch_name}'. Run \"Analyze all reports\" first to save analyses.",
        "ar": "لم أجد معلومات واضحة عن {topic} في المجموعة '{batch_name}'. نفّذ \"تحليل جميع التقارير\" أولًا لحفظ التحليلات.",
    },
    "batch_doc_related_snippets": {
        "en": "From batch '{batch_name}', related to your question:",
        "ar": "من المجموعة '{batch_name}'، متعلق بسؤالك:",
    },
    "batch_doc_fallback_intro": {
        "en": "I searched batch '{batch_name}' ({files}) for your question.",
        "ar": "بحثت في المجموعة '{batch_name}' ({files}) عن سؤالك.",
    },
    "batch_doc_analyzed_count": {
        "en": "{analyzed} of {total} reports have saved analyses.",
        "ar": "{analyzed} من {total} تقارير لديها تحليلات محفوظة.",
    },
    "batch_doc_run_analysis": {
        "en": "Run \"Analyze all reports\" to save combined and per-report analyses, then ask again.",
        "ar": "نفّذ \"تحليل جميع التقارير\" لحفظ التحليل المجمّع وتحليلات كل تقرير، ثم اسأل مجددًا.",
    },
    "batch_doc_context_intro": {
        "en": "Batch '{batch_name}' with {count} reports.",
        "ar": "المجموعة '{batch_name}' تضم {count} تقارير.",
    },
    "batch_doc_report_analysis": {
        "en": "{filename}: {summary}",
        "ar": "{filename}: {summary}",
    },
    "figure_labels": {
        "en": "revenue,expenses,profit_loss,cash_flow,assets,liabilities",
        "ar": "الإيرادات,المصروفات,الربح / الخسارة,التدفق النقدي,الأصول,الالتزامات",
    },
    "topic_labels": {
        "en": "revenue,expenses,profit_loss,cash_flow,assets,liabilities,risks,recommendations,total,date,vendor,items,tax",
        "ar": "الإيرادات,المصروفات,الربح / الخسارة,التدفق النقدي,الأصول,الالتزامات,المخاطر,التوصيات,الإجمالي,التاريخ,البائع,العناصر,الضريبة",
    },
}


def translate(key: str, language: str, **kwargs: str | int) -> str:
    lang = normalize_language(language)
    template = MESSAGES.get(key, {}).get(lang) or MESSAGES.get(key, {}).get("en", key)
    return template.format(**kwargs)


def analysis_field_labels(language: str) -> list[tuple[str, str]]:
    lang = normalize_language(language)
    keys = "summary,revenue,expenses,profit_loss,cash_flow,assets,liabilities,risks,strengths,weaknesses,recommendations".split(",")
    labels = MESSAGES["analysis_labels"][lang].split(",")
    return list(zip(keys, labels, strict=True))


def topic_label(topic: str, language: str) -> str:
    lang = normalize_language(language)
    keys = MESSAGES["topic_labels"]["en"].split(",")
    labels = MESSAGES["topic_labels"][lang].split(",")
    mapping = dict(zip(keys, labels, strict=True))
    return mapping.get(topic, topic.replace("_", " "))
