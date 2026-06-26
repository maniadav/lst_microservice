"""Async MongoDB connection using Motor."""

from __future__ import annotations

import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None


async def connect_db() -> None:
    """Initialize the Motor client. Called once during app startup."""
    global _client
    _client = AsyncIOMotorClient(settings.MONGODB_URL)
    await _client.admin.command("ping")
    logger.info("Connected to MongoDB at %s", settings.MONGODB_URL)


async def close_db() -> None:
    """Close the Motor client. Called during app shutdown."""
    global _client
    if _client:
        _client.close()
        _client = None
        logger.info("Disconnected from MongoDB")


def get_database() -> AsyncIOMotorDatabase | None:
    """Return the application database instance, or None if not connected."""
    if _client is None:
        return None
    return _client[settings.MONGODB_DATABASE]


def is_connected() -> bool:
    """Check if MongoDB client is initialized."""
    return _client is not None
