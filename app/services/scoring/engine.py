"""Deterministic scoring engine.

All scores are computed in Python. The LLM never assigns scores.
Weights are from the LST specification:
  Semantic (80%): Scene 35%, Object 20%, Action 15%, Attribute 10%
  Language (20%): Vocabulary 5%, Sentence Quality 5%, Grammar 5%, MLU 5%
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SemanticWeights:
    scene_similarity: float = 0.35
    object_coverage: float = 0.20
    action_coverage: float = 0.15
    attribute_coverage: float = 0.10


@dataclass(frozen=True)
class LanguageWeights:
    vocabulary: float = 0.05
    sentence_quality: float = 0.05
    grammar: float = 0.05
    mlu: float = 0.05


@dataclass(frozen=True)
class ScoringWeights:
    semantic: SemanticWeights = SemanticWeights()
    language: LanguageWeights = LanguageWeights()


class ScoringEngine:
    """Deterministic scoring engine using configurable weights."""

    def __init__(self, weights: ScoringWeights | None = None) -> None:
        self._weights = weights or ScoringWeights()

    def compute_final_score(
        self,
        scene_similarity: float,
        object_coverage: float,
        action_coverage: float,
        attribute_coverage: float,
        vocabulary_score: float,
        sentence_quality_score: float,
        grammar_score: float,
        mlu_score: float,
    ) -> float:
        """Compute the weighted final LST score (0–100).

        All input scores must be in range 0–100.
        """
        sw = self._weights.semantic
        lw = self._weights.language

        score = (
            scene_similarity * sw.scene_similarity
            + object_coverage * sw.object_coverage
            + action_coverage * sw.action_coverage
            + attribute_coverage * sw.attribute_coverage
            + vocabulary_score * lw.vocabulary
            + sentence_quality_score * lw.sentence_quality
            + grammar_score * lw.grammar
            + mlu_score * lw.mlu
        )

        final = round(min(max(score, 0.0), 100.0), 2)

        logger.info(
            "Final score: %.2f | scene=%.1f obj=%.1f act=%.1f attr=%.1f "
            "vocab=%.1f sent=%.1f gram=%.1f mlu=%.1f",
            final,
            scene_similarity,
            object_coverage,
            action_coverage,
            attribute_coverage,
            vocabulary_score,
            sentence_quality_score,
            grammar_score,
            mlu_score,
        )

        return final
