# Implementation Plan: Bug Basher — Full Codebase Review & Fix

**Branch**: `001-bug-basher` | **Date**: 2026-03-04 | **Spec**: `specs/001-bug-basher/spec.md`
**Input**: Feature specification from `/specs/001-bug-basher/spec.md`

## Summary

Perform a comprehensive bug bash across the entire codebase, auditing every file for security vulnerabilities, runtime errors, logic bugs, test gaps, and code quality issues — in priority order. Each bug is either fixed in-place with a regression test (✅ Fixed) or flagged with a `TODO(bug-bash)` comment for human review (⚠️ Flagged). The codebase is a web application with a Python/FastAPI backend (~29 k LOC, 80+ source files) and a React/TypeScript frontend (~17 k LOC, 60+ source files). Validation requires the full pytest suite, Ruff lint/format, Vitest, ESLint, and TypeScript type-check all passing after changes.

## Technical Context

**Language/Version**: Python ≥3.11 (backend), TypeScript 5.4 / React 18.3 (frontend)
**Primary Dependencies**: FastAPI ≥0.109, Pydantic v2, httpx, aiosqlite, github-copilot-sdk, agent-framework-core, React, @tanstack/react-query, Vite, Tailwind CSS, socket.io-client, dnd-kit
**Storage**: SQLite via aiosqlite (durable settings/session storage)
**Testing**: pytest + pytest-asyncio + pytest-cov (backend, ~1200+ unit tests across 45+ files), Vitest + @testing-library/react (frontend, ~277 tests across 29 files), Playwright (e2e)
**Linting**: Ruff (backend lint + format), ESLint 9 + Prettier (frontend), Pyright (type-check)
**Target Platform**: Linux server (Docker), browser client
**Project Type**: Web application (backend + frontend)
**Performance Goals**: N/A — bug bash does not alter performance characteristics
**Constraints**: No new dependencies, no architecture changes, no public API surface changes, minimal focused fixes only
**Scale/Scope**: ~46 k LOC total, ~140+ source files to audit across backend and frontend

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Specification-First Development | ✅ PASS | spec.md exists with prioritized user stories (P1–P5), Given-When-Then scenarios, and clear scope |
| II | Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| III | Agent-Orchestrated Execution | ✅ PASS | Plan phase produces plan.md, research.md, data-model.md, quickstart.md, contracts/ — single-responsibility |
| IV | Test Optionality with Clarity | ✅ PASS | Tests are explicitly required by spec (FR-004, FR-007); each bug fix MUST have a regression test |
| V | Simplicity and DRY | ✅ PASS | Each fix must be minimal and focused (FR-013); no drive-by refactors |
| — | Branch/Directory Naming | ✅ PASS | `001-bug-basher` follows `###-short-name` convention |
| — | Phase-Based Execution | ✅ PASS | Specify → Plan → Tasks → Implement flow respected |
| — | Independent User Stories | ✅ PASS | Five user stories (P1–P5) are independently testable; each maps to a bug category |

**Gate Result**: ✅ All principles satisfied. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/001-bug-basher/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output — codebase audit methodology and findings
├── data-model.md        # Phase 1 output — bug report entity model
├── quickstart.md        # Phase 1 output — how to execute the bug bash
├── contracts/           # Phase 1 output — review checklist contracts per category
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/             # 13 route modules (auth, board, chat, cleanup, health, mcp, projects, settings, signal, tasks, webhooks, workflow, chores)
│   ├── models/          # 12 Pydantic model modules
│   ├── services/        # 20+ service modules (AI, auth, cache, chores, copilot_polling, database, encryption, github_projects, mcp, session, settings, signal, websocket, workflow_orchestrator)
│   ├── middleware/       # request_id middleware
│   ├── migrations/      # database migrations
│   ├── prompts/         # AI prompt templates
│   ├── config.py        # configuration management
│   ├── constants.py     # application constants
│   ├── dependencies.py  # dependency injection
│   ├── exceptions.py    # custom exceptions
│   ├── logging_utils.py # centralized logging
│   ├── main.py          # FastAPI app entry
│   └── utils.py         # utility functions
└── tests/
    ├── conftest.py      # shared fixtures
    ├── helpers/         # test factories, mocks, assertions
    ├── integration/     # 3 integration test files
    └── unit/            # 45+ unit test files

frontend/
├── src/
│   ├── components/      # React components (auth, board, chat, chores, common, settings)
│   ├── hooks/           # custom React hooks (useAuth, useBoard, useChat, useChores, useCleanup, useMcp, useProjects, useSettings, useSocket, useTasks, useWorkflow)
│   ├── lib/             # utility library
│   ├── pages/           # page components
│   ├── services/        # API service layer
│   ├── test/            # test setup
│   ├── types/           # TypeScript type definitions
│   └── utils/           # utility functions
└── tests/               # component and unit tests (via Vitest)
```

**Structure Decision**: Web application with separate backend (Python/FastAPI) and frontend (React/TypeScript). Bug bash audits both codebases independently, organized by the five priority categories defined in the spec.

## Complexity Tracking

> No Constitution Check violations — this section is intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
