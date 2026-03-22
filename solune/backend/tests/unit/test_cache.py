"""Unit tests for cache service."""

import time
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest

from src.services.cache import CacheEntry, InMemoryCache, compute_data_hash
from src.utils import utcnow


class TestCacheEntry:
    """Tests for CacheEntry class."""

    def test_entry_stores_value(self):
        """Should store value correctly."""
        entry = CacheEntry("test_value", ttl_seconds=60)

        assert entry.value == "test_value"

    def test_entry_calculates_expiration(self):
        """Should calculate expiration time based on TTL."""
        entry = CacheEntry("test_value", ttl_seconds=60)

        expected_min = utcnow() + timedelta(seconds=59)
        expected_max = utcnow() + timedelta(seconds=61)

        assert expected_min <= entry.expires_at <= expected_max

    def test_entry_is_not_expired_initially(self):
        """Should not be expired when just created."""
        entry = CacheEntry("test_value", ttl_seconds=60)

        assert entry.is_expired is False

    def test_entry_is_expired_after_ttl(self):
        """Should be expired after TTL passes."""
        entry = CacheEntry("test_value", ttl_seconds=0)

        # Very short TTL means it's already expired
        time.sleep(0.01)
        assert entry.is_expired is True


class TestInMemoryCache:
    """Tests for InMemoryCache class."""

    @patch("src.services.cache.get_settings")
    def test_get_returns_none_for_missing_key(self, mock_settings):
        """Should return None for non-existent key."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)

        cache = InMemoryCache()

        assert cache.get("nonexistent_key") is None

    @patch("src.services.cache.get_settings")
    def test_set_and_get_value(self, mock_settings):
        """Should store and retrieve value."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)

        cache = InMemoryCache()
        cache.set("test_key", "test_value")

        assert cache.get("test_key") == "test_value"

    @patch("src.services.cache.get_settings")
    def test_set_with_custom_ttl(self, mock_settings):
        """Should accept custom TTL."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)

        cache = InMemoryCache()
        cache.set("test_key", "test_value", ttl_seconds=600)

        assert cache.get("test_key") == "test_value"

    @patch("src.services.cache.get_settings")
    def test_get_returns_none_for_expired_entry(self, mock_settings):
        """Should return None and delete expired entries."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)

        cache = InMemoryCache()
        cache.set("test_key", "test_value", ttl_seconds=1)

        # Wait for entry to expire
        time.sleep(1.1)
        assert cache.get("test_key") is None

    @patch("src.services.cache.get_settings")
    def test_delete_removes_entry(self, mock_settings):
        """Should delete entry from cache."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)

        cache = InMemoryCache()
        cache.set("test_key", "test_value")

        result = cache.delete("test_key")

        assert result is True
        assert cache.get("test_key") is None

    @patch("src.services.cache.get_settings")
    def test_delete_returns_false_for_missing_key(self, mock_settings):
        """Should return False when deleting non-existent key."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)

        cache = InMemoryCache()

        result = cache.delete("nonexistent_key")

        assert result is False

    @patch("src.services.cache.get_settings")
    def test_cache_stores_different_types(self, mock_settings):
        """Should store different value types."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)

        cache = InMemoryCache()

        cache.set("string", "test")
        cache.set("number", 42)
        cache.set("list", [1, 2, 3])
        cache.set("dict", {"key": "value"})

        assert cache.get("string") == "test"
        assert cache.get("number") == 42
        assert cache.get("list") == [1, 2, 3]
        assert cache.get("dict") == {"key": "value"}

    @patch("src.services.cache.get_settings")
    def test_overwrite_existing_key(self, mock_settings):
        """Should overwrite existing key with new value."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)

        cache = InMemoryCache()

        cache.set("test_key", "original")
        cache.set("test_key", "updated")

        assert cache.get("test_key") == "updated"


class TestComputeDataHash:
    """Tests for compute_data_hash helper."""

    def test_deterministic_for_same_data(self):
        """Same data should produce the same hash."""
        data = {"columns": [{"name": "Todo"}, {"name": "Done"}], "count": 5}
        assert compute_data_hash(data) == compute_data_hash(data)

    def test_different_data_produces_different_hash(self):
        """Different data should produce different hashes."""
        data_a = {"columns": [{"name": "Todo"}]}
        data_b = {"columns": [{"name": "Done"}]}
        assert compute_data_hash(data_a) != compute_data_hash(data_b)

    def test_key_order_independent(self):
        """Key ordering should not affect hash (sort_keys=True)."""
        data_a = {"b": 2, "a": 1}
        data_b = {"a": 1, "b": 2}
        assert compute_data_hash(data_a) == compute_data_hash(data_b)

    def test_returns_hex_string(self):
        """Hash should be a hex-encoded SHA-256 string."""
        h = compute_data_hash({"key": "value"})
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 hex length


class TestCacheEntryDataHash:
    """Tests for CacheEntry data_hash field (FR-004 change detection)."""

    def test_data_hash_defaults_to_none(self):
        """CacheEntry should default data_hash to None when not provided."""
        entry = CacheEntry("value", ttl_seconds=60)
        assert entry.data_hash is None

    def test_data_hash_stored_on_entry(self):
        """CacheEntry should store the provided data_hash."""
        entry = CacheEntry("value", ttl_seconds=60, data_hash="abc123")
        assert entry.data_hash == "abc123"

    @patch("src.services.cache.get_settings")
    def test_set_with_data_hash(self, mock_settings):
        """InMemoryCache.set should forward data_hash to CacheEntry."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)
        c = InMemoryCache()
        c.set("k", "v", data_hash="hash1")
        entry = c.get_entry("k")
        assert entry is not None
        assert entry.data_hash == "hash1"

    @patch("src.services.cache.get_settings")
    def test_set_without_data_hash(self, mock_settings):
        """InMemoryCache.set without data_hash should store None."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)
        c = InMemoryCache()
        c.set("k", "v")
        entry = c.get_entry("k")
        assert entry is not None
        assert entry.data_hash is None

    @patch("src.services.cache.get_settings")
    def test_overwrite_preserves_new_hash(self, mock_settings):
        """Overwriting a cache key should update the data_hash."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)
        c = InMemoryCache()
        c.set("k", "v1", data_hash="old_hash")
        c.set("k", "v2", data_hash="new_hash")
        entry = c.get_entry("k")
        assert entry is not None
        assert entry.data_hash == "new_hash"

    @patch("src.services.cache.get_settings")
    def test_get_entry_returns_data_hash(self, mock_settings):
        """get_entry should expose data_hash for change-detection consumers."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)
        c = InMemoryCache()
        h = compute_data_hash({"columns": [{"name": "Todo"}]})
        c.set("board:1", {"columns": [{"name": "Todo"}]}, data_hash=h)
        entry = c.get_entry("board:1")
        assert entry is not None
        assert entry.data_hash == h


class TestCacheClearExpiredSafety:
    """Regression test: clear_expired must not raise KeyError when entries
    are concurrently removed (bug-bash fix)."""

    @patch("src.services.cache.get_settings")
    def test_clear_expired_tolerates_missing_key(self, mock_settings):
        """If a key disappears between snapshot and deletion, no KeyError."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=0)
        cache = InMemoryCache()
        cache.set("k1", "v1", ttl_seconds=0)

        time.sleep(0.01)

        class _DelRaisesDict(dict):
            def __delitem__(self, key):
                raise KeyError(key)

        cache._cache = _DelRaisesDict(cache._cache)

        # Should NOT raise KeyError even if __delitem__ would fail.
        removed = cache.clear_expired()
        assert removed == 1

    @patch("src.services.cache.get_settings")
    def test_get_expired_entry_uses_pop(self, mock_settings):
        """Expired entry cleanup in get() should not raise KeyError."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=0)
        cache = InMemoryCache()
        cache.set("k1", "v1", ttl_seconds=0)

        time.sleep(0.01)

        # Simulate key already removed
        cache._cache.pop("k1", None)
        cache.set("k1", "v2", ttl_seconds=0)

        time.sleep(0.01)

        # Should return None, not raise
        assert cache.get("k1") is None


class TestCacheWarmPreventsOutboundCalls:
    """Performance regression tests: warm cache should prevent redundant work."""

    @patch("src.services.cache.get_settings")
    def test_warm_cache_returns_value_without_fetch(self, mock_settings):
        """A warm (non-expired) cache entry should be returned directly (SC-001)."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)
        c = InMemoryCache()
        c.set("board:proj1", {"columns": []}, ttl_seconds=300)

        result = c.get("board:proj1")
        assert result == {"columns": []}

    @patch("src.services.cache.get_settings")
    def test_stale_cache_available_after_expiry(self, mock_settings):
        """After TTL expires, get_stale should still return the value even when
        get() has not been called (entry is still in the internal store)."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=0)
        c = InMemoryCache()
        c.set("board:proj1", {"columns": []}, ttl_seconds=0)

        time.sleep(0.01)

        # get_stale() returns the value even though TTL expired — this is the
        # stale-fallback path used by WebSocket periodic checks and error fallback.
        assert c.get_stale("board:proj1") == {"columns": []}

    @patch("src.services.cache.get_settings")
    def test_ttl_alignment_with_board_cache(self, mock_settings):
        """Board cache TTL should be settable to 300s to align with frontend auto-refresh."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=60)
        c = InMemoryCache()
        c.set("board_data:proj1", {"columns": []}, ttl_seconds=300)

        entry = c.get_entry("board_data:proj1")
        assert entry is not None
        # TTL should be 300s, not the default 60s
        remaining = (entry.expires_at - utcnow()).total_seconds()
        assert 295 <= remaining <= 305

    @patch("src.services.cache.get_settings")
    def test_hash_based_change_detection_ttl_refresh(self, mock_settings):
        """Unchanged data (same hash) should allow TTL refresh without replacing value (T048)."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)
        c = InMemoryCache()

        data = {"columns": [{"name": "Backlog"}]}
        data_hash = compute_data_hash(data)
        c.set("board:proj1", data, data_hash=data_hash)

        entry_before = c.get_entry("board:proj1")
        assert entry_before is not None
        original_expires = entry_before.expires_at

        time.sleep(0.01)
        c.refresh_ttl("board:proj1")

        entry_after = c.get_entry("board:proj1")
        assert entry_after is not None
        # TTL refreshed — new expiry is later
        assert entry_after.expires_at > original_expires
        # Data hash preserved
        assert entry_after.data_hash == data_hash
        # Value unchanged
        assert entry_after.value == data

    @patch("src.services.cache.get_settings")
    def test_300s_ttl_aligns_with_frontend_auto_refresh(self, mock_settings):
        """Board data cache uses 300-second TTL consistent with frontend (T048/SC-002)."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)
        c = InMemoryCache()

        c.set("board_data:proj1", {"columns": []})
        entry = c.get_entry("board_data:proj1")
        assert entry is not None
        remaining = (entry.expires_at - utcnow()).total_seconds()
        assert 295 <= remaining <= 305

    @patch("src.services.cache.get_settings")
    def test_refresh_ttl_returns_false_for_missing_key(self, mock_settings):
        """refresh_ttl() should return False when key does not exist (T016)."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)
        c = InMemoryCache()

        assert c.refresh_ttl("nonexistent:key") is False

    @patch("src.services.cache.get_settings")
    def test_refresh_ttl_preserves_etag_and_last_modified(self, mock_settings):
        """refresh_ttl() should preserve all metadata (etag, last_modified, data_hash) (T016)."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)
        c = InMemoryCache()

        c.set("k", "val", etag='"abc"', last_modified="Mon, 01 Jan 2024", data_hash="hash123")
        time.sleep(0.01)
        assert c.refresh_ttl("k") is True

        entry = c.get_entry("k")
        assert entry is not None
        assert entry.etag == '"abc"'
        assert entry.last_modified == "Mon, 01 Jan 2024"
        assert entry.data_hash == "hash123"
        assert entry.value == "val"


class TestCachedFetchExtensions:
    """Tests for cached_fetch() rate_limit_fallback and data_hash_fn extensions."""

    @patch("src.services.cache.get_settings")
    @pytest.mark.asyncio
    async def test_rate_limit_fallback_returns_stale_on_rate_limit(self, mock_settings):
        """When rate_limit_fallback=True and RateLimitError raised, return stale data."""
        from src.exceptions import RateLimitError
        from src.services.cache import cached_fetch

        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)
        c = InMemoryCache()
        # Seed data that will become stale before fetch is attempted
        c.set("k", "stale_value", ttl_seconds=1)
        time.sleep(1.1)

        async def fetch_fn():
            raise RateLimitError("rate limited")

        result = await cached_fetch(c, "k", fetch_fn, rate_limit_fallback=True, refresh=True)
        assert result == "stale_value"

    @patch("src.services.cache.get_settings")
    @pytest.mark.asyncio
    async def test_rate_limit_fallback_reraises_when_no_stale(self, mock_settings):
        """When rate_limit_fallback=True but no stale data, re-raise RateLimitError."""
        from src.exceptions import RateLimitError
        from src.services.cache import cached_fetch

        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)
        c = InMemoryCache()

        async def fetch_fn():
            raise RateLimitError("rate limited")

        with pytest.raises(RateLimitError):
            await cached_fetch(c, "k", fetch_fn, rate_limit_fallback=True)

    @patch("src.services.cache.get_settings")
    @pytest.mark.asyncio
    async def test_data_hash_fn_refreshes_ttl_on_unchanged_data(self, mock_settings):
        """When data_hash_fn hash matches cached hash, refresh_ttl instead of set."""
        from src.services.cache import cached_fetch

        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)
        c = InMemoryCache()
        data = {"key": "value"}
        data_hash = compute_data_hash(data)
        c.set("k", data, data_hash=data_hash)

        entry_before = c.get_entry("k")
        assert entry_before is not None
        original_expires = entry_before.expires_at

        time.sleep(0.01)

        async def fetch_fn():
            return {"key": "value"}

        result = await cached_fetch(c, "k", fetch_fn, refresh=True, data_hash_fn=compute_data_hash)
        assert result == {"key": "value"}

        entry_after = c.get_entry("k")
        assert entry_after is not None
        # TTL should be refreshed (later expiry)
        assert entry_after.expires_at > original_expires
        # Hash preserved
        assert entry_after.data_hash == data_hash

    @patch("src.services.cache.get_settings")
    @pytest.mark.asyncio
    async def test_data_hash_fn_stores_on_different_hash(self, mock_settings):
        """When data_hash_fn hash differs from cached hash, full set() is called."""
        from src.services.cache import cached_fetch

        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)
        c = InMemoryCache()
        old_data = {"key": "old"}
        c.set("k", old_data, data_hash=compute_data_hash(old_data))

        new_data = {"key": "new"}

        async def fetch_fn():
            return new_data

        result = await cached_fetch(c, "k", fetch_fn, refresh=True, data_hash_fn=compute_data_hash)
        assert result == new_data

        entry = c.get_entry("k")
        assert entry is not None
        assert entry.value == new_data
        assert entry.data_hash == compute_data_hash(new_data)

    @patch("src.services.cache.get_settings")
    @pytest.mark.asyncio
    async def test_backward_compatibility_no_new_params(self, mock_settings):
        """Existing callers without new params should work identically."""
        from src.services.cache import cached_fetch

        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)
        c = InMemoryCache()

        async def fetch_fn():
            return "fresh_data"

        result = await cached_fetch(c, "k", fetch_fn)
        assert result == "fresh_data"
        assert c.get("k") == "fresh_data"

    @patch("src.services.cache.get_settings")
    @pytest.mark.asyncio
    async def test_stale_fallback_still_works(self, mock_settings):
        """stale_fallback should still work without rate_limit_fallback."""
        from src.services.cache import cached_fetch

        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)
        c = InMemoryCache()
        c.set("k", "stale", ttl_seconds=0)
        time.sleep(0.01)

        async def fetch_fn():
            raise ValueError("fetch failed")

        result = await cached_fetch(c, "k", fetch_fn, stale_fallback=True)
        assert result == "stale"
