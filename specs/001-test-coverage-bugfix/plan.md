# Implementation Plan: Improve Test Coverage to 85% and Fix Discovered Bugs

**Branch**: `001-test-coverage-bugfix` | **Date**: 2026-02-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-test-coverage-bugfix/spec.md`

## Summary

Audit the existing test suites for both the frontend (Vitest + React Testing Library) and backend (PyTest), measure baseline coverage, write unit/integration/edge-case tests to reach ≥85% aggregate coverage, fix any bugs discovered during testing, and document coverage deltas and bug fixes in the PR description.

## Technical Context

**Language/Version**: TypeScript 5.4 (frontend), Python 3.11+ (backend)
**Primary Dependencies**: React 18, Vitest 4, @testing-library/react 16, happy-dom (frontend); FastAPI, PyTest 7, pytest-asyncio, pytest-cov (backend)
**Storage**: SQLite via aiosqlite (backend); browser-only state via React Query (frontend)
**Testing**: Vitest with @vitest/coverage-v8 (frontend), PyTest with pytest-cov (backend)
**Target Platform**: Web application — Node.js/browser (frontend), Linux server (backend)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: N/A — testing infrastructure task; no runtime performance targets
**Constraints**: No new runtime dependencies; tests must be deterministic and isolated; aggregate coverage ≥85%
**Scale/Scope**: ~44 frontend source files, ~36 backend source files; 3 existing frontend test files, 11 existing backend unit test files + 1 integration test file

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | spec.md exists with prioritized user stories (P1–P3), acceptance scenarios, and scope boundaries |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | ✅ PASS | Specify phase completed; Plan phase in progress; single-responsibility handoff maintained |
| IV. Test Optionality with Clarity | ✅ PASS | Tests are explicitly the core deliverable of this feature — spec mandates testing |
| V. Simplicity and DRY | ✅ PASS | No new abstractions introduced; tests follow AAA pattern; bug fixes are localized |

No violations detected. No entries needed in Complexity Tracking.

### Post-Design Re-evaluation (after Phase 1)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | All design artifacts (research, data-model, contracts, quickstart) align with spec requirements |
| II. Template-Driven Workflow | ✅ PASS | All generated artifacts follow plan-template.md structure; no custom sections added |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase complete with all outputs; ready for handoff to tasks phase |
| IV. Test Optionality with Clarity | ✅ PASS | Test contracts and patterns documented in contracts/coverage-contract.md |
| V. Simplicity and DRY | ✅ PASS | Research resolved all unknowns without introducing complexity; reuses existing tools and conventions |

No new violations. Design phase complete.

## Project Structure

### Documentation (this feature)

```text
specs/001-test-coverage-bugfix/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── coverage-contract.md
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/             # FastAPI route handlers
│   ├── models/          # Pydantic models
│   ├── services/        # Business logic services
│   ├── config.py        # App configuration
│   ├── constants.py     # Constants
│   ├── exceptions.py    # Custom exceptions
│   └── main.py          # FastAPI app entry point
└── tests/
    ├── conftest.py      # Shared fixtures
    ├── unit/            # Unit tests (11 existing files)
    └── integration/     # Integration tests (1 existing file)

frontend/
├── src/
│   ├── components/      # React components (auth, board, chat, common, settings, sidebar)
│   ├── hooks/           # Custom React hooks (3 existing test files co-located)
│   ├── pages/           # Page-level components
│   ├── services/        # API client
│   ├── types/           # TypeScript type definitions
│   ├── test/            # Test setup (setup.ts)
│   ├── App.tsx          # Root component
│   └── main.tsx         # Entry point
├── vitest.config.ts     # Vitest configuration
└── e2e/                 # Playwright E2E tests (out of scope)
```

**Structure Decision**: Web application (Option 2). Tests are co-located with source for frontend hooks (existing convention); backend tests are in a separate `tests/` directory with `unit/` and `integration/` subdirectories (existing convention). No structural changes needed — new tests follow existing placement conventions.

## Complexity Tracking

> No violations detected in Constitution Check. No entries required.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
