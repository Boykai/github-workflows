# Implementation Plan: Codebase Cleanup & Refactor

**Branch**: `009-codebase-cleanup-refactor` | **Date**: 2026-02-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-codebase-cleanup-refactor/spec.md`

## Summary

Comprehensive codebase cleanup targeting dead code removal, module decomposition of 3 oversized backend files (4,448 + 4,044 + 2,048 lines), DRY consolidation of 14+ duplicated patterns across backend and frontend, deprecation migration (30+ `datetime.utcnow()` calls), and structural improvements including error boundaries and dependency injection. Pure refactor — no user-facing behavior changes. Total codebase is ~25,385 LOC; target ≥10% reduction through dead code removal and deduplication.

## Technical Context

**Language/Version**: Python 3.11+ (backend, pyright targets 3.12), TypeScript ~5.4 (frontend)
**Primary Dependencies**: FastAPI, Pydantic 2.x, httpx, aiosqlite (backend); React 18, TanStack Query v5, Vite 5, dnd-kit (frontend)
**Storage**: SQLite via aiosqlite (async), plus synchronous `sqlite3` in workflow_orchestrator (to be migrated)
**Testing**: pytest + pytest-asyncio (backend), Vitest + React Testing Library (frontend unit), Playwright (frontend e2e)
**Target Platform**: Linux server (Docker), browser (SPA served via nginx)
**Project Type**: Web application — separate `backend/` and `frontend/` directories
**Performance Goals**: No measurable regression in startup time or API p95 latency after refactoring (SC-011)
**Constraints**: Each user story delivered as one atomic commit/PR; all tests must pass at each merge point
**Scale/Scope**: ~25,385 LOC (18,179 backend src + 5,953 frontend src + tests); 3 backend files >2,000 lines; 14+ DRY violations; 30+ deprecated API calls

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | `spec.md` fully written with 6 prioritized user stories, acceptance scenarios, and clarifications |
| II. Template-Driven Workflow | ✅ PASS | All artifacts use canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | ✅ PASS | Single plan agent producing well-defined outputs for subsequent phases |
| IV. Test Optionality | ✅ PASS | Spec requires existing tests to continue passing (FR-009) but mandates no new tests. Tests are opt-in per constitution. |
| V. Simplicity and DRY | ✅ PASS | The entire feature is *about* enforcing simplicity and DRY. Module decomposition targets single-responsibility, not arbitrary line counts. No premature abstractions introduced. |

**Gate result**: PASS — proceed to Phase 0.

### Post-Design Re-evaluation (after Phase 1)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | All design artifacts (research.md, data-model.md, contracts/, quickstart.md) trace to spec.md requirements |
| II. Template-Driven Workflow | ✅ PASS | All Phase 0/1 outputs follow canonical structure from plan prompt |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan agent produced defined outputs; research sub-agent dispatched for Phase 0; clear handoff to `/speckit.tasks` |
| IV. Test Optionality | ✅ PASS | Design does not introduce new test mandates beyond FR-009 (existing tests pass) |
| V. Simplicity and DRY | ✅ PASS | All patterns chosen are native/standard (Extract & Re-export, TYPE_CHECKING guards, lifespan DI, 40-line ErrorBoundary). No new deps. Complexity Tracking empty. |

**Post-design gate result**: PASS — proceed to Phase 2 (tasks).

## Project Structure

### Documentation (this feature)

```text
specs/009-codebase-cleanup-refactor/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (N/A — pure refactor, no new APIs)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── main.py                          # FastAPI app entry point
│   ├── config.py                        # Settings via pydantic-settings
│   ├── constants.py                     # Shared constants (labels, etc.)
│   ├── exceptions.py                    # Custom exception classes
│   ├── api/                             # FastAPI route handlers
│   │   ├── auth.py
│   │   ├── board.py
│   │   ├── chat.py
│   │   ├── projects.py
│   │   ├── settings.py
│   │   ├── tasks.py
│   │   ├── webhooks.py
│   │   └── workflow.py
│   ├── models/                          # Pydantic models
│   │   ├── board.py
│   │   ├── chat.py                      # To be split (Story 6)
│   │   ├── project.py
│   │   ├── settings.py
│   │   ├── task.py
│   │   └── user.py
│   ├── prompts/                         # AI prompt templates
│   │   ├── issue_generation.py
│   │   └── task_generation.py
│   └── services/                        # Business logic (decomposition targets)
│       ├── agent_tracking.py
│       ├── ai_agent.py
│       ├── cache.py
│       ├── completion_providers.py
│       ├── copilot_polling.py           # 4,044 lines → decompose (Story 2)
│       ├── database.py
│       ├── github_auth.py
│       ├── github_projects.py           # 4,448 lines → decompose (Story 2)
│       ├── session_store.py
│       ├── settings_store.py
│       ├── websocket.py
│       └── workflow_orchestrator.py     # 2,048 lines → decompose (Story 2)
├── tests/
│   ├── conftest.py
│   ├── test_api_e2e.py
│   ├── integration/
│   └── unit/                            # 13 unit test files
└── pyproject.toml

frontend/
├── src/
│   ├── App.tsx                          # Root component (Story 6 target)
│   ├── main.tsx
│   ├── components/
│   │   ├── board/                       # Board UI components
│   │   ├── chat/                        # Chat UI components
│   │   ├── common/                      # Dead code — ErrorDisplay, RateLimitIndicator (Story 1)
│   │   ├── settings/                    # Settings form components (Story 4 DRY)
│   │   └── sidebar/                     # Sidebar components
│   ├── hooks/                           # Custom hooks
│   ├── pages/                           # Page-level components
│   ├── services/
│   │   └── api.ts                       # Centralized API client
│   ├── types/
│   │   └── index.ts                     # Shared TypeScript types
│   └── utils/                           # Empty — to house extracted utilities (Story 4)
├── e2e/                                 # Playwright E2E tests
├── package.json
└── tsconfig.json
```

**Structure Decision**: Existing web application structure with separate `backend/` and `frontend/` directories is preserved. No new top-level directories. New modules created during decomposition go into existing `backend/src/services/` directory. New frontend utilities go into existing `frontend/src/utils/` directory.

## Complexity Tracking

> No constitution violations found. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
