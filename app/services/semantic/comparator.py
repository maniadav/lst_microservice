"""Semantic comparator — compares child semantics against stored image semantics."""

from __future__ import annotations

import logging

from app.services.semantic.providers import SceneSimilarityProvider

logger = logging.getLogger(__name__)


class SemanticComparator:
    """Compares extracted child semantics against stored image ground-truth."""

    def __init__(self, similarity_provider: SceneSimilarityProvider) -> None:
        self._similarity_provider = similarity_provider

    @staticmethod
    def compute_coverage(expected: list[str], detected: list[str]) -> float:
        """Compute set-based coverage percentage.

        Uses case-insensitive matching. Returns 0–100.
        """
        if not expected:
            return 100.0

        expected_lower = {item.lower().strip() for item in expected}
        detected_lower = {item.lower().strip() for item in detected}
        matched = expected_lower & detected_lower
        return round((len(matched) / len(expected_lower)) * 100.0, 1)

    async def compute_scene_similarity(self, expected: str, detected: str) -> float:
        """Delegate to the pluggable similarity provider."""
        return await self._similarity_provider.compute_similarity(expected, detected)
