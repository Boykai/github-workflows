# API Contracts: Codebase Audit & Refactor

**Feature**: 018-codebase-audit-refactor
**Date**: 2026-03-05

## Contract: No API Changes

This feature is a refactoring effort. **All existing API endpoints maintain their exact request/response contracts.** No new endpoints are added, no existing endpoints are removed, and no response shapes change.

### Verified Endpoints (backward-compatible)

| Method | Path | Contract Change |
|--------|------|-----------------|
| GET | `/api/chat/messages` | None — same response shape, now backed by SQLite instead of in-memory dict |
| DELETE | `/api/chat/messages` | None — same behavior, clears from SQLite instead of dict |
| POST | `/api/chat/messages` | None — same request/response, persists to SQLite |
| POST | `/api/chat/proposals/{id}/confirm` | None — same behavior, updates SQLite |
| DELETE | `/api/chat/proposals/{id}` | None — same behavior, deletes from SQLite |

### Internal Interface Changes (not API-facing)

These changes affect internal Python method signatures but do not impact HTTP API contracts:

#### `CopilotClientPool` (new class)
```python
class CopilotClientPool:
    def __init__(self, maxlen: int = 50) -> None: ...
    async def get_or_create(self, github_token: str) -> Any: ...
    async def cleanup(self) -> None: ...
    async def remove(self, github_token: str) -> None: ...
```

#### `_with_fallback()` (new helper in service.py)
```python
async def _with_fallback(
    self,
    primary_fn: Callable[[], Awaitable[T]],
    fallback_fn: Callable[[], Awaitable[T]],
    context_msg: str,
) -> tuple[T, str]: ...
```

#### `_graphql()` parameter change
```python
# Before:
async def _graphql(self, query, variables, access_token, extra_headers=None): ...

# After:
async def _graphql(self, query, variables, access_token, extra_headers=None, graphql_features: list[str] | None = None): ...
```

#### `ASSIGN_COPILOT_MUTATION` parameter change
```graphql
# Before: model hardcoded
mutation($issueId: ID!, $assigneeIds: [ID!]!, ...) {
  addAssigneesToAssignable(input: { ... model: "claude-opus-4.6" ... })
}

# After: model as variable
mutation($issueId: ID!, $assigneeIds: [ID!]!, ..., $model: String!) {
  addAssigneesToAssignable(input: { ... model: $model ... })
}
```

#### `CREATE_COMMIT_ON_BRANCH_MUTATION` extension
```graphql
# Before: additions only
fileChanges: { additions: $additions }

# After: additions + optional deletions
fileChanges: { additions: $additions, deletions: $deletions }
```

### Migration Contract (SQL)

```sql
-- 011_chat_persistence.sql
-- Additive migration: creates 3 new tables, does not modify existing tables
CREATE TABLE IF NOT EXISTS chat_messages (...);
CREATE TABLE IF NOT EXISTS chat_proposals (...);
CREATE TABLE IF NOT EXISTS chat_recommendations (...);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_proposals_session ON chat_proposals(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_recommendations_session ON chat_recommendations(session_id);
```
