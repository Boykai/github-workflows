"""Tests for structured health endpoint (US7 — FR-020, SC-008).

T036:
- Health endpoint returns structured per-component status
- Returns 503 when database is unreachable
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def health_client():
    """Client for health endpoint tests — no auth dependency override needed."""
    from src.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


class TestHealthEndpoint:
    """GET /api/v1/health must return structured per-component health."""

    @pytest.mark.anyio
    async def test_healthy_response_structure(self, health_client):
        """When all checks pass, return 200 with status=pass and per-component results."""
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=AsyncMock(fetchone=AsyncMock(return_value=(1,))))

        with (
            patch("src.api.health.get_db", return_value=mock_db),
            patch(
                "src.api.health._check_github_api", return_value={"status": "pass", "time": "50ms"}
            ),
            patch(
                "src.api.health._check_polling_loop",
                return_value={"status": "pass", "observed_value": "running"},
            ),
        ):
            response = await health_client.get("/api/v1/health")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "pass"
        assert "checks" in body
        assert "database" in body["checks"]
        assert "github_api" in body["checks"]
        assert "polling_loop" in body["checks"]

    @pytest.mark.anyio
    async def test_unhealthy_returns_503(self, health_client):
        """When database check fails, return 503 with status=fail."""
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=Exception("database is locked"))

        with (
            patch("src.api.health.get_db", return_value=mock_db),
            patch(
                "src.api.health._check_github_api", return_value={"status": "pass", "time": "50ms"}
            ),
            patch(
                "src.api.health._check_polling_loop",
                return_value={"status": "pass", "observed_value": "running"},
            ),
        ):
            response = await health_client.get("/api/v1/health")

        assert response.status_code == 503
        body = response.json()
        assert body["status"] == "fail"
        assert body["checks"]["database"][0]["status"] == "fail"

    @pytest.mark.anyio
    async def test_polling_not_running(self, health_client):
        """When polling loop is not running, it reports as warn but overall can still pass."""
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=AsyncMock(fetchone=AsyncMock(return_value=(1,))))

        with (
            patch("src.api.health.get_db", return_value=mock_db),
            patch(
                "src.api.health._check_github_api", return_value={"status": "pass", "time": "50ms"}
            ),
            patch(
                "src.api.health._check_polling_loop",
                return_value={"status": "warn", "observed_value": "stopped"},
            ),
        ):
            response = await health_client.get("/api/v1/health")

        body = response.json()
        # warn does not degrade to 503 — only fail does
        assert response.status_code == 200
        assert body["checks"]["polling_loop"][0]["status"] == "warn"
