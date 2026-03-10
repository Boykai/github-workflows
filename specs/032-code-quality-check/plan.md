# Implementation Plan: Code Quality Check

**Branch**: `032-code-quality-check` | **Date**: 2026-03-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/032-code-quality-check/spec.md`

## Summary

Comprehensive code quality audit and remediation across backend (Python/FastAPI) and frontend (TypeScript/React). The work spans 7 phases: fix silent exception swallowing and security leaks (P0), consolidate duplicated patterns into shared utilities (P1), decompose oversized files into focused modules (P2), strengthen type safety (P2), remove technical debt and legacy patterns (P3), improve performance and observability (P3), and close testing and linting gaps (P4). Research confirms 98 bare `except Exception:` blocks, 3 Signal API exception leaks, wildcard CORS, 5,220-line service file, 1,128-line API client, and multiple unused utilities ready for adoption.

## Technical Context

**Language/Version**: Python 3.12+ (backend), TypeScript ES2022 (frontend)
**Primary Dependencies**: FastAPI 0.135+, Pydantic 2.12+, httpx 0.28+, GitHub Copilot SDK 0.1.30+, React 18, TanStack React Query, Vite, Tailwind CSS
**Storage**: SQLite via aiosqlite 0.22+ (existing migrations 001–020)
**Testing**: pytest 9.0+ / pytest-asyncio (backend), Vitest 4.0+ / React Testing Library / Playwright (frontend)
**Target Platform**: Linux server (backend), Modern browsers (frontend)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: Sub-second UI interactions, bounded in-memory structures, request cancellation on route changes
**Constraints**: No new runtime dependencies unless justified; all files under 500 LOC (backend) / 400 LOC (frontend hooks); zero unsafe type casts in production code
**Scale/Scope**: 17 API route files, 30+ service files, 80+ frontend components, 46 hooks, 9 page components

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development — ✅ PASS

The feature specification (`spec.md`) includes 7 prioritized user stories (P1–P4) with independent testing criteria, 30 functional requirements with Given-When-Then acceptance scenarios, clear scope boundaries, and 17 measurable success criteria.

### II. Template-Driven Workflow — ✅ PASS

All artifacts follow the canonical templates from `.specify/templates/`. This plan follows `plan-template.md`. The spec follows `spec-template.md`. No custom sections are added.

### III. Agent-Orchestrated Execution — ✅ PASS

The work is decomposed into clear phases with well-defined inputs and outputs. Each phase produces specific artifacts and hands off to the next via explicit transitions. The `speckit.plan` agent produces plan, research, data-model, contracts, and quickstart documents.

### IV. Test Optionality with Clarity — ✅ PASS

Tests are explicitly required by the specification (User Stories 1 and 7, FR-027, FR-028). Phase 7 is dedicated to testing and linting gaps. Test tasks are specified as following implementation tasks (test what you change), consistent with the "every refactor ships with updated or new tests" guiding principle.

### V. Simplicity and DRY — ✅ PASS

The entire feature is focused on simplicity and DRY: consolidating duplicated patterns (Phase 2), decomposing oversized files (Phase 3), and removing anti-patterns (Phase 5). No premature abstractions are introduced. The `cached_fetch()` helper and validation guards are extracted from 5+ existing duplications. No complexity tracking violations identified.

## Project Structure

### Documentation (this feature)

```text
specs/032-code-quality-check/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── exception-handling.md
│   ├── dry-consolidation.md
│   ├── module-decomposition.md
│   └── type-safety.md
├── checklists/
│   └── requirements.md  # Pre-existing quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── main.py                           # CORS fix (Phase 1)
│   ├── utils.py                          # cached_fetch() helper (Phase 2)
│   ├── dependencies.py                   # require_selected_project() guard (Phase 2)
│   ├── logging_utils.py                  # Existing helpers adopted across codebase
│   ├── api/                              # Error handling adoption (Phase 2)
│   │   ├── board.py
│   │   ├── chat.py                       # Chat persistence migration (Phase 5)
│   │   ├── chores.py
│   │   ├── projects.py
│   │   ├── tasks.py
│   │   ├── workflow.py                   # Remove _get_repository_info() (Phase 2)
│   │   └── ...
│   ├── services/
│   │   ├── signal_chat.py               # Fix exception leaks (Phase 1)
│   │   ├── cache.py                     # Bounded size (Phase 6)
│   │   ├── database.py                  # Migration prefix audit (Phase 5)
│   │   ├── ai_agent.py                  # Singleton → DI (Phase 5)
│   │   ├── github_projects/
│   │   │   ├── service.py               # Split into submodules (Phase 3)
│   │   │   ├── issues.py               # NEW — Issue CRUD (Phase 3)
│   │   │   ├── pull_requests.py        # NEW — PR operations (Phase 3)
│   │   │   ├── copilot.py             # NEW — Copilot agent ops (Phase 3)
│   │   │   └── board.py               # NEW — Board data (Phase 3)
│   │   ├── chores/
│   │   │   └── template_builder.py     # Remove __import__() (Phase 5)
│   │   └── workflow_orchestrator/
│   │       └── orchestrator.py          # Singleton → DI (Phase 5)
│   └── migrations/
│       └── ...                          # Fix duplicate prefixes (Phase 5)
└── tests/
    └── unit/                            # New exception-specific tests (Phase 7)

frontend/
├── src/
│   ├── services/
│   │   ├── api/                        # NEW — Split from api.ts (Phase 3)
│   │   │   ├── client.ts              # request<T>(), ApiError, auth
│   │   │   ├── projects.ts
│   │   │   ├── chat.ts
│   │   │   ├── agents.ts
│   │   │   ├── tools.ts
│   │   │   ├── board.ts
│   │   │   └── index.ts              # Re-exports
│   │   └── api.ts                     # REMOVED after migration
│   ├── components/
│   │   ├── ui/
│   │   │   └── confirmation-dialog.tsx # Base modal pattern (Phase 2)
│   │   └── board/
│   │       ├── AgentPresetSelector.tsx # Dialog refactor (Phase 2)
│   │       └── IssueDetailModal.tsx    # Dialog refactor (Phase 2)
│   ├── hooks/
│   │   ├── usePipelineConfig.ts       # Split into sub-hooks (Phase 3)
│   │   ├── usePipelineState.ts        # NEW (Phase 3)
│   │   ├── usePipelineMutations.ts    # NEW (Phase 3)
│   │   └── usePipelineValidation.ts   # NEW (Phase 3)
│   ├── pages/                          # Memoization (Phase 6), tests (Phase 7)
│   └── test/                           # Consolidated from test/ + tests/ (Phase 5)
├── tsconfig.json                       # Strict checks (Phase 4)
├── eslint.config.js                    # Plugin additions (Phase 7)
├── vite.config.ts                      # Bundle analysis (Phase 6)
└── package.json                        # Remove jsdom (Phase 5)
```

**Structure Decision**: Web application structure (Option 2). Backend and frontend are separate top-level directories with independent build and test toolchains. No new top-level directories are added. All changes are within existing directories, with new submodules created within `services/github_projects/`, `services/api/`, and `hooks/`.

## Complexity Tracking

> No constitution violations identified. All changes follow simplicity and DRY principles.
