from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.deps import resolve_language
from app.schemas import ChatMessageCreate, ChatMessageResponse, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/reports/{report_id}/chat", tags=["chat"])


def get_chat_service() -> ChatService:
    return ChatService(get_settings())


@router.get("", response_model=list[ChatMessageResponse])
def list_chat_messages(report_id: int, db: Session = Depends(get_db)):
    return get_chat_service().list_messages(db, report_id)


@router.post("", response_model=ChatResponse, status_code=201)
async def send_chat_message(
    report_id: int,
    body: ChatMessageCreate,
    accept_language: str | None = Header(default=None, alias="Accept-Language"),
    db: Session = Depends(get_db),
):
    language = resolve_language(accept_language, body.language)
    user_msg, assistant_msg = await get_chat_service().send_message(
        db, report_id, body.message, language=language
    )
    return ChatResponse(user_message=user_msg, assistant_message=assistant_msg)
