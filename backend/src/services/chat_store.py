"""Chat persistence — SQLite-backed message, proposal, and recommendation storage.

Replaces the in-memory dict storage in ``api/chat.py`` with durable SQLite
persistence using the tables created by ``012_chat_persistence.sql``.
"""

from __future__ import annotations

import aiosqlite

from src.logging_utils import get_logger

logger = get_logger(__name__)


# ── Messages ─────────────────────────────────────────────────────


async def save_message(
    db: aiosqlite.Connection,
    session_id: str,
    message_id: str,
    sender_type: str,
    content: str,
    action_type: str | None = None,
    action_data: str | None = None,
) -> None:
    """Persist a chat message to SQLite."""
    await db.execute(
        """INSERT OR REPLACE INTO chat_messages
           (message_id, session_id, sender_type, content, action_type, action_data)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (message_id, session_id, sender_type, content, action_type, action_data),
    )
    await db.commit()


async def get_messages(
    db: aiosqlite.Connection,
    session_id: str,
) -> list[dict]:
    """Retrieve all messages for a session, ordered by timestamp."""
    cursor = await db.execute(
        """SELECT message_id, session_id, sender_type, content,
                  action_type, action_data, timestamp
           FROM chat_messages WHERE session_id = ? ORDER BY timestamp""",
        (session_id,),
    )
    rows = await cursor.fetchall()
    result = []
    for row in rows:
        if isinstance(row, tuple):
            result.append(
                {
                    "message_id": row[0],
                    "session_id": row[1],
                    "sender_type": row[2],
                    "content": row[3],
                    "action_type": row[4],
                    "action_data": row[5],
                    "timestamp": row[6],
                }
            )
        else:
            result.append(dict(row))
    return result


async def clear_messages(
    db: aiosqlite.Connection,
    session_id: str,
) -> None:
    """Delete all messages for a session."""
    await db.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
    await db.commit()


# ── Proposals ────────────────────────────────────────────────────


async def save_proposal(
    db: aiosqlite.Connection,
    session_id: str,
    proposal_id: str,
    original_input: str,
    proposed_title: str,
    proposed_description: str,
) -> None:
    """Persist a chat proposal to SQLite."""
    await db.execute(
        """INSERT OR REPLACE INTO chat_proposals
           (proposal_id, session_id, original_input, proposed_title, proposed_description)
           VALUES (?, ?, ?, ?, ?)""",
        (proposal_id, session_id, original_input, proposed_title, proposed_description),
    )
    await db.commit()


async def get_proposals(
    db: aiosqlite.Connection,
    session_id: str,
) -> list[dict]:
    """Retrieve all proposals for a session, ordered by creation time."""
    cursor = await db.execute(
        """SELECT proposal_id, session_id, original_input, proposed_title,
                  proposed_description, status, edited_title, edited_description,
                  created_at, expires_at
           FROM chat_proposals WHERE session_id = ? ORDER BY created_at""",
        (session_id,),
    )
    rows = await cursor.fetchall()
    result = []
    for row in rows:
        if isinstance(row, tuple):
            result.append(
                {
                    "proposal_id": row[0],
                    "session_id": row[1],
                    "original_input": row[2],
                    "proposed_title": row[3],
                    "proposed_description": row[4],
                    "status": row[5],
                    "edited_title": row[6],
                    "edited_description": row[7],
                    "created_at": row[8],
                    "expires_at": row[9],
                }
            )
        else:
            result.append(dict(row))
    return result


async def update_proposal_status(
    db: aiosqlite.Connection,
    proposal_id: str,
    status: str,
    edited_title: str | None = None,
    edited_description: str | None = None,
) -> None:
    """Update a proposal's status and optional edited fields."""
    if edited_title is not None or edited_description is not None:
        await db.execute(
            """UPDATE chat_proposals
               SET status = ?, edited_title = ?, edited_description = ?
               WHERE proposal_id = ?""",
            (status, edited_title, edited_description, proposal_id),
        )
    else:
        await db.execute(
            "UPDATE chat_proposals SET status = ? WHERE proposal_id = ?",
            (status, proposal_id),
        )
    await db.commit()


# ── Recommendations ──────────────────────────────────────────────


async def save_recommendation(
    db: aiosqlite.Connection,
    session_id: str,
    recommendation_id: str,
    data: str,
) -> None:
    """Persist a chat recommendation to SQLite."""
    await db.execute(
        """INSERT OR REPLACE INTO chat_recommendations
           (recommendation_id, session_id, data)
           VALUES (?, ?, ?)""",
        (recommendation_id, session_id, data),
    )
    await db.commit()


async def get_recommendations(
    db: aiosqlite.Connection,
    session_id: str,
) -> list[dict]:
    """Retrieve all recommendations for a session."""
    cursor = await db.execute(
        """SELECT recommendation_id, session_id, data, status, created_at
           FROM chat_recommendations WHERE session_id = ? ORDER BY created_at""",
        (session_id,),
    )
    rows = await cursor.fetchall()
    result = []
    for row in rows:
        if isinstance(row, tuple):
            result.append(
                {
                    "recommendation_id": row[0],
                    "session_id": row[1],
                    "data": row[2],
                    "status": row[3],
                    "created_at": row[4],
                }
            )
        else:
            result.append(dict(row))
    return result


async def update_recommendation_status(
    db: aiosqlite.Connection,
    recommendation_id: str,
    status: str,
) -> None:
    """Update a recommendation's status."""
    await db.execute(
        "UPDATE chat_recommendations SET status = ? WHERE recommendation_id = ?",
        (status, recommendation_id),
    )
    await db.commit()
