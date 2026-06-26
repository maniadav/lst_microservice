"""Repository pattern for MongoDB collections."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.models.assessment import (
    AssessmentDocument,
    AssessmentImageDocument,
    AssessmentResultDocument,
)

logger = logging.getLogger(__name__)


class AssessmentRepository:
    """Data access layer for assessment-related MongoDB collections."""

    def __init__(self, db: AsyncIOMotorDatabase | None) -> None:
        self._db = db

    def _collection(self, name: str):
        if self._db is None:
            raise RuntimeError(f"MongoDB not connected — cannot access '{name}' collection")
        return self._db[name]

    async def get_assessment(self, assessment_id: str) -> AssessmentDocument | None:
        doc = await self._collection("assessments").find_one({"assessmentId": assessment_id})
        if not doc:
            return None
        return AssessmentDocument.model_validate(doc)

    async def create_assessment(self, data: dict[str, Any]) -> str:
        result = await self._collection("assessments").insert_one(data)
        return str(result.inserted_id)

    async def get_image_semantics(
        self,
        assessment_id: str,
        image_id: str,
    ) -> AssessmentImageDocument | None:
        """Fetch image semantics from either local file or MongoDB based on config."""
        if settings.SEMANTICS_SOURCE == "local":
            return _load_local_semantics(assessment_id, image_id)
        return await self._get_image_semantics_from_db(assessment_id, image_id)

    async def _get_image_semantics_from_db(
        self,
        assessment_id: str,
        image_id: str,
    ) -> AssessmentImageDocument | None:
        doc = await self._collection("assessment_images").find_one({
            "assessmentId": assessment_id,
            "imageId": image_id,
        })
        if not doc:
            return None
        return AssessmentImageDocument.model_validate(doc)

    async def list_images(self, assessment_id: str) -> list[AssessmentImageDocument]:
        cursor = self._collection("assessment_images").find({"assessmentId": assessment_id})
        docs = await cursor.to_list(length=100)
        return [AssessmentImageDocument.model_validate(d) for d in docs]

    async def create_image(self, data: dict[str, Any]) -> str:
        result = await self._collection("assessment_images").insert_one(data)
        return str(result.inserted_id)

    async def save_result(self, result: AssessmentResultDocument) -> str | None:
        """Save result to MongoDB. Skipped when SAVE_RESULTS_TO_DB is false."""
        if not settings.SAVE_RESULTS_TO_DB:
            logger.info(
                "Result saving disabled (SAVE_RESULTS_TO_DB=false) — skipping DB write "
                "for child=%s assessment=%s",
                result.child_id,
                result.assessment_id,
            )
            return None

        data = result.model_dump(by_alias=True)
        data["createdAt"] = datetime.now(timezone.utc)
        insert = await self._collection("assessment_results").insert_one(data)
        logger.info(
            "Saved assessment result %s for child=%s assessment=%s",
            insert.inserted_id,
            result.child_id,
            result.assessment_id,
        )
        return str(insert.inserted_id)

    async def get_results_by_child(
        self,
        child_id: str,
        assessment_id: str | None = None,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {"childId": child_id}
        if assessment_id:
            query["assessmentId"] = assessment_id
        cursor = self._collection("assessment_results").find(query).sort("createdAt", -1)
        return await cursor.to_list(length=100)


def _load_local_semantics(
    assessment_id: str,
    image_id: str,
) -> AssessmentImageDocument | None:
    """Load image semantics from the local JSON file."""
    path = Path(settings.LOCAL_SEMANTICS_PATH)
    if not path.exists():
        logger.error("Local semantics file not found: %s", path)
        return None

    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Failed to read local semantics file: %s", exc)
        return None

    assessment = data.get("assessments", {}).get(assessment_id)
    if not assessment:
        logger.warning("Assessment %s not found in local semantics", assessment_id)
        return None

    image = assessment.get("images", {}).get(image_id)
    if not image:
        logger.warning(
            "Image %s not found for assessment %s in local semantics",
            image_id,
            assessment_id,
        )
        return None

    return AssessmentImageDocument.model_validate(image)

