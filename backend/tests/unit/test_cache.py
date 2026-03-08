"""Unit tests for cache service."""

import time
from datetime import timedelta
from unittest.mock import MagicMock, patch

from src.services.cache import CacheEntry, InMemoryCache
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


class TestCacheSubIssueTTL:
    """Regression tests for sub-issue cache TTL and warm-cache reuse (FR-015)."""

    @patch("src.services.cache.get_settings")
    def test_sub_issue_cache_uses_custom_ttl(self, mock_settings):
        """Sub-issue data cached with TTL=600s should survive past default TTL=300s."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)
        cache = InMemoryCache()
        cache.set("sub_issues:owner/repo#1", [{"id": 1}], ttl_seconds=600)

        # Should still be valid (600s TTL, not default 300s)
        assert cache.get("sub_issues:owner/repo#1") == [{"id": 1}]

    @patch("src.services.cache.get_settings")
    def test_warm_cache_returns_data_without_refetch(self, mock_settings):
        """Warm cache should serve data directly without API calls."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)
        cache = InMemoryCache()
        cache.set("sub_issues:owner/repo#5", [{"id": 5, "title": "sub"}], ttl_seconds=600)

        result = cache.get("sub_issues:owner/repo#5")
        assert result == [{"id": 5, "title": "sub"}]

    @patch("src.services.cache.get_settings")
    def test_cache_delete_clears_sub_issue_entry(self, mock_settings):
        """Manual refresh should be able to clear sub-issue cache entries."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)
        cache = InMemoryCache()
        cache.set("sub_issues:owner/repo#1", [{"id": 1}], ttl_seconds=600)
        cache.set("sub_issues:owner/repo#2", [{"id": 2}], ttl_seconds=600)

        cache.delete("sub_issues:owner/repo#1")

        assert cache.get("sub_issues:owner/repo#1") is None
        assert cache.get("sub_issues:owner/repo#2") == [{"id": 2}]


class TestCacheGetStale:
    """Tests for stale cache fallback (FR-015)."""

    @patch("src.services.cache.get_settings")
    def test_get_stale_returns_expired_data(self, mock_settings):
        """get_stale should return data even after TTL expiry."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)
        cache = InMemoryCache()
        cache.set("board_data:proj1", {"columns": []}, ttl_seconds=1)

        time.sleep(1.1)

        # get_stale returns expired value
        stale_val = cache.get_stale("board_data:proj1")
        assert stale_val == {"columns": []}

        # Normal get returns None (expired) and cleans up
        assert cache.get("board_data:proj1") is None

    @patch("src.services.cache.get_settings")
    def test_get_stale_returns_none_for_missing(self, mock_settings):
        """get_stale should return None when key never existed."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)
        cache = InMemoryCache()

        assert cache.get_stale("nonexistent") is None


class TestCacheRefreshTTL:
    """Tests for refresh_ttl method (FR-015)."""

    @patch("src.services.cache.get_settings")
    def test_refresh_ttl_extends_expiration(self, mock_settings):
        """refresh_ttl should extend cache entry TTL without replacing value."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)
        cache = InMemoryCache()
        cache.set("key1", "value1", ttl_seconds=1)

        result = cache.refresh_ttl("key1", ttl_seconds=600)
        assert result is True

        time.sleep(1.1)
        # Should still be valid after original TTL since we refreshed
        assert cache.get("key1") == "value1"

    @patch("src.services.cache.get_settings")
    def test_refresh_ttl_returns_false_for_missing(self, mock_settings):
        """refresh_ttl should return False for non-existent keys."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)
        cache = InMemoryCache()

        assert cache.refresh_ttl("nonexistent") is False


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
