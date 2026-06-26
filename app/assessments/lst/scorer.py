"""LST-specific scorer — bridges LLM analysis with the deterministic scoring engine."""

from __future__ import annotations

import logging

from app.assessments.lst.metrics import (
    LSTLanguageScores,
    LSTSemanticScores,
    normalize_grammar_quality,
    normalize_mlu,
    normalize_sentence_quality,
    normalize_vocabulary_richness,
)
from app.assessments.lst.parser import ParsedLSTResponse
from app.models.assessment import AssessmentImageDocument
from app.services.scoring.engine import ScoringEngine
from app.services.semantic.comparator import SemanticComparator

logger = logging.getLogger(__name__)


class LSTScorer:
    """Orchestrates LST-specific scoring.

    Takes parsed LLM output + stored image semantics and produces
    deterministic scores using the scoring engine.
    """

    def __init__(
        self,
        scoring_engine: ScoringEngine,
        semantic_comparator: SemanticComparator,
    ) -> None:
        self._engine = scoring_engine
        self._comparator = semantic_comparator

    async def score(
        self,
        llm_result: ParsedLSTResponse,
        image_semantics: AssessmentImageDocument,
    ) -> tuple[LSTSemanticScores, LSTLanguageScores, float]:
        """Compute all LST scores.

        Returns:
            Tuple of (semantic_scores, language_scores, overall_score).
        """
        # Semantic scores
        scene_similarity = await self._comparator.compute_scene_similarity(
            expected=image_semantics.scene_summary,
            detected=llm_result.semantics.scene_summary,
        )
        object_coverage = SemanticComparator.compute_coverage(
            expected=image_semantics.objects,
            detected=llm_result.semantics.objects,
        )
        action_coverage = SemanticComparator.compute_coverage(
            expected=image_semantics.actions,
            detected=llm_result.semantics.actions,
        )
        attribute_coverage = SemanticComparator.compute_coverage(
            expected=image_semantics.attributes,
            detected=llm_result.semantics.attributes,
        )

        semantic_scores = LSTSemanticScores(
            scene_similarity=scene_similarity,
            object_coverage=object_coverage,
            action_coverage=action_coverage,
            attribute_coverage=attribute_coverage,
        )

        # Language scores (normalize raw metrics to 0–100)
        lm = llm_result.language_metrics
        vocabulary_score = normalize_vocabulary_richness(lm.vocabulary_richness)
        sentence_quality_score = normalize_sentence_quality(lm.sentence_quality)
        grammar_score = normalize_grammar_quality(lm.grammar_quality)
        mlu_score = normalize_mlu(lm.mlu)

        language_scores = LSTLanguageScores(
            vocabulary_score=vocabulary_score,
            sentence_quality_score=sentence_quality_score,
            grammar_score=grammar_score,
            mlu_score=mlu_score,
        )

        # Final deterministic score
        overall = self._engine.compute_final_score(
            scene_similarity=scene_similarity,
            object_coverage=object_coverage,
            action_coverage=action_coverage,
            attribute_coverage=attribute_coverage,
            vocabulary_score=vocabulary_score,
            sentence_quality_score=sentence_quality_score,
            grammar_score=grammar_score,
            mlu_score=mlu_score,
        )

        return semantic_scores, language_scores, overall
