"""LST analysis pipeline orchestrator.

Coordinates the full flow:
  Audio → WhisperX → LLM Analysis → Semantic Comparison → Scoring → Save → Response
"""

from __future__ import annotations

import logging
import os
import tempfile
import time
from typing import Any

from app.assessments.lst.scorer import LSTScorer
from app.core.exceptions import (
    AssessmentNotFoundError,
    AudioProcessingError,
    ImageSemanticsNotFoundError,
    TranscriptionError,
)
from app.models.assessment import (
    AssessmentResultDocument,
    LanguageMetricsDocument,
    SemanticMetricsDocument,
)
from app.repositories.assessment_repository import AssessmentRepository
from app.schemas.analysis import AnalysisResponse, LanguageMetrics, SemanticMetrics
from app.services.language.analyzer import LanguageAnalyzer
from app.services.whisper.transcriber import WhisperTranscriber

logger = logging.getLogger(__name__)


class LSTAnalysisService:
    """Orchestrates the complete LST analysis pipeline."""

    def __init__(
        self,
        transcriber: WhisperTranscriber,
        language_analyzer: LanguageAnalyzer,
        lst_scorer: LSTScorer,
        repository: AssessmentRepository,
    ) -> None:
        self._transcriber = transcriber
        self._analyzer = language_analyzer
        self._scorer = lst_scorer
        self._repository = repository

    async def analyze(
        self,
        audio_content: bytes,
        audio_filename: str,
        assessment_id: str,
        image_id: str,
        child_id: str,
        language: str = "auto",
    ) -> AnalysisResponse:
        """Run the full LST analysis pipeline.

        Steps:
            1. Save audio to temp file
            2. Run WhisperX transcription + diarization
            3. Send speaker-attributed transcript to LLM
            4. Load image semantics from MongoDB
            5. Compute deterministic scores
            6. Save result to MongoDB
            7. Return structured response
        """
        pipeline_start = time.monotonic()
        tmp_path: str | None = None

        try:
            # Step 1: Save audio to temp file
            suffix = _get_audio_suffix(audio_filename)
            tmp_path = _save_temp_audio(audio_content, suffix)
            logger.info("Saved audio to temp file: %s (%d bytes)", tmp_path, len(audio_content))

            # Step 2: Transcribe with WhisperX
            t0 = time.monotonic()
            try:
                transcription = self._transcriber.transcribe(tmp_path)
            except Exception as exc:
                raise TranscriptionError(f"WhisperX transcription failed: {exc}") from exc
            transcription_duration = time.monotonic() - t0
            logger.info(
                "Transcription complete in %.1fs | language=%s segments=%d",
                transcription_duration,
                transcription.language,
                len(transcription.segments),
                transcription.speaker_transcript
            )

            detected_language = language if language != "auto" else transcription.language

            # Step 3: LLM analysis (speaker ID + semantics + language metrics)
            t1 = time.monotonic()
            llm_result = {"child_transcript": "the boy is eating a cookie","observer_transcript": "the boy is eating a cookie"} #await self._analyzer.analyze(transcription.speaker_transcript)
            llm_duration = time.monotonic() - t1
            logger.info("LLM analysis complete in %.1fs", llm_duration)

            # Step 4: Load image semantics from MongoDB
            image_semantics = await self._repository.get_image_semantics(assessment_id, image_id)
            if not image_semantics:
                raise ImageSemanticsNotFoundError(assessment_id, image_id)

            # Step 5: Deterministic scoring
            t2 = time.monotonic()
            semantic_scores, language_scores, overall_score = await self._scorer.score(
                llm_result=llm_result,
                image_semantics=image_semantics,
            )
            scoring_duration = time.monotonic() - t2
            logger.info("Scoring complete in %.1fs | overall=%.2f", scoring_duration, overall_score)

            # Step 6: Save result to MongoDB
            lm = llm_result.language_metrics
            result_doc = AssessmentResultDocument(
                childId=child_id,
                assessmentId=assessment_id,
                imageId=image_id,
                language=detected_language,
                childTranscript=llm_result.child_transcript,
                observerTranscript=llm_result.observer_transcript,
                semanticMetrics=SemanticMetricsDocument(
                    sceneSimilarity=semantic_scores.scene_similarity,
                    objectCoverage=semantic_scores.object_coverage,
                    actionCoverage=semantic_scores.action_coverage,
                    attributeCoverage=semantic_scores.attribute_coverage,
                ),
                languageMetrics=LanguageMetricsDocument(
                    totalWords=lm.total_words,
                    uniqueWords=lm.unique_words,
                    sentenceCount=lm.sentence_count,
                    averageWordsPerSentence=lm.average_words_per_sentence,
                    mlu=lm.mlu,
                    sentenceQuality=lm.sentence_quality,
                    grammarQuality=lm.grammar_quality,
                    vocabularyRichness=lm.vocabulary_richness,
                ),
                overallScore=overall_score,
            )
            await self._repository.save_result(result_doc)

            # Step 7: Build response
            total_duration = time.monotonic() - pipeline_start
            logger.info(
                "Pipeline complete in %.1fs | assessment=%s child=%s score=%.2f",
                total_duration,
                assessment_id,
                child_id,
                overall_score,
            )

            return AnalysisResponse(
                assessmentId=assessment_id,
                childId=child_id,
                language=detected_language,
                childTranscript=llm_result.child_transcript,
                observerTranscript=llm_result.observer_transcript,
                semanticMetrics=SemanticMetrics(
                    sceneSimilarity=semantic_scores.scene_similarity,
                    objectCoverage=semantic_scores.object_coverage,
                    actionCoverage=semantic_scores.action_coverage,
                    attributeCoverage=semantic_scores.attribute_coverage,
                ),
                languageMetrics=LanguageMetrics(
                    totalWords=lm.total_words,
                    uniqueWords=lm.unique_words,
                    sentenceCount=lm.sentence_count,
                    averageWordsPerSentence=lm.average_words_per_sentence,
                    mlu=lm.mlu,
                    sentenceQuality=lm.sentence_quality,
                    grammarQuality=lm.grammar_quality,
                    vocabularyRichness=lm.vocabulary_richness,
                ),
                overallScore=overall_score,
            )

        finally:
            # Always clean up temp files
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
                logger.debug("Cleaned up temp file: %s", tmp_path)


def _get_audio_suffix(filename: str) -> str:
    """Extract file extension for temp file creation."""
    _, ext = os.path.splitext(filename)
    if ext.lower() not in {".wav", ".mp3", ".m4a"}:
        raise AudioProcessingError(f"Unsupported audio format: {ext}")
    return ext


def _save_temp_audio(content: bytes, suffix: str) -> str:
    """Save audio bytes to a named temp file. Caller must delete."""
    os.makedirs("tmp", exist_ok=True)
    fd, path = tempfile.mkstemp(suffix=suffix, dir="tmp")
    try:
        os.write(fd, content)
    finally:
        os.close(fd)
    return path
