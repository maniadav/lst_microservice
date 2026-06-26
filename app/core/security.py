"""API key authentication dependency."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

from app.core.config import settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: str | None = Security(_api_key_header),
) -> str | None:
    """Validate the API key from X-API-Key header.

    If API_KEY is not configured, authentication is disabled (dev mode).
    """
    if not settings.API_KEY:
        return None

    if not api_key or api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    return api_key
