"""Metadata API endpoints for fetching and refreshing repository metadata."""

from typing import Annotated

from fastapi import APIRouter, Depends

from src.api.auth import get_session_dep
from src.logging_utils import get_logger
from src.models.user import UserSession
from src.services.metadata_service import MetadataService, RepositoryMetadataContext

logger = get_logger(__name__)
router = APIRouter()


@router.get("/{owner}/{repo}", response_model=RepositoryMetadataContext)
async def get_metadata(
    owner: str,
    repo: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> RepositoryMetadataContext:
    """Return cached repository metadata (labels, branches, milestones, collaborators).

    If the cache is empty, triggers a fresh fetch from the GitHub API.
    """
    from src.services.github_projects import github_projects_service

    svc = MetadataService(github_service=github_projects_service)
    ctx = await svc.get_or_fetch(session.access_token, owner, repo)
    return ctx


@router.post("/{owner}/{repo}/refresh", response_model=RepositoryMetadataContext)
async def refresh_metadata(
    owner: str,
    repo: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> RepositoryMetadataContext:
    """Force-refresh repository metadata from the GitHub API."""
    from src.services.github_projects import github_projects_service

    svc = MetadataService(github_service=github_projects_service)
    await svc.invalidate(owner, repo)
    ctx = await svc.fetch_metadata(session.access_token, owner, repo)
    return ctx
