# Contracts: Codebase Cleanup & Refactor

**Feature**: `009-codebase-cleanup-refactor` | **Date**: 2026-02-22

## N/A — Pure Refactor

This feature introduces **no new API endpoints, no schema changes, and no new external contracts**. All existing API contracts remain unchanged.

### Preserved Contracts

| Contract | Location | Impact |
|----------|----------|--------|
| REST API endpoints | `backend/src/api/*.py` | No changes to routes, request/response schemas, or status codes |
| WebSocket protocol | `backend/src/services/websocket.py` | No changes to message format |
| Pydantic models | `backend/src/models/*.py` | Models are **reorganized** into new files but field definitions, validation rules, and serialization behavior are identical |
| Frontend API client | `frontend/src/services/api.ts` | New workflow/agent endpoints added to the typed client (previously bypassed via raw `fetch`), but the HTTP contract is unchanged |
| SQLite schema | `backend/src/migrations/*.sql` | No schema changes; `datetime` serialization adds `+00:00` suffix to new timestamps (backward-compatible with `fromisoformat()`) |
| Docker/deployment | `docker-compose.yml`, `Dockerfile` | No changes |

### Internal Contract Changes (Module Boundaries)

While external contracts are preserved, **internal Python import paths** change due to module decomposition. Backward compatibility is maintained via `__init__.py` re-exports — see [data-model.md](data-model.md) for the full decomposition map.
