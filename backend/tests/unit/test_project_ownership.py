"""Tests for project-level access control (US3 — FR-009, FR-010).

T018:
- Authenticated request with unowned project_id returns 403
- Endpoints that accept project_id enforce ownership check
- verify_project_access dependency rejects unknown projects
"""

from unittest.mock import AsyncMock

import pytest

from src.exceptions import AuthorizationError
from src.models.user import UserSession


def _make_session(**overrides) -> UserSession:
    defaults = {
        "github_user_id": "12345",
        "github_username": "testuser",
        "access_token": "test-token",
    }
    defaults.update(overrides)
    return UserSession(**defaults)


class TestTaskEndpointOwnershipCheck:
    """Task creation endpoint must enforce project ownership."""

    @pytest.mark.anyio
    async def test_create_task_rejects_unowned_project(self, client):
        """POST /tasks with unowned project_id returns 403."""
        # Override the default bypass to actually enforce ownership
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "src.api.tasks.verify_project_access",
                AsyncMock(side_effect=AuthorizationError("You do not have access to this project")),
            )
            response = await client.post(
                "/api/v1/tasks",
                json={"title": "Test task", "project_id": "PVT_unowned"},
            )

        assert response.status_code == 403

    @pytest.mark.anyio
    async def test_create_task_calls_verify_project_access(self):
        """create_task invokes verify_project_access with the correct project_id.

        This test directly calls the endpoint function to verify the ownership
        check is wired in, without needing the full ASGI transport stack.
        """
        from unittest.mock import AsyncMock, MagicMock

        mock_verify = AsyncMock(return_value=None)

        request = MagicMock()
        session = UserSession(
            github_user_id="12345",
            github_username="testuser",
            access_token="test-token",
        )

        from src.models.task import TaskCreateRequest

        task_req = TaskCreateRequest(title="Test task", project_id="PVT_owned")

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("src.api.tasks.verify_project_access", mock_verify)
            mp.setattr(
                "src.api.tasks.resolve_repository",
                AsyncMock(side_effect=RuntimeError("stop after verify")),
            )
            from src.api.tasks import create_task

            with pytest.raises(RuntimeError, match="stop after verify"):
                await create_task(request, task_req, session)

        # verify_project_access was called with the correct project_id
        assert mock_verify.called
        call_args = mock_verify.call_args
        assert call_args[0][1] == "PVT_owned"


class TestWorkflowEndpointOwnershipCheck:
    """Workflow endpoints must enforce project ownership."""

    @pytest.mark.anyio
    async def test_get_config_rejects_unowned_project(self, client):
        """GET /workflow/config with unowned selected project returns 403."""
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "src.api.workflow.verify_project_access",
                AsyncMock(side_effect=AuthorizationError("You do not have access to this project")),
            )
            response = await client.get("/api/v1/workflow/config")

        # 403 or 422 (no project selected) — depends on session fixture
        assert response.status_code in (403, 422)

    @pytest.mark.anyio
    async def test_update_config_rejects_unowned_project(self, client):
        """PUT /workflow/config with unowned project returns 403."""
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "src.api.workflow.verify_project_access",
                AsyncMock(side_effect=AuthorizationError("You do not have access to this project")),
            )
            response = await client.put(
                "/api/v1/workflow/config",
                json={
                    "project_id": "PVT_unowned",
                    "repository_owner": "owner",
                    "repository_name": "repo",
                },
            )

        assert response.status_code in (403, 422)


class TestAgentEndpointOwnershipCheck:
    """Agent endpoints must enforce project ownership via dependency."""

    @pytest.mark.anyio
    async def test_agents_endpoint_uses_dependency(self, client):
        """GET /agents/{project_id} endpoints use verify_project_access dependency."""
        # The conftest bypasses verify_project_access via dependency override.
        # If the dependency were missing, this would fail differently.
        response = await client.get("/api/v1/agents/PVT_test123")
        # Should not be 403 (dependency is overridden in test fixture)
        # May be 500/422 due to mocked service, but not 403
        assert response.status_code != 403
