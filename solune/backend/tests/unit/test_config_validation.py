"""Tests for security-related startup configuration validation (US2 - FR-004-FR-008).

T014:
- Missing ENCRYPTION_KEY fails startup in production mode
- Missing GITHUB_WEBHOOK_SECRET fails startup in production mode
- SESSION_SECRET_KEY shorter than 64 characters fails startup
- Cookie Secure flag enforced in production mode
- Malformed CORS origins fail startup
- Debug mode degrades gracefully with warnings
"""

import pytest

from src.config import Settings


def _make_production(**overrides) -> Settings:
    """Create a Settings instance in production (non-debug) mode."""
    defaults = {
        "github_client_id": "cid",
        "github_client_secret": "csecret",
        "session_secret_key": "a" * 64,
        "encryption_key": "ZmVybmV0LXRlc3Qta2V5LWZvci11bml0LXRlc3Rz",  # base64
        "github_webhook_secret": "whsec_test_1234567890",
        "cookie_secure": True,
        "admin_github_user_id": 12345,
        "debug": False,
        "_env_file": None,
    }
    defaults.update(overrides)
    return Settings(**defaults)


def _make_debug(**overrides) -> Settings:
    """Create a Settings instance in debug mode."""
    defaults = {
        "github_client_id": "cid",
        "github_client_secret": "csecret",
        "session_secret_key": "short",
        "debug": True,
        "_env_file": None,
    }
    defaults.update(overrides)
    return Settings(**defaults)


class TestProductionEncryptionKeyRequired:
    """ENCRYPTION_KEY must be set in production mode (FR-004)."""

    def test_missing_encryption_key_raises(self):
        with pytest.raises(ValueError, match="ENCRYPTION_KEY is required"):
            _make_production(encryption_key=None)

    def test_empty_encryption_key_raises(self):
        with pytest.raises(ValueError, match="ENCRYPTION_KEY is required"):
            _make_production(encryption_key="")

    def test_valid_encryption_key_passes(self):
        s = _make_production()
        assert s.encryption_key is not None


class TestProductionWebhookSecretRequired:
    """GITHUB_WEBHOOK_SECRET must be set in production mode (FR-005)."""

    def test_missing_webhook_secret_raises(self):
        with pytest.raises(ValueError, match="GITHUB_WEBHOOK_SECRET is required"):
            _make_production(github_webhook_secret=None)

    def test_empty_webhook_secret_raises(self):
        with pytest.raises(ValueError, match="GITHUB_WEBHOOK_SECRET is required"):
            _make_production(github_webhook_secret="")


class TestSessionSecretKeyMinLength:
    """SESSION_SECRET_KEY must be at least 64 characters (FR-006)."""

    def test_short_key_raises(self):
        with pytest.raises(ValueError, match="SESSION_SECRET_KEY must be at least 64"):
            _make_production(session_secret_key="too-short")

    def test_63_char_key_raises(self):
        with pytest.raises(ValueError, match="SESSION_SECRET_KEY must be at least 64"):
            _make_production(session_secret_key="a" * 63)

    def test_64_char_key_passes(self):
        s = _make_production(session_secret_key="a" * 64)
        assert len(s.session_secret_key) == 64

    def test_longer_key_passes(self):
        s = _make_production(session_secret_key="a" * 128)
        assert len(s.session_secret_key) == 128


class TestCookieSecureEnforced:
    """Cookies must use the Secure flag in production (FR-007)."""

    def test_insecure_cookies_raise(self):
        with pytest.raises(ValueError, match="Cookies must use the Secure flag"):
            _make_production(cookie_secure=False, frontend_url="http://localhost:5173")

    def test_auto_detect_https_passes(self):
        """HTTPS frontend_url auto-enables cookie secure flag."""
        s = _make_production(cookie_secure=False, frontend_url="https://app.example.com")
        assert s.effective_cookie_secure is True

    def test_explicit_cookie_secure_passes(self):
        s = _make_production(cookie_secure=True)
        assert s.effective_cookie_secure is True


class TestProductionAdminUserIdRequired:
    """ADMIN_GITHUB_USER_ID must be set in production mode."""

    def test_missing_admin_user_id_raises(self):
        with pytest.raises(ValueError, match="ADMIN_GITHUB_USER_ID is required"):
            _make_production(admin_github_user_id=None)

    def test_zero_admin_user_id_raises(self):
        with pytest.raises(ValueError, match="ADMIN_GITHUB_USER_ID is required"):
            _make_production(admin_github_user_id=0)

    def test_negative_admin_user_id_raises(self):
        with pytest.raises(ValueError, match="ADMIN_GITHUB_USER_ID is required"):
            _make_production(admin_github_user_id=-1)

    def test_valid_admin_user_id_passes(self):
        s = _make_production(admin_github_user_id=12345)
        assert s.admin_github_user_id == 12345


class TestCorsOriginsValidation:
    """CORS origins must be well-formed URLs with scheme and hostname (FR-008)."""

    def test_valid_single_origin(self):
        s = _make_debug(cors_origins="http://localhost:5173")
        assert s.cors_origins_list == ["http://localhost:5173"]

    def test_valid_multiple_origins(self):
        s = _make_debug(cors_origins="http://localhost:5173,https://app.example.com")
        assert s.cors_origins_list == ["http://localhost:5173", "https://app.example.com"]

    def test_malformed_origin_no_scheme_raises(self):
        s = _make_debug(cors_origins="localhost:5173")
        with pytest.raises(ValueError, match="Malformed CORS origin"):
            _ = s.cors_origins_list

    def test_malformed_origin_no_hostname_raises(self):
        s = _make_debug(cors_origins="http://")
        with pytest.raises(ValueError, match="Malformed CORS origin"):
            _ = s.cors_origins_list

    def test_empty_origin_ignored(self):
        s = _make_debug(cors_origins="http://localhost:5173,,")
        assert s.cors_origins_list == ["http://localhost:5173"]


class TestDebugModeDegradedGracefully:
    """Debug mode should warn but not fail on missing secrets."""

    def test_missing_encryption_key_warns(self, caplog):
        s = _make_debug(encryption_key=None)
        assert s.debug is True
        assert "ENCRYPTION_KEY not set" in caplog.text

    def test_missing_webhook_secret_warns(self, caplog):
        s = _make_debug(github_webhook_secret=None)
        assert s.debug is True
        assert "GITHUB_WEBHOOK_SECRET not set" in caplog.text

    def test_short_session_key_warns(self, caplog):
        s = _make_debug(session_secret_key="short")
        assert s.debug is True
        assert "SESSION_SECRET_KEY is shorter than 64 characters" in caplog.text

    def test_missing_admin_user_id_warns(self, caplog):
        s = _make_debug(admin_github_user_id=None)
        assert s.debug is True
        assert "ADMIN_GITHUB_USER_ID not set" in caplog.text

    def test_negative_admin_user_id_warns_in_debug(self, caplog):
        s = _make_debug(admin_github_user_id=-1)
        assert s.debug is True
        assert "not a valid GitHub user ID" in caplog.text

    def test_all_valid_in_debug_no_errors(self):
        """Even with full production-grade config, debug mode shouldn't fail."""
        s = _make_debug(
            encryption_key="ZmVybmV0LXRlc3Qta2V5LWZvci11bml0LXRlc3Rz",
            github_webhook_secret="whsec_test",
            session_secret_key="a" * 64,
        )
        assert s.debug is True


# ── AI Provider Validation ──


class TestAIProviderValidation:
    """AI_PROVIDER must be a supported value."""

    def test_unsupported_provider_raises(self):
        with pytest.raises(ValueError, match="AI_PROVIDER must be one of"):
            _make_debug(ai_provider="openai_direct")

    def test_copilot_provider_passes(self):
        s = _make_debug(ai_provider="copilot")
        assert s.ai_provider == "copilot"

    def test_azure_openai_provider_passes_with_settings(self):
        s = _make_debug(
            ai_provider="azure_openai",
            azure_openai_endpoint="https://myoai.openai.azure.com",
            azure_openai_key="key123",
        )
        assert s.ai_provider == "azure_openai"

    def test_azure_openai_missing_endpoint_raises(self):
        with pytest.raises(ValueError, match="AZURE_OPENAI_ENDPOINT is required"):
            _make_debug(
                ai_provider="azure_openai",
                azure_openai_endpoint=None,
                azure_openai_key="key123",
            )

    def test_azure_openai_missing_key_raises(self):
        with pytest.raises(ValueError, match="AZURE_OPENAI_KEY is required"):
            _make_debug(
                ai_provider="azure_openai",
                azure_openai_endpoint="https://myoai.openai.azure.com",
                azure_openai_key=None,
            )

    def test_azure_openai_missing_both_raises(self):
        with pytest.raises(ValueError, match="AZURE_OPENAI_ENDPOINT is required"):
            _make_debug(
                ai_provider="azure_openai",
                azure_openai_endpoint=None,
                azure_openai_key=None,
            )


# ── Database Path Validation ──


class TestDatabasePathValidation:
    """DATABASE_PATH parent directory must exist in production mode."""

    def test_nonexistent_db_parent_raises_in_production(self):
        with pytest.raises(ValueError, match="DATABASE_PATH parent directory"):
            _make_production(database_path="/nonexistent/path/settings.db")

    def test_nonexistent_db_parent_warns_in_debug(self, caplog):
        s = _make_debug(database_path="/nonexistent/path/settings.db")
        assert s.debug is True
        assert "DATABASE_PATH parent directory" in caplog.text

    def test_valid_db_path_passes(self, tmp_path):
        db_path = str(tmp_path / "settings.db")
        s = _make_debug(database_path=db_path)
        assert s.database_path == db_path

    def test_valid_db_path_production(self, tmp_path):
        db_path = str(tmp_path / "settings.db")
        s = _make_production(database_path=db_path)
        assert s.database_path == db_path
