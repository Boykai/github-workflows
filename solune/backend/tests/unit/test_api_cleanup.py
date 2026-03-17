"""Tests for cleanup API routes (src/api/cleanup.py).

Covers:
- POST /api/v1/cleanup/preflight  → cleanup_preflight
- POST /api/v1/cleanup/execute    → cleanup_execute
- GET  /api/v1/cleanup/history    → cleanup_history
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.models.cleanup import (
    CleanupExecuteResponse,
    CleanupHistoryResponse,
    CleanupPreflightResponse,
)

# ── Helpers ─────────────────────────────────────────────────────────────────


def _preflight_response(**overrides) -> CleanupPreflightResponse:
    defaults = {
        "branches_to_delete": [],
        "branches_to_preserve": [],
        "prs_to_close": [],
        "prs_to_preserve": [],
        "orphaned_issues": [],
        "open_issues_on_board": 0,
        "has_permission": True,
    }
    defaults.update(overrides)
    return CleanupPreflightResponse(**defaults)


def _execute_response(**overrides) -> CleanupExecuteResponse:
    defaults = {
        "operation_id": "op-123",
        "branches_deleted": 1,
        "branches_preserved": 0,
        "prs_closed": 0,
        "prs_preserved": 0,
        "issues_deleted": 0,
        "errors": [],
        "results": [],
    }
    defaults.update(overrides)
    return CleanupExecuteResponse(**defaults)


_PREFLIGHT_BODY = {
    "owner": "testowner",
    "repo": "testrepo",
    "project_id": "PVT_123",
}

_EXECUTE_BODY = {
    "owner": "testowner",
    "repo": "testrepo",
    "project_id": "PVT_123",
    "branches_to_delete": ["feature-old"],
    "prs_to_close": [],
    "issues_to_delete": [],
}


# ── POST /cleanup/preflight ───────────────────────────────────────────────


class TestCleanupPreflight:
    @pytest.fixture(autouse=True)
    def _patch_service(self):
        with patch("src.api.cleanup.cleanup_service.preflight", new_callable=AsyncMock) as mock:
            self.mock_preflight = mock
            yield

    async def test_preflight_success(self, client):
        self.mock_preflight.return_value = _preflight_response()
        resp = await client.post("/api/v1/cleanup/preflight", json=_PREFLIGHT_BODY)
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_permission"] is True

    async def test_preflight_missing_fields(self, client):
        resp = await client.post("/api/v1/cleanup/preflight", json={})
        assert resp.status_code == 422

    async def test_preflight_service_error(self, client):
        from src.exceptions import GitHubAPIError

        self.mock_preflight.side_effect = GitHubAPIError("API failed")
        resp = await client.post("/api/v1/cleanup/preflight", json=_PREFLIGHT_BODY)
        assert resp.status_code == 502


# ── POST /cleanup/execute ─────────────────────────────────────────────────


class TestCleanupExecute:
    @pytest.fixture(autouse=True)
    def _patch_service(self):
        with patch(
            "src.api.cleanup.cleanup_service.execute_cleanup", new_callable=AsyncMock
        ) as mock:
            self.mock_execute = mock
            yield

    async def test_execute_success(self, client):
        self.mock_execute.return_value = _execute_response()
        resp = await client.post("/api/v1/cleanup/execute", json=_EXECUTE_BODY)
        assert resp.status_code == 200
        assert resp.json()["branches_deleted"] == 1

    async def test_execute_missing_fields(self, client):
        resp = await client.post("/api/v1/cleanup/execute", json={})
        assert resp.status_code == 422

    async def test_execute_service_error(self, client):
        from src.exceptions import GitHubAPIError

        self.mock_execute.side_effect = GitHubAPIError("API failed")
        resp = await client.post("/api/v1/cleanup/execute", json=_EXECUTE_BODY)
        assert resp.status_code == 502


# ── GET /cleanup/history ──────────────────────────────────────────────────


class TestCleanupHistory:
    @pytest.fixture(autouse=True)
    def _patch_service(self):
        with patch(
            "src.api.cleanup.cleanup_service.get_cleanup_history",
            new_callable=AsyncMock,
        ) as mock:
            self.mock_history = mock
            yield

    async def test_history_success(self, client):
        self.mock_history.return_value = CleanupHistoryResponse(operations=[], count=0)
        resp = await client.get(
            "/api/v1/cleanup/history",
            params={"owner": "testowner", "repo": "testrepo"},
        )
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    async def test_history_missing_params(self, client):
        resp = await client.get("/api/v1/cleanup/history")
        assert resp.status_code == 422

    async def test_history_custom_limit(self, client):
        self.mock_history.return_value = CleanupHistoryResponse(operations=[], count=0)
        resp = await client.get(
            "/api/v1/cleanup/history",
            params={"owner": "o", "repo": "r", "limit": 5},
        )
        assert resp.status_code == 200
        call_args = self.mock_history.call_args
        assert call_args[0][4] == 5  # limit positional arg
