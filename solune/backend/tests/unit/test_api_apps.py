"""Tests for apps API routes (src/api/apps.py).

Covers:
- GET    /api/v1/apps                → list_apps_endpoint
- POST   /api/v1/apps                → create_app_endpoint
- GET    /api/v1/apps/{app_name}     → get_app_endpoint
- PUT    /api/v1/apps/{app_name}     → update_app_endpoint
- DELETE /api/v1/apps/{app_name}     → delete_app_endpoint
- POST   /api/v1/apps/{name}/start   → start_app_endpoint
- POST   /api/v1/apps/{name}/stop    → stop_app_endpoint
- GET    /api/v1/apps/{name}/status  → get_app_status_endpoint
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.models.app import App, AppStatus, AppStatusResponse

# ── Helpers ─────────────────────────────────────────────────────────────────


def _sample_app(**overrides) -> App:
    defaults = {
        "name": "my-app",
        "display_name": "My App",
        "description": "A test app",
        "directory_path": "apps/my-app",
        "status": AppStatus.ACTIVE,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }
    defaults.update(overrides)
    return App(**defaults)


def _sample_status_response(**overrides) -> AppStatusResponse:
    defaults = {
        "name": "my-app",
        "status": AppStatus.ACTIVE,
    }
    defaults.update(overrides)
    return AppStatusResponse(**defaults)


# ── GET /apps ───────────────────────────────────────────────────────────────


class TestListApps:
    @pytest.fixture(autouse=True)
    def _patch_service(self):
        with patch("src.api.apps.list_apps", new_callable=AsyncMock) as mock:
            self.mock_list = mock
            yield

    async def test_list_apps_empty(self, client):
        self.mock_list.return_value = []
        resp = await client.get("/api/v1/apps")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_apps_returns_items(self, client):
        app = _sample_app()
        self.mock_list.return_value = [app]
        resp = await client.get("/api/v1/apps")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "my-app"

    async def test_list_apps_with_status_filter(self, client):
        self.mock_list.return_value = []
        resp = await client.get("/api/v1/apps", params={"status": "stopped"})
        assert resp.status_code == 200
        call_kwargs = self.mock_list.call_args
        assert call_kwargs[1]["status_filter"] == AppStatus.STOPPED


# ── POST /apps ──────────────────────────────────────────────────────────────


class TestCreateApp:
    @pytest.fixture(autouse=True)
    def _patch_service(self):
        with patch("src.api.apps.create_app", new_callable=AsyncMock) as mock:
            self.mock_create = mock
            yield

    async def test_create_app_success(self, client):
        self.mock_create.return_value = _sample_app(status=AppStatus.CREATING)
        resp = await client.post(
            "/api/v1/apps",
            json={
                "name": "my-app",
                "display_name": "My App",
                "branch": "main",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "my-app"

    async def test_create_app_missing_required_fields(self, client):
        resp = await client.post("/api/v1/apps", json={})
        assert resp.status_code == 422

    async def test_create_app_invalid_name(self, client):
        resp = await client.post(
            "/api/v1/apps",
            json={"name": "X", "display_name": "App", "branch": "main"},
        )
        assert resp.status_code == 422


# ── GET /apps/{app_name} ───────────────────────────────────────────────────


class TestGetApp:
    @pytest.fixture(autouse=True)
    def _patch_service(self):
        with patch("src.api.apps.get_app", new_callable=AsyncMock) as mock:
            self.mock_get = mock
            yield

    async def test_get_app_success(self, client):
        self.mock_get.return_value = _sample_app()
        resp = await client.get("/api/v1/apps/my-app")
        assert resp.status_code == 200
        assert resp.json()["name"] == "my-app"

    async def test_get_app_not_found(self, client):
        from src.exceptions import NotFoundError

        self.mock_get.side_effect = NotFoundError("App not found")
        resp = await client.get("/api/v1/apps/nonexistent")
        assert resp.status_code == 404


# ── PUT /apps/{app_name} ──────────────────────────────────────────────────


class TestUpdateApp:
    @pytest.fixture(autouse=True)
    def _patch_service(self):
        with patch("src.api.apps.update_app", new_callable=AsyncMock) as mock:
            self.mock_update = mock
            yield

    async def test_update_app_success(self, client):
        self.mock_update.return_value = _sample_app(display_name="Updated")
        resp = await client.put(
            "/api/v1/apps/my-app",
            json={"display_name": "Updated"},
        )
        assert resp.status_code == 200
        assert resp.json()["display_name"] == "Updated"


# ── DELETE /apps/{app_name} ────────────────────────────────────────────────


class TestDeleteApp:
    @pytest.fixture(autouse=True)
    def _patch_service(self):
        with patch("src.api.apps.delete_app", new_callable=AsyncMock) as mock:
            self.mock_delete = mock
            yield

    async def test_delete_app_success(self, client):
        self.mock_delete.return_value = None
        resp = await client.delete("/api/v1/apps/my-app")
        assert resp.status_code == 200

    async def test_delete_running_app_fails(self, client):
        from src.exceptions import AppException

        self.mock_delete.side_effect = AppException("App must be stopped first", status_code=409)
        resp = await client.delete("/api/v1/apps/running-app")
        assert resp.status_code == 409


# ── POST /apps/{name}/start ───────────────────────────────────────────────


class TestStartApp:
    @pytest.fixture(autouse=True)
    def _patch_service(self):
        with patch("src.api.apps.start_app", new_callable=AsyncMock) as mock:
            self.mock_start = mock
            yield

    async def test_start_app_success(self, client):
        self.mock_start.return_value = _sample_status_response(status=AppStatus.ACTIVE)
        resp = await client.post("/api/v1/apps/my-app/start")
        assert resp.status_code == 200
        assert resp.json()["status"] == "active"


# ── POST /apps/{name}/stop ────────────────────────────────────────────────


class TestStopApp:
    @pytest.fixture(autouse=True)
    def _patch_service(self):
        with patch("src.api.apps.stop_app", new_callable=AsyncMock) as mock:
            self.mock_stop = mock
            yield

    async def test_stop_app_success(self, client):
        self.mock_stop.return_value = _sample_status_response(status=AppStatus.STOPPED)
        resp = await client.post("/api/v1/apps/my-app/stop")
        assert resp.status_code == 200
        assert resp.json()["status"] == "stopped"


# ── GET /apps/{name}/status ───────────────────────────────────────────────


class TestGetAppStatus:
    @pytest.fixture(autouse=True)
    def _patch_service(self):
        with patch("src.api.apps.get_app_status", new_callable=AsyncMock) as mock:
            self.mock_status = mock
            yield

    async def test_get_status_success(self, client):
        self.mock_status.return_value = _sample_status_response()
        resp = await client.get("/api/v1/apps/my-app/status")
        assert resp.status_code == 200
        assert resp.json()["name"] == "my-app"

    async def test_get_status_not_found(self, client):
        from src.exceptions import NotFoundError

        self.mock_status.side_effect = NotFoundError("App not found")
        resp = await client.get("/api/v1/apps/missing/status")
        assert resp.status_code == 404
