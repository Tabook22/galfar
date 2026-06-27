from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.deps import resolve_language
from app.schemas import AnalysisRequest, AnalysisResponse
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/reports/{report_id}/analysis", tags=["analysis"])


def get_analysis_service() -> AnalysisService:
    return AnalysisService(get_settings())


@router.get("", response_model=list[AnalysisResponse])
def list_analyses(report_id: int, db: Session = Depends(get_db)):
    return get_analysis_service().list_analyses(db, report_id)


@router.get("/latest", response_model=AnalysisResponse)
def get_latest_analysis(
    report_id: int,
    accept_language: str | None = Header(default=None, alias="Accept-Language"),
    db: Session = Depends(get_db),
):
    from app.database import Report
    from app.exceptions import AppError, ReportNotFoundError
    from app.i18n.locale import translate

    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise ReportNotFoundError(report_id)

    analysis = get_analysis_service().get_latest_analysis(db, report_id)
    if not analysis:
        lang = resolve_language(accept_language)
        raise AppError(translate("no_analysis_found", lang), 404)
    return analysis


@router.post("", response_model=AnalysisResponse, status_code=201)
async def run_analysis(
    report_id: int,
    body: AnalysisRequest | None = None,
    accept_language: str | None = Header(default=None, alias="Accept-Language"),
    db: Session = Depends(get_db),
):
    force = body.force if body else False
    language = resolve_language(accept_language, body.language if body else None)
    return await get_analysis_service().run_analysis(db, report_id, force=force, language=language)


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(report_id: int, analysis_id: int, db: Session = Depends(get_db)):
    analysis = get_analysis_service().get_analysis(db, analysis_id)
    if analysis.report_id != report_id:
        from app.exceptions import ReportNotFoundError

        raise ReportNotFoundError(report_id)
    return analysis
