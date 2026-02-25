"""Application configuration loaded from environment variables."""

import logging
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file="../.env",
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

    # Default repository for issue creation (owner/repo format)
    default_repository: str | None = None

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
    database_path: str = "/app/data/settings.db"

    # Cookie
    cookie_secure: bool = False  # Set True in production (HTTPS)
    cookie_max_age: int = 8 * 60 * 60  # 8 hours in seconds

    # Session cleanup interval in seconds
    session_cleanup_interval: int = 3600

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def default_repo_owner(self) -> str | None:
        """Get default repository owner."""
        if self.default_repository and "/" in self.default_repository:
            return self.default_repository.split("/")[0]
        return None

    @property
    def default_repo_name(self) -> str | None:
        """Get default repository name."""
        if self.default_repository and "/" in self.default_repository:
            return self.default_repository.split("/")[1]
        return None


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()  # type: ignore[call-arg]  # pydantic-settings loads from env


# Logging configuration
def setup_logging(debug: bool = False) -> None:
    """Configure application logging."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # Suppress noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
