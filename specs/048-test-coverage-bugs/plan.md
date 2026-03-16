# Implementation Plan: Increase Test Coverage & Surface Unknown Bugs

**Branch**: `048-test-coverage-bugs` | **Date**: 2026-03-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/048-test-coverage-bugs/spec.md`

## Summary

Grow backend line coverage from 69% to 80% and frontend coverage from 46/41/38/47 to 60/55/52/60 through phased test writing targeting highest-ROI untested modules. Promote existing local-only advanced tests (property, fuzz, chaos, concurrency) into CI. Add time-controlled testing for 15+ temporal behaviors, production-parity tests for code paths only exercised outside `TESTING=1`, architecture fitness functions to prevent layer violations, expanded property/fuzz testing for new modules, and WebSocket/real-time state lifecycle tests. The approach follows a ratchet strategy — CI thresholds are bumped only after each phase merges, never aspirationally.

## Technical Context

**Language/Version**: Python ≥3.12 (target 3.13) backend; TypeScript ~5.9 / React 19.2 frontend
**Primary Dependencies**: FastAPI ≥0.135, github-copilot-sdk, githubkit, Pydantic 2.12, aiosqlite (backend); Vite 7.3, @tanstack/react-query 5.90, Zod 4.3, react-hook-form 7.71 (frontend)
**Storage**: SQLite via aiosqlite (async), in-memory SQLite for test fixtures
**Testing**: pytest + pytest-asyncio + pytest-cov + hypothesis + mutmut (backend); Vitest 4.0 + @testing-library/react + @vitest/coverage-v8 + @stryker-mutator (frontend); Playwright 1.58 (E2E)
**Target Platform**: GitHub Actions CI (Ubuntu), Node 20/22, Python 3.12
**Project Type**: Web application (backend + frontend monorepo under `solune/`)
**Performance Goals**: Total backend test suite increase ≤90s; total frontend test suite increase ≤60s (SC-012)
**Constraints**: All new tests must use existing fixture patterns; no new external service dependencies; advanced tests must respect 120s per-test timeout in CI
**Scale/Scope**: Backend: ~131 source files, 31 untested → 0 untested in priority modules; Frontend: ~267 source files, 175 untested → reduce by ~100+ files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md exists with 11 prioritized user stories (P1–P11), Given-When-Then acceptance scenarios, and clear scope boundaries |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Plan phase produces plan.md, research.md, data-model.md, contracts/, quickstart.md per workflow |
| **IV. Test Optionality** | ✅ PASS | This feature explicitly requests tests — the entire spec is about test coverage. Tests are the deliverable, not optional overhead |
| **V. Simplicity & DRY** | ✅ PASS | All new tests follow existing template patterns (no new abstractions). Test structure mirrors established conventions. No new frameworks introduced except `freezegun` (single-purpose time-freezing library) |

**Gate result**: ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/048-test-coverage-bugs/
├── plan.md              # This file
├── research.md          # Phase 0: Research findings
├── data-model.md        # Phase 1: Coverage entity model
├── quickstart.md        # Phase 1: Quick-start guide for contributors
├── contracts/           # Phase 1: CI contract definitions
│   ├── ci-advanced-tests.md     # Advanced test job contract
│   └── ci-mutation.md           # Mutation testing workflow contract
└── tasks.md             # Phase 2 output (speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
solune/backend/
├── src/
│   ├── api/                      # Route handlers (apps, cleanup, metadata, signal — untested)
│   ├── models/                   # Pydantic models
│   ├── services/
│   │   ├── github_projects/      # 9 untested modules (graphql, issues, PRs, etc.)
│   │   ├── copilot_polling/      # 4 untested modules (state, pipeline, helpers, validation)
│   │   ├── agents/               # Agent service logic
│   │   ├── chores/               # Template builder, chat
│   │   ├── pipelines/            # Pipeline service
│   │   ├── tools/                # Tool presets
│   │   └── workflow_orchestrator/ # Orchestrator models
│   ├── config.py
│   ├── dependencies.py           # DI resolution (untested)
│   └── protocols.py              # Protocol definitions (untested)
└── tests/
    ├── unit/                     # ~50 existing test files
    ├── integration/              # 8 existing integration tests
    ├── property/                 # 5 property-based tests (LOCAL ONLY)
    ├── fuzz/                     # 2 fuzz tests (LOCAL ONLY)
    ├── chaos/                    # 3 chaos tests (LOCAL ONLY)
    ├── concurrency/              # 3 concurrency tests (LOCAL ONLY)
    ├── architecture/             # NEW: Import direction enforcement
    └── conftest.py               # Shared fixtures (mock_db, client, mock_github_service, etc.)

solune/frontend/
├── src/
│   ├── __tests__/fuzz/           # 2 fuzz tests (discovered but verify CI inclusion)
│   ├── components/               # 14 dirs, ~175 untested files across all
│   │   ├── settings/             # 14 untested components
│   │   ├── board/                # 12 untested components
│   │   ├── pipeline/             # 8 untested components
│   │   ├── agents/               # 8 untested components
│   │   ├── tools/                # 9 untested components
│   │   ├── chores/               # 10 untested components
│   │   ├── chat/                 # 6 untested components
│   │   └── ...
│   ├── hooks/                    # ~24 untested hooks
│   ├── layout/                   # 8 untested layout components
│   ├── services/
│   │   └── schemas/              # 6 Zod schema files (pure validators, untested)
│   ├── lib/                      # 3 untested lib modules
│   └── utils/                    # 3 untested util modules
├── vitest.config.ts              # Coverage thresholds: 46/41/38/47
└── package.json                  # Scripts: test, test:coverage, test:mutate

.github/workflows/
├── ci.yml                        # Current CI: backend + frontend jobs (to be extended)
└── mutation.yml                  # NEW: Scheduled mutation testing workflow
```

**Structure Decision**: Existing web application structure (`solune/backend/` + `solune/frontend/`) is used as-is. New test files are added within the existing `tests/` hierarchies following established naming conventions. One new test directory (`tests/architecture/`) is added for fitness function tests. One new CI workflow file (`.github/workflows/mutation.yml`) is added. The CI workflow (`.github/workflows/ci.yml`) is extended with an additional job for advanced tests.

## Complexity Tracking

> No constitution violations — table intentionally left empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
