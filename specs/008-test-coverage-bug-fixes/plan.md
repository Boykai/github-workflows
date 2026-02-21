# Implementation Plan: Test Coverage & Bug Fixes

**Branch**: `008-test-coverage-bug-fixes` | **Date**: 2026-02-20 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/008-test-coverage-bug-fixes/spec.md`

## Summary

Achieve ≥85% aggregate line coverage (with a per-file 70% floor) for both the Python/FastAPI backend and the React/TypeScript frontend. Establish DRY shared test fixtures, configure coverage thresholds in tooling, and fix any bugs or dead code discovered during test writing. New unit/component tests run offline; existing integration/e2e tests are untouched.

## Technical Context

**Language/Version**: Python ≥3.11 (Pyright targets 3.12), TypeScript ~5.4 (target ES2022)  
**Primary Dependencies**: FastAPI ≥0.109, React 18.3, TanStack Query 5.17, Pydantic 2.x, httpx, aiosqlite  
**Storage**: SQLite via aiosqlite (WAL mode, migration-managed schema)  
**Testing**: pytest + pytest-asyncio (auto mode) + pytest-cov (backend); Vitest 4.x + happy-dom + @vitest/coverage-v8 + React Testing Library (frontend)  
**Target Platform**: Linux server (backend), Web/Chromium (frontend)  
**Project Type**: Web application (backend + frontend)  
**Performance Goals**: Test suite completes in <60s backend, <30s frontend on CI  
**Constraints**: No network access for new unit/component tests; all external deps mocked  
**Scale/Scope**: ~4,019 untested backend LOC across 13 modules; ~4,417 untested frontend LOC across 7 hooks/services + 28 components

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | PASS | `spec.md` written with prioritized stories, acceptance scenarios, clarifications resolved |
| II. Template-Driven Workflow | PASS | All artifacts use canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | PASS | Plan produced by `/speckit.plan` agent; tasks will be produced by `/speckit.tasks` |
| IV. Test Optionality with Clarity | PASS | Tests are **explicitly requested** in the feature specification (the entire feature IS tests). TDD not mandated — tests added alongside coverage gaps. |
| V. Simplicity and DRY | PASS | Spec requires DRY fixtures, simple tests. No premature abstraction. Shared conftest/setup.ts patterns reused across all new test files. |

**Gate result**: ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/008-test-coverage-bug-fixes/
├── plan.md              # This file
├── research.md          # Phase 0: Mocking strategies, coverage tooling research
├── data-model.md        # Phase 1: Test fixture & mock entity definitions
├── quickstart.md        # Phase 1: How to run tests and check coverage
├── contracts/           # Phase 1: Coverage configuration contracts
│   ├── backend-coverage.toml
│   └── frontend-coverage.json
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/           # 8 route modules (6 untested: auth, chat, projects, settings, tasks, workflow)
│   ├── models/        # 6 Pydantic model modules (partial coverage via test_models.py)
│   ├── services/      # 12 service modules (5 untested: agent_tracking, completion_providers, database, session_store, settings_store)
│   ├── prompts/       # 2 prompt modules (0 tests)
│   ├── config.py      # Settings (0 tests)
│   ├── constants.py   # Constants (0 tests)
│   ├── exceptions.py  # Exception classes (0 tests)
│   └── main.py        # App factory (0 tests)
└── tests/
    ├── conftest.py    # Shared fixtures (expand with TestClient, mock DB, mock services)
    ├── unit/          # 10 existing + new test files
    ├── integration/   # 1 existing (untouched)
    └── test_api_e2e.py # 1 existing (untouched)

frontend/
├── src/
│   ├── components/    # 6 subdirs, 28 .tsx files (0 tests)
│   │   ├── auth/      #   1 component
│   │   ├── board/     #  10 components
│   │   ├── chat/      #   5 components
│   │   ├── common/    #   2 components
│   │   ├── settings/  #   7 components
│   │   └── sidebar/   #   3 components
│   ├── hooks/         # 9 hooks (3 tested, 6 untested)
│   ├── services/      # api.ts (0 tests)
│   ├── pages/         # 2 pages (0 tests)
│   └── test/
│       ├── setup.ts   # Existing mocks (expand with API, router, theme test utils)
│       └── test-utils.tsx  # NEW: shared render wrapper with providers
├── e2e/               # 3 Playwright specs (untouched)
└── vitest.config.ts   # Add coverage thresholds
```

**Structure Decision**: Web application (Option 2). No structural changes needed — tests go into existing `backend/tests/unit/` and co-located with frontend source files as `*.test.tsx`.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
