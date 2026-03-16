"""Secrets API endpoints — GitHub Actions environment secrets management."""

import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.api.auth import get_session_dep
from src.logging_utils import get_logger
from src.models.user import UserSession
from src.services import secrets_service

logger = get_logger(__name__)
router = APIRouter()

# ── Validation constants ────────────────────────────────────────────────────

_SECRET_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
_SECRET_NAME_MAX_LEN = 255
_SECRET_VALUE_MAX_BYTES = 65_536  # 64 KiB


def _validate_secret_name(secret_name: str) -> None:
    """Raise HTTP 422 if the secret name is invalid."""
    if len(secret_name) > _SECRET_NAME_MAX_LEN:
        raise HTTPException(
            status_code=422,
            detail=f"Secret name must be at most {_SECRET_NAME_MAX_LEN} characters.",
        )
    if not _SECRET_NAME_RE.match(secret_name):
        raise HTTPException(
            status_code=422,
            detail=(
                "Secret name must start with an uppercase letter and contain only "
                "uppercase letters, digits, and underscores."
            ),
        )


# ── Request / Response models ───────────────────────────────────────────────


class SecretListItem(BaseModel):
    """Metadata for a single secret (values are never returned)."""

    name: str
    created_at: str | None
    updated_at: str | None


class SecretsListResponse(BaseModel):
    """Response body for the list-secrets endpoint."""

    total_count: int
    secrets: list[SecretListItem]


class SetSecretRequest(BaseModel):
    """Request body for creating or updating a secret."""

    value: str = Field(max_length=_SECRET_VALUE_MAX_BYTES)


class SecretCheckResponse(BaseModel):
    """Response body for the check-secrets endpoint."""

    results: dict[str, bool]


# ── Endpoints ───────────────────────────────────────────────────────────────


@router.get("/{owner}/{repo}/{environment}", response_model=SecretsListResponse)
async def list_environment_secrets(
    owner: str,
    repo: str,
    environment: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> SecretsListResponse:
    """List secret metadata for a repository environment (names only)."""
    secrets = await secrets_service.list_secrets(
        session.access_token, owner, repo, environment
    )
    items = [SecretListItem(**s) for s in secrets]
    return SecretsListResponse(total_count=len(items), secrets=items)


@router.put("/{owner}/{repo}/{environment}/{secret_name}", status_code=204)
async def set_environment_secret(
    owner: str,
    repo: str,
    environment: str,
    secret_name: str,
    body: SetSecretRequest,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> None:
    """Create or update a secret in a repository environment."""
    _validate_secret_name(secret_name)
    await secrets_service.get_or_create_environment(
        session.access_token, owner, repo, environment
    )
    await secrets_service.set_secret(
        session.access_token, owner, repo, environment, secret_name, body.value
    )


@router.delete("/{owner}/{repo}/{environment}/{secret_name}", status_code=204)
async def delete_environment_secret(
    owner: str,
    repo: str,
    environment: str,
    secret_name: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> None:
    """Delete a secret from a repository environment."""
    _validate_secret_name(secret_name)
    await secrets_service.delete_secret(
        session.access_token, owner, repo, environment, secret_name
    )


@router.get("/{owner}/{repo}/{environment}/check", response_model=SecretCheckResponse)
async def check_environment_secrets(
    owner: str,
    repo: str,
    environment: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
    names: str = Query(..., description="Comma-separated list of secret names to check"),
) -> SecretCheckResponse:
    """Check whether specific secrets exist in a repository environment."""
    secret_names = [n.strip() for n in names.split(",") if n.strip()]
    results = await secrets_service.check_secrets(
        session.access_token, owner, repo, environment, secret_names
    )
    return SecretCheckResponse(results=results)
