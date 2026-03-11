"""Unit tests for cache service."""

import time
from datetime import timedelta
from unittest.mock import MagicMock, patch

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

    def test_entry_stores_data_hash(self):
        """Should store data_hash when provided."""
        entry = CacheEntry("test_value", ttl_seconds=60, data_hash="abc123")
        assert entry.data_hash == "abc123"

    def test_entry_data_hash_defaults_to_none(self):
        """Should default data_hash to None when not provided."""
        entry = CacheEntry("test_value", ttl_seconds=60)
        assert entry.data_hash is None


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

    @patch("src.services.cache.get_settings")
    def test_set_stores_data_hash(self, mock_settings):
        """Should store data_hash when provided via set()."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)

        cache = InMemoryCache()
        cache.set("test_key", "value", data_hash="hash123")

        entry = cache.get_entry("test_key")
        assert entry is not None
        assert entry.data_hash == "hash123"

    @patch("src.services.cache.get_settings")
    def test_data_hash_detects_changes(self, mock_settings):
        """Overwriting with different data_hash reflects the new hash."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)

        cache = InMemoryCache()
        cache.set("board", {"columns": [1]}, data_hash="hash_v1")
        cache.set("board", {"columns": [1, 2]}, data_hash="hash_v2")

        entry = cache.get_entry("board")
        assert entry is not None
        assert entry.data_hash == "hash_v2"


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
