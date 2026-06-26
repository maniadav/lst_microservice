"""Pydantic document models matching MongoDB collections."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class AssessmentDocument(BaseModel):
    """Matches the `assessments` collection."""

    assessment_id: str = Field(alias="assessmentId")
    title: str
    description: str = ""
    module: str = "lst"

    model_config = {"populate_by_name": True}


class AssessmentImageDocument(BaseModel):
    """Matches the `assessment_images` collection."""

    image_id: str = Field(alias="imageId")
    assessment_id: str = Field(alias="assessmentId")
    image_url: str = Field(default="", alias="imageUrl")
    objects: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    attributes: list[str] = Field(default_factory=list)
    scene_summary: str = Field(default="", alias="sceneSummary")
    version: int = 1

    model_config = {"populate_by_name": True}


class SemanticMetricsDocument(BaseModel):
    """Embedded semantic metrics."""

    scene_similarity: float = Field(alias="sceneSimilarity")
    object_coverage: float = Field(alias="objectCoverage")
    action_coverage: float = Field(alias="actionCoverage")
    attribute_coverage: float = Field(alias="attributeCoverage")

    model_config = {"populate_by_name": True}


class LanguageMetricsDocument(BaseModel):
    """Embedded language metrics."""

    total_words: int = Field(alias="totalWords")
    unique_words: int = Field(alias="uniqueWords")
    sentence_count: int = Field(alias="sentenceCount")
    average_words_per_sentence: float = Field(alias="averageWordsPerSentence")
    mlu: float
    sentence_quality: str = Field(alias="sentenceQuality")
    grammar_quality: str = Field(alias="grammarQuality")
    vocabulary_richness: float = Field(alias="vocabularyRichness")

    model_config = {"populate_by_name": True}


class AssessmentResultDocument(BaseModel):
    """Matches the `assessment_results` collection."""

    child_id: str = Field(alias="childId")
    assessment_id: str = Field(alias="assessmentId")
    image_id: str = Field(alias="imageId")
    language: str = ""
    child_transcript: str = Field(default="", alias="childTranscript")
    observer_transcript: str = Field(default="", alias="observerTranscript")
    semantic_metrics: SemanticMetricsDocument = Field(alias="semanticMetrics")
    language_metrics: LanguageMetricsDocument = Field(alias="languageMetrics")
    overall_score: float = Field(alias="overallScore")
    processing_version: str = Field(default="1.0.0", alias="processingVersion")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        alias="createdAt",
    )

    model_config = {"populate_by_name": True}
