"""Application data models for Solune multi-app management."""

from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator

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
    NEW_REPO = "new-repo"


class App(BaseModel):
    name: str = Field(..., pattern=APP_NAME_PATTERN, min_length=2, max_length=64)
    display_name: str = Field(..., min_length=1, max_length=128)
    description: str = Field(default="")
    directory_path: str
    associated_pipeline_id: str | None = None
    status: AppStatus = AppStatus.CREATING
    repo_type: RepoType = RepoType.SAME_REPO
    external_repo_url: str | None = None
    github_repo_url: str | None = None
    github_project_url: str | None = None
    github_project_id: str | None = None
    parent_issue_number: int | None = None
    parent_issue_url: str | None = None
    port: int | None = None
    error_message: str | None = None
    created_at: str = ""
    updated_at: str = ""
    # Transient field — populated in memory only, not persisted in the DB.
    # Set by create_app_with_new_repo when optional steps (e.g. Azure secret
    # storage) fail non-fatally so the frontend can surface a notice.
    warnings: list[str] | None = None


class AppCreate(BaseModel):
    name: str = Field(..., pattern=APP_NAME_PATTERN, min_length=2, max_length=64)
    display_name: str = Field(..., min_length=1, max_length=128)
    description: str = Field(default="")
    branch: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        description="Target branch for app scaffold commit (required for same-repo/external-repo)",
    )
    pipeline_id: str | None = None
    project_id: str | None = None
    repo_type: RepoType = RepoType.SAME_REPO
    external_repo_url: str | None = None
    repo_owner: str | None = None
    repo_visibility: Literal["public", "private"] = Field(
        default="private",
        description="Repository visibility: 'public' or 'private'",
    )
    create_project: bool = True
    ai_enhance: bool = True
    azure_client_id: str | None = Field(default=None, min_length=1)
    azure_client_secret: str | None = Field(
        default=None, min_length=1, json_schema_extra={"writeOnly": True}
    )

    @model_validator(mode="after")
    def validate_azure_credentials(self) -> Self:
        has_id = self.azure_client_id is not None
        has_secret = self.azure_client_secret is not None
        if has_id != has_secret:
            msg = "Azure Client ID and Client Secret must both be provided or both omitted."
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def validate_external_repo_url(self) -> Self:
        if self.repo_type == RepoType.EXTERNAL_REPO:
            if not self.external_repo_url:
                msg = "external_repo_url is required when repo_type is 'external-repo'."
                raise ValueError(msg)
            from src.utils import parse_github_url

            try:
                parse_github_url(self.external_repo_url)
            except Exception as exc:
                raise ValueError(str(exc)) from exc
        return self


class AppUpdate(BaseModel):
    display_name: str | None = Field(None, min_length=1, max_length=128)
    description: str | None = None
    pipeline_id: str | None = None


class AppStatusResponse(BaseModel):
    name: str
    status: AppStatus
    port: int | None = None
    error_message: str | None = None


class AppAssetInventory(BaseModel):
    """Inventory of all GitHub assets associated with an app."""

    app_name: str
    github_repo: str | None = None
    github_project_id: str | None = None
    parent_issue_number: int | None = None
    sub_issues: list[int] = Field(default_factory=list)
    branches: list[str] = Field(default_factory=list)
    has_azure_secrets: bool = False


class DeleteAppResult(BaseModel):
    """Result of a force-delete operation with asset cleanup details."""

    app_name: str
    issues_closed: int = 0
    branches_deleted: int = 0
    project_deleted: bool = False
    repo_deleted: bool = False
    db_deleted: bool = False
    errors: list[str] = Field(default_factory=list)
