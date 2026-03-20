"""Verification tests for CSRF middleware."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from src.middleware.csrf import CSRFMiddleware


@pytest.fixture()
def csrf_app(monkeypatch):
    """Minimal Starlette app with CSRF middleware for testing.

    Temporarily unsets ``TESTING`` so the middleware is active.
    """
    monkeypatch.delenv("TESTING", raising=False)

    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Route

    async def _post_endpoint(request: Request) -> JSONResponse:
        return JSONResponse({"ok": True})

    async def _get_endpoint(request: Request) -> JSONResponse:
        return JSONResponse({"ok": True})

    app = Starlette(
        routes=[
            Route("/test", _post_endpoint, methods=["POST"]),
            Route("/test", _get_endpoint, methods=["GET"]),
            Route("/api/v1/webhooks/github", _post_endpoint, methods=["POST"]),
        ],
    )
    app.add_middleware(CSRFMiddleware)
    return app


class TestCSRFProtection:
    """CSRF double-submit cookie validation."""

    def test_post_without_token_returns_403(self, csrf_app) -> None:
        client = TestClient(csrf_app)
        resp = client.post("/test")
        assert resp.status_code == 403
        assert "CSRF" in resp.json()["detail"]

    def test_post_with_valid_token_succeeds(self, csrf_app) -> None:
        client = TestClient(csrf_app)
        # First GET to obtain the csrf_token cookie.
        get_resp = client.get("/test")
        assert get_resp.status_code == 200
        token = get_resp.cookies.get("csrf_token")
        assert token, "csrf_token cookie should be set"

        # POST with matching header.
        client.cookies.set("csrf_token", token)
        post_resp = client.post("/test", headers={"X-CSRF-Token": token})
        assert post_resp.status_code == 200

    def test_post_with_wrong_token_returns_403(self, csrf_app) -> None:
        client = TestClient(csrf_app)
        get_resp = client.get("/test")
        token = get_resp.cookies.get("csrf_token")
        assert token

        client.cookies.set("csrf_token", token)
        post_resp = client.post("/test", headers={"X-CSRF-Token": "wrong-token"})
        assert post_resp.status_code == 403

    def test_webhook_exempt_from_csrf(self, csrf_app) -> None:
        client = TestClient(csrf_app)
        resp = client.post("/api/v1/webhooks/github")
        assert resp.status_code == 200

    def test_get_request_exempt(self, csrf_app) -> None:
        client = TestClient(csrf_app)
        resp = client.get("/test")
        assert resp.status_code == 200
