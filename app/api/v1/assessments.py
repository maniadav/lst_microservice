"""Assessment CRUD endpoints for seeding data."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from app.core.exceptions import AssessmentNotFoundError
from app.core.security import verify_api_key
from app.database.mongodb import get_database
from app.repositories.assessment_repository import AssessmentRepository
from app.schemas.assessment import (
    AssessmentCreate,
    AssessmentImageCreate,
    AssessmentImageResponse,
    AssessmentResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assessments", tags=["Assessments"])


def _get_repo() -> AssessmentRepository:
    return AssessmentRepository(get_database())


@router.post("", response_model=dict, status_code=201)
async def create_assessment(
    data: AssessmentCreate,
    _api_key: str | None = Depends(verify_api_key),
) -> dict:
    """Create a new assessment definition."""
    repo = _get_repo()
    doc = data.model_dump(by_alias=True)
    inserted_id = await repo.create_assessment(doc)
    logger.info("Created assessment %s (id=%s)", data.assessment_id, inserted_id)
    return {"id": inserted_id, "assessmentId": data.assessment_id}


@router.get("/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
    assessment_id: str,
    _api_key: str | None = Depends(verify_api_key),
) -> AssessmentResponse:
    """Get an assessment by ID."""
    repo = _get_repo()
    doc = await repo.get_assessment(assessment_id)
    if not doc:
        raise AssessmentNotFoundError(assessment_id)
    return AssessmentResponse(
        assessmentId=doc.assessment_id,
        title=doc.title,
        description=doc.description,
        module=doc.module,
    )


@router.post("/{assessment_id}/images", response_model=dict, status_code=201)
async def create_assessment_image(
    assessment_id: str,
    data: AssessmentImageCreate,
    _api_key: str | None = Depends(verify_api_key),
) -> dict:
    """Add image semantics for an assessment."""
    repo = _get_repo()
    doc = data.model_dump(by_alias=True)
    doc["assessmentId"] = assessment_id
    inserted_id = await repo.create_image(doc)
    logger.info(
        "Created image semantics %s for assessment %s",
        data.image_id,
        assessment_id,
    )
    return {"id": inserted_id, "imageId": data.image_id}


@router.get("/{assessment_id}/images", response_model=list[AssessmentImageResponse])
async def list_assessment_images(
    assessment_id: str,
    _api_key: str | None = Depends(verify_api_key),
) -> list[AssessmentImageResponse]:
    """List all image semantics for an assessment."""
    repo = _get_repo()
    docs = await repo.list_images(assessment_id)
    return [
        AssessmentImageResponse(
            imageId=d.image_id,
            assessmentId=d.assessment_id,
            imageUrl=d.image_url,
            objects=d.objects,
            actions=d.actions,
            attributes=d.attributes,
            sceneSummary=d.scene_summary,
            version=d.version,
        )
        for d in docs
    ]
