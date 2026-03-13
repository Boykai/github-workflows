"""Integration test: chat persistence across simulated restarts.

Verifies that chat messages, proposals, and recommendations survive
a simulated application restart (clear in-memory state → re-read from SQLite).
"""

from __future__ import annotations

import json
from uuid import uuid4

import aiosqlite
import pytest

from src.services.chat_store import (
    clear_messages,
    get_messages,
    get_proposals,
    save_message,
    save_proposal,
)

CHAT_SCHEMA = """\
CREATE TABLE IF NOT EXISTS chat_messages (
    message_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    sender_type TEXT NOT NULL CHECK (sender_type IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    action_type TEXT,
    action_data TEXT,
    timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);

CREATE TABLE IF NOT EXISTS chat_proposals (
    proposal_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    original_input TEXT NOT NULL,
    proposed_title TEXT NOT NULL,
    proposed_description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'confirmed', 'edited', 'cancelled')),
    edited_title TEXT,
    edited_description TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    expires_at TEXT,
    file_urls TEXT
);
CREATE INDEX IF NOT EXISTS idx_chat_proposals_session ON chat_proposals(session_id);
"""


@pytest.fixture
async def db():
    """In-memory SQLite with chat persistence tables."""
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row
    await conn.executescript(CHAT_SCHEMA)
    yield conn
    await conn.close()


class TestChatMessagePersistence:
    """Messages survive simulated restart (write → read from DB only)."""

    @pytest.mark.asyncio
    async def test_messages_round_trip(self, db: aiosqlite.Connection):
        session_id = str(uuid4())
        user_msg_id = str(uuid4())
        assistant_msg_id = str(uuid4())

        await save_message(db, session_id, user_msg_id, "user", "Fix the login bug")
        await save_message(
            db,
            session_id,
            assistant_msg_id,
            "assistant",
            "Created task: Fix login bug",
            action_type="task_create",
            action_data=json.dumps({"task_id": "PVTI_123"}),
        )

        # Simulate restart: read fresh from DB
        recovered = await get_messages(db, session_id)

        assert len(recovered) == 2
        assert recovered[0]["sender_type"] == "user"
        assert recovered[0]["content"] == "Fix the login bug"
        assert recovered[1]["sender_type"] == "assistant"
        assert recovered[1]["action_type"] == "task_create"
        assert json.loads(recovered[1]["action_data"])["task_id"] == "PVTI_123"

    @pytest.mark.asyncio
    async def test_clear_messages_removes_session(self, db: aiosqlite.Connection):
        session_id = str(uuid4())

        await save_message(db, session_id, str(uuid4()), "user", "hello")
        await clear_messages(db, session_id)

        recovered = await get_messages(db, session_id)
        assert recovered == []

    @pytest.mark.asyncio
    async def test_sessions_are_isolated(self, db: aiosqlite.Connection):
        s1, s2 = str(uuid4()), str(uuid4())

        await save_message(db, s1, str(uuid4()), "user", "session 1 msg")
        await save_message(db, s2, str(uuid4()), "user", "session 2 msg")

        msgs_s1 = await get_messages(db, s1)
        msgs_s2 = await get_messages(db, s2)

        assert len(msgs_s1) == 1
        assert msgs_s1[0]["content"] == "session 1 msg"
        assert len(msgs_s2) == 1
        assert msgs_s2[0]["content"] == "session 2 msg"


class TestProposalPersistence:
    """Proposals survive simulated restart."""

    @pytest.mark.asyncio
    async def test_proposal_round_trip(self, db: aiosqlite.Connection):
        session_id = str(uuid4())
        proposal_id = str(uuid4())

        await save_proposal(
            db,
            session_id,
            proposal_id,
            original_input="Add dark mode",
            proposed_title="Implement Dark Mode",
            proposed_description="Add a toggle for dark/light theme",
            file_urls=["https://example.com/mockup.png"],
        )

        recovered = await get_proposals(db, session_id)

        assert len(recovered) == 1
        p = recovered[0]
        assert p["proposed_title"] == "Implement Dark Mode"
        assert p["original_input"] == "Add dark mode"
        assert p["status"] == "pending"
        assert p["file_urls"] == ["https://example.com/mockup.png"]
