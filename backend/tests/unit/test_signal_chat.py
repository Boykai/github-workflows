"""Tests for signal_chat.py helpers — _signal_session_id (T101)."""

from uuid import NAMESPACE_URL, uuid5

from src.services.signal_chat import _signal_session_id


class TestSignalSessionId:
    """_signal_session_id returns a deterministic UUID5 for a GitHub user id."""

    def test_returns_expected_uuid(self):
        expected = uuid5(NAMESPACE_URL, "signal:12345")
        assert _signal_session_id("12345") == expected

    def test_deterministic(self):
        """Same input always yields the same UUID."""
        assert _signal_session_id("abc") == _signal_session_id("abc")

    def test_different_ids_differ(self):
        assert _signal_session_id("user-a") != _signal_session_id("user-b")

    def test_empty_string(self):
        expected = uuid5(NAMESPACE_URL, "signal:")
        assert _signal_session_id("") == expected

    def test_return_type_is_uuid(self):
        from uuid import UUID

        result = _signal_session_id("test")
        assert isinstance(result, UUID)
