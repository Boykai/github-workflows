# Implementation Plan: Bug Basher — Full Codebase Review & Fix

**Branch**: `037-bug-basher` | **Date**: 2026-03-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/037-bug-basher/spec.md`

## Summary

Perform a comprehensive bug bash code review of the entire codebase (backend Python + frontend TypeScript) across five priority-ordered categories: security vulnerabilities, runtime errors, logic bugs, test quality gaps, and code quality issues. For each obvious bug, apply a minimal fix and add a regression test. For ambiguous issues, add a `TODO(bug-bash)` comment. Validate all changes pass the full test suite (`pytest` for backend, `vitest` for frontend) and existing linters (`ruff` for Python, `eslint` + `type-check` for TypeScript). Produce a summary table of all findings.

## Technical Context

**Language/Version**: Python ≥3.12 (target 3.13) for backend; TypeScript 5.x for frontend
**Primary Dependencies**: FastAPI, aiosqlite, httpx, PyYAML (backend); React 19.2, TanStack React Query 5.90, Vitest 4.0 (frontend)
**Storage**: aiosqlite (SQLite) with custom migration runner; GitHub API for repository file operations
**Testing**: pytest (backend, ~1736 unit tests); Vitest with happy-dom (frontend, ~644 tests)
**Target Platform**: Linux server (backend API), browser SPA (frontend)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: N/A — this is a review/fix pass, not a feature with performance targets
**Constraints**: No architecture changes, no public API surface changes, no new dependencies, minimal focused fixes only, preserve existing code style
**Scale/Scope**: ~40 backend Python source files, ~261 frontend TypeScript/TSX files, full test suites for both

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | Full spec exists at `specs/037-bug-basher/spec.md` with 5 prioritized user stories (P1–P5), Given-When-Then acceptance scenarios, 14 functional requirements, and measurable success criteria. |
| **II. Template-Driven Workflow** | ✅ PASS | All artifacts follow canonical templates. This plan follows `plan-template.md`. |
| **III. Agent-Orchestrated Execution** | ✅ PASS | `speckit.plan` agent produces this plan with well-defined inputs (spec.md) and outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md). |
| **IV. Test Optionality with Clarity** | ✅ PASS | Tests are explicitly required by the feature spec — FR-003 mandates at least one regression test per bug fix. This is justified by the nature of the feature: bug fixes without regression tests have high reoccurrence risk. |
| **V. Simplicity and DRY** | ✅ PASS | Each fix is minimal and focused (FR-012). No new abstractions or refactoring. Changes are surgical per-bug corrections. |

**Gate Result**: ✅ ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/037-bug-basher/
├── plan.md              # This file
├── research.md          # Phase 0 output — review methodology and tooling research
├── data-model.md        # Phase 1 output — bug report entity model
├── quickstart.md        # Phase 1 output — how to execute the bug bash
├── contracts/           # Phase 1 output
│   └── bug-report-schema.yaml  # Summary table output schema
├── checklists/
│   └── requirements.md  # Pre-existing specification quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/                    # REST API endpoints — review for auth/input validation
│   ├── config.py               # Configuration — review for insecure defaults
│   ├── constants.py            # Constants — review for hardcoded secrets
│   ├── dependencies.py         # DI setup — review for resource leaks
│   ├── exceptions.py           # Error handling — review for silent failures
│   ├── main.py                 # App entrypoint — review for startup errors
│   ├── middleware/              # HTTP middleware — review for auth bypasses
│   ├── migrations/             # DB migrations — review for data integrity
│   ├── models/                 # Data models — review for type safety
│   ├── prompts/                # AI prompt templates — review for injection
│   ├── services/               # Business logic — review for all categories
│   │   ├── agents/             # Agent management
│   │   ├── tools/              # Tool/MCP management
│   │   ├── github_projects/    # GitHub API integration
│   │   ├── workflow_orchestrator/ # Pipeline orchestration
│   │   ├── copilot_polling/    # Copilot polling service
│   │   ├── database.py         # DB operations — review for SQL injection, connection leaks
│   │   ├── encryption.py       # Encryption — review for crypto weaknesses
│   │   └── ...                 # Other services
│   └── utils.py                # Utilities — review for edge cases
└── tests/
    └── unit/                   # ~1736 existing unit tests

frontend/
├── src/
│   ├── components/             # UI components — review for XSS, logic errors
│   │   ├── agents/
│   │   ├── auth/
│   │   ├── board/
│   │   ├── chat/
│   │   ├── chores/
│   │   ├── common/
│   │   ├── pipeline/
│   │   ├── settings/
│   │   ├── tools/
│   │   └── ui/
│   ├── hooks/                  # Custom hooks — review for race conditions, stale state
│   ├── lib/                    # Utility libraries
│   ├── pages/                  # Page components
│   ├── services/               # API client services
│   └── utils/                  # Frontend utilities
└── tests/                      # ~644 existing Vitest tests (colocated with source)
```

**Structure Decision**: Web application structure (Option 2). The bug bash reviews both `backend/` and `frontend/` directories. No new files are created in the source tree — only existing files are modified (bug fixes) and new test files/cases are added to existing test directories.

## Review Execution Strategy

### Phase 1: Backend Review (Python) — Priority Order

**Pass 1 — Security (P1)**:
1. Scan `backend/src/config.py`, `constants.py` for hardcoded secrets/tokens
2. Review `backend/src/services/encryption.py` for cryptographic weaknesses
3. Audit `backend/src/api/` endpoints for input validation gaps
4. Check `backend/src/middleware/` for authentication/authorization bypasses
5. Review `backend/src/services/database.py` for SQL injection risks
6. Scan all files for exposed secrets in string literals or comments

**Pass 2 — Runtime Errors (P2)**:
1. Check all `async` functions for unhandled exceptions and missing `await`
2. Review file handle and database connection lifecycle (open/close patterns)
3. Audit `None`/null reference access patterns
4. Check import statements for missing or circular dependencies
5. Review type annotations vs actual runtime values

**Pass 3 — Logic Bugs (P3)**:
1. Review state machine transitions in `workflow_orchestrator/`
2. Check boundary conditions in loops and conditionals
3. Audit return values and error propagation paths
4. Review API call parameters and response handling in `github_projects/`

**Pass 4 — Test Quality (P4)**:
1. Identify tests with assertions that never fail (e.g., `assert True`)
2. Check for mock objects leaking into production code paths
3. Find untested critical code paths
4. Review test isolation (shared state between tests)

**Pass 5 — Code Quality (P5)**:
1. Identify dead/unreachable code
2. Find duplicated logic across modules
3. Check for silent error swallowing (bare `except:` or empty `except` blocks)
4. Review hardcoded values that should be configurable

### Phase 2: Frontend Review (TypeScript) — Priority Order

**Pass 1 — Security (P1)**:
1. Review user input handling for XSS risks
2. Check API client for credential exposure
3. Audit localStorage/sessionStorage for sensitive data

**Pass 2 — Runtime Errors (P2)**:
1. Check for unhandled promise rejections
2. Review null/undefined access patterns
3. Audit React hook dependency arrays for missing dependencies
4. Check for race conditions in async state updates

**Pass 3 — Logic Bugs (P3)**:
1. Review conditional rendering logic
2. Check state management for incorrect updates
3. Audit event handler logic

**Pass 4 — Test Quality (P4)**:
1. Identify weak assertions in Vitest tests
2. Check mock cleanup between tests
3. Find untested component interactions

**Pass 5 — Code Quality (P5)**:
1. Identify unused exports and dead code
2. Find duplicated component logic
3. Check for silent error handling

### Phase 3: Validation

1. Run `python -m pytest tests/unit/ -v` — all tests must pass
2. Run `python -m ruff check src/` — no new linting violations
3. Run `npx vitest run` — all frontend tests must pass
4. Run `npm run type-check` — no new type errors
5. Run `npm run lint` — no new ESLint violations
6. Generate final summary table

## Complexity Tracking

> No constitution violations detected. No complexity justifications required.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | — | — |
