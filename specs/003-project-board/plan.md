# Implementation Plan: Standalone Project Board Page

**Branch**: `003-project-board` | **Date**: 2026-02-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-project-board/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Add a standalone `/project-board` route with Kanban-style visualization of GitHub Project V2 boards. The feature includes a project selector dropdown, status-based columns with colored dots and aggregate statistics, rich issue cards (repo name, assignee avatars, linked PR badges, priority/estimate/size), a detail modal with GitHub links, 15-second auto-refresh with pause-on-modal, and proper loading/error states. Backend adds three new FastAPI endpoints proxying GitHub Projects V2 GraphQL API for board data and linked PRs. Frontend extends TypeScript types and adds new React components styled with the existing CSS design system.

## Technical Context

**Language/Version**: TypeScript 5.4 (frontend), Python 3.11+ (backend)  
**Primary Dependencies**: React 18.3, Vite 5.4, @tanstack/react-query 5.17, FastAPI 0.109+, httpx 0.26+  
**Storage**: N/A (all data proxied from GitHub Projects V2 GraphQL API; existing in-memory cache for API responses)  
**Testing**: Vitest (unit), Playwright (E2E), pytest + pytest-asyncio (backend)  
**Target Platform**: Modern web browsers (Chrome, Firefox, Safari, Edge)  
**Project Type**: Web (frontend React SPA + backend Python FastAPI API)  
**Performance Goals**: Page load < 3s, dropdown interaction < 1s, modal open < 1s, auto-refresh every 15s  
**Constraints**: Must match existing app design system; GitHub token must have read:project and repo scopes; board must remain responsive with 100+ issues  
**Scale/Scope**: 1 new route, ~8 new React components, 3 new backend endpoints, extended TypeScript types, new GraphQL queries

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Evaluation (Before Phase 0)

| Principle | Status | Justification |
|-----------|--------|---------------|
| **I. Specification-First** | ✅ PASS | Complete spec.md with 4 prioritized user stories (P1: View Board, P2: Issue Details, P3: Auto-Refresh, P4: Loading/Error), Given-When-Then acceptance scenarios, edge cases, and clear scope boundaries. |
| **II. Template-Driven** | ✅ PASS | Following plan-template.md structure. All sections populated per template requirements. No custom sections added. |
| **III. Agent-Orchestrated** | ✅ PASS | Single speckit.plan agent execution. Clear input (spec.md) and outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md). Handoff to speckit.tasks next. |
| **IV. Test Optionality** | ✅ PASS | Spec does not explicitly request tests. Manual verification via browser sufficient for visual Kanban board. Existing test infrastructure available if needed. |
| **V. Simplicity & DRY** | ✅ PASS | Leverages existing GitHub Projects V2 service, cache, and auth infrastructure. New components follow existing patterns (ProjectSelector, TaskCard). No premature abstractions. |

**Pre-Design Gate Status**: ✅ **PASSED** - All principles satisfied. No violations requiring justification.

### Post-Design Evaluation (After Phase 1)

| Principle | Status | Justification |
|-----------|--------|---------------|
| **I. Specification-First** | ✅ PASS | Design artifacts (research.md, data-model.md, contracts/) align with all 16 functional requirements. No scope expansion beyond spec. |
| **II. Template-Driven** | ✅ PASS | All Phase 0-1 artifacts follow prescribed templates. No deviations introduced. |
| **III. Agent-Orchestrated** | ✅ PASS | Phase 0-1 completed by single agent. Clean handoff state achieved. Ready for speckit.tasks. |
| **IV. Test Optionality** | ✅ PASS | Design confirms no new test infrastructure required per spec. Manual verification sufficient for Kanban board UI. |
| **V. Simplicity & DRY** | ✅ PASS | Reuses existing github_projects_service for GraphQL queries. New endpoints follow established FastAPI patterns. Frontend components follow existing component structure. No unnecessary abstractions. |

**Post-Design Gate Status**: ✅ **PASSED** - Design maintains constitutional compliance. No complexity tracking required.

## Project Structure

### Documentation (this feature)

```text
specs/003-project-board/
├── spec.md              # Feature specification (completed)
├── checklists/
│   └── requirements.md  # Spec validation checklist (completed)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (generated below)
├── data-model.md        # Phase 1 output (generated below)
├── quickstart.md        # Phase 1 output (generated below)
├── contracts/           # Phase 1 output (generated below)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── __init__.py          # Add project_board router
│   │   └── project_board.py     # New: 3 endpoints (list projects, board data, linked PRs)
│   ├── models/
│   │   └── project_board.py     # New: Pydantic models for board data
│   └── services/
│       └── github_projects.py   # Extended: new GraphQL queries for board data + linked PRs
└── tests/                       # No changes required (tests optional per constitution)

frontend/
├── src/
│   ├── types/
│   │   └── index.ts             # Extended: BoardProject, BoardColumn, BoardIssueCard, LinkedPR types
│   ├── services/
│   │   └── api.ts               # Extended: projectBoardApi methods
│   ├── hooks/
│   │   └── useProjectBoard.ts   # New: data fetching + auto-refresh hook
│   ├── components/
│   │   ├── sidebar/
│   │   │   └── ProjectSidebar.tsx  # Modified: add /project-board nav link
│   │   └── project-board/
│   │       ├── ProjectBoardPage.tsx   # New: main page component
│   │       ├── BoardColumn.tsx        # New: status column component
│   │       ├── BoardIssueCard.tsx     # New: issue card component
│   │       └── IssueDetailModal.tsx   # New: detail modal component
│   ├── App.tsx                  # Modified: add /project-board route
│   └── App.css                  # Extended: board-specific styles
└── tests/                       # No changes required (tests optional per constitution)
```

**Structure Decision**: Web application with React frontend + FastAPI backend. Changes span both layers: backend adds new API endpoints proxying GitHub GraphQL API; frontend adds new route, page component, and supporting components. Follows existing patterns: backend api/models/services structure, frontend components/hooks/services structure.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations detected. This section intentionally left minimal per constitution principle V (Simplicity).
