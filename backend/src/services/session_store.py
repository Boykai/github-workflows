"""Database-backed session store replacing in-memory session dict."""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

import aiosqlite

from src.config import get_settings
from src.models.user import UserSession

logger = logging.getLogger(__name__)


def _row_to_session(row: aiosqlite.Row) -> UserSession:
    """Convert a database row to a ``UserSession`` instance.

    Centralises the column→field mapping so ``get_session()`` and
    ``get_sessions_by_user()`` stay in sync.
    """
    token_expires = (
        datetime.fromisoformat(row["token_expires_at"]) if row["token_expires_at"] else None
    )
    updated_at = datetime.fromisoformat(row["updated_at"])
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=UTC)

    return UserSession(
        session_id=UUID(row["session_id"]),
        github_user_id=row["github_user_id"],
        github_username=row["github_username"],
        github_avatar_url=row["github_avatar_url"],
        access_token=row["access_token"],
        refresh_token=row["refresh_token"],
        token_expires_at=token_expires,
        selected_project_id=row["selected_project_id"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=updated_at,
    )


async def save_session(db: aiosqlite.Connection, session: UserSession) -> None:
    """
    Persist a session to the database (INSERT OR REPLACE).

    Args:
        db: Database connection
        session: UserSession to persist
    """
    logger.debug("Saving session %s for user %s", session.session_id, session.github_username)
    await db.execute(
        """
        INSERT OR REPLACE INTO user_sessions (
            session_id, github_user_id, github_username, github_avatar_url,
            access_token, refresh_token, token_expires_at,
            selected_project_id, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(session.session_id),
            session.github_user_id,
            session.github_username,
            session.github_avatar_url,
            session.access_token,
            session.refresh_token,
            session.token_expires_at.isoformat() if session.token_expires_at else None,
            session.selected_project_id,
            session.created_at.isoformat(),
            session.updated_at.isoformat(),
        ),
    )
    await db.commit()


async def get_session(db: aiosqlite.Connection, session_id: str | UUID) -> UserSession | None:
    """
    Load a session by ID. Returns None if not found or expired.

    Expired sessions are lazily deleted on access (FR-012).
    """
    sid = str(session_id)
    logger.debug("Looking up session %s", sid)

    cursor = await db.execute("SELECT * FROM user_sessions WHERE session_id = ?", (sid,))
    row = await cursor.fetchone()

    if row is None:
        logger.debug("Session %s not found", sid)
        return None

    # Check expiry: session is expired if updated_at + session_expire_hours < now
    settings = get_settings()
    updated_at = datetime.fromisoformat(row["updated_at"])
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=UTC)
    expiry = updated_at + timedelta(hours=settings.session_expire_hours)

    if datetime.now(UTC) > expiry:
        logger.debug("Session %s expired, deleting", sid)
        await delete_session(db, sid)
        return None

    # Reconstruct UserSession from row
    return _row_to_session(row)


async def delete_session(db: aiosqlite.Connection, session_id: str | UUID) -> bool:
    """
    Delete a session by ID. Returns True if a row was deleted.
    """
    sid = str(session_id)
    logger.debug("Deleting session %s", sid)
    cursor = await db.execute("DELETE FROM user_sessions WHERE session_id = ?", (sid,))
    await db.commit()
    return cursor.rowcount > 0


async def get_sessions_by_user(db: aiosqlite.Connection, github_user_id: str) -> list[UserSession]:
    """
    Get all sessions for a given GitHub user ID.
    """
    logger.debug("Looking up sessions for user %s", github_user_id)
    cursor = await db.execute(
        "SELECT * FROM user_sessions WHERE github_user_id = ?", (github_user_id,)
    )
    rows = await cursor.fetchall()

    sessions = []
    for row in rows:
        sessions.append(_row_to_session(row))
    return sessions


async def purge_expired_sessions(db: aiosqlite.Connection) -> int:
    """
    Delete all expired sessions from the database.

    Returns the number of sessions purged.
    """
    settings = get_settings()
    cutoff = (datetime.now(UTC) - timedelta(hours=settings.session_expire_hours)).isoformat()

    cursor = await db.execute("DELETE FROM user_sessions WHERE updated_at < ?", (cutoff,))
    await db.commit()
    count = cursor.rowcount
    logger.debug("Purged %d expired sessions", count)
    return count
