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


class BoardProjectListResponse(BaseModel):
    """Response for listing board projects."""

    projects: list[BoardProject]


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


class BoardColumn(BaseModel):
    """A board column representing a status with its items."""

    status: StatusOption = Field(..., description="Status option for this column")
    items: list[BoardItem] = Field(default_factory=list, description="Items in this column")
    item_count: int = Field(default=0, description="Total items in this column")
    estimate_total: float = Field(
        default=0.0, description="Sum of estimates for items in this column"
    )


class BoardDataResponse(BaseModel):
    """Response for board data with columns and items."""

    project: BoardProject = Field(..., description="Project metadata")
    columns: list[BoardColumn] = Field(..., description="Board columns with their items")
