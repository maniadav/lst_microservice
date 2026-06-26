"""Health check endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter

from app.core.config import settings
from app.database.mongodb import get_database, is_connected

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> dict:
    """Check service health: DB connectivity and WhisperX model status."""
    checks: dict = {"status": "healthy"}

    # MongoDB
    if settings.is_mongodb_required:
        try:
            db = get_database()
            if db is not None:
                await db.command("ping")
                checks["mongodb"] = "connected"
            else:
                checks["mongodb"] = "disconnected"
                checks["status"] = "unhealthy"
        except Exception:
            checks["mongodb"] = "disconnected"
            checks["status"] = "unhealthy"
    else:
        checks["mongodb"] = "disabled"

    # WhisperX
    from app.main import get_transcriber

    transcriber = get_transcriber()
    checks["whisperx"] = "loaded" if transcriber and transcriber.is_loaded else "not_loaded"

    return checks
