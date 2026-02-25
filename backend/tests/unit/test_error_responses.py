"""Tests for error response handling (US4 — FR-009, FR-010).

T030:
- 429 responses include Retry-After header (SC-004)
- Task status update endpoint returns 501 Not Implemented
"""

import pytest


class TestRetryAfterHeader:
    """429 responses must include a Retry-After header."""

    @pytest.mark.anyio
    async def test_rate_limit_includes_retry_after_header(self, client):
        """When a RateLimitError is raised, the response must contain
        a Retry-After header with the configured number of seconds."""
        from unittest.mock import AsyncMock

        from src.exceptions import RateLimitError

        # Patch resolve_repository to raise RateLimitError with retry_after=45
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "src.api.tasks.resolve_repository",
                AsyncMock(side_effect=RateLimitError("Rate limit exceeded", retry_after=45)),
            )
            response = await client.post(
                "/api/v1/tasks",
                json={"title": "Test task", "project_id": "PVT_test123"},
            )

        assert response.status_code == 429
        assert "Retry-After" in response.headers
        assert response.headers["Retry-After"] == "45"

    @pytest.mark.anyio
    async def test_rate_limit_default_retry_after(self, client):
        """When no explicit retry_after is provided, the default (60s) is used."""
        from unittest.mock import AsyncMock

        from src.exceptions import RateLimitError

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "src.api.tasks.resolve_repository",
                AsyncMock(side_effect=RateLimitError()),
            )
            response = await client.post(
                "/api/v1/tasks",
                json={"title": "Test task", "project_id": "PVT_test123"},
            )

        assert response.status_code == 429
        assert response.headers["Retry-After"] == "60"

    @pytest.mark.anyio
    async def test_rate_limit_body_format(self, client):
        """429 response body must match standard error format."""
        from unittest.mock import AsyncMock

        from src.exceptions import RateLimitError

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "src.api.tasks.resolve_repository",
                AsyncMock(side_effect=RateLimitError("Rate limit exceeded", retry_after=30)),
            )
            response = await client.post(
                "/api/v1/tasks",
                json={"title": "Test task", "project_id": "PVT_test123"},
            )

        body = response.json()
        assert body["error"] == "Rate limit exceeded"
        assert body["details"] == {}


class TestTaskStatusEndpoint:
    """Task status update endpoint returns 501 Not Implemented."""

    @pytest.mark.anyio
    async def test_task_status_returns_501(self, client):
        """PATCH /tasks/{id}/status must return 501 Not Implemented."""
        response = await client.patch(
            "/api/v1/tasks/PVTI_some_id/status",
            params={"status": "Done"},
        )
        assert response.status_code == 501

    @pytest.mark.anyio
    async def test_task_status_501_body(self, client):
        """501 response body must include descriptive error and details."""
        response = await client.patch(
            "/api/v1/tasks/PVTI_some_id/status",
            params={"status": "In Progress"},
        )
        body = response.json()
        assert body["error"] == "Not implemented"
        assert "not yet implemented" in body["details"]["message"].lower()
