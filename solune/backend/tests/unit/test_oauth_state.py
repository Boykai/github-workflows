"""Tests for OAuth state management (US1 — FR-006).

Verifies:
- OAuth states auto-expire after 10 minutes
- BoundedDict eviction when capacity is reached
- Expired states cleaned up on access
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from src.services.github_auth import GitHubAuthService


class TestOAuthStateExpiry:
    """OAuth states must be rejected after 10 minutes."""

    async def test_state_valid_within_window(self):
        """A state used within 10 minutes should be accepted."""
        svc = _make_service()
        _url, state = svc.generate_oauth_url()
        assert svc.validate_state(state) is True

    async def test_state_rejected_after_10_minutes(self):
        """A state older than 10 minutes must be rejected."""
        svc = _make_service()
        _url, state = svc.generate_oauth_url()

        # Time-travel: shift the stored timestamp 11 minutes into the past
        from src.services import github_auth as _mod

        _mod._oauth_states[state] = datetime.now(UTC) - timedelta(minutes=11)

        assert svc.validate_state(state) is False

    async def test_state_consumed_on_validate(self):
        """A valid state should only be usable once (consumed on validate)."""
        svc = _make_service()
        _url, state = svc.generate_oauth_url()
        assert svc.validate_state(state) is True
        # Second use must fail
        assert svc.validate_state(state) is False


class TestOAuthStateBounding:
    """_oauth_states must use BoundedDict to prevent unbounded memory growth."""

    async def test_bounded_dict_type(self):
        """_oauth_states must be a BoundedDict, not a plain dict."""
        from src.services import github_auth as _mod
        from src.utils import BoundedDict

        assert isinstance(_mod._oauth_states, BoundedDict), (
            f"Expected BoundedDict, got {type(_mod._oauth_states).__name__}"
        )

    async def test_eviction_at_capacity(self):
        """When capacity is reached, oldest states should be evicted."""
        from src.utils import BoundedDict

        # Create a small BoundedDict to test eviction
        states: BoundedDict[str, datetime] = BoundedDict(maxlen=3)
        states["a"] = datetime.now(UTC)
        states["b"] = datetime.now(UTC)
        states["c"] = datetime.now(UTC)

        assert len(states) == 3
        assert "a" in states

        # Adding a 4th should evict "a" (oldest)
        states["d"] = datetime.now(UTC)
        assert len(states) == 3
        assert "a" not in states
        assert "d" in states

    async def test_bounded_dict_maxlen_at_least_1000(self):
        """The production _oauth_states should have maxlen >= 1000."""
        from src.services import github_auth as _mod
        from src.utils import BoundedDict

        states = _mod._oauth_states
        if isinstance(states, BoundedDict):
            assert states.maxlen >= 1000, f"Expected maxlen >= 1000, got {states.maxlen}"
        else:
            # Will be caught by test_bounded_dict_type
            pass


class TestOAuthStateCleanupOnAccess:
    """Expired states should be cleaned up when new states are generated."""

    async def test_expired_states_pruned(self):
        """Generating a new OAuth URL should remove expired states."""
        from src.services import github_auth as _mod

        svc = _make_service()

        # Manually insert expired states
        expired_time = datetime.now(UTC) - timedelta(minutes=15)
        _mod._oauth_states["expired_1"] = expired_time
        _mod._oauth_states["expired_2"] = expired_time

        # Generate a new URL — should trigger cleanup of expired entries
        svc.generate_oauth_url()

        # After cleanup, expired entries should be gone
        assert "expired_1" not in _mod._oauth_states
        assert "expired_2" not in _mod._oauth_states


# ── Helpers ─────────────────────────────────────────────────────────────────


def _make_service() -> GitHubAuthService:
    """Create a GitHubAuthService with test settings."""
    with patch("src.services.github_auth.get_settings") as mock:
        mock.return_value.github_client_id = "test-id"
        mock.return_value.github_client_secret = "test-secret"
        mock.return_value.github_redirect_uri = "http://localhost/callback"
        svc = GitHubAuthService()
    return svc
