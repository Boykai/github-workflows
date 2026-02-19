"""Unit tests for cache service."""

import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.services.cache import (
    CacheEntry,
    InMemoryCache,
    get_cache_key,
    get_project_items_cache_key,
    get_user_projects_cache_key,
)


class TestCacheEntry:
    """Tests for CacheEntry class."""

    def test_entry_stores_value(self):
        """Should store value correctly."""
        entry = CacheEntry("test_value", ttl_seconds=60)

        assert entry.value == "test_value"

    def test_entry_calculates_expiration(self):
        """Should calculate expiration time based on TTL."""
        entry = CacheEntry("test_value", ttl_seconds=60)

        expected_min = datetime.utcnow() + timedelta(seconds=59)
        expected_max = datetime.utcnow() + timedelta(seconds=61)

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

    def test_entry_stores_none_value(self):
        """Should store None as a valid value."""
        entry = CacheEntry(None, ttl_seconds=60)

        assert entry.value is None
        assert entry.is_expired is False

    def test_entry_stores_complex_nested_dict(self):
        """Should store complex nested structures."""
        data = {"users": [{"id": 1, "roles": ["admin"]}], "count": 1}
        entry = CacheEntry(data, ttl_seconds=60)

        assert entry.value == data

    def test_entry_with_large_ttl(self):
        """Should handle large TTL values."""
        entry = CacheEntry("val", ttl_seconds=86400)

        expected_min = datetime.utcnow() + timedelta(seconds=86399)
        assert entry.expires_at >= expected_min
        assert entry.is_expired is False


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
    def test_clear_removes_all_entries(self, mock_settings):
        """Should remove all entries from cache."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)

        cache = InMemoryCache()
        cache.set("key1", "val1")
        cache.set("key2", "val2")
        cache.set("key3", "val3")

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") is None

    @patch("src.services.cache.get_settings")
    def test_clear_expired_removes_only_expired(self, mock_settings):
        """Should remove only expired entries and return count."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)

        cache = InMemoryCache()
        cache.set("short_lived", "expires", ttl_seconds=1)
        cache.set("long_lived", "stays", ttl_seconds=600)

        time.sleep(1.1)
        removed = cache.clear_expired()

        assert removed == 1
        assert cache.get("short_lived") is None
        assert cache.get("long_lived") == "stays"

    @patch("src.services.cache.get_settings")
    def test_clear_expired_returns_zero_when_none_expired(self, mock_settings):
        """Should return 0 when no entries are expired."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)

        cache = InMemoryCache()
        cache.set("key1", "val1", ttl_seconds=600)

        removed = cache.clear_expired()

        assert removed == 0

    @patch("src.services.cache.get_settings")
    def test_set_uses_default_ttl_from_settings(self, mock_settings):
        """Should use settings TTL when no custom TTL provided."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=120)

        cache = InMemoryCache()
        cache.set("key", "value")

        # Entry should exist (not expired with 120s TTL)
        assert cache.get("key") == "value"


class TestCacheKeyHelpers:
    """Tests for cache key generation functions."""

    def test_get_cache_key_formats_correctly(self):
        """Should format key as prefix:identifier."""
        result = get_cache_key("users", "123")

        assert result == "users:123"

    def test_get_cache_key_with_empty_identifier(self):
        """Should handle empty identifier."""
        result = get_cache_key("prefix", "")

        assert result == "prefix:"

    def test_get_user_projects_cache_key(self):
        """Should generate correct user projects cache key."""
        result = get_user_projects_cache_key("user_456")

        assert "user_456" in result
        assert ":" in result

    def test_get_project_items_cache_key(self):
        """Should generate correct project items cache key."""
        result = get_project_items_cache_key("proj_789")

        assert "proj_789" in result
        assert ":" in result

    def test_different_users_get_different_keys(self):
        """Should produce unique keys for different users."""
        key1 = get_user_projects_cache_key("user_a")
        key2 = get_user_projects_cache_key("user_b")

        assert key1 != key2

    def test_different_projects_get_different_keys(self):
        """Should produce unique keys for different projects."""
        key1 = get_project_items_cache_key("proj_1")
        key2 = get_project_items_cache_key("proj_2")

        assert key1 != key2
