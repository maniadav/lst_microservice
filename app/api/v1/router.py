"""v1 API router."""

from fastapi import APIRouter

from app.api.v1 import lst

router = APIRouter(prefix="/api/v1")

router.include_router(lst.router)
