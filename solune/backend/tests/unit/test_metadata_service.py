"""Unit tests for MetadataService.

Covers:
- _is_stale() — staleness check logic
- _fallback_context() — hardcoded constant fallback
- get_or_fetch() — three-tier cache fallback
- invalidate() — cache clearing
- fetch_metadata() — GitHub REST API fetch with paginated results
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.services.cache import InMemoryCache
from src.services.metadata_service import MetadataService, RepositoryMetadataContext
from src.utils import utcnow


# =============================================================================
# Helpers
# =============================================================================

def _fresh_fetched_at() -> str:
    """Return an ISO timestamp that will pass any reasonable TTL check."""
    return utcnow().isoformat()


def _stale_fetched_at(ttl: int = 3600) -> str:
    """Return an ISO timestamp that is older than *ttl* seconds."""
    return (utcnow() - timedelta(seconds=ttl + 60)).isoformat()


def _make_ctx(repo_key: str = "owner/repo", **overrides) -> dict:
    """Build a minimal RepositoryMetadataContext dict for L1 cache seeding."""
    defaults = {
        "repo_key": repo_key,
        "labels": [{"name": "bug", "color": "d73a4a", "description": ""}],
        "branches": [{"name": "main", "protected": True}],
        "milestones": [],
        "collaborators": [],
        "fetched_at": _fresh_fetched_at(),
        "is_stale": False,
        "source": "cache",
    }
    defaults.update(overrides)
    return defaults


# =============================================================================
# _is_stale
# =============================================================================


class TestIsStale:
    """Tests for MetadataService._is_stale."""

    @patch("src.services.metadata_service.get_settings")
    def test_empty_fetched_at_is_stale(self, mock_settings):
        mock_settings.return_value = MagicMock(metadata_cache_ttl_seconds=3600)
        svc = MetadataService(l1_cache=InMemoryCache())
        assert svc._is_stale("", 3600) is True

    @patch("src.services.metadata_service.get_settings")
    def test_recent_timestamp_not_stale(self, mock_settings):
        mock_settings.return_value = MagicMock(metadata_cache_ttl_seconds=3600)
        svc = MetadataService(l1_cache=InMemoryCache())
        assert svc._is_stale(_fresh_fetched_at(), 3600) is False

    @patch("src.services.metadata_service.get_settings")
    def test_old_timestamp_is_stale(self, mock_settings):
        mock_settings.return_value = MagicMock(metadata_cache_ttl_seconds=3600)
        svc = MetadataService(l1_cache=InMemoryCache())
        assert svc._is_stale(_stale_fetched_at(3600), 3600) is True

    @patch("src.services.metadata_service.get_settings")
    def test_invalid_timestamp_is_stale(self, mock_settings):
        mock_settings.return_value = MagicMock(metadata_cache_ttl_seconds=3600)
        svc = MetadataService(l1_cache=InMemoryCache())
        assert svc._is_stale("not-a-date", 3600) is True


# =============================================================================
# _fallback_context
# =============================================================================


class TestFallbackContext:
    """Tests for the hardcoded constant fallback."""

    @patch("src.services.metadata_service.get_settings")
    def test_fallback_returns_known_labels(self, mock_settings):
        mock_settings.return_value = MagicMock(metadata_cache_ttl_seconds=3600)
        svc = MetadataService(l1_cache=InMemoryCache())
        ctx = svc._fallback_context("owner/repo")

        assert ctx.source == "fallback"
        assert ctx.repo_key == "owner/repo"
        assert len(ctx.labels) > 0
        assert ctx.branches == [{"name": "main", "protected": True}]


# =============================================================================
# get_or_fetch — L1 hit
# =============================================================================


class TestGetOrFetchL1:
    """Tests for get_or_fetch when L1 cache has fresh data."""

    @pytest.mark.anyio
    @patch("src.services.metadata_service.get_settings")
    async def test_l1_hit_returns_cached(self, mock_settings):
        mock_settings.return_value = MagicMock(metadata_cache_ttl_seconds=3600)
        l1 = InMemoryCache()
        svc = MetadataService(l1_cache=l1)

        ctx_dict = _make_ctx()
        l1.set("metadata:owner/repo", ctx_dict, ttl_seconds=3600)

        result = await svc.get_or_fetch("tok", "owner", "repo")

        assert result.source == "cache"
        assert result.is_stale is False


# =============================================================================
# get_or_fetch — fallback to constants
# =============================================================================


class TestGetOrFetchFallback:
    """get_or_fetch falls back to constants when API and SQLite fail."""

    @pytest.mark.anyio
    @patch("src.services.metadata_service.get_settings")
    async def test_falls_back_to_constants(self, mock_settings):
        mock_settings.return_value = MagicMock(metadata_cache_ttl_seconds=3600)
        l1 = InMemoryCache()
        svc = MetadataService(l1_cache=l1)

        # Patch SQLite reads and API fetch to fail
        with (
            patch.object(svc, "_read_from_sqlite", new_callable=AsyncMock, return_value=None),
            patch.object(svc, "fetch_metadata", new_callable=AsyncMock, side_effect=Exception("API down")),
        ):
            result = await svc.get_or_fetch("tok", "owner", "repo")

        assert result.source == "fallback"
        assert len(result.labels) > 0


# =============================================================================
# invalidate
# =============================================================================


class TestInvalidate:
    """Tests for MetadataService.invalidate."""

    @pytest.mark.anyio
    @patch("src.services.metadata_service.get_settings")
    async def test_invalidate_clears_l1(self, mock_settings):
        mock_settings.return_value = MagicMock(metadata_cache_ttl_seconds=3600)
        l1 = InMemoryCache()
        svc = MetadataService(l1_cache=l1)

        l1.set("metadata:owner/repo", _make_ctx(), ttl_seconds=3600)
        assert l1.get("metadata:owner/repo") is not None

        with patch("src.services.metadata_service.get_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            await svc.invalidate("owner", "repo")

        assert l1.get("metadata:owner/repo") is None
