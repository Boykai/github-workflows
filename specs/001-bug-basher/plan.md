# Implementation Plan: Bug Basher — Full Codebase Review & Fix

**Branch**: `001-bug-basher` | **Date**: 2026-03-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-bug-basher/spec.md`

## Summary

Perform a comprehensive bug bash code review of the entire Solune codebase (backend: Python/FastAPI, frontend: TypeScript/React). Audit all files across five priority-ordered categories — security vulnerabilities, runtime errors, logic bugs, test quality gaps, and code quality issues. For each clear bug: fix it, update affected tests, and add a regression test. For ambiguous issues: flag with `TODO(bug-bash)` comments. Produce a summary table of all findings. All changes must preserve the existing architecture, public API surface, code style, and pass the full test suite plus linting.

## Technical Context

**Language/Version**: Python 3.12+ (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI, Pydantic, aiosqlite, httpx, githubkit, cryptography (backend); React 19, Vite, TanStack Query, Zod, Tailwind CSS (frontend)
**Storage**: SQLite via aiosqlite (backend persistent storage)
**Testing**: pytest + pytest-asyncio + pytest-cov (backend, 3575+ unit tests); Vitest (frontend, 155+ test files); Playwright (e2e)
**Target Platform**: Linux server (backend), Web browser (frontend), GitHub Actions (CI)
**Project Type**: Web application (frontend + backend under `solune/`)
**Performance Goals**: N/A — this is a review/fix task, not a feature build
**Constraints**: No new dependencies (FR-005), no architecture/API changes (FR-004), preserve code style (FR-006), all tests green post-fix (FR-008), all linting green post-fix (FR-009)
**Scale/Scope**: ~143 backend source files, ~419 frontend source files, ~194 backend test files, ~155 frontend test files, 5 middleware, 21 API routes, 33 service files + 7 service sub-packages, 25 model files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | `spec.md` with 5 prioritized user stories (P1–P5), Given-When-Then scenarios, and clear scope boundaries exists and is validated |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Single-responsibility agent (`speckit.plan`) producing plan artifacts with clear handoff to `speckit.tasks` |
| **IV. Test Optionality** | ✅ PASS | Tests are explicitly required by the spec (FR-002, FR-008, FR-013) — regression tests mandatory per bug fix |
| **V. Simplicity / DRY** | ✅ PASS | Each fix must be minimal and focused (FR-006). No drive-by refactors. No new dependencies. No architecture changes |

**Gate Result**: ✅ ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-bug-basher/
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0 output — research findings
├── data-model.md        # Phase 1 output — bug report entity model
├── quickstart.md        # Phase 1 output — execution guide
├── contracts/           # Phase 1 output — process contracts
│   └── process-contracts.md
├── checklists/
│   └── requirements.md  # Specification quality checklist (pre-existing)
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── src/
│   │   ├── api/              # 21 route files (activity, agents, apps, auth, board, chat, chores, cleanup, health, mcp, metadata, onboarding, pipelines, projects, settings, signal, tasks, tools, webhook_models, webhooks, workflow)
│   │   ├── middleware/       # 5 middleware (admin_guard, csp, csrf, rate_limit, request_id)
│   │   ├── migrations/       # Database migration scripts
│   │   ├── models/           # 25 Pydantic model files
│   │   ├── prompts/          # AI prompt templates
│   │   ├── services/         # 33 service files + 7 sub-packages (agents, chores, copilot_polling, github_projects, pipelines, tools, workflow_orchestrator)
│   │   ├── config.py         # Application configuration
│   │   ├── constants.py      # Shared constants
│   │   ├── dependencies.py   # FastAPI dependency injection
│   │   ├── exceptions.py     # Custom exception classes
│   │   ├── logging_utils.py  # Logging utilities (handle_service_error pattern)
│   │   ├── main.py           # FastAPI app entry point
│   │   ├── protocols.py      # Protocol/interface definitions
│   │   └── utils.py          # Shared utility functions
│   └── tests/
│       ├── unit/             # ~144 unit test files
│       ├── integration/      # ~15 integration test files
│       ├── property/         # ~8 property-based test files (Hypothesis)
│       ├── fuzz/             # ~3 fuzz test files
│       ├── chaos/            # ~5 chaos test files
│       ├── concurrency/      # ~5 concurrency test files
│       ├── architecture/     # ~1 architecture test file
│       └── helpers/          # ~2 test helper modules
├── frontend/
│   ├── src/
│   │   ├── components/       # UI components (activity, agents, apps, auth, board, chat, chores, command-palette, common, help, onboarding, pipeline, settings, tools, ui)
│   │   ├── pages/            # Page components
│   │   ├── hooks/            # React hooks
│   │   ├── services/         # API service layer + schemas/
│   │   ├── context/          # React context providers
│   │   ├── lib/              # Libraries (commands/)
│   │   ├── types/            # TypeScript type definitions
│   │   ├── utils/            # Utility functions
│   │   ├── constants/        # Frontend constants
│   │   ├── data/             # Static data
│   │   ├── layout/           # Layout components
│   │   ├── assets/           # Static assets (avatars, onboarding)
│   │   └── test/             # Test factories + utilities
│   └── e2e/                  # Playwright end-to-end tests
├── docs/                     # Project documentation
└── scripts/                  # Utility scripts
```

**Structure Decision**: Web application (Option 2). The existing `solune/backend/` and `solune/frontend/` structure is preserved. Bug fixes are applied in-place across both projects — no new directories or structural changes.

## Complexity Tracking

> No Constitution violations identified. All fixes are minimal, focused, and within existing patterns.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *None* | — | — |
