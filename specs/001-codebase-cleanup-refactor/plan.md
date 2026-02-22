# Implementation Plan: Codebase Cleanup & Refactor

**Branch**: `001-codebase-cleanup-refactor` | **Date**: 2026-02-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-codebase-cleanup-refactor/spec.md`

## Summary

Refactor the entire codebase for maintainability, DRY compliance, and modern best practices. The two highest-impact deliverables are: (1) splitting the two oversized backend service files (`github_projects.py` at 4,449 lines and `copilot_polling.py` at 3,948 lines) into focused sub-module packages of ~500 lines each with re-export facades for backward compatibility, and (2) eliminating duplicated code patterns (repository resolution, cache keys, GitHub headers, datetime parsing, issue-number extraction) into shared utilities. Secondary deliverables include standardized error handling with sanitized responses (replacing 9 `HTTPException` uses and 73 bare `except Exception` blocks), consolidated magic numbers/constants, a unified frontend HTTP client (migrating 5 raw `fetch()` calls from `useWorkflow.ts` and `useAgentConfig.ts`), `sessionStorage`-based state persistence, an `ErrorBoundary` component, WebSocket-primary real-time updates with polling fallback, and expanded test coverage for untested backend services and frontend hooks.

## Technical Context

**Language/Version**: Python ≥3.11 (backend), TypeScript ~5.4 (frontend)
**Primary Dependencies**: FastAPI 0.109+, Pydantic v2 5.0+, httpx, aiosqlite, github-copilot-sdk, agent-framework-core (backend); React 18.3, @tanstack/react-query 5.17, socket.io-client 4.7, Vite 5.4 (frontend)
**Storage**: SQLite via aiosqlite (settings/sessions); in-memory caches (module-level dicts/sets)
**Testing**: pytest 7.4+ / pytest-asyncio 0.23+ (backend); Vitest 4.0 / @testing-library/react (frontend unit); Playwright 1.58 (frontend e2e)
**Target Platform**: Linux server (backend via Docker); modern browsers (frontend via nginx)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: No regression — refactoring must not introduce additional latency or resource consumption
**Constraints**: All existing tests must pass without assertion changes; all external API contracts (GitHub API, Copilot API) unchanged; database schema unchanged
**Scale/Scope**: ~18K backend LOC across 34 Python files, ~7K frontend LOC across 9 hooks + services, ~9K test LOC; 8 API route modules, 12 service modules, 6 model modules

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development — ✅ PASS

Spec exists at `specs/001-codebase-cleanup-refactor/spec.md` with 7 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios for each story, clear scope boundaries, edge cases, and a Clarifications section with 5 resolved questions.

### II. Template-Driven Workflow — ✅ PASS

All artifacts follow canonical templates (`spec-template.md`, `plan-template.md`). No custom sections added without documentation.

### III. Agent-Orchestrated Execution — ✅ PASS

Workflow follows specify → plan → tasks → implement phase ordering. Each agent has a single purpose with well-defined inputs/outputs.

### IV. Test Optionality with Clarity — ✅ PASS

Tests are explicitly requested in the spec (FR-015, FR-016, User Story 7). Test tasks will precede implementation where TDD is appropriate. Existing tests serve as the regression baseline (SC-007).

### V. Simplicity and DRY — ✅ PASS (core goal)

This feature's entire purpose is to enforce Principle V. The module splits follow single-responsibility principle. Re-export facades add a thin layer but prevent external breakage — justified by backward compatibility requirement (FR-001). No premature abstractions; shared utilities are extracted only from proven-duplicated code (2+ call sites each).

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
specs/001-codebase-cleanup-refactor/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
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
│   │   │   ├── recovery.py      # Stalled issue recovery
│   │   │   └── manual.py        # Manual single-issue check
│   │   ├── shared/              # NEW shared utilities
│   │   │   ├── __init__.py
│   │   │   ├── github_headers.py    # GitHub REST/GraphQL header builder
│   │   │   ├── bounded_set.py       # BoundedSet (dedup with max size + prune)
│   │   │   ├── datetime_utils.py    # ISO 8601 parsing + timezone normalization
│   │   │   ├── cache_keys.py        # All cache key construction (consolidated)
│   │   │   └── issue_parsing.py     # Issue-number extraction from PR branch/body
│   │   ├── ai_agent.py             # (existing)
│   │   ├── agent_tracking.py       # (existing)
│   │   ├── cache.py                # (existing, cache key helpers moved out)
│   │   ├── completion_providers.py  # (existing)
│   │   ├── database.py             # (existing)
│   │   ├── github_auth.py          # (existing)
│   │   ├── session_store.py        # (existing)
│   │   ├── settings_store.py       # (existing)
│   │   ├── websocket.py            # (existing)
│   │   └── workflow_orchestrator.py # (existing, target reduction)
│   ├── config.py                # (existing)
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
│   │   ├── useProjectBoard.ts   # (existing, independent polling removed)
│   │   ├── useRealTimeSync.ts   # (existing, enhanced: WS primary + polling fallback)
│   │   ├── useWorkflow.ts       # (existing, raw fetch → shared client)
│   │   ├── useAgentConfig.ts    # (existing, raw fetch → shared client)
│   │   ├── useChat.ts           # (existing)
│   │   └── ...                  # (existing)
│   ├── constants.ts             # NEW: consolidated frontend constants
│   ├── hooks/
│   │   ├── useAuth.test.tsx          # (existing)
│   │   ├── useProjects.test.tsx      # (existing)
│   │   ├── useRealTimeSync.test.tsx  # (existing)
│   │   ├── useSettings.test.tsx      # NEW
│   │   ├── useWorkflow.test.tsx      # NEW
│   │   ├── useAgentConfig.test.tsx   # NEW
│   │   ├── useChat.test.tsx          # NEW
│   │   ├── useProjectBoard.test.tsx  # NEW
│   │   └── useAppTheme.test.tsx      # NEW
│   └── ...
└── ...
```

**Structure Decision**: Web application structure (backend + frontend). The key structural change is converting two monolithic service files into Python packages with `__init__.py` re-export facades, and adding a `services/shared/` directory for extracted utility code. Frontend changes are additive (new files) with modifications to existing hooks and services.

## Complexity Tracking

> No constitution violations to justify. All design decisions follow simplicity principles:
> - Re-export facades are thin (import + re-export only) — justified by backward compatibility (FR-001)
> - `services/shared/` is extracted from proven-duplicate code (2+ call sites), not premature abstraction
> - No new frameworks, patterns, or architectural layers introduced
