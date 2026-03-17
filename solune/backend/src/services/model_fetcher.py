"""Provider-abstracted model fetching service with TTL-based caching.

Provides a unified interface to fetch available model options from different
AI providers (GitHub Copilot, Azure OpenAI), with in-memory caching, rate-limit
awareness, and stale-while-revalidate semantics.
"""

import asyncio
import hashlib
import time
from abc import ABC, abstractmethod
from datetime import UTC, datetime

from src.config import get_settings
from src.logging_utils import get_logger
from src.models.settings import ModelOption, ModelsResponse
from src.services.completion_providers import CopilotClientPool, get_copilot_client_pool
from src.utils import BoundedDict

logger = get_logger(__name__)

DEFAULT_CACHE_TTL = 600  # 10 minutes
RATE_LIMIT_WARNING_THRESHOLD = 500  # Warn when remaining quota is below this value
MAX_BACKOFF = 900  # 15 minutes
DEFAULT_BACKOFF = 60  # 1 minute


def _cancel_evicted_task(_key: str, task: asyncio.Task) -> None:  # type: ignore[type-arg]
    """Cancel an evicted asyncio.Task that hasn't finished yet."""
    if not task.done():
        task.cancel()
        logger.debug("Cancelled evicted inflight task: %s", _key)


# ── Provider Interface ──


class ModelFetchProvider(ABC):
    """Abstract interface for model list providers."""

    @abstractmethod
    async def fetch_models(self, token: str | None = None) -> list[ModelOption]:
        """Retrieve available models from the provider.

        Args:
            token: Authentication token (required for some providers).

        Returns:
            List of available model options.
        """
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider identifier string."""
        ...

    @property
    @abstractmethod
    def requires_auth(self) -> bool:
        """Whether this provider requires user-specific credentials."""
        ...

    # Optional rate-limit metadata populated after fetch_models() calls.
    # Providers that track rate-limit headers should set these attributes.
    _last_rate_limit_remaining: str | None = None
    _last_rate_limit_reset: str | None = None
    _last_retry_after: str | None = None


# ── Provider Implementations ──


class GitHubCopilotModelFetcher(ModelFetchProvider):
    """Fetches available models from the GitHub Copilot SDK.

    Uses the shared CopilotClientPool to manage client instances,
    eliminating duplication with CopilotCompletionProvider.
    """

    def __init__(self, pool: CopilotClientPool | None = None) -> None:
        self._pool = pool or get_copilot_client_pool()
        self._last_list_models_at: float = 0.0
        self._min_list_models_interval: float = 2.0
        self._lock: asyncio.Lock | None = None

    def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def fetch_models(self, token: str | None = None) -> list[ModelOption]:
        if not token:
            raise ValueError("GitHub OAuth token required for Copilot model fetching")

        client = await self._pool.get_or_create(token)

        async with self._get_lock():
            elapsed = time.monotonic() - self._last_list_models_at
            if self._last_list_models_at > 0 and elapsed < self._min_list_models_interval:
                await asyncio.sleep(self._min_list_models_interval - elapsed)

            try:
                model_list = await client.list_models()
                self._last_retry_after = None
                self._last_rate_limit_remaining = None
                self._last_rate_limit_reset = None
            except Exception as e:
                response = getattr(e, "response", None)
                status_code = getattr(e, "status_code", None)
                if status_code is None and response is not None:
                    status_code = getattr(response, "status_code", None)

                response_headers = getattr(response, "headers", {}) if response else {}
                retry_after = response_headers.get("retry-after") if response_headers else None
                remaining = (
                    response_headers.get("x-ratelimit-remaining") if response_headers else None
                )
                reset = response_headers.get("x-ratelimit-reset") if response_headers else None

                message = str(e).lower()
                is_rate_limited = status_code == 429 or "rate limit" in message
                if is_rate_limited:
                    self._last_retry_after = retry_after
                    self._last_rate_limit_remaining = remaining
                    self._last_rate_limit_reset = reset
                    raise ProviderRateLimitError(
                        retry_after=retry_after,
                        remaining=remaining,
                        reset=reset,
                    ) from e
                raise
            finally:
                self._last_list_models_at = time.monotonic()

        models: list[ModelOption] = []
        for info in model_list:
            model_id = getattr(info, "id", "") or ""
            model_name = getattr(info, "name", "") or model_id
            if model_id:
                models.append(
                    ModelOption(
                        id=model_id,
                        name=model_name,
                        provider="copilot",
                    )
                )

        return models

    @property
    def provider_name(self) -> str:
        return "copilot"

    @property
    def requires_auth(self) -> bool:
        return True


class AzureOpenAIModelFetcher(ModelFetchProvider):
    """Returns a static list of Azure OpenAI models from environment config.

    Azure OpenAI does not expose a public model-listing API with user tokens,
    so this provider returns the configured deployment as a single model option.
    """

    async def fetch_models(self, token: str | None = None) -> list[ModelOption]:
        settings = get_settings()
        models: list[ModelOption] = []

        deployment = getattr(settings, "azure_openai_deployment", None)
        if deployment:
            models.append(
                ModelOption(
                    id=deployment,
                    name=deployment,
                    provider="azure_openai",
                )
            )

        return models

    @property
    def provider_name(self) -> str:
        return "azure_openai"

    @property
    def requires_auth(self) -> bool:
        return False


# ── Errors ──


class ProviderRateLimitError(Exception):
    """Raised when an external model provider returns HTTP 429.

    Named ``ProviderRateLimitError`` to avoid confusion with the
    application-level ``src.exceptions.RateLimitError`` used by the
    global exception handler.
    """

    def __init__(
        self,
        retry_after: str | None = None,
        remaining: str | None = None,
        reset: str | None = None,
    ):
        self.retry_after = retry_after
        self.remaining = remaining
        self.reset = reset
        super().__init__("Provider rate limit exceeded")


# ── Cache Entry ──


class CacheEntry:
    """In-memory cache entry with TTL metadata."""

    def __init__(
        self,
        models: list[ModelOption],
        fetched_at: datetime,
        ttl_seconds: int = DEFAULT_CACHE_TTL,
    ):
        self.models = models
        self.fetched_at = fetched_at
        self.ttl_seconds = ttl_seconds

    @property
    def is_stale(self) -> bool:
        elapsed = (datetime.now(UTC) - self.fetched_at).total_seconds()
        return elapsed > self.ttl_seconds


# ── Service ──


PROVIDER_REGISTRY: dict[str, ModelFetchProvider] = {}


def _ensure_registry() -> None:
    """Lazily populate the provider registry."""
    if not PROVIDER_REGISTRY:
        PROVIDER_REGISTRY["copilot"] = GitHubCopilotModelFetcher()
        PROVIDER_REGISTRY["azure_openai"] = AzureOpenAIModelFetcher()


class ModelFetcherService:
    """Orchestrates model fetching with caching and rate-limit handling.

    Cache is keyed by ``{provider}:{sha256(token)[:16]}``.
    Default TTL is 600 seconds (10 minutes).
    """

    def __init__(self, ttl_seconds: int = DEFAULT_CACHE_TTL):
        self._cache: dict[str, CacheEntry] = {}
        self._ttl_seconds = ttl_seconds
        # Backoff/rate-limit state keyed by cache_key (provider:token_hash)
        # so that one user hitting 429 doesn't block all other users.
        self._backoff_until: dict[str, float] = {}  # cache_key → timestamp
        self._backoff_duration: dict[str, float] = {}  # cache_key → current backoff
        self._rate_limit_remaining: dict[str, int | None] = {}  # cache_key → remaining
        self._inflight_fetches: BoundedDict[str, asyncio.Task[ModelsResponse]] = BoundedDict(
            maxlen=64,
            on_evict=_cancel_evicted_task,
        )
        _ensure_registry()

    @staticmethod
    def _cache_key(provider: str, token: str | None) -> str:
        token_hash = hashlib.sha256((token or "").encode()).hexdigest()[:16]
        return f"{provider}:{token_hash}"

    async def get_models(
        self,
        provider: str,
        token: str | None = None,
        force_refresh: bool = False,
    ) -> ModelsResponse:
        """Fetch models for a provider, using cache when appropriate.

        Returns a ModelsResponse with status indicating the outcome.
        """
        _ensure_registry()
        fetcher = PROVIDER_REGISTRY.get(provider)
        if not fetcher:
            return ModelsResponse(
                status="error",
                message=f"Unknown provider: {provider}",
            )

        # Check auth prerequisite
        if fetcher.requires_auth and not token:
            return ModelsResponse(
                status="auth_required",
                message=_get_auth_message(provider),
            )

        cache_key = self._cache_key(provider, token)
        cached = self._cache.get(cache_key)

        # Check rate-limit backoff (keyed per-user, not per-provider)
        backoff_until = self._backoff_until.get(cache_key, 0)
        if time.time() < backoff_until and not force_refresh:
            # Still in backoff period — return cached if available
            if cached:
                return ModelsResponse(
                    status="rate_limited",
                    models=cached.models,
                    fetched_at=cached.fetched_at.isoformat(),
                    cache_hit=True,
                    rate_limit_warning=True,
                    message=f"Rate limit active. Using cached values. Retry in {int(backoff_until - time.time())}s.",
                )
            return ModelsResponse(
                status="rate_limited",
                rate_limit_warning=True,
                message="Rate limit active. Please try again later.",
            )

        # Serve from cache if fresh
        if cached and not cached.is_stale and not force_refresh:
            return ModelsResponse(
                status="success",
                models=cached.models,
                fetched_at=cached.fetched_at.isoformat(),
                cache_hit=True,
                rate_limit_warning=self._is_rate_limit_warning(cache_key),
            )

        # Serve stale cache immediately and trigger background refresh
        if cached and cached.is_stale and not force_refresh:
            from src.services.task_registry import task_registry

            task_registry.create_task(
                self._background_refresh(provider, token, cache_key),
                name=f"model-refresh-{cache_key[:16]}",
            )
            return ModelsResponse(
                status="success",
                models=cached.models,
                fetched_at=cached.fetched_at.isoformat(),
                cache_hit=True,
                rate_limit_warning=self._is_rate_limit_warning(cache_key),
            )

        # Fresh fetch
        inflight = self._inflight_fetches.get(cache_key)
        if inflight and not force_refresh:
            return await inflight

        async def _fetch_and_cache() -> ModelsResponse:
            try:
                from src.config import get_settings

                timeout = get_settings().api_timeout_seconds
                models = await asyncio.wait_for(fetcher.fetch_models(token), timeout=timeout)
                now = datetime.now(UTC)
                self._cache[cache_key] = CacheEntry(
                    models=models,
                    fetched_at=now,
                    ttl_seconds=self._ttl_seconds,
                )
                # Reset backoff on success
                self._backoff_until.pop(cache_key, None)
                self._backoff_duration.pop(cache_key, None)

                # Parse rate-limit info if available
                if hasattr(fetcher, "_last_rate_limit_remaining"):
                    remaining = fetcher._last_rate_limit_remaining
                    if remaining is not None:
                        try:
                            self._rate_limit_remaining[cache_key] = int(remaining)
                        except (ValueError, TypeError):
                            pass

                return ModelsResponse(
                    status="success",
                    models=models,
                    fetched_at=now.isoformat(),
                    cache_hit=False,
                    rate_limit_warning=self._is_rate_limit_warning(cache_key),
                )

            except ProviderRateLimitError as e:
                self._apply_backoff(cache_key, e.retry_after)
                if cached:
                    return ModelsResponse(
                        status="rate_limited",
                        models=cached.models,
                        fetched_at=cached.fetched_at.isoformat(),
                        cache_hit=True,
                        rate_limit_warning=True,
                        message="Rate limit reached. Using cached values.",
                    )
                return ModelsResponse(
                    status="rate_limited",
                    rate_limit_warning=True,
                    message="Rate limit reached. Please try again later.",
                )

            except Exception as e:
                logger.warning("Failed to fetch models from %s: %s", provider, e)
                if cached:
                    return ModelsResponse(
                        status="error",
                        models=cached.models,
                        fetched_at=cached.fetched_at.isoformat(),
                        cache_hit=True,
                        message="Failed to fetch models. Using cached values.",
                    )
                return ModelsResponse(
                    status="error",
                    message=f"Failed to fetch models from {provider}. Please try again.",
                )

        from src.services.task_registry import task_registry

        task: asyncio.Task[ModelsResponse] = task_registry.create_task(
            _fetch_and_cache(), name=f"model-fetch-{cache_key[:16]}"
        )
        self._inflight_fetches[cache_key] = task
        try:
            return await task
        finally:
            current = self._inflight_fetches.get(cache_key)
            if current is task:
                self._inflight_fetches.pop(cache_key, None)

    async def _background_refresh(self, provider: str, token: str | None, cache_key: str) -> None:
        """Refresh cache in background without blocking the caller."""
        try:
            from src.config import get_settings

            timeout = get_settings().api_timeout_seconds
            fetcher = PROVIDER_REGISTRY.get(provider)
            if not fetcher:
                return
            models = await asyncio.wait_for(fetcher.fetch_models(token), timeout=timeout)
            now = datetime.now(UTC)
            self._cache[cache_key] = CacheEntry(
                models=models,
                fetched_at=now,
                ttl_seconds=self._ttl_seconds,
            )
            logger.info("Background refresh complete for %s", provider)
        except Exception as e:
            logger.warning("Background refresh failed for %s: %s", provider, e)

    def _apply_backoff(self, key: str, retry_after: str | None) -> None:
        """Apply exponential backoff, keyed per-user (cache_key)."""
        if retry_after:
            try:
                wait_seconds = int(retry_after)
            except ValueError:
                wait_seconds = DEFAULT_BACKOFF
        else:
            wait_seconds = DEFAULT_BACKOFF

        # Exponential backoff: double on consecutive rate limits
        current = self._backoff_duration.get(key, 0)
        if current > 0:
            wait_seconds = min(current * 2, MAX_BACKOFF)
        self._backoff_duration[key] = wait_seconds
        self._backoff_until[key] = time.time() + wait_seconds

    def _is_rate_limit_warning(self, key: str) -> bool:
        """Check if remaining rate limit is below warning threshold."""
        remaining = self._rate_limit_remaining.get(key)
        if remaining is not None and remaining < RATE_LIMIT_WARNING_THRESHOLD:
            return True
        return False

    def invalidate_cache(self, provider: str | None = None) -> None:
        """Clear cache entries, optionally for a specific provider."""
        if provider:
            keys_to_remove = [k for k in self._cache if k.startswith(f"{provider}:")]
            for k in keys_to_remove:
                del self._cache[k]
        else:
            self._cache.clear()


def _get_auth_message(provider: str) -> str:
    """Return a user-friendly auth prerequisite message for a provider."""
    messages = {
        "copilot": "Connect your GitHub account to see available Copilot models",
        "azure_openai": "Azure OpenAI credentials not configured",
    }
    return messages.get(provider, f"Authentication required for {provider}")


# ── Singleton ──

_model_fetcher_service: ModelFetcherService | None = None


def get_model_fetcher_service() -> ModelFetcherService:
    """Get or create the singleton ModelFetcherService instance."""
    global _model_fetcher_service
    if _model_fetcher_service is None:
        _model_fetcher_service = ModelFetcherService()
    return _model_fetcher_service
