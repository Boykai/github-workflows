# Implementation Plan: Bug Basher — Full Codebase Review & Fix

**Branch**: `001-bug-basher` | **Date**: 2026-03-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-bug-basher/spec.md`

## Summary

Perform a comprehensive bug bash code review of the entire codebase (141 Python files in `solune/backend/src/`, 409 TypeScript/TSX files in `solune/frontend/src/`). Systematically audit all files across five priority-ordered categories: security vulnerabilities, runtime errors, logic bugs, test quality gaps, and code quality issues. For each clear bug found, fix it directly with at least one regression test. For ambiguous issues, flag with `TODO(bug-bash)` comments. Produce a final summary table of all findings. All existing tests and lint checks must pass after fixes.

This is a **process-oriented feature** — it does not add new functionality, APIs, or dependencies. Instead, it applies targeted fixes across the existing codebase while preserving the current architecture, public API surface, and code style.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI, aiosqlite, Pydantic, OpenAI SDK, Sentry (backend); React 18, TanStack Query, Vite, lucide-react, Tailwind CSS 4 (frontend)
**Storage**: SQLite via aiosqlite (backend)
**Testing**: pytest with pytest-asyncio, hypothesis, freezegun (backend); Vitest with happy-dom, @testing-library/react, Playwright E2E (frontend)
**Target Platform**: Web application (SPA served by Vite, API served by FastAPI/Uvicorn)
**Project Type**: Web (frontend + backend monorepo under `solune/`)
**Performance Goals**: N/A — bug fixes must not degrade existing performance characteristics
**Constraints**: No new dependencies; no public API changes; no architecture changes; each fix minimal and focused; preserve code style; all tests + lint green after fixes
**Scale/Scope**: ~550 source files total (141 Python + 409 TypeScript/TSX); 5 bug categories audited in priority order; test suites: backend coverage ≥75%, frontend coverage thresholds (50% statements, 44% branches, 41% functions, 50% lines)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | `spec.md` completed with 6 prioritized user stories (P1–P3), acceptance scenarios per story, edge cases, and 15 functional requirements |
| **II. Template-Driven Workflow** | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| **III. Agent-Orchestrated Execution** | ✅ PASS | Plan phase produces plan.md, research.md, data-model.md, contracts/, quickstart.md as defined. Bug-bashing execution decomposes into category-based passes (security → runtime → logic → tests → quality) |
| **IV. Test Optionality** | ✅ PASS | Tests are mandated by spec: FR-004 requires at least one regression test per bug fix; FR-007 requires full test suite to pass. This is explicit spec requirement, not optional |
| **V. Simplicity and DRY** | ✅ PASS | Each fix is minimal and focused (FR-014). No refactors, no new abstractions. Fixes address exactly one bug each. Ambiguous cases flagged rather than over-engineered |

**Gate Result**: ✅ All principles satisfied. No violations requiring justification.

**Post-Phase 1 Re-check**: ✅ All principles remain satisfied. The process-oriented nature of this feature (fixing existing code, not adding new features) inherently aligns with simplicity and DRY — no new abstractions are introduced.

## Project Structure

### Documentation (this feature)

```text
specs/001-bug-basher/
├── plan.md              # This file
├── research.md          # Phase 0 output — research on audit strategy and tooling
├── data-model.md        # Phase 1 output — bug report entity model
├── quickstart.md        # Phase 1 output — developer guide for bug-bash workflow
├── contracts/           # Phase 1 output — bug report format contract
│   └── bug-report.yaml  # Summary table schema
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── src/
│   │   ├── api/                    # FastAPI route handlers (11 modules)
│   │   ├── middleware/             # Request middleware (auth, CORS, rate limiting)
│   │   ├── migrations/            # SQLite migration scripts (31+ files)
│   │   ├── models/                # Pydantic models
│   │   ├── services/              # Business logic
│   │   │   ├── agents/            # AI agent services
│   │   │   ├── chores/            # Chore scheduling services
│   │   │   ├── copilot_polling/   # GitHub Copilot polling
│   │   │   ├── github_projects/   # GitHub Projects integration
│   │   │   ├── pipelines/         # Pipeline management
│   │   │   ├── tools/             # Tool integrations
│   │   │   └── workflow_orchestrator/  # Workflow state machine
│   │   ├── config.py              # Application configuration
│   │   ├── dependencies.py        # FastAPI dependency injection
│   │   ├── exceptions.py          # Custom exception classes
│   │   ├── logging_utils.py       # Structured logging utilities
│   │   ├── main.py                # Application entry point
│   │   └── utils.py               # Shared utilities
│   └── tests/
│       ├── unit/                  # Unit tests
│       ├── integration/           # Integration tests
│       ├── property/              # Hypothesis property tests
│       ├── fuzz/                  # Fuzz tests
│       ├── chaos/                 # Chaos engineering tests
│       ├── concurrency/           # Concurrency tests
│       ├── architecture/          # Architecture validation tests
│       └── helpers/               # Test utilities and fixtures
├── frontend/
│   ├── src/
│   │   ├── components/            # React components
│   │   ├── hooks/                 # Custom React hooks
│   │   ├── lib/                   # Shared libraries (icons barrel)
│   │   ├── services/              # API client and schemas
│   │   ├── utils/                 # Utility functions
│   │   ├── __tests__/             # Test files
│   │   ├── test/                  # Test setup and helpers
│   │   └── e2e/                   # E2E test fixtures
│   └── e2e/                       # Playwright E2E tests
└── docs/                          # Documentation
```

**Structure Decision**: Web application structure — existing `solune/backend/` and `solune/frontend/` layout. Bug-bash audits all files in-place. No new directories or structural changes. Fixes modify existing files only; new files are limited to regression tests when needed.

## Implementation Phases

### Phase 1 — Security Vulnerability Audit (Priority: P1)

| Step | Description | Depends On | Scope |
|------|-------------|------------|-------|
| 1.1 | Audit authentication & authorization logic | — | `middleware/`, `api/`, `dependencies.py` |
| 1.2 | Audit input validation and injection risks | — | `api/` route handlers, Pydantic models |
| 1.3 | Scan for exposed secrets/tokens in code and config | — | All source files, config files, `.env` patterns |
| 1.4 | Review insecure defaults (CORS, rate limiting, crypto) | — | `config.py`, `middleware/`, `main.py` |
| 1.5 | Run `bandit -r src/` and address findings | 1.1–1.4 | Backend Python source |
| 1.6 | Run ESLint security plugin checks | — | Frontend TypeScript source |

**Verification**: `bandit -r src/` clean; ESLint security rules pass; no secrets in source; regression tests for each fix.

### Phase 2 — Runtime Error Elimination (Priority: P1)

| Step | Description | Depends On | Scope |
|------|-------------|------------|-------|
| 2.1 | Audit exception handling (try/catch/except) | Phase 1 | All service modules, API handlers |
| 2.2 | Check for null/None dereferences | — | All source files |
| 2.3 | Audit resource management (file handles, DB connections) | — | `aiosqlite` usage, file I/O |
| 2.4 | Identify race conditions in async code | — | `asyncio` tasks, shared state, caches |
| 2.5 | Check for missing imports and type errors | — | All modules |

**Verification**: `pyright src` clean; `npm run type-check` clean; regression tests for each fix.

### Phase 3 — Logic Bug Resolution (Priority: P2)

| Step | Description | Depends On | Scope |
|------|-------------|------------|-------|
| 3.1 | Trace state transitions in workflow orchestrator | Phase 2 | `workflow_orchestrator/`, `transitions.py` |
| 3.2 | Verify API call parameters and return handling | — | All API client code, service calls |
| 3.3 | Check boundary conditions (off-by-one, pagination) | — | Loops, list operations, pagination logic |
| 3.4 | Validate control flow and return values | — | All functions with conditional logic |

**Verification**: Full pytest suite passes; regression tests for each logic fix.

### Phase 4 — Test Quality Improvement (Priority: P2)

| Step | Description | Depends On | Scope |
|------|-------------|------------|-------|
| 4.1 | Audit mock usage for leaks (MagicMock in prod paths) | Phase 3 | All test files |
| 4.2 | Identify tautological assertions | — | All test assertions |
| 4.3 | Find untested critical code paths | — | Coverage gaps in services/ |
| 4.4 | Add missing edge case tests | 4.3 | Test files for identified gaps |

**Verification**: `pytest --cov` meets thresholds; `npm run test:coverage` meets thresholds; no mock leaks.

### Phase 5 — Code Quality Cleanup (Priority: P3)

| Step | Description | Depends On | Scope |
|------|-------------|------------|-------|
| 5.1 | Remove dead code (unused functions, variables, imports) | Phase 4 | All source files |
| 5.2 | Consolidate duplicated logic | 5.1 | Cross-file duplicate detection |
| 5.3 | Add error logging for silent failures | — | Exception handlers with `pass` or bare `except` |
| 5.4 | Replace hardcoded values with configuration | — | Magic numbers, hardcoded strings |

**Verification**: `ruff check src tests` clean; `npm run lint` clean; all tests pass.

### Phase 6 — Summary & Validation

| Step | Description | Depends On | Scope |
|------|-------------|------------|-------|
| 6.1 | Run full backend test suite | Phases 1–5 | `pytest --timeout=60` |
| 6.2 | Run full frontend test suite | Phases 1–5 | `npm run test` |
| 6.3 | Run all linting/formatting checks | 6.1–6.2 | `ruff`, `pyright`, `eslint`, `prettier` |
| 6.4 | Generate final summary table | 6.1–6.3 | All identified issues |
| 6.5 | Review all `TODO(bug-bash)` comments | 6.4 | Flagged ambiguous issues |

**Verification**: Zero test failures; zero lint errors; complete summary table with every finding categorized.

## Complexity Tracking

> No constitution violations to justify. All changes follow simplicity and DRY principles. Each fix is minimal, focused, and addresses exactly one bug.
