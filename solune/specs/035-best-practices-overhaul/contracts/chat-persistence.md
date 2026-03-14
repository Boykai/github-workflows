# Contract: Chat Persistence

**Feature**: `035-best-practices-overhaul` | **Phase**: 1 — Data Integrity
**File**: `backend/src/api/chat.py` (modification) + `backend/src/services/chat_store.py` (new)

## Purpose

Replace in-memory dict storage for chat messages, proposals, and recommendations with SQLite-backed persistence using the existing `012_chat_persistence.sql` migration tables.

## Interface

```python
"""Chat persistence — SQLite-backed message, proposal, and recommendation storage."""

import aiosqlite


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
    ...

async def get_messages(
    db: aiosqlite.Connection,
    session_id: str,
) -> list[dict]:
    """Retrieve all messages for a session, ordered by timestamp."""
    ...

async def clear_messages(
    db: aiosqlite.Connection,
    session_id: str,
) -> None:
    """Delete all messages for a session."""
    ...


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
    ...

async def get_proposals(
    db: aiosqlite.Connection,
    session_id: str,
) -> list[dict]:
    """Retrieve all proposals for a session, ordered by creation time."""
    ...

async def update_proposal_status(
    db: aiosqlite.Connection,
    proposal_id: str,
    status: str,
    edited_title: str | None = None,
    edited_description: str | None = None,
) -> None:
    """Update a proposal's status and optional edited fields."""
    ...


# ── Recommendations ──────────────────────────────────────────────

async def save_recommendation(
    db: aiosqlite.Connection,
    session_id: str,
    recommendation_id: str,
    data: str,
) -> None:
    """Persist a chat recommendation to SQLite."""
    ...

async def get_recommendations(
    db: aiosqlite.Connection,
    session_id: str,
) -> list[dict]:
    """Retrieve all recommendations for a session."""
    ...

async def update_recommendation_status(
    db: aiosqlite.Connection,
    recommendation_id: str,
    status: str,
) -> None:
    """Update a recommendation's status."""
    ...
```

## Behavior Contract

1. **Migration**: Tables are created by `012_chat_persistence.sql` which is already in the migration chain. No additional migration needed.
2. **Write path**: All chat state mutations write directly to SQLite via aiosqlite. No in-memory cache layer (chat reads are infrequent enough that SQLite performance is adequate).
3. **Session scoping**: All queries filter by `session_id` to enforce user-scoped access (Phase 5 requirement).
4. **Ordering**: Messages returned in timestamp order; proposals and recommendations in creation order.
5. **Cleanup**: `clear_messages()` deletes all messages for a session (used on conversation reset).

## Migration Reference

The `012_chat_persistence.sql` migration already creates:
- `chat_messages` (message_id PK, session_id indexed)
- `chat_proposals` (proposal_id PK, session_id indexed)
- `chat_recommendations` (recommendation_id PK, session_id indexed)

## Integration Points

- `backend/src/api/chat.py`: Replace `_messages: dict[str, list]`, `_proposals: dict[str, list]`, `_recommendations: dict[str, list]` with calls to `chat_store.py` functions.
- The `get_database()` dependency provides the `aiosqlite.Connection` via `request.app.state.db`.
