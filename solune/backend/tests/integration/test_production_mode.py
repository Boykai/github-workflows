"""Production-parity tests — verify behavior under production-like config."""

from unittest.mock import patch

import pytest

from src.config import Settings, clear_settings_cache


@pytest.fixture(autouse=True)
def _clear_cache():
    """Ensure settings cache is cleared between tests."""
    clear_settings_cache()
    yield
    clear_settings_cache()


# Minimal valid production env vars
_PRODUCTION_BASE = {
    "GITHUB_CLIENT_ID": "test-client-id",
    "GITHUB_CLIENT_SECRET": "test-secret",
    "SESSION_SECRET_KEY": "a" * 64,
    "ENCRYPTION_KEY": "dGVzdGtleXRlc3RrZXl0ZXN0a2V5dGVzdGtleXQ=",  # dummy base64
    "GITHUB_WEBHOOK_SECRET": "abc123",
    "COOKIE_SECURE": "true",
    "ADMIN_GITHUB_USER_ID": "12345",
    "DEBUG": "false",
}


class TestProductionConfig:
    """Tests verifying application behavior with production settings."""

    def test_debug_mode_disabled_requires_secrets(self) -> None:
        """When DEBUG=false, required secrets must be present."""
        env = {**_PRODUCTION_BASE, "ENCRYPTION_KEY": ""}
        with (
            patch.dict("os.environ", env, clear=True),
            pytest.raises(ValueError, match="ENCRYPTION_KEY is required"),
        ):
            Settings()  # type: ignore[call-arg]

    def test_production_rejects_short_session_key(self) -> None:
        """Production mode rejects session keys shorter than 64 chars."""
        env = {**_PRODUCTION_BASE, "SESSION_SECRET_KEY": "short"}
        with (
            patch.dict("os.environ", env, clear=True),
            pytest.raises(ValueError, match="SESSION_SECRET_KEY must be at least 64"),
        ):
            Settings()  # type: ignore[call-arg]

    def test_production_requires_admin_user_id(self) -> None:
        """Production mode requires ADMIN_GITHUB_USER_ID."""
        env = {k: v for k, v in _PRODUCTION_BASE.items() if k != "ADMIN_GITHUB_USER_ID"}
        with (
            patch.dict("os.environ", env, clear=True),
            pytest.raises(ValueError, match="ADMIN_GITHUB_USER_ID is required"),
        ):
            Settings()  # type: ignore[call-arg]

    def test_production_requires_cookie_secure(self) -> None:
        """Production mode requires secure cookies."""
        env = {**_PRODUCTION_BASE, "COOKIE_SECURE": "false", "FRONTEND_URL": "http://localhost"}
        with (
            patch.dict("os.environ", env, clear=True),
            pytest.raises(ValueError, match="Secure flag"),
        ):
            Settings()  # type: ignore[call-arg]

    def test_valid_production_config_succeeds(self) -> None:
        """A fully-specified production config loads without error."""
        with patch.dict("os.environ", _PRODUCTION_BASE, clear=True):
            settings = Settings()  # type: ignore[call-arg]
            assert settings.debug is False
            assert settings.encryption_key is not None

    def test_debug_mode_allows_missing_secrets(self) -> None:
        """Debug mode allows missing optional secrets without raising."""
        env = {
            "GITHUB_CLIENT_ID": "test",
            "GITHUB_CLIENT_SECRET": "test",
            "SESSION_SECRET_KEY": "short",
            "DEBUG": "true",
        }
        with patch.dict("os.environ", env, clear=True):
            settings = Settings()  # type: ignore[call-arg]
            assert settings.debug is True
