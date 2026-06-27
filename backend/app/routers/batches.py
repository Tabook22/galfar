from fastapi import APIRouter, Depends, File, Form, Header, UploadFile
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import BatchAnalysis, get_db
from app.deps import resolve_language
from app.exceptions import AppError
from app.i18n.locale import translate
from app.schemas import (
    BatchAnalysisRequest,
    BatchAnalysisResponse,
    BatchChatMessageCreate,
    BatchChatMessageResponse,
    BatchChatResponse,
    BatchDetailResponse,
    BatchReportAnalysesResponse,
    BatchReportAnalysisItem,
    BatchResponse,
)
from app.services.batch_chat_service import BatchChatService
from app.services.batch_service import BatchService
from app.services.file_service import FileService
from app.services.report_service import ReportService

router = APIRouter(prefix="/batches", tags=["batches"])


def get_batch_service() -> BatchService:
    return BatchService(get_settings())


def get_batch_chat_service() -> BatchChatService:
    return BatchChatService(get_settings())


def get_report_service() -> ReportService:
    return ReportService(FileService(get_settings()))


def _to_batch_response(db: Session, batch, report_count: int | None = None) -> BatchResponse:
    from app.database import Report

    if report_count is None:
        report_count = db.query(Report).filter(Report.batch_id == batch.id).count()
    latest = (
        db.query(BatchAnalysis)
        .filter(BatchAnalysis.batch_id == batch.id, BatchAnalysis.status == "completed")
        .order_by(BatchAnalysis.created_at.desc())
        .first()
    )
    return BatchResponse(
        id=batch.id,
        name=batch.name,
        status=batch.status,
        report_count=report_count,
        has_analysis=latest is not None,
        latest_analysis_id=latest.id if latest else None,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
    )


@router.get("", response_model=list[BatchResponse])
def list_batches(db: Session = Depends(get_db)):
    batches = get_batch_service().list_batches(db)
    return [_to_batch_response(db, b) for b in batches]


@router.post("", response_model=BatchDetailResponse, status_code=201)
async def create_batch(
    files: list[UploadFile] = File(...),
    name: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    batch = await get_batch_service().create_batch_with_files(db, files, name)
    reports = get_batch_service().get_batch_reports(db, batch.id)
    base = _to_batch_response(db, batch)
    return BatchDetailResponse(
        **base.model_dump(),
        reports=[get_report_service()._to_response(db, r) for r in reports],
    )


@router.get("/{batch_id}", response_model=BatchDetailResponse)
def get_batch(batch_id: int, db: Session = Depends(get_db)):
    batch = get_batch_service().get_batch(db, batch_id)
    reports = get_batch_service().get_batch_reports(db, batch_id)
    base = _to_batch_response(db, batch)
    return BatchDetailResponse(
        **base.model_dump(),
        reports=[get_report_service()._to_response(db, r) for r in reports],
    )


@router.delete("/{batch_id}", status_code=204)
def delete_batch(batch_id: int, db: Session = Depends(get_db)):
    get_batch_service().delete_batch(db, batch_id)


@router.post("/{batch_id}/analysis", response_model=BatchAnalysisResponse, status_code=201)
async def run_batch_analysis(
    batch_id: int,
    body: BatchAnalysisRequest | None = None,
    accept_language: str | None = Header(default=None, alias="Accept-Language"),
    db: Session = Depends(get_db),
):
    force = body.force if body else False
    language = resolve_language(accept_language, body.language if body else None)
    return await get_batch_service().run_batch_analysis(db, batch_id, language=language, force=force)


@router.get("/{batch_id}/analysis/latest", response_model=BatchAnalysisResponse)
def get_latest_batch_analysis(
    batch_id: int,
    accept_language: str | None = Header(default=None, alias="Accept-Language"),
    db: Session = Depends(get_db),
):
    get_batch_service().get_batch(db, batch_id)
    analysis = get_batch_service().get_latest_batch_analysis(db, batch_id)
    if not analysis:
        lang = resolve_language(accept_language)
        raise AppError(translate("no_analysis_found", lang), 404)
    return analysis


@router.get("/{batch_id}/analysis/history", response_model=list[BatchAnalysisResponse])
def list_batch_analyses(batch_id: int, db: Session = Depends(get_db)):
    return get_batch_service().list_batch_analyses(db, batch_id)


@router.get("/{batch_id}/report-analyses", response_model=BatchReportAnalysesResponse)
def get_batch_report_analyses(batch_id: int, db: Session = Depends(get_db)):
    get_batch_service().get_batch(db, batch_id)
    items = []
    for report, analysis in get_batch_service().get_batch_report_analyses(db, batch_id):
        items.append(
            BatchReportAnalysisItem(
                report_id=report.id,
                original_filename=report.original_filename,
                analysis=analysis,
            )
        )
    return BatchReportAnalysesResponse(batch_id=batch_id, items=items)


@router.get("/{batch_id}/chat", response_model=list[BatchChatMessageResponse])
def list_batch_chat(batch_id: int, db: Session = Depends(get_db)):
    return get_batch_chat_service().list_messages(db, batch_id)


@router.post("/{batch_id}/chat", response_model=BatchChatResponse, status_code=201)
async def send_batch_chat(
    batch_id: int,
    body: BatchChatMessageCreate,
    accept_language: str | None = Header(default=None, alias="Accept-Language"),
    db: Session = Depends(get_db),
):
    language = resolve_language(accept_language, body.language)
    user_msg, assistant_msg = await get_batch_chat_service().send_message(
        db, batch_id, body.message, language=language
    )
    return BatchChatResponse(user_message=user_msg, assistant_message=assistant_msg)
