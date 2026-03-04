# Implementation Plan: Codebase Cleanup — Reduce Technical Debt

**Branch**: `018-code-cleanup` | **Date**: 2026-03-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/018-code-cleanup/spec.md`

## Summary

Perform a thorough codebase cleanup across backend (Python/FastAPI), frontend (React/TypeScript), scripts, and specs to reduce technical debt. The work is decomposed into five categories: (1) remove backwards-compatibility shims, (2) eliminate dead code paths, (3) consolidate duplicated logic, (4) delete stale tests, and (5) general hygiene. All changes are internal-only — no public API contracts change. CI checks must pass after every change.

## Technical Context

**Language/Version**: Python ≥3.11 (backend), TypeScript ~5.4 (frontend)
**Primary Dependencies**: FastAPI ≥0.109, Pydantic ≥2.5, React 18.3, Vite 5.4, Tailwind CSS 3.4
**Storage**: aiosqlite (async SQLite) with raw SQL migrations
**Testing**: pytest + pytest-asyncio (backend, ~1284 tests); Vitest + happy-dom (frontend, ~334 tests); Playwright (e2e)
**Target Platform**: Linux server (Docker Compose: backend, frontend, signal-api)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: N/A (cleanup-only, no new functionality)
**Constraints**: All CI must pass (ruff, pyright, pytest for backend; eslint, tsc, vitest, vite build for frontend). No public API contract changes. Preserve meaningful test coverage.
**Scale/Scope**: ~80 backend Python files, ~65 frontend TS/TSX files, 10 SQL migrations, 47+ backend test files, 33+ frontend test files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | spec.md exists with prioritized user stories (P1–P3), acceptance scenarios, and edge cases |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated Execution | ✅ PASS | Single-responsibility agent (speckit.plan) producing plan artifacts |
| IV. Test Optionality | ✅ PASS | No new tests required — this feature removes code and verifies via existing CI checks |
| V. Simplicity and DRY | ✅ PASS | Feature itself enforces DRY by consolidating duplicated logic |

**Gate Result**: ✅ All gates pass. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/018-code-cleanup/
├── plan.md              # This file
├── research.md          # Phase 0 output — research findings
├── data-model.md        # Phase 1 output — cleanup inventory
├── quickstart.md        # Phase 1 output — developer quick-start guide
├── contracts/           # Phase 1 output — change contracts per category
│   └── cleanup-categories.md
├── checklists/
│   └── requirements.md  # Spec quality checklist (pre-existing)
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/             # Route handlers (auth, board, chat, chores, etc.)
│   ├── models/          # Pydantic models (agent, board, chat, etc.)
│   ├── services/        # Business logic (agents, chores, copilot_polling, etc.)
│   ├── middleware/       # RequestID middleware
│   ├── migrations/      # SQL migration files (001–010)
│   ├── prompts/         # LLM prompt templates
│   ├── config.py        # Settings (pydantic-settings)
│   ├── constants.py     # Application constants
│   ├── dependencies.py  # FastAPI dependency injection
│   ├── exceptions.py    # Custom exceptions
│   ├── main.py          # App entry point
│   └── utils.py         # Shared utilities
├── tests/
│   ├── helpers/         # factories.py, mocks.py (shared test utilities)
│   ├── unit/            # 47+ unit test files
│   └── integration/     # Integration tests
└── pyproject.toml       # Dependencies, ruff, pyright, pytest config

frontend/
├── src/
│   ├── components/      # React components (board, chat, agents, settings, etc.)
│   ├── hooks/           # Custom hooks (useAuth, useChat, useProjectBoard, etc.)
│   ├── pages/           # Page components (ProjectBoardPage, SettingsPage)
│   ├── services/        # API client (api.ts)
│   ├── lib/             # Commands framework, utils
│   ├── types/           # TypeScript type definitions
│   ├── utils/           # Utility functions
│   ├── test/            # Test setup and helpers
│   ├── constants.ts     # Frontend constants
│   └── App.tsx          # App root
├── package.json         # Dependencies
├── vitest.config.ts     # Test config
├── eslint.config.js     # Lint config
└── tsconfig.json        # TypeScript config

scripts/
├── pre-commit/          # Git hooks
└── setup-hooks.sh       # Hook installer
```

**Structure Decision**: Web application (Option 2) — existing backend + frontend layout. No structural changes needed; cleanup operates within existing directories.

## Complexity Tracking

> No Constitution Check violations. No complexity justifications needed.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
