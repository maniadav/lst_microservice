"""FastAPI application entry point.

Lifespan handler:
  - Conditionally connects to MongoDB (only when needed)
  - Loads WhisperX model (once, stays in memory)
  - Initializes all service instances
  - Logs available endpoints on startup
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.routing import APIRoute

from app.api.v1.health import router as health_router
from app.api.v1.router import router as v1_router
from app.assessments.lst.scorer import LSTScorer
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.database.mongodb import close_db, connect_db, get_database
from app.repositories.assessment_repository import AssessmentRepository
from app.services.groq.client import GroqClient
from app.services.language.analyzer import LanguageAnalyzer
from app.services.pipeline import LSTAnalysisService
from app.services.scoring.engine import ScoringEngine
from app.services.semantic.comparator import SemanticComparator
from app.services.semantic.providers import GroqSceneSimilarityProvider
from app.services.whisper.transcriber import WhisperTranscriber

logger = logging.getLogger(__name__)

# Module-level singletons — initialized during lifespan
_transcriber: WhisperTranscriber | None = None
_groq_client: GroqClient | None = None
_analysis_service: LSTAnalysisService | None = None


def get_transcriber() -> WhisperTranscriber | None:
    return _transcriber


def get_analysis_service() -> LSTAnalysisService:
    if _analysis_service is None:
        raise RuntimeError("Analysis service not initialized")
    return _analysis_service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle."""
    global _transcriber, _groq_client, _analysis_service

    setup_logging()
    logger.info("Starting LST Microservice")

    # 1. Conditionally connect to MongoDB
    if settings.is_mongodb_required:
        await connect_db()
    else:
        logger.info(
            "MongoDB connection skipped (SEMANTICS_SOURCE=%s, SAVE_RESULTS_TO_DB=%s)",
            settings.SEMANTICS_SOURCE,
            settings.SAVE_RESULTS_TO_DB,
        )

    # 2. Load WhisperX model (downloads to cache on first run)
    _transcriber = WhisperTranscriber()
    try:
        _transcriber.load_model()
    except Exception:
        logger.exception("Failed to load WhisperX model — transcription will be unavailable")

    # 3. Initialize services
    _groq_client = GroqClient()

    similarity_provider = GroqSceneSimilarityProvider(_groq_client)
    semantic_comparator = SemanticComparator(similarity_provider)
    scoring_engine = ScoringEngine()
    language_analyzer = LanguageAnalyzer(_groq_client)
    lst_scorer = LSTScorer(scoring_engine, semantic_comparator)

    db = get_database()
    repository = AssessmentRepository(db) if db else AssessmentRepository(None)

    _analysis_service = LSTAnalysisService(
        transcriber=_transcriber,
        language_analyzer=language_analyzer,
        lst_scorer=lst_scorer,
        repository=repository,
    )

    # 4. Log startup summary
    _log_startup_summary(app)

    yield

    # Shutdown
    logger.info("Shutting down LST Microservice")
    if _groq_client:
        await _groq_client.close()
    if settings.is_mongodb_required:
        await close_db()


def _log_startup_summary(app: FastAPI) -> None:
    """Log configuration summary and all registered endpoints."""
    logger.info("=" * 60)
    logger.info("LST Microservice ready")
    logger.info("=" * 60)

    logger.info("Configuration:")
    logger.info("  Semantics source  : %s", settings.SEMANTICS_SOURCE)
    logger.info("  Save results to DB: %s", settings.SAVE_RESULTS_TO_DB)
    logger.info("  MongoDB connected : %s", settings.is_mongodb_required)
    logger.info("  WhisperX model    : %s", settings.WHISPER_MODEL_NAME)
    logger.info("  WhisperX device   : %s", settings.WHISPER_DEVICE)
    logger.info("  Groq model        : %s", settings.GROQ_MODEL_NAME)
    logger.info("  Auth enabled      : %s", bool(settings.API_KEY))

    logger.info("")
    logger.info("Server: http://0.0.0.0:8000")
    logger.info("Docs:   http://0.0.0.0:8000/docs")
    logger.info("")
    logger.info("Endpoints:")
    for route in app.routes:
        if isinstance(route, APIRoute):
            methods = ", ".join(route.methods) if route.methods else "GET"
            logger.info("  %-6s %s", methods, route.path)

    logger.info("=" * 60)


app = FastAPI(
    title="LST Language Assessment Service",
    description="Language Sampling Task analysis for autism and speech-language assessments",
    version="1.0.0",
    lifespan=lifespan,
)

register_exception_handlers(app)
app.include_router(v1_router)
app.include_router(health_router)
