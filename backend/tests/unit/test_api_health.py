"""Tests for health API routes (src/api/health.py).

Regression tests for bug-bash security fixes:
- Health check responses must not leak internal exception details.
"""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
class TestHealthCheckErrorLeakRegression:
    """Verify that health check never leaks exception text in HTTP responses."""

    async def test_database_check_failure_does_not_leak(self, client):
        """_check_database failure must not expose raw exception in response body."""
        mock_db = AsyncMock()
        mock_db.execute.side_effect = ConnectionError(
            "Could not connect to /var/run/secrets/db.sock"
        )
        with patch("src.api.health.get_db", return_value=mock_db):
            resp = await client.get("/api/v1/health")

        body = resp.json()
        db_output = body["checks"]["database"][0].get("output", "")
        assert "/var/run/secrets" not in db_output
        assert "db.sock" not in db_output
        assert body["checks"]["database"][0]["status"] == "fail"

    async def test_github_api_check_failure_does_not_leak(self, client):
        """_check_github_api failure must not expose raw exception in response body."""

        async def _failing_check() -> dict:
            return {"status": "fail", "output": "GitHub API connectivity check failed"}

        with patch("src.api.health.get_db", return_value=AsyncMock()):
            with patch(
                "src.api.health._check_github_api",
                side_effect=_failing_check,
            ):
                resp = await client.get("/api/v1/health")

        body = resp.json()
        gh_output = body["checks"]["github_api"][0].get("output", "")
        assert "CERTIFICATE_VERIFY_FAILED" not in gh_output
        assert "/etc/ssl" not in gh_output
        assert body["checks"]["github_api"][0]["status"] == "fail"
