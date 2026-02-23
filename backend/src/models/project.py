"""GitHub Project model with status columns."""

from datetime import datetime
from src.utils import utcnow
from enum import StrEnum

from pydantic import BaseModel, Field


class ProjectType(StrEnum):
    """Type of GitHub Project."""

    ORGANIZATION = "organization"
    USER = "user"
    REPOSITORY = "repository"


class StatusColumn(BaseModel):
    """Status column in a GitHub Project."""

    field_id: str = Field(..., description="Status field node ID")
    name: str = Field(..., description="Column display name (e.g., 'Todo')")
    option_id: str = Field(..., description="Option ID for this status value")
    color: str | None = Field(default=None, description="Display color")


class GitHubProject(BaseModel):
    """Represents a GitHub Project V2 board accessible to the user."""

    project_id: str = Field(..., description="GitHub Project V2 node ID (PVT_xxx)")
    owner_id: str = Field(..., description="Owner (user/org) node ID")
    owner_login: str = Field(..., description="Owner username/org name")
    name: str = Field(..., description="Project display name")
    type: ProjectType = Field(..., description="Project type: organization, user, or repository")
    url: str = Field(..., description="GitHub web URL for the project")
    description: str | None = Field(default=None, description="Project description")
    status_columns: list[StatusColumn] = Field(
        ..., min_length=1, description="List of StatusColumn objects"
    )
    item_count: int | None = Field(default=None, description="Total items in project")
    cached_at: datetime = Field(
        default_factory=utcnow, description="When this data was fetched"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "project_id": "PVT_kwDOABCD1234",
                "owner_id": "O_kgDOBcdef",
                "owner_login": "acme-corp",
                "name": "Sprint 42",
                "type": "organization",
                "url": "https://github.com/orgs/acme-corp/projects/42",
                "description": "Sprint planning board",
                "status_columns": [
                    {
                        "field_id": "PVTSSF_lADOABCD",
                        "name": "Todo",
                        "option_id": "f75ad846",
                        "color": "gray",
                    },
                    {
                        "field_id": "PVTSSF_lADOABCD",
                        "name": "In Progress",
                        "option_id": "47fc9ee4",
                        "color": "yellow",
                    },
                    {
                        "field_id": "PVTSSF_lADOABCD",
                        "name": "Done",
                        "option_id": "98236657",
                        "color": "green",
                    },
                ],
                "item_count": 24,
                "cached_at": "2026-01-30T10:00:00Z",
            }
        }
    }


class ProjectListResponse(BaseModel):
    """Response for listing projects."""

    projects: list[GitHubProject]
