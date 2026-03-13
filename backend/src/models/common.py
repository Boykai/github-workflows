"""Shared response models used across multiple API endpoints."""

from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Generic response with a message field, optionally with extra keys."""

    message: str


class DeleteResponse(BaseModel):
    """Response for resource deletion endpoints."""

    success: bool = True
    deleted_id: str


class SeedPresetsResponse(BaseModel):
    """Response for seed-presets endpoints."""

    created: int


class PipelineSeedPresetsResponse(BaseModel):
    """Response for pipeline seed-presets endpoint."""

    seeded: list[str]
    skipped: list[str]
    total: int
