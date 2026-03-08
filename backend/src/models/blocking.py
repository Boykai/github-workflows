"""Pydantic models for the Blocking Queue — serial issue activation."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class BlockingQueueStatus(StrEnum):
    """Lifecycle states of a blocking queue entry."""

    PENDING = "pending"
    ACTIVE = "active"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"


class BlockingQueueEntry(BaseModel):
    """A single entry in a repository's blocking queue."""

    id: int
    repo_key: str
    issue_number: int
    project_id: str
    is_blocking: bool
    queue_status: BlockingQueueStatus = BlockingQueueStatus.PENDING
    parent_branch: str | None = None
    blocking_source_issue: int | None = None
    created_at: str
    activated_at: str | None = None
    completed_at: str | None = None
