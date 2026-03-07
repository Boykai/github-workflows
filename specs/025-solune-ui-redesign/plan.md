# Implementation Plan: Solune UI Redesign

**Branch**: `025-solune-ui-redesign` | **Date**: 2026-03-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/025-solune-ui-redesign/spec.md`

## Summary

Complete frontend UI redesign from "Agent Projects" (warm/western theme, 3-view hash routing) to "Solune" (modern purple/violet theme, 6-page React Router app with persistent sidebar layout). All existing backend APIs and React hooks are preserved; changes are frontend-only. The approach replaces hash routing with `react-router-dom` v7, swaps HSL theme tokens in-place for the new palette, lifts global components (chat, notifications) to a new `AppLayout` shell, and migrates existing panel components into dedicated pages by composition.

## Technical Context

**Language/Version**: TypeScript 5.9, React 19.2, Vite 7.3  
**Primary Dependencies**: react-router-dom v7 (new), TanStack Query 5.90, Tailwind CSS v4 (via @tailwindcss/vite), @dnd-kit, lucide-react 0.577, Radix UI  
**Storage**: localStorage (sidebar state, chat history, notification read timestamp, pre-auth redirect URL)  
**Testing**: Vitest 4 + Testing Library + happy-dom, Playwright (E2E), jest-axe (a11y)  
**Target Platform**: Desktop browsers, 1024px minimum viewport width  
**Project Type**: Web application (frontend/ + backend/)  
**Performance Goals**: Page navigation < 2s (SC-001), zero compile errors per phase (SC-002)  
**Constraints**: No new backend APIs, no animation libraries beyond CSS transitions, WCAG AA contrast in dark mode  
**Scale/Scope**: 6 pages, ~15 new/modified components, ~8 new/modified hooks

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 9 prioritized user stories, acceptance scenarios, and clarifications |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (specify → clarify → plan) |
| **IV. Test Optionality** | ✅ PASS | FR-026 mandates existing tests pass; test updates are included |
| **V. Simplicity/DRY** | ✅ PASS | Component migration by composition (R8), in-place theme token swap (R2), no new abstractions beyond what's needed |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace back to spec FRs |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/ all follow template structure |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 |
| **IV. Test Optionality** | ✅ PASS | FR-026 requires test fixture updates; no additional tests mandated |
| **V. Simplicity/DRY** | ✅ PASS | Existing components reused (not duplicated) in new pages. No unnecessary abstractions. 3 new hooks are minimal (sidebar state, notifications, recent issues). |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/025-solune-ui-redesign/
├── plan.md              # This file
├── research.md          # Phase 0: 10 research items (R1–R10)
├── data-model.md        # Phase 1: Types, hooks, component props, state transitions
├── quickstart.md        # Phase 1: Developer onboarding guide
├── contracts/
│   ├── routes.md        # Phase 1: Route contract, nav items, backend API inventory
│   └── components.md    # Phase 1: Component interface contracts
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── index.html                        # Title → "Solune", font → Plus Jakarta Sans
├── src/
│   ├── App.tsx                       # BrowserRouter + Routes + Route config (rewritten)
│   ├── index.css                     # Theme tokens (rewritten: purple/violet palette)
│   ├── constants.ts                  # NAV_ROUTES, PRIORITY_COLORS added
│   ├── types/index.ts                # NavRoute, SidebarState, Notification types added
│   ├── layout/                       # NEW directory
│   │   ├── AppLayout.tsx             # Shell: Sidebar + TopBar + Outlet + ChatPopup
│   │   ├── Sidebar.tsx               # Collapsible nav with brand, links, recent, project
│   │   ├── TopBar.tsx                # Breadcrumb + notifications + theme + avatar
│   │   ├── Breadcrumb.tsx            # Route-derived breadcrumbs
│   │   ├── ProjectSelector.tsx       # Project switcher
│   │   └── NotificationBell.tsx      # Notification dropdown
│   ├── pages/
│   │   ├── AppPage.tsx               # NEW: Home / welcome
│   │   ├── ProjectsPage.tsx          # NEW: Board (migrates from ProjectBoardPage)
│   │   ├── AgentsPipelinePage.tsx     # NEW: Pipeline view
│   │   ├── AgentsPage.tsx            # NEW: Agent catalog
│   │   ├── ChoresPage.tsx            # NEW: Chore management
│   │   ├── SettingsPage.tsx          # EXISTING: Restyled
│   │   ├── LoginPage.tsx             # NEW: Auth gate
│   │   └── NotFoundPage.tsx          # NEW: 404
│   ├── hooks/
│   │   ├── useSidebarState.ts        # NEW: Sidebar collapse persistence
│   │   ├── useNotifications.ts       # NEW: Aggregate notifications
│   │   └── useRecentParentIssues.ts  # NEW: Derive recent issues from board
│   ├── components/
│   │   ├── board/
│   │   │   ├── IssueCard.tsx         # MODIFIED: Priority badges, description, labels
│   │   │   ├── BoardColumn.tsx       # MODIFIED: "+" button scaffolding
│   │   │   └── ProjectBoard.tsx      # MODIFIED: "Add column" scaffolding
│   │   ├── agents/                   # EXISTING: Reused in AgentsPage
│   │   ├── chores/                   # EXISTING: Reused in ChoresPage
│   │   ├── chat/ChatPopup.tsx        # EXISTING: Lifted to AppLayout
│   │   └── CowboyAvatar.tsx          # DELETED
│   └── test/                         # Test fixtures updated
└── tests/                            # E2E tests updated for new routes

backend/                              # NO CHANGES
```

**Structure Decision**: Web application (Option 2). The repo already has `frontend/` and `backend/` directories. All changes are within `frontend/`. A new `frontend/src/layout/` directory is added for the layout shell components. New pages go into the existing `frontend/src/pages/` directory. Existing components under `frontend/src/components/` are modified in-place or reused by import.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

*Table intentionally left empty — all design decisions favor simplicity per Principle V.*
