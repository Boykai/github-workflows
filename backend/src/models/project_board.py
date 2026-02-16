"""Pydantic models for project board feature."""

from pydantic import BaseModel


class BoardAssignee(BaseModel):
    login: str
    avatar_url: str


class LinkedPullRequest(BaseModel):
    pr_number: int
    title: str
    state: str  # "OPEN", "CLOSED", "MERGED"
    url: str


class BoardIssueCard(BaseModel):
    item_id: str
    content_id: str | None = None
    issue_number: int | None = None
    title: str
    body: str | None = None
    state: str | None = None
    url: str | None = None
    repo_name: str | None = None
    repo_full_name: str | None = None
    status: str | None = None
    priority: str | None = None
    size: str | None = None
    estimate: float | None = None
    assignees: list[BoardAssignee] = []
    linked_prs: list[LinkedPullRequest] = []


class BoardStatusColumn(BaseModel):
    name: str
    color: str
    option_id: str
    description: str | None = None
    item_count: int = 0
    total_estimate: float | None = None
    items: list[BoardIssueCard] = []


class BoardStatusColumnSummary(BaseModel):
    name: str
    color: str
    option_id: str


class BoardProject(BaseModel):
    project_id: str
    title: str
    description: str | None = None
    url: str
    item_count: int = 0
    status_columns: list[BoardStatusColumnSummary] = []


class BoardProjectListResponse(BaseModel):
    projects: list[BoardProject] = []


class BoardDataResponse(BaseModel):
    project_id: str
    title: str
    columns: list[BoardStatusColumn] = []


class LinkedPRsRequest(BaseModel):
    content_ids: list[str]


class LinkedPRsResponse(BaseModel):
    linked_prs: dict[str, list[LinkedPullRequest]] = {}
