"""Tests for admin guard middleware path enforcement."""

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from src.models.guard import GuardResult


async def _ok(_request):
    return JSONResponse({"ok": True})


def _make_client() -> TestClient:
    from src.middleware.admin_guard import AdminGuardMiddleware

    app = Starlette(routes=[Route("/test", _ok)])
    app.add_middleware(AdminGuardMiddleware)
    return TestClient(app)


class TestAdminGuardMiddleware:
    def test_requests_without_target_paths_pass_through(self):
        client = _make_client()

        response = client.get("/test")

        assert response.status_code == 200
        assert response.json() == {"ok": True}

    def test_locked_paths_return_403(self, monkeypatch):
        monkeypatch.setattr(
            "src.middleware.admin_guard.check_guard",
            lambda _paths, elevated=False: GuardResult(locked=[".github/workflows/ci.yml"]),
        )
        client = _make_client()

        response = client.get("/test", headers={"X-Target-Paths": ".github/workflows/ci.yml"})

        assert response.status_code == 403
        assert "@adminlock" in response.text
        assert ".github/workflows/ci.yml" in response.text

    def test_admin_paths_require_elevation(self, monkeypatch):
        monkeypatch.setattr(
            "src.middleware.admin_guard.check_guard",
            lambda _paths, elevated=False: GuardResult(
                admin_blocked=["solune/backend/src/main.py"]
            ),
        )
        client = _make_client()

        response = client.get("/test", headers={"X-Target-Paths": "solune/backend/src/main.py"})

        assert response.status_code == 403
        assert "@admin" in response.text
        assert "X-Guard-Elevated: true" in response.text

    def test_trims_target_paths_and_passes_elevation_to_guard(self, monkeypatch):
        captured: dict[str, object] = {}

        def fake_check_guard(paths, elevated=False):
            captured["paths"] = paths
            captured["elevated"] = elevated
            return GuardResult(allowed=paths)

        monkeypatch.setattr("src.middleware.admin_guard.check_guard", fake_check_guard)
        client = _make_client()

        response = client.get(
            "/test",
            headers={
                "X-Target-Paths": " solune/backend/src/main.py , apps/test-app/README.md ",
                "X-Guard-Elevated": "true",
            },
        )

        assert response.status_code == 200
        assert captured == {
            "paths": ["solune/backend/src/main.py", "apps/test-app/README.md"],
            "elevated": True,
        }

    def test_empty_target_paths_after_trimming_pass_through(self):
        client = _make_client()

        response = client.get("/test", headers={"X-Target-Paths": " ,  , "})

        assert response.status_code == 200
        assert response.json() == {"ok": True}
