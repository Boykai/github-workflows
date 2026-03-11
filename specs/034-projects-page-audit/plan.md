# Implementation Plan: Audit & Polish Projects Page for Visual Cohesion and UX Quality

**Branch**: `034-projects-page-audit` | **Date**: 2026-03-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/034-projects-page-audit/spec.md`

## Summary

Conduct a comprehensive audit of the Projects page (`frontend/src/pages/ProjectsPage.tsx`) and all its child components (board, toolbar, modals, panels, selectors, loaders, empty states, error states) within Project Solune. The primary goal is to ensure visual consistency with the Celestial design system, eliminate rendering bugs and broken states, enforce WCAG AA accessibility compliance, validate responsive behavior across desktop/tablet/mobile breakpoints, verify all interactive elements function correctly with proper feedback, and ensure code quality follows established project conventions. No backend API changes are required — this is a frontend-only audit-and-refactor effort.

## Technical Context

**Language/Version**: TypeScript 5.x with React 19.2  
**Primary Dependencies**: React 19, TanStack React Query 5.90, Tailwind CSS v4 (via `@tailwindcss/vite`), Radix UI (Slot, Tooltip), Lucide React icons, class-variance-authority, tailwind-merge, react-router-dom 7.13, react-markdown 10.1, @dnd-kit (drag-and-drop)  
**Storage**: N/A (frontend-only; backend uses SQLite with FastAPI)  
**Testing**: Vitest (unit, happy-dom), Playwright (E2E), Testing Library (React), jest-axe (accessibility)  
**Target Platform**: Modern browsers (desktop, tablet, mobile web)  
**Project Type**: Web application (frontend + backend)  
**Performance Goals**: Page interactive within 3 seconds; user actions reflected in under 1 second perceived response time; no jank with 100+ board items  
**Constraints**: WCAG AA minimum (4.5:1 contrast normal text, 3:1 large text/UI); 44×44px minimum touch targets on mobile; no hardcoded colors — all must reference design tokens  
**Scale/Scope**: Single page audit affecting ~20 frontend components, 6 custom hooks, 1 page component; no new features, purely audit and refinement

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Evaluation

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | `spec.md` exists with 6 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, and clear scope boundaries |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | This plan is produced by the `speckit.plan` agent with clear inputs/outputs |
| **IV. Test Optionality** | ✅ PASS | Tests are not mandated by spec; existing tests (IssueCard, BoardColumn, IssueDetailModal, ProjectIssueLaunchPanel, etc.) will be verified to pass but no new test creation is required unless accessibility scanning reveals gaps |
| **V. Simplicity and DRY** | ✅ PASS | Audit refactors toward simplicity; no new abstractions introduced. All changes simplify or consolidate existing code |

### Post-Phase 1 Re-Evaluation

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | Data model and contracts align with spec requirements; all 13 functional requirements traced to audit points |
| **II. Template-Driven** | ✅ PASS | All generated artifacts (research.md, data-model.md, contracts/, quickstart.md) follow prescribed templates |
| **III. Agent-Orchestrated** | ✅ PASS | Clear handoff to `speckit.tasks` after this phase |
| **IV. Test Optionality** | ✅ PASS | No new test infrastructure added; existing 7 board component test files and 6 hook test files maintained |
| **V. Simplicity and DRY** | ✅ PASS | No new abstractions; refactors consolidate duplicate patterns and align with design tokens |

## Project Structure

### Documentation (this feature)

```text
specs/034-projects-page-audit/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output — design system analysis, accessibility patterns, performance best practices
├── data-model.md        # Phase 1 output — entity model for Projects page components
├── quickstart.md        # Phase 1 output — developer guide for running the audit
├── contracts/           # Phase 1 output — component interface contracts
│   └── component-contracts.yaml
├── checklists/          # Quality checklist from spec phase
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── pages/
│   │   └── ProjectsPage.tsx                  # Main page component (~749 lines) — PRIMARY AUDIT TARGET
│   ├── components/
│   │   ├── board/
│   │   │   ├── ProjectBoard.tsx              # Grid container for columns
│   │   │   ├── BoardColumn.tsx               # Status column with header + items
│   │   │   ├── IssueCard.tsx                 # Individual issue card (~306 lines)
│   │   │   ├── IssueDetailModal.tsx          # Full issue detail overlay (~310 lines)
│   │   │   ├── BoardToolbar.tsx              # Filter/sort/group controls (~326 lines)
│   │   │   ├── RefreshButton.tsx             # Manual refresh with spinner
│   │   │   ├── BlockingIssuePill.tsx         # Oldest blocking issue display
│   │   │   ├── BlockingChainPanel.tsx        # Collapsible blocking queue
│   │   │   ├── ProjectIssueLaunchPanel.tsx   # Issue creation + pipeline launch (~491 lines)
│   │   │   └── colorUtils.ts                # Status color mapping
│   │   ├── common/
│   │   │   ├── CelestialLoader.tsx           # Loading spinner
│   │   │   ├── CelestialCatalogHero.tsx      # Page hero section
│   │   │   └── ProjectSelectionEmptyState.tsx # Empty state when no project
│   │   └── ui/
│   │       ├── button.tsx                    # Shared button (CVA variants)
│   │       ├── card.tsx                      # Shared card
│   │       ├── input.tsx                     # Shared input
│   │       ├── tooltip.tsx                   # Radix tooltip wrapper
│   │       └── confirmation-dialog.tsx       # Confirmation modal
│   ├── hooks/
│   │   ├── useProjectBoard.ts               # Board data fetching + state
│   │   ├── useBoardControls.ts              # Filter/sort/group with localStorage
│   │   ├── useBlockingQueue.ts              # Blocking queue entries
│   │   ├── useBoardRefresh.ts               # Manual/auto refresh + rate limits
│   │   ├── useProjects.ts                   # Project listing + selection
│   │   └── useRealTimeSync.ts               # WebSocket sync + polling fallback
│   ├── layout/
│   │   └── ProjectSelector.tsx              # Project dropdown selector
│   ├── services/
│   │   └── api.ts                           # API client (pipelinesApi, projectsApi, boardApi)
│   ├── types/
│   │   └── index.ts                         # BoardItem, BoardColumn, BoardDataResponse, etc.
│   ├── utils/
│   │   ├── formatTime.ts                    # formatTimeAgo, formatTimeUntil
│   │   ├── rateLimit.ts                     # extractRateLimitInfo, isRateLimitApiError
│   │   └── formatAgentName.ts               # Agent display name formatting
│   ├── lib/
│   │   └── utils.ts                         # cn() — clsx + tailwind-merge
│   └── index.css                            # Celestial design system tokens + custom classes
├── e2e/
│   ├── board-navigation.spec.ts             # Board navigation E2E tests
│   └── responsive-board.spec.ts             # Responsive design E2E tests
└── package.json                             # React 19, Vitest, Playwright, Tailwind v4
```

**Structure Decision**: Web application (frontend-only audit). All changes target `frontend/src/` — primarily `pages/ProjectsPage.tsx` and `components/board/`. No backend modifications are needed. The existing project structure is well-established and no structural reorganization is planned.

## Complexity Tracking

> No violations identified. All changes follow simplicity principles — refactoring toward design-token consistency, removing hardcoded values, and standardizing existing patterns. No new abstractions, libraries, or architectural changes are introduced.
