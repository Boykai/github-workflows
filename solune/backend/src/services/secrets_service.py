"""GitHub Actions Environment Secrets service.

Provides CRUD operations for GitHub Actions secrets scoped to a specific
repository environment.  All encryption uses NaCl sealed-box as required
by the GitHub API.
"""

from __future__ import annotations

import base64

from nacl.encoding import Base64Encoder
from nacl.public import PublicKey, SealedBox

from src.logging_utils import get_logger
from src.services.github_projects import GitHubClientFactory

logger = get_logger(__name__)

_factory = GitHubClientFactory()


async def get_or_create_environment(
    access_token: str,
    owner: str,
    repo: str,
    environment_name: str,
) -> dict:
    """Ensure the environment exists; create it if not.

    Returns the environment object from the GitHub API.
    """
    client = await _factory.get_client(access_token)
    async with client as gh:
        try:
            resp = await gh.rest.repos.async_get_environment(
                owner=owner,
                repo=repo,
                environment_name=environment_name,
            )
            return resp.parsed_data.model_dump()
        except Exception:
            logger.info(
                "Environment %s not found in %s/%s — creating it",
                environment_name,
                owner,
                repo,
            )
            resp = await gh.rest.repos.async_create_or_update_environment(
                owner=owner,
                repo=repo,
                environment_name=environment_name,
            )
            return resp.parsed_data.model_dump()


async def list_secrets(
    access_token: str,
    owner: str,
    repo: str,
    environment_name: str,
) -> list[dict]:
    """Return a list of secret metadata dicts (name, created_at, updated_at).

    Secret *values* are never returned by the GitHub API.
    """
    client = await _factory.get_client(access_token)
    async with client as gh:
        resp = await gh.rest.actions.async_list_environment_secrets(
            owner=owner,
            repo=repo,
            environment_name=environment_name,
        )
        secrets = []
        for s in resp.parsed_data.secrets:
            secrets.append(
                {
                    "name": s.name,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                }
            )
        return secrets


async def _encrypt_secret_value(
    access_token: str,
    owner: str,
    repo: str,
    environment_name: str,
    plaintext: str,
) -> tuple[str, str]:
    """Fetch the environment's public key and return (key_id, encrypted_value).

    Uses NaCl sealed-box encryption as required by the GitHub API.
    """
    client = await _factory.get_client(access_token)
    async with client as gh:
        pk_resp = await gh.rest.actions.async_get_environment_public_key(
            owner=owner,
            repo=repo,
            environment_name=environment_name,
        )
    key_id: str = pk_resp.parsed_data.key_id
    raw_key: str = pk_resp.parsed_data.key

    # Decode the base64-encoded public key
    public_key_bytes = base64.b64decode(raw_key)
    public_key = PublicKey(public_key_bytes)
    sealed_box = SealedBox(public_key)

    encrypted = sealed_box.encrypt(plaintext.encode("utf-8"), encoder=Base64Encoder)
    encrypted_value = encrypted.decode("utf-8")

    return key_id, encrypted_value


async def set_secret(
    access_token: str,
    owner: str,
    repo: str,
    environment_name: str,
    secret_name: str,
    secret_value: str,
) -> None:
    """Create or update a secret in the specified repository environment."""
    key_id, encrypted_value = await _encrypt_secret_value(
        access_token, owner, repo, environment_name, secret_value
    )
    client = await _factory.get_client(access_token)
    async with client as gh:
        await gh.rest.actions.async_create_or_update_environment_secret(
            owner=owner,
            repo=repo,
            environment_name=environment_name,
            secret_name=secret_name,
            data={
                "encrypted_value": encrypted_value,
                "key_id": key_id,
            },
        )
    logger.info(
        "Set secret %s in %s/%s (env=%s)",
        secret_name,
        owner,
        repo,
        environment_name,
    )


async def delete_secret(
    access_token: str,
    owner: str,
    repo: str,
    environment_name: str,
    secret_name: str,
) -> None:
    """Delete a secret from the specified repository environment."""
    client = await _factory.get_client(access_token)
    async with client as gh:
        await gh.rest.actions.async_delete_environment_secret(
            owner=owner,
            repo=repo,
            environment_name=environment_name,
            secret_name=secret_name,
        )
    logger.info(
        "Deleted secret %s from %s/%s (env=%s)",
        secret_name,
        owner,
        repo,
        environment_name,
    )


async def check_secrets(
    access_token: str,
    owner: str,
    repo: str,
    environment_name: str,
    secret_names: list[str],
) -> dict[str, bool]:
    """Return a dict mapping each requested secret name to whether it exists."""
    existing = await list_secrets(access_token, owner, repo, environment_name)
    existing_names = {s["name"] for s in existing}
    return {name: name in existing_names for name in secret_names}
