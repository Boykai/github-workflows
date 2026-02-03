"""Unit tests for cache service."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import time

from src.services.cache import CacheEntry, InMemoryCache


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


class TestInMemoryCache:
    """Tests for InMemoryCache class."""

    @patch('src.services.cache.get_settings')
    def test_get_returns_none_for_missing_key(self, mock_settings):
        """Should return None for non-existent key."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)
        
        cache = InMemoryCache()
        
        assert cache.get("nonexistent_key") is None

    @patch('src.services.cache.get_settings')
    def test_set_and_get_value(self, mock_settings):
        """Should store and retrieve value."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)
        
        cache = InMemoryCache()
        cache.set("test_key", "test_value")
        
        assert cache.get("test_key") == "test_value"

    @patch('src.services.cache.get_settings')
    def test_set_with_custom_ttl(self, mock_settings):
        """Should accept custom TTL."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)
        
        cache = InMemoryCache()
        cache.set("test_key", "test_value", ttl_seconds=600)
        
        assert cache.get("test_key") == "test_value"

    @patch('src.services.cache.get_settings')
    def test_get_returns_none_for_expired_entry(self, mock_settings):
        """Should return None and delete expired entries."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)
        
        cache = InMemoryCache()
        cache.set("test_key", "test_value", ttl_seconds=1)
        
        # Wait for entry to expire
        time.sleep(1.1)
        assert cache.get("test_key") is None

    @patch('src.services.cache.get_settings')
    def test_delete_removes_entry(self, mock_settings):
        """Should delete entry from cache."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)
        
        cache = InMemoryCache()
        cache.set("test_key", "test_value")
        
        result = cache.delete("test_key")
        
        assert result is True
        assert cache.get("test_key") is None

    @patch('src.services.cache.get_settings')
    def test_delete_returns_false_for_missing_key(self, mock_settings):
        """Should return False when deleting non-existent key."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)
        
        cache = InMemoryCache()
        
        result = cache.delete("nonexistent_key")
        
        assert result is False

    @patch('src.services.cache.get_settings')
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

    @patch('src.services.cache.get_settings')
    def test_overwrite_existing_key(self, mock_settings):
        """Should overwrite existing key with new value."""
        mock_settings.return_value = MagicMock(cache_ttl_seconds=300)
        
        cache = InMemoryCache()
        
        cache.set("test_key", "original")
        cache.set("test_key", "updated")
        
        assert cache.get("test_key") == "updated"
