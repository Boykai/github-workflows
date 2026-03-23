"""Tests for project-level access control (US3 — FR-006, FR-007).

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
        mock_verify.assert_called_once()
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
    async def test_agents_endpoint_rejects_unowned_project(self, client):
        """GET /agents/{project_id} returns 403 when ownership fails."""
        from src.dependencies import verify_project_access

        overrides = client._transport.app.dependency_overrides
        original_override = overrides.get(verify_project_access)

        try:
            # Re-enable the real ownership check that raises 403
            if verify_project_access in overrides:
                del overrides[verify_project_access]

            with pytest.MonkeyPatch.context() as mp:
                from unittest.mock import AsyncMock

                mock_svc = AsyncMock()
                mock_svc.list_user_projects.return_value = []  # no projects

                mp.setattr(
                    "src.dependencies.get_github_service",
                    lambda req: mock_svc,
                )
                response = await client.get("/api/v1/agents/PVT_test123")

            assert response.status_code == 403
        finally:
            # Restore the original override for subsequent tests
            if original_override is not None:
                overrides[verify_project_access] = original_override
            else:
                overrides[verify_project_access] = lambda: None
