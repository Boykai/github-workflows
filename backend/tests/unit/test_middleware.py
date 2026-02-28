"""Tests for request ID middleware (src/middleware/request_id.py)."""

import pytest
from starlette.requests import Request
from starlette.testclient import TestClient

from src.middleware.request_id import RequestIDMiddleware, request_id_var


class TestRequestIDVar:
    def test_default_value_is_empty_string(self):
        assert request_id_var.get() == ""


class TestRequestIDMiddleware:
    @pytest.fixture
    def app(self):
        """Create a minimal Starlette app with the middleware."""
        from starlette.applications import Starlette
        from starlette.responses import JSONResponse
        from starlette.routing import Route

        async def read_request_id(request: Request) -> JSONResponse:
            return JSONResponse({"request_id": request_id_var.get()})

        app = Starlette(routes=[Route("/test", read_request_id)])
        app.add_middleware(RequestIDMiddleware)
        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_generates_request_id_when_missing(self, client):
        resp = client.get("/test")
        assert resp.status_code == 200
        rid = resp.headers.get("X-Request-ID")
        assert rid is not None
        assert len(rid) == 32  # uuid4().hex

    def test_propagates_existing_request_id(self, client):
        custom_id = "my-custom-request-id-123"
        resp = client.get("/test", headers={"X-Request-ID": custom_id})
        assert resp.status_code == 200
        assert resp.headers["X-Request-ID"] == custom_id
        assert resp.json()["request_id"] == custom_id

    def test_request_id_available_in_handler(self, client):
        resp = client.get("/test")
        body = resp.json()
        assert body["request_id"] == resp.headers["X-Request-ID"]

    def test_request_id_reset_after_request(self, client):
        client.get("/test")
        # After request completes, contextvar should be reset
        assert request_id_var.get() == ""

    def test_different_requests_get_different_ids(self, client):
        resp1 = client.get("/test")
        resp2 = client.get("/test")
        id1 = resp1.headers["X-Request-ID"]
        id2 = resp2.headers["X-Request-ID"]
        assert id1 != id2
