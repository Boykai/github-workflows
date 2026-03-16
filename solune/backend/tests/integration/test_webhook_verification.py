"""Tests for webhook signature verification (US6 — SC-009).

Verifies:
- Unsigned payloads rejected with 401 (always, regardless of debug mode)
- Signed payloads accepted
"""

import hashlib
import hmac
import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient

from src.config import Settings
from src.exceptions import AppException
from src.models.user import UserSession

# Production-valid secrets for tests that need debug=False
_PROD_SECRETS = {
    "session_secret_key": "a" * 64,
    "encryption_key": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
    "cookie_secure": True,
}


def _make_session(**overrides) -> UserSession:
    defaults = {
        "github_user_id": "12345",
        "github_username": "testuser",
        "access_token": "test-token",
    }
    defaults.update(overrides)
    return UserSession(**defaults)


def _sign_payload(payload: bytes, secret: str) -> str:
    """Generate X-Hub-Signature-256 for a payload."""
    sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


def _build_webhook_app() -> FastAPI:
    from src.api.webhooks import router as webhooks_router

    app = FastAPI()

    @app.exception_handler(AppException)
    async def _app_exception_handler(_request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.message,
                "details": exc.details,
            },
        )

    app.include_router(webhooks_router, prefix="/api/v1/webhooks")
    return app


@pytest.mark.asyncio
class TestWebhookVerification:
    """Webhook signature verification must always be enforced."""

    async def test_unsigned_payload_rejected_without_secret(self):
        """POST /webhooks/github without signature → 401 when no secret configured."""
        # In debug mode with no secret, webhooks are now rejected (bypass removed)
        settings = Settings(
            github_client_id="id",
            github_client_secret="secret",
            session_secret_key="key-key-key-key-key-key-key-key-key",
            debug=True,
            github_webhook_secret=None,
            _env_file=None,
        )
        app = _build_webhook_app()
        with (
            patch("src.config.get_settings", return_value=settings),
            patch("src.api.webhooks.get_settings", return_value=settings),
        ):
            transport = ASGITransport(app=app)
            try:
                async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
                    resp = await ac.post(
                        "/api/v1/webhooks/github",
                        json={"action": "opened"},
                        headers={
                            "X-GitHub-Event": "pull_request",
                            "X-GitHub-Delivery": "test-delivery-001",
                        },
                    )
            finally:
                await transport.aclose()

        assert resp.status_code == 401, f"Expected 401 for unsigned webhook, got {resp.status_code}"

    async def test_valid_signature_accepted(self):
        """POST /webhooks/github with valid signature → 200."""
        webhook_secret = "test-webhook-secret"
        settings = Settings(
            github_client_id="id",
            github_client_secret="secret",
            debug=True,
            github_webhook_secret=webhook_secret,
            _env_file=None,
            **{k: v for k, v in _PROD_SECRETS.items() if k != "session_secret_key"},
            session_secret_key="key-key-key-key-key-key-key-key-key",
        )

        payload = json.dumps({"action": "opened"}).encode()
        signature = _sign_payload(payload, webhook_secret)

        app = _build_webhook_app()
        mock_gh = AsyncMock(name="github_projects_service")
        with (
            patch("src.config.get_settings", return_value=settings),
            patch("src.api.webhooks.get_settings", return_value=settings),
            patch("src.api.webhooks.github_projects_service", mock_gh),
        ):
            transport = ASGITransport(app=app)
            try:
                async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
                    resp = await ac.post(
                        "/api/v1/webhooks/github",
                        content=payload,
                        headers={
                            "Content-Type": "application/json",
                            "X-GitHub-Event": "ping",
                            "X-GitHub-Delivery": "test-delivery-003",
                            "X-Hub-Signature-256": signature,
                        },
                    )
            finally:
                await transport.aclose()

        assert resp.status_code == 200, (
            f"Expected 200 for signed webhook, got {resp.status_code}: {resp.text}"
        )
