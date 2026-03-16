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
