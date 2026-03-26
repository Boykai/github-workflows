"""Additional request ID middleware coverage for error and empty-header paths."""

import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from src.middleware.request_id import RequestIDMiddleware, request_id_var


@pytest.fixture
def client_factory():
    def _build(handler, *, raise_server_exceptions: bool = True) -> TestClient:
        app = Starlette(routes=[Route("/test", handler)])
        app.add_middleware(RequestIDMiddleware)
        return TestClient(app, raise_server_exceptions=raise_server_exceptions)

    return _build


class TestRequestIDMiddlewareEdgeCases:
    def test_empty_header_falls_back_to_generated_request_id(self, client_factory):
        async def handler(_request):
            return PlainTextResponse(request_id_var.get())

        with client_factory(handler) as client:
            response = client.get("/test", headers={"X-Request-ID": ""})

        assert response.status_code == 200
        assert response.text == response.headers["X-Request-ID"]
        assert len(response.headers["X-Request-ID"]) == 32

    def test_contextvar_resets_when_handler_raises(self, client_factory):
        seen_request_ids: list[str] = []

        async def handler(_request):
            seen_request_ids.append(request_id_var.get())
            raise RuntimeError("boom")

        with client_factory(handler, raise_server_exceptions=False) as client:
            response = client.get("/test", headers={"X-Request-ID": "fixed-request-id"})

        assert response.status_code == 500
        assert seen_request_ids == ["fixed-request-id"]
        assert request_id_var.get() == ""

    def test_rejects_header_with_crlf_injection(self, client_factory):
        """Regression: malicious X-Request-ID with CRLF chars must be replaced."""

        async def handler(_request):
            return PlainTextResponse(request_id_var.get())

        with client_factory(handler) as client:
            response = client.get(
                "/test",
                headers={"X-Request-ID": "evil\r\nSet-Cookie: admin=true"},
            )

        rid = response.headers["X-Request-ID"]
        assert "\r" not in rid
        assert "\n" not in rid
        assert len(rid) == 32  # falls back to uuid4().hex

    def test_rejects_header_with_spaces(self, client_factory):
        """Regression: X-Request-ID with spaces must be replaced."""

        async def handler(_request):
            return PlainTextResponse(request_id_var.get())

        with client_factory(handler) as client:
            response = client.get(
                "/test",
                headers={"X-Request-ID": "has spaces inside"},
            )

        rid = response.headers["X-Request-ID"]
        assert " " not in rid
        assert len(rid) == 32

    def test_accepts_valid_custom_request_id(self, client_factory):
        """Valid alphanumeric IDs with hyphens/underscores/dots are propagated."""

        async def handler(_request):
            return PlainTextResponse(request_id_var.get())

        with client_factory(handler) as client:
            response = client.get(
                "/test",
                headers={"X-Request-ID": "req-abc_123.456"},
            )

        assert response.headers["X-Request-ID"] == "req-abc_123.456"
        assert response.text == "req-abc_123.456"

    def test_rejects_oversized_request_id(self, client_factory):
        """Regression: extremely long X-Request-ID values must be replaced."""

        async def handler(_request):
            return PlainTextResponse(request_id_var.get())

        with client_factory(handler) as client:
            response = client.get(
                "/test",
                headers={"X-Request-ID": "a" * 200},
            )

        rid = response.headers["X-Request-ID"]
        assert len(rid) == 32  # falls back to uuid4().hex
