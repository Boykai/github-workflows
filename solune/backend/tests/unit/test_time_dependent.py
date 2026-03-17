"""Time-controlled tests — verify temporal behavior at exact boundaries."""

import pytest
from freezegun import freeze_time

from src.services.chores.chat import (
    _MAX_AGE_SECONDS,
    _conversations,
    _evict_stale_conversations,
    get_or_create_conversation,
)


@pytest.fixture(autouse=True)
def _clear_conversations():
    """Ensure conversation store is empty before/after each test."""
    _conversations.clear()
    yield
    _conversations.clear()


class TestConversationEviction:
    """Verify that stale conversations are evicted based on _MAX_AGE_SECONDS."""

    @freeze_time("2025-01-15 12:00:00", tz_offset=0)
    def test_fresh_conversation_not_evicted(self) -> None:
        """A conversation created now should survive eviction."""
        cid, _ = get_or_create_conversation(None)
        assert cid in _conversations

        _evict_stale_conversations()
        assert cid in _conversations, "Fresh conversation was incorrectly evicted"

    def test_expired_conversation_evicted(self) -> None:
        """A conversation older than _MAX_AGE_SECONDS should be evicted."""
        with freeze_time("2025-01-15 12:00:00", tz_offset=0):
            cid, _ = get_or_create_conversation(None)

        # Advance past the expiry boundary
        with freeze_time("2025-01-15 13:00:01", tz_offset=0):
            _evict_stale_conversations()
            assert cid not in _conversations, "Expired conversation was not evicted"

    def test_conversation_at_exact_boundary_not_evicted(self) -> None:
        """A conversation at exactly _MAX_AGE_SECONDS should NOT be evicted (≤ not <)."""
        with freeze_time("2025-01-15 12:00:00", tz_offset=0):
            cid, _ = get_or_create_conversation(None)

        # Advance to exactly the boundary (3600 seconds)
        with freeze_time("2025-01-15 13:00:00", tz_offset=0):
            _evict_stale_conversations()
            assert cid in _conversations, "Conversation at exact boundary was evicted"

    def test_mixed_ages_only_old_evicted(self) -> None:
        """Only conversations past the age limit are evicted."""
        with freeze_time("2025-01-15 10:00:00", tz_offset=0):
            old_cid, _ = get_or_create_conversation(None)

        with freeze_time("2025-01-15 12:30:00", tz_offset=0):
            new_cid, _ = get_or_create_conversation(None)

        with freeze_time("2025-01-15 13:00:01", tz_offset=0):
            _evict_stale_conversations()
            assert old_cid not in _conversations, "Old conversation should be evicted"
            assert new_cid in _conversations, "Recent conversation should survive"


class TestCacheEntryExpiry:
    """Verify CacheEntry TTL behavior."""

    def test_cache_entry_not_expired_within_ttl(self) -> None:
        from src.services.cache import CacheEntry

        with freeze_time("2025-01-15 12:00:00", tz_offset=0):
            entry = CacheEntry(value="data", ttl_seconds=300)

        with freeze_time("2025-01-15 12:04:59", tz_offset=0):
            assert not entry.is_expired, "Entry should be valid within TTL"

    def test_cache_entry_expired_after_ttl(self) -> None:
        from src.services.cache import CacheEntry

        with freeze_time("2025-01-15 12:00:00", tz_offset=0):
            entry = CacheEntry(value="data", ttl_seconds=300)

        with freeze_time("2025-01-15 12:05:01", tz_offset=0):
            assert entry.is_expired, "Entry should be expired after TTL"


class TestMaxAgeConstant:
    """Sanity check on the eviction constant."""

    def test_max_age_is_one_hour(self) -> None:
        assert _MAX_AGE_SECONDS == 3600
