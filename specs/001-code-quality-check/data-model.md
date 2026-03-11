# Data Model: Code Quality Check

**Feature**: 001-code-quality-check | **Date**: 2026-03-11

## Overview

This feature is primarily a behavior-preserving refactoring initiative. It does not introduce new persistent entities or API endpoints. The data model documents the key conceptual entities that the quality work touches, their relationships, and the validation rules that govern the refactored code.

## Entities

### 1. Exception Handling Policy

The expected behavior for each `except` block in the backend codebase.

| Field | Type | Description |
|-------|------|-------------|
| `exception_type` | `str` | Specific exception class caught (e.g., `httpx.HTTPStatusError`, `KeyError`) |
| `binding` | `str \| None` | Variable name the exception is bound to (`as e`), or `None` if unbound |
| `action` | `enum` | One of: `log_and_propagate`, `log_and_return_default`, `log_debug_continue`, `sanitize_and_respond` |
| `external_facing` | `bool` | Whether the error response reaches an external system (Signal, webhook, etc.) |
| `context_preserved` | `bool` | Whether diagnostic context (traceback, message) is logged internally |

**Validation Rules**:

- `binding` MUST NOT be `None` for any `except Exception` block (FR-001, FR-002)
- If `external_facing` is `True`, the response MUST NOT contain `str(e)` or raw exception details (FR-003)
- `action` MUST NOT be `pass` or empty for any block (FR-001)
- Exception in `logging_utils.py` resilience guards: bare `except Exception:` is permitted (4 locations)

**State Transitions**:

```text
unhandled → caught → [logged | propagated | sanitized_response]
                   ↗ never → silently_swallowed (PROHIBITED)
```

---

### 2. Repository Context Resolution

The resolved `(owner, repo)` pair used by backend endpoints.

| Field | Type | Description |
|-------|------|-------------|
| `owner` | `str` | GitHub repository owner (user or org) |
| `repo` | `str` | GitHub repository name |
| `source` | `enum` | One of: `explicit_param`, `selected_project`, `env_default`, `fallback` |

**Validation Rules**:

- All resolution MUST go through `utils.resolve_repository()` (FR-005)
- No inline resolution logic in route handlers
- Fallback chain: explicit → selected project → environment default

**Current State**: ✅ Already consolidated — `resolve_repository()` exists and is used.

---

### 3. Selected Project Guard

The shared validation outcome for endpoints requiring an active project.

| Field | Type | Description |
|-------|------|-------------|
| `session` | `SessionData` | The current user session |
| `selected_project_id` | `str \| None` | The active project ID from session |
| `validation_result` | `str` | The validated project ID (returned on success) |

**Validation Rules**:

- All guard checks MUST use `require_selected_project(session)` from `dependencies.py` (FR-008)
- Returns `str` (project ID) on success
- Raises `ValidationError` with consistent message on failure

**Current State**: ✅ Already consolidated — `require_selected_project()` exists and is used.

---

### 4. Domain Module (Backend)

A focused unit of backend behavior in the `github_projects/` service.

| Module | Responsibility | LOC Target |
|--------|---------------|------------|
| `service.py` | Orchestration facade, shared infra | ≤500 |
| `issues.py` | Issue CRUD, comments, state management | ≤800 |
| `pull_requests.py` | PR creation, merge, review, completion | ≤800 |
| `copilot.py` | Agent assignment, unassignment, review | ≤800 |
| `board.py` | Board data fetching, reconciliation | ≤800 |
| `agents.py` | Agent management | ≤500 |
| `branches.py` | Branch operations | ≤300 |
| `graphql.py` | GraphQL query execution | ≤600 |
| `projects.py` | Project CRUD | ≤800 |
| `repository.py` | Repository metadata | ≤300 |

**Current State**: ✅ Already split — 12 modules, `service.py` at 343 LOC.

---

### 5. Domain Module (Frontend API)

Planned split of `frontend/src/services/api.ts` (1,136 LOC).

| Module | Exports | LOC Target |
|--------|---------|------------|
| `api/client.ts` | `request<T>()`, `ApiError`, auth listener | ≤150 |
| `api/auth.ts` | `authApi` | ≤50 |
| `api/projects.ts` | `projectsApi`, `tasksApi` | ≤100 |
| `api/chat.ts` | `chatApi` | ≤100 |
| `api/board.ts` | `boardApi` | ≤100 |
| `api/settings.ts` | `settingsApi` | ≤100 |
| `api/workflow.ts` | `workflowApi`, `metadataApi` | ≤50 |
| `api/signal.ts` | `signalApi` | ≤100 |
| `api/agents.ts` | `agentsApi`, `modelsApi` | ≤100 |
| `api/pipelines.ts` | `pipelinesApi` | ≤100 |
| `api/tools.ts` | `mcpApi`, `toolsApi`, `agentToolsApi` | ≤100 |
| `api/chores.ts` | `choresApi` | ≤150 |
| `api/cleanup.ts` | `cleanupApi` | ≤50 |
| `api/index.ts` | Re-exports all domain modules | ≤30 |

**Validation Rules**:

- Each module ≤300 LOC (SC-004)
- All modules import `request<T>()` from `client.ts`
- `index.ts` re-exports maintain backward compatibility

---

### 6. Frontend Hook Decomposition

Planned split of `useBoardControls.ts` (375 LOC).

| Hook | Responsibility | LOC Target |
|------|---------------|------------|
| `useBoardFilters` | Filter state, localStorage persistence for filters | ≤100 |
| `useBoardSort` | Sort state, localStorage persistence for sorting | ≤80 |
| `useBoardGroups` | Grouping logic, group computation | ≤100 |
| `useBoardControls` | Composition wrapper, orchestrates sub-hooks | ≤100 |

**Validation Rules**:

- Each hook ≤250 LOC (SC-004)
- Each hook owns a single concern
- Composition hook maintains the existing public interface

---

### 7. Chat Session Record

Persistent per-session chat history (partially implemented via migration 012).

| Field | Type | Description |
|-------|------|-------------|
| `message_id` | `TEXT PRIMARY KEY` | Unique message identifier |
| `session_id` | `TEXT NOT NULL` | Session this message belongs to |
| `sender_type` | `TEXT NOT NULL` | `user` or `assistant` |
| `content` | `TEXT` | Message content |
| `action_type` | `TEXT` | Optional action type |
| `action_data` | `TEXT` | Optional action payload (JSON) |
| `timestamp` | `TEXT NOT NULL` | ISO 8601 creation time |

**Validation Rules**:

- Per-session retention cap: 1,000 messages (FR-020, SC-006)
- Oldest messages trimmed when cap exceeded
- Must survive application restart (FR-020)

**Current State**: Schema exists (migration 012). Code may still use in-memory stores (TODO at `api/chat.py:84`).

---

### 8. Retention Policy

Explicit bounds on in-memory collections.

| Store | Location | Current State | Target |
|-------|----------|---------------|--------|
| `_signal_pending` | `signal_chat.py` | Unbounded `dict` | Bounded dict with TTL or max entries |
| Chat in-memory stores | `api/chat.py` | In-memory (TODO) | SQLite-backed with 1,000 msg/session cap |
| ETag cache | `github_projects/service.py` | Instance-scoped | Verify bounded |
| Model fetcher cache | `completion_providers.py` | TTL-based | Verify bounded |

**Validation Rules**:

- All in-memory stores MUST have documented size limits (FR-025, SC-007)
- Automated tests MUST verify eviction/trimming (SC-007)

---

## Entity Relationships

```text
┌─────────────────────────┐
│   Exception Handling     │
│   Policy                 │──── applied to ────▶ Backend except blocks
│   (conceptual)           │                       (38 remaining targets)
└─────────────────────────┘

┌─────────────────────────┐
│   Repository Context     │
│   Resolution             │──── used by ────────▶ API route handlers
│   (utils.resolve_repo)   │                       (already consolidated)
└─────────────────────────┘

┌─────────────────────────┐
│   Selected Project       │
│   Guard                  │──── validates ──────▶ Endpoints requiring project
│   (dependencies.py)      │                       (already consolidated)
└─────────────────────────┘

┌─────────────────────────┐
│   Chat Session Record    │
│   (SQLite: chat_messages)│──── bounded by ─────▶ Retention Policy
└─────────────────────────┘                         (1,000 msgs/session)

┌─────────────────────────┐
│   Frontend API Module    │
│   (api/*.ts)             │──── imports ────────▶ Shared Client
└─────────────────────────┘                         (api/client.ts)

┌─────────────────────────┐
│   Board Controls Hook    │
│   (useBoardControls)     │──── composes ───────▶ Sub-hooks
└─────────────────────────┘                         (filters, sort, groups)
```
