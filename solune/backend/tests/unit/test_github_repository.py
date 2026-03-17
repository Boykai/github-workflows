"""Unit tests for RepositoryMixin.create_repository and list_available_owners."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest


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


class TestCreateRepository:
    @pytest.mark.asyncio
    async def test_creates_personal_repo(self) -> None:
        svc = FakeRepositoryService()
        svc._rest.return_value = {
            "id": 123,
            "node_id": "R_abc",
            "name": "my-app",
            "full_name": "user/my-app",
            "html_url": "https://github.com/user/my-app",
            "default_branch": "main",
        }

        result = await svc.create_repository("tok", "my-app", private=True, auto_init=True)

        svc._rest.assert_awaited_once()
        call_args = svc._rest.call_args
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
        svc._rest.return_value = {
            "id": 456,
            "node_id": "R_xyz",
            "name": "my-app",
            "full_name": "my-org/my-app",
            "html_url": "https://github.com/my-org/my-app",
            "default_branch": "main",
        }

        result = await svc.create_repository("tok", "my-app", owner="my-org")

        call_args = svc._rest.call_args
        assert call_args[0][2] == "/orgs/my-org/repos"
        assert result["full_name"] == "my-org/my-app"

    @pytest.mark.asyncio
    async def test_auto_init_default_true(self) -> None:
        svc = FakeRepositoryService()
        svc._rest.return_value = {"id": 1, "node_id": "R_1", "name": "x", "full_name": "u/x", "html_url": "", "default_branch": "main"}

        await svc.create_repository("tok", "x")
        body = svc._rest.call_args[1]["json"]
        assert body["auto_init"] is True

    @pytest.mark.asyncio
    async def test_returns_default_branch_fallback(self) -> None:
        svc = FakeRepositoryService()
        svc._rest.return_value = {"id": 1, "node_id": "R_1", "name": "x", "full_name": "u/x", "html_url": ""}

        result = await svc.create_repository("tok", "x")
        assert result["default_branch"] == "main"


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
        assert owners[0] == {"login": "alice", "avatar_url": "https://a.com/alice.png", "type": "User"}
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
