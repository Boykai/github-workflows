from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class UserData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    login: str


class OwnerData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    login: str


class RepositoryData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    owner: OwnerData


class BranchRef(BaseModel):
    model_config = ConfigDict(extra="ignore")

    ref: str = ""


class PullRequestData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    number: int
    draft: bool = False
    merged: bool = False
    user: UserData
    head: BranchRef = Field(default_factory=BranchRef)
    body: str | None = None


class PullRequestEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    action: str
    pull_request: PullRequestData
    repository: RepositoryData


class IssueData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    number: int
    title: str | None = None
    body: str | None = None
    user: UserData | None = None


class IssuesEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    action: str
    issue: IssueData
    repository: RepositoryData


class PingEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    zen: str = ""
    hook_id: int | None = None


# ── Check Run / Check Suite Webhook Events ──


class CheckRunPR(BaseModel):
    """PR reference within a check run event."""

    model_config = ConfigDict(extra="ignore")

    number: int
    head: BranchRef = Field(default_factory=BranchRef)
    base: BranchRef = Field(default_factory=BranchRef)


class CheckRunData(BaseModel):
    """Check run details from webhook payload."""

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str = ""
    status: str = ""
    conclusion: str | None = None
    head_sha: str = ""
    pull_requests: list[CheckRunPR] = Field(default_factory=list)


class CheckSuiteData(BaseModel):
    """Check suite details from webhook payload."""

    model_config = ConfigDict(extra="ignore")

    id: int
    status: str = ""
    conclusion: str | None = None
    head_sha: str = ""
    pull_requests: list[CheckRunPR] = Field(default_factory=list)


class CheckRunEvent(BaseModel):
    """GitHub check_run webhook event."""

    model_config = ConfigDict(extra="ignore")

    action: str
    check_run: CheckRunData
    repository: RepositoryData


class CheckSuiteEvent(BaseModel):
    """GitHub check_suite webhook event."""

    model_config = ConfigDict(extra="ignore")

    action: str
    check_suite: CheckSuiteData
    repository: RepositoryData
