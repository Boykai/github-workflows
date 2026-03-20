"""Pagination models — generic paginated response envelope and query parameters."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Query parameters for paginated list endpoints."""

    limit: int = Field(default=25, ge=1, le=100, description="Items per page (1-100)")
    cursor: str | None = Field(default=None, description="Opaque cursor for the next page")


class PaginatedResponse[T](BaseModel):
    """Generic paginated response envelope."""

    items: list[T] = Field(default_factory=list)
    next_cursor: str | None = Field(default=None)
    has_more: bool = Field(default=False)
    total_count: int | None = Field(default=None)
