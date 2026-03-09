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


class TestSubIssueCacheTTL:
    """T032: Sub-issue cache entries served from cache within 600s TTL window."""

    @patch("src.services.cache.get_settings")
    def test_sub_issue_cache_served_within_ttl(self, mock_settings):
        """Cache entry with 600s TTL should be retrievable before expiration."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)

        cache = InMemoryCache()
        sub_issues_data = [{"id": 1, "title": "Sub-issue 1", "state": "open"}]
        cache.set("sub_issues:testuser/testrepo#42", sub_issues_data, ttl_seconds=600)

        # Entry should be retrievable within TTL window
        assert cache.get("sub_issues:testuser/testrepo#42") == sub_issues_data

    @patch("src.services.cache.get_settings")
    def test_sub_issue_cache_expired_after_ttl(self, mock_settings):
        """Cache entry should expire after its TTL."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)

        cache = InMemoryCache()
        sub_issues_data = [{"id": 1, "title": "Sub-issue 1", "state": "open"}]
        cache.set("sub_issues:testuser/testrepo#42", sub_issues_data, ttl_seconds=1)

        time.sleep(1.1)
        assert cache.get("sub_issues:testuser/testrepo#42") is None


class TestCacheTTLExpiration:
    """T049: Cache TTL expiration — entries evicted after TTL, fresh data fetched."""

    @patch("src.services.cache.get_settings")
    def test_entry_evicted_after_ttl(self, mock_settings):
        """Entry should be None after TTL expires."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)

        cache = InMemoryCache()
        cache.set("board_data:PVT_123", {"project": {}, "columns": []}, ttl_seconds=1)

        # Should exist immediately
        assert cache.get("board_data:PVT_123") is not None

        # Wait for TTL to expire
        time.sleep(1.1)

        # Should be evicted
        assert cache.get("board_data:PVT_123") is None

    @patch("src.services.cache.get_settings")
    def test_subsequent_set_after_expiry_stores_fresh_data(self, mock_settings):
        """After TTL expires, a new set() stores fresh data."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)

        cache = InMemoryCache()
        cache.set("key1", "stale_value", ttl_seconds=1)

        time.sleep(1.1)
        assert cache.get("key1") is None

        # Store fresh data
        cache.set("key1", "fresh_value", ttl_seconds=300)
        assert cache.get("key1") == "fresh_value"

    @patch("src.services.cache.get_settings")
    def test_stale_cache_fallback_via_get_stale(self, mock_settings):
        """get_stale() should return expired entries for fallback scenarios."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)

        cache = InMemoryCache()
        cache.set("fallback_key", "stale_data", ttl_seconds=1)

        time.sleep(1.1)

        # get_stale returns the stale entry value even though it's expired
        # (must be called BEFORE get() which would evict the entry)
        stale = cache.get_stale("fallback_key")
        assert stale == "stale_data"

        # Regular get returns None (expired) and evicts the entry
        assert cache.get("fallback_key") is None
