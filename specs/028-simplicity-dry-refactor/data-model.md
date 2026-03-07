# Data Model: Simplicity & DRY Refactoring Plan (5 Phases)

**Feature**: `028-simplicity-dry-refactor` | **Date**: 2026-03-07

---

## Overview

This refactoring does not introduce new persistent data models (no database schema changes, no new API resources). Instead, it restructures existing code into new **module boundaries** and **shared abstractions**. This document describes the entities being refactored and their relationships.

---

## Backend Module Entities

### Service Module Decomposition

The monolithic `GitHubProjectsService` class (4,937 LOC, 79 methods) is decomposed into focused modules. Each module is a class that receives a shared `GitHubClient` instance via constructor injection.

| Module | Entity | Responsibility | Max LOC | Dependencies |
|--------|--------|---------------|---------|-------------|
| `client.py` | `GitHubClient` | HTTP infrastructure, `_request_with_retry`, `_graphql`, rate limits, request coalescing | 600 | `githubkit`, `httpx` |
| `projects.py` | `ProjectService` | List/get projects, project parsing | 500 | `GitHubClient` |
| `issues.py` | `IssueService` | Issue CRUD, completion detection, draft items | 600 | `GitHubClient`, `FieldService` |
| `pull_requests.py` | `PullRequestService` | PR CRUD, merge, review operations | 500 | `GitHubClient` |
| `copilot.py` | `CopilotService` | Copilot assignment, bot ID detection | 400 | `GitHubClient` |
| `fields.py` | `FieldService` | Field queries & mutations (status, iteration, custom) | 300 | `GitHubClient` |
| `board.py` | `BoardService` | Board queries, item reconciliation | 400 | `GitHubClient`, `FieldService` |
| `repository.py` | `RepositoryService` | Repo info, branch/commit workflow | 300 | `GitHubClient` |

### Module Dependency Graph

```
GitHubClient (base)
    ├── ProjectService
    ├── IssueService ──→ FieldService
    ├── PullRequestService
    ├── CopilotService
    ├── FieldService
    ├── BoardService ──→ FieldService
    └── RepositoryService
```

**Constraint**: No circular dependencies. All modules depend on `GitHubClient`; only `IssueService` and `BoardService` additionally depend on `FieldService`.

### Facade Entity

| Entity | Location | Purpose |
|--------|----------|---------|
| `GitHubProjectsService` | `__init__.py` | Backward-compatible composite that holds all sub-services and delegates method calls. Existing callers continue to import this class unchanged. |

### Facade Composition

```
GitHubProjectsService
    ├── .client: GitHubClient
    ├── .projects: ProjectService
    ├── .issues: IssueService
    ├── .pull_requests: PullRequestService
    ├── .copilot: CopilotService
    ├── .fields: FieldService
    ├── .board: BoardService
    └── .repository: RepositoryService
```

---

## Backend Shared Abstractions

### Helper Functions (New)

| Function | Location | Input | Output | Replaces |
|----------|----------|-------|--------|----------|
| `require_selected_project(session)` | `dependencies.py` | `UserSession` | `str` (project_id) or raises HTTP 400 | 5 inline guard clauses |
| `cached_fetch(cache, key, fetch_fn, ...)` | `cache.py` | cache instance, key, async callable, refresh flag, TTL | `T` (cached or fresh result) | Verbose check/get/set in 3 files |

### Helper Functions (Existing — Now Wired In)

| Function | Location | Status | Callers After Wiring |
|----------|----------|--------|---------------------|
| `resolve_repository(access_token, project_id)` | `utils.py:145-186` | Exists, some callers bypass it | All 8 resolution sites |
| `handle_service_error(exc, operation, error_cls)` | `logging_utils.py:241-276` | Exists, zero callers | 12+ endpoint error handlers |
| `safe_error_response(exc, operation)` | `logging_utils.py:215-238` | Exists, zero callers | Used by `handle_service_error` |

---

## Frontend Shared Abstractions

### Generic CRUD Hook Factory

| Entity | Location | Purpose |
|--------|----------|---------|
| `useCrudResource<T, C, U>` | `hooks/useCrudResource.ts` | Generic hook accepting resource config, returning list query + CRUD mutations with automatic cache invalidation |

**Configuration Shape**:

| Field | Type | Description |
|-------|------|-------------|
| `resourceKey` | `string` | Base query key (e.g., `'agents'`) |
| `endpoints.list` | `(projectId: string) => Promise<T[]>` | List endpoint |
| `endpoints.create` | `(projectId: string, input: C) => Promise<T>` | Create endpoint (optional) |
| `endpoints.update` | `(projectId: string, id: string, input: U) => Promise<T>` | Update endpoint (optional) |
| `endpoints.delete` | `(projectId: string, id: string) => Promise<void>` | Delete endpoint (optional) |
| `staleTime` | `number` | React Query stale time (optional) |

**Consumers**: `useAgents.ts`, `useChores.ts`, `useSettings.ts` (3 hooks)

### Shared UI Components

| Component | Location | Props | Replaces |
|-----------|----------|-------|----------|
| `PreviewCard` | `components/chat/PreviewCard.tsx` | `title`, `onConfirm`, `onCancel`, `confirmLabel?`, `cancelLabel?`, `isLoading?`, `error?`, `children` | `TaskPreview`, `StatusChangePreview`, `IssueRecommendationPreview` card layout |
| `Modal` | `components/common/Modal.tsx` | `isOpen`, `onClose`, `title`, `children`, `size?` | Escape-key/backdrop/overflow logic in 5+ modal components |
| `ErrorAlert` | `components/common/ErrorAlert.tsx` | `error`, `onDismiss?`, `className?` | Scattered error display patterns |

### ChatInterface Sub-Components

| Component | Location | Responsibility | ~LOC |
|-----------|----------|---------------|------|
| `ChatMessageList` | `components/chat/ChatMessageList.tsx` | Message rendering, auto-scroll, retry, proposals | ~150 |
| `ChatInput` | `components/chat/ChatInput.tsx` | Text input, autocomplete, history navigation | ~120 |

### Query Key Registry

| Entity | Location | Purpose |
|--------|----------|---------|
| `queryKeys` | `hooks/queryKeys.ts` | Single source of truth for all React Query cache keys |

**Namespaces**: `agents`, `chores`, `settings`, `signal`, `projects`, `board`, `chat`, `workflow`, `tools`, `agentTools`, `pipeline`, `mcp`, `models`, `auth`

---

## Initialization Model

### Before (3 Competing Patterns)

| Pattern | Location | Example |
|---------|----------|---------|
| Lifespan + `app.state` | `main.py:304-308` | `app.state.github_service = github_projects_service` |
| Module-level global | `service.py` (bottom) | `github_projects_service = GitHubProjectsService(...)` |
| Lazy singleton | Various | `_instance = None; def get(): ...` |

### After (Single Pattern)

```
lifespan() creates all services
    → stores on app.state
        → dependencies.py getters read from app.state
            → endpoints use Depends(get_xxx_service)
```

**Constraint**: No module-level service instantiation. All service creation happens in `lifespan()`. Tests override via `app.dependency_overrides` (already in use in `conftest.py`).

---

## Relationships Summary

```
┌─────────────────────────────────────────────────────────────────┐
│ Backend                                                         │
│                                                                 │
│  lifespan() ──creates──→ GitHubProjectsService (facade)         │
│       │                        │                                │
│       │                        ├── GitHubClient                 │
│       │                        ├── ProjectService               │
│       │                        ├── IssueService                 │
│       │                        ├── PullRequestService           │
│       │                        ├── CopilotService               │
│       │                        ├── FieldService                 │
│       │                        ├── BoardService                 │
│       │                        └── RepositoryService            │
│       │                                                         │
│       └──stores on──→ app.state                                 │
│                          │                                      │
│                          └──read by──→ dependencies.py getters  │
│                                           │                     │
│           Endpoints use Depends(getter) ──┘                     │
│           + require_selected_project()                          │
│           + handle_service_error()                              │
│           + cached_fetch()                                      │
│           + resolve_repository()                                │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ Frontend                                                        │
│                                                                 │
│  queryKeys (registry) ──used by──→ all hooks                    │
│                                                                 │
│  useCrudResource (factory) ──used by──→ useAgents, useChores,   │
│                                         useSettings             │
│                                                                 │
│  PreviewCard ──used by──→ TaskPreview, StatusChangePreview,     │
│                            IssueRecommendationPreview           │
│                                                                 │
│  Modal ──used by──→ AddAgentModal, IssueDetailModal,            │
│                      AddChoreModal, ToolSelectorModal, etc.     │
│                                                                 │
│  ChatInterface ──composed of──→ ChatMessageList + ChatInput     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## State Transitions

No new state machines are introduced. Existing state (project selection, chat messages, board items) is preserved unchanged through refactoring. The only state change is the initialization lifecycle:

| State | Before | After |
|-------|--------|-------|
| Service creation | Import-time (module-level) | Startup-time (`lifespan()`) |
| Service access | Direct import or `app.state` | `Depends()` only |
| Cache access | Verbose inline patterns | `cached_fetch()` wrapper |
| Error handling | Hand-rolled per endpoint | `handle_service_error()` |
| Session validation | Inline guard clauses | `require_selected_project()` |
