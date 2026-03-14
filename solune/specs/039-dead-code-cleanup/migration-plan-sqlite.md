# Migration Plan: In-Memory Store to SQLite for Chat Data

**Date**: 2026-03-13
**Feature**: 039-dead-code-cleanup (planning only — implementation deferred)

## Current State

Chat data is stored in in-memory dictionaries in `backend/src/api/chat.py`:
- `_messages: dict[str, list[ChatMessage]]` — chat messages per session
- `_proposals: dict[str, AITaskProposal]` — AI task proposals
- `_recommendations: dict[str, AIRecommendation]` — AI recommendations

All data is lost on server restart.

## Target State

Migration 012 (`backend/src/migrations/012_chat_persistence.sql`) already created the SQLite tables:
- `chat_messages`
- `chat_proposals`
- `chat_recommendations`

The tables exist but are not yet used by the application code.

## Migration Checklist

### Read paths (replace dict lookup with SQL SELECT)
- [ ] `_messages` reads in `get_messages()` — ~3 code paths
- [ ] `_proposals` reads in `get_proposal()` — ~3 code paths
- [ ] `_recommendations` reads in `get_recommendation()` — ~2 code paths

### Write paths (replace dict mutation with SQL INSERT/UPDATE)
- [ ] `add_message()` — INSERT into `chat_messages`
- [ ] `create_proposal()` — INSERT into `chat_proposals`
- [ ] `update_proposal_status()` — UPDATE `chat_proposals`
- [ ] `create_recommendation()` — INSERT into `chat_recommendations`
- [ ] `update_recommendation()` — UPDATE `chat_recommendations`

### Transaction management
- [ ] Message + proposal creation (atomic)
- [ ] Proposal confirmation + issue creation (atomic)
- [ ] Session cleanup / logout (CASCADE or manual DELETE)

### API endpoint updates
- [ ] `POST /chat/message` — write message to SQLite
- [ ] `GET /chat/messages` — read from SQLite
- [ ] `POST /chat/proposals` — write proposal to SQLite
- [ ] `PUT /chat/proposals/{id}/confirm` — update proposal in SQLite
- [ ] `DELETE /chat/proposals/{id}` — delete proposal from SQLite

## Risks

- Transaction management across async code (aiosqlite)
- Performance impact of SQLite writes in chat hot path
- Need to handle migration of any in-flight data during deployment
- WebSocket message broadcasting must remain fast (don't block on writes)

## Recommendation

Implement as a separate spec. Use a write-through cache pattern:
1. Write to SQLite (durable)
2. Keep in-memory dict as read cache (fast)
3. On restart, hydrate cache from SQLite

This gives durability without sacrificing latency in the chat hot path.
