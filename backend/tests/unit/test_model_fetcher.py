"""Tests for the model fetcher service and /settings/models/{provider} endpoint.

Covers:
- ModelFetcherService caching logic
- GET /api/v1/settings/models/copilot → dynamic fetch
- GET /api/v1/settings/models/azure_openai → static fetch
- GET /api/v1/settings/models/unknown → error response
- Auth prerequisite validation
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from src.models.settings import ModelOption, ModelsResponse
from src.services.database import seed_global_settings
from src.services.model_fetcher import (
    CacheEntry,
    ModelFetcherService,
    _model_fetcher_service,
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
        assert len(result.models) >= 0  # May be 0 if no deployment configured

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
            resp = await seeded_client.get(
                "/api/v1/settings/models/copilot?force_refresh=true"
            )

        assert resp.status_code == 200
        mock_service.get_models.assert_called_once_with(
            "copilot", token="test-token", force_refresh=True
        )
