"""Language analysis service — sends transcript to Groq for analysis."""

from __future__ import annotations

import logging
from typing import Any

from app.assessments.lst.parser import ParsedLSTResponse, parse_lst_response
from app.assessments.lst.prompts import LST_SYSTEM_PROMPT, build_analysis_prompt
from app.services.groq.client import GroqClient

logger = logging.getLogger(__name__)


class LanguageAnalyzer:
    """Sends speaker-attributed transcript to Groq for comprehensive analysis.

    The LLM identifies the child speaker, extracts semantics, and computes
    language metrics. It does NOT assign any scores.
    """

    def __init__(self, groq_client: GroqClient) -> None:
        self._groq = groq_client

    async def analyze(self, speaker_transcript: str) -> ParsedLSTResponse:
        """Analyze a speaker-attributed transcript.

        Args:
            speaker_transcript: Full transcript with speaker labels
                (e.g., "SPEAKER_00:\\nHello...\\nSPEAKER_01:\\n...")

        Returns:
            Parsed LLM response with child transcript, semantics, and metrics.
        """
        user_prompt = build_analysis_prompt(speaker_transcript)

        logger.info("Sending transcript to Groq for analysis (%d chars)", len(speaker_transcript))
        raw = await self._groq.chat_json(
            system_prompt=LST_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        parsed = parse_lst_response(raw)
        logger.info(
            "LLM identified child=%s observer=%s | %d objects, %d actions",
            parsed.child_speaker,
            parsed.observer_speaker,
            len(parsed.semantics.objects),
            len(parsed.semantics.actions),
        )
        return parsed
