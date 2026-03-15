# Tasks: Onboarding Spotlight Tour & Help/FAQ Page

**Input**: Design documents from `/solune/specs/042-onboarding-help-faq/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Included for useOnboarding hook (guards critical localStorage logic per constitution check).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/frontend/src/` for all source files
- SVG assets: `solune/frontend/src/assets/onboarding/`
- Tests: `solune/frontend/src/` colocated as `*.test.ts(x)`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, shared types, and `data-tour-step` attributes on existing layout components

- [X] T001 Add TourStep and FaqEntry type definitions to `solune/frontend/src/types/index.ts`
- [X] T002 [P] Create 9 SVG line-art icons in `solune/frontend/src/assets/onboarding/` (sun-moon.svg, compass-rose.svg, star-chart.svg, chat-stars.svg, constellation-grid.svg, orbital-rings.svg, celestial-hand.svg, sun-moon-toggle.svg, book-stars.svg) — monochrome `currentColor` stroke, 24×24 viewBox, strokeWidth 1.5, fill none
- [X] T003 [P] Add `data-tour-step` attributes to Sidebar nav links, project selector, and theme toggle button in `solune/frontend/src/layout/Sidebar.tsx` — attributes: `sidebar-nav` on `<nav>`, `project-selector` on selector button, `theme-toggle` on Sun/Moon button, `projects-link`/`pipeline-link`/`agents-link`/`help-link` on corresponding NavLink elements
- [X] T004 [P] Add `data-tour-step="chat-toggle"` attribute to ChatPopup toggle button in `solune/frontend/src/components/chat/ChatPopup.tsx`
- [X] T005 Add `HelpCircle` import and Help entry `{ path: '/help', label: 'Help', icon: HelpCircle }` to NAV_ROUTES in `solune/frontend/src/constants.ts` (after Apps, before Settings)
- [X] T006 Add lazy HelpPage import and `<Route path="help" element={withSuspense(<HelpPage />)} />` to route tree inside AppLayout parent in `solune/frontend/src/App.tsx`

**Checkpoint**: All layout elements have `data-tour-step` attributes. Help route registered but HelpPage not yet implemented (will 404 as NotFoundPage until Phase 4). NAV_ROUTES updated. SVG assets available for import.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core hook that both the tour (US1) and Help page replay (US3) depend on

**⚠️ CRITICAL**: useOnboarding hook must be complete before any user story implementation

- [X] T007 Implement `useOnboarding` hook in `solune/frontend/src/hooks/useOnboarding.ts` — localStorage key `solune-onboarding-completed`, TOTAL_STEPS constant = 9, returns `{ isActive, hasCompleted, currentStep, totalSteps, next, prev, skip, restart }`, follows useSidebarState try/catch pattern for localStorage, auto-activates when hasCompleted is false
- [X] T008 Write unit test for useOnboarding hook in `solune/frontend/src/hooks/useOnboarding.test.ts` — test first-visit auto-activation, next/prev step navigation, skip sets completion flag, restart resets currentStep to 0 without clearing hasCompleted, localStorage persistence across hook re-mounts

**Checkpoint**: useOnboarding hook ready. Both tour and Help page can consume it.

---

## Phase 3: User Story 1 — First-Time Guided Spotlight Tour (Priority: P1) 🎯 MVP

**Goal**: New users see a 9-step guided spotlight that auto-launches on first login, highlighting sidebar, chat, pipelines, agents, and theme toggle with glowing cutouts and tooltips.

**Independent Test**: Clear `solune-onboarding-completed` from localStorage → refresh → tour auto-starts → step through all 9 → completes → refresh → tour does not reappear.

### Implementation for User Story 1

- [X] T009 [P] [US1] Create TourProgress dot indicator component in `solune/frontend/src/components/onboarding/TourProgress.tsx` — renders row of dots (total = totalSteps), active dot gets `celestial-pulse-glow` class with gold bg, completed dots solid gold, upcoming dots muted border only, accepts `currentStep` and `totalSteps` props per contract
- [X] T010 [P] [US1] Create SpotlightOverlay component in `solune/frontend/src/components/onboarding/SpotlightOverlay.tsx` — fixed full-viewport div at z-[100], CSS clip-path polygon with rectangular cutout (8px padding) around targetRect, smooth transition via `transition: clip-path var(--transition-cosmic-base)`, bg-night/60 dark / bg-background/70 light backdrop, renders nothing when isVisible is false, null targetRect renders full overlay with no cutout (welcome step)
- [X] T011 [P] [US1] Create SpotlightTooltip component in `solune/frontend/src/components/onboarding/SpotlightTooltip.tsx` — positioned popover near targetRect using viewport-aware algorithm (preferred placement from step, flip if overflows, 16px margin), celestial-panel background + golden-ring shadow, renders step icon + title + description + step counter ("3 of 9") + Back/Next/Skip Tour buttons (Button component) + TourProgress dots, celestial-fade-in entry animation, mobile (<768px) renders as fixed bottom sheet with rounded-t-2xl, null targetRect centers tooltip in viewport
- [X] T012 [US1] Create SpotlightTour orchestrator in `solune/frontend/src/components/onboarding/SpotlightTour.tsx` — defines TOUR_STEPS array of 9 TourStep objects (Welcome/sidebar-nav/project-selector/chat-toggle/projects-link/pipeline-link/agents-link/theme-toggle/help-link), imports SVG icons from assets/onboarding/, consumes useOnboarding hook, queries `document.querySelector('[data-tour-step="..."]')` for target element, computes targetRect via getBoundingClientRect, uses ResizeObserver + scroll listener + window resize to recompute rect, renders SpotlightOverlay + SpotlightTooltip when isActive, auto-expands sidebar (calls onToggleSidebar) for sidebar-related steps (2-9) if isSidebarCollapsed and restores original state on tour end, scrolls target into view, skips step if target element not found
- [X] T013 [US1] Mount SpotlightTour in AppLayout — add `<SpotlightTour isSidebarCollapsed={isCollapsed} onToggleSidebar={toggleSidebar} />` after ChatPopup in `solune/frontend/src/layout/AppLayout.tsx`, import SpotlightTour component

**Checkpoint**: First-time spotlight tour is fully functional. Clear localStorage → login → 9-step tour auto-plays. Skip/complete persists flag. Sidebar auto-expands for sidebar steps.

---

## Phase 4: User Story 2 — Help Center Page with FAQ (Priority: P2)

**Goal**: Users navigate to `/help` from the sidebar to find FAQ answers, feature guides, and slash command reference. Delivers self-service guidance independent of the tour.

**Independent Test**: Navigate to `/help` → hero + Getting Started cards + FAQ accordion + Feature Guide grid + Slash Commands table all render. FAQ items expand/collapse. Feature guide cards link to correct pages.

### Implementation for User Story 2

- [X] T014 [P] [US2] Create FaqAccordion component in `solune/frontend/src/components/help/FaqAccordion.tsx` — accepts `entries: FaqEntry[]` prop, groups by category with section headings (Getting Started, Agents & Pipelines, Chat & Voice, Settings & Integration), exclusive toggle via useState tracking open item id, animated expand via grid-template-rows 0fr→1fr transition, celestial-panel per item, gold ChevronDown icon rotates 180° on expand, keyboard Enter/Space toggles, Tab navigates between items, ARIA attributes (role button, aria-expanded, aria-controls)
- [X] T015 [P] [US2] Create FeatureGuideCard component in `solune/frontend/src/components/help/FeatureGuideCard.tsx` — accepts title, description, icon, href props per contract, renders clickable card using react-router-dom Link, moonwell background class, rounded-[1.25rem], hover -translate-y-0.5 + border-primary/20, icon rendered at w-8 h-8 in primary color
- [X] T016 [US2] Create HelpPage in `solune/frontend/src/pages/HelpPage.tsx` — export named `HelpPage`, sections: (1) CelestialCatalogHero with eyebrow "// Guidance & support", title "Help Center", description "Everything you need to navigate your celestial workspace", actions slot with "Replay Tour" Button (calls useOnboarding restart), (2) Getting Started section with 3 cards linking to /projects, /pipeline, /agents, (3) FaqAccordion with 12 hardcoded FAQ_ENTRIES (3 per category: getting-started, agents-pipelines, chat-voice, settings-integration), (4) Feature Guide grid with 8 FeatureGuideCard instances (one per NAV_ROUTES area), (5) Slash Commands table reading getAllCommands() from registry

**Checkpoint**: Help page fully functional at `/help`. FAQ accordion expands/collapses. Feature guide cards navigate. Slash commands table populated from registry. Replay Tour button visible (wired in Phase 5).

---

## Phase 5: User Story 3 — Replay Tour from Help Page (Priority: P3)

**Goal**: Users who completed the tour can replay it from the Help page. The "Replay Tour" button restarts the spotlight from step 1.

**Independent Test**: Complete or skip tour → navigate to `/help` → click "Replay Tour" → tour restarts from step 1 → complete tour again → refresh → tour does not auto-launch.

### Implementation for User Story 3

- [X] T017 [US3] Wire "Replay Tour" button in HelpPage to call `useOnboarding().restart()` in `solune/frontend/src/pages/HelpPage.tsx` — verify restart sets isActive true + currentStep 0 without clearing hasCompleted flag, button uses default Button variant with Play icon from lucide-react

**Checkpoint**: Full loop works: first-visit tour → complete → Help page → Replay → tour restarts → complete again → no auto-launch on refresh.

---

## Phase 6: User Story 4 — Keyboard & Accessibility Navigation (Priority: P3)

**Goal**: Tour is fully navigable via keyboard with proper focus management and screen reader support.

**Independent Test**: Start tour → ArrowRight advances, ArrowLeft goes back, Escape skips, Tab cycles within tooltip, screen reader announces each step change.

### Implementation for User Story 4

- [X] T018 [US4] Add keyboard event listener to SpotlightTour in `solune/frontend/src/components/onboarding/SpotlightTour.tsx` — useEffect with keydown handler: ArrowRight → next(), ArrowLeft → prev(), Escape → skip(), attach on mount when isActive, cleanup on unmount or inactive
- [X] T019 [US4] Add focus trap to SpotlightTooltip in `solune/frontend/src/components/onboarding/SpotlightTooltip.tsx` — on mount query all focusable elements (buttons) in tooltip ref, on Tab at last element wrap to first, on Shift+Tab at first wrap to last, on mount focus first button, on unmount restore previously focused element, add role="dialog" aria-modal="true" to tooltip container
- [X] T020 [US4] Add aria-live announcer to SpotlightTour in `solune/frontend/src/components/onboarding/SpotlightTour.tsx` — visually hidden div with aria-live="polite" and role="status", on step change update inner text to `"Step {n} of 9: {title}. {description}"`, use sr-only class for visual hiding

**Checkpoint**: Tour is fully keyboard-accessible. Screen readers announce step changes. Focus is trapped within tooltip.

---

## Phase 7: User Story 5 — Theme-Aware Tour & Help Experience (Priority: P3)

**Goal**: All new components adapt to light/dark/system theme. Mid-tour theme toggle immediately updates overlay, tooltip, and progress indicator colors.

**Independent Test**: Start tour in dark mode → toggle to light → overlay, tooltip bg, icon colors, progress dots all update. Open Help page in light → toggle to dark → FAQ panels, feature cards, hero all adapt.

### Implementation for User Story 5

- [X] T021 [US5] Verify and fix theme-adaptive CSS in SpotlightOverlay — ensure bg-night/60 in dark, bg-background/70 in light via Tailwind dark: variant in `solune/frontend/src/components/onboarding/SpotlightOverlay.tsx`
- [X] T022 [US5] Verify and fix theme-adaptive CSS in SpotlightTooltip — ensure celestial-panel and golden-ring classes inherit dark mode tokens, icon uses text-primary for currentColor, buttons use existing Button variants which already handle dark mode in `solune/frontend/src/components/onboarding/SpotlightTooltip.tsx`
- [X] T023 [US5] Verify and fix theme-adaptive CSS in FaqAccordion — ensure celestial-panel dark variant applies, chevron uses text-primary, answer text uses text-muted-foreground in `solune/frontend/src/components/help/FaqAccordion.tsx`
- [X] T024 [US5] Verify and fix theme-adaptive CSS in FeatureGuideCard — ensure moonwell dark variant applies, icon color uses text-primary in `solune/frontend/src/components/help/FeatureGuideCard.tsx`

**Checkpoint**: All components theme-correct. Toggle theme mid-tour or on Help page → immediate visual update with no flicker or incorrect colors.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Edge case handling, responsive behavior, reduced motion, and final validation

- [X] T025 [P] Add mobile bottom sheet fallback to SpotlightTooltip — use `window.matchMedia('(max-width: 767px)')` to conditionally render fixed bottom-0 left-0 right-0 panel with rounded-t-2xl and drag handle indicator instead of positioned popover in `solune/frontend/src/components/onboarding/SpotlightTooltip.tsx`
- [X] T026 [P] Verify reduced motion support — all new components use existing `.celestial-*` animation classes which are already disabled under `@media (prefers-reduced-motion: reduce)` in index.css; verify clip-path transition on SpotlightOverlay also respects reduced motion by adding `motion-safe:` prefix to transition in `solune/frontend/src/components/onboarding/SpotlightOverlay.tsx`
- [X] T027 Run `npm run type-check` and `npm run lint` in `solune/frontend/` to verify no TypeScript or lint errors across all new and modified files
- [X] T028 Run `npm run test` in `solune/frontend/` to verify useOnboarding hook tests pass and no existing tests regress
- [X] T029 Run quickstart.md validation — follow the steps in `solune/specs/042-onboarding-help-faq/quickstart.md` to verify: tour auto-launches on first visit, Help page renders all sections, Replay Tour works, FAQ accordion works, each new tour step can be added following the documented process

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on T001 types from Setup — BLOCKS all user stories
- **US1 Tour (Phase 3)**: Depends on Phase 2 (useOnboarding), Phase 1 (SVGs, data-tour-step attrs)
- **US2 Help Page (Phase 4)**: Depends on Phase 2 (useOnboarding for Replay button type), Phase 1 (route, NAV_ROUTES)
- **US3 Replay (Phase 5)**: Depends on Phase 3 (tour exists) + Phase 4 (Help page exists)
- **US4 Keyboard/A11y (Phase 6)**: Depends on Phase 3 (tour components exist to enhance)
- **US5 Theme (Phase 7)**: Depends on Phase 3 + Phase 4 (components exist to verify)
- **Polish (Phase 8)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational (Phase 2) — standalone MVP
- **US2 (P2)**: Can start after Foundational (Phase 2) — standalone, parallel with US1
- **US3 (P3)**: Requires US1 + US2 complete (integrates both)
- **US4 (P3)**: Requires US1 complete (enhances tour components)
- **US5 (P3)**: Requires US1 + US2 complete (verifies both)

### Within Each User Story

- Models/types before components
- Leaf components (TourProgress, SpotlightOverlay) before orchestrator (SpotlightTour)
- Orchestrator before layout mount
- Sub-components (FaqAccordion, FeatureGuideCard) before page (HelpPage)

### Parallel Opportunities

**Phase 1** (4 parallel tasks):
- T002, T003, T004 can all run in parallel (different files)

**Phase 3** (3 parallel tasks):
- T009, T010, T011 can all run in parallel (different component files)

**Phase 4** (2 parallel tasks):
- T014, T015 can run in parallel (different component files)

**Phase 7** (4 parallel tasks):
- T021, T022, T023, T024 can all run in parallel (different files)

**Phase 8** (2 parallel tasks):
- T025, T026 can run in parallel (different files)

---

## Parallel Example: User Story 1

```bash
# Phase 1 parallel tasks (different files):
Task T002: "Create 9 SVG icons in solune/frontend/src/assets/onboarding/"
Task T003: "Add data-tour-step attrs to Sidebar.tsx"
Task T004: "Add data-tour-step attr to ChatPopup.tsx"

# Phase 3 parallel leaf components (different files):
Task T009: "TourProgress in components/onboarding/TourProgress.tsx"
Task T010: "SpotlightOverlay in components/onboarding/SpotlightOverlay.tsx"
Task T011: "SpotlightTooltip in components/onboarding/SpotlightTooltip.tsx"

# Then sequential orchestrator + mount:
Task T012: "SpotlightTour in components/onboarding/SpotlightTour.tsx" (depends on T009-T011)
Task T013: "Mount SpotlightTour in AppLayout.tsx" (depends on T012)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (types, SVGs, data-tour-step attrs, route registration)
2. Complete Phase 2: Foundational (useOnboarding hook + test)
3. Complete Phase 3: User Story 1 (tour components + AppLayout mount)
4. **STOP and VALIDATE**: Clear localStorage → tour auto-starts → 9 steps → completes → no re-launch
5. Deploy/demo if ready — tour works standalone without Help page

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Tour) → Test independently → Deploy (MVP!)
3. Add US2 (Help Page) → Test independently → Deploy
4. Add US3 (Replay) → Connects US1+US2 → Deploy
5. Add US4 (Keyboard/A11y) → Enhances US1 → Deploy
6. Add US5 (Theme) → Verifies all → Deploy
7. Polish → Final validation → Ship

### Parallel Team Strategy

With two developers:
1. Both complete Setup + Foundational together
2. Once Foundational done:
   - Developer A: User Story 1 (Tour)
   - Developer B: User Story 2 (Help Page)
3. US3 (Replay) after both A+B done
4. US4 + US5 can be split

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- All file paths are relative to repository root
- No new npm dependencies needed — all tools available in existing stack
- SVG icons use `currentColor` stroke — theme-adaptive by design
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
