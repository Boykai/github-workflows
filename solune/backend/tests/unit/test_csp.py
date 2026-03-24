"""Tests for content security policy middleware."""

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from src.middleware.csp import CSPMiddleware


async def _ok(_request):
    return JSONResponse({"ok": True})


def _make_client(*, policy: str | None = None) -> TestClient:
    app = Starlette(routes=[Route("/test", _ok)])
    app.add_middleware(CSPMiddleware, policy=policy)
    return TestClient(app)


class TestCSPMiddleware:
    def test_adds_default_csp_header(self):
        client = _make_client()

        response = client.get("/test")

        assert response.status_code == 200
        assert response.headers["Content-Security-Policy"] == CSPMiddleware.default_policy()

    def test_respects_custom_policy_override(self):
        client = _make_client(policy="default-src 'none'; img-src https:")

        response = client.get("/test")

        assert response.headers["Content-Security-Policy"] == "default-src 'none'; img-src https:"

    def test_default_policy_contains_expected_hardening_directives(self):
        policy = CSPMiddleware.default_policy()

        assert "frame-ancestors 'none'" in policy
        assert "base-uri 'self'" in policy
        assert "form-action 'self'" in policy
        assert "connect-src 'self' wss:" in policy

    def test_adds_strict_transport_security_header(self):
        """Responses must include the HSTS header for HTTPS enforcement."""
        client = _make_client()
        response = client.get("/test")

        assert response.status_code == 200
        assert "Strict-Transport-Security" in response.headers
        assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
