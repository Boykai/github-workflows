# Implementation Plan: Improve Test Coverage to 85% and Fix Discovered Bugs

**Branch**: `001-test-coverage-bugfix` | **Date**: 2026-02-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-test-coverage-bugfix/spec.md`

## Summary

Audit and expand the test suite for Tech Connect (React/TypeScript frontend + FastAPI/Python backend) to achieve a minimum of 85% aggregate code coverage. The approach uses existing Vitest + @vitest/coverage-v8 for frontend and Pytest + pytest-cov for backend. During this process, identify and resolve any bugs uncovered by the new tests, following the Arrange-Act-Assert pattern with isolated, deterministic tests.

## Technical Context

**Language/Version**: TypeScript 5.x (frontend), Python 3.11+ (backend)  
**Primary Dependencies**: React 18.3 + Vitest 4.0 + Testing Library (frontend), FastAPI + Pytest 7.4 + pytest-cov (backend)  
**Storage**: N/A — no new storage; testing covers existing aiosqlite-backed services  
**Testing**: Vitest + @vitest/coverage-v8 (frontend), Pytest + pytest-cov + pytest-asyncio (backend)  
**Target Platform**: Web application — browser (frontend), Linux server (backend)  
**Project Type**: web (frontend + backend)  
**Performance Goals**: N/A — quality improvement, not performance  
**Constraints**: Minimum 85% aggregate test coverage across frontend and backend  
**Scale/Scope**: ~45 frontend source files (hooks, components, services, pages), ~30 backend source files (API routes, models, services, prompts)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | `spec.md` contains 4 prioritized user stories (P1–P3) with Given-When-Then acceptance scenarios and clear scope boundaries |
| II. Template-Driven Workflow | ✅ PASS | Using `plan-template.md` canonical template; all sections populated |
| III. Agent-Orchestrated Execution | ✅ PASS | Separate agents for specify → plan → tasks → implement; each produces defined artifacts |
| IV. Test Optionality with Clarity | ✅ PASS | Tests are explicitly the core deliverable of this feature — mandated by the specification itself |
| V. Simplicity and DRY | ✅ PASS | No new abstractions introduced; testing existing code with existing frameworks; no premature generalization |

**Gate Result**: ALL PASS — proceed to Phase 0.

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
│   ├── api/             # Route handlers: auth, board, chat, projects, settings, tasks, webhooks, workflow
│   ├── models/          # Pydantic models: board, chat, project, settings, task, user
│   ├── services/        # Business logic: ai_agent, cache, copilot_polling, database, github_auth, github_projects, session_store, settings_store, websocket, workflow_orchestrator, agent_tracking, completion_providers
│   ├── prompts/         # AI prompt templates: task_generation, issue_generation
│   ├── migrations/      # Database migration scripts
│   ├── config.py        # Application configuration
│   ├── constants.py     # Shared constants
│   ├── exceptions.py    # Custom exception classes
│   └── main.py          # FastAPI application entry point
└── tests/
    ├── unit/            # Unit tests for services, models, routes
    ├── integration/     # Integration tests (e.g., agent assignment)
    ├── test_api_e2e.py  # End-to-end API tests
    └── conftest.py      # Shared fixtures and mocks

frontend/
├── src/
│   ├── components/
│   │   ├── auth/        # LoginButton
│   │   ├── board/       # ProjectBoard, IssueCard, BoardColumn, AgentConfigRow, etc.
│   │   ├── chat/        # ChatInterface, MessageBubble, preview components
│   │   ├── common/      # ErrorDisplay, RateLimitIndicator
│   │   ├── settings/    # GlobalSettings, AIPreferences, DisplayPreferences, etc.
│   │   └── sidebar/     # ProjectSelector, ProjectSidebar, TaskCard
│   ├── hooks/           # Custom hooks: useAuth, useProjects, useChat, useSettings, etc.
│   ├── pages/           # ProjectBoardPage, SettingsPage
│   ├── services/        # api.ts — HTTP client and API functions
│   ├── types/           # TypeScript type definitions
│   └── test/            # Test setup (happy-dom, mocks)
├── e2e/                 # Playwright E2E tests
├── vitest.config.ts     # Vitest configuration
└── playwright.config.ts # Playwright configuration
```

**Structure Decision**: Web application layout with separate `frontend/` and `backend/` directories. Tests live within each project: `backend/tests/` (unit, integration, e2e) and `frontend/src/**/*.test.{ts,tsx}` (co-located unit tests) plus `frontend/e2e/` (E2E tests via Playwright).

## Complexity Tracking

> No constitution violations detected — no entries required.
