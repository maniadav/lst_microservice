"""v1 API router."""

from fastapi import APIRouter

from app.api.v1 import assessments, lst

router = APIRouter(prefix="/api/v1")

router.include_router(lst.router)
router.include_router(assessments.router)
