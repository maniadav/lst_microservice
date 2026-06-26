"""Async Groq API client using httpx."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import LLMError

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqClient:
    """Reusable async HTTP client for Groq's chat completions API."""

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0, connect=10.0),
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> str:
        """Send a chat completion request and return the response text."""
        client = await self._get_client()

        payload = {
            "model": settings.GROQ_MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }

        try:
            response = await client.post(GROQ_API_URL, json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error("Groq API HTTP error: %s %s", exc.response.status_code, exc.response.text)
            raise LLMError(f"Groq API returned {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            logger.error("Groq API request error: %s", exc)
            raise LLMError("Failed to connect to Groq API") from exc

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return content

    async def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """Send a chat request and parse the response as JSON."""
        raw = await self.chat(system_prompt, user_prompt, temperature, max_tokens)
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse Groq response as JSON: %s", raw[:500])
            raise LLMError("Groq returned invalid JSON") from exc

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
