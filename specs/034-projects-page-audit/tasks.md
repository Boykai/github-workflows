# Tasks: Audit & Polish Projects Page for Visual Cohesion and UX Quality

**Input**: Design documents from `/specs/034-projects-page-audit/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/component-contracts.yaml, quickstart.md

**Tests**: The feature specification does not request a TDD workflow, so no dedicated test-writing tasks are included. Existing frontend tests, lint, and type-check must pass after all changes.

**Organization**: Tasks are grouped by user story so each story can be audited, fixed, and validated independently. User Stories 1 and 2 deliver the P1 visual and state-correctness MVP; User Stories 3–5 address P2 accessibility, responsiveness, and interactivity; User Story 6 covers P3 code quality and performance.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on incomplete tasks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/` (React/TypeScript), `backend/src/` (Python/FastAPI)
- **Frontend pages**: `frontend/src/pages/`
- **Board components**: `frontend/src/components/board/`
- **Common components**: `frontend/src/components/common/`
- **UI primitives**: `frontend/src/components/ui/`
- **Hooks**: `frontend/src/hooks/`
- **Layout**: `frontend/src/layout/`
- **Design tokens**: `frontend/src/index.css`

---

## Phase 1: Setup

**Purpose**: Establish a passing baseline and create the audit reference material.

- [ ] T001 Run `npm run test`, `npm run lint`, and `npm run type-check` in `frontend/` to confirm the existing codebase passes all checks before any changes
- [ ] T002 [P] Review and document the Celestial design token inventory (colors, typography, spacing, shadows, radii, motion) in `frontend/src/index.css` as the audit reference baseline
- [ ] T003 [P] Review and document the custom CSS classes used by the Projects page (`.celestial-panel`, `.moonwell`, `.solar-chip`, `.project-board-column`, `.project-board-card`, `.project-pipeline-select`, `.project-pipeline-option`) in `frontend/src/index.css`

**Checkpoint**: Existing tests pass, and the full design token reference is established for auditing.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Audit and fix the shared utilities and primitives that all board components depend on. These must be correct before per-component story work begins.

**⚠️ CRITICAL**: No user story work should begin until shared color utilities and base component tokens are verified.

- [ ] T004 Audit `frontend/src/components/board/colorUtils.ts` for hardcoded hex/rgb/hsl values and replace any off-palette colors with Celestial design tokens
- [ ] T005 [P] Audit `frontend/src/lib/utils.ts` to confirm the `cn()` helper is used consistently — no template literal className composition anywhere on the Projects page
- [ ] T006 [P] Audit `frontend/src/components/common/CelestialLoader.tsx` for design token compliance (colors, sizing, animation) and `prefers-reduced-motion` support
- [ ] T007 [P] Audit `frontend/src/components/common/ProjectSelectionEmptyState.tsx` for design token compliance, proper empty-state messaging, and consistent styling with other empty states in the application
- [ ] T008 [P] Audit `frontend/src/components/common/CelestialCatalogHero.tsx` for design token compliance (typography uses `--font-display`, spacing follows standard scale, colors reference tokens)

**Checkpoint**: All shared utilities and base components used by the Projects page are design-token compliant and visually consistent.

---

## Phase 3: User Story 1 — Visually Cohesive Projects Page (Priority: P1) 🎯 MVP

**Goal**: Ensure every visual element on the Projects page uses the Celestial design system tokens — no hardcoded colors, ad-hoc spacing, or mismatched typography.

**Independent Test**: Perform a side-by-side visual comparison of the Projects page against other application pages (Dashboard, Agents, Settings). All shared elements — headings, buttons, cards, icons, spacing — must use the same design tokens and styling patterns. Verify in both light and dark mode.

### Implementation for User Story 1

- [ ] T009 [US1] Audit and fix `frontend/src/pages/ProjectsPage.tsx` inline components (ProjectSelectorButton, SyncStatusIndicator, PipelineSelectorDropdown, BlockingToggle) for hardcoded colors — replace any raw Tailwind color classes (e.g., `green-500`, `yellow-500`, `blue-500`, `red-500`, `amber-500`) with Celestial design tokens or semantic CSS custom properties
- [ ] T010 [P] [US1] Audit and fix `frontend/src/components/board/IssueCard.tsx` for design token compliance — verify priority colors use `--priority-p0` through `--priority-p3` tokens, label chips use proper contrast, avatar styling matches application conventions, and `.project-board-card` class is applied consistently
- [ ] T011 [P] [US1] Audit and fix `frontend/src/components/board/BoardColumn.tsx` for design token compliance — verify column header typography, status dot colors from `colorUtils.ts`, spacing between items, and `.project-board-column` class usage
- [ ] T012 [P] [US1] Audit and fix `frontend/src/components/board/BoardToolbar.tsx` for design token compliance — verify filter/sort/group button styling, active state indicators, dropdown panel backgrounds, and consistent icon sizing from Lucide React
- [ ] T013 [P] [US1] Audit and fix `frontend/src/components/board/IssueDetailModal.tsx` for design token compliance — verify modal backdrop, panel background, typography hierarchy, section spacing, link colors, and badge/chip styling
- [ ] T014 [P] [US1] Audit and fix `frontend/src/components/board/ProjectIssueLaunchPanel.tsx` for design token compliance — verify form input styling, button variants, pipeline stage grid colors, error message styling, and panel layout
- [ ] T015 [P] [US1] Audit and fix `frontend/src/components/board/BlockingIssuePill.tsx` and `frontend/src/components/board/BlockingChainPanel.tsx` for design token compliance — verify pill colors, action button styling, panel collapse/expand styling, and typography
- [ ] T016 [P] [US1] Audit and fix `frontend/src/components/board/RefreshButton.tsx` for design token compliance — verify spinner animation, button variant, and icon sizing
- [ ] T017 [US1] Audit and fix `frontend/src/layout/ProjectSelector.tsx` for design token compliance — verify dropdown panel background, option hover/selected states, search input styling, and loading indicator
- [ ] T018 [US1] Verify light mode and dark mode rendering across all Projects page components by confirming all color references resolve correctly under both `@media (prefers-color-scheme: dark)` and default themes in `frontend/src/index.css`

**Checkpoint**: All visual elements on the Projects page use Celestial design tokens exclusively. No hardcoded colors, ad-hoc spacing, or mismatched typography remains. Both light and dark modes render correctly.

---

## Phase 4: User Story 2 — Bug-Free and Complete Page States (Priority: P1)

**Goal**: Ensure every page state — loading, empty (no project), empty (no items), empty (filtered), populated, error, and rate-limited — renders correctly with appropriate messaging and no console errors.

**Independent Test**: Trigger each page state and verify correct rendering: loading spinner during fetch, empty-state message when no project is selected, empty-board guidance when board has no items, filter-empty message with clear button, error banner with retry on network failure, rate-limit banner with countdown, and a fully populated board with no layout overflow. Verify zero console errors across all states.

### Implementation for User Story 2

- [ ] T019 [US2] Audit and fix loading state rendering in `frontend/src/pages/ProjectsPage.tsx` — verify `CelestialLoader` displays correctly during board data fetch, matches loading patterns on other pages, and transitions cleanly to populated/empty/error states
- [ ] T020 [P] [US2] Audit and fix no-project-selected empty state in `frontend/src/pages/ProjectsPage.tsx` — verify `ProjectSelectionEmptyState` renders with no layout breaks, messaging is clear, and the component matches empty states on other pages
- [ ] T021 [P] [US2] Audit and fix empty board states in `frontend/src/pages/ProjectsPage.tsx` — verify the "No items yet" message (Inbox icon) for empty boards and the "No issues match" message (Search icon + Clear All button) for filtered-empty boards both render correctly with consistent styling
- [ ] T022 [US2] Audit and fix error and rate-limit state rendering in `frontend/src/pages/ProjectsPage.tsx` — verify error banners (board error with retry, projects error, refresh failure), rate-limit banner with countdown, and rate-limit-low warning all render with correct styling, appropriate icons, and functional retry/dismiss actions
- [ ] T023 [US2] Audit and fix populated board rendering in `frontend/src/pages/ProjectsPage.tsx` and `frontend/src/components/board/ProjectBoard.tsx` — verify no layout overflow, clipping, or misalignment with multiple columns and varying item counts per column
- [ ] T024 [US2] Verify zero console errors (no unhandled errors, missing React keys, or deprecation warnings) across all page states by exercising each state in the browser developer console in `frontend/src/pages/ProjectsPage.tsx`

**Checkpoint**: Every page state renders correctly with appropriate messaging. Zero console errors across all states. Error banners have functional retry actions.

---

## Phase 5: User Story 3 — Accessible Projects Page (Priority: P2)

**Goal**: Ensure the Projects page meets WCAG AA accessibility standards — full keyboard navigability, proper ARIA attributes, sufficient color contrast, and correct focus management.

**Independent Test**: Navigate the entire Projects page using only the keyboard (Tab, Shift+Tab, Enter, Escape, Arrow keys). Verify every interactive element is reachable, focus order is logical, visible focus indicators are present, and modals/dropdowns trap focus correctly. Run an automated accessibility scanner and verify zero critical/serious violations.

### Implementation for User Story 3

- [ ] T025 [US3] Audit and fix keyboard navigation in `frontend/src/pages/ProjectsPage.tsx` — verify all interactive elements (project selector button, pipeline selector, blocking toggle, toolbar buttons, board cards, banners) are reachable via Tab with a logical focus order
- [ ] T026 [P] [US3] Audit and fix ARIA attributes on custom dropdown controls in `frontend/src/pages/ProjectsPage.tsx` — verify ProjectSelectorButton has `aria-haspopup`/`aria-expanded`/`aria-label`, PipelineSelectorDropdown has `role="listbox"` with `role="option"` children and `aria-selected`, and BlockingToggle has `role="switch"` with `aria-checked`
- [ ] T027 [P] [US3] Audit and fix ARIA attributes and keyboard interaction in `frontend/src/components/board/BoardToolbar.tsx` — verify filter/sort/group dropdowns have `aria-label`, dropdown panels close on Escape, and active state is communicated to screen readers
- [ ] T028 [US3] Audit and fix focus management in `frontend/src/components/board/IssueDetailModal.tsx` — verify focus is trapped within the modal when open, Escape key closes the modal, focus returns to the triggering board card on close, and the modal has `role="dialog"` with `aria-modal="true"` and an accessible title
- [ ] T029 [P] [US3] Audit and fix accessible names on interactive elements in `frontend/src/components/board/IssueCard.tsx` — verify each card has an accessible name from its title, priority badges include accessible text (not color-only), assignee avatars have alt text, and the card has appropriate button or link semantics
- [ ] T030 [P] [US3] Audit and fix accessible names and roles in `frontend/src/components/board/ProjectIssueLaunchPanel.tsx` — verify form inputs are labeled, submit button states are communicated, error messages are associated with fields, and the panel has appropriate landmark roles
- [ ] T031 [US3] Audit and fix color contrast ratios across all Projects page components — verify all `text-muted-foreground`, `text-muted-foreground/80`, and `text-muted-foreground/60` usages meet WCAG AA minimum 4.5:1 against their backgrounds, and all UI components meet 3:1
- [ ] T032 [US3] Audit and add visible focus indicators (`focus-visible:ring-*` classes) to any interactive elements on the Projects page that lack them across `frontend/src/pages/ProjectsPage.tsx`, `frontend/src/components/board/IssueCard.tsx`, `frontend/src/components/board/BoardToolbar.tsx`, and `frontend/src/components/board/BlockingIssuePill.tsx`

**Checkpoint**: The Projects page is fully navigable via keyboard, all custom controls have correct ARIA attributes, focus is properly managed in modals, and contrast ratios meet WCAG AA.

---

## Phase 6: User Story 4 — Responsive Layout Across Screen Sizes (Priority: P2)

**Goal**: Ensure the Projects page adapts gracefully to desktop (1280px+), tablet (768px–1279px), and mobile (below 768px) with no horizontal scrolling, overlapping elements, or truncated interactive content.

**Independent Test**: Resize the browser to each breakpoint and verify: desktop shows the full board grid with all panels visible; tablet adapts with horizontally scrollable columns; mobile provides a single-column-friendly layout with touch-friendly targets. Verify smooth transitions when crossing breakpoints.

### Implementation for User Story 4

- [ ] T033 [US4] Audit and fix the board grid responsive behavior in `frontend/src/components/board/ProjectBoard.tsx` — verify the dynamic `gridTemplateColumns` style adapts to smaller screens, add `overflow-x-auto` wrapper if missing, and set minimum column widths that work on mobile
- [ ] T034 [P] [US4] Audit and fix responsive behavior of `frontend/src/components/board/IssueDetailModal.tsx` — verify the modal is full-width on mobile, centered with `max-width` on desktop, and all content remains readable and scrollable on small screens
- [ ] T035 [P] [US4] Audit and fix responsive behavior of `frontend/src/components/board/ProjectIssueLaunchPanel.tsx` — verify the launch panel adapts to mobile widths, form inputs remain usable, and the pipeline stages grid (dynamic `gridTemplateColumns`) has responsive handling
- [ ] T036 [US4] Audit and fix touch target sizes on mobile across `frontend/src/pages/ProjectsPage.tsx` and `frontend/src/components/board/` — verify all buttons, toggles, dropdown triggers, and card click targets meet the 44×44px minimum on touch-capable screen sizes
- [ ] T037 [US4] Audit and fix the page shell, header, and toolbar responsive behavior in `frontend/src/pages/ProjectsPage.tsx` and `frontend/src/components/board/BoardToolbar.tsx` — verify `flex-col`/`sm:flex-row` wrapping on the header, toolbar controls adapt to narrower widths without overflow, and padding scales with `p-4 sm:p-6`

**Checkpoint**: The Projects page renders correctly across desktop, tablet, and mobile breakpoints. No horizontal overflow, overlapping elements, or undersized touch targets.

---

## Phase 7: User Story 5 — Correct and Responsive Interactive Elements (Priority: P2)

**Goal**: Ensure every interactive control on the Projects page works correctly and provides clear visual feedback — hover states, focus states, loading indicators, and disabled states during processing.

**Independent Test**: Exercise every interactive element: open/close/select in the project selector, open/close/select in the pipeline selector, toggle blocking on/off, apply and clear filters/sorts/groups in the toolbar, click a board card to open and close the issue detail modal, trigger a pipeline launch and observe confirmation/error feedback, and click the refresh button.

### Implementation for User Story 5

- [ ] T038 [US5] Audit and fix project selector interactions in `frontend/src/pages/ProjectsPage.tsx` and `frontend/src/layout/ProjectSelector.tsx` — verify the dropdown opens on click, displays available projects, closes on selection or outside click, and updates the board on selection
- [ ] T039 [P] [US5] Audit and fix pipeline selector and blocking toggle interactions in `frontend/src/pages/ProjectsPage.tsx` — verify the pipeline dropdown opens/closes correctly with Escape and outside-click support, option selection triggers assignment mutation, and the blocking toggle reflects effective state with proper visual feedback
- [ ] T040 [P] [US5] Audit and fix toolbar filter, sort, and group interactions in `frontend/src/components/board/BoardToolbar.tsx` — verify each control opens/closes correctly, selections update the board, active states are visually indicated, and the Clear All button resets all controls
- [ ] T041 [US5] Audit and fix board card click → modal open → modal close flow in `frontend/src/pages/ProjectsPage.tsx`, `frontend/src/components/board/IssueCard.tsx`, and `frontend/src/components/board/IssueDetailModal.tsx` — verify clicking a card opens the correct issue detail, the modal can be closed via close button or Escape, and board state is preserved on close
- [ ] T042 [US5] Audit and fix pipeline launch flow in `frontend/src/components/board/ProjectIssueLaunchPanel.tsx` — verify issue creation, pipeline trigger, confirmation/error feedback, and page state update after launch
- [ ] T043 [US5] Audit and fix hover and focus states on all buttons across `frontend/src/pages/ProjectsPage.tsx`, `frontend/src/components/board/RefreshButton.tsx`, `frontend/src/components/board/BlockingIssuePill.tsx`, and `frontend/src/components/board/BoardToolbar.tsx` — verify visible hover/focus state changes and immediate visual feedback on click (loading state, disabled during processing)

**Checkpoint**: Every interactive element on the Projects page functions correctly with appropriate visual feedback for all user interactions.

---

## Phase 8: User Story 6 — Performance and Code Quality (Priority: P3)

**Goal**: Ensure the Projects page follows project conventions for component structure, avoids unnecessary re-renders, and makes efficient data-fetching requests.

**Independent Test**: Profile the Projects page with React DevTools during typical interactions (switching projects, applying filters, opening modals). Verify no unnecessary re-renders for components whose inputs haven't changed. Inspect the Network tab for duplicate or redundant API requests. Review component code for single-responsibility adherence.

### Implementation for User Story 6

- [ ] T044 [US6] Audit `frontend/src/components/board/IssueCard.tsx` render behavior — verify the component does not re-render when sibling cards change, confirm stable `onClick` reference from parent via `useCallback`, and add `React.memo` wrapping if missing and beneficial
- [ ] T045 [P] [US6] Audit data-fetching patterns in `frontend/src/hooks/useProjectBoard.ts`, `frontend/src/hooks/useProjects.ts`, and `frontend/src/hooks/useBlockingQueue.ts` — verify no duplicate requests during normal navigation, confirm `staleTime` values are appropriate, and ensure request cancellation on rapid project switching
- [ ] T046 [P] [US6] Audit component boundaries and code conventions in `frontend/src/pages/ProjectsPage.tsx` — verify inline components (ProjectSelectorButton, SyncStatusIndicator, PipelineSelectorDropdown, BlockingToggle, PipelineStagesGrid) follow single-responsibility principle, confirm `cn()` is used for all className composition (no template literals), and unused variables/parameters use `_` prefix per `tsconfig.json` conventions
- [ ] T047 [US6] Audit render performance of the pipeline selector dropdown and rate-limit banner in `frontend/src/pages/ProjectsPage.tsx` — verify dropdown state changes do not trigger full board re-renders, and rate-limit info updates do not cause unnecessary full-page re-renders

**Checkpoint**: The Projects page follows project conventions, avoids unnecessary re-renders, and makes efficient data-fetching requests.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Validate the complete audit, run all quality gates, and produce the audit summary.

- [ ] T048 [P] Validate the audit checklist scenarios from `specs/034-projects-page-audit/quickstart.md` against the updated Projects page — exercise each priority group (P1: visual consistency and states, P2: accessibility and responsiveness and interactions, P3: performance) to confirm all fixes are effective
- [ ] T049 [P] Run `npm run test`, `npm run lint`, `npm run type-check`, and `npm run build` in `frontend/` to confirm all quality gates pass after audit changes
- [ ] T050 Produce an audit summary documenting all findings, all changes made with file references, and any improvements deferred for future work — per FR-013 in `spec.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story phases (Phases 3–8)**: Depend on Foundational completion
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories. Establishes the visual baseline for all subsequent stories.
- **US2 (P1)**: Can start after Foundational (Phase 2) — independent of US1 but benefits from visual fixes being in place.
- **US3 (P2)**: Can start after Foundational (Phase 2) — independent of US1/US2 but ARIA/focus fixes may touch the same files.
- **US4 (P2)**: Can start after Foundational (Phase 2) — independent of other stories. Responsive changes are additive.
- **US5 (P2)**: Can start after Foundational (Phase 2) — independent of other stories. Interaction fixes complement visual and accessibility work.
- **US6 (P3)**: Should start after US1 (Phase 3) — performance and code quality audit is most effective after visual fixes have stabilized the code.

### Within Each User Story

- Audit shared/foundational elements before page-specific elements
- Fix design token compliance before verifying dark/light mode
- Fix ARIA attributes before verifying keyboard navigation flow
- Fix responsive layout before verifying touch targets
- Audit individual components before verifying cross-component interactions

### Parallel Opportunities

- **Phase 1**: T002 and T003 can run in parallel (both are read-only documentation tasks)
- **Phase 2**: T005, T006, T007, and T008 can all run in parallel (different files, no dependencies)
- **US1**: T010, T011, T012, T013, T014, T015, and T016 can all run in parallel (different component files)
- **US2**: T020 and T021 can run in parallel (different empty state conditions)
- **US3**: T026/T027, T029/T030 can run in parallel within their pairs (different component files)
- **US4**: T034 and T035 can run in parallel (different component files)
- **US5**: T039 and T040 can run in parallel (different component files)
- **US6**: T045 and T046 can run in parallel (hooks vs. page component)
- **Phase 9**: T048 and T049 can run in parallel (manual validation vs. automated checks)

---

## Parallel Execution Examples

### User Story 1

```text
# Launch all per-component design token audits in parallel:
Task T010: Audit and fix IssueCard.tsx for design token compliance
Task T011: Audit and fix BoardColumn.tsx for design token compliance
Task T012: Audit and fix BoardToolbar.tsx for design token compliance
Task T013: Audit and fix IssueDetailModal.tsx for design token compliance
Task T014: Audit and fix ProjectIssueLaunchPanel.tsx for design token compliance
Task T015: Audit and fix BlockingIssuePill.tsx and BlockingChainPanel.tsx
Task T016: Audit and fix RefreshButton.tsx for design token compliance
```

### User Story 3

```text
# Launch ARIA attribute audits in parallel:
Task T026: Audit ARIA on custom dropdowns in ProjectsPage.tsx
Task T027: Audit ARIA on BoardToolbar.tsx
Task T029: Audit accessible names on IssueCard.tsx
Task T030: Audit accessible names on ProjectIssueLaunchPanel.tsx
```

### User Story 4

```text
# Launch per-component responsive audits in parallel:
Task T034: Audit responsive behavior of IssueDetailModal.tsx
Task T035: Audit responsive behavior of ProjectIssueLaunchPanel.tsx
```

### User Story 6

```text
# Launch independent audit streams in parallel:
Task T045: Audit data-fetching patterns in hooks
Task T046: Audit component boundaries and code conventions in ProjectsPage.tsx
```

---

## Implementation Strategy

### MVP First (User Stories 1 and 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (visual cohesion)
4. Complete Phase 4: User Story 2 (bug-free states)
5. **STOP and VALIDATE**: Compare Projects page against other pages side-by-side. Verify all states render correctly. Confirm zero console errors.
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Shared utilities verified
2. Add User Story 1 → Visual cohesion across all components (**Visual MVP**)
3. Add User Story 2 → All page states render correctly (**State Correctness MVP**)
4. Add User Story 3 → Accessibility compliance (WCAG AA)
5. Add User Story 4 → Responsive across all breakpoints
6. Add User Story 5 → All interactions verified and polished
7. Add User Story 6 → Performance and code quality validated
8. Polish → Full audit summary and quality gate validation

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (visual cohesion) — touches all component files for design token compliance
   - Developer B: User Story 2 (page states) — focuses on ProjectsPage.tsx state rendering
   - Developer C: User Story 3 (accessibility) — ARIA, focus management, contrast
   - Developer D: User Story 4 (responsive) — breakpoint behavior, touch targets
3. After P1 and P2 stories complete:
   - Developer A or B: User Story 5 (interactions)
   - Developer C or D: User Story 6 (performance/code quality)
4. Team converges for Polish phase

**Note**: Since US1 touches many component files for design tokens and US3–US5 may also touch the same files for accessibility/responsive/interaction fixes, coordinate carefully if running P1 and P2 stories in parallel to avoid merge conflicts.

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 50 |
| **Setup tasks** | 3 (T001–T003) |
| **Foundational tasks** | 5 (T004–T008) |
| **US1 tasks** | 10 (T009–T018) |
| **US2 tasks** | 6 (T019–T024) |
| **US3 tasks** | 8 (T025–T032) |
| **US4 tasks** | 5 (T033–T037) |
| **US5 tasks** | 6 (T038–T043) |
| **US6 tasks** | 4 (T044–T047) |
| **Polish tasks** | 3 (T048–T050) |
| **Parallel opportunities** | 25 tasks marked `[P]` across setup, foundational, visual audits, accessibility audits, responsive audits, and final validation |
| **MVP scope** | Phases 1–4 (T001–T024) for visual cohesion and bug-free states |
| **Independent test criteria** | Each user story phase includes a standalone validation scenario derived from spec.md |
| **Format validation** | Every task uses the required `- [ ] T### [P?] [US?] Description with file path` checklist structure |

---

## Notes

- [P] tasks touch different files or can proceed once the task immediately before them establishes the shared context
- No dedicated automated-test authoring tasks are included because the specification did not request TDD; validation is captured in Phase 9 (T049) and through the quickstart.md scenarios (T048)
- This is a frontend-only audit — no backend changes are required per the plan
- All `cn()` usage must follow the established convention: no template literal className composition anywhere on the Projects page
- The SyncStatusIndicator inline component uses raw Tailwind color classes (`green-500`, `yellow-500`, `blue-500`, `red-500`) that should be evaluated for design token replacement during US1 (T009)
- The BlockingToggle uses `amber-500` which should be evaluated for replacement with `--color-gold` or a warning semantic token during US1 (T009)
- Deferred improvements (not in scope for this audit) should be documented in the audit summary (T050) per FR-013
