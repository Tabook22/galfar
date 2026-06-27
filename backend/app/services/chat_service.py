from sqlalchemy.orm import Session

from app.config import Settings
from app.database import Analysis, ChatMessage, Report
from app.exceptions import ChatError, ReportNotFoundError
from app.services.document_chat_service import DocumentChatService
from app.services.llm_service import LLMService
from app.services.report_parser import ReportParser


class ChatService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm = LLMService(settings)
        self.parser = ReportParser()
        self.document_chat = DocumentChatService()

    def list_messages(self, db: Session, report_id: int) -> list[ChatMessage]:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise ReportNotFoundError(report_id)
        return (
            db.query(ChatMessage)
            .filter(ChatMessage.report_id == report_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )

    async def send_message(
        self, db: Session, report_id: int, user_message: str, language: str = "en"
    ) -> tuple[ChatMessage, ChatMessage]:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise ReportNotFoundError(report_id)

        if not report.extracted_text:
            try:
                report.extracted_text = self.parser.extract_text(report.file_path, report.file_type)
                db.commit()
            except Exception as exc:
                raise ChatError(f"Could not read report content: {exc}") from exc

        user_msg = ChatMessage(report_id=report_id, role="user", content=user_message)
        db.add(user_msg)
        db.commit()
        db.refresh(user_msg)

        history = [
            {"role": m.role, "content": m.content}
            for m in self.list_messages(db, report_id)
            if m.id != user_msg.id
        ]

        analysis = self._get_latest_completed_analysis(db, report_id)
        analysis_context = self._build_analysis_context(analysis, language) if analysis else None

        try:
            llm_reply = await self.llm.chat_with_report(
                report.extracted_text or "",
                report.original_filename,
                history,
                user_message,
                language,
                analysis_context=analysis_context,
            )
            if llm_reply:
                assistant_content = llm_reply
            else:
                assistant_content = self.document_chat.reply(user_message, report, analysis, language)
        except Exception as exc:
            raise ChatError(f"Chat request failed: {exc}") from exc

        assistant_msg = ChatMessage(report_id=report_id, role="assistant", content=assistant_content)
        db.add(assistant_msg)
        db.commit()
        db.refresh(assistant_msg)
        return user_msg, assistant_msg

    def _get_latest_completed_analysis(self, db: Session, report_id: int) -> Analysis | None:
        return (
            db.query(Analysis)
            .filter(Analysis.report_id == report_id, Analysis.status == "completed")
            .order_by(Analysis.created_at.desc())
            .first()
        )

    def _build_analysis_context(self, analysis: Analysis, language: str) -> str:
        from app.i18n.locale import analysis_field_labels, normalize_language

        lang = normalize_language(language)
        parts = []
        if analysis.summary:
            parts.append(analysis.summary)
        for field, label in analysis_field_labels(lang):
            value = getattr(analysis, field, None)
            if value:
                parts.append(f"{label}: {value}")
        return "\n\n".join(parts)[:12000]
