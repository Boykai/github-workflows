# Implementation Plan: Codebase Cleanup & Refactor

**Branch**: `001-codebase-cleanup-refactor` | **Date**: 2026-02-20 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-codebase-cleanup-refactor/spec.md`

## Summary

Refactor the codebase to improve maintainability by splitting two oversized backend services (`github_projects.py` at 4,448 lines and `copilot_polling.py` at 3,987 lines) into focused sub-modules under ~500 lines each, consolidating duplicated logic (repository resolution, polling initialization, session reconstruction, cache key construction) into shared utilities, standardizing error handling through a unified middleware, centralizing magic numbers as named constants, creating a shared frontend HTTP client, adding error boundaries and sessionStorage-backed state persistence, implementing WebSocket-primary/polling-fallback real-time updates, and adding test coverage for five untested backend services and six untested frontend hooks.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript ~5.4 (frontend)
**Primary Dependencies**: FastAPI 0.109+, httpx 0.26+, Pydantic 2.5+, pydantic-settings 2.1+, github-copilot-sdk 0.1+, agent-framework-core 1.0a1 (backend); React 18.3, @tanstack/react-query 5.17, socket.io-client 4.7, Vite 5.4 (frontend)
**Storage**: SQLite via aiosqlite 0.20+ (settings/session), in-memory cache (backend)
**Testing**: pytest 7.4+ with pytest-asyncio 0.23+, pytest-cov 4.1+ (backend); Vitest 4.0+ with @testing-library/react 16.3+, happy-dom 20.6+ (frontend)
**Target Platform**: Linux server (backend Docker), modern browsers (frontend SPA)
**Project Type**: web (backend + frontend)
**Performance Goals**: No regression from current performance; refactoring is internal-only
**Constraints**: All existing tests must pass without assertion changes; no API contract changes
**Scale/Scope**: ~16,500 LOC backend, ~2,800 LOC frontend hooks/services; 12 backend service files, 12 frontend hooks, 8 API route files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | spec.md completed with 7 prioritized user stories (P1–P3), Given-When-Then scenarios, FR-001–FR-016, and measurable success criteria SC-001–SC-010 |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates; plan.md, research.md, data-model.md, quickstart.md generated per template |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase generates design artifacts; tasks phase will decompose into executable units per user story |
| IV. Test Optionality with Clarity | ✅ PASS | Tests explicitly required by spec (FR-015, FR-016, US7); existing tests are the correctness baseline (SC-007) |
| V. Simplicity and DRY | ✅ PASS | The entire feature is about eliminating duplication and reducing complexity; module splits follow single-responsibility principle |

## Project Structure

### Documentation (this feature)

```text
specs/001-codebase-cleanup-refactor/
├── plan.md              # This file
├── research.md          # Phase 0: Research findings
├── data-model.md        # Phase 1: Entity & module definitions
├── quickstart.md        # Phase 1: Developer guide with test patterns
├── contracts/           # Phase 1: API contract documentation
│   └── error-response.md
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/                          # Route handlers (8 files)
│   │   ├── auth.py                   # Auth routes (199 lines)
│   │   ├── board.py                  # Board routes (84 lines)
│   │   ├── chat.py                   # Chat routes (635 lines)
│   │   ├── projects.py               # Project routes (371 lines)
│   │   ├── settings.py               # Settings routes (127 lines)
│   │   ├── tasks.py                  # Task routes (173 lines)
│   │   ├── webhooks.py               # Webhook routes (534 lines)
│   │   └── workflow.py               # Workflow routes (762 lines)
│   ├── config.py                     # Pydantic settings (108 lines)
│   ├── constants.py                  # Named constants (93 lines)
│   ├── exceptions.py                 # Exception hierarchy (61 lines)
│   ├── main.py                       # FastAPI app setup (183 lines)
│   ├── models/                       # Pydantic models
│   ├── services/                     # Business logic
│   │   ├── github_projects.py        # ⚠ 4,448 lines → split into sub-modules
│   │   ├── copilot_polling.py        # ⚠ 3,987 lines → split into sub-modules
│   │   ├── workflow_orchestrator.py   # 1,959 lines (large but not in scope for split)
│   │   ├── ai_agent.py               # 772 lines
│   │   ├── settings_store.py         # 413 lines (needs tests)
│   │   ├── agent_tracking.py         # 365 lines (needs tests)
│   │   ├── completion_providers.py   # 302 lines (needs tests)
│   │   ├── github_auth.py            # 293 lines
│   │   ├── database.py               # 225 lines
│   │   ├── session_store.py          # 150 lines (needs tests)
│   │   ├── cache.py                  # 128 lines
│   │   └── websocket.py              # 105 lines
│   └── prompts/                      # Prompt templates
├── tests/
│   ├── conftest.py                   # Shared fixtures
│   ├── test_api_e2e.py               # E2E API tests
│   ├── unit/                         # Unit tests (10 files)
│   └── integration/                  # Integration tests

frontend/
├── src/
│   ├── hooks/                        # React hooks (12 files, 3 with tests)
│   │   ├── useAuth.ts / useAuth.test.tsx
│   │   ├── useProjects.ts / useProjects.test.tsx
│   │   ├── useRealTimeSync.ts / useRealTimeSync.test.tsx
│   │   ├── useChat.ts               # ⚠ No tests (238 lines)
│   │   ├── useAgentConfig.ts         # ⚠ No tests (237 lines)
│   │   ├── useWorkflow.ts            # ⚠ No tests (163 lines)
│   │   ├── useSettings.ts            # ⚠ No tests (113 lines)
│   │   ├── useProjectBoard.ts        # ⚠ No tests (98 lines)
│   │   └── useAppTheme.ts            # ⚠ No tests (63 lines)
│   ├── services/
│   │   └── api.ts                    # API client (294 lines)
│   ├── components/                   # UI components (6 directories)
│   ├── pages/                        # Page components
│   └── types/                        # TypeScript types
├── vitest.config.ts
└── package.json
```

**Structure Decision**: Web application (backend + frontend). Existing directory structure is retained. New sub-modules are created within `backend/src/services/` as sub-packages (`github_projects/` and `copilot_polling/` directories with `__init__.py` re-export facades). Frontend changes are within existing `src/hooks/`, `src/services/`, and `src/components/` directories.

## Complexity Tracking

> No Constitution Check violations found. No complexity justifications needed.
