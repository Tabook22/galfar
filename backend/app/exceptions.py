"""Custom exceptions for the application."""

from fastapi import HTTPException, status


class AppError(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ReportNotFoundError(AppError):
    def __init__(self, report_id: int):
        super().__init__(f"Report with id {report_id} not found.", status.HTTP_404_NOT_FOUND)


class BatchNotFoundError(AppError):
    def __init__(self, batch_id: int):
        super().__init__(f"Batch with id {batch_id} not found.", status.HTTP_404_NOT_FOUND)


class InvalidFileError(AppError):
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class AnalysisError(AppError):
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


class BatchAnalysisError(AppError):
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChatError(AppError):
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


class SavedAnalysisNotFoundError(AppError):
    def __init__(self, saved_id: int):
        super().__init__(f"Saved analysis with id {saved_id} not found.", status.HTTP_404_NOT_FOUND)
