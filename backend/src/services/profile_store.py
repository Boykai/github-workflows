"""Profile data persistence for user_profiles table."""

import logging
from datetime import UTC, datetime

import aiosqlite

from src.models.user import UserProfile, UserProfileUpdate

logger = logging.getLogger(__name__)

_table_ensured = False


async def ensure_table(db: aiosqlite.Connection) -> None:
    """Create user_profiles table if not exists (lazy initialization)."""
    global _table_ensured
    if _table_ensured:
        return

    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS user_profiles (
            github_user_id TEXT PRIMARY KEY,
            display_name TEXT,
            bio TEXT,
            avatar_path TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_user_profiles_updated
            ON user_profiles(updated_at)
        """
    )
    await db.commit()
    _table_ensured = True


async def get_profile(db: aiosqlite.Connection, github_user_id: str) -> UserProfile | None:
    """Fetch profile by GitHub user ID. Returns None if not found."""
    await ensure_table(db)

    cursor = await db.execute(
        "SELECT github_user_id, display_name, bio, avatar_path, created_at, updated_at "
        "FROM user_profiles WHERE github_user_id = ?",
        (github_user_id,),
    )
    row = await cursor.fetchone()
    if row is None:
        return None

    return UserProfile(
        github_user_id=row["github_user_id"],
        display_name=row["display_name"],
        bio=row["bio"],
        avatar_path=row["avatar_path"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


async def upsert_profile(
    db: aiosqlite.Connection, github_user_id: str, update: UserProfileUpdate
) -> UserProfile:
    """Create or update profile fields. Preserves existing fields not in update."""
    await ensure_table(db)

    now = datetime.now(UTC).isoformat()

    # Read existing profile to merge
    existing = await get_profile(db, github_user_id)

    display_name = update.display_name if update.display_name is not None else (
        existing.display_name if existing else None
    )
    bio = update.bio if update.bio is not None else (
        existing.bio if existing else None
    )
    avatar_path = existing.avatar_path if existing else None
    created_at = existing.created_at.isoformat() if existing else now

    await db.execute(
        """
        INSERT INTO user_profiles (github_user_id, display_name, bio, avatar_path, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(github_user_id) DO UPDATE SET
            display_name = excluded.display_name,
            bio = excluded.bio,
            updated_at = excluded.updated_at
        """,
        (github_user_id, display_name, bio, avatar_path, created_at, now),
    )
    await db.commit()

    result = await get_profile(db, github_user_id)
    assert result is not None
    return result


async def update_avatar_path(
    db: aiosqlite.Connection, github_user_id: str, avatar_path: str | None
) -> None:
    """Update the avatar_path field for a user."""
    await ensure_table(db)

    now = datetime.now(UTC).isoformat()

    # Ensure profile row exists
    existing = await get_profile(db, github_user_id)
    if existing is None:
        await db.execute(
            """
            INSERT INTO user_profiles (github_user_id, avatar_path, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (github_user_id, avatar_path, now, now),
        )
    else:
        await db.execute(
            "UPDATE user_profiles SET avatar_path = ?, updated_at = ? WHERE github_user_id = ?",
            (avatar_path, now, github_user_id),
        )
    await db.commit()
