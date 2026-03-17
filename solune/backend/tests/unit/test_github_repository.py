"""Unit tests for RepositoryMixin.create_repository and list_available_owners."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


def _mock_response(status_code: int, json_data: dict | list) -> MagicMock:
    """Create a mock HTTP response with status_code and .json()."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.text = str(json_data)
    return resp


class FakeRepositoryService:
    """Minimal stub that exposes RepositoryMixin methods with a mocked _rest."""

    def __init__(self) -> None:
        self._rest = AsyncMock()
        self._rest_response = AsyncMock()
        self._graphql = AsyncMock()

    # Pull in the real mixin methods
    from src.services.github_projects.repository import RepositoryMixin

    create_repository = RepositoryMixin.create_repository
    list_available_owners = RepositoryMixin.list_available_owners
    set_repository_secret = RepositoryMixin.set_repository_secret


class TestCreateRepository:
    @pytest.mark.asyncio
    async def test_creates_personal_repo(self) -> None:
        svc = FakeRepositoryService()
        resp_data = {
            "id": 123,
            "node_id": "R_abc",
            "name": "my-app",
            "full_name": "user/my-app",
            "html_url": "https://github.com/user/my-app",
            "default_branch": "main",
        }
        svc._rest_response.return_value = _mock_response(201, resp_data)

        result = await svc.create_repository("tok", "my-app", private=True, auto_init=True)

        svc._rest_response.assert_awaited_once()
        call_args = svc._rest_response.call_args
        assert call_args[0][1] == "POST"
        assert call_args[0][2] == "/user/repos"
        body = call_args[1]["json"]
        assert body["name"] == "my-app"
        assert body["private"] is True
        assert body["auto_init"] is True

        assert result["id"] == 123
        assert result["node_id"] == "R_abc"
        assert result["name"] == "my-app"
        assert result["html_url"] == "https://github.com/user/my-app"
        assert result["default_branch"] == "main"

    @pytest.mark.asyncio
    async def test_creates_org_repo(self) -> None:
        svc = FakeRepositoryService()
        resp_data = {
            "id": 456,
            "node_id": "R_xyz",
            "name": "my-app",
            "full_name": "my-org/my-app",
            "html_url": "https://github.com/my-org/my-app",
            "default_branch": "main",
        }
        svc._rest_response.return_value = _mock_response(201, resp_data)

        result = await svc.create_repository("tok", "my-app", owner="my-org")

        call_args = svc._rest_response.call_args
        assert call_args[0][2] == "/orgs/my-org/repos"
        assert result["full_name"] == "my-org/my-app"

    @pytest.mark.asyncio
    async def test_auto_init_default_true(self) -> None:
        svc = FakeRepositoryService()
        svc._rest_response.return_value = _mock_response(
            201,
            {
                "id": 1,
                "node_id": "R_1",
                "name": "x",
                "full_name": "u/x",
                "html_url": "",
                "default_branch": "main",
            },
        )

        await svc.create_repository("tok", "x")
        body = svc._rest_response.call_args[1]["json"]
        assert body["auto_init"] is True

    @pytest.mark.asyncio
    async def test_returns_default_branch_fallback(self) -> None:
        svc = FakeRepositoryService()
        svc._rest_response.return_value = _mock_response(
            201, {"id": 1, "node_id": "R_1", "name": "x", "full_name": "u/x", "html_url": ""}
        )

        result = await svc.create_repository("tok", "x")
        assert result["default_branch"] == "main"

    @pytest.mark.asyncio
    async def test_raises_on_github_error(self) -> None:
        from src.exceptions import GitHubAPIError

        svc = FakeRepositoryService()
        svc._rest_response.return_value = _mock_response(
            422, {"message": "Repository creation failed", "errors": [{"field": "name"}]}
        )

        with pytest.raises(GitHubAPIError, match="Repository creation failed"):
            await svc.create_repository("tok", "bad-name")


class TestListAvailableOwners:
    @pytest.mark.asyncio
    async def test_returns_user_and_orgs(self) -> None:
        svc = FakeRepositoryService()
        svc._rest.side_effect = [
            {"login": "alice", "avatar_url": "https://a.com/alice.png"},
            [
                {"login": "org1", "avatar_url": "https://a.com/org1.png"},
                {"login": "org2", "avatar_url": "https://a.com/org2.png"},
            ],
        ]

        owners = await svc.list_available_owners("tok")

        assert len(owners) == 3
        assert owners[0] == {
            "login": "alice",
            "avatar_url": "https://a.com/alice.png",
            "type": "User",
        }
        assert owners[1]["login"] == "org1"
        assert owners[1]["type"] == "Organization"
        assert owners[2]["login"] == "org2"

    @pytest.mark.asyncio
    async def test_returns_only_user_when_no_orgs(self) -> None:
        svc = FakeRepositoryService()
        svc._rest.side_effect = [
            {"login": "bob", "avatar_url": ""},
            [],
        ]

        owners = await svc.list_available_owners("tok")
        assert len(owners) == 1
        assert owners[0]["login"] == "bob"
        assert owners[0]["type"] == "User"


class TestSetRepositorySecret:
    """Unit tests for RepositoryMixin.set_repository_secret.

    Validates:
    - GET /repos/{owner}/{repo}/actions/secrets/public-key is called first to
      fetch the public key and key_id.
    - The secret is encrypted using PyNaCl sealed-box and base64-encoded.
    - PUT /repos/{owner}/{repo}/actions/secrets/{name} is called with the
      encrypted value and key_id.
    - API errors (from _rest) propagate to the caller.
    """

    @pytest.mark.asyncio
    async def test_happy_path_calls_get_then_put(self) -> None:
        """set_repository_secret fetches the public key then PUTs the encrypted value."""
        import base64

        from nacl.public import PrivateKey

        svc = FakeRepositoryService()

        # Generate a real NaCl key pair so the sealed box decryption can be verified.
        recipient_sk = PrivateKey.generate()
        pk_b64 = base64.b64encode(bytes(recipient_sk.public_key)).decode()
        key_id = "key-id-1"

        svc._rest.side_effect = [
            {"key": pk_b64, "key_id": key_id},  # GET public-key response
            None,  # PUT secret response
        ]

        await svc.set_repository_secret("tok", "owner", "repo", "MY_SECRET", "secret-value")

        assert svc._rest.await_count == 2
        # First call: GET public key
        get_call = svc._rest.call_args_list[0]
        assert get_call[0][1] == "GET"
        assert "/actions/secrets/public-key" in get_call[0][2]

        # Second call: PUT secret with encrypted value and key_id
        put_call = svc._rest.call_args_list[1]
        assert put_call[0][1] == "PUT"
        assert "MY_SECRET" in put_call[0][2]
        put_body = put_call[1]["json"]
        assert put_body["key_id"] == key_id
        # encrypted_value should be non-empty base64
        encrypted_b64 = put_body["encrypted_value"]
        assert isinstance(encrypted_b64, str) and len(encrypted_b64) > 0
        # Verify the sealed box can be decrypted by the recipient key
        from nacl.public import SealedBox

        decrypted = SealedBox(recipient_sk).decrypt(base64.b64decode(encrypted_b64))
        assert decrypted == b"secret-value"

    @pytest.mark.asyncio
    async def test_propagates_api_error_on_get_public_key_failure(self) -> None:
        """set_repository_secret re-raises when GET public-key fails."""
        svc = FakeRepositoryService()
        svc._rest.side_effect = Exception("403 Forbidden")

        with pytest.raises(Exception, match="403 Forbidden"):
            await svc.set_repository_secret("tok", "owner", "repo", "SECRET", "value")

    @pytest.mark.asyncio
    async def test_propagates_api_error_on_put_failure(self) -> None:
        """set_repository_secret re-raises when PUT secret fails."""
        import base64

        from nacl.public import PrivateKey

        svc = FakeRepositoryService()
        recipient_sk = PrivateKey.generate()
        pk_b64 = base64.b64encode(bytes(recipient_sk.public_key)).decode()

        svc._rest.side_effect = [
            {"key": pk_b64, "key_id": "kid"},
            Exception("422 Unprocessable Entity"),
        ]

        with pytest.raises(Exception, match="422 Unprocessable Entity"):
            await svc.set_repository_secret("tok", "owner", "repo", "SECRET", "value")

    @pytest.mark.asyncio
    async def test_different_secrets_use_same_key_from_first_call(self) -> None:
        """Each call to set_repository_secret makes exactly one GET and one PUT."""
        import base64

        from nacl.public import PrivateKey

        svc = FakeRepositoryService()
        recipient_sk = PrivateKey.generate()
        pk_b64 = base64.b64encode(bytes(recipient_sk.public_key)).decode()

        # Two independent calls each need their own GET + PUT
        svc._rest.side_effect = [
            {"key": pk_b64, "key_id": "kid"},
            None,
            {"key": pk_b64, "key_id": "kid"},
            None,
        ]

        await svc.set_repository_secret("tok", "o", "r", "SECRET_A", "val-a")
        await svc.set_repository_secret("tok", "o", "r", "SECRET_B", "val-b")

        assert svc._rest.await_count == 4
