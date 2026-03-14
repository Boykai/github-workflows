"""Unit tests for session store CRUD operations.

Covers:
- save_session()
- get_session()
- delete_session()
- get_sessions_by_user()
- purge_expired_sessions()
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch
from uuid import uuid4

from src.models.user import UserSession
from src.services.session_store import (
    delete_session,
    get_session,
    get_sessions_by_user,
    purge_expired_sessions,
    save_session,
)


def _make_session(**overrides) -> UserSession:
    """Create a UserSession with deterministic defaults."""
    defaults = {
        "session_id": uuid4(),
        "github_user_id": "u123",
        "github_username": "testuser",
        "access_token": "tok",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    return UserSession(**defaults)


# =============================================================================
# save_session + get_session roundtrip
# =============================================================================


class TestSaveAndGetSession:
    async def test_roundtrip(self, mock_db, mock_settings):
        session = _make_session()
        await save_session(mock_db, session)

        with patch("src.services.session_store.get_settings", return_value=mock_settings):
            loaded = await get_session(mock_db, session.session_id)

        assert loaded is not None
        assert loaded.session_id == session.session_id
        assert loaded.github_user_id == session.github_user_id
        assert loaded.github_username == session.github_username
        assert loaded.access_token == session.access_token

    async def test_upsert_replaces(self, mock_db, mock_settings):
        sid = uuid4()
        s1 = _make_session(session_id=sid, access_token="old")
        s2 = _make_session(session_id=sid, access_token="new")
        await save_session(mock_db, s1)
        await save_session(mock_db, s2)

        with patch("src.services.session_store.get_settings", return_value=mock_settings):
            loaded = await get_session(mock_db, sid)
        assert loaded is not None
        assert loaded.access_token == "new"

    async def test_get_nonexistent_returns_none(self, mock_db, mock_settings):
        with patch("src.services.session_store.get_settings", return_value=mock_settings):
            assert await get_session(mock_db, uuid4()) is None


# =============================================================================
# Expiry
# =============================================================================


class TestSessionExpiry:
    async def test_expired_session_returns_none(self, mock_db, mock_settings):
        """A session whose updated_at + expire_hours < now should not be returned."""
        old_time = datetime.now(UTC) - timedelta(hours=mock_settings.session_expire_hours + 1)
        session = _make_session(updated_at=old_time, created_at=old_time)
        await save_session(mock_db, session)

        with patch("src.services.session_store.get_settings", return_value=mock_settings):
            loaded = await get_session(mock_db, session.session_id)
        assert loaded is None

    async def test_not_yet_expired_returns_session(self, mock_db, mock_settings):
        recent_time = datetime.now(UTC) - timedelta(hours=1)
        session = _make_session(updated_at=recent_time, created_at=recent_time)
        await save_session(mock_db, session)

        with patch("src.services.session_store.get_settings", return_value=mock_settings):
            loaded = await get_session(mock_db, session.session_id)
        assert loaded is not None


# =============================================================================
# delete_session
# =============================================================================


class TestDeleteSession:
    async def test_deletes_existing(self, mock_db):
        session = _make_session()
        await save_session(mock_db, session)
        result = await delete_session(mock_db, session.session_id)
        assert result is True

    async def test_returns_false_for_missing(self, mock_db):
        result = await delete_session(mock_db, uuid4())
        assert result is False


# =============================================================================
# get_sessions_by_user
# =============================================================================


class TestGetSessionsByUser:
    async def test_returns_matching(self, mock_db):
        s1 = _make_session(github_user_id="u1")
        s2 = _make_session(github_user_id="u1")
        s3 = _make_session(github_user_id="u2")
        for s in (s1, s2, s3):
            await save_session(mock_db, s)
        sessions = await get_sessions_by_user(mock_db, "u1")
        assert len(sessions) == 2
        assert all(s.github_user_id == "u1" for s in sessions)

    async def test_empty_for_unknown_user(self, mock_db):
        sessions = await get_sessions_by_user(mock_db, "nobody")
        assert sessions == []


# =============================================================================
# purge_expired_sessions
# =============================================================================


class TestPurgeExpiredSessions:
    async def test_purges_old_sessions(self, mock_db, mock_settings):
        old = _make_session(
            updated_at=datetime.now(UTC) - timedelta(hours=mock_settings.session_expire_hours + 1),
            created_at=datetime.now(UTC) - timedelta(hours=mock_settings.session_expire_hours + 1),
        )
        fresh = _make_session()
        await save_session(mock_db, old)
        await save_session(mock_db, fresh)

        with patch("src.services.session_store.get_settings", return_value=mock_settings):
            purged = await purge_expired_sessions(mock_db)
        assert purged == 1

        # Fresh session should still exist
        with patch("src.services.session_store.get_settings", return_value=mock_settings):
            loaded = await get_session(mock_db, fresh.session_id)
        assert loaded is not None

    async def test_purge_returns_zero_when_none_expired(self, mock_db, mock_settings):
        fresh = _make_session()
        await save_session(mock_db, fresh)
        with patch("src.services.session_store.get_settings", return_value=mock_settings):
            purged = await purge_expired_sessions(mock_db)
        assert purged == 0
