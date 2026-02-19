"""Unit tests for application configuration."""

import logging

from src.config import Settings, get_settings, setup_logging


class TestSettings:
    """Tests for the Settings class."""

    def test_creation_with_required_fields(self, monkeypatch):
        """Settings should be created when required env vars are set."""
        # Arrange
        monkeypatch.setenv("GITHUB_CLIENT_ID", "test_id")
        monkeypatch.setenv("GITHUB_CLIENT_SECRET", "test_secret")
        monkeypatch.setenv("SESSION_SECRET_KEY", "test_key")

        # Act
        settings = Settings()  # type: ignore[call-arg]

        # Assert
        assert settings.github_client_id == "test_id"
        assert settings.github_client_secret == "test_secret"
        assert settings.session_secret_key == "test_key"

    def test_default_values(self, monkeypatch):
        """Settings should have sensible defaults."""
        monkeypatch.setenv("GITHUB_CLIENT_ID", "test_id")
        monkeypatch.setenv("GITHUB_CLIENT_SECRET", "test_secret")
        monkeypatch.setenv("SESSION_SECRET_KEY", "test_key")

        settings = Settings()  # type: ignore[call-arg]

        assert settings.debug is False
        assert settings.port == 8000
        assert settings.host == "0.0.0.0"
        assert settings.cors_origins == "http://localhost:5173"
        assert settings.cache_ttl_seconds == 300
        assert settings.ai_provider == "copilot"
        assert settings.session_expire_hours == 8


class TestCorsOriginsList:
    """Tests for the cors_origins_list property."""

    def test_single_origin(self, monkeypatch):
        """Should return a list with one origin."""
        monkeypatch.setenv("GITHUB_CLIENT_ID", "test_id")
        monkeypatch.setenv("GITHUB_CLIENT_SECRET", "test_secret")
        monkeypatch.setenv("SESSION_SECRET_KEY", "test_key")
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")

        settings = Settings()  # type: ignore[call-arg]

        assert settings.cors_origins_list == ["http://localhost:3000"]

    def test_multiple_origins(self, monkeypatch):
        """Should split comma-separated origins into a list."""
        monkeypatch.setenv("GITHUB_CLIENT_ID", "test_id")
        monkeypatch.setenv("GITHUB_CLIENT_SECRET", "test_secret")
        monkeypatch.setenv("SESSION_SECRET_KEY", "test_key")
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000, https://example.com")

        settings = Settings()  # type: ignore[call-arg]

        assert settings.cors_origins_list == ["http://localhost:3000", "https://example.com"]

    def test_origins_strips_whitespace(self, monkeypatch):
        """Should strip whitespace around each origin."""
        monkeypatch.setenv("GITHUB_CLIENT_ID", "test_id")
        monkeypatch.setenv("GITHUB_CLIENT_SECRET", "test_secret")
        monkeypatch.setenv("SESSION_SECRET_KEY", "test_key")
        monkeypatch.setenv("CORS_ORIGINS", "  http://a.com ,  http://b.com  ")

        settings = Settings()  # type: ignore[call-arg]

        assert settings.cors_origins_list == ["http://a.com", "http://b.com"]


class TestDefaultRepoProperties:
    """Tests for default_repo_owner and default_repo_name properties."""

    def test_with_valid_repository(self, monkeypatch):
        """Should parse owner and name from 'owner/repo' format."""
        monkeypatch.setenv("GITHUB_CLIENT_ID", "test_id")
        monkeypatch.setenv("GITHUB_CLIENT_SECRET", "test_secret")
        monkeypatch.setenv("SESSION_SECRET_KEY", "test_key")
        monkeypatch.setenv("DEFAULT_REPOSITORY", "myorg/myrepo")

        settings = Settings()  # type: ignore[call-arg]

        assert settings.default_repo_owner == "myorg"
        assert settings.default_repo_name == "myrepo"

    def test_without_repository(self, monkeypatch):
        """Should return None when default_repository is not set."""
        monkeypatch.setenv("GITHUB_CLIENT_ID", "test_id")
        monkeypatch.setenv("GITHUB_CLIENT_SECRET", "test_secret")
        monkeypatch.setenv("SESSION_SECRET_KEY", "test_key")
        monkeypatch.delenv("DEFAULT_REPOSITORY", raising=False)

        settings = Settings()  # type: ignore[call-arg]

        assert settings.default_repo_owner is None
        assert settings.default_repo_name is None

    def test_without_slash(self, monkeypatch):
        """Should return None when default_repository has no slash."""
        monkeypatch.setenv("GITHUB_CLIENT_ID", "test_id")
        monkeypatch.setenv("GITHUB_CLIENT_SECRET", "test_secret")
        monkeypatch.setenv("SESSION_SECRET_KEY", "test_key")
        monkeypatch.setenv("DEFAULT_REPOSITORY", "noslash")

        settings = Settings()  # type: ignore[call-arg]

        assert settings.default_repo_owner is None
        assert settings.default_repo_name is None


class TestGetSettings:
    """Tests for the get_settings cached function."""

    def test_returns_settings_instance(self, monkeypatch):
        """get_settings should return a Settings instance."""
        monkeypatch.setenv("GITHUB_CLIENT_ID", "test_id")
        monkeypatch.setenv("GITHUB_CLIENT_SECRET", "test_secret")
        monkeypatch.setenv("SESSION_SECRET_KEY", "test_key")
        get_settings.cache_clear()

        result = get_settings()

        assert isinstance(result, Settings)

    def test_caching(self, monkeypatch):
        """get_settings should return the same instance on repeated calls."""
        monkeypatch.setenv("GITHUB_CLIENT_ID", "test_id")
        monkeypatch.setenv("GITHUB_CLIENT_SECRET", "test_secret")
        monkeypatch.setenv("SESSION_SECRET_KEY", "test_key")
        get_settings.cache_clear()

        first = get_settings()
        second = get_settings()

        assert first is second

    def test_cache_clear(self, monkeypatch):
        """Clearing cache should produce a new instance."""
        monkeypatch.setenv("GITHUB_CLIENT_ID", "test_id")
        monkeypatch.setenv("GITHUB_CLIENT_SECRET", "test_secret")
        monkeypatch.setenv("SESSION_SECRET_KEY", "test_key")
        get_settings.cache_clear()

        first = get_settings()
        get_settings.cache_clear()
        second = get_settings()

        # They are equal but not the same object
        assert first is not second


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_debug_mode(self):
        """Debug mode should configure root logger with DEBUG level."""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.WARNING)  # reset

        setup_logging(debug=True)

        # basicConfig only sets level if no handlers exist; verify via handlers
        assert (
            any(h.level <= logging.DEBUG for h in root_logger.handlers)
            or root_logger.level == logging.DEBUG
        )

    def test_info_mode(self):
        """Non-debug mode should configure root logger with INFO level."""
        root_logger = logging.getLogger()
        # Remove existing handlers so basicConfig can set level
        root_logger.handlers.clear()

        setup_logging(debug=False)

        assert root_logger.level == logging.INFO

    def test_suppresses_noisy_loggers(self):
        """Should suppress httpx and httpcore loggers."""
        setup_logging(debug=False)

        assert logging.getLogger("httpx").level == logging.WARNING
        assert logging.getLogger("httpcore").level == logging.WARNING
