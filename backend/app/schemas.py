from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ReportBase(BaseModel):
    original_filename: str
    file_type: str
    file_size: int


class ReportCreate(BaseModel):
    pass


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_id: Optional[int] = None
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    status: str
    created_at: datetime
    updated_at: datetime
    has_analysis: bool = False
    latest_analysis_id: Optional[int] = None


class ReportDetailResponse(ReportResponse):
    extracted_text_preview: Optional[str] = None
    analysis_count: int = 0
    chat_message_count: int = 0


class BulkDeleteReportsRequest(BaseModel):
    report_ids: list[int] = Field(..., min_length=1)


class BulkDeleteReportsResponse(BaseModel):
    deleted_count: int


class BulkDeleteSavedAnalysesRequest(BaseModel):
    saved_ids: list[int] = Field(..., min_length=1)


class BulkDeleteSavedAnalysesResponse(BaseModel):
    deleted_count: int


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    report_id: int
    status: str
    summary: Optional[str] = None
    revenue: Optional[str] = None
    expenses: Optional[str] = None
    profit_loss: Optional[str] = None
    cash_flow: Optional[str] = None
    assets: Optional[str] = None
    liabilities: Optional[str] = None
    risks: Optional[str] = None
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    recommendations: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime


class AnalysisRequest(BaseModel):
    force: bool = False
    language: str = "en"


class ChatMessageCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    language: str = "en"


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    report_id: int
    role: str
    content: str
    created_at: datetime


class ChatResponse(BaseModel):
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse


class DashboardStats(BaseModel):
    total_reports: int
    analyzed_reports: int
    pending_reports: int
    total_chat_messages: int


class ErrorResponse(BaseModel):
    detail: str


class BatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: str
    report_count: int = 0
    has_analysis: bool = False
    latest_analysis_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class BatchDetailResponse(BatchResponse):
    reports: list[ReportResponse] = []


class BatchAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_id: int
    status: str
    report_count: int
    summary: Optional[str] = None
    revenue: Optional[str] = None
    expenses: Optional[str] = None
    profit_loss: Optional[str] = None
    cash_flow: Optional[str] = None
    assets: Optional[str] = None
    liabilities: Optional[str] = None
    risks: Optional[str] = None
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    recommendations: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime


class BatchAnalysisRequest(BaseModel):
    force: bool = False
    language: str = "en"


class BatchChatMessageCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    language: str = "en"


class BatchChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_id: int
    role: str
    content: str
    created_at: datetime


class BatchChatResponse(BaseModel):
    user_message: BatchChatMessageResponse
    assistant_message: BatchChatMessageResponse


class BatchReportAnalysisItem(BaseModel):
    report_id: int
    original_filename: str
    analysis: AnalysisResponse | None = None


class BatchReportAnalysesResponse(BaseModel):
    batch_id: int
    items: list[BatchReportAnalysisItem] = []


class SaveAnalysisRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    analysis_id: Optional[int] = None


class SaveBatchAnalysisRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    batch_analysis_id: Optional[int] = None


class SavedAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    filename: str
    source_type: str
    source_name: str
    report_id: Optional[int] = None
    batch_id: Optional[int] = None
    analysis_id: Optional[int] = None
    batch_analysis_id: Optional[int] = None
    created_at: datetime


class SavedAnalysisDetailResponse(SavedAnalysisResponse):
    content: dict


class SavedAnalysisCustomSection(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = ""


class UpdateSavedAnalysisRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    summary: Optional[str] = None
    revenue: Optional[str] = None
    expenses: Optional[str] = None
    profit_loss: Optional[str] = None
    cash_flow: Optional[str] = None
    assets: Optional[str] = None
    liabilities: Optional[str] = None
    risks: Optional[str] = None
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    recommendations: Optional[str] = None
    custom_sections: Optional[list[SavedAnalysisCustomSection]] = None
    document_html: Optional[str] = None


class ReanalyzeSavedAnalysisRequest(BaseModel):
    criteria: str = Field(..., min_length=1, max_length=4000)
    language: str = "en"


class BilingualText(BaseModel):
    ar: str = ""
    en: str = ""


class CompanySettingsResponse(BaseModel):
    company_name: BilingualText
    page_title: BilingualText
    tagline: BilingualText = BilingualText()
    logo_url: Optional[str] = None
    address: BilingualText = BilingualText()
    industry: BilingualText = BilingualText()
    history: BilingualText = BilingualText()
    introduction_html: BilingualText = BilingualText()
    phone: str = ""
    email: str = ""
    website: str = ""
    updated_at: Optional[str] = None


class UpdateCompanySettingsRequest(BaseModel):
    company_name: BilingualText
    page_title: BilingualText
    tagline: BilingualText = BilingualText()
    address: BilingualText = BilingualText()
    industry: BilingualText = BilingualText()
    history: BilingualText = BilingualText()
    introduction_html: BilingualText = BilingualText()
    phone: str = Field(default="", max_length=100)
    email: str = Field(default="", max_length=200)
    website: str = Field(default="", max_length=500)
