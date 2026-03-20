"""Tests for the model fetcher service and /settings/models/{provider} endpoint.

Covers:
- ModelFetcherService caching logic
- GET /api/v1/settings/models/copilot → dynamic fetch
- GET /api/v1/settings/models/azure_openai → static fetch
- GET /api/v1/settings/models/unknown → error response
- Auth prerequisite validation
"""

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from src.models.settings import ModelOption, ModelsResponse
from src.services.database import seed_global_settings
from src.services.model_fetcher import (
    DEFAULT_BACKOFF,
    MAX_BACKOFF,
    AzureOpenAIModelFetcher,
    CacheEntry,
    GitHubCopilotModelFetcher,
    ModelFetcherService,
    ProviderRateLimitError,
    _get_auth_message,
    get_model_fetcher_service,
)

# ── Helpers ─────────────────────────────────────────────────────────────────


@pytest.fixture
async def seeded_client(client, mock_db):
    """Client fixture with global_settings row seeded."""
    await seed_global_settings(mock_db)
    return client


@pytest.fixture
def fetcher_service():
    """Fresh ModelFetcherService instance for each test."""
    return ModelFetcherService(ttl_seconds=600)


# ── ModelFetcherService Unit Tests ──────────────────────────────────────────


class TestModelFetcherService:
    async def test_unknown_provider_returns_error(self, fetcher_service):
        result = await fetcher_service.get_models("unknown_provider", token="tok")
        assert result.status == "error"
        assert "Unknown provider" in (result.message or "")

    async def test_auth_required_when_no_token_for_copilot(self, fetcher_service):
        result = await fetcher_service.get_models("copilot", token=None)
        assert result.status == "auth_required"
        assert "GitHub" in (result.message or "")

    async def test_azure_returns_models_without_token(self, fetcher_service):
        """Azure OpenAI doesn't require user auth; returns static deployment."""
        with patch("src.services.model_fetcher.get_settings") as mock_settings:
            mock_settings.return_value.azure_openai_deployment = "gpt-4o-deploy"
            result = await fetcher_service.get_models("azure_openai", token=None)
        assert result.status == "success"
        assert any(m.id == "gpt-4o-deploy" for m in result.models)

    async def test_cache_hit_on_second_call(self, fetcher_service):
        """Second call should return cached data."""
        # Seed cache manually
        key = fetcher_service._cache_key("copilot", "test-token")
        fetcher_service._cache[key] = CacheEntry(
            models=[ModelOption(id="gpt-4o", name="GPT-4o", provider="copilot")],
            fetched_at=datetime.now(UTC),
            ttl_seconds=600,
        )
        result = await fetcher_service.get_models("copilot", token="test-token")
        assert result.status == "success"
        assert result.cache_hit is True
        assert len(result.models) == 1
        assert result.models[0].id == "gpt-4o"

    async def test_force_refresh_bypasses_cache(self, fetcher_service):
        """force_refresh=True should fetch fresh data even with valid cache."""
        key = fetcher_service._cache_key("copilot", "test-token")
        fetcher_service._cache[key] = CacheEntry(
            models=[ModelOption(id="old-model", name="Old", provider="copilot")],
            fetched_at=datetime.now(UTC),
            ttl_seconds=600,
        )

        mock_fetcher = AsyncMock()
        mock_fetcher.fetch_models.return_value = [
            ModelOption(id="new-model", name="New", provider="copilot")
        ]
        mock_fetcher.requires_auth = True

        with patch.dict(
            "src.services.model_fetcher.PROVIDER_REGISTRY",
            {"copilot": mock_fetcher},
        ):
            result = await fetcher_service.get_models(
                "copilot", token="test-token", force_refresh=True
            )

        assert result.status == "success"
        assert result.cache_hit is False
        assert result.models[0].id == "new-model"

    async def test_error_fallback_to_cached_values(self, fetcher_service):
        """On fetch error, should return cached values if available."""
        key = fetcher_service._cache_key("copilot", "test-token")
        fetcher_service._cache[key] = CacheEntry(
            models=[ModelOption(id="cached-model", name="Cached", provider="copilot")],
            fetched_at=datetime.now(UTC),
            ttl_seconds=0,  # Already stale — will try to refresh
        )

        mock_fetcher = AsyncMock()
        mock_fetcher.fetch_models.side_effect = Exception("API down")
        mock_fetcher.requires_auth = True

        with patch.dict(
            "src.services.model_fetcher.PROVIDER_REGISTRY",
            {"copilot": mock_fetcher},
        ):
            result = await fetcher_service.get_models(
                "copilot", token="test-token", force_refresh=True
            )

        assert result.status == "error"
        assert result.cache_hit is True
        assert len(result.models) == 1
        assert result.models[0].id == "cached-model"

    def test_invalidate_cache_for_provider(self, fetcher_service):
        fetcher_service._cache["copilot:abc123"] = CacheEntry(
            models=[], fetched_at=datetime.now(UTC)
        )
        fetcher_service._cache["azure_openai:def456"] = CacheEntry(
            models=[], fetched_at=datetime.now(UTC)
        )
        fetcher_service.invalidate_cache("copilot")
        assert "copilot:abc123" not in fetcher_service._cache
        assert "azure_openai:def456" in fetcher_service._cache

    def test_invalidate_cache_all(self, fetcher_service):
        fetcher_service._cache["copilot:abc123"] = CacheEntry(
            models=[], fetched_at=datetime.now(UTC)
        )
        fetcher_service.invalidate_cache()
        assert len(fetcher_service._cache) == 0

    async def test_stale_cache_returns_cached_models_and_schedules_background_refresh(
        self, fetcher_service
    ):
        key = fetcher_service._cache_key("copilot", "test-token")
        fetcher_service._cache[key] = CacheEntry(
            models=[ModelOption(id="cached", name="Cached", provider="copilot")],
            fetched_at=datetime.now(UTC),
            ttl_seconds=0,
        )

        scheduled: dict[str, str] = {}

        def create_task(coro, name):
            scheduled["name"] = name
            coro.close()
            return AsyncMock()

        with patch("src.services.task_registry.task_registry.create_task", side_effect=create_task):
            result = await fetcher_service.get_models("copilot", token="test-token")

        assert result.status == "success"
        assert result.cache_hit is True
        assert result.models[0].id == "cached"
        assert scheduled["name"].startswith("model-refresh-")

    async def test_existing_inflight_fetch_is_reused(self, fetcher_service):
        key = fetcher_service._cache_key("copilot", "test-token")
        inflight = asyncio.create_task(
            asyncio.sleep(
                0,
                result=ModelsResponse(
                    status="success",
                    models=[ModelOption(id="shared", name="Shared", provider="copilot")],
                ),
            )
        )
        fetcher_service._inflight_fetches[key] = inflight

        result = await fetcher_service.get_models("copilot", token="test-token")

        assert result.status == "success"
        assert result.models[0].id == "shared"

    async def test_provider_rate_limit_without_cache_returns_rate_limited(self, fetcher_service):
        mock_fetcher = AsyncMock()
        mock_fetcher.fetch_models.side_effect = ProviderRateLimitError(retry_after="30")
        mock_fetcher.requires_auth = True

        with (
            patch.dict("src.services.model_fetcher.PROVIDER_REGISTRY", {"copilot": mock_fetcher}),
            patch(
                "src.services.model_fetcher.get_settings",
                return_value=SimpleNamespace(api_timeout_seconds=1),
            ),
            patch(
                "src.services.task_registry.task_registry.create_task",
                side_effect=lambda coro, name: asyncio.create_task(coro, name=name),
            ),
        ):
            result = await fetcher_service.get_models(
                "copilot", token="test-token", force_refresh=True
            )

        key = fetcher_service._cache_key("copilot", "test-token")
        assert result.status == "rate_limited"
        assert result.cache_hit is False
        assert fetcher_service._backoff_duration[key] == 30

    async def test_provider_rate_limit_with_cache_returns_cached_values(self, fetcher_service):
        key = fetcher_service._cache_key("copilot", "test-token")
        fetcher_service._cache[key] = CacheEntry(
            models=[ModelOption(id="cached", name="Cached", provider="copilot")],
            fetched_at=datetime.now(UTC),
            ttl_seconds=600,
        )
        mock_fetcher = AsyncMock()
        mock_fetcher.fetch_models.side_effect = ProviderRateLimitError(retry_after="45")
        mock_fetcher.requires_auth = True

        with (
            patch.dict("src.services.model_fetcher.PROVIDER_REGISTRY", {"copilot": mock_fetcher}),
            patch(
                "src.services.model_fetcher.get_settings",
                return_value=SimpleNamespace(api_timeout_seconds=1),
            ),
            patch(
                "src.services.task_registry.task_registry.create_task",
                side_effect=lambda coro, name: asyncio.create_task(coro, name=name),
            ),
        ):
            result = await fetcher_service.get_models(
                "copilot", token="test-token", force_refresh=True
            )

        assert result.status == "rate_limited"
        assert result.cache_hit is True
        assert result.models[0].id == "cached"

    def test_apply_backoff_doubles_and_caps_wait_time(self, fetcher_service):
        fetcher_service._apply_backoff("copilot:key", str(DEFAULT_BACKOFF))
        assert fetcher_service._backoff_duration["copilot:key"] == DEFAULT_BACKOFF

        fetcher_service._apply_backoff("copilot:key", str(DEFAULT_BACKOFF))
        assert fetcher_service._backoff_duration["copilot:key"] == DEFAULT_BACKOFF * 2

        fetcher_service._backoff_duration["copilot:key"] = MAX_BACKOFF
        fetcher_service._apply_backoff("copilot:key", str(DEFAULT_BACKOFF))
        assert fetcher_service._backoff_duration["copilot:key"] == MAX_BACKOFF

    def test_rate_limit_warning_only_trips_below_threshold(self, fetcher_service):
        fetcher_service._rate_limit_remaining["copilot:key"] = 499
        assert fetcher_service._is_rate_limit_warning("copilot:key") is True

        fetcher_service._rate_limit_remaining["copilot:key"] = 500
        assert fetcher_service._is_rate_limit_warning("copilot:key") is False


# ── API Endpoint Tests ──────────────────────────────────────────────────────


class TestModelsEndpoint:
    async def test_get_models_unknown_provider(self, seeded_client):
        resp = await seeded_client.get("/api/v1/settings/models/unknown")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "error"
        assert "Unknown provider" in data["message"]

    async def test_get_models_copilot_returns_response(self, seeded_client):
        """Copilot endpoint should return a valid ModelsResponse structure."""
        mock_service = AsyncMock()
        mock_service.get_models.return_value = ModelsResponse(
            status="success",
            models=[
                ModelOption(id="gpt-4o", name="GPT-4o", provider="copilot"),
                ModelOption(id="gpt-4o-mini", name="GPT-4o Mini", provider="copilot"),
            ],
            fetched_at="2026-02-28T01:00:00Z",
            cache_hit=False,
        )

        with patch(
            "src.api.settings.get_model_fetcher_service",
            return_value=mock_service,
        ):
            resp = await seeded_client.get("/api/v1/settings/models/copilot")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert len(data["models"]) == 2
        assert data["models"][0]["id"] == "gpt-4o"

    async def test_get_models_with_force_refresh(self, seeded_client):
        """force_refresh query param should be passed through."""
        mock_service = AsyncMock()
        mock_service.get_models.return_value = ModelsResponse(
            status="success", models=[], cache_hit=False
        )

        with patch(
            "src.api.settings.get_model_fetcher_service",
            return_value=mock_service,
        ):
            resp = await seeded_client.get("/api/v1/settings/models/copilot?force_refresh=true")

        assert resp.status_code == 200
        mock_service.get_models.assert_called_once_with(
            "copilot", token="test-token", force_refresh=True
        )


class TestProviderImplementations:
    async def test_github_fetcher_requires_token(self):
        fetcher = GitHubCopilotModelFetcher(pool=AsyncMock())

        with pytest.raises(ValueError):
            await fetcher.fetch_models()

    async def test_github_fetcher_maps_models_and_ignores_missing_ids(self):
        client = AsyncMock()
        client.list_models.return_value = [
            SimpleNamespace(id="gpt-4o", name="GPT-4o"),
            SimpleNamespace(id="", name="skip-me"),
            SimpleNamespace(id="gpt-4o-mini", name=""),
        ]
        pool = AsyncMock()
        pool.get_or_create.return_value = client
        fetcher = GitHubCopilotModelFetcher(pool=pool)

        models = await fetcher.fetch_models("token-1")

        assert [model.id for model in models] == ["gpt-4o", "gpt-4o-mini"]
        assert models[1].name == "gpt-4o-mini"

    async def test_github_fetcher_raises_provider_rate_limit_error(self):
        response = SimpleNamespace(
            status_code=429,
            headers={
                "retry-after": "60",
                "x-ratelimit-remaining": "0",
                "x-ratelimit-reset": "12345",
            },
        )
        client = AsyncMock()
        client.list_models.side_effect = RuntimeError("rate limit exceeded")
        client.list_models.side_effect.response = response
        client.list_models.side_effect.status_code = 429
        pool = AsyncMock()
        pool.get_or_create.return_value = client
        fetcher = GitHubCopilotModelFetcher(pool=pool)

        with pytest.raises(ProviderRateLimitError) as exc_info:
            await fetcher.fetch_models("token-1")

        assert exc_info.value.retry_after == "60"
        assert fetcher._last_rate_limit_remaining == "0"

    async def test_azure_fetcher_returns_empty_without_deployment(self):
        fetcher = AzureOpenAIModelFetcher()

        with patch("src.services.model_fetcher.get_settings", return_value=SimpleNamespace()):
            models = await fetcher.fetch_models()

        assert models == []


class TestSingletonHelpers:
    def test_get_auth_message_uses_provider_specific_and_fallback_messages(self):
        assert "GitHub" in _get_auth_message("copilot")
        assert _get_auth_message("custom-provider") == "Authentication required for custom-provider"

    def test_get_model_fetcher_service_returns_singleton_instance(self):
        with patch("src.services.model_fetcher._model_fetcher_service", None):
            first = get_model_fetcher_service()
            second = get_model_fetcher_service()

        assert first is second
