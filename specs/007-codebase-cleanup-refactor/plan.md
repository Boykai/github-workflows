# Implementation Plan: Codebase Cleanup & Refactor

**Branch**: `007-codebase-cleanup-refactor` | **Date**: 2026-02-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/007-codebase-cleanup-refactor/spec.md`

## Summary

Refactor the entire codebase for maintainability, DRY compliance, and best practices. The two most critical deliverables are: (1) splitting the two oversized backend services (`github_projects.py` at 4,449 lines and `copilot_polling.py` at 3,988 lines) into focused sub-modules of ~500 lines each with re-export facades for backward compatibility, and (2) eliminating duplicated code patterns (repository resolution, cache keys, event filtering, GitHub headers) into shared utilities. Secondary deliverables include standardized error handling with sanitized responses, consolidated magic numbers/constants, a unified frontend HTTP client with lazy auth token lookup, sessionStorage-based state persistence, WebSocket-primary real-time updates with polling fallback, and expanded test coverage for untested modules.

## Technical Context

**Language/Version**: Python ≥3.11 (backend), TypeScript ~5.4 (frontend)
**Primary Dependencies**: FastAPI, Pydantic v2, httpx, aiosqlite, github-copilot-sdk, agent-framework-core (backend); React 18, @tanstack/react-query v5, socket.io-client, Vite 5 (frontend)
**Storage**: SQLite via aiosqlite (settings/sessions); in-memory caches (InMemoryCache, module-level dicts/sets)
**Testing**: pytest + pytest-asyncio (backend); Vitest + @testing-library/react (frontend unit); Playwright (frontend e2e)
**Target Platform**: Linux server (backend via Docker); modern browsers (frontend via nginx)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: No regression — refactoring must not introduce additional latency or resource consumption
**Constraints**: All existing tests must pass without assertion changes; all external API contracts (GitHub API, Copilot API) unchanged; database schema unchanged
**Scale/Scope**: ~18K backend LOC, ~7K frontend LOC, ~9K test LOC; 8 API route modules, 12 service modules, 7 model modules, 10+ frontend hooks

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development — ✅ PASS

Spec exists at `specs/007-codebase-cleanup-refactor/spec.md` with 7 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, clear scope boundaries, and a Clarifications section with 5 resolved questions.

### II. Template-Driven Workflow — ✅ PASS

All artifacts follow canonical templates (`spec-template.md`, `plan-template.md`). No custom sections added without documentation.

### III. Agent-Orchestrated Execution — ✅ PASS

Workflow follows specify → plan → tasks → implement phase ordering. Each agent has a single purpose with well-defined inputs/outputs.

### IV. Test Optionality with Clarity — ✅ PASS

Tests are explicitly requested in the spec (FR-015, FR-016, User Story 7). Test tasks will precede implementation where TDD is appropriate. Existing tests serve as the regression baseline (SC-007).

### V. Simplicity and DRY — ✅ PASS (core goal)

This feature's entire purpose is to enforce Principle V. The module splits follow single-responsibility principle. Re-export facades add a thin layer but prevent external breakage — justified by backward compatibility. No premature abstractions; shared utilities are extracted only from proven-duplicated code.

**Post-Design Re-Check (Phase 1)**: All five principles remain satisfied. The design introduces:
- 2 Python packages (replacing 2 monolithic files) — reduces complexity per-module
- 1 shared utility package (5 modules) — each extracted from 2+ duplication sites
- 1 frontend utility (`sessionState.ts`) — minimal API surface
- 1 React component (`ErrorBoundary.tsx`) — standard React pattern
- 1 constants file (`constants.ts`) — centralization, not new abstraction

No new frameworks, patterns, or architectural layers. All changes simplify or consolidate existing code.

## Project Structure

### Documentation (this feature)

```text
specs/007-codebase-cleanup-refactor/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── __init__.py          # Router aggregator (existing)
│   │   ├── auth.py              # Auth routes (existing, error handling updated)
│   │   ├── board.py             # Board routes (existing)
│   │   ├── chat.py              # Chat routes (existing)
│   │   ├── projects.py          # Project routes (existing)
│   │   ├── settings.py          # Settings routes (existing)
│   │   ├── tasks.py             # Task routes (existing)
│   │   ├── webhooks.py          # Webhook routes (existing, dedup extracted)
│   │   └── workflow.py          # Workflow routes (existing)
│   ├── models/                  # (unchanged)
│   ├── prompts/                 # (unchanged)
│   ├── services/
│   │   ├── github_projects/     # NEW package (split from monolith)
│   │   │   ├── __init__.py      # Re-export facade
│   │   │   ├── client.py        # GraphQL/REST client + retry logic
│   │   │   ├── queries.py       # GraphQL query constants
│   │   │   ├── projects.py      # Project listing, board data, field updates
│   │   │   ├── issues.py        # Issue CRUD, sub-issues, comments
│   │   │   ├── pull_requests.py # PR lifecycle, merge, review
│   │   │   ├── assignments.py   # Copilot/agent assignment
│   │   │   ├── status.py        # Status field updates
│   │   │   └── agents.py        # Agent listing/discovery
│   │   ├── copilot_polling/     # NEW package (split from monolith)
│   │   │   ├── __init__.py      # Re-export facade
│   │   │   ├── state.py         # PollingState + module-level state vars
│   │   │   ├── loop.py          # Polling lifecycle (start/stop/status)
│   │   │   ├── backlog.py       # Backlog + Ready issue processing
│   │   │   ├── in_progress.py   # In-progress issue processing
│   │   │   ├── pipeline.py      # Pipeline state management
│   │   │   ├── completion.py    # PR completion detection + merge
│   │   │   ├── outputs.py       # Agent output posting
│   │   │   └── recovery.py      # Stalled issue recovery
│   │   ├── shared/              # NEW shared utilities
│   │   │   ├── __init__.py
│   │   │   ├── github_headers.py    # GitHub REST/GraphQL header builder
│   │   │   ├── bounded_set.py       # BoundedSet (dedup with max size + prune)
│   │   │   ├── datetime_utils.py    # ISO 8601 parsing + timezone normalization
│   │   │   ├── cache_keys.py        # All cache key construction (consolidated)
│   │   │   └── issue_parsing.py     # Issue-number extraction from PR branch/body
│   │   ├── ai_agent.py             # (existing)
│   │   ├── agent_tracking.py       # (existing, well-factored)
│   │   ├── cache.py                # (existing, cache key helpers moved out)
│   │   ├── completion_providers.py  # (existing)
│   │   ├── database.py             # (existing)
│   │   ├── github_auth.py          # (existing)
│   │   ├── session_store.py        # (existing)
│   │   ├── settings_store.py       # (existing)
│   │   ├── websocket.py            # (existing)
│   │   └── workflow_orchestrator.py # (existing, <500 lines target)
│   ├── config.py                # (existing, new constants added)
│   ├── constants.py             # (existing, consolidated magic numbers)
│   ├── exceptions.py            # (existing, error handler enhanced)
│   └── main.py                  # (existing, error middleware updated)
└── tests/
    ├── unit/
    │   ├── test_github_projects.py       # (existing, imports updated)
    │   ├── test_copilot_polling.py       # (existing, imports updated)
    │   ├── test_completion_providers.py  # NEW
    │   ├── test_session_store.py         # NEW
    │   ├── test_settings_store.py        # NEW
    │   ├── test_agent_tracking.py        # NEW
    │   └── test_workflow_orchestrator.py  # (existing)
    └── integration/

frontend/
├── src/
│   ├── services/
│   │   ├── api.ts               # (existing, enhanced as shared HTTP client)
│   │   └── sessionState.ts      # NEW: sessionStorage persistence helpers
│   ├── components/
│   │   ├── common/
│   │   │   └── ErrorBoundary.tsx # NEW
│   │   └── ...                  # (existing)
│   ├── hooks/
│   │   ├── useAuth.ts           # (existing)
│   │   ├── useProjectBoard.ts   # (existing, polling removed — uses WS via useRealTimeSync)
│   │   ├── useRealTimeSync.ts   # (existing, enhanced: WS primary + polling fallback)
│   │   ├── useChat.ts           # (existing, API calls via shared client)
│   │   └── ...                  # (existing)
│   ├── hooks/
│   │   ├── useAuth.test.tsx          # (existing)
│   │   ├── useSettings.test.tsx      # NEW
│   │   ├── useWorkflow.test.tsx      # NEW
│   │   ├── useAgentConfig.test.tsx   # NEW
│   │   ├── useChat.test.tsx          # NEW
│   │   ├── useProjectBoard.test.tsx  # NEW
│   │   └── useAppTheme.test.tsx      # NEW
│   └── ...
└── ...
```

**Structure Decision**: Web application structure (Option 2). The key change is converting two monolithic service files into Python packages with `__init__.py` re-export facades, and adding a `services/shared/` directory for extracted utility code. Frontend changes are additive (new files) with modifications to existing hooks and services.

## Complexity Tracking

> No constitution violations to justify. All design decisions follow simplicity principles:
> - Re-export facades are thin (import + re-export only) — justified by backward compatibility
> - `services/shared/` is extracted from proven-duplicate code, not premature abstraction
> - No new frameworks, patterns, or architectural layers introduced
