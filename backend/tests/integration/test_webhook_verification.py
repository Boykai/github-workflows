"""Tests for webhook signature verification (US6 — SC-009).

Verifies:
- Unsigned payloads rejected with 401 in production mode
- Signed payloads accepted
- Unsigned payloads allowed in debug mode with warning
"""

import hashlib
import hmac
import json
from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient

from src.config import Settings
from src.models.user import UserSession


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


class TestWebhookVerification:
    """Webhook signature verification must be enforced in production."""

    async def test_unsigned_payload_rejected_in_production(self):
        """POST /webhooks/github without signature → 401 when debug=False."""
        from src.api.auth import get_session_dep
        from src.main import create_app

        prod_settings = Settings(
            github_client_id="id",
            github_client_secret="secret",
            session_secret_key="a" * 64,
            encryption_key="sdGVj_fRew3oi2qQBVv9Rb3yE06w65yHzcdkARVd0es=",
            github_webhook_secret="required-in-prod",
            cookie_secure=True,
            debug=False,
            _env_file=None,
        )
        # Override the webhook secret to None for this specific test
        # (test that missing secret results in 401)
        import unittest.mock

        webhook_settings = unittest.mock.MagicMock(wraps=prod_settings)
        webhook_settings.github_webhook_secret = None

        app = create_app()
        session = _make_session()
        app.dependency_overrides[get_session_dep] = lambda: session
        with (
            patch("src.config.get_settings", return_value=prod_settings),
            patch("src.api.webhooks.get_settings", return_value=webhook_settings),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
                resp = await ac.post(
                    "/api/v1/webhooks/github",
                    json={"action": "opened"},
                    headers={
                        "X-GitHub-Event": "pull_request",
                        "X-GitHub-Delivery": "test-delivery-001",
                    },
                )

        assert resp.status_code == 401, (
            f"Expected 401 for unsigned webhook in production, got {resp.status_code}"
        )
        app.dependency_overrides.clear()

    async def test_unsigned_payload_rejected_in_debug(self):
        """POST /webhooks/github without signature → 401 even in debug mode.

        Webhook verification must never be bypassed, regardless of debug mode.
        """
        from src.api.auth import get_session_dep
        from src.main import create_app

        debug_settings = Settings(
            github_client_id="id",
            github_client_secret="secret",
            session_secret_key="key-key-key-key-key-key-key-key-key",
            debug=True,
            github_webhook_secret=None,
            _env_file=None,
        )
        app = create_app()
        session = _make_session()
        app.dependency_overrides[get_session_dep] = lambda: session
        mock_gh = AsyncMock(name="github_projects_service")
        with (
            patch("src.config.get_settings", return_value=debug_settings),
            patch("src.api.webhooks.get_settings", return_value=debug_settings),
            patch("src.api.webhooks.github_projects_service", mock_gh),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
                resp = await ac.post(
                    "/api/v1/webhooks/github",
                    json={"action": "opened"},
                    headers={
                        "X-GitHub-Event": "ping",
                        "X-GitHub-Delivery": "test-delivery-002",
                    },
                )

        # Webhook verification must never be bypassed, even in debug mode
        assert resp.status_code == 401, (
            f"Unsigned webhook should be rejected even in debug mode, got {resp.status_code}"
        )
        app.dependency_overrides.clear()

    async def test_valid_signature_accepted(self):
        """POST /webhooks/github with valid signature → 200."""
        from src.api.auth import get_session_dep
        from src.main import create_app

        webhook_secret = "test-webhook-secret"
        settings = Settings(
            github_client_id="id",
            github_client_secret="secret",
            session_secret_key="a" * 64,
            encryption_key="sdGVj_fRew3oi2qQBVv9Rb3yE06w65yHzcdkARVd0es=",
            github_webhook_secret=webhook_secret,
            cookie_secure=True,
            debug=False,
            _env_file=None,
        )

        payload = json.dumps({"action": "opened"}).encode()
        signature = _sign_payload(payload, webhook_secret)

        app = create_app()
        session = _make_session()
        app.dependency_overrides[get_session_dep] = lambda: session
        mock_gh = AsyncMock(name="github_projects_service")
        with (
            patch("src.config.get_settings", return_value=settings),
            patch("src.api.webhooks.get_settings", return_value=settings),
            patch("src.api.webhooks.github_projects_service", mock_gh),
        ):
            transport = ASGITransport(app=app)
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

        assert resp.status_code == 200, (
            f"Expected 200 for signed webhook, got {resp.status_code}: {resp.text}"
        )
        app.dependency_overrides.clear()
