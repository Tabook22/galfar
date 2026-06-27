import mimetypes

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import FileResponse

from app.config import get_settings
from app.exceptions import AppError
from app.schemas import CompanySettingsResponse, UpdateCompanySettingsRequest
from app.services.company_settings_service import CompanySettingsService

router = APIRouter(prefix="/settings", tags=["settings"])


def get_company_settings_service() -> CompanySettingsService:
    return CompanySettingsService(get_settings())


@router.get("/company", response_model=CompanySettingsResponse)
def get_company_settings():
    return get_company_settings_service().get_settings()


@router.put("/company", response_model=CompanySettingsResponse)
def update_company_settings(body: UpdateCompanySettingsRequest):
    return get_company_settings_service().update_settings(body.model_dump())


@router.post("/company/logo", response_model=CompanySettingsResponse)
async def upload_company_logo(file: UploadFile = File(...)):
    content = await file.read()
    return get_company_settings_service().save_logo(content, file.filename or "logo.png")


@router.delete("/company/logo", response_model=CompanySettingsResponse)
def delete_company_logo():
    return get_company_settings_service().delete_logo()


@router.get("/company/logo")
def get_company_logo():
    service = get_company_settings_service()
    path = service.get_logo_path()
    if not path:
        raise AppError("Company logo not found.", 404)
    media_type, _ = mimetypes.guess_type(path.name)
    return FileResponse(path=path, media_type=media_type or "application/octet-stream")
