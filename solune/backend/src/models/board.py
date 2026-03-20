"""Board-specific Pydantic models for the Project Board feature."""

from enum import StrEnum

from pydantic import BaseModel, Field


class StatusColor(StrEnum):
    """GitHub predefined status colors."""

    GRAY = "GRAY"
    BLUE = "BLUE"
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    ORANGE = "ORANGE"
    RED = "RED"
    PINK = "PINK"
    PURPLE = "PURPLE"


class ContentType(StrEnum):
    """Type of content backing a project item."""

    ISSUE = "issue"
    DRAFT_ISSUE = "draft_issue"
    PULL_REQUEST = "pull_request"


class PRState(StrEnum):
    """State of a pull request."""

    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class StatusOption(BaseModel):
    """A single status option (maps to a board column)."""

    option_id: str = Field(..., description="Unique option identifier")
    name: str = Field(..., description="Status display name")
    color: StatusColor = Field(..., description="GitHub predefined status color")
    description: str | None = Field(default=None, description="Optional status description")


class StatusField(BaseModel):
    """Configuration for the project's Status single-select field."""

    field_id: str = Field(..., description="GraphQL node ID for the Status field")
    options: list[StatusOption] = Field(..., description="Available status values")


class BoardProject(BaseModel):
    """A GitHub Project V2 with metadata for board display."""

    project_id: str = Field(..., description="GitHub GraphQL node ID")
    name: str = Field(..., description="Project title")
    description: str | None = Field(default=None, description="Project short description")
    url: str = Field(..., description="GitHub project URL")
    owner_login: str = Field(..., description="Owner username or organization")
    status_field: StatusField = Field(..., description="The Status field configuration")


class Repository(BaseModel):
    """Repository reference for an issue/PR."""

    owner: str = Field(..., description="Repository owner login")
    name: str = Field(..., description="Repository name")


class Assignee(BaseModel):
    """User assigned to an issue."""

    login: str = Field(..., description="GitHub username")
    avatar_url: str = Field(..., description="Avatar image URL")


class CustomFieldValue(BaseModel):
    """Custom field value (Priority or Size)."""

    name: str = Field(..., description="Field value name")
    color: StatusColor | None = Field(default=None, description="Option color if configured")


class LinkedPR(BaseModel):
    """A pull request linked to an issue."""

    pr_id: str = Field(..., description="PR GraphQL ID")
    number: int = Field(..., description="PR number")
    title: str = Field(..., description="PR title")
    state: PRState = Field(..., description="PR state")
    url: str = Field(..., description="PR URL on GitHub")


class Label(BaseModel):
    """A GitHub issue label with color information."""

    id: str = Field(..., description="GraphQL node ID")
    name: str = Field(..., description="Label display name (e.g., 'enhancement')")
    color: str = Field(..., description="Hex color without '#' prefix (e.g., '0075ca')")


class SubIssue(BaseModel):
    """A sub-issue attached to a parent issue, representing work for a specific agent."""

    id: str = Field(..., description="Sub-issue GraphQL node ID")
    number: int = Field(..., description="Sub-issue number")
    title: str = Field(..., description="Sub-issue title")
    url: str = Field(..., description="GitHub URL")
    state: str = Field(default="open", description="Issue state: open or closed")
    assigned_agent: str | None = Field(
        default=None, description="Agent slug assigned to this sub-issue"
    )
    assignees: list[Assignee] = Field(default_factory=list, description="Assigned users")
    linked_prs: list[LinkedPR] = Field(
        default_factory=list, description="PRs linked to this sub-issue"
    )


class BoardItem(BaseModel):
    """An item (issue/draft/PR) on the board with all display metadata."""

    item_id: str = Field(..., description="Project item GraphQL ID")
    content_id: str | None = Field(default=None, description="Underlying issue/PR GraphQL ID")
    content_type: ContentType = Field(..., description="Type of content")
    title: str = Field(..., description="Issue/PR title")
    number: int | None = Field(default=None, description="Issue/PR number (null for drafts)")
    repository: Repository | None = Field(
        default=None, description="Repository info (null for drafts)"
    )
    url: str | None = Field(default=None, description="GitHub URL (null for drafts)")
    body: str | None = Field(default=None, description="Issue body/description")
    status: str = Field(..., description="Current status option name")
    status_option_id: str = Field(..., description="Status option ID")
    assignees: list[Assignee] = Field(default_factory=list, description="Assigned users")
    priority: CustomFieldValue | None = Field(
        default=None, description="Priority custom field value"
    )
    size: CustomFieldValue | None = Field(default=None, description="Size custom field value")
    estimate: float | None = Field(default=None, description="Estimate value (numeric)")
    linked_prs: list[LinkedPR] = Field(
        default_factory=list, description="Pull requests linked to this issue"
    )
    sub_issues: list[SubIssue] = Field(
        default_factory=list, description="Sub-issues for agent work"
    )
    labels: list[Label] = Field(default_factory=list, description="GitHub issue labels")
    issue_type: str | None = Field(
        default=None,
        description="GitHub Issue Type name (e.g. 'Bug', 'Feature', 'Chore')",
    )
    created_at: str | None = Field(default=None, description="ISO 8601 creation timestamp")
    updated_at: str | None = Field(default=None, description="ISO 8601 last update timestamp")
    milestone: str | None = Field(default=None, description="Milestone name")
    queued: bool = Field(default=False, description="Whether this issue's pipeline is queued")


class BoardColumn(BaseModel):
    """A board column representing a status with its items."""

    status: StatusOption = Field(..., description="Status option for this column")
    items: list[BoardItem] = Field(default_factory=list, description="Items in this column")
    item_count: int = Field(default=0, description="Total items in this column")
    estimate_total: float = Field(
        default=0.0, description="Sum of estimates for items in this column"
    )
    next_cursor: str | None = Field(default=None, description="Cursor for next page of items")
    has_more: bool = Field(default=False, description="Whether more items exist")


class RateLimitInfo(BaseModel):
    """GitHub API rate limit status from response headers."""

    limit: int = Field(..., description="Maximum requests per hour")
    remaining: int = Field(..., description="Remaining requests in current window")
    reset_at: int = Field(..., description="Unix timestamp when limit resets")
    used: int = Field(..., description="Requests used in current window")


class BoardDataResponse(BaseModel):
    """Response for board data with columns and items."""

    project: BoardProject = Field(..., description="Project metadata")
    columns: list[BoardColumn] = Field(..., description="Board columns with their items")
    rate_limit: RateLimitInfo | None = Field(
        default=None, description="GitHub API rate limit status"
    )


class BoardProjectListResponse(BaseModel):
    """Response for listing board projects."""

    projects: list[BoardProject]
    rate_limit: RateLimitInfo | None = Field(
        default=None, description="GitHub API rate limit status"
    )


class StatusUpdateRequest(BaseModel):
    """Request body for updating a board item's status by name."""

    status: str = Field(..., min_length=1, description="Target status name (case-insensitive)")


class StatusUpdateResponse(BaseModel):
    """Response for a board item status update."""

    success: bool = Field(..., description="Whether the status update was applied")
