"""LST analysis endpoint — POST /api/v1/lst/analyze."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.core.logging import generate_request_id, request_id_var
from app.core.security import verify_api_key
from app.database.mongodb import get_database
from app.repositories.assessment_repository import AssessmentRepository
from app.schemas.analysis import AnalysisResponse
from app.utils.audio import validate_audio_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lst", tags=["LST"])


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_lst(
    audio: UploadFile = File(...),
    assessmentId: str = Form(...),
    imageId: str = Form(...),
    childId: str = Form(...),
    language: str = Form("auto"),
    # _api_key: str | None = Depends(verify_api_key),
) -> AnalysisResponse:
    """Analyze an LST audio recording.

    Accepts multipart/form-data with:
    - audio: wav/mp3/m4a file
    - assessmentId: assessment identifier
    - imageId: assessment image identifier
    - childId: child identifier
    - language: optional, defaults to auto-detection
    """
    rid = generate_request_id()
    request_id_var.set(rid)

    logger.info(
        "LST analysis request started | request_id=%s assessment=%s image=%s child=%s language=%s",
        rid,
        assessmentId,
        imageId,
        childId,
        language,
    )

    try:
        # Read and validate audio
        logger.debug("Reading uploaded audio content...")
        content = await audio.read()
        size_bytes = len(content)
        logger.info(
            "Audio read successfully | filename=%s content_type=%s size=%d bytes",
            audio.filename,
            audio.content_type,
            size_bytes,
        )

        logger.debug("Validating audio file parameters...")
        validate_audio_file(
            filename=audio.filename or "",
            content_type=audio.content_type,
            size=size_bytes,
        )
        logger.info("Audio validation passed")

        # Get pipeline service from app state (injected during startup)
        logger.debug("Retrieving analysis service from app state...")
        from app.main import get_analysis_service
        service = get_analysis_service()
        logger.debug("Analysis service retrieved successfully")

        logger.info("Starting LST pipeline analysis...")
        result = await service.analyze(
            audio_content=content,
            audio_filename=audio.filename or "audio.wav",
            assessment_id=assessmentId,
            image_id=imageId,
            child_id=childId,
            language=language,
        )

        logger.info(
            "LST pipeline analysis completed successfully | overall_score=%.2f language=%s words=%d sentences=%d",
            result.overall_score,
            result.language,
            result.language_metrics.total_words,
            result.language_metrics.sentence_count,
        )
        return result

    except Exception as e:
        logger.exception(
            "LST analysis failed | request_id=%s assessment=%s child=%s error=%s",
            rid,
            assessmentId,
            childId,
            str(e),
        )
        raise

# @router.post("/diarization", response_model=any)
# @router.post("/score", response_model=any)