"""Unit tests for ProjectsMixin.create_project_v2 and link_project_to_repository."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest


class FakeProjectsService:
    """Stub that exposes ProjectsMixin creation methods with mocked transports."""

    def __init__(self) -> None:
        self._rest = AsyncMock()
        self._rest_response = AsyncMock()
        self._graphql = AsyncMock()

    from src.services.github_projects.projects import ProjectsMixin

    create_project_v2 = ProjectsMixin.create_project_v2
    _configure_project_status = ProjectsMixin._configure_project_status
    link_project_to_repository = ProjectsMixin.link_project_to_repository


class TestCreateProjectV2:
    @pytest.mark.asyncio
    async def test_happy_path(self) -> None:
        svc = FakeProjectsService()
        # First _rest call: GET /users/{owner} → user node_id
        svc._rest.return_value = {"node_id": "U_abc123"}
        # GraphQL createProjectV2 mutation
        svc._graphql.side_effect = [
            {
                "createProjectV2": {
                    "projectV2": {
                        "id": "PVT_123",
                        "number": 5,
                        "url": "https://github.com/users/alice/projects/5",
                    }
                }
            },
            # GET_PROJECT_STATUS_FIELD_QUERY
            {
                "node": {
                    "field": {
                        "id": "FIELD_status",
                        "options": [],
                    }
                }
            },
            # UPDATE_PROJECT_V2_SINGLE_SELECT_FIELD_MUTATION
            {
                "updateProjectV2SingleSelectField": {
                    "projectV2SingleSelectField": {
                        "id": "FIELD_status",
                        "options": [
                            {"id": "1", "name": "Backlog", "color": "GRAY"},
                            {"id": "2", "name": "In Progress", "color": "YELLOW"},
                        ],
                    }
                }
            },
        ]

        result = await svc.create_project_v2("tok", owner="alice", title="My Project")

        assert result["id"] == "PVT_123"
        assert result["number"] == 5
        assert result["url"] == "https://github.com/users/alice/projects/5"

    @pytest.mark.asyncio
    async def test_status_config_failure_is_non_blocking(self) -> None:
        svc = FakeProjectsService()
        svc._rest.return_value = {"node_id": "U_abc123"}
        svc._graphql.side_effect = [
            # createProjectV2 succeeds
            {
                "createProjectV2": {
                    "projectV2": {
                        "id": "PVT_456",
                        "number": 1,
                        "url": "https://github.com/users/bob/projects/1",
                    }
                }
            },
            # Status field query fails
            ValueError("GraphQL error"),
        ]

        # Should NOT raise — status config failure is non-blocking
        result = await svc.create_project_v2("tok", owner="bob", title="Test")
        assert result["id"] == "PVT_456"

    @pytest.mark.asyncio
    async def test_resolves_org_owner(self) -> None:
        svc = FakeProjectsService()
        # GET /users/{owner} fails, GET /orgs/{owner} succeeds
        svc._rest.side_effect = [
            ValueError("Not found"),
            {"node_id": "O_org123"},
        ]
        svc._graphql.side_effect = [
            {
                "createProjectV2": {
                    "projectV2": {
                        "id": "PVT_org",
                        "number": 2,
                        "url": "https://github.com/orgs/my-org/projects/2",
                    }
                }
            },
            {"node": {"field": None}},  # No Status field → skip config
        ]

        result = await svc.create_project_v2("tok", owner="my-org", title="Org Project")
        assert result["id"] == "PVT_org"


class TestLinkProjectToRepository:
    @pytest.mark.asyncio
    async def test_happy_path(self) -> None:
        svc = FakeProjectsService()
        svc._graphql.return_value = {"linkProjectV2ToRepository": {"repository": {"id": "R_abc"}}}

        await svc.link_project_to_repository("tok", project_id="PVT_1", repository_id="R_abc")
        svc._graphql.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_idempotent_call(self) -> None:
        """Calling link twice should just make two GraphQL calls (idempotent)."""
        svc = FakeProjectsService()
        svc._graphql.return_value = {"linkProjectV2ToRepository": {"repository": {"id": "R_abc"}}}

        await svc.link_project_to_repository("tok", project_id="PVT_1", repository_id="R_abc")
        await svc.link_project_to_repository("tok", project_id="PVT_1", repository_id="R_abc")
        assert svc._graphql.await_count == 2
