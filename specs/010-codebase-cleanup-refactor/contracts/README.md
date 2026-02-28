# Contracts: Codebase Cleanup — Remove Dead Code, Backwards Compatibility & Stale Tests

**Feature**: `010-codebase-cleanup-refactor` | **Date**: 2026-02-28

> **N/A — Pure Refactor**
>
> This feature is a codebase cleanup and refactoring effort. No new API endpoints, contracts, or external interfaces are introduced. All existing public APIs and user-facing behavior are preserved without modification.
>
> The following existing contracts remain unchanged:
> - All FastAPI REST API endpoints in `backend/src/api/`
> - All WebSocket interfaces in `backend/src/services/websocket.py`
> - All frontend API client methods in `frontend/src/services/api.ts`
> - All GitHub webhook handlers in `backend/src/api/webhooks.py`
