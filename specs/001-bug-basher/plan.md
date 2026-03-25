# Implementation Plan: Bug Basher

**Branch**: `001-bug-basher` | **Date**: 2026-03-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-bug-basher/spec.md`

## Summary

Perform a comprehensive bug bash code review of the entire codebase, covering both the Python/FastAPI backend (`solune/backend/`) and the TypeScript/React frontend (`solune/frontend/`). The review audits all source files across five priority-ordered categories: security vulnerabilities, runtime errors, logic bugs, test quality gaps, and code quality issues. Each confirmed bug is fixed in-place with a regression test; ambiguous findings are flagged with `# TODO(bug-bash):` comments. The approach is file-by-file, priority-ordered scanning with validation via existing test suites (`pytest`, `vitest`) and linters (`ruff`, `eslint`, `pyright`, `tsc`).

## Technical Context

**Language/Version**: Python ≥3.12 (target 3.13), TypeScript 5.9, Node 25
**Primary Dependencies**: FastAPI 0.135+, React 19.2, Vite 8.0, Pydantic 2.12+, React Query 5.91+, Zod 4.3+
**Storage**: SQLite (async via aiosqlite) at `/var/lib/solune/data/settings.db`
**Testing**: Backend: pytest 9+ (pytest-asyncio, pytest-cov — 75% coverage minimum); Frontend: Vitest 4+ (happy-dom, @testing-library/react)
**Target Platform**: Linux server (backend), browser (frontend)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: N/A — this is a code review/fix feature, not a runtime feature
**Constraints**: No new dependencies, no public API changes, no architecture changes, minimal focused fixes only
**Scale/Scope**: ~143 backend source files, ~413 frontend source files, ~193 backend test files, ~152 frontend test files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First Development** | ✅ PASS | `spec.md` exists with 5 prioritized user stories (P1–P5), Given-When-Then acceptance scenarios, and clear scope boundaries |
| **II. Template-Driven Workflow** | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| **III. Agent-Orchestrated Execution** | ✅ PASS | Plan phase produces plan.md, research.md, data-model.md, contracts/, quickstart.md; tasks phase follows separately |
| **IV. Test Optionality with Clarity** | ✅ PASS | Tests are explicitly required by spec (FR-003: "at least one new regression test per bug", FR-006: "full test suite MUST pass") |
| **V. Simplicity and DRY** | ✅ PASS | Each fix must be "minimal and focused — no drive-by refactors" (FR-011); YAGNI enforced by constraint FR-009 (no new dependencies) |

**GATE RESULT: ✅ PASS — All principles satisfied. Proceeding to Phase 0.**

## Project Structure

### Documentation (this feature)

```text
specs/001-bug-basher/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── src/
│   │   ├── api/              # 21 FastAPI route modules
│   │   ├── models/           # 25 Pydantic data models
│   │   ├── services/         # 38+ service modules (core, polling, GitHub, orchestration)
│   │   ├── middleware/        # 4 middleware components (rate_limit, csrf, csp, request_id)
│   │   ├── prompts/          # 3 LLM prompt templates
│   │   ├── migrations/       # Database schema migrations
│   │   ├── main.py           # FastAPI app entry point
│   │   ├── config.py         # Settings and configuration
│   │   ├── constants.py      # Application constants
│   │   ├── dependencies.py   # FastAPI dependency injection
│   │   ├── exceptions.py     # Custom exception classes
│   │   ├── logging_utils.py  # Logging configuration
│   │   ├── protocols.py      # Protocol/interface definitions
│   │   └── utils.py          # Shared utility functions
│   └── tests/
│       ├── unit/             # Unit tests
│       ├── integration/      # Integration tests
│       ├── property/         # Property-based tests (Hypothesis)
│       ├── fuzz/             # Fuzz tests
│       ├── chaos/            # Chaos engineering tests
│       ├── concurrency/      # Concurrency tests
│       └── architecture/     # Architecture tests
├── frontend/
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/            # Page components
│   │   ├── hooks/            # Custom React hooks
│   │   ├── services/         # API service layer
│   │   ├── context/          # React context providers
│   │   ├── types/            # TypeScript type definitions
│   │   ├── utils/            # Utility functions
│   │   ├── lib/              # Library wrappers
│   │   ├── layout/           # Layout components
│   │   ├── constants/        # Frontend constants
│   │   ├── data/             # Static data
│   │   ├── App.tsx           # Root component
│   │   └── main.tsx          # Entry point
│   └── e2e/                  # Playwright E2E tests
├── docs/                     # Project documentation
└── scripts/                  # Build and validation scripts
```

**Structure Decision**: Web application structure (Option 2). The codebase is organized under `solune/` with separate `backend/` (Python/FastAPI) and `frontend/` (TypeScript/React) directories. The bug bash reviews both in priority order, starting with backend (higher risk surface: auth, DB, API) then frontend.

## Complexity Tracking

> No constitution violations detected. All fixes are minimal, focused, and within existing patterns.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |
