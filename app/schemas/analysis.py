"""Pydantic schemas for LST analysis request/response."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SemanticMetrics(BaseModel):
    scene_similarity: float = Field(alias="sceneSimilarity", ge=0, le=100)
    object_coverage: float = Field(alias="objectCoverage", ge=0, le=100)
    action_coverage: float = Field(alias="actionCoverage", ge=0, le=100)
    attribute_coverage: float = Field(alias="attributeCoverage", ge=0, le=100)

    model_config = {"populate_by_name": True}


class LanguageMetrics(BaseModel):
    total_words: int = Field(alias="totalWords", ge=0)
    unique_words: int = Field(alias="uniqueWords", ge=0)
    sentence_count: int = Field(alias="sentenceCount", ge=0)
    average_words_per_sentence: float = Field(alias="averageWordsPerSentence", ge=0)
    mlu: float = Field(ge=0)
    sentence_quality: str = Field(alias="sentenceQuality")
    grammar_quality: str = Field(alias="grammarQuality")
    vocabulary_richness: float = Field(alias="vocabularyRichness", ge=0, le=1)

    model_config = {"populate_by_name": True}


class AnalysisResponse(BaseModel):
    assessment_id: str = Field(alias="assessmentId")
    child_id: str = Field(alias="childId")
    language: str
    child_transcript: str = Field(alias="childTranscript")
    observer_transcript: str = Field(alias="observerTranscript")
    semantic_metrics: SemanticMetrics = Field(alias="semanticMetrics")
    language_metrics: LanguageMetrics = Field(alias="languageMetrics")
    overall_score: float = Field(alias="overallScore", ge=0, le=100)

    model_config = {"populate_by_name": True}
