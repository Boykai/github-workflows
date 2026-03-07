# Implementation Plan: Simplicity & DRY Refactoring Across Backend and Frontend

**Branch**: `028-simplicity-dry-refactor` | **Date**: 2026-03-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/028-simplicity-dry-refactor/spec.md`

## Summary

Eliminate ~1,500+ lines of duplicated code and reduce architectural complexity across the backend and frontend. The backend consolidates 8 duplicate repository resolution implementations into one canonical helper, wires up unused error handling and validation helpers, adds a generic cache wrapper, decomposes a 4,913-line God object into 8 focused modules (<800 LOC each) using composition over inheritance with a backward-compatible facade, and unifies 3 competing initialization patterns into a single lifespan → app.state → Depends() path. The frontend creates a CRUD hook factory, unified settings hook, shared UI components (Modal, PreviewCard, ErrorAlert), centralized query key registry, API endpoint factory, and splits a 417-line ChatInterface megacomponent. Test helpers are consolidated into conftest.py fixtures.

## Technical Context

**Language/Version**: Python ≥3.12 (target 3.13) for backend; TypeScript 5.9 + React 19.2 for frontend
**Primary Dependencies**: FastAPI ≥0.135, githubkit ≥0.14.6, httpx ≥0.28, aiosqlite ≥0.22 (backend); Vite 7.3, TanStack React Query 5.90, React Router DOM 7.13, Radix UI, @dnd-kit, Tailwind CSS 4.2 (frontend)
**Storage**: SQLite via aiosqlite (async); InMemoryCache with TTL for API responses
**Testing**: pytest ≥9.0 with pytest-asyncio (backend, 57 unit + 3 integration); Vitest 4.0 with @testing-library/react + Playwright (frontend, 36 test files)
**Target Platform**: Linux server (Docker Compose) with browser-based SPA frontend
**Project Type**: Web application (backend + frontend)
**Performance Goals**: No regression from current baseline; cache TTLs preserved (5min long, 15min projects, 1min medium)
**Constraints**: Zero breaking changes to public API; backward-compatible facade for all existing imports; all existing tests must pass without modification
**Scale/Scope**: 18 API router modules, 4,913-line service monolith (79 methods), 25 hooks, 17 API endpoint groups, 85+ components

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Assessment

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Specification-First Development | ✅ PASS | spec.md complete with 6 prioritized user stories, acceptance scenarios, edge cases |
| II | Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates |
| III | Agent-Orchestrated Execution | ✅ PASS | Plan phase produces plan.md, research.md, data-model.md, contracts/, quickstart.md |
| IV | Test Optionality with Clarity | ✅ PASS | Spec requires all existing tests to pass (FR-017); no new test creation mandated beyond test helper consolidation |
| V | Simplicity and DRY | ✅ PASS | This feature is explicitly about enforcing Simplicity & DRY — the entire purpose is reducing duplication and complexity |

### Post-Phase 1 Assessment

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Specification-First Development | ✅ PASS | All design decisions traced to spec requirements |
| II | Template-Driven Workflow | ✅ PASS | All artifacts generated per template |
| III | Agent-Orchestrated Execution | ✅ PASS | Clear phase boundaries with explicit handoffs |
| IV | Test Optionality with Clarity | ✅ PASS | Tests are not opt-in here — spec mandates all existing suites pass (SC-009, SC-010) |
| V | Simplicity and DRY | ⚠️ JUSTIFIED | Service decomposition adds 8 new files; justified because it replaces 1 file with 4,913 lines. Net complexity decreases. See Complexity Tracking. |

## Project Structure

### Documentation (this feature)

```text
specs/028-simplicity-dry-refactor/
├── plan.md              # This file
├── research.md          # Phase 0: Research decisions
├── data-model.md        # Phase 1: Entity models and type definitions
├── quickstart.md        # Phase 1: Developer onboarding guide
├── contracts/           # Phase 1: API and component contracts
│   ├── api.md           # Backend helper and DI contracts
│   ├── components.md    # Frontend component and hook contracts
│   ├── backend-helpers.md   # Shared helper function signatures
│   ├── service-modules.md   # Decomposed service module contracts
│   └── frontend-factories.md # Hook and API factory contracts
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/                          # 18 router modules (modified: adopt shared helpers)
│   │   ├── board.py                  # Modified: use handle_service_error(), cached_fetch()
│   │   ├── chat.py                   # Modified: use require_selected_project(), cached_fetch()
│   │   ├── chores.py                 # Modified: use require_selected_project()
│   │   ├── projects.py               # Modified: use handle_service_error(), cached_fetch()
│   │   ├── tasks.py                  # Modified: use require_selected_project()
│   │   ├── workflow.py               # Modified: delete _get_repository_info(), use shared helpers
│   │   └── auth.py                   # Modified: use handle_service_error()
│   ├── dependencies.py               # Modified: add require_selected_project()
│   ├── logging_utils.py              # Existing: handle_service_error(), safe_error_response()
│   ├── utils.py                      # Existing: resolve_repository() (canonical)
│   ├── main.py                       # Modified: consolidate initialization in lifespan()
│   ├── services/
│   │   ├── cache.py                  # Modified: add cached_fetch() wrapper
│   │   └── github_projects/
│   │       ├── __init__.py           # Modified: backward-compatible facade with re-exports
│   │       ├── service.py            # Modified: remove module-level singleton, reduce to facade
│   │       ├── client.py             # NEW: HTTP client and GraphQL execution
│   │       ├── projects.py           # NEW: Project listing and management
│   │       ├── issues.py             # NEW: Issue CRUD operations
│   │       ├── pull_requests.py      # NEW: PR operations
│   │       ├── copilot.py            # NEW: Copilot/AI agent operations
│   │       ├── fields.py             # NEW: Project field management
│   │       ├── board.py              # NEW: Board data and views
│   │       └── repository.py         # NEW: Repository and file operations
│   └── github_auth.py               # Modified: remove module-level singleton
└── tests/
    ├── conftest.py                   # Modified: absorb mock factories from helpers/mocks.py
    ├── test_api_e2e.py               # Modified: replace inline patches with conftest fixtures
    └── helpers/
        └── mocks.py                  # Deprecated: factories moved to conftest.py

frontend/
├── src/
│   ├── hooks/
│   │   ├── useCrudResource.ts        # NEW: Generic CRUD hook factory
│   │   ├── useSettings.ts            # Modified: extract generic useSettingsHook()
│   │   ├── useAgents.ts              # Modified: refactor to use useCrudResource
│   │   ├── useChores.ts              # Modified: refactor to use useCrudResource
│   │   └── queryKeys.ts              # NEW: Centralized query key registry
│   ├── components/
│   │   ├── common/
│   │   │   ├── PreviewCard.tsx        # NEW: Shared preview/proposal card
│   │   │   ├── Modal.tsx              # NEW: Shared modal wrapper
│   │   │   └── ErrorAlert.tsx         # NEW: Shared error alert component
│   │   └── chat/
│   │       ├── ChatInterface.tsx      # Modified: delegate to sub-components
│   │       ├── ChatMessageList.tsx    # NEW: Extracted message list
│   │       └── ChatInput.tsx          # NEW: Extracted input component
│   └── services/
│       └── api.ts                    # Modified: add createApiGroup() factory, refactor groups
└── tests/                            # Existing tests must pass without modification
```

**Structure Decision**: Web application structure (backend + frontend). All changes are modifications to existing files or new files within the established directory structure. No new top-level directories. The 8 decomposed service modules are added under the existing `services/github_projects/` package.

## Complexity Tracking

> Justified violations of Constitution Principle V (Simplicity and DRY)

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 8 new service module files | Decomposing 4,913-line monolith (79 methods) into focused modules <800 LOC each | Single file is unmaintainable; 8 focused files are simpler to navigate than 1 massive file |
| Backward-compatible facade in `__init__.py` | 15+ files import `github_projects_service` singleton; facade prevents big-bang migration | Updating all 15+ import sites simultaneously is high-risk and creates a massive, hard-to-review changeset |
| CRUD hook factory abstraction | Consolidates ~600 lines of duplicated hook logic across agents and chores | Per-resource hooks duplicate 90% of logic; factory is simpler than maintaining parallel implementations |
| API endpoint factory abstraction | Consolidates ~300 lines of duplicated API client code across 17 endpoint groups | Per-group definitions repeat the same request() wrapper pattern; factory eliminates boilerplate |
