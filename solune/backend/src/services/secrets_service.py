"""GitHub Environment Secrets service.

Wraps githubkit environment secrets endpoints with NaCl sealed-box
encryption required by the GitHub API.  Follows the
``GitHubClientFactory.get_client()`` pooling pattern used elsewhere.
"""

from __future__ import annotations

import base64
from typing import Any

from nacl.encoding import Base64Encoder
from nacl.public import PublicKey, SealedBox

from src.services.github_projects import GitHubClientFactory
from src.logging_utils import get_logger

logger = get_logger(__name__)


class SecretsService:
    """CRUD operations for GitHub repository environment secrets."""

    def __init__(self, client_factory: GitHubClientFactory) -> None:
        self._client_factory = client_factory

    # ------------------------------------------------------------------
    # Environment helpers
    # ------------------------------------------------------------------

    async def get_or_create_environment(
        self,
        access_token: str,
        owner: str,
        repo: str,
        environment_name: str,
    ) -> None:
        """Ensure the target deployment environment exists."""
        client = await self._client_factory.get_client(access_token)
        await client.rest.repos.async_create_or_update_environment(
            owner=owner,
            repo=repo,
            environment_name=environment_name,
        )

    # ------------------------------------------------------------------
    # Secret CRUD
    # ------------------------------------------------------------------

    async def list_secrets(
        self,
        access_token: str,
        owner: str,
        repo: str,
        environment_name: str,
    ) -> dict[str, Any]:
        """Return the list of secret names + metadata (values are never exposed)."""
        client = await self._client_factory.get_client(access_token)
        response = await client.rest.actions.async_list_environment_secrets(
            owner=owner,
            repo=repo,
            environment_name=environment_name,
        )
        return response.parsed_data.model_dump()

    async def set_secret(
        self,
        access_token: str,
        owner: str,
        repo: str,
        environment_name: str,
        secret_name: str,
        secret_value: str,
    ) -> None:
        """Encrypt *secret_value* with the environment public key and upsert."""
        encrypted_value, key_id = await self._encrypt_secret_value(
            access_token, owner, repo, environment_name, secret_value
        )
        client = await self._client_factory.get_client(access_token)
        await client.rest.actions.async_create_or_update_environment_secret(
            owner=owner,
            repo=repo,
            environment_name=environment_name,
            secret_name=secret_name,
            data={"encrypted_value": encrypted_value, "key_id": key_id},
        )

    async def delete_secret(
        self,
        access_token: str,
        owner: str,
        repo: str,
        environment_name: str,
        secret_name: str,
    ) -> None:
        """Remove an environment secret."""
        client = await self._client_factory.get_client(access_token)
        await client.rest.actions.async_delete_environment_secret(
            owner=owner,
            repo=repo,
            environment_name=environment_name,
            secret_name=secret_name,
        )

    async def check_secrets(
        self,
        access_token: str,
        owner: str,
        repo: str,
        environment_name: str,
        secret_names: list[str],
    ) -> dict[str, bool]:
        """Return a mapping of requested names → exists (True/False)."""
        data = await self.list_secrets(access_token, owner, repo, environment_name)
        existing = {s["name"] for s in data.get("secrets", [])}
        return {name: name in existing for name in secret_names}

    # ------------------------------------------------------------------
    # Encryption
    # ------------------------------------------------------------------

    async def _encrypt_secret_value(
        self,
        access_token: str,
        owner: str,
        repo: str,
        environment_name: str,
        plaintext: str,
    ) -> tuple[str, str]:
        """Fetch the environment public key, encrypt with NaCl sealed-box.

        Returns ``(base64_ciphertext, key_id)``.
        """
        client = await self._client_factory.get_client(access_token)
        pk_response = await client.rest.actions.async_get_environment_public_key(
            owner=owner,
            repo=repo,
            environment_name=environment_name,
        )
        pk_data = pk_response.parsed_data
        public_key_bytes = base64.b64decode(pk_data.key)
        public_key = PublicKey(public_key_bytes)
        sealed_box = SealedBox(public_key)
        encrypted = sealed_box.encrypt(
            plaintext.encode(),
            encoder=Base64Encoder,
        )
        return encrypted.decode(), pk_data.key_id
