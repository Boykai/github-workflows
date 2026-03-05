# Implementation Plan: Codebase Cleanup — Reduce Technical Debt

**Branch**: `018-code-cleanup` | **Date**: 2026-03-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/018-code-cleanup/spec.md`

## Summary

Perform a thorough codebase cleanup across the entire repository (backend, frontend, scripts, specs) to reduce technical debt and improve maintainability. The work is organized into five equally weighted cleanup categories: (1) remove backwards-compatibility shims, (2) eliminate dead code paths, (3) consolidate duplicated logic, (4) delete stale/irrelevant tests, and (5) general hygiene. All changes are internal-only — no public API contracts are modified. The approach uses static analysis tools (ruff, pyright, eslint, tsc) as the primary detection mechanism, supplemented by manual code review for patterns the tools cannot detect (shims, duplication, stale tests).

## Technical Context

**Language/Version**: Python ≥3.11 (backend), TypeScript ~5.4 (frontend), Bash (scripts)
**Primary Dependencies**: FastAPI ≥0.109, React 18.3, TanStack Query 5, Tailwind CSS 3.4, aiosqlite, Pydantic ≥2.5, Vite 5.4, Vitest 4
**Storage**: SQLite via aiosqlite (10 migrations, 001–010)
**Testing**: pytest + pytest-asyncio + pytest-cov (backend), Vitest + Testing Library + Playwright (frontend)
**Target Platform**: Docker (Linux) — web application
**Project Type**: Web application (frontend + backend)
**Performance Goals**: CI check suite execution time must not increase; test suite runtime should not increase (and ideally decreases after stale test removal)
**Constraints**: All existing CI checks must pass (ruff, pyright, pytest for backend; eslint, tsc, vitest, vite build for frontend). No public API contract changes. No removal of dynamically-loaded code without confirmation. Conventional commits required (`refactor:` for consolidation, `chore:` for removal).
**Scale/Scope**: Full repository — backend (~15 API routes, ~15 models, ~12 services), frontend (~40 components, ~23 hooks, ~2 pages), scripts, specs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development — ✅ PASS
Spec exists at `specs/018-code-cleanup/spec.md` with 5 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, edge cases, and functional requirements (FR-001 through FR-023).

### II. Template-Driven Workflow — ✅ PASS
All artifacts follow canonical templates. Plan uses `plan-template.md`. Spec uses `spec-template.md`. Checklists generated via `/speckit.checklist`.

### III. Agent-Orchestrated Execution — ✅ PASS
Plan produced by `/speckit.plan` agent. Tasks will be produced by `/speckit.tasks`. Each agent has a single responsibility with clear handoffs.

### IV. Test Optionality with Clarity — ✅ PASS
The spec does not mandate writing new tests. However, existing tests must be preserved (FR-022) — only genuinely stale tests may be removed. No TDD approach is specified. The cleanup itself is validated by running the existing CI checks rather than by writing new tests.

### V. Simplicity and DRY — ✅ PASS
This feature directly advances the DRY principle by consolidating duplicated logic (User Story 3, FR-008 through FR-011). The cleanup approach is deliberately simple: use existing static analysis tools for detection, make surgical removals, and validate with existing CI. No new abstractions or frameworks are introduced.

## Project Structure

### Documentation (this feature)

```text
specs/018-code-cleanup/
├── plan.md              # This file
├── research.md          # Phase 0 output — cleanup target analysis
├── data-model.md        # Phase 1 output — no model changes (cleanup-only)
├── quickstart.md        # Phase 1 output — cleanup execution guide
├── contracts/           # Phase 1 output — no contract changes (cleanup-only)
│   └── README.md        # Explanation of N/A status
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/             # MODIFY — remove unused route handlers, dead imports
│   ├── models/          # MODIFY — remove unused models, consolidate duplicates
│   ├── services/        # MODIFY — consolidate duplicated service logic, remove dead code
│   ├── middleware/       # INSPECT — check for dead middleware
│   ├── migrations/      # INSPECT — check for orphaned migrations
│   ├── config.py        # INSPECT — remove unused config entries
│   ├── constants.py     # INSPECT — remove unused constants
│   ├── dependencies.py  # INSPECT — remove unused dependencies
│   ├── exceptions.py    # INSPECT — remove unused exception classes
│   ├── logging_utils.py # INSPECT — remove dead logging helpers
│   └── utils.py         # INSPECT — remove dead utility functions
├── tests/
│   ├── helpers/         # INSPECT — factories.py, mocks.py for consolidation opportunities
│   ├── unit/            # MODIFY — remove stale tests, consolidate duplicated patterns
│   └── integration/     # MODIFY — remove stale tests
└── pyproject.toml       # MODIFY — remove unused dependencies

frontend/
├── src/
│   ├── components/      # MODIFY — remove unused components, consolidate duplicates
│   ├── hooks/           # MODIFY — remove unused hooks, consolidate duplicates
│   ├── services/        # INSPECT — consolidate duplicated API client logic
│   ├── types/           # MODIFY — remove unused types, consolidate overlapping definitions
│   ├── utils/           # INSPECT — remove dead utility functions
│   ├── constants.ts     # INSPECT — remove unused constants
│   └── App.tsx          # INSPECT — remove dead imports
├── e2e/                 # INSPECT — check for stale e2e tests
└── package.json         # MODIFY — remove unused dependencies

scripts/                 # INSPECT — check for dead scripts
docker-compose.yml       # INSPECT — check for unused services/env vars
.env.example             # INSPECT — check for unused environment variables
```

**Structure Decision**: Web application (frontend + backend). No new files are created — this is a pure cleanup operation. All changes are modifications to or deletions of existing files across both backend and frontend codebases, plus dependency manifest cleanup.

## Complexity Tracking

> No violations detected. No complexity justifications needed. This feature reduces complexity rather than adding it.
