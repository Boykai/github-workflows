"""Application data models for Solune multi-app management."""

from enum import StrEnum

from pydantic import BaseModel, Field

APP_NAME_PATTERN = r"^[a-z0-9][a-z0-9-]*[a-z0-9]$"

RESERVED_NAMES = frozenset(
    {
        "api",
        "admin",
        "solune",
        "apps",
        "github",
        "platform",
        "static",
        "health",
        "login",
        "auth",
    }
)


class AppStatus(StrEnum):
    CREATING = "creating"
    ACTIVE = "active"
    STOPPED = "stopped"
    ERROR = "error"


class RepoType(StrEnum):
    SAME_REPO = "same-repo"
    EXTERNAL_REPO = "external-repo"


class App(BaseModel):
    name: str = Field(..., pattern=APP_NAME_PATTERN, min_length=2, max_length=64)
    display_name: str = Field(..., min_length=1, max_length=128)
    description: str = Field(default="")
    directory_path: str
    associated_pipeline_id: str | None = None
    status: AppStatus = AppStatus.CREATING
    repo_type: RepoType = RepoType.SAME_REPO
    external_repo_url: str | None = None
    port: int | None = None
    error_message: str | None = None
    created_at: str = ""
    updated_at: str = ""


class AppCreate(BaseModel):
    name: str = Field(..., pattern=APP_NAME_PATTERN, min_length=2, max_length=64)
    display_name: str = Field(..., min_length=1, max_length=128)
    description: str = Field(default="")
    pipeline_id: str | None = None
    repo_type: RepoType = RepoType.SAME_REPO
    external_repo_url: str | None = None


class AppUpdate(BaseModel):
    display_name: str | None = Field(None, min_length=1, max_length=128)
    description: str | None = None
    pipeline_id: str | None = None


class AppStatusResponse(BaseModel):
    name: str
    status: AppStatus
    port: int | None = None
    error_message: str | None = None
