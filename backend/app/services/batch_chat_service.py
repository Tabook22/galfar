from sqlalchemy.orm import Session

from app.config import Settings
from app.database import Analysis, BatchChatMessage
from app.exceptions import BatchNotFoundError, ChatError
from app.i18n.locale import normalize_language
from app.services.batch_document_chat_service import BatchDocumentChatService
from app.services.batch_service import BatchService
from app.services.llm_service import LLMService


class BatchChatService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm = LLMService(settings)
        self.batch_service = BatchService(settings)
        self.document_chat = BatchDocumentChatService()

    def list_messages(self, db: Session, batch_id: int) -> list[BatchChatMessage]:
        self.batch_service.get_batch(db, batch_id)
        return (
            db.query(BatchChatMessage)
            .filter(BatchChatMessage.batch_id == batch_id)
            .order_by(BatchChatMessage.created_at.asc())
            .all()
        )

    async def send_message(
        self, db: Session, batch_id: int, user_message: str, language: str = "en"
    ) -> tuple[BatchChatMessage, BatchChatMessage]:
        lang = normalize_language(language)
        batch = self.batch_service.get_batch(db, batch_id)
        reports = self.batch_service.get_batch_reports(db, batch_id)

        user_msg = BatchChatMessage(batch_id=batch_id, role="user", content=user_message)
        db.add(user_msg)
        db.commit()
        db.refresh(user_msg)

        combined = self.batch_service._build_combined_context(reports)
        batch_analysis = self.batch_service.get_latest_batch_analysis(db, batch_id)
        report_analyses = self._get_report_analyses(db, reports)
        history = [
            {"role": m.role, "content": m.content}
            for m in self.list_messages(db, batch_id)
            if m.id != user_msg.id
        ]

        try:
            analysis_context = self.document_chat.build_analysis_context(
                batch.name, reports, batch_analysis, report_analyses, lang
            )
            llm_reply = await self.llm.chat_with_batch(
                combined, batch.name, history, user_message, lang, analysis_context=analysis_context
            )
            if llm_reply:
                content = llm_reply
            else:
                content = self.document_chat.reply(
                    user_message,
                    batch.name,
                    reports,
                    batch_analysis,
                    report_analyses,
                    lang,
                )
        except Exception as exc:
            raise ChatError(f"Batch chat failed: {exc}") from exc

        assistant_msg = BatchChatMessage(batch_id=batch_id, role="assistant", content=content)
        db.add(assistant_msg)
        db.commit()
        db.refresh(assistant_msg)
        return user_msg, assistant_msg

    def _get_report_analyses(self, db: Session, reports) -> dict[int, Analysis]:
        result: dict[int, Analysis] = {}
        for report in reports:
            analysis = (
                db.query(Analysis)
                .filter(Analysis.report_id == report.id, Analysis.status == "completed")
                .order_by(Analysis.created_at.desc())
                .first()
            )
            if analysis:
                result[report.id] = analysis
        return result
