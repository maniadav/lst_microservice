"""Scene similarity provider interface and implementations.

The scoring engine calls the interface only. Providers can be swapped
without changing business logic.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class SceneSimilarityProvider(ABC):
    """Abstract interface for computing scene similarity."""

    @abstractmethod
    async def compute_similarity(self, expected: str, detected: str) -> float:
        """Compare two scene descriptions and return a similarity score (0–100).

        Args:
            expected: The ground-truth scene summary from the assessment image.
            detected: The scene summary extracted from the child's speech.

        Returns:
            Similarity score between 0 and 100.
        """


class GroqSceneSimilarityProvider(SceneSimilarityProvider):
    """Scene similarity using Groq LLM for semantic comparison."""

    def __init__(self, groq_client: Any) -> None:
        from app.services.groq.client import GroqClient
        self._groq: GroqClient = groq_client

    async def compute_similarity(self, expected: str, detected: str) -> float:
        from app.assessments.lst.prompts import (
            LST_SCENE_SIMILARITY_SYSTEM_PROMPT,
            build_scene_similarity_prompt,
        )
        from app.assessments.lst.parser import parse_scene_similarity_response

        if not expected or not detected:
            return 0.0

        user_prompt = build_scene_similarity_prompt(expected, detected)
        raw = await self._groq.chat_json(
            system_prompt=LST_SCENE_SIMILARITY_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        parsed = parse_scene_similarity_response(raw)
        logger.info(
            "Scene similarity: %.1f — %s",
            parsed.similarity,
            parsed.reasoning,
        )
        return parsed.similarity
