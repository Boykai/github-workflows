"""Unit tests for config, exceptions, and constants modules.

Covers:
- Settings validation and properties
- get_settings() caching
- All AppException subclasses
- Constants and cache key helpers
"""

from src.config import Settings, get_settings
from src.constants import (
    AGENT_DISPLAY_NAMES,
    AGENT_OUTPUT_FILES,
    CACHE_PREFIX_PROJECT_ITEMS,
    CACHE_PREFIX_PROJECTS,
    DEFAULT_AGENT_MAPPINGS,
    DEFAULT_STATUS_COLUMNS,
    NOTIFICATION_EVENT_TYPES,
    SESSION_COOKIE_NAME,
    StatusNames,
    cache_key_agent_output,
    cache_key_issue_pr,
    cache_key_review_requested,
)
from src.exceptions import (
    AppException,
    AuthenticationError,
    AuthorizationError,
    GitHubAPIError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)

# =============================================================================
# Settings
# =============================================================================


class TestSettings:
    """Tests for the Settings model."""

    def _make(self, **overrides) -> Settings:
        defaults = {
            "github_client_id": "cid",
            "github_client_secret": "csecret",
            "session_secret_key": "skey",
            "debug": True,  # Use debug mode to bypass production secret requirements
            "_env_file": None,  # prevent loading .env during tests
        }
        defaults.update(overrides)
        return Settings(**defaults)

    def test_required_fields(self):
        s = self._make()
        assert s.github_client_id == "cid"
        assert s.github_client_secret == "csecret"
        assert s.session_secret_key == "skey"

    def test_defaults(self):
        s = self._make()
        assert s.ai_provider == "copilot"
        assert s.port == 8000
        assert s.session_expire_hours == 8
        assert s.cache_ttl_seconds == 300

    def test_debug_default_is_false(self):
        """The field-level default for debug is False.

        _make() forces debug=True to bypass production validators, so
        test_defaults cannot verify this.  Check the model field directly.
        """
        assert Settings.model_fields["debug"].default is False

    def test_cors_origins_list_single(self):
        s = self._make(cors_origins="http://localhost:5173")
        assert s.cors_origins_list == ["http://localhost:5173"]

    def test_cors_origins_list_multiple(self):
        s = self._make(cors_origins="http://a.com, http://b.com")
        assert s.cors_origins_list == ["http://a.com", "http://b.com"]

    def test_default_repo_owner_set(self):
        s = self._make(default_repository="myorg/myrepo")
        assert s.default_repo_owner == "myorg"

    def test_default_repo_name_set(self):
        s = self._make(default_repository="myorg/myrepo")
        assert s.default_repo_name == "myrepo"

    def test_default_repo_owner_none(self):
        s = self._make(default_repository=None)
        assert s.default_repo_owner is None

    def test_default_repo_name_none(self):
        s = self._make(default_repository=None)
        assert s.default_repo_name is None

    def test_default_repo_no_slash(self):
        s = self._make(default_repository="noslash")
        assert s.default_repo_owner is None
        assert s.default_repo_name is None

    def test_default_repo_trailing_slash(self):
        """A value like 'owner/' should return None, not an empty string."""
        s = self._make(default_repository="owner/")
        assert s.default_repo_owner is None
        assert s.default_repo_name is None

    def test_default_repo_leading_slash(self):
        """A value like '/repo' should return None for owner, not an empty string."""
        s = self._make(default_repository="/repo")
        assert s.default_repo_owner is None
        assert s.default_repo_name is None

    def test_default_repo_slash_only(self):
        """A bare '/' should return None for both owner and name."""
        s = self._make(default_repository="/")
        assert s.default_repo_owner is None
        assert s.default_repo_name is None

    def test_default_repo_extra_slashes_ignored(self):
        """'owner/repo/extra' should split on first slash only, returning 'owner' and 'repo/extra'."""
        s = self._make(default_repository="owner/repo/extra")
        assert s.default_repo_owner == "owner"
        assert s.default_repo_name == "repo/extra"

    # -- effective_cookie_secure property ------------------------------------

    def test_effective_cookie_secure_default_http(self):
        """With default cookie_secure=False and http frontend_url, returns False."""
        s = self._make(frontend_url="http://localhost:5173")
        assert s.effective_cookie_secure is False

    def test_effective_cookie_secure_auto_detects_https(self):
        """Auto-detects HTTPS from frontend_url when cookie_secure is False."""
        s = self._make(frontend_url="https://app.example.com")
        assert s.effective_cookie_secure is True

    def test_effective_cookie_secure_explicit_true(self):
        """Explicit cookie_secure=True always wins regardless of frontend_url."""
        s = self._make(cookie_secure=True, frontend_url="http://localhost:5173")
        assert s.effective_cookie_secure is True

    def test_effective_cookie_secure_explicit_true_with_https(self):
        """Both cookie_secure=True and HTTPS frontend → True."""
        s = self._make(cookie_secure=True, frontend_url="https://app.example.com")
        assert s.effective_cookie_secure is True


class TestGetSettings:
    """Tests for get_settings() LRU caching."""

    def test_returns_settings_instance(self, monkeypatch):
        # Clear lru_cache
        get_settings.cache_clear()
        monkeypatch.setenv("GITHUB_CLIENT_ID", "test-cid")
        monkeypatch.setenv("GITHUB_CLIENT_SECRET", "test-csecret")
        monkeypatch.setenv("SESSION_SECRET_KEY", "test-skey")
        s = get_settings()
        assert isinstance(s, Settings)
        assert s.github_client_id == "test-cid"
        # Cleanup
        get_settings.cache_clear()

    def test_is_cached(self, monkeypatch):
        get_settings.cache_clear()
        monkeypatch.setenv("GITHUB_CLIENT_ID", "a")
        monkeypatch.setenv("GITHUB_CLIENT_SECRET", "b")
        monkeypatch.setenv("SESSION_SECRET_KEY", "c")
        first = get_settings()
        second = get_settings()
        assert first is second
        get_settings.cache_clear()


# =============================================================================
# Exceptions
# =============================================================================


class TestAppException:
    def test_base(self):
        exc = AppException("boom", status_code=418, details={"k": "v"})
        assert str(exc) == "boom"
        assert exc.status_code == 418
        assert exc.details == {"k": "v"}

    def test_defaults(self):
        exc = AppException("x")
        assert exc.status_code == 500
        assert exc.details == {}


class TestAuthenticationError:
    def test_status_code(self):
        exc = AuthenticationError("bad token")
        assert exc.status_code == 401

    def test_inherits(self):
        assert issubclass(AuthenticationError, AppException)


class TestAuthorizationError:
    def test_status_code(self):
        exc = AuthorizationError("forbidden")
        assert exc.status_code == 403


class TestNotFoundError:
    def test_status_code(self):
        exc = NotFoundError("missing")
        assert exc.status_code == 404


class TestValidationError:
    def test_status_code(self):
        exc = ValidationError("bad data")
        assert exc.status_code == 422


class TestGitHubAPIError:
    def test_status_code(self):
        exc = GitHubAPIError("github down")
        assert exc.status_code == 502


class TestRateLimitError:
    def test_status_code(self):
        exc = RateLimitError("slow down")
        assert exc.status_code == 429

    def test_retry_after(self):
        exc = RateLimitError("slow down", retry_after=30)
        assert exc.retry_after == 30

    def test_inherits(self):
        assert issubclass(RateLimitError, AppException)


# =============================================================================
# Constants
# =============================================================================


class TestConstants:
    def test_default_status_columns(self):
        assert DEFAULT_STATUS_COLUMNS == ["Backlog", "In Progress", "Done"]

    def test_session_cookie_name(self):
        assert SESSION_COOKIE_NAME == "session_id"

    def test_cache_prefixes_are_strings(self):
        assert isinstance(CACHE_PREFIX_PROJECTS, str)
        assert isinstance(CACHE_PREFIX_PROJECT_ITEMS, str)

    def test_notification_event_types(self):
        assert "task_status_change" in NOTIFICATION_EVENT_TYPES
        assert len(NOTIFICATION_EVENT_TYPES) == 4

    def test_status_names(self):
        assert StatusNames.BACKLOG == "Backlog"
        assert StatusNames.READY == "Ready"
        assert StatusNames.IN_PROGRESS == "In Progress"
        assert StatusNames.IN_REVIEW == "In Review"
        assert StatusNames.DONE == "Done"

    def test_agent_output_files(self):
        assert "speckit.specify" in AGENT_OUTPUT_FILES
        assert AGENT_OUTPUT_FILES["speckit.specify"] == ["spec.md"]

    def test_default_agent_mappings(self):
        assert StatusNames.BACKLOG in DEFAULT_AGENT_MAPPINGS
        assert "speckit.specify" in DEFAULT_AGENT_MAPPINGS[StatusNames.BACKLOG]

    def test_agent_display_names(self):
        assert "speckit.specify" in AGENT_DISPLAY_NAMES
        assert AGENT_DISPLAY_NAMES["speckit.specify"] == "Spec Kit - Specify"
        assert AGENT_DISPLAY_NAMES["speckit.analyze"] == "Spec Kit - Analyze"


class TestCacheKeyHelpers:
    def test_cache_key_issue_pr(self):
        assert cache_key_issue_pr(42, 100, "PVT_1") == "PVT_1:42:100"

    def test_cache_key_agent_output(self):
        assert cache_key_agent_output(42, "my.agent", 100, "PVT_1") == "PVT_1:42:my.agent:100"

    def test_cache_key_review_requested(self):
        assert cache_key_review_requested(42, "PVT_1") == "PVT_1:copilot_review_requested:42"
