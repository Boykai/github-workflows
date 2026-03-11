"""Tests for webhook security (Findings #5, #13).

Covers:
- Signal webhook uses constant-time comparison (Finding #5)
- GitHub webhook signature verification is mandatory (Finding #13)
- No debug-mode bypass for webhook verification
"""

import hmac

from src.api.webhooks import verify_webhook_signature

# ── GitHub webhook signature verification ────────────────────────────────────


class TestVerifyWebhookSignature:
    def test_valid_signature_accepted(self):
        secret = "test-secret"
        payload = b'{"action": "opened"}'
        expected_sig = "sha256=" + hmac.new(
            secret.encode(), payload, "sha256"
        ).hexdigest()
        assert verify_webhook_signature(payload, expected_sig, secret) is True

    def test_invalid_signature_rejected(self):
        secret = "test-secret"
        payload = b'{"action": "opened"}'
        assert verify_webhook_signature(payload, "sha256=bad", secret) is False

    def test_missing_signature_rejected(self):
        assert verify_webhook_signature(b"payload", None, "secret") is False

    def test_wrong_prefix_rejected(self):
        assert verify_webhook_signature(b"payload", "sha1=abc", "secret") is False


# ── Webhook endpoint: no debug bypass (Finding #13) ─────────────────────────


class TestWebhookEndpointSecurity:
    """Verify the webhook endpoint always requires a valid secret."""

    async def test_rejects_when_no_secret_configured(self, client, mock_settings):
        """Even with no GITHUB_WEBHOOK_SECRET configured, webhook is rejected."""
        mock_settings.github_webhook_secret = None

        resp = await client.post(
            "/api/v1/webhooks/github",
            json={"action": "opened"},
            headers={
                "X-GitHub-Event": "push",
                "X-GitHub-Delivery": "delivery-123",
            },
        )
        assert resp.status_code in (401, 403)

    async def test_rejects_invalid_signature(self, client, mock_settings):
        """Invalid signature must be rejected."""
        mock_settings.github_webhook_secret = "real-secret"

        resp = await client.post(
            "/api/v1/webhooks/github",
            content=b'{"action": "opened"}',
            headers={
                "X-GitHub-Event": "push",
                "X-GitHub-Delivery": "delivery-456",
                "X-Hub-Signature-256": "sha256=invalid",
                "Content-Type": "application/json",
            },
        )
        assert resp.status_code in (401, 403)


# ── Signal webhook: constant-time comparison (Finding #5) ────────────────────


class TestSignalWebhookSecurity:
    """Verify Signal webhook uses hmac.compare_digest (constant-time)."""

    def test_hmac_compare_digest_used(self):
        """The signal.py endpoint should use hmac.compare_digest.

        This is a code-review check — verify that the compare_digest function
        is used in the signal module for secret comparison.
        """
        import inspect

        from src.api import signal as signal_mod

        source = inspect.getsource(signal_mod)
        assert "hmac.compare_digest" in source, (
            "Signal webhook must use hmac.compare_digest for constant-time comparison"
        )
