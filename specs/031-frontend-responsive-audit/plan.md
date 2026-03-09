# Implementation Plan: Full Frontend Responsiveness & Mobile-Friendly Audit

**Branch**: `031-frontend-responsive-audit` | **Date**: 2026-03-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/031-frontend-responsive-audit/spec.md`

## Summary

Conduct a comprehensive audit and remediation of the entire Project Solune frontend to ensure full responsiveness from 320px mobile to 1440px+ desktop. The work introduces a centralized responsive breakpoint token system, a `useMediaQuery` hook for programmatic viewport detection, a mobile navigation drawer (hamburger menu) replacing the always-visible sidebar on small screens, touch-target sizing utilities, and systematic responsive fixes across all 9 pages, 120+ components, 16 modals, and all layout wrappers. The approach is CSS-first using Tailwind v4 utilities with the existing celestial design system, requiring zero backend changes. Existing responsive E2E tests (Playwright viewport tests) are extended with additional breakpoint coverage.

## Technical Context

**Language/Version**: TypeScript ~5.9 (frontend-only changes)
**Primary Dependencies**: React 19.2, Tailwind CSS v4, @radix-ui/react-tooltip, @radix-ui/react-slot, @dnd-kit/core, lucide-react 0.577, class-variance-authority 0.7
**Storage**: N/A — no database or localStorage schema changes; sidebar collapse state persists via existing `useSidebarState` hook
**Testing**: Vitest 4 + Testing Library + jest-axe (unit/a11y), Playwright 1.58 (E2E responsive viewport tests)
**Target Platform**: Desktop browsers (Chrome, Firefox, Safari, Edge); mobile browsers (iOS Safari, Android Chrome); tablets (portrait + landscape)
**Project Type**: Web application (frontend-only changes)
**Performance Goals**: Zero layout shift on viewport resize; no horizontal scrollbar at any breakpoint; <100ms reflow on orientation change
**Constraints**: Must use existing Tailwind v4 design system tokens; must meet WCAG 2.5.8 touch target minimum (44×44px); no new runtime dependencies (CSS/Tailwind-only approach); no backend changes
**Scale/Scope**: 9 pages, 120+ components, 16 modals, 8 layout components, ~36,000 LOC frontend; 7 standard breakpoints (320px, 375px, 390px, 768px, 1024px, 1280px, 1440px)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 5 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, 12 functional requirements (FR-001–FR-012), 8 success criteria (SC-001–SC-008), edge cases, and assumptions |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (specify → plan → tasks → implement) |
| **IV. Test Optionality** | ✅ PASS | Tests not explicitly mandated in spec; existing Playwright responsive E2E tests provide baseline regression coverage; extending viewport tests is recommended but optional |
| **V. Simplicity/DRY** | ✅ PASS | Uses existing Tailwind v4 breakpoint system; introduces a small `useMediaQuery` hook (~20 lines) for sidebar drawer behavior; no new UI library dependencies; centralized breakpoint tokens via CSS custom properties |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace back to spec FRs (FR-001–FR-012) and success criteria (SC-001–SC-008) |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/components.md, quickstart.md all follow template structure |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 task generation |
| **IV. Test Optionality** | ✅ PASS | Existing E2E tests cover basic overflow; additional viewport tests recommended but not mandated |
| **V. Simplicity/DRY** | ✅ PASS | Centralized breakpoint tokens in CSS custom properties prevent ad-hoc media query values. `useMediaQuery` hook is a minimal (~20-line) utility that replaces multiple inline `window.matchMedia` calls. The mobile drawer pattern reuses existing Sidebar component content and animations. No new libraries added — all changes use existing Tailwind v4 + Radix + Lucide stack. |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/031-frontend-responsive-audit/
├── plan.md              # This file
├── research.md          # Phase 0: Research decisions (R1–R6)
├── data-model.md        # Phase 1: Breakpoint tokens, responsive types, component patterns
├── quickstart.md        # Phase 1: Developer onboarding guide
├── contracts/
│   └── components.md    # Phase 1: Component interface contracts
├── checklists/
│   └── requirements.md  # Specification quality checklist (complete)
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── index.css                        # MODIFIED: Add responsive breakpoint CSS custom properties, touch-target utility
│   ├── hooks/
│   │   ├── useSidebarState.ts           # MODIFIED: Add auto-collapse on mobile viewport
│   │   └── useMediaQuery.ts             # NEW: Programmatic media query hook
│   ├── layout/
│   │   ├── AppLayout.tsx                # MODIFIED: Add mobile drawer overlay, responsive main padding
│   │   ├── Sidebar.tsx                  # MODIFIED: Mobile drawer behavior, overlay backdrop, swipe-to-close
│   │   ├── TopBar.tsx                   # MODIFIED: Add hamburger menu toggle for mobile, responsive padding
│   │   └── RateLimitBar.tsx             # MODIFIED: Compact mobile variant
│   ├── components/
│   │   ├── agents/
│   │   │   ├── AgentsPanel.tsx          # MODIFIED: Responsive grid, touch targets, mobile search
│   │   │   ├── AgentCard.tsx            # MODIFIED: Touch-friendly action buttons, responsive card layout
│   │   │   └── AddAgentModal.tsx        # MODIFIED: Full-screen modal on mobile, scrollable content
│   │   ├── board/
│   │   │   ├── ProjectBoard.tsx         # MODIFIED: Horizontal scroll for columns on mobile, responsive gaps
│   │   │   ├── BoardColumn.tsx          # MODIFIED: Responsive column widths
│   │   │   ├── IssueCard.tsx            # MODIFIED: Responsive card content, touch targets
│   │   │   └── IssueDetailModal.tsx     # MODIFIED: Full-screen on mobile, scrollable
│   │   ├── chat/
│   │   │   ├── ChatInterface.tsx        # MODIFIED: Responsive message layout, touch-friendly controls
│   │   │   ├── ChatPopup.tsx            # VERIFIED: Already has mobile optimization (max-sm: full-screen)
│   │   │   └── MentionInput.tsx         # MODIFIED: Touch-friendly input sizing
│   │   ├── chores/
│   │   │   ├── AddChoreModal.tsx        # MODIFIED: Full-screen on mobile
│   │   │   └── ChoreScheduleConfig.tsx  # MODIFIED: Responsive form layout
│   │   ├── pipeline/
│   │   │   ├── PipelineBoard.tsx        # MODIFIED: Responsive stage layout, horizontal scroll on mobile
│   │   │   ├── StageCard.tsx            # MODIFIED: Responsive card content
│   │   │   └── PipelineFlowGraph.tsx    # MODIFIED: Horizontal scroll container on mobile
│   │   ├── settings/                    # MODIFIED: Responsive form layouts across all settings panels
│   │   ├── tools/
│   │   │   └── ToolSelectorModal.tsx    # MODIFIED: Full-screen on mobile, scrollable tool list
│   │   ├── common/
│   │   │   └── CelestialCatalogHero.tsx # VERIFIED: Already responsive (grid-cols at lg:)
│   │   └── ui/
│   │       ├── Button.tsx               # MODIFIED: Add touch-target size variant
│   │       └── Input.tsx                # MODIFIED: Mobile-friendly input sizing (min-h-[44px])
│   ├── pages/
│   │   ├── AppPage.tsx                  # MODIFIED: Responsive dashboard layout
│   │   ├── ProjectsPage.tsx             # MODIFIED: Responsive project cards grid
│   │   ├── AgentsPipelinePage.tsx        # MODIFIED: Responsive pipeline builder
│   │   ├── AgentsPage.tsx               # MODIFIED: Responsive agents page
│   │   ├── ToolsPage.tsx               # MODIFIED: Responsive tools grid
│   │   ├── ChoresPage.tsx              # MODIFIED: Responsive chores grid
│   │   ├── SettingsPage.tsx            # MODIFIED: Responsive settings layout
│   │   ├── LoginPage.tsx               # MODIFIED: Centered mobile layout
│   │   └── NotFoundPage.tsx            # VERIFIED: Simple layout, already responsive
│   └── constants.ts                     # MODIFIED: Add BREAKPOINTS constant object
├── e2e/
│   ├── viewports.ts                     # MODIFIED: Add additional breakpoints (320, 390, 1440)
│   ├── responsive-home.spec.ts          # MODIFIED: Extend with additional viewport tests
│   ├── responsive-board.spec.ts         # MODIFIED: Extend with additional viewport tests
│   └── responsive-settings.spec.ts      # MODIFIED: Extend with additional viewport tests
└── package.json                         # NO CHANGES: No new dependencies needed
```

**Structure Decision**: Web application (frontend-only). This feature is entirely a frontend concern — no backend changes, no database changes, no API changes. All changes modify existing directories and components. One new hook (`useMediaQuery.ts`) is added to the existing hooks directory. Breakpoint tokens are added to the existing CSS custom properties in `index.css`. No new dependencies are required — all responsive behavior uses existing Tailwind v4 utilities.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| `useMediaQuery` hook (new utility) | Provides programmatic viewport detection for sidebar mobile drawer behavior. ~20 lines of code using native `window.matchMedia`. Needed because CSS-only `hidden`/`block` cannot handle the sidebar's interactive open/close state on mobile. | CSS-only approach with `hidden md:flex` (rejected: sidebar needs open/close toggle on mobile, which requires JavaScript state management based on viewport) |
| CSS custom property breakpoint tokens | Centralizes breakpoint values in `index.css` as `--bp-sm`, `--bp-md`, etc. Tailwind v4 already uses these values internally, but explicit custom properties allow JavaScript access via `getComputedStyle` and serve as the single source of truth for FR-009. | Tailwind-only breakpoints (rejected: FR-009 requires centralized, documented tokens; Tailwind breakpoints are implicit and not accessible from JavaScript) |
| Mobile sidebar drawer (not new component) | Reuses existing `Sidebar.tsx` with conditional rendering: at `<768px`, sidebar renders as a full-height overlay with backdrop, triggered by hamburger button in TopBar. This avoids duplicating navigation content in a separate `MobileNav` component. | Separate `MobileDrawer` component (rejected: duplicates all navigation items, route definitions, and sidebar content; violates DRY; harder to maintain parity between mobile and desktop nav) |
