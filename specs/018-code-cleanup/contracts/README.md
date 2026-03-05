# Contracts: Codebase Cleanup — Reduce Technical Debt

**Feature**: `018-code-cleanup` | **Date**: 2026-03-05

## No API Contract Changes

This feature explicitly **does not change any public API contracts** (FR-020). All changes are internal implementation only.

**Constraint from spec**: "Do not change any public API contracts (route paths, request/response shapes) — only internal implementation."

### Existing API Routes — Unchanged

All existing API routes under `/api/v1/` remain unchanged:

| Route | File | Status |
|-------|------|--------|
| `/api/v1/health` | `backend/src/api/health.py` | Unchanged |
| `/api/v1/auth/*` | `backend/src/api/auth.py` | Unchanged |
| `/api/v1/projects/*` | `backend/src/api/projects.py` | Unchanged |
| `/api/v1/board/*` | `backend/src/api/board.py` | Unchanged |
| `/api/v1/chat/*` | `backend/src/api/chat.py` | Unchanged |
| `/api/v1/tasks/*` | `backend/src/api/tasks.py` | Unchanged |
| `/api/v1/agents/*` | `backend/src/api/agents.py` | Unchanged |
| `/api/v1/chores/*` | `backend/src/api/chores.py` | Unchanged |
| `/api/v1/settings/*` | `backend/src/api/settings.py` | Unchanged |
| `/api/v1/webhooks/*` | `backend/src/api/webhooks.py` | Unchanged |
| `/api/v1/workflow/*` | `backend/src/api/workflow.py` | Unchanged |
| `/api/v1/mcp/*` | `backend/src/api/mcp.py` | Unchanged |
| `/api/v1/signal/*` | `backend/src/api/signal.py` | Unchanged |
| `/api/v1/cleanup/*` | `backend/src/api/cleanup.py` | Unchanged |

### Note on Route Handler Removal

If any route handlers are identified as unused (FR-006), they will only be removed after confirming:

1. No frontend code calls the endpoint
2. No test coverage relies on the endpoint
3. No external integrations reference the endpoint
4. The route is not part of the public API contract

Any such removal will be documented in the PR description with rationale.
