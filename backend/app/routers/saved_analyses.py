from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.deps import resolve_language
from app.schemas import (
    BulkDeleteSavedAnalysesRequest,
    BulkDeleteSavedAnalysesResponse,
    ReanalyzeSavedAnalysisRequest,
    SaveAnalysisRequest,
    SaveBatchAnalysisRequest,
    SavedAnalysisDetailResponse,
    SavedAnalysisResponse,
    UpdateSavedAnalysisRequest,
)
from app.services.saved_analysis_service import SavedAnalysisService

router = APIRouter(prefix="/saved-analyses", tags=["saved-analyses"])


def get_saved_analysis_service() -> SavedAnalysisService:
    return SavedAnalysisService(get_settings())


@router.get("", response_model=list[SavedAnalysisResponse])
def list_saved_analyses(db: Session = Depends(get_db)):
    return get_saved_analysis_service().list_saved(db)


@router.post("/bulk-delete", response_model=BulkDeleteSavedAnalysesResponse)
def bulk_delete_saved_analyses(body: BulkDeleteSavedAnalysesRequest, db: Session = Depends(get_db)):
    deleted_count = get_saved_analysis_service().delete_saved_many(db, body.saved_ids)
    return BulkDeleteSavedAnalysesResponse(deleted_count=deleted_count)


@router.get("/{saved_id}", response_model=SavedAnalysisDetailResponse)
def get_saved_analysis(saved_id: int, db: Session = Depends(get_db)):
    item = get_saved_analysis_service().get_saved(db, saved_id)
    content = get_saved_analysis_service().get_saved_content(db, saved_id)
    return SavedAnalysisDetailResponse(**SavedAnalysisResponse.model_validate(item).model_dump(), content=content)


@router.post("/reports/{report_id}", response_model=SavedAnalysisResponse, status_code=201)
def save_report_analysis(
    report_id: int,
    body: SaveAnalysisRequest,
    db: Session = Depends(get_db),
):
    return get_saved_analysis_service().save_report_analysis(
        db, report_id, body.title, analysis_id=body.analysis_id
    )


@router.post("/batches/{batch_id}", response_model=SavedAnalysisResponse, status_code=201)
def save_batch_analysis(
    batch_id: int,
    body: SaveBatchAnalysisRequest,
    db: Session = Depends(get_db),
):
    return get_saved_analysis_service().save_batch_analysis(
        db, batch_id, body.title, batch_analysis_id=body.batch_analysis_id
    )


@router.patch("/{saved_id}", response_model=SavedAnalysisDetailResponse)
def update_saved_analysis(
    saved_id: int,
    body: UpdateSavedAnalysisRequest,
    db: Session = Depends(get_db),
):
    service = get_saved_analysis_service()
    item = service.update_saved(db, saved_id, body.model_dump(exclude_unset=True))
    content = service.get_saved_content(db, saved_id)
    return SavedAnalysisDetailResponse(**SavedAnalysisResponse.model_validate(item).model_dump(), content=content)


@router.post("/{saved_id}/reanalyze", response_model=SavedAnalysisDetailResponse)
async def reanalyze_saved_analysis(
    saved_id: int,
    body: ReanalyzeSavedAnalysisRequest,
    accept_language: str | None = Header(default=None, alias="Accept-Language"),
    db: Session = Depends(get_db),
):
    service = get_saved_analysis_service()
    language = resolve_language(accept_language, body.language)
    item = await service.reanalyze_saved(db, saved_id, body.criteria, language=language)
    content = service.get_saved_content(db, saved_id)
    return SavedAnalysisDetailResponse(**SavedAnalysisResponse.model_validate(item).model_dump(), content=content)


@router.delete("/{saved_id}", status_code=204)
def delete_saved_analysis(saved_id: int, db: Session = Depends(get_db)):
    get_saved_analysis_service().delete_saved(db, saved_id)
