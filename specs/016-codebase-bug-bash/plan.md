# Implementation Plan: Bug Bash — Full Codebase Review & Fix

**Branch**: `016-codebase-bug-bash` | **Date**: 2026-03-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/016-codebase-bug-bash/spec.md`

## Summary

Perform a comprehensive bug bash code review of the entire codebase on `main`, systematically auditing ~342 source files across five bug categories (Security → Runtime → Logic → Test Quality → Code Quality) in strict priority order. Each confirmed bug is fixed with a minimal, isolated commit and at least one regression test. Ambiguous issues are flagged with `TODO(bug-bash)` comments for human review. A structured summary report documents every finding. No architectural changes, public API modifications, or new dependencies are introduced.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.4 / Node 20 (frontend)
**Primary Dependencies**: FastAPI 0.109+, aiosqlite 0.20+, Pydantic Settings (backend); React 18, Vite 5, TanStack Query v5, Radix UI, Socket.io-client (frontend)
**Storage**: SQLite via aiosqlite (async, no ORM), migrations in `backend/src/migrations/` (001–009)
**Testing**: pytest 7.4+ with asyncio + pytest-cov (backend, ~55 test files), Vitest 4.0+ with happy-dom + @testing-library/react (frontend, ~29 test files), Playwright 1.58+ (E2E, 9 spec files)
**Target Platform**: Linux server (Docker), modern browsers (Chrome, Firefox, Safari, Edge)
**Project Type**: Web application (backend + frontend monorepo with Docker Compose)
**Performance Goals**: N/A — bug bash is a quality/correctness audit, not a performance initiative
**Constraints**: No new dependencies, no architecture changes, no public API signature changes, no large-scale refactors; each fix must be minimal and isolated
**Scale/Scope**: ~87 backend Python source files, ~122 frontend TypeScript/TSX files, ~55 backend test files, ~29 frontend test files, 9 SQL migrations, 3 GitHub workflows, 3 Docker files, ~10 config files — approximately 342 files total

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | `spec.md` exists with 6 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, edge cases, and clear scope boundaries. All five bug categories are defined with priority order. |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/`. Plan, research, data-model, contracts, and quickstart produced per template structure. |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase follows single-responsibility model. Outputs are well-defined markdown documents for handoff to tasks phase. |
| IV. Test Optionality with Clarity | ✅ PASS | Tests are *explicitly mandated* by the feature specification (FR-003: "each bug fix MUST include at least one new regression test"). The spec makes testing a core requirement, not optional. |
| V. Simplicity and DRY | ✅ PASS | All fixes use existing test infrastructure (pytest, Vitest, factories, mock API). No new frameworks, abstractions, or dependencies introduced. Each fix is isolated and minimal. |

**Gate Result**: ✅ ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/016-codebase-bug-bash/
├── plan.md              # This file
├── research.md          # Phase 0: Audit strategy and research decisions
├── data-model.md        # Phase 1: Finding/Fix/Flag entity model
├── quickstart.md        # Phase 1: Implementation guide for the bug bash
├── contracts/           # Phase 1: Audit standards and process contracts
│   └── audit-standards.md
└── tasks.md             # Phase 2 output (created by /speckit.tasks, NOT this phase)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/             # 14 API route files (auth, chat, projects, board, tasks, etc.)
│   ├── services/        # 25+ service files (database, github_projects, ai_agent, etc.)
│   │   ├── github_projects/
│   │   │   └── service.py    # 4000+ line main service (highest audit priority)
│   │   ├── database.py       # SQLite connection management
│   │   ├── ai_agent.py       # AI agent orchestration
│   │   └── signal_chat.py    # Signal messaging integration
│   ├── models/          # 12 data model files
│   ├── middleware/       # Request ID tracking
│   ├── prompts/          # AI prompt templates
│   ├── migrations/       # 9 SQL migration files (001–009)
│   ├── config.py         # Settings (Pydantic BaseSettings with lru_cache)
│   ├── constants.py      # Application constants (StatusNames, LABELS, etc.)
│   ├── dependencies.py   # FastAPI dependencies (auth, admin, session)
│   ├── main.py           # FastAPI entry point (lifespan, cleanup loop)
│   └── utils.py          # Utility classes (BoundedDict, etc.)
├── tests/
│   ├── unit/             # 45 unit test files
│   ├── integration/      # 4 integration test files
│   └── conftest.py       # Shared fixtures
└── Dockerfile

frontend/
├── src/
│   ├── components/       # 50+ React components
│   │   ├── ui/           # 3 primitives (button, card, input)
│   │   ├── board/        # 11 board components
│   │   ├── chat/         # 6 chat components
│   │   ├── settings/     # 12 settings components
│   │   ├── auth/         # 2 auth components
│   │   └── common/       # 2 common components (ErrorBoundary)
│   ├── hooks/            # 18 custom hooks
│   ├── pages/            # 2 pages (ProjectBoard, Settings)
│   ├── services/         # API client (api.ts) with 9 namespaces
│   ├── test/             # Test infrastructure (setup, factories, utilities)
│   ├── lib/              # Utilities (cn(), commands/)
│   ├── App.tsx           # Root component
│   └── main.tsx          # Vite entry point
├── e2e/                  # 9 Playwright E2E spec files
├── vitest.config.ts
├── playwright.config.ts
└── eslint.config.js

docker-compose.yml        # Services: backend, frontend, signal-api
.github/workflows/
├── ci.yml                # Main CI: lint, type-check, test, build
├── housekeeping-cron.yml # Scheduled housekeeping
└── branch-issue-link.yml # Branch-to-issue automation
```

**Structure Decision**: Web application — the repository uses a `backend/` + `frontend/` split with Docker Compose orchestration. The bug bash audits all files across both directories plus infrastructure. No new directories or files are created in source code; only existing files are modified (fixes) or annotated (flags). New regression test functions are added to existing test files where possible, or to new test files following existing naming conventions.

## Complexity Tracking

> No constitution violations detected. All changes are minimal, isolated edits to existing files with no new abstractions.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | — | — |

## Constitution Re-Check (Post Phase 1 Design)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | All design artifacts trace back to spec.md requirements (FR-001 through FR-010). Audit phases map directly to user stories. |
| II. Template-Driven Workflow | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow canonical structure from completed examples. |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase produced well-defined outputs for handoff to tasks phase. Each audit phase is independently executable. |
| IV. Test Optionality with Clarity | ✅ PASS | Regression tests are the explicit subject of this feature (FR-003); every fix must include ≥1 regression test. Test infrastructure reuses existing patterns. |
| V. Simplicity and DRY | ✅ PASS | Audit process reuses existing tools (Ruff, Pyright, ESLint, pytest, Vitest). No new frameworks or abstractions. Fix commits are isolated and minimal. Finding/Fix/Flag model is lightweight (comments + summary table, not new code). |

**Post-Design Gate Result**: ✅ ALL PASS — ready for Phase 2 (tasks generation via `/speckit.tasks`).
