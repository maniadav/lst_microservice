"""Parser for Groq LLM JSON responses in LST analysis."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from app.core.exceptions import LLMError

logger = logging.getLogger(__name__)


class ParsedSemantics(BaseModel):
    """Semantic extraction from child's speech."""

    objects: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    attributes: list[str] = Field(default_factory=list)
    scene_summary: str = Field(default="", alias="sceneSummary")

    model_config = {"populate_by_name": True}


class ParsedLanguageMetrics(BaseModel):
    """Language metrics from child's speech."""

    total_words: int = Field(default=0, alias="totalWords")
    unique_words: int = Field(default=0, alias="uniqueWords")
    sentence_count: int = Field(default=0, alias="sentenceCount")
    average_words_per_sentence: float = Field(default=0.0, alias="averageWordsPerSentence")
    mlu: float = 0.0
    sentence_quality: str = Field(default="Simple Sentences", alias="sentenceQuality")
    grammar_quality: str = Field(default="Fair", alias="grammarQuality")
    vocabulary_richness: float = Field(default=0.0, alias="vocabularyRichness")

    model_config = {"populate_by_name": True}


class ParsedLSTResponse(BaseModel):
    """Complete parsed LLM response for LST analysis."""

    child_speaker: str = Field(default="", alias="childSpeaker")
    observer_speaker: str = Field(default="", alias="observerSpeaker")
    child_transcript: str = Field(default="", alias="childTranscript")
    observer_transcript: str = Field(default="", alias="observerTranscript")
    semantics: ParsedSemantics = Field(default_factory=ParsedSemantics)
    language_metrics: ParsedLanguageMetrics = Field(
        default_factory=ParsedLanguageMetrics,
        alias="languageMetrics",
    )

    model_config = {"populate_by_name": True}


def parse_lst_response(raw: dict[str, Any]) -> ParsedLSTResponse:
    """Parse and validate the LLM's JSON response.

    Handles malformed responses gracefully by using defaults for missing fields.
    """
    try:
        return ParsedLSTResponse.model_validate(raw)
    except ValidationError as exc:
        logger.error("Failed to parse LLM response: %s", exc.errors())
        raise LLMError("LLM returned an invalid response structure") from exc


class ParsedSceneSimilarity(BaseModel):
    """Parsed scene similarity response."""

    similarity: float = Field(ge=0, le=100)
    reasoning: str = ""


def parse_scene_similarity_response(raw: dict[str, Any]) -> ParsedSceneSimilarity:
    """Parse the scene similarity JSON response."""
    try:
        return ParsedSceneSimilarity.model_validate(raw)
    except ValidationError as exc:
        logger.error("Failed to parse scene similarity response: %s", exc.errors())
        raise LLMError("LLM returned invalid scene similarity response") from exc
