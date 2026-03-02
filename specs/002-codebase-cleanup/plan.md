# Implementation Plan: Codebase Cleanup — Reduce Technical Debt and Improve Maintainability

**Branch**: `002-codebase-cleanup` | **Date**: 2026-03-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-codebase-cleanup/spec.md`

## Summary

Perform a comprehensive codebase cleanup across backend (Python/FastAPI) and frontend (TypeScript/React) to eliminate dead code, stale tests, duplicated logic, backwards-compatibility shims, and general hygiene issues. The technical approach is analysis-driven: use static analysis tools (ruff, pyright, tsc, eslint) and grep-based search to identify targets, manually verify each removal against dynamic-use patterns, execute changes with conventional commits, and validate via full CI suite. No new code is added — only removals, consolidations, and metadata cleanup.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.4 (frontend)  
**Primary Dependencies**: FastAPI, Pydantic v2, aiosqlite, httpx (backend); React 18, Vite 5.4, TanStack Query v5, Tailwind CSS 3.4, Shadcn UI (frontend)  
**Storage**: SQLite WAL via aiosqlite (backend persistent storage)  
**Testing**: pytest + pytest-asyncio (backend), Vitest + Testing Library (frontend unit), Playwright (frontend e2e)  
**Target Platform**: Linux server (Docker Compose: backend :8000, frontend :5173→nginx, signal-api :8080)  
**Project Type**: Web application (backend + frontend)  
**Performance Goals**: N/A — cleanup-only, no new features. CI must not regress.  
**Constraints**: No public API contract changes. All CI checks must pass. Conventional commits required.  
**Scale/Scope**: ~60 backend source files, ~80 frontend source files, ~45 backend test files, ~30 MagicMock artifact files in backend root.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | PASS | `spec.md` exists with 5 prioritized user stories, Given-When-Then acceptance criteria, and clear scope boundaries |
| II. Template-Driven | PASS | Using canonical plan template; spec follows canonical spec template |
| III. Agent-Orchestrated | PASS | Following plan phase workflow; clear inputs (spec) and outputs (plan artifacts) |
| IV. Test Optionality | PASS | No new tests added. Existing stale tests removed per spec FR-007/FR-008. Meaningful coverage preserved per FR-019. |
| V. Simplicity and DRY | PASS | This feature enforces simplicity and DRY by removing dead code and consolidating duplicates. No new abstractions introduced. |

**Gate Result**: ALL PASS — proceed to Phase 0 research.

## Project Structure

### Documentation (this feature)

```text
specs/002-codebase-cleanup/
├── plan.md              # This file
├── research.md          # Phase 0: analysis findings and decisions
├── data-model.md        # Phase 1: N/A for cleanup (no new entities)
├── quickstart.md        # Phase 1: execution guide
├── contracts/           # Phase 1: N/A for cleanup (no API changes)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/             # Route handlers (board, chat, auth, etc.) — cleanup target
│   ├── models/          # Pydantic models (15 files) — dedup target
│   ├── services/        # Business logic (copilot_polling, github_projects, etc.) — dedup/dead-code target
│   ├── middleware/       # Request middleware
│   ├── prompts/         # AI prompt templates
│   ├── config.py        # App configuration
│   ├── dependencies.py  # FastAPI dependency injection
│   ├── exceptions.py    # Custom exceptions
│   └── main.py          # App entry point
├── tests/
│   ├── unit/            # ~40 unit test files — stale test cleanup target
│   ├── integration/     # 3 integration test files
│   ├── helpers/         # factories.py, mocks.py, assertions.py — consolidation targets
│   ├── conftest.py      # Test configuration
│   └── test_api_e2e.py  # E2E test
├── <MagicMock ...>      # ~30 artifact files — deletion target (FR-004)
└── pyproject.toml       # Dependency manifest — unused dep cleanup target

frontend/
├── src/
│   ├── components/      # UI components (board, chat, settings, etc.) — unused component target
│   ├── hooks/           # Custom React hooks — unused hook target
│   ├── lib/             # Command system utilities
│   ├── pages/           # Page-level components
│   ├── services/        # API client (api.ts) — dedup target
│   ├── test/            # Test utilities and factories
│   ├── types/           # TypeScript type definitions — dedup target
│   └── utils/           # Utility functions — dedup target
├── package.json         # Dependency manifest — unused dep cleanup target
└── e2e/                 # Playwright E2E tests

scripts/                 # Build/deploy scripts — orphaned script target
docker-compose.yml       # Container orchestration — unused service/env target
```

**Structure Decision**: Existing web application structure (backend + frontend). No structural changes — cleanup operates within existing directory layout.

## Complexity Tracking

> No constitution violations detected. No complexity justifications needed.
