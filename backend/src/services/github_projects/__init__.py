"""GitHub Projects V2 GraphQL service."""

from src.services.github_projects.service import (  # noqa: F401
    GitHubProjectsService,
    github_projects_service,
)

__all__ = [
    "GitHubProjectsService",
    "github_projects_service",
]
