# Implementation Plan: Improve Test Coverage to 85% and Fix Discovered Bugs

**Branch**: `001-test-coverage-bugfix` | **Date**: 2026-02-20 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-test-coverage-bugfix/spec.md`

## Summary

Audit and expand the test suite for Tech Connect to achieve a minimum of 85% code coverage across the codebase. The project is a web application with a React/TypeScript frontend (tested with Vitest) and a Python/FastAPI backend (tested with pytest). Current test coverage is below 85%. New tests will follow the Arrange-Act-Assert pattern, be isolated and deterministic. Any bugs discovered during testing will be fixed in the same branch with clear commit separation.

## Technical Context

**Language/Version**: TypeScript 5.x (frontend), Python 3.11 (backend)  
**Primary Dependencies**: React 18.3.1, Vitest 4.x, @vitest/coverage-v8 (frontend); FastAPI, pytest 7.4+, pytest-cov, pytest-asyncio (backend)  
**Storage**: SQLite (settings store via aiosqlite)  
**Testing**: Vitest + @vitest/coverage-v8 (frontend), pytest + pytest-cov (backend)  
**Target Platform**: Web application (Docker-based, Linux server)  
**Project Type**: Web (frontend + backend)  
**Performance Goals**: N/A — this feature is test-only; no runtime performance impact  
**Constraints**: Overall test coverage must reach ≥85% as reported by Vitest and pytest-cov  
**Scale/Scope**: ~35 frontend source files, ~35 backend source files; 3 existing frontend test files, 11 existing backend test files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | spec.md created with prioritized user stories (US1–US4), acceptance scenarios, and scope boundaries |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | ✅ PASS | specify → plan pipeline; each agent has single responsibility |
| IV. Test Optionality with Clarity | ✅ PASS | Tests are explicitly the core feature requirement per spec FR-002; TDD approach is inherent to the feature |
| V. Simplicity and DRY | ✅ PASS | Leveraging existing test frameworks (Vitest, pytest) and coverage tools; no new abstractions introduced |

**Gate Result**: ✅ ALL PASS — Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-test-coverage-bugfix/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/             # FastAPI route handlers (auth, board, chat, projects, settings, tasks, webhooks, workflow)
│   ├── models/          # Pydantic models (board, chat, project, settings, task, user)
│   ├── services/        # Business logic (ai_agent, cache, copilot_polling, database, github_auth, github_projects, session_store, settings_store, websocket, workflow_orchestrator, agent_tracking, completion_providers)
│   ├── prompts/         # AI prompt templates (issue_generation, task_generation)
│   ├── migrations/      # Database migrations
│   ├── config.py        # Application configuration
│   ├── constants.py     # Shared constants
│   ├── exceptions.py    # Custom exception classes
│   └── main.py          # FastAPI application entry point
└── tests/
    ├── conftest.py      # Shared fixtures
    ├── unit/            # Unit tests (10 files)
    ├── integration/     # Integration tests (1 file)
    └── test_api_e2e.py  # End-to-end API tests

frontend/
├── src/
│   ├── components/      # React components (auth, board, chat, common, settings, sidebar)
│   ├── hooks/           # Custom React hooks (9 hooks, 3 tested)
│   ├── pages/           # Page components (ProjectBoardPage, SettingsPage)
│   ├── services/        # API service layer (api.ts)
│   ├── test/            # Test setup (setup.ts)
│   └── types/           # TypeScript type definitions
└── e2e/                 # Playwright E2E tests (3 files)
```

**Structure Decision**: Web application structure with separate frontend and backend directories. Test files for frontend are co-located with source in `src/` (vitest pattern). Backend tests are in a dedicated `tests/` directory with `unit/` and `integration/` subdirectories.

## Complexity Tracking

> No constitution violations — table left empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
