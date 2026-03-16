"""Secrets API endpoints — GitHub environment secrets CRUD."""

from __future__ import annotations

import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.api.auth import get_session_dep
from src.models.user import UserSession
from src.services.secrets_service import SecretsService
from src.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["secrets"])

# ---------------------------------------------------------------------------
# Module-level singleton (created on first import)
# ---------------------------------------------------------------------------

_secrets_service: SecretsService | None = None


def _get_secrets_service() -> SecretsService:
    global _secrets_service
    if _secrets_service is None:
        from src.services.github_projects import GitHubClientFactory

        _secrets_service = SecretsService(GitHubClientFactory())
    return _secrets_service


# ---------------------------------------------------------------------------
# Pydantic request / response models
# ---------------------------------------------------------------------------

_SECRET_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
_SECRET_NAME_MAX = 255
_SECRET_VALUE_MAX = 65_536  # 64 KB


class SecretSetRequest(BaseModel):
    """Body for PUT (create / update) a secret."""

    value: str = Field(..., max_length=_SECRET_VALUE_MAX)


class SecretListItem(BaseModel):
    name: str
    created_at: str
    updated_at: str


class SecretListResponse(BaseModel):
    total_count: int
    secrets: list[SecretListItem]


class SecretCheckResponse(BaseModel):
    results: dict[str, bool]


# ---------------------------------------------------------------------------
# Validation helper
# ---------------------------------------------------------------------------


def _validate_secret_name(secret_name: str) -> None:
    if len(secret_name) > _SECRET_NAME_MAX:
        raise HTTPException(
            status_code=422,
            detail=f"Secret name must be at most {_SECRET_NAME_MAX} characters",
        )
    if not _SECRET_NAME_RE.match(secret_name):
        raise HTTPException(
            status_code=422,
            detail="Secret name must match ^[A-Z][A-Z0-9_]*$ (uppercase letters, digits, underscores)",
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/{owner}/{repo}/{environment}", response_model=SecretListResponse)
async def list_secrets(
    owner: str,
    repo: str,
    environment: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> SecretListResponse:
    """List secret names + metadata for a repository environment."""
    svc = _get_secrets_service()
    data = await svc.list_secrets(session.access_token, owner, repo, environment)
    secrets = [
        SecretListItem(
            name=s["name"],
            created_at=s.get("created_at", ""),
            updated_at=s.get("updated_at", ""),
        )
        for s in data.get("secrets", [])
    ]
    return SecretListResponse(total_count=data.get("total_count", len(secrets)), secrets=secrets)


@router.put("/{owner}/{repo}/{environment}/{secret_name}", status_code=204)
async def set_secret(
    owner: str,
    repo: str,
    environment: str,
    secret_name: str,
    body: SecretSetRequest,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> None:
    """Create or update an environment secret (value is encrypted before upload)."""
    _validate_secret_name(secret_name)
    svc = _get_secrets_service()
    # Ensure the environment exists first
    await svc.get_or_create_environment(session.access_token, owner, repo, environment)
    await svc.set_secret(session.access_token, owner, repo, environment, secret_name, body.value)


@router.delete("/{owner}/{repo}/{environment}/{secret_name}", status_code=204)
async def delete_secret(
    owner: str,
    repo: str,
    environment: str,
    secret_name: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> None:
    """Remove an environment secret."""
    _validate_secret_name(secret_name)
    svc = _get_secrets_service()
    await svc.delete_secret(session.access_token, owner, repo, environment, secret_name)


@router.get("/{owner}/{repo}/{environment}/check", response_model=SecretCheckResponse)
async def check_secrets(
    owner: str,
    repo: str,
    environment: str,
    names: Annotated[str, Query(description="Comma-separated secret names to check")],
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> SecretCheckResponse:
    """Return a name → exists boolean map for the requested secret names."""
    name_list = [n.strip() for n in names.split(",") if n.strip()]
    svc = _get_secrets_service()
    results = await svc.check_secrets(session.access_token, owner, repo, environment, name_list)
    return SecretCheckResponse(results=results)
