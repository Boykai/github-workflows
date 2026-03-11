"""Tests for production startup validation in config.py.

Covers:
- Encryption key enforcement in production mode (Finding #2)
- GitHub webhook secret enforcement in production mode (Finding #2)
- Session secret key minimum entropy check (Finding #9)
- Cookie secure flag enforcement in production mode (Finding #12)
- CORS origins validation (Finding #16)
"""

import pytest

from src.config import Settings

# ── Helpers ──────────────────────────────────────────────────────────────────

# Common base settings that satisfy all required fields.
_BASE = {
    "github_client_id": "cid",
    "github_client_secret": "csecret",
    "session_secret_key": "a" * 64,  # Meets minimum length
    "encryption_key": "dGVzdC1lbmNyeXB0aW9uLWtleS0xMjM0NTY3ODkwYWI=",
    "github_webhook_secret": "whsec_test_123",
    "cookie_secure": True,
    "frontend_url": "https://app.example.com",
}


def _settings(**overrides) -> Settings:
    """Create a Settings instance with production defaults and *overrides*."""
    env = {**_BASE, **overrides}
    return Settings(**env)  # type: ignore[arg-type]


# ── Encryption key enforcement (Finding #2) ──────────────────────────────────


class TestEncryptionKeyEnforcement:
    def test_production_rejects_missing_encryption_key(self):
        with pytest.raises(ValueError, match="ENCRYPTION_KEY is required"):
            _settings(debug=False, encryption_key=None)

    def test_production_accepts_valid_encryption_key(self):
        s = _settings(debug=False)
        assert s.encryption_key is not None

    def test_debug_allows_missing_encryption_key(self):
        s = _settings(debug=True, encryption_key=None)
        assert s.encryption_key is None


# ── Webhook secret enforcement (Finding #2) ──────────────────────────────────


class TestWebhookSecretEnforcement:
    def test_production_rejects_missing_webhook_secret(self):
        with pytest.raises(ValueError, match="GITHUB_WEBHOOK_SECRET is required"):
            _settings(debug=False, github_webhook_secret=None)

    def test_production_accepts_valid_webhook_secret(self):
        s = _settings(debug=False)
        assert s.github_webhook_secret is not None

    def test_debug_allows_missing_webhook_secret(self):
        s = _settings(debug=True, github_webhook_secret=None)
        assert s.github_webhook_secret is None


# ── Session secret minimum entropy (Finding #9) ──────────────────────────────


class TestSessionSecretEntropy:
    def test_production_rejects_short_session_secret(self):
        with pytest.raises(ValueError, match="SESSION_SECRET_KEY must be at least 64"):
            _settings(debug=False, session_secret_key="short")

    def test_production_accepts_64_char_session_secret(self):
        s = _settings(debug=False, session_secret_key="x" * 64)
        assert len(s.session_secret_key) == 64

    def test_debug_allows_short_session_secret(self):
        s = _settings(debug=True, session_secret_key="short")
        assert s.session_secret_key == "short"


# ── Cookie secure flag enforcement (Finding #12) ─────────────────────────────


class TestCookieSecureEnforcement:
    def test_production_rejects_insecure_cookies(self):
        with pytest.raises(ValueError, match="Secure flag"):
            _settings(
                debug=False,
                cookie_secure=False,
                frontend_url="http://localhost:5173",
            )

    def test_production_accepts_explicit_cookie_secure(self):
        s = _settings(debug=False, cookie_secure=True)
        assert s.effective_cookie_secure is True

    def test_production_accepts_https_auto_detection(self):
        s = _settings(
            debug=False,
            cookie_secure=False,
            frontend_url="https://app.example.com",
        )
        assert s.effective_cookie_secure is True


# ── CORS origins validation (Finding #16) ────────────────────────────────────


class TestCorsOriginsValidation:
    def test_valid_origins(self):
        s = _settings(cors_origins="http://localhost:5173,https://app.example.com")
        assert s.cors_origins_list == [
            "http://localhost:5173",
            "https://app.example.com",
        ]

    def test_rejects_malformed_origin_no_scheme(self):
        s = _settings(cors_origins="localhost:5173")
        with pytest.raises(ValueError, match="Malformed CORS origin"):
            _ = s.cors_origins_list

    def test_rejects_malformed_origin_no_hostname(self):
        s = _settings(cors_origins="http://")
        with pytest.raises(ValueError, match="Malformed CORS origin"):
            _ = s.cors_origins_list

    def test_empty_origin_skipped(self):
        s = _settings(cors_origins="http://a.com,,http://b.com")
        assert s.cors_origins_list == ["http://a.com", "http://b.com"]

    def test_invalid_scheme_rejected(self):
        s = _settings(cors_origins="ftp://files.example.com")
        with pytest.raises(ValueError, match="Malformed CORS origin"):
            _ = s.cors_origins_list
