"""Custom exceptions and global FastAPI exception handlers."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """Base exception for all service errors."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AudioProcessingError(ServiceError):
    def __init__(self, message: str = "Audio processing failed") -> None:
        super().__init__(message, status_code=422)


class TranscriptionError(ServiceError):
    def __init__(self, message: str = "Transcription failed") -> None:
        super().__init__(message, status_code=500)


class LLMError(ServiceError):
    def __init__(self, message: str = "LLM analysis failed") -> None:
        super().__init__(message, status_code=500)


class ScoringError(ServiceError):
    def __init__(self, message: str = "Scoring computation failed") -> None:
        super().__init__(message, status_code=500)


class AssessmentNotFoundError(ServiceError):
    def __init__(self, identifier: str = "") -> None:
        detail = f"Assessment not found: {identifier}" if identifier else "Assessment not found"
        super().__init__(detail, status_code=404)


class ImageSemanticsNotFoundError(ServiceError):
    def __init__(self, assessment_id: str = "", image_id: str = "") -> None:
        detail = f"Image semantics not found for assessment={assessment_id} image={image_id}"
        super().__init__(detail, status_code=404)


def _error_response(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": message},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers. Never expose stack traces."""

    @app.exception_handler(ServiceError)
    async def service_error_handler(_request: Request, exc: ServiceError) -> JSONResponse:
        logger.error("Service error: %s", exc.message, exc_info=False)
        return _error_response(exc.status_code, exc.message)

    @app.exception_handler(ValueError)
    async def value_error_handler(_request: Request, exc: ValueError) -> JSONResponse:
        logger.warning("Validation error: %s", exc)
        return _error_response(400, str(exc))

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error")
        return _error_response(500, "Internal server error")
