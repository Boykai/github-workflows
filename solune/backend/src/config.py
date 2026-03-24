"""Application configuration loaded from environment variables."""

import logging
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore frontend vars like VITE_API_URL
    )

    # GitHub OAuth
    github_client_id: str
    github_client_secret: str = Field(repr=False)
    github_redirect_uri: str = "http://localhost:8000/api/v1/auth/github/callback"

    # AI Provider selection: "copilot" (default) or "azure_openai"
    ai_provider: str = "copilot"

    # GitHub Copilot settings (used when ai_provider="copilot")
    copilot_model: str = "gpt-4o"

    # Azure OpenAI settings (used when ai_provider="azure_openai", optional)
    azure_openai_endpoint: str | None = None
    azure_openai_key: str | None = Field(default=None, repr=False)
    azure_openai_deployment: str = "gpt-4"

    # Session
    session_secret_key: str = Field(repr=False)
    session_expire_hours: int = 8

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors_origins: str = "http://localhost:5173"
    frontend_url: str = "http://localhost:5173"

    # Cache
    cache_ttl_seconds: int = 300

    # Metadata cache TTL (labels, branches, milestones, collaborators)
    metadata_cache_ttl_seconds: int = 300

    # Default repository for issue creation (owner/repo format)
    default_repository: str | None = None

    # Default GitHub Project V2 node ID for polling (e.g. PVT_kwHOAIsXss4BOJmo)
    # When set, the webhook-token fallback uses this project directly instead of
    # searching project_settings rows.
    default_project_id: str | None = None

    # Default assignee for issues in "In Progress" status (empty to skip)
    default_assignee: str = ""

    # GitHub Webhook secret for verifying webhook payloads
    github_webhook_secret: str | None = Field(default=None, repr=False)

    # GitHub Personal Access Token for webhook operations (service account)
    # This token is used when webhooks trigger actions that need GitHub API access
    github_webhook_token: str | None = Field(default=None, repr=False)

    # Copilot PR polling interval in seconds (0 to disable polling)
    copilot_polling_interval: int = 60

    # Encryption — Fernet key for token-at-rest encryption
    encryption_key: str | None = Field(default=None, repr=False)

    # Database
    database_path: str = "/var/lib/solune/data/settings.db"

    # Signal integration
    signal_api_url: str = "http://signal-api:8080"
    signal_phone_number: str | None = None
    signal_webhook_secret: str | None = Field(default=None, repr=False)

    # Cookie
    cookie_secure: bool = False  # Set True in production (HTTPS)
    cookie_max_age: int = 8 * 60 * 60  # 8 hours in seconds

    # Session cleanup interval in seconds
    session_cleanup_interval: int = 3600

    # API documentation toggle (independent of DEBUG)
    enable_docs: bool = False

    # Timeout for external API calls (seconds).
    api_timeout_seconds: int = 30

    # Explicit admin designation via environment variable (numeric GitHub user ID).
    # Required in production mode.  In debug mode, when unset, the first
    # authenticated user is auto-promoted (with a warning).
    admin_github_user_id: int | None = None

    # ── Observability (Phase 5) — all opt-in with safe defaults ──

    # OpenTelemetry — disabled by default; zero import/runtime overhead when off
    otel_enabled: bool = False
    otel_endpoint: str = Field(
        default="http://localhost:4317",
        validation_alias="OTEL_EXPORTER_OTLP_ENDPOINT",
    )
    otel_service_name: str = Field(
        default="solune-backend",
        validation_alias="OTEL_SERVICE_NAME",
    )

    # Sentry — disabled when DSN is empty
    sentry_dsn: str = Field(default="", repr=False)

    # Alert dispatcher — log-only by default
    pipeline_stall_alert_minutes: int = 30
    agent_timeout_alert_minutes: int = 15
    rate_limit_critical_threshold: int = 20
    alert_webhook_url: str = ""
    alert_cooldown_minutes: int = 15

    @model_validator(mode="after")
    def _validate_production_secrets(self) -> "Settings":
        """Enforce mandatory secrets in non-debug (production) mode.

        In debug mode, missing values produce warnings instead of errors so
        that local development is not blocked.
        """
        _logger = logging.getLogger(__name__)
        errors: list[str] = []

        # 1. ai_provider enum check — universal (fatal in all modes)
        _valid_providers = {"copilot", "azure_openai"}
        if self.ai_provider not in _valid_providers:
            raise ValueError(
                f"Unknown AI_PROVIDER {self.ai_provider!r}. "
                f"Supported values: {', '.join(sorted(_valid_providers))}."
            )

        if not self.debug:
            if not self.encryption_key:
                errors.append(
                    "ENCRYPTION_KEY is required in production mode. "
                    'Generate one with: python -c "from cryptography.fernet import Fernet; '
                    'print(Fernet.generate_key().decode())"'
                )
            if not self.github_webhook_secret:
                errors.append(
                    "GITHUB_WEBHOOK_SECRET is required in production mode. "
                    "Generate one with: openssl rand -hex 32"
                )
            if len(self.session_secret_key) < 64:
                errors.append(
                    f"SESSION_SECRET_KEY must be at least 64 characters "
                    f"(current length: {len(self.session_secret_key)}). "
                    "Generate one with: openssl rand -hex 32"
                )
            if not self.effective_cookie_secure:
                errors.append(
                    "Cookies must use the Secure flag in production mode. "
                    "Set COOKIE_SECURE=true or use an https:// FRONTEND_URL."
                )
            if self.admin_github_user_id is None or self.admin_github_user_id <= 0:
                errors.append(
                    "ADMIN_GITHUB_USER_ID is required in production mode. "
                    "Set it to the numeric GitHub user ID of the admin account."
                )
            # 2. Azure OpenAI completeness — production
            if self.ai_provider == "azure_openai":
                if not self.azure_openai_endpoint:
                    errors.append(
                        "AZURE_OPENAI_ENDPOINT is required when AI_PROVIDER is 'azure_openai'. "
                        "Set the AZURE_OPENAI_ENDPOINT environment variable or switch to "
                        "AI_PROVIDER=copilot."
                    )
                if not self.azure_openai_key:
                    errors.append(
                        "AZURE_OPENAI_KEY is required when AI_PROVIDER is 'azure_openai'. "
                        "Set the AZURE_OPENAI_KEY environment variable or switch to "
                        "AI_PROVIDER=copilot."
                    )
            # 3. Database path — production only
            if not self.database_path or (
                self.database_path != ":memory:" and not Path(self.database_path).is_absolute()
            ):
                errors.append(
                    "DATABASE_PATH must be a non-empty absolute path in production mode "
                    "(e.g. /var/lib/solune/data/settings.db). "
                    "Use ':memory:' only for testing."
                )
            if errors:
                raise ValueError("Production configuration errors:\n  - " + "\n  - ".join(errors))
        else:
            if not self.encryption_key:
                _logger.warning("ENCRYPTION_KEY not set — tokens stored in plaintext (debug mode)")
            if not self.github_webhook_secret:
                _logger.warning(
                    "GITHUB_WEBHOOK_SECRET not set — incoming GitHub webhooks will be rejected until configured (debug mode)"
                )
            if len(self.session_secret_key) < 64:
                _logger.warning("SESSION_SECRET_KEY is shorter than 64 characters (debug mode)")
            if self.admin_github_user_id is None:
                _logger.warning(
                    "ADMIN_GITHUB_USER_ID not set — first user to hit an admin endpoint "
                    "will be auto-promoted (debug mode only)"
                )
            elif self.admin_github_user_id <= 0:
                _logger.warning(
                    "ADMIN_GITHUB_USER_ID is %d which is not a valid GitHub user ID (debug mode)",
                    self.admin_github_user_id,
                )
            # 2. Azure OpenAI completeness — debug warning
            if self.ai_provider == "azure_openai" and (
                not self.azure_openai_endpoint or not self.azure_openai_key
            ):
                _logger.warning(
                    "AI_PROVIDER is 'azure_openai' but AZURE_OPENAI_ENDPOINT or "
                    "AZURE_OPENAI_KEY is missing — AI features will not work (debug mode)"
                )

        return self

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse and validate CORS origins from comma-separated string.

        Each origin must be a well-formed URL with a scheme (http/https)
        and a hostname.  Raises :class:`ValueError` on malformed values.
        """
        origins: list[str] = []
        for raw in self.cors_origins.split(","):
            origin = raw.strip()
            if not origin:
                continue
            parsed = urlparse(origin)
            if parsed.scheme not in ("http", "https") or not parsed.hostname:
                raise ValueError(
                    f"Malformed CORS origin: {origin!r}. "
                    "Each origin must include a scheme (http/https) and hostname."
                )
            origins.append(origin)
        return origins

    def _parse_default_repository(self) -> tuple[str | None, str | None]:
        """Split ``default_repository`` into (owner, name).

        Returns ``(None, None)`` when the value is unset, missing a ``/``,
        or either component is empty (e.g. ``"/"``, ``"owner/"``, ``"/repo"``).
        """
        if self.default_repository and "/" in self.default_repository:
            parts = self.default_repository.split("/", 1)
            owner = parts[0]
            name = parts[1] if len(parts) > 1 else ""
            if owner and name:
                return owner, name
        return None, None

    @property
    def default_repo_owner(self) -> str | None:
        """Get default repository owner."""
        return self._parse_default_repository()[0]

    @property
    def default_repo_name(self) -> str | None:
        """Get default repository name."""
        return self._parse_default_repository()[1]

    @property
    def effective_cookie_secure(self) -> bool:
        """Return True if cookies should use the Secure flag.

        Auto-detects HTTPS from ``frontend_url`` so that production
        deployments behind TLS get secure cookies even when
        ``cookie_secure`` is not explicitly set.
        """
        return self.cookie_secure or self.frontend_url.startswith("https://")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()  # type: ignore[call-arg]  # pydantic-settings loads from env


def clear_settings_cache() -> None:
    """Clear the cached :func:`get_settings` instance.

    Useful in test teardown to prevent ``MagicMock`` leaks between tests.
    """
    get_settings.cache_clear()


# Logging configuration
def setup_logging(debug: bool = False, *, structured: bool = False) -> None:
    """Configure application logging.

    Args:
        debug: If *True* the root logger level is set to DEBUG.
        structured: If *True* the :class:`StructuredJsonFormatter` is used
            (production / machine-parseable).  Otherwise a human-readable
            line format is used (development).
    """
    from src.logging_utils import (
        RequestIDFilter,
        SanitizingFormatter,
        StructuredJsonFormatter,
    )

    level = logging.DEBUG if debug else logging.INFO

    # Remove any pre-existing handlers so we don't duplicate output.
    # Copy the list ([:]) because we modify it during iteration.
    root = logging.getLogger()
    root.setLevel(level)
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setLevel(level)

    # Always attach the request-ID filter.
    handler.addFilter(RequestIDFilter())

    if structured:
        handler.setFormatter(StructuredJsonFormatter())
    else:
        fmt = "%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] %(message)s"
        handler.setFormatter(SanitizingFormatter(fmt=fmt, datefmt="%Y-%m-%d %H:%M:%S"))

    root.addHandler(handler)

    # Suppress noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)
