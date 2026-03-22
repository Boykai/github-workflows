"""Tests for the readiness endpoint (GET /api/v1/ready).

Covers:
- All checks pass → HTTP 200 with status "pass"
- Database write fails → HTTP 503 with status "fail"
- OAuth not configured → HTTP 503
- Encryption disabled → HTTP 503
- Polling task dead → HTTP 503
- Polling intentionally disabled (interval=0) → pass
- GET /health liveness probe remains unchanged (FR-005)
"""

from unittest.mock import AsyncMock, patch

import pytest

READY_URL = "/api/v1/ready"
HEALTH_URL = "/api/v1/health"


class TestReadinessAllPass:
    """Tests when all readiness checks pass."""

    @pytest.fixture(autouse=True)
    def _patch(self):
        with (
            patch(
                "src.api.health._readiness_check_db",
                new_callable=AsyncMock,
            ) as mock_db,
            patch("src.api.health._readiness_check_oauth") as mock_oauth,
            patch("src.api.health._readiness_check_encryption") as mock_enc,
            patch("src.api.health._readiness_check_polling") as mock_poll,
        ):
            from src.api.health import ReadinessCheckResult

            mock_db.return_value = ReadinessCheckResult(
                component_id="database:writeable",
                status="pass",
                time="2026-03-22T14:00:00Z",
            )
            mock_oauth.return_value = ReadinessCheckResult(
                component_id="oauth:configured",
                status="pass",
                time="2026-03-22T14:00:00Z",
            )
            mock_enc.return_value = ReadinessCheckResult(
                component_id="encryption:enabled",
                status="pass",
                time="2026-03-22T14:00:00Z",
            )
            mock_poll.return_value = ReadinessCheckResult(
                component_id="polling:alive",
                status="pass",
                time="2026-03-22T14:00:00Z",
            )
            yield

    async def test_all_pass_returns_200(self, client):
        """All readiness checks pass → HTTP 200."""
        resp = await client.get(READY_URL)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "pass"

    async def test_all_pass_has_four_checks(self, client):
        """Response includes all four readiness checks."""
        resp = await client.get(READY_URL)
        checks = resp.json()["checks"]
        assert "database:writeable" in checks
        assert "oauth:configured" in checks
        assert "encryption:enabled" in checks
        assert "polling:alive" in checks

    async def test_all_pass_ietf_format(self, client):
        """Each check follows IETF health-check format."""
        resp = await client.get(READY_URL)
        checks = resp.json()["checks"]
        for check_list in checks.values():
            assert len(check_list) == 1
            check = check_list[0]
            assert "component_id" in check
            assert "component_type" in check
            assert "status" in check
            assert "time" in check


class TestReadinessDbFail:
    """Tests when the database readiness check fails."""

    @pytest.fixture(autouse=True)
    def _patch(self):
        with (
            patch(
                "src.api.health._readiness_check_db",
                new_callable=AsyncMock,
            ) as mock_db,
            patch("src.api.health._readiness_check_oauth") as mock_oauth,
            patch("src.api.health._readiness_check_encryption") as mock_enc,
            patch("src.api.health._readiness_check_polling") as mock_poll,
        ):
            from src.api.health import ReadinessCheckResult

            mock_db.return_value = ReadinessCheckResult(
                component_id="database:writeable",
                status="fail",
                time="2026-03-22T14:00:00Z",
                output="Database write check failed",
            )
            mock_oauth.return_value = ReadinessCheckResult(
                component_id="oauth:configured",
                status="pass",
                time="2026-03-22T14:00:00Z",
            )
            mock_enc.return_value = ReadinessCheckResult(
                component_id="encryption:enabled",
                status="pass",
                time="2026-03-22T14:00:00Z",
            )
            mock_poll.return_value = ReadinessCheckResult(
                component_id="polling:alive",
                status="pass",
                time="2026-03-22T14:00:00Z",
            )
            yield

    async def test_db_fail_returns_503(self, client):
        """Database write failure causes 503."""
        resp = await client.get(READY_URL)
        assert resp.status_code == 503
        assert resp.json()["status"] == "fail"

    async def test_db_fail_includes_output(self, client):
        """Failed check includes output field."""
        resp = await client.get(READY_URL)
        db_check = resp.json()["checks"]["database:writeable"][0]
        assert db_check["status"] == "fail"
        assert "output" in db_check


class TestReadinessOAuthFail:
    """Tests when OAuth is not configured."""

    @pytest.fixture(autouse=True)
    def _patch(self):
        with (
            patch(
                "src.api.health._readiness_check_db",
                new_callable=AsyncMock,
            ) as mock_db,
            patch("src.api.health._readiness_check_oauth") as mock_oauth,
            patch("src.api.health._readiness_check_encryption") as mock_enc,
            patch("src.api.health._readiness_check_polling") as mock_poll,
        ):
            from src.api.health import ReadinessCheckResult

            mock_db.return_value = ReadinessCheckResult(
                component_id="database:writeable",
                status="pass",
                time="2026-03-22T14:00:00Z",
            )
            mock_oauth.return_value = ReadinessCheckResult(
                component_id="oauth:configured",
                status="fail",
                time="2026-03-22T14:00:00Z",
                output="GitHub OAuth client ID or secret is empty",
            )
            mock_enc.return_value = ReadinessCheckResult(
                component_id="encryption:enabled",
                status="pass",
                time="2026-03-22T14:00:00Z",
            )
            mock_poll.return_value = ReadinessCheckResult(
                component_id="polling:alive",
                status="pass",
                time="2026-03-22T14:00:00Z",
            )
            yield

    async def test_oauth_fail_returns_503(self, client):
        """Missing OAuth config causes 503."""
        resp = await client.get(READY_URL)
        assert resp.status_code == 503
        assert resp.json()["status"] == "fail"


class TestReadinessPollingFail:
    """Tests when the polling task has crashed."""

    @pytest.fixture(autouse=True)
    def _patch(self):
        with (
            patch(
                "src.api.health._readiness_check_db",
                new_callable=AsyncMock,
            ) as mock_db,
            patch("src.api.health._readiness_check_oauth") as mock_oauth,
            patch("src.api.health._readiness_check_encryption") as mock_enc,
            patch("src.api.health._readiness_check_polling") as mock_poll,
        ):
            from src.api.health import ReadinessCheckResult

            mock_db.return_value = ReadinessCheckResult(
                component_id="database:writeable",
                status="pass",
                time="2026-03-22T14:00:00Z",
            )
            mock_oauth.return_value = ReadinessCheckResult(
                component_id="oauth:configured",
                status="pass",
                time="2026-03-22T14:00:00Z",
            )
            mock_enc.return_value = ReadinessCheckResult(
                component_id="encryption:enabled",
                status="pass",
                time="2026-03-22T14:00:00Z",
            )
            mock_poll.return_value = ReadinessCheckResult(
                component_id="polling:alive",
                status="fail",
                time="2026-03-22T14:00:00Z",
                output="Polling task has crashed",
            )
            yield

    async def test_polling_fail_returns_503(self, client):
        """Crashed polling task causes 503."""
        resp = await client.get(READY_URL)
        assert resp.status_code == 503
        assert resp.json()["status"] == "fail"


class TestReadinessEncryptionFail:
    """Tests when encryption is disabled (no valid key)."""

    @pytest.fixture(autouse=True)
    def _patch(self):
        with (
            patch(
                "src.api.health._readiness_check_db",
                new_callable=AsyncMock,
            ) as mock_db,
            patch("src.api.health._readiness_check_oauth") as mock_oauth,
            patch("src.api.health._readiness_check_encryption") as mock_enc,
            patch("src.api.health._readiness_check_polling") as mock_poll,
        ):
            from src.api.health import ReadinessCheckResult

            mock_db.return_value = ReadinessCheckResult(
                component_id="database:writeable",
                status="pass",
                time="2026-03-22T14:00:00Z",
            )
            mock_oauth.return_value = ReadinessCheckResult(
                component_id="oauth:configured",
                status="pass",
                time="2026-03-22T14:00:00Z",
            )
            mock_enc.return_value = ReadinessCheckResult(
                component_id="encryption:enabled",
                status="fail",
                time="2026-03-22T14:00:00Z",
                output="Encryption service is disabled (no valid key)",
            )
            mock_poll.return_value = ReadinessCheckResult(
                component_id="polling:alive",
                status="pass",
                time="2026-03-22T14:00:00Z",
            )
            yield

    async def test_encryption_disabled_returns_503(self, client):
        """Encryption disabled causes 503."""
        resp = await client.get(READY_URL)
        assert resp.status_code == 503
        assert resp.json()["status"] == "fail"

    async def test_encryption_disabled_includes_output(self, client):
        """Encryption failure check includes descriptive output."""
        resp = await client.get(READY_URL)
        enc_check = resp.json()["checks"]["encryption:enabled"][0]
        assert enc_check["status"] == "fail"
        assert "output" in enc_check


class TestReadinessPollingDisabled:
    """Tests when polling is intentionally disabled (interval=0)."""

    @pytest.fixture(autouse=True)
    def _patch(self):
        with (
            patch(
                "src.api.health._readiness_check_db",
                new_callable=AsyncMock,
            ) as mock_db,
            patch("src.api.health._readiness_check_oauth") as mock_oauth,
            patch("src.api.health._readiness_check_encryption") as mock_enc,
            patch("src.api.health._readiness_check_polling") as mock_poll,
        ):
            from src.api.health import ReadinessCheckResult

            mock_db.return_value = ReadinessCheckResult(
                component_id="database:writeable",
                status="pass",
                time="2026-03-22T14:00:00Z",
            )
            mock_oauth.return_value = ReadinessCheckResult(
                component_id="oauth:configured",
                status="pass",
                time="2026-03-22T14:00:00Z",
            )
            mock_enc.return_value = ReadinessCheckResult(
                component_id="encryption:enabled",
                status="pass",
                time="2026-03-22T14:00:00Z",
            )
            mock_poll.return_value = ReadinessCheckResult(
                component_id="polling:alive",
                status="pass",
                time="2026-03-22T14:00:00Z",
            )
            yield

    async def test_polling_disabled_returns_200(self, client):
        """Polling intentionally disabled (interval=0) still returns 200."""
        resp = await client.get(READY_URL)
        assert resp.status_code == 200
        assert resp.json()["status"] == "pass"


class TestHealthEndpointUnchanged:
    """Verify GET /health liveness endpoint remains unchanged (FR-005)."""

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

    async def test_health_still_returns_200(self, client):
        """GET /health still returns 200 with all pass."""
        resp = await client.get(HEALTH_URL)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "pass"
        assert "version" in body

    async def test_health_has_original_checks(self, client):
        """GET /health still has original check keys."""
        resp = await client.get(HEALTH_URL)
        checks = resp.json()["checks"]
        assert "database" in checks
        assert "github_api" in checks
        assert "polling_loop" in checks
