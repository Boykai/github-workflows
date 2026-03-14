"""Unit tests for app management API routes."""

from __future__ import annotations

import pytest


@pytest.fixture
async def apps_client(client, mock_db, monkeypatch, tmp_path):
    """Client fixture with the apps router bound to the test database."""
    import src.api.apps as apps_api
    from src.services import app_service

    apps_dir = tmp_path / "apps"
    apps_dir.mkdir()
    monkeypatch.setattr(apps_api, "get_db", lambda: mock_db)
    monkeypatch.setattr(app_service, "_APPS_DIR", apps_dir)
    monkeypatch.setattr(app_service, "_APPS_DIR_RESOLVED", apps_dir.resolve())
    return client


class TestAppsApi:
    async def test_create_list_and_filter_apps(self, apps_client):
        create_resp = await apps_client.post(
            "/api/v1/apps",
            json={
                "name": "demo-app",
                "display_name": "Demo App",
                "description": "Created through the API",
            },
        )
        assert create_resp.status_code == 201
        created = create_resp.json()
        assert created["name"] == "demo-app"
        assert created["status"] == "active"

        stop_resp = await apps_client.post("/api/v1/apps/demo-app/stop")
        assert stop_resp.status_code == 200
        assert stop_resp.json()["status"] == "stopped"

        filtered = await apps_client.get("/api/v1/apps", params={"status": "stopped"})
        assert filtered.status_code == 200
        assert [item["name"] for item in filtered.json()] == ["demo-app"]

    async def test_active_app_cannot_be_deleted_until_stopped(self, apps_client):
        create_resp = await apps_client.post(
            "/api/v1/apps",
            json={
                "name": "demo-app",
                "display_name": "Demo App",
                "description": "Created through the API",
            },
        )
        assert create_resp.status_code == 201

        delete_resp = await apps_client.delete("/api/v1/apps/demo-app")
        assert delete_resp.status_code == 422
        assert "must stop the app first" in delete_resp.json()["error"]

        stop_resp = await apps_client.post("/api/v1/apps/demo-app/stop")
        assert stop_resp.status_code == 200

        delete_resp = await apps_client.delete("/api/v1/apps/demo-app")
        assert delete_resp.status_code == 204

        get_resp = await apps_client.get("/api/v1/apps/demo-app")
        assert get_resp.status_code == 404

    async def test_invalid_name_is_rejected(self, apps_client):
        resp = await apps_client.post(
            "/api/v1/apps",
            json={
                "name": "invalid@chars",
                "display_name": "Demo App",
                "description": "Created through the API",
            },
        )

        assert resp.status_code == 422
