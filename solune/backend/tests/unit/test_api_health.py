"""Tests for health check endpoint (src/api/health.py).

Covers:
- GET /api/v1/health -> health_check
- All components pass -> 200, status "pass"
- Database fails -> 503, status "fail"
- GitHub API fails -> 503, status "fail"
- Polling loop stopped -> 200, status "pass" (warn component, not fail)
- Database exception -> 503
"""

from unittest.mock import AsyncMock, patch

import pytest

HEALTH_URL = "/api/v1/health"


class TestHealthAllPass:
    """Tests when all health check components pass."""

    @pytest.fixture(autouse=True)
    def _patch(self):
        with (
            patch("src.api.health._check_database", new_callable=AsyncMock) as mock_db,
            patch("src.api.health._check_github_api", new_callable=AsyncMock) as mock_gh,
            patch("src.api.health._check_polling_loop") as mock_poll,
        ):
            mock_db.return_value = {"status": "pass", "time": "1ms"}
            mock_gh.return_value = {"status": "pass", "time": "50ms"}
            mock_poll.return_value = {"status": "pass", "observed_value": "running"}
            yield

    async def test_all_pass_returns_200(self, client):
        """All components healthy returns 200 with status pass."""
        resp = await client.get(HEALTH_URL)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "pass"

    async def test_all_pass_has_three_components(self, client):
        """Response includes database, github_api, and polling_loop checks."""
        resp = await client.get(HEALTH_URL)
        checks = resp.json()["checks"]
        assert "database" in checks
        assert "github_api" in checks
        assert "polling_loop" in checks


class TestHealthDatabaseFail:
    """Tests when the database health check fails."""

    @pytest.fixture(autouse=True)
    def _patch(self):
        with (
            patch("src.api.health._check_database", new_callable=AsyncMock) as mock_db,
            patch("src.api.health._check_github_api", new_callable=AsyncMock) as mock_gh,
            patch("src.api.health._check_polling_loop") as mock_poll,
        ):
            mock_db.return_value = {"status": "fail", "output": "database connectivity"}
            mock_gh.return_value = {"status": "pass", "time": "50ms"}
            mock_poll.return_value = {"status": "pass", "observed_value": "running"}
            yield

    async def test_db_fail_returns_503(self, client):
        """Database failure results in 503 with status fail."""
        resp = await client.get(HEALTH_URL)
        assert resp.status_code == 503
        assert resp.json()["status"] == "fail"


class TestHealthGitHubApiFail:
    """Tests when the GitHub API health check fails."""

    @pytest.fixture(autouse=True)
    def _patch(self):
        with (
            patch("src.api.health._check_database", new_callable=AsyncMock) as mock_db,
            patch("src.api.health._check_github_api", new_callable=AsyncMock) as mock_gh,
            patch("src.api.health._check_polling_loop") as mock_poll,
        ):
            mock_db.return_value = {"status": "pass", "time": "1ms"}
            mock_gh.return_value = {"status": "fail", "output": "GitHub API connectivity"}
            mock_poll.return_value = {"status": "pass", "observed_value": "running"}
            yield

    async def test_github_api_fail_returns_503(self, client):
        """GitHub API failure results in 503."""
        resp = await client.get(HEALTH_URL)
        assert resp.status_code == 503
        assert resp.json()["status"] == "fail"


class TestHealthPollingLoopStopped:
    """Tests when the polling loop is stopped (warn, not fail)."""

    @pytest.fixture(autouse=True)
    def _patch(self):
        with (
            patch("src.api.health._check_database", new_callable=AsyncMock) as mock_db,
            patch("src.api.health._check_github_api", new_callable=AsyncMock) as mock_gh,
            patch("src.api.health._check_polling_loop") as mock_poll,
        ):
            mock_db.return_value = {"status": "pass", "time": "1ms"}
            mock_gh.return_value = {"status": "pass", "time": "50ms"}
            mock_poll.return_value = {"status": "warn", "observed_value": "stopped"}
            yield

    async def test_polling_stopped_returns_200(self, client):
        """Polling loop stopped is a warn, not a fail -- still 200."""
        resp = await client.get(HEALTH_URL)
        assert resp.status_code == 200

    async def test_polling_stopped_overall_pass(self, client):
        """Overall status is pass when only polling_loop is warn."""
        resp = await client.get(HEALTH_URL)
        assert resp.json()["status"] == "pass"


class TestHealthDatabaseException:
    """Tests when the database check function returns fail due to exception."""

    @pytest.fixture(autouse=True)
    def _patch(self):
        with (
            patch("src.api.health._check_database", new_callable=AsyncMock) as mock_db,
            patch("src.api.health._check_github_api", new_callable=AsyncMock) as mock_gh,
            patch("src.api.health._check_polling_loop") as mock_poll,
        ):
            mock_db.return_value = {"status": "fail", "output": "database connectivity"}
            mock_gh.return_value = {"status": "pass", "time": "50ms"}
            mock_poll.return_value = {"status": "pass", "observed_value": "running"}
            yield

    async def test_db_exception_returns_503(self, client):
        """Database exception causes 503."""
        resp = await client.get(HEALTH_URL)
        assert resp.status_code == 503
        assert resp.json()["status"] == "fail"
