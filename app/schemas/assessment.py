"""Pydantic schemas for assessment CRUD operations."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AssessmentCreate(BaseModel):
    assessment_id: str = Field(alias="assessmentId")
    title: str
    description: str = ""
    module: str = "lst"

    model_config = {"populate_by_name": True}


class AssessmentResponse(BaseModel):
    assessment_id: str = Field(alias="assessmentId")
    title: str
    description: str
    module: str

    model_config = {"populate_by_name": True}


class AssessmentImageCreate(BaseModel):
    image_id: str = Field(alias="imageId")
    image_url: str = Field(default="", alias="imageUrl")
    objects: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    attributes: list[str] = Field(default_factory=list)
    scene_summary: str = Field(default="", alias="sceneSummary")
    version: int = 1

    model_config = {"populate_by_name": True}


class AssessmentImageResponse(BaseModel):
    image_id: str = Field(alias="imageId")
    assessment_id: str = Field(alias="assessmentId")
    image_url: str = Field(alias="imageUrl")
    objects: list[str]
    actions: list[str]
    attributes: list[str]
    scene_summary: str = Field(alias="sceneSummary")
    version: int

    model_config = {"populate_by_name": True}
