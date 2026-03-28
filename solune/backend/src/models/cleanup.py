"""Pydantic models for repository cleanup operations."""

from typing import Any

from pydantic import BaseModel, Field

# ── Request Models ──────────────────────────────────────────────────


class CleanupPreflightRequest(BaseModel):
    """Request body for the preflight check."""

    owner: str = Field(min_length=1, description="Repository owner (user or org)")
    repo: str = Field(min_length=1, description="Repository name")
    project_id: str = Field(min_length=1, description="GitHub Projects v2 project node ID")


class IssueToDelete(BaseModel):
    """An orphaned issue to permanently delete."""

    number: int = Field(description="GitHub issue number")
    node_id: str = Field(min_length=1, description="GitHub GraphQL node ID")


class CleanupExecuteRequest(BaseModel):
    """Request body to execute the cleanup operation."""

    owner: str = Field(min_length=1, description="Repository owner")
    repo: str = Field(min_length=1, description="Repository name")
    project_id: str = Field(min_length=1, description="Project board ID (for audit trail)")
    branches_to_delete: list[str] = Field(description="Branch names to delete")
    prs_to_close: list[int] = Field(description="PR numbers to close")
    issues_to_delete: list[IssueToDelete] = Field(
        default=[],
        description="Orphaned issues to permanently delete (requires node_id)",
    )


# ── Response Models ─────────────────────────────────────────────────


class BranchInfo(BaseModel):
    """Branch details for preflight response."""

    name: str
    eligible_for_deletion: bool
    linked_issue_number: int | None = None
    linked_issue_title: str | None = None
    linking_method: str | None = None
    preservation_reason: str | None = None
    deletion_reason: str | None = None


class PullRequestInfo(BaseModel):
    """PR details for preflight response."""

    number: int
    title: str
    head_branch: str
    referenced_issues: list[int] = []
    eligible_for_deletion: bool
    preservation_reason: str | None = None
    deletion_reason: str | None = None


class OrphanedIssueInfo(BaseModel):
    """An app-created GitHub Issue that is no longer on the project board."""

    number: int
    title: str
    labels: list[str] = []
    html_url: str | None = None
    node_id: str | None = None


class IssueInfo(BaseModel):
    """An open issue surfaced in the cleanup modal (preserve section)."""

    number: int
    title: str
    labels: list[str] = []
    html_url: str | None = None
    node_id: str | None = None
    preservation_reason: str | None = None


class CleanupPreflightResponse(BaseModel):
    """Response from preflight endpoint."""

    branches_to_delete: list[BranchInfo]
    branches_to_preserve: list[BranchInfo]
    prs_to_close: list[PullRequestInfo]
    prs_to_preserve: list[PullRequestInfo]
    orphaned_issues: list[OrphanedIssueInfo] = []
    issues_to_preserve: list[IssueInfo] = []
    open_issues_on_board: int
    has_permission: bool
    permission_error: str | None = None


class CleanupItemResult(BaseModel):
    """Result of a single deletion/close operation."""

    item_type: str = Field(description="'branch', 'pr', or 'issue'")
    identifier: str = Field(description="Branch name, PR number, or issue number as string")
    action: str = Field(description="'deleted', 'closed', 'preserved', or 'failed'")
    reason: str | None = None
    error: str | None = None


class CleanupExecuteResponse(BaseModel):
    """Final summary response from execute endpoint."""

    operation_id: str
    branches_deleted: int
    branches_preserved: int
    prs_closed: int
    prs_preserved: int
    issues_deleted: int = 0
    errors: list[CleanupItemResult]
    results: list[CleanupItemResult]


# ── Database Row Model ──────────────────────────────────────────────


class CleanupAuditLogRow(BaseModel):
    """Represents a cleanup_audit_logs database row."""

    id: str
    github_user_id: str
    owner: str
    repo: str
    project_id: str
    started_at: str
    completed_at: str | None
    status: str
    branches_deleted: int
    branches_preserved: int
    prs_closed: int
    prs_preserved: int
    issues_closed: int = 0
    errors_count: int
    details: dict[str, Any] | None  # Parsed JSON object (stored as TEXT in SQLite)


# ── History Response ────────────────────────────────────────────────


class CleanupHistoryResponse(BaseModel):
    """Response for the audit history endpoint."""

    operations: list[CleanupAuditLogRow]
    count: int
