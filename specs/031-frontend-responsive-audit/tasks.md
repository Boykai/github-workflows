# Tasks: Full Frontend Responsiveness & Mobile-Friendly Audit

**Input**: Design documents from `/specs/031-frontend-responsive-audit/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/components.md ✅, quickstart.md ✅

**Tests**: NOT explicitly requested in the specification. Existing Playwright E2E responsive tests provide baseline regression coverage. E2E viewport test extensions are included in the Polish phase as optional improvements.

**Organization**: Tasks are grouped by user story (US1–US5) to enable independent implementation and testing of each responsive scope. US1 and US2 are both P1 priority; US3 and US4 are P2; US5 is P3.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- **Frontend tests**: Co-located `.test.{ts,tsx}` files or `frontend/e2e/` for Playwright
- **No backend changes**: This feature is entirely frontend

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish responsive design tokens, utility hooks, and CSS utility classes that all subsequent phases depend on. These are the centralized building blocks per FR-009.

- [x] T001 Add responsive breakpoint CSS custom properties (`--bp-xs` through `--bp-2xl`) to the `@theme` block in `frontend/src/index.css`
- [x] T002 [P] Add `.touch-target` utility class (`min-height: 44px; min-width: 44px`) to `frontend/src/index.css` for WCAG 2.5.8 touch target compliance (FR-002)
- [x] T003 [P] Add `BREAKPOINTS` constant object (`xs: 320, sm: 640, md: 768, lg: 1024, xl: 1280, '2xl': 1440`) to `frontend/src/constants.ts`
- [x] T004 Create `useMediaQuery` hook with `useIsMobile()` convenience function in `frontend/src/hooks/useMediaQuery.ts` — uses native `window.matchMedia`, SSR-safe, subscribes to viewport changes

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core component modifications that MUST be complete before any user story can be implemented. These modify shared UI primitives and layout state management.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T005 Add `touch` size variant (`min-h-[44px] min-w-[44px] px-4 py-2`) to the Button CVA variants in `frontend/src/components/ui/Button.tsx`
- [x] T006 [P] Add `max-sm:min-h-[44px]` to base input classes in `frontend/src/components/ui/Input.tsx` for mobile touch-friendly input height
- [x] T007 Extend `useSidebarState` hook with mobile drawer state (`isMobileOpen`, `openMobile`, `closeMobile`) and auto-close on route change via `useLocation` in `frontend/src/hooks/useSidebarState.ts`

**Checkpoint**: Foundation ready — responsive tokens, utility hook, UI primitives, and sidebar state are in place. User story implementation can now begin.

---

## Phase 3: User Story 1 — Mobile User Browses and Navigates the App (Priority: P1) 🎯 MVP

**Goal**: A user on a mobile phone (320px–390px) can access the full app via a hamburger menu / slide-out drawer, browse all pages without horizontal scrolling, and interact with all controls via touch. The sidebar is hidden by default on mobile, replaced by a drawer overlay triggered from the TopBar.

**Independent Test**: Load every page at 320px, 375px, and 390px viewport widths. Verify: (1) no horizontal scrollbar on any page, (2) hamburger icon visible and opens navigation drawer, (3) all navigation items accessible in drawer, (4) drawer closes on backdrop tap and on route change, (5) all content visible within viewport width.

### Layout Components (Mobile Navigation — FR-003)

- [x] T008 [US1] Add hamburger menu button (`md:hidden`, `touch-target`, lucide `Menu` icon) to the left of TopBar, wired to `onMenuToggle` prop, with responsive padding (`px-3 md:px-6`) and breadcrumb truncation on mobile in `frontend/src/layout/TopBar.tsx`
- [x] T009 [US1] Implement dual rendering mode in `frontend/src/layout/Sidebar.tsx` — desktop: existing inline sidebar (`hidden md:flex`); mobile: fixed overlay drawer (`fixed inset-y-0 left-0 z-40 w-72`) with slide animation (`transition-transform duration-300`), backdrop, close button (X icon, 44×44px), and `aria-label="Main navigation"` accessibility attributes
- [x] T010 [US1] Wire mobile drawer state into `frontend/src/layout/AppLayout.tsx` — use `useIsMobile()` hook to conditionally render Sidebar inline (desktop) or as overlay drawer (mobile), add backdrop overlay (`fixed inset-0 z-30 bg-black/50`), pass `openMobile`/`closeMobile` to TopBar and Sidebar, adjust main content padding (`px-2 md:px-4`)

### Page Layouts — Mobile Responsive (FR-001, FR-004)

- [x] T011 [P] [US1] Make `frontend/src/pages/AppPage.tsx` responsive at mobile breakpoints — reduce padding (`px-2 md:px-4 lg:px-6`), scale heading typography (`text-2xl md:text-3xl`), ensure card grids use `grid-cols-1` on mobile
- [x] T012 [P] [US1] Make `frontend/src/pages/ProjectsPage.tsx` responsive at mobile breakpoints — responsive padding, ensure project card grid uses `grid-cols-1 md:grid-cols-2`, no fixed pixel widths
- [x] T013 [P] [US1] Make `frontend/src/pages/AgentsPage.tsx` responsive at mobile breakpoints — verify existing `md:grid-cols-2 xl:grid-cols-3` grid, add responsive padding, ensure touch targets on agent card actions
- [x] T014 [P] [US1] Make `frontend/src/pages/AgentsPipelinePage.tsx` responsive at mobile breakpoints — responsive padding, pipeline content adapts to narrow viewport without horizontal overflow
- [x] T015 [P] [US1] Make `frontend/src/pages/ToolsPage.tsx` responsive at mobile breakpoints — responsive grid (`grid-cols-1 md:grid-cols-2 xl:grid-cols-3`), responsive padding
- [x] T016 [P] [US1] Make `frontend/src/pages/ChoresPage.tsx` responsive at mobile breakpoints — responsive grid, responsive padding, touch-friendly action buttons
- [x] T017 [P] [US1] Make `frontend/src/pages/SettingsPage.tsx` responsive at mobile breakpoints — responsive tab navigation (horizontal scrollable pills on mobile, vertical sidebar on desktop), form layout stacking
- [x] T018 [P] [US1] Make `frontend/src/pages/LoginPage.tsx` responsive at mobile breakpoints — centered mobile layout, responsive padding, ensure login form inputs are full-width on mobile
- [x] T019 [P] [US1] Verify `frontend/src/pages/NotFoundPage.tsx` renders correctly at 320px — simple layout, confirm no horizontal overflow

### Feature Components — Mobile Responsive

- [x] T020 [P] [US1] Make `frontend/src/components/agents/AgentsPanel.tsx` responsive — mobile search bar full-width, responsive grid, touch targets on filter/sort controls
- [x] T021 [P] [US1] Make `frontend/src/components/agents/AgentCard.tsx` responsive — touch-friendly action buttons (44×44px), responsive card layout, text truncation for long agent names
- [x] T022 [P] [US1] Make `frontend/src/layout/RateLimitBar.tsx` responsive — verify compact mobile variant or hidden on mobile (`hidden md:flex`), no overflow on small screens

**Checkpoint**: At this point, User Story 1 should be fully functional and testable. Every page loads without horizontal scrollbar at 320px, 375px, 390px. Mobile navigation drawer works. All content accessible.

---

## Phase 4: User Story 2 — Tablet User Views Data-Heavy Content (Priority: P1)

**Goal**: A user on a tablet (768px) in portrait and landscape can view agent pipelines, chat panels, kanban boards, and data tables with content reflowing gracefully. No clipping, no text overflow, no z-index collisions. Sticky/fixed elements don't obscure content.

**Independent Test**: Load agent pipeline views, chat panels, project boards, and data tables at 768px (portrait) and 1024px (landscape). Verify: (1) pipeline stages reflow or scroll horizontally without clipping, (2) chat messages fully readable with touch-friendly input, (3) kanban board columns accessible via horizontal scroll or reflow, (4) sticky header doesn't obscure first visible content item.

### Board Components — Horizontal Scroll (FR-005)

- [x] T023 [US2] Implement horizontal scroll container for kanban columns in `frontend/src/components/board/ProjectBoard.tsx` — `overflow-x-auto snap-x snap-mandatory md:flex-wrap md:overflow-visible`, column width `w-[85vw] shrink-0 snap-center md:w-auto md:shrink`
- [x] T024 [P] [US2] Make `frontend/src/components/board/BoardColumn.tsx` responsive — responsive column widths, ensure content doesn't overflow column boundaries on mobile
- [x] T025 [P] [US2] Make `frontend/src/components/board/IssueCard.tsx` responsive — responsive card content layout, touch targets on card actions, text truncation for long issue titles
- [x] T026 [P] [US2] Make `frontend/src/components/board/IssueDetailModal.tsx` responsive — full-screen on mobile (handled in US5 but card content inside must reflow at 768px), scrollable content area

### Pipeline Components — Horizontal Scroll (FR-005)

- [x] T027 [US2] Implement horizontal scroll for pipeline stages in `frontend/src/components/pipeline/PipelineBoard.tsx` — `overflow-x-auto md:overflow-visible` with `min-w-max md:min-w-0` inner container
- [x] T028 [P] [US2] Make `frontend/src/components/pipeline/StageCard.tsx` responsive — responsive card content, touch targets on stage actions
- [x] T029 [P] [US2] Make `frontend/src/components/pipeline/PipelineFlowGraph.tsx` responsive — horizontal scroll container (`overflow-x-auto`), `touch-action: pan-x pan-y` to prevent pinch-to-zoom conflicts

### Chat Components — Tablet Reflow (FR-005)

- [x] T030 [P] [US2] Audit and fix `frontend/src/components/chat/ChatInterface.tsx` for tablet responsiveness — verify message layout, touch-friendly controls, no z-index collisions with other UI layers
- [x] T031 [P] [US2] Verify `frontend/src/components/chat/ChatPopup.tsx` mobile optimization — confirm existing `max-sm:` full-screen behavior works correctly at 768px, no content clipping
- [x] T032 [P] [US2] Make `frontend/src/components/chat/MentionInput.tsx` touch-friendly — ensure input sizing meets 44px minimum height on mobile, responsive placeholder text

### Fixed/Sticky Element Audit (FR-006)

- [x] T033 [US2] Audit all fixed/sticky elements (TopBar header, footers, toolbars) across all pages at 768px and 1024px — ensure they don't obscure primary content, add sufficient padding/offset for sticky header clearance in `frontend/src/layout/TopBar.tsx` and `frontend/src/layout/AppLayout.tsx`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. All data-heavy views reflow correctly on tablet. Pipeline and board horizontal scroll works.

---

## Phase 5: User Story 3 — Desktop User Experiences Consistent Visual Language (Priority: P2)

**Goal**: A user on a large desktop (1280px–1440px+) sees polished, consistent layouts with fluid responsive widths, proportionally scaled typography and spacing, and consistent visual language across breakpoints.

**Independent Test**: Load all pages at 1280px and 1440px. Verify: (1) all grids, cards, and lists use fluid widths that fill available space, (2) typography sizes and spacing are proportionally scaled, (3) text readable without zooming, (4) visual consistency with mobile/tablet experiences (no degraded hierarchy).

### Typography & Spacing Audit (FR-010)

- [x] T034 [P] [US3] Audit and fix heading typography scaling across all pages — ensure responsive modifiers (e.g., `text-2xl md:text-3xl lg:text-4xl`) are applied consistently in `frontend/src/pages/AppPage.tsx`, `ProjectsPage.tsx`, `AgentsPage.tsx`, `AgentsPipelinePage.tsx`, `ToolsPage.tsx`, `ChoresPage.tsx`, `SettingsPage.tsx`
- [x] T035 [P] [US3] Audit body text minimum sizes — ensure `text-base` (16px) minimum on mobile viewports across all components, bump critical `text-sm` instances to `max-sm:text-base` where readability is impacted
- [x] T036 [P] [US3] Audit and fix spacing consistency — ensure horizontal padding scales (`px-2 md:px-4 lg:px-6`), vertical gaps scale (`gap-3 md:gap-4 lg:gap-6`) across all page layouts

### Fluid Layout Verification (FR-004)

- [x] T037 [P] [US3] Audit all grid and card components for fixed pixel widths — replace any hard-coded `w-[NNNpx]` values with fluid equivalents (`w-full`, `max-w-*`, percentage-based) across `frontend/src/components/agents/`, `frontend/src/components/board/`, `frontend/src/components/pipeline/`
- [x] T038 [P] [US3] Verify `frontend/src/components/common/CelestialCatalogHero.tsx` responsive behavior at 1280px and 1440px — confirm existing responsive grid works correctly at large breakpoints

**Checkpoint**: All pages render with consistent, proportional visual language at desktop breakpoints. No fixed widths break fluid layouts.

---

## Phase 6: User Story 4 — User Interacts with Forms and Controls on Mobile (Priority: P2)

**Goal**: A user on a mobile device can fill out forms, select dropdowns, and interact with all input controls via touch. Every form control is operable via touch, large enough to tap accurately (44×44px minimum), and does not require precise pointer input.

**Independent Test**: Navigate to every form/input screen on a 375px mobile viewport. Complete each form field using touch-only interaction. Verify: (1) all inputs activate correctly on tap, (2) dropdowns fully visible and scrollable, (3) each option meets 44×44px touch target, (4) validation messages display within viewport.

### Touch Target Remediation (FR-002)

- [x] T039 [P] [US4] Audit and fix icon buttons across all components — ensure padding creates 44×44px hit area (e.g., `p-2.5` for 24px icons = 44px total) in `frontend/src/components/agents/`, `frontend/src/components/board/`, `frontend/src/components/pipeline/`, `frontend/src/components/chat/`, `frontend/src/components/chores/`, `frontend/src/components/tools/`
- [x] T040 [P] [US4] Audit and fix menu items across navigation and dropdowns — ensure `min-h-[44px]` on mobile for all clickable menu items in `frontend/src/layout/Sidebar.tsx` nav items
- [x] T041 [P] [US4] Audit and fix link touch targets — ensure all text links have sufficient tap area via padding or `touch-target` class across `frontend/src/components/` and `frontend/src/pages/`

### Form Input Responsiveness (FR-007)

- [x] T042 [P] [US4] Make `frontend/src/components/chores/ChoreScheduleConfig.tsx` responsive — stack form fields vertically on mobile, ensure all inputs and dropdowns are touch-friendly
- [x] T043 [P] [US4] Audit and fix all settings panels for responsive form layout in `frontend/src/components/settings/` — ensure form inputs stack on mobile, labels above inputs, full-width controls
- [x] T044 [P] [US4] Verify chat input controls are touch-friendly — audit `frontend/src/components/chat/ChatInterface.tsx` send button, file upload button, and toolbar controls for 44×44px minimum tap area

### Hover-to-Touch Fallbacks (FR-011)

- [x] T045 [US4] Audit all hover-dependent interactions across `frontend/src/components/` — ensure every hover-triggered tooltip, dropdown, or action has a touch-equivalent fallback (tap, long-press, or tap-to-toggle) for touch-only devices

**Checkpoint**: All form inputs and interactive controls are fully operable via touch on mobile. All touch targets meet 44×44px minimum.

---

## Phase 7: User Story 5 — Modals, Drawers, and Tooltips Adapt to Mobile (Priority: P3)

**Goal**: A user on mobile or tablet can trigger modals, drawers, tooltips, and overlay elements that adapt to the smaller viewport. Modals go full-screen on mobile (<640px). Tooltips convert to tap-friendly. All overlays are dismissible via touch.

**Independent Test**: Trigger every modal, drawer, and tooltip at 375px and 768px viewports. Verify: (1) modals fill viewport on mobile, scrollable content, visible close button, (2) tooltips display on tap without clipping, (3) drawers overlay with backdrop, no horizontal overflow.

### Modal Full-Screen Mobile (FR-008)

- [x] T046 [P] [US5] Apply full-screen mobile pattern to `frontend/src/components/agents/AddAgentModal.tsx` — `max-sm:max-w-none max-sm:h-full max-sm:rounded-none max-sm:m-0`, scrollable content, 44×44px close button
- [x] T047 [P] [US5] Apply full-screen mobile pattern to `frontend/src/components/board/IssueDetailModal.tsx` — full-screen on mobile, scrollable issue content, touch-friendly close button
- [x] T048 [P] [US5] Apply full-screen mobile pattern to `frontend/src/components/tools/ToolSelectorModal.tsx` — full-screen on mobile, scrollable tool list, touch-friendly controls
- [x] T049 [P] [US5] Apply full-screen mobile pattern to `frontend/src/components/chores/AddChoreModal.tsx` — full-screen on mobile, scrollable form, touch-friendly close button
- [x] T050 [P] [US5] Apply full-screen mobile pattern to remaining modals — AgentIconPickerModal, ConfirmChoreModal, UploadMcpModal, EditRepoMcpModal, CleanUpConfirmModal, BulkModelUpdateDialog, UnsavedChangesDialog, ConfirmationDialog — each gets `max-sm:` full-screen overrides and scrollable content

### Tooltip Touch Adaptation (FR-011)

- [x] T051 [US5] Audit and fix tooltip components across `frontend/src/components/` — convert hover-only tooltips to tap-to-show on touch devices using existing `@radix-ui/react-tooltip` touch behavior or adding `onTouchStart` handlers

### Orientation Change Handling (FR-012)

- [x] T052 [US5] Verify orientation change behavior — test that open modals, drawers, and tooltips re-adapt layout correctly when device rotates from portrait to landscape (and vice versa) without visual glitches, content loss, or scroll position jumps

**Checkpoint**: All user stories (US1–US5) should now be independently functional. All modals, drawers, and tooltips adapt correctly on mobile and tablet.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final verification, optional E2E test extensions, and cross-cutting quality improvements that span multiple user stories.

### E2E Test Extensions (Optional — existing tests provide baseline)

- [x] T053 [P] Add additional viewport definitions (`mobileSmall: 320×568`, `mobileLarge: 390×844`, `desktopLarge: 1440×900`) to `frontend/e2e/viewports.ts`
- [x] T054 [P] Extend responsive home page tests with new viewport breakpoints in `frontend/e2e/responsive-home.spec.ts`
- [x] T055 [P] Extend responsive board tests with new viewport breakpoints in `frontend/e2e/responsive-board.spec.ts`
- [x] T056 [P] Extend responsive settings tests with new viewport breakpoints in `frontend/e2e/responsive-settings.spec.ts`

### Cross-Cutting Quality

- [x] T057 Run `npm run type-check` in `frontend/` — verify zero TypeScript errors after all responsive changes
- [x] T058 [P] Run `npm run lint` in `frontend/` — verify zero ESLint errors after all responsive changes
- [x] T059 [P] Run `npm run build` in `frontend/` — verify successful production build
- [x] T060 Run `npm run test` in `frontend/` — verify all existing Vitest tests pass with responsive changes
- [x] T061 Perform full breakpoint sweep — load every page at 320px, 375px, 390px, 768px, 1024px, 1280px, 1440px and verify no horizontal scrollbar (`document.documentElement.scrollWidth <= window.innerWidth`)
- [x] T062 Verify dark mode compatibility — confirm all responsive changes work correctly in both light and dark themes via ThemeProvider
- [x] T063 Run quickstart.md validation — follow the verification checklist in `specs/031-frontend-responsive-audit/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion (needs breakpoint tokens and useMediaQuery hook) — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 — can start once foundational is complete
- **User Story 2 (Phase 4)**: Depends on Phase 2 — can start in parallel with US1 (different files)
- **User Story 3 (Phase 5)**: Depends on Phase 2 — can start after US1/US2 (audits typography/spacing set in US1/US2)
- **User Story 4 (Phase 6)**: Depends on Phase 2 — can start after US1 (touch targets apply to components modified in US1)
- **User Story 5 (Phase 7)**: Depends on Phase 2 — can start in parallel with US3/US4 (modals are separate files)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Core mobile navigation + page layouts — no dependencies on other stories. **MVP scope.**
- **US2 (P1)**: Data-heavy component reflow — independent of US1 (different components). Can run in parallel.
- **US3 (P2)**: Desktop visual consistency — should run after US1/US2 to audit typography changes made in those phases.
- **US4 (P2)**: Touch targets and forms — should run after US1 (builds on page layout changes). Can run in parallel with US3/US5.
- **US5 (P3)**: Modal/tooltip adaptation — fully independent file changes. Can run in parallel with US3/US4.

### Within Each User Story

- Layout changes before page-specific changes
- Component infrastructure (shared patterns) before individual component fixes
- Core implementations before polish/audit passes

### Parallel Opportunities

**Phase 1** (all [P] tasks):
```
T001 (index.css breakpoints)  ──┐
T002 (touch-target utility)    ──┼── All in parallel (different locations in same file or different files)
T003 (constants.ts)            ──┤
T004 (useMediaQuery.ts)        ──┘
```

**Phase 2** (foundational):
```
T005 (Button.tsx)              ──┐
T006 (Input.tsx)               ──┼── T005 and T006 in parallel (different files)
T007 (useSidebarState.ts)      ──┘   T007 sequential (depends on T004)
```

**Phase 3** (US1 — page layouts after navigation):
```
T008 (TopBar.tsx)    ──→ T009 (Sidebar.tsx) ──→ T010 (AppLayout.tsx)  [sequential: wiring]
T011–T019 (pages)    ──── All in parallel after T010 [P] (different files)
T020–T022 (components) ── All in parallel [P] (different files)
```

**Phase 4** (US2 — all component groups in parallel):
```
T023 (ProjectBoard)  ──→ T024–T026 [P]  ┐
T027 (PipelineBoard) ──→ T028–T029 [P]  ├── Three groups in parallel
T030–T032 (Chat)     ──── All [P]       ┘
T033 (sticky audit)  ──── After above
```

**Phase 7** (US5 — all modal fixes in parallel):
```
T046–T050 ──── All [P] (different modal files)
T051 (tooltips) ──── After modals
T052 (orientation) ──── After all
```

---

## Parallel Example: User Story 1

```bash
# After Phase 2 is complete, launch navigation wiring sequentially:
Task T008: "Add hamburger menu button to TopBar.tsx"
Task T009: "Implement dual rendering mode in Sidebar.tsx"
Task T010: "Wire mobile drawer state into AppLayout.tsx"

# Then launch ALL page responsive fixes in parallel:
Task T011: "Make AppPage.tsx responsive at mobile breakpoints"
Task T012: "Make ProjectsPage.tsx responsive at mobile breakpoints"
Task T013: "Make AgentsPage.tsx responsive at mobile breakpoints"
Task T014: "Make AgentsPipelinePage.tsx responsive at mobile breakpoints"
Task T015: "Make ToolsPage.tsx responsive at mobile breakpoints"
Task T016: "Make ChoresPage.tsx responsive at mobile breakpoints"
Task T017: "Make SettingsPage.tsx responsive at mobile breakpoints"
Task T018: "Make LoginPage.tsx responsive at mobile breakpoints"
Task T019: "Verify NotFoundPage.tsx at 320px"

# And launch component fixes in parallel:
Task T020: "Make AgentsPanel.tsx responsive"
Task T021: "Make AgentCard.tsx responsive"
Task T022: "Make RateLimitBar.tsx responsive"
```

---

## Parallel Example: User Story 2

```bash
# Board, pipeline, and chat components can all be worked on in parallel:
# Group A — Board:
Task T023: "Implement horizontal scroll in ProjectBoard.tsx"
Task T024: "Make BoardColumn.tsx responsive"
Task T025: "Make IssueCard.tsx responsive"

# Group B — Pipeline:
Task T027: "Implement horizontal scroll in PipelineBoard.tsx"
Task T028: "Make StageCard.tsx responsive"
Task T029: "Make PipelineFlowGraph.tsx responsive"

# Group C — Chat:
Task T030: "Audit ChatInterface.tsx for tablet responsiveness"
Task T031: "Verify ChatPopup.tsx mobile optimization"
Task T032: "Make MentionInput.tsx touch-friendly"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (breakpoint tokens, useMediaQuery, touch-target utility)
2. Complete Phase 2: Foundational (Button touch variant, Input mobile sizing, sidebar mobile state)
3. Complete Phase 3: User Story 1 — Mobile navigation + all page layouts
4. **STOP and VALIDATE**: Test every page at 320px, 375px, 390px — no horizontal scrollbar, drawer navigation works
5. Deploy/demo if ready — this is the highest-value increment

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add **US1** (mobile navigation + page layouts) → Test at mobile breakpoints → **MVP!**
3. Add **US2** (data-heavy content reflow) → Test at tablet breakpoints → Demo
4. Add **US3** (desktop visual consistency) → Test at desktop breakpoints → Demo
5. Add **US4** (forms and touch targets) → Test all interactive controls on mobile → Demo
6. Add **US5** (modals, tooltips) → Test all overlays on mobile/tablet → Demo
7. Complete Polish → Full breakpoint sweep → **Ship!**
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (mobile nav + pages) — P1
   - Developer B: User Story 2 (data-heavy reflow) — P1
3. After P1 stories complete:
   - Developer A: User Story 3 (desktop consistency) — P2
   - Developer B: User Story 4 (touch targets + forms) — P2
   - Developer C: User Story 5 (modals + tooltips) — P3
4. All developers: Polish phase together

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 63 |
| **Phase 1 — Setup** | 4 tasks |
| **Phase 2 — Foundational** | 3 tasks |
| **Phase 3 — US1 (P1, MVP)** | 15 tasks |
| **Phase 4 — US2 (P1)** | 11 tasks |
| **Phase 5 — US3 (P2)** | 5 tasks |
| **Phase 6 — US4 (P2)** | 7 tasks |
| **Phase 7 — US5 (P3)** | 7 tasks |
| **Phase 8 — Polish** | 11 tasks |
| **Parallel opportunities** | 43 tasks marked [P] |
| **Suggested MVP scope** | Phase 1 + Phase 2 + Phase 3 (US1 only = 22 tasks) |
| **New files** | 1 (`frontend/src/hooks/useMediaQuery.ts`) |
| **Modified files** | ~40 (9 pages, 8 layout, 20+ components, 3 E2E tests) |

### Independent Test Criteria per Story

| Story | Test Method |
|-------|-------------|
| US1 | Load every page at 320px, 375px, 390px — no horizontal scroll, drawer nav works |
| US2 | Load pipelines, boards, chat at 768px/1024px — content reflows, no clipping |
| US3 | Load all pages at 1280px, 1440px — fluid widths, proportional typography |
| US4 | Complete all forms on 375px via touch-only — all controls operable |
| US5 | Trigger all modals/tooltips at 375px, 768px — full-screen, dismissible, no clipping |

### Format Validation

✅ ALL 63 tasks follow the required checklist format: `- [x] [TaskID] [P?] [Story?] Description with file path`
✅ Setup phase (Phase 1): NO story labels
✅ Foundational phase (Phase 2): NO story labels
✅ User Story phases (Phase 3–7): ALL tasks have story labels ([US1]–[US5])
✅ Polish phase (Phase 8): NO story labels
✅ All tasks include specific file paths
✅ [P] markers only on tasks with different files and no dependencies on incomplete tasks

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- No backend changes required — this is entirely a frontend audit
- No new npm dependencies needed — all changes use existing Tailwind v4 + Radix + Lucide stack
- Commit after each task or logical group of parallel tasks
- Stop at any checkpoint to validate the story independently
- Refer to `quickstart.md` for detailed implementation patterns and code examples
