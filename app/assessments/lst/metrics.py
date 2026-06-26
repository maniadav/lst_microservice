"""LST-specific metric types and normalization."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LSTSemanticScores:
    """Computed semantic scores (0–100 each)."""

    scene_similarity: float = 0.0
    object_coverage: float = 0.0
    action_coverage: float = 0.0
    attribute_coverage: float = 0.0


@dataclass
class LSTLanguageScores:
    """Normalized language scores (0–100 each)."""

    vocabulary_score: float = 0.0
    sentence_quality_score: float = 0.0
    grammar_score: float = 0.0
    mlu_score: float = 0.0


SENTENCE_QUALITY_SCORES: dict[str, float] = {
    "Single Word": 20.0,
    "Phrase": 40.0,
    "Simple Sentences": 60.0,
    "Compound Sentences": 80.0,
    "Complex Sentences": 100.0,
}

GRAMMAR_QUALITY_SCORES: dict[str, float] = {
    "Poor": 25.0,
    "Fair": 50.0,
    "Good": 75.0,
    "Excellent": 100.0,
}


def normalize_sentence_quality(label: str) -> float:
    """Convert sentence quality label to a 0–100 score."""
    return SENTENCE_QUALITY_SCORES.get(label, 60.0)


def normalize_grammar_quality(label: str) -> float:
    """Convert grammar quality label to a 0–100 score."""
    return GRAMMAR_QUALITY_SCORES.get(label, 50.0)


def normalize_vocabulary_richness(ttr: float) -> float:
    """Convert Type-Token Ratio (0.0–1.0) to a 0–100 score.

    TTR of 0.7+ is considered excellent for children.
    """
    return min(ttr * 100.0, 100.0)


def normalize_mlu(mlu: float) -> float:
    """Convert MLU to a 0–100 score.

    Typical child MLU ranges from 1.0 to 8.0+.
    Score is capped at MLU=10 for 100.
    """
    return min((mlu / 10.0) * 100.0, 100.0)
