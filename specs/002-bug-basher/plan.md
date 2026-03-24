# Implementation Plan: Bug Basher — Full Codebase Review & Fix

**Branch**: `002-bug-basher` | **Date**: 2026-03-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-bug-basher/spec.md`

## Summary

This plan covers a comprehensive bug bash code review of the entire Solune platform codebase. The review audits all backend (Python/FastAPI) and frontend (TypeScript/React) source files across five bug categories in priority order: security vulnerabilities, runtime errors, logic bugs, test quality issues, and code quality problems. Each confirmed bug is fixed with a minimal, focused change accompanied by at least one regression test. Ambiguous issues are flagged with `TODO(bug-bash)` comments for human review. A summary report is produced at completion cataloguing all findings.

The review follows a phased approach — scanning backend first (highest complexity and security-critical surface), then frontend, then shared infrastructure (Docker, CI, scripts). Each phase produces verified fixes with passing test suites before proceeding.

## Technical Context

**Language/Version**: Python 3.12+ (backend), TypeScript 5.9 (frontend)
**Primary Dependencies**: FastAPI, Pydantic v2, aiosqlite, httpx, github-copilot-sdk, cryptography (backend); React 19, TanStack Query v5, Vite 8, Tailwind CSS 4, Zod v4 (frontend)
**Storage**: SQLite with WAL mode via aiosqlite
**Testing**: pytest 9.0+ with pytest-asyncio, pytest-cov, hypothesis, freezegun (backend); Vitest 4.0+ with Testing Library, Playwright 1.58 (frontend)
**Target Platform**: Web application (SPA + FastAPI API server, Docker Compose orchestration)
**Project Type**: Web (monorepo under `solune/` with `backend/` and `frontend/` subdirectories)
**Performance Goals**: N/A — this is a review/fix effort, not a performance feature
**Constraints**: No architecture changes, no public API surface changes, no new dependencies, preserve existing code style, each fix must be minimal and focused
**Scale/Scope**: ~143 Python source files, ~413 TypeScript/TSX source files, ~183 backend test files, ~152 frontend test files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | `spec.md` completed with 5 prioritized user stories (P1–P5), acceptance scenarios, edge cases, and functional requirements |
| **II. Template-Driven Workflow** | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| **III. Agent-Orchestrated Execution** | ✅ PASS | Plan phase produces plan.md, research.md, data-model.md, contracts/, quickstart.md as defined by workflow |
| **IV. Test Optionality** | ✅ PASS | Tests are mandated by the spec itself (FR-003: regression test per bug fix, FR-006: full test suite must pass). This is appropriate for a bug fix feature where test coverage is a core requirement |
| **V. Simplicity and DRY** | ✅ PASS | Each fix is minimal and focused — no drive-by refactors per FR-008/FR-010. No premature abstraction introduced |

**Gate Result**: ✅ All principles satisfied. No violations requiring justification.

**Post-Design Re-check**: ✅ All principles still satisfied after Phase 1 design. The review process introduces no new entities, APIs, or abstractions — it only fixes existing code.

## Project Structure

### Documentation (this feature)

```text
specs/002-bug-basher/
├── plan.md              # This file
├── research.md          # Phase 0 output — research findings
├── data-model.md        # Phase 1 output — entity/audit model definitions
├── quickstart.md        # Phase 1 output — developer quickstart guide
├── contracts/           # Phase 1 output — review process contracts
│   └── bug-report.yaml  # Bug report schema definition
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── src/
│   │   ├── api/            # Route handlers — security audit target (auth, CSRF, input validation)
│   │   ├── models/         # Pydantic models — type safety and validation review
│   │   ├── services/       # Business logic — runtime errors, logic bugs, resource leaks
│   │   ├── middleware/     # Security middleware — CSP, CSRF, rate limiting review
│   │   ├── prompts/        # LLM prompts — injection risk review
│   │   ├── config.py       # Configuration — secrets exposure review
│   │   ├── main.py         # App setup — middleware ordering, error handling
│   │   └── ...             # All other source files
│   └── tests/
│       ├── unit/           # Unit tests — quality audit (mock leaks, dead assertions)
│       ├── integration/    # Integration tests — quality audit
│       ├── property/       # Property tests — quality audit
│       ├── fuzz/           # Fuzz tests — quality audit
│       ├── chaos/          # Chaos tests — quality audit
│       ├── concurrency/    # Concurrency tests — quality audit
│       └── conftest.py     # Test fixtures — mock leak review
│
└── frontend/
    ├── src/
    │   ├── components/     # React components — XSS, error handling review
    │   ├── hooks/          # Custom hooks — race condition, cleanup review
    │   ├── services/       # API clients — error handling, type safety review
    │   ├── context/        # Context providers — state management review
    │   ├── lib/            # Utilities — edge case and logic review
    │   └── ...             # All other source files
    └── src/__tests__/      # Frontend tests — quality audit
```

**Structure Decision**: Web application structure — existing `solune/backend/` and `solune/frontend/` layout. No new files or directories are created for the feature itself. All changes are modifications to existing source and test files. The bug bash is a review-and-fix effort, not a feature build.

## Implementation Phases

### Phase 1 — Security Vulnerability Audit (P1 — Highest Priority)

| Step | Description | Depends On | Target Area |
|------|-------------|------------|-------------|
| 1.1 | Audit authentication and authorization flows | — | `src/api/auth.py`, `src/middleware/csrf.py`, `src/middleware/admin_guard.py`, `src/services/github_auth.py` |
| 1.2 | Audit secrets and token handling | — | `src/config.py`, `src/services/encryption.py`, `src/services/session_store.py`, `.env.example` |
| 1.3 | Audit input validation and injection risks | — | `src/api/*.py` (all route handlers), `src/models/*.py`, webhook handlers |
| 1.4 | Audit security middleware and headers | — | `src/middleware/csp.py`, `src/middleware/rate_limit.py`, `src/main.py` (CORS config) |
| 1.5 | Audit frontend for XSS and client-side security | — | React components rendering user content, `dangerouslySetInnerHTML` usage, URL handling |
| 1.6 | Run existing security tools and verify | 1.1–1.5 | `ruff`, `bandit`, `pip-audit`, `npm audit` |

**Verification**: `bandit` clean, `pip-audit` clean, `npm audit` clean, no secrets in source, CSRF tokens validated, auth middleware applied correctly.

### Phase 2 — Runtime Error and Logic Bug Resolution (P2)

| Step | Description | Depends On | Target Area |
|------|-------------|------------|-------------|
| 2.1 | Audit exception handling and error propagation | Phase 1 | `src/services/**/*.py`, `src/api/*.py` — unhandled exceptions, missing try/catch |
| 2.2 | Audit resource management | Phase 1 | Database connections, file handles, WebSocket cleanup, aiosqlite sessions |
| 2.3 | Audit null/None references and type safety | Phase 1 | Optional field access, dictionary key access, API response parsing |
| 2.4 | Audit state transitions and control flow | Phase 1 | `src/services/workflow_orchestrator/`, `src/services/copilot_polling/`, `src/services/pipelines/` |
| 2.5 | Audit frontend runtime errors | Phase 1 | React component error boundaries, hook cleanup, async state management |
| 2.6 | Audit race conditions and concurrency | Phase 1 | WebSocket handlers, polling loops, concurrent state updates |

**Verification**: Full pytest suite passes, no unhandled exceptions in error paths, resource cleanup verified.

### Phase 3 — Test Quality Improvement (P3)

| Step | Description | Depends On | Target Area |
|------|-------------|------------|-------------|
| 3.1 | Audit for mock leaks in test fixtures | Phase 2 | `tests/conftest.py`, `tests/unit/*.py` — MagicMock objects leaking into production paths |
| 3.2 | Audit for assertions that never fail | Phase 2 | All test files — assertions on constants, always-true conditions |
| 3.3 | Audit for tests passing for wrong reason | Phase 2 | Tests with mocked return values matching expected output by coincidence |
| 3.4 | Identify and cover untested code paths | Phase 2 | Run coverage report, identify critical untested paths |
| 3.5 | Frontend test quality audit | Phase 2 | `src/__tests__/*.test.tsx` — snapshot staleness, missing assertions |

**Verification**: `pytest --cov` shows improved coverage for fixed paths, all mock objects properly scoped.

### Phase 4 — Code Quality Cleanup (P4)

| Step | Description | Depends On | Target Area |
|------|-------------|------------|-------------|
| 4.1 | Identify and remove dead code | Phase 3 | Unreachable branches, unused imports, dead functions |
| 4.2 | Fix silent failures | Phase 3 | Bare `except: pass`, swallowed errors, missing error messages |
| 4.3 | Address hardcoded values | Phase 3 | Magic numbers, hardcoded strings that should be configurable |
| 4.4 | Frontend code quality | Phase 3 | Dead components, unused hooks, unreachable code paths |

**Verification**: `ruff` clean, `eslint` clean, `pyright` clean, no new linting warnings introduced.

### Phase 5 — Summary Report Generation (P5)

| Step | Description | Depends On | Target Area |
|------|-------------|------------|-------------|
| 5.1 | Compile all fixes and flags into summary table | Phase 4 | All phases |
| 5.2 | Validate complete test suite passes | 5.1 | `pytest`, `vitest`, `eslint`, `ruff` |
| 5.3 | Verify no architecture or API surface changes | 5.2 | Diff review |

**Verification**: Summary table complete, all tests pass, no public API changes.

## Complexity Tracking

> No constitution violations to justify. All changes follow simplicity and DRY principles.
> Each fix is minimal and focused per FR-008/FR-010. No new abstractions introduced.
