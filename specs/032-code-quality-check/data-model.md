# Data Model: Code Quality Check

**Feature**: 032-code-quality-check
**Date**: 2026-03-10

## Overview

This feature is primarily a refactoring initiative — no new domain entities are introduced. The data model documents the existing entities that are modified, the new utility abstractions extracted, and the structural changes to module boundaries.

## Modified Entities

### ExceptionHandler (Conceptual — Code Pattern)

Represents the standardized try/except pattern across the backend codebase.

| Field | Type | Description |
|-------|------|-------------|
| `exception_type` | `type[Exception]` | Specific exception class (not bare `Exception`) |
| `variable_binding` | `str` | Exception variable name (e.g., `e`, `exc`) |
| `recovery_action` | `enum` | One of: `log_and_propagate`, `log_and_return_safe`, `log_and_fallback` |
| `context_message` | `str` | Human-readable description of what was attempted |

**Validation Rules**:

- `exception_type` must not be bare `Exception` when specific types are determinable
- `variable_binding` must always be present (no anonymous catches)
- `recovery_action` must never be `pass` (silent swallowing prohibited)
- `context_message` must not contain internal details when exposed externally

**State Transitions**:

- `bare_exception` → `narrowed_exception` (Phase 1: type narrowing)
- `silent_pass` → `logged_handler` (Phase 1: add logging)
- `detail_leak` → `safe_response` (Phase 1: sanitize external responses)

### CachedFetchHelper (New Utility — `utils.py` or `cache_utils.py`)

Encapsulates the repeated cache-check/fetch/cache-set pattern.

| Field | Type | Description |
|-------|------|-------------|
| `cache_key` | `str` | Unique cache identifier |
| `fetch_fn` | `Callable[..., Awaitable[T]]` | Async function to call on cache miss |
| `refresh` | `bool` | If True, bypass cache and force fetch |
| `stale_fallback` | `bool` | If True, serve stale cache on fetch error |
| `ttl` | `int \| None` | Optional TTL override (seconds) |

**Validation Rules**:

- `cache_key` must be non-empty
- `fetch_fn` must be an async callable
- Cache read/write must be atomic (no race conditions between check and set)

### ValidationGuard (New Utility — `dependencies.py`)

Standardized validation guard for preconditions.

| Field | Type | Description |
|-------|------|-------------|
| `session` | `UserSession` | Current user session |
| `selected_project_id` | `str \| None` | Extracted from session |

**Validation Rules**:

- If `selected_project_id` is None or empty, raise `ValidationError` with consistent message
- Error message: "No project selected. Please select a project first."

### BoundedCache (Modified — `cache.py`)

Extends existing `InMemoryCache` with maximum size enforcement.

| Field | Type | Description |
|-------|------|-------------|
| `max_size` | `int` | Maximum number of entries (default: 10,000) |
| `eviction_policy` | `str` | Eviction strategy: `"lru"` (default) |
| `_store` | `dict[str, CacheEntry]` | Existing TTL-based storage |

**Validation Rules**:

- On `set()`, if `len(_store) >= max_size`, evict oldest entry before inserting
- `max_size` must be positive integer
- Existing TTL expiration continues to work alongside size-based eviction

### ChatMessageStore (Modified — `chat.py` → SQLite)

Migrates in-memory `_messages` dict to SQLite using existing migration 012 tables.

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | `str` | Session/project identifier (partition key) |
| `messages` | `list[ChatMessage]` | Ordered list of messages |
| `max_retention` | `int` | Maximum messages per session (default: 1,000) |

**Validation Rules**:

- On insert, if message count exceeds `max_retention`, delete oldest messages
- Messages are persisted asynchronously (non-blocking to the chat flow)
- On read, return messages ordered by timestamp ascending

**State Transitions**:

- `in_memory` → `persisted` (Phase 5: migration to SQLite)
- `unbounded` → `bounded` (Phase 6: retention limit enforcement)

## Module Decomposition Entities

### GitHubProjectsService (Split — Phase 3)

Original: `github_projects/service.py` (5,220 LOC)

| New Module | Responsibility | Key Methods |
|-----------|---------------|-------------|
| `issues.py` | Issue CRUD, comments, state management | `create_issue()`, `update_issue()`, `add_comment()`, `list_issues()` |
| `pull_requests.py` | PR creation, merge, review, completion detection | `create_pull_request()`, `merge_pr()`, `check_completion()` |
| `copilot.py` | Agent assignment, unassignment, review request | `assign_agent()`, `unassign_agent()`, `request_review()` |
| `board.py` | Board data fetching, reconciliation | `get_board_data()`, `reconcile_board()`, `list_board_projects()` |
| `service.py` | Orchestration facade, shared infra | `GitHubProjectsService` class, retry logic, ETag cache, throttle |

**Relationships**:

- `issues.py`, `pull_requests.py`, `copilot.py`, `board.py` all import shared infrastructure from `service.py`
- `service.py` re-exports or delegates to submodules for backward compatibility
- All submodules share the same `httpx.AsyncClient` and rate-limiting configuration

### FrontendAPIService (Split — Phase 3)

Original: `services/api.ts` (1,128 LOC)

| New Module | Responsibility |
|-----------|---------------|
| `client.ts` | `request<T>()`, `ApiError` class, auth event listener, AbortSignal support |
| `projects.ts` | Project CRUD endpoints |
| `chat.ts` | Chat message endpoints |
| `agents.ts` | Agent CRUD endpoints |
| `tools.ts` | MCP tool endpoints |
| `board.ts` | Board data endpoints |
| `index.ts` | Re-exports all modules for backward compatibility |

### FrontendHooks (Split — Phase 3)

| Original | New Sub-Hooks | Responsibility |
|---------|---------------|---------------|
| `usePipelineConfig.ts` (616 LOC) | `usePipelineState.ts` | Pipeline state management, selection |
| | `usePipelineMutations.ts` | Create, update, delete pipeline operations |
| | `usePipelineValidation.ts` | Stage validation, conflict detection |
| `useChat.ts` (385 LOC) | Evaluate post-Phase 3 | Close to 400 LOC threshold |
| `useBoardControls.ts` (375 LOC) | Evaluate post-Phase 3 | Close to 400 LOC threshold |

## Dependency Injection Entities (Phase 5)

### ServiceRegistry (FastAPI app.state)

Migrates module-level singletons to FastAPI dependency injection.

| Singleton | Current Location | Target Pattern |
|-----------|-----------------|----------------|
| `_ai_agent_service_instance` | `services/ai_agent.py` | `app.state.ai_agent_service` via lifespan startup |
| `_orchestrator_instance` | `workflow_orchestrator/orchestrator.py` | `app.state.orchestrator` via lifespan startup |
| `_connection` | `services/database.py` | `app.state.db` (already partially migrated) |
| `cache` | `services/cache.py` | `app.state.cache` via lifespan startup |
| `github_projects_service` | `github_projects/service.py` | `app.state.github_service` (already partially migrated) |

**Pattern**: Factory functions called during FastAPI lifespan startup, accessed via `Depends()` in endpoints. `dependencies.py` already implements the hybrid pattern (app.state with module-level fallback) that serves as the migration template.

## Migration Schema Changes

### Existing Tables (012_chat_persistence.sql)

The tables already exist from migration 012. No new migrations are needed for chat persistence — only the Python code needs to use them.

### Migration Prefix Audit

| Prefix | File A | File B | Resolution |
|--------|--------|--------|------------|
| 013 | `013_agent_config_lifecycle_status.sql` | `013_pipeline_configs.sql` | Add startup duplicate-detection warning |
| 014 | `014_agent_default_models.sql` | `014_extend_mcp_tools.sql` | Add startup duplicate-detection warning |
| 015 | `015_agent_icon_name.sql` | `015_pipeline_mcp_presets.sql` | Add startup duplicate-detection warning |

**Decision**: Add duplicate-detection with a startup warning (per R-018 in research.md). Defer renumbering to avoid breaking existing production databases.
