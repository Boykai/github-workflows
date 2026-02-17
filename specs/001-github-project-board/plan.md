# Implementation Plan: Real-Time GitHub Project Board

**Branch**: `001-github-project-board` | **Date**: 2026-02-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-github-project-board/spec.md`

## Summary

Add a standalone `/project-board` route displaying a Kanban-style board with real-time GitHub Project V2 data. The board allows users to select from available projects, view issues organized by status columns with rich metadata (priority, size, estimate, linked PRs, assignees), and click cards for detail modals. Auto-refresh polling every 15 seconds keeps data current.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript ~5.4 (frontend)  
**Primary Dependencies**: FastAPI, React 18, TanStack React Query, Tailwind CSS  
**Storage**: N/A (no persistent storage; data fetched from GitHub API)  
**Testing**: pytest + pytest-asyncio (backend), vitest + playwright (frontend)  
**Target Platform**: Web application (Docker containers)
**Project Type**: Web (frontend + backend)  
**Performance Goals**: Board loads within 5 seconds of project selection (SC-001)  
**Constraints**: 15-second polling interval for auto-refresh; graceful handling of GitHub API rate limits  
**Scale/Scope**: Single user viewing their accessible GitHub Projects (personal + org)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | spec.md complete with 3 prioritized user stories, acceptance scenarios, and scope |
| II. Template-Driven | ✅ PASS | Using canonical plan template; spec follows standard structure |
| III. Agent-Orchestrated | ✅ PASS | Following speckit workflow phases (specify → plan → tasks → implement) |
| IV. Test Optionality | ✅ PASS | Tests not explicitly required in spec; will be included for new API endpoints |
| V. Simplicity/DRY | ✅ PASS | Extends existing patterns (github_projects service, React hooks, existing types) |

**Gate Result**: ALL PASS - Proceeding to Phase 0

### Post-Design Re-evaluation (Phase 1 Complete)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | Design artifacts align with spec requirements |
| II. Template-Driven | ✅ PASS | All outputs follow canonical templates |
| III. Agent-Orchestrated | ✅ PASS | Ready for tasks phase handoff |
| IV. Test Optionality | ✅ PASS | API contract defined; tests can follow contract |
| V. Simplicity/DRY | ✅ PASS | Reuses existing GraphQL patterns, extends types, follows React patterns |

**Post-Design Gate Result**: ALL PASS - Ready for `/speckit.tasks`

## Project Structure

### Documentation (this feature)

```text
specs/001-github-project-board/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── board-api.yaml   # OpenAPI spec for board endpoints
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   └── board.py           # NEW: Board API endpoints
│   ├── models/
│   │   └── board.py           # NEW: Board-specific Pydantic models
│   └── services/
│       └── github_projects.py # EXTEND: Add board data queries
└── tests/
    └── unit/
        └── test_board.py      # NEW: Unit tests for board endpoints

frontend/
├── src/
│   ├── components/
│   │   └── board/             # NEW: Board UI components
│   │       ├── ProjectBoard.tsx
│   │       ├── BoardColumn.tsx
│   │       ├── IssueCard.tsx
│   │       └── IssueDetailModal.tsx
│   ├── hooks/
│   │   └── useProjectBoard.ts # NEW: Board data hook with polling
│   ├── pages/
│   │   └── ProjectBoardPage.tsx # NEW: Page component
│   ├── types/
│   │   └── index.ts           # EXTEND: Add board types
│   └── App.tsx                # EXTEND: Add route
└── tests/
    └── (vitest tests as needed)
```

**Structure Decision**: Web application structure (Option 2). Backend extends existing FastAPI service with new router. Frontend adds new page/route with dedicated components following existing patterns.

## Complexity Tracking

> No constitution violations identified. Complexity justified below for transparency.

| Decision | Rationale | Simpler Alternative Rejected Because |
|----------|-----------|-------------------------------------|
| New `/board` API router | Separates board-specific endpoints from existing `/projects` | Extending existing router would bloat it; board has distinct data shape |
| Dedicated board models | BoardItem differs from Task (includes linked PRs, custom fields) | Reusing Task model would require awkward field additions |
| 15-second polling | Provides near-real-time experience | WebSocket overhead not justified for read-only board; existing WebSocket is for task sync |
