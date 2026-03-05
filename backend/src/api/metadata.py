"""Metadata API endpoints for fetching and refreshing repository metadata."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from src.api.auth import get_session_dep
from src.models.user import UserSession
from src.services.metadata_service import MetadataService, RepositoryMetadataContext

logger = logging.getLogger(__name__)
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
    svc = MetadataService()
    ctx = await svc.get_or_fetch(session.access_token, owner, repo)
    return ctx


@router.post("/{owner}/{repo}/refresh", response_model=RepositoryMetadataContext)
async def refresh_metadata(
    owner: str,
    repo: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> RepositoryMetadataContext:
    """Force-refresh repository metadata from the GitHub API."""
    svc = MetadataService()
    await svc.invalidate(owner, repo)
    ctx = await svc.fetch_metadata(session.access_token, owner, repo)
    return ctx
