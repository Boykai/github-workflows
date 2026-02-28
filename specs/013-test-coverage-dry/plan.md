# Implementation Plan: Increase Meaningful Test Coverage, Fix Discovered Bugs, and Enforce DRY Best Practices

**Branch**: `013-test-coverage-dry` | **Date**: 2026-02-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/013-test-coverage-dry/spec.md`

## Summary

Audit the entire test suite (backend: pytest, frontend: Vitest + Playwright) against documented application behavior, remove or rewrite misaligned and redundant tests, add missing coverage for critical flows (authentication, agent orchestration, project board, real-time sync, chat, webhooks), fix discovered bugs with regression tests, extract shared test utilities to enforce DRY, apply AAA/naming best practices, re-enable backend tests in CI, and organize test files to mirror the application module structure.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.4 / Node 20 (frontend)
**Primary Dependencies**: FastAPI, React 18, Vite 5, TanStack Query v5, dnd-kit, Socket.io
**Storage**: SQLite (aiosqlite, WAL mode) — in-memory for tests
**Testing**: pytest 7.4+ / pytest-asyncio 0.23+ / pytest-cov 4.1+ (backend), Vitest 4.0+ / @testing-library/react 16.3+ / happy-dom 20.6+ (frontend unit), Playwright 1.58+ (frontend E2E)
**Target Platform**: Linux server (backend), Modern browsers (frontend)
**Project Type**: web (backend + frontend)
**Performance Goals**: Tests must complete in CI within existing timeout limits; no flaky failures across 5+ consecutive runs
**Constraints**: No new testing frameworks; reuse pytest, Vitest, and Playwright; backend tests must run in CI (currently commented out)
**Scale/Scope**: ~39 backend test files (~560KB+), 3 frontend unit test files, 3 frontend E2E test files; 11 API modules, 14+ service modules, 13 hooks, 25+ components

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | spec.md exists with prioritized user stories (P1–P3), acceptance scenarios, and scope boundaries |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase follows single-responsibility agent model; outputs are well-defined markdown documents |
| IV. Test Optionality with Clarity | ✅ PASS | Tests are *explicitly requested* in the feature specification (this feature IS about testing); TDD approach (red-green-refactor) is specified for bug fixes |
| V. Simplicity and DRY | ✅ PASS | DRY is a core requirement of this feature; shared test utilities over premature abstraction; YAGNI applies — only test documented behavior |

**Gate Result**: ✅ ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/013-test-coverage-dry/
├── plan.md              # This file
├── research.md          # Phase 0: Research findings
├── data-model.md        # Phase 1: Test entity model
├── quickstart.md        # Phase 1: Developer quickstart for test workflow
├── contracts/           # Phase 1: Test conventions and contracts
│   └── test-conventions.md
└── tasks.md             # Phase 2 output (created by /speckit.tasks, NOT this phase)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/             # 11 endpoint modules (auth, board, chat, health, projects, settings, signal, tasks, webhooks, workflow, __init__)
│   ├── services/        # 14+ service modules and sub-packages
│   ├── models/          # Pydantic models
│   ├── middleware/       # Request middleware
│   ├── migrations/      # 5 SQL migrations
│   ├── config.py        # App configuration
│   ├── exceptions.py    # Custom exceptions
│   └── main.py          # App factory and lifespan
└── tests/
    ├── conftest.py      # Shared fixtures (mock_session, mock_db, client, service mocks)
    ├── helpers/          # NEW: Shared test utilities (factories, assertions, mocks)
    ├── unit/            # 33+ unit test files mirroring src/
    ├── integration/     # 3 integration test files
    └── test_api_e2e.py  # End-to-end smoke tests

frontend/
├── src/
│   ├── components/      # React components (auth, board, chat, common, settings, ui)
│   ├── hooks/           # 13 custom React hooks
│   ├── services/        # API client (api.ts)
│   ├── pages/           # 2 page components
│   ├── utils/           # Utility functions
│   └── test/            # Test setup and shared utilities
│       ├── setup.ts     # Vitest global setup (mocks, polyfills)
│       ├── test-utils.tsx  # renderWithProviders, createTestQueryClient
│       └── factories/   # NEW: Test data factories
├── e2e/                 # Playwright E2E tests
├── vitest.config.ts     # Vitest configuration
└── playwright.config.ts # Playwright configuration

.github/
└── workflows/
    └── ci.yml           # CI pipeline (backend pytest to be re-enabled)
```

**Structure Decision**: Web application (Option 2) — the repository already uses a `backend/` + `frontend/` split. Test files mirror the source structure: backend unit tests in `backend/tests/unit/` named `test_<module>.py`, frontend unit tests co-located in `frontend/src/` named `*.test.{ts,tsx}`, and frontend E2E tests in `frontend/e2e/`.

## Complexity Tracking

> No constitution violations to justify. All principles are satisfied.

## Constitution Re-Check (Post Phase 1 Design)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | All design artifacts trace back to spec.md requirements |
| II. Template-Driven Workflow | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow canonical structure |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase produced well-defined outputs for handoff to tasks phase |
| IV. Test Optionality with Clarity | ✅ PASS | Tests are the explicit subject of this feature; TDD approach defined for bug fixes in research.md |
| V. Simplicity and DRY | ✅ PASS | Design favors factory functions over complex abstractions; shared utilities use simple module pattern; no unnecessary frameworks introduced |

**Post-Design Gate Result**: ✅ ALL PASS — ready for Phase 2 (tasks generation via `/speckit.tasks`).
