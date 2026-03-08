# Implementation Plan: Bug Basher — Full Codebase Review & Fix

**Branch**: `031-bug-basher` | **Date**: 2026-03-08 | **Spec**: [`specs/031-bug-basher/spec.md`](spec.md)
**Input**: Feature specification from `/specs/031-bug-basher/spec.md`

## Summary

Perform a comprehensive bug bash code review of the entire codebase across five priority categories: security vulnerabilities, runtime errors, logic bugs, test gaps, and code quality issues. Each clear bug is fixed in-place with a regression test; ambiguous issues are flagged with `TODO(bug-bash):` comments for human review. The approach is a systematic file-by-file audit of both the Python/FastAPI backend and the React/TypeScript frontend, validated by running the full test suite (`pytest`, `vitest`) and existing linting tools (`ruff`, `ESLint`).

## Technical Context

**Language/Version**: Python >=3.12 (tooling targets 3.13) for backend; TypeScript ~5.9 / React 19 for frontend
**Primary Dependencies**: FastAPI >=0.135, aiosqlite, githubkit, Pydantic >=2.12 (backend); React 19, TanStack Query, Tailwind CSS 4, dnd-kit (frontend)
**Storage**: SQLite via aiosqlite (WAL mode, single persistent connection)
**Testing**: pytest + pytest-asyncio (backend, 53 unit test files); Vitest + React Testing Library (frontend)
**Target Platform**: Linux server (Docker), modern browsers (frontend)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: N/A — this feature is a code review, not a performance change
**Constraints**: No new dependencies; no architecture or public API changes; minimal focused fixes; preserve existing code style
**Scale/Scope**: ~18 backend API modules, ~49 backend service modules, ~19 model files, 20 SQL migration files (001–017 with duplicate prefixes at 013, 014, 015), ~183 frontend component/hook/page files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development — ✅ PASS

The feature spec (`spec.md`) includes six prioritized user stories (P1–P6) with independent testing criteria and Given-When-Then acceptance scenarios. Scope boundaries are explicit (no architecture changes, no new dependencies, no drive-by refactors).

### II. Template-Driven Workflow — ✅ PASS

All artifacts follow canonical templates from `.specify/templates/`. This plan follows `plan-template.md`. Research, data model, contracts, and quickstart follow established conventions.

### III. Agent-Orchestrated Execution — ✅ PASS

This plan is produced by the `speckit.plan` agent. Subsequent phases (`speckit.tasks`, `speckit.implement`) will be handled by their respective agents. Each agent has a single clear purpose and operates on well-defined inputs/outputs.

### IV. Test Optionality with Clarity — ✅ PASS (Tests REQUIRED)

The spec explicitly mandates regression tests for every bug fix (FR-004). This is not optional — it is a core functional requirement. Tests follow existing patterns (pytest for backend, vitest for frontend).

### V. Simplicity and DRY — ✅ PASS

Each fix must be minimal and focused (FR-013). No drive-by refactors. No premature abstraction. The bug bash is inherently simple: find bug → fix bug → add test → verify.

**Gate Result: ✅ ALL GATES PASS — Proceed to Phase 0**

## Project Structure

### Documentation (this feature)

```text
specs/031-bug-basher/
├── plan.md              # This file
├── research.md          # Phase 0: Research findings and known issues
├── data-model.md        # Phase 1: Bug report entry model and summary schema
├── quickstart.md        # Phase 1: How to run the bug bash workflow
├── contracts/           # Phase 1: Summary table output format contract
│   └── summary-table.md
├── checklists/          # Tracking checklists
│   └── requirements.md
└── tasks.md             # Phase 2 output (NOT created by speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/             # 18 endpoint modules — audit for input validation, auth, error handling
│   ├── models/          # 19 Pydantic model files — audit for type safety, validation rules
│   ├── services/        # 49 service modules + agents/, github_projects/ packages
│   │   ├── agents/      # AgentsService — method naming, preferences handling
│   │   ├── github_projects/  # GraphQL client, service — exception handling, resource mgmt
│   │   ├── workflow_orchestrator/  # Orchestrator — state transitions, error propagation
│   │   ├── copilot_polling/       # Copilot integration — async patterns, error handling
│   │   ├── database.py  # Migration runner — numbering conflicts, SQL safety
│   │   └── ...          # encryption, auth, caching, signal, websocket, etc.
│   ├── migrations/      # 20 SQL migration files — duplicate prefix conflicts (013, 014, 015)
│   ├── config.py        # Settings validation — secret enforcement, CORS config
│   └── main.py          # App factory, lifespan, middleware — startup/shutdown, error handlers
└── tests/
    ├── unit/            # 53 test files — audit for mock leaks, tautological assertions
    ├── helpers/         # Test factories, mocks, assertions
    └── conftest.py      # Shared fixtures (mock_db, mock_session, client, etc.)

frontend/
├── src/
│   ├── components/      # React components with co-located tests
│   ├── pages/           # Page-level components
│   ├── hooks/           # Custom React hooks
│   ├── services/        # API client (api.ts)
│   └── test/            # Test utilities (test-utils.tsx, factories)
└── e2e/                 # Playwright end-to-end tests
```

**Structure Decision**: Web application with separate `backend/` (Python/FastAPI) and `frontend/` (TypeScript/React) projects. All bug fixes are made in-place within the existing structure. No structural changes.

## Constitution Check — Post-Design Re-evaluation

*Re-checked after Phase 1 design completion.*

### I. Specification-First Development — ✅ PASS (unchanged)
### II. Template-Driven Workflow — ✅ PASS (unchanged)
### III. Agent-Orchestrated Execution — ✅ PASS (unchanged)
### IV. Test Optionality with Clarity — ✅ PASS (unchanged)
### V. Simplicity and DRY — ✅ PASS (unchanged)

**Post-Design Gate Result: ✅ ALL GATES PASS**

## Complexity Tracking

> No constitution violations — this section is intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
