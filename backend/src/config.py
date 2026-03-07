"""Application configuration loaded from environment variables."""

import logging
from functools import lru_cache
from urllib.parse import urlparse

from pydantic import model_validator
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
    github_client_secret: str
    github_redirect_uri: str = "http://localhost:8000/api/v1/auth/github/callback"

    # AI Provider selection: "copilot" (default) or "azure_openai"
    ai_provider: str = "copilot"

    # GitHub Copilot settings (used when ai_provider="copilot")
    copilot_model: str = "gpt-4o"

    # Azure OpenAI settings (used when ai_provider="azure_openai", optional)
    azure_openai_endpoint: str | None = None
    azure_openai_key: str | None = None
    azure_openai_deployment: str = "gpt-4"

    # Session
    session_secret_key: str
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
    metadata_cache_ttl_seconds: int = 3600

    # Default repository for issue creation (owner/repo format)
    default_repository: str | None = None

    # Default GitHub Project V2 node ID for polling (e.g. PVT_kwHOAIsXss4BOJmo)
    # When set, the webhook-token fallback uses this project directly instead of
    # searching project_settings rows.
    default_project_id: str | None = None

    # Default assignee for issues in "In Progress" status (empty to skip)
    default_assignee: str = ""

    # GitHub Webhook secret for verifying webhook payloads
    github_webhook_secret: str | None = None

    # GitHub Personal Access Token for webhook operations (service account)
    # This token is used when webhooks trigger actions that need GitHub API access
    github_webhook_token: str | None = None

    # Copilot PR polling interval in seconds (0 to disable polling)
    copilot_polling_interval: int = 60

    # Encryption — Fernet key for token-at-rest encryption
    encryption_key: str | None = None

    # Database
    database_path: str = "/var/lib/ghchat/data/settings.db"

    # Signal integration
    signal_api_url: str = "http://signal-api:8080"
    signal_phone_number: str | None = None
    signal_webhook_secret: str | None = None

    # Cookie
    cookie_secure: bool = False  # Set True in production (HTTPS)
    cookie_max_age: int = 8 * 60 * 60  # 8 hours in seconds

    # Session cleanup interval in seconds
    session_cleanup_interval: int = 3600

    # API documentation toggle (independent of DEBUG)
    enable_docs: bool = False

    @model_validator(mode="after")
    def _validate_production_secrets(self) -> "Settings":
        """Enforce mandatory secrets in non-debug (production) mode.

        In debug mode, missing values produce warnings instead of errors so
        that local development is not blocked.
        """
        _logger = logging.getLogger(__name__)
        errors: list[str] = []

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
            if errors:
                raise ValueError(
                    "Production configuration errors:\n  - " + "\n  - ".join(errors)
                )
        else:
            if not self.encryption_key:
                _logger.warning(
                    "ENCRYPTION_KEY not set — tokens stored in plaintext (debug mode)"
                )
            if not self.github_webhook_secret:
                _logger.warning(
                    "GITHUB_WEBHOOK_SECRET not set — webhook verification disabled (debug mode)"
                )
            if len(self.session_secret_key) < 64:
                _logger.warning(
                    "SESSION_SECRET_KEY is shorter than 64 characters (debug mode)"
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

    @property
    def default_repo_owner(self) -> str | None:
        """Get default repository owner."""
        if self.default_repository and "/" in self.default_repository:
            owner = self.default_repository.split("/")[0]
            return owner or None
        return None

    @property
    def default_repo_name(self) -> str | None:
        """Get default repository name."""
        if self.default_repository and "/" in self.default_repository:
            name = self.default_repository.split("/")[1]
            return name or None
        return None

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
