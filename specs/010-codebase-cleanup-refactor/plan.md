# Implementation Plan: Codebase Cleanup — Remove Dead Code, Backwards Compatibility & Stale Tests

**Branch**: `010-codebase-cleanup-refactor` | **Date**: 2026-02-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/010-codebase-cleanup-refactor/spec.md`

## Summary

Targeted codebase cleanup to improve maintainability and reduce technical debt. This iteration focuses on removing backwards compatibility shims, eliminating dead code (unused types, silent exception suppression, stale constants), consolidating duplicated logic (cache patterns, error handling, hook factories), and removing stale tests. Pure refactor — no user-facing behavior changes. Total codebase is ~33k LOC (22,903 backend src + 10,219 frontend src); target ≥5% reduction through dead code removal and deduplication.

Building on previous cleanups (specs 007 and 009) which decomposed monolithic service files and migrated `datetime.utcnow()`. This iteration addresses the remaining technical debt discovered during those refactors.

## Technical Context

**Language/Version**: Python 3.11+ (backend, pyright targets 3.12), TypeScript ~5.4 (frontend)
**Primary Dependencies**: FastAPI 0.109, Pydantic 2.x, httpx, aiosqlite (backend); React 18, TanStack Query v5, Vite 5, dnd-kit (frontend)
**Storage**: SQLite via aiosqlite (async)
**Testing**: pytest 7.4 + pytest-asyncio 0.23 (backend), Vitest 4.0 + React Testing Library 16.3 (frontend unit), Playwright 1.58 (frontend e2e)
**Target Platform**: Linux server (Docker), browser (SPA served via nginx)
**Project Type**: Web application — separate `backend/` and `frontend/` directories
**Performance Goals**: No measurable regression in startup time or API p95 latency after refactoring
**Constraints**: Each user story delivered as one atomic commit/PR; all tests must pass at each merge point
**Scale/Scope**: ~33,122 LOC (22,903 backend src + 10,219 frontend src); ~20,708 backend test LOC; ~1,917 frontend test LOC; 10+ silent exception handlers; 6+ unused type exports; 8+ cache pattern duplications

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | `spec.md` fully written with 5 prioritized user stories (P1–P3), acceptance scenarios, edge cases, and assumptions |
| II. Template-Driven Workflow | ✅ PASS | All artifacts use canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | ✅ PASS | Single plan agent producing well-defined outputs for subsequent phases |
| IV. Test Optionality | ✅ PASS | Spec requires existing tests to continue passing (FR-009) but mandates no new test frameworks. Stale test removal is explicitly scoped (Story 4). |
| V. Simplicity and DRY | ✅ PASS | The entire feature is *about* enforcing simplicity and DRY. Consolidation targets real duplication, not premature abstraction. |

**Gate result**: PASS — proceed to Phase 0.

### Post-Design Re-evaluation (after Phase 1)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | All design artifacts (research.md, data-model.md, contracts/, quickstart.md) trace to spec.md requirements |
| II. Template-Driven Workflow | ✅ PASS | All Phase 0/1 outputs follow canonical structure from plan template |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan agent produced defined outputs; research resolved all unknowns; clear handoff to `/speckit.tasks` |
| IV. Test Optionality | ✅ PASS | Design does not introduce new test mandates beyond FR-009 (existing tests pass) |
| V. Simplicity and DRY | ✅ PASS | All consolidation patterns use existing framework features (decorators, context managers, hook composition). No new dependencies introduced. Complexity Tracking empty. |

**Post-design gate result**: PASS — proceed to Phase 2 (tasks).

## Project Structure

### Documentation (this feature)

```text
specs/010-codebase-cleanup-refactor/
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
│   ├── constants.py                     # Shared constants — audit for stale entries
│   ├── exceptions.py                    # Custom exception classes
│   ├── utils.py                         # Shared utilities (utcnow, etc.)
│   ├── api/                             # FastAPI route handlers
│   │   ├── auth.py
│   │   ├── board.py                     # Cache pattern duplication (Story 3)
│   │   ├── chat.py                      # Cache pattern duplication (Story 3)
│   │   ├── projects.py                  # Cache pattern duplication (Story 3)
│   │   ├── settings.py                  # Silent exception handler (Story 2)
│   │   ├── tasks.py
│   │   ├── webhooks.py
│   │   └── workflow.py                  # Silent exception handler (Story 2)
│   ├── models/                          # Pydantic models
│   │   ├── board.py
│   │   ├── chat.py
│   │   ├── project.py
│   │   ├── settings.py
│   │   ├── task.py
│   │   └── user.py
│   ├── prompts/                         # AI prompt templates
│   │   ├── issue_generation.py
│   │   └── task_generation.py
│   └── services/                        # Business logic
│       ├── ai_agent.py                  # Silent JSON parse handlers (Story 2)
│       ├── cache.py                     # Cache utilities — consolidation target
│       ├── copilot_polling/             # Already decomposed (spec 009)
│       │   ├── agent_output.py          # Silent exception handler (Story 2)
│       │   ├── completion.py
│       │   ├── helpers.py
│       │   ├── pipeline.py              # Legacy code path comments (Story 1)
│       │   ├── polling_loop.py
│       │   ├── recovery.py
│       │   └── state.py
│       ├── encryption.py                # Legacy plaintext fallback (Story 1)
│       ├── github_projects/             # Already decomposed (spec 009)
│       │   ├── graphql.py
│       │   └── service.py               # 3,779 lines — largest file
│       ├── model_fetcher.py             # Silent exception handler (Story 2)
│       ├── signal_chat.py               # Silent exception handler (Story 2)
│       ├── workflow_orchestrator/
│       │   ├── config.py                # Silent exception handler (Story 2)
│       │   └── orchestrator.py
│       └── ...
├── tests/
│   ├── conftest.py
│   ├── unit/                            # 41 unit test files
│   │   ├── test_token_encryption.py     # Legacy fallback test (Story 4)
│   │   └── ...
│   └── integration/                     # 3 integration test files
└── pyproject.toml

frontend/
├── src/
│   ├── App.tsx
│   ├── main.tsx
│   ├── components/
│   │   ├── board/
│   │   ├── chat/
│   │   ├── common/                      # ErrorBoundary
│   │   ├── settings/
│   │   └── ui/
│   ├── hooks/
│   │   ├── useAgentConfig.ts            # Duplicated comparison logic (Story 3)
│   │   ├── useAuth.ts                   # Repeated useQuery pattern (Story 3)
│   │   ├── useProjects.ts              # Repeated useQuery pattern (Story 3)
│   │   ├── useSettings.ts              # Repeated useQuery/mutation pattern (Story 3)
│   │   ├── useRealTimeSync.ts
│   │   └── ...
│   ├── pages/
│   ├── services/
│   │   └── api.ts                       # Centralized API client
│   ├── types/
│   │   └── index.ts                     # 6+ unused type exports (Story 2)
│   └── utils/
├── e2e/                                 # Playwright E2E tests
├── package.json
└── tsconfig.json
```

**Structure Decision**: Existing web application structure with separate `backend/` and `frontend/` directories is preserved. No new top-level directories. Consolidation creates shared utilities within existing directory structures. Dead code removal reduces file count and LOC.

## Complexity Tracking

> No constitution violations found. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
