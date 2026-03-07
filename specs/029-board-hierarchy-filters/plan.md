# Implementation Plan: Project Board — Parent Issue Hierarchy, Sub-Issue Display, Agent Pipeline Fixes & Functional Filters

**Branch**: `029-board-hierarchy-filters` | **Date**: 2026-03-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/029-board-hierarchy-filters/spec.md`

## Summary

Restructure the Project Board to show only parent GitHub Issues as top-level cards with collapsible sub-issue panels (displaying agent/model metadata), add label chips to parent cards, make columns independently scrollable, fix Agent Pipeline model name and tool count data-binding bugs, dynamically rename the "Custom" pipeline label to the active saved configuration name, and implement functional Filter, Sort, and Group By controls operating on the parent-issue-only view. The backend GraphQL query must be extended to fetch labels, and the frontend adds client-side filtering/sorting/grouping with localStorage persistence.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript/React 18 (frontend), Node.js 20  
**Primary Dependencies**: FastAPI, TanStack Query, @dnd-kit/core, Tailwind CSS v4  
**Storage**: GitHub API (GraphQL + REST) with in-memory caching (backend), localStorage (frontend persistence)  
**Testing**: pytest (backend), Vitest (frontend)  
**Target Platform**: Web (Linux server backend, modern browser frontend)  
**Project Type**: Web application (backend + frontend)  
**Performance Goals**: Filter/Sort/Group operations complete in <1s (client-side), board render <2s for 50+ parent issues  
**Constraints**: No additional API calls for sort/group operations; filters may require client-side predicate functions; GitHub API rate limits apply  
**Scale/Scope**: Boards with up to 100 parent issues, each with up to 50 sub-issues; 8 user stories (FR-001 through FR-013)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | spec.md complete with 8 prioritized user stories, Given-When-Then scenarios, clear scope boundaries |
| II. Template-Driven | ✅ PASS | All artifacts follow canonical templates; plan.md, research.md, data-model.md, contracts/, quickstart.md |
| III. Agent-Orchestrated | ✅ PASS | speckit.plan produces design artifacts; speckit.tasks will decompose into executable tasks |
| IV. Test Optionality | ✅ PASS | Tests not explicitly mandated in spec; include only if needed for critical logic (e.g., filter predicates) |
| V. Simplicity/DRY | ✅ PASS | Client-side filtering/sorting reuses in-memory data; no new backend endpoints for sort/group; existing component patterns extended |

## Post-Phase 1 Constitution Re-check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | All design artifacts trace back to FR-001 through FR-013 |
| II. Template-Driven | ✅ PASS | Plan, research, data-model, contracts, quickstart all follow templates |
| III. Agent-Orchestrated | ✅ PASS | Clean handoff to speckit.tasks for Phase 2 |
| IV. Test Optionality | ✅ PASS | No tests mandated; implementation may add unit tests for filter/sort utilities if desired |
| V. Simplicity/DRY | ✅ PASS | Single `useBoardControls` hook centralizes filter/sort/group state; label rendering reuses existing chip patterns; no premature abstractions |

## Project Structure

### Documentation (this feature)

```text
specs/029-board-hierarchy-filters/
├── plan.md              # This file
├── research.md          # Phase 0: Technical research and decisions
├── data-model.md        # Phase 1: Type changes and new interfaces
├── quickstart.md        # Phase 1: Verification commands and manual checklist
├── contracts/
│   ├── api.md           # Phase 1: Backend API contract changes
│   └── components.md    # Phase 1: Frontend component contracts
└── tasks.md             # Phase 2 output (speckit.tasks — NOT created by speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   └── board.py                    # Add Label model, labels field to BoardItem
│   ├── services/
│   │   └── github_projects/
│   │       ├── graphql.py              # Extend BOARD_GET_PROJECT_ITEMS_QUERY with labels
│   │       └── service.py              # Parse labels from GraphQL response, parent-issue filtering
│   └── api/
│       └── board.py                    # No endpoint changes needed (model changes propagate)
└── tests/

frontend/
├── src/
│   ├── components/
│   │   └── board/
│   │       ├── ProjectBoard.tsx        # Layout adjustments for group-by sections
│   │       ├── BoardColumn.tsx         # Independent vertical scroll (already has overflow-y-auto)
│   │       ├── IssueCard.tsx           # Collapsible sub-issues, label chips, agent/model on sub-tiles
│   │       ├── AgentTile.tsx           # Fix model name / tool count data-binding
│   │       ├── AgentPresetSelector.tsx # Dynamic "Custom" → saved config name label
│   │       └── BoardToolbar.tsx        # NEW: Filter/Sort/GroupBy control panels
│   ├── hooks/
│   │   ├── useAgentConfig.ts           # Fix agent metadata resolution
│   │   └── useBoardControls.ts         # NEW: Filter/Sort/GroupBy state + localStorage persistence
│   ├── pages/
│   │   └── ProjectsPage.tsx            # Integrate BoardToolbar, apply filter/sort/group transforms
│   ├── services/
│   │   └── api.ts                      # No changes (model changes propagate via types)
│   └── types/
│       └── index.ts                    # Add Label type, labels to BoardItem, SubIssue model_name field
└── tests/
```

**Structure Decision**: Web application with `backend/` + `frontend/` structure. This feature modifies existing files across both layers and adds two new frontend files (`BoardToolbar.tsx`, `useBoardControls.ts`). No new backend endpoints required — only model and query extensions.

## Complexity Tracking

No constitution violations. All design decisions favor simplicity:

| Decision | Rationale | Alternative Rejected |
|----------|-----------|---------------------|
| Client-side filter/sort/group | Board data already in memory via TanStack Query; no new API calls needed | Server-side filtering — unnecessary complexity, adds latency |
| Single `useBoardControls` hook | Centralizes all board control state; DRY principle | Separate hooks per control — more files, more state coordination |
| localStorage for persistence | Simple, synchronous, no server round-trips for preference storage | URL query params — complex serialization, pollutes URL for internal state |
| Extend existing GraphQL query for labels | Labels are a standard GitHub field; single query change | Separate REST call for labels — additional API call per issue, rate limit impact |
