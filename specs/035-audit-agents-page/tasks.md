# Tasks: Audit & Polish the Agents Page for Quality and Consistency

**Input**: Design documents from `/specs/035-audit-agents-page/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/component-contracts.yaml, quickstart.md

**Tests**: No new tests are mandated by the specification. Existing tests (AgentSaveBar, AgentTile, ThemedAgentIcon) must continue to pass. Tests are NOT included in task phases below unless accessibility scanning reveals gaps.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. This is a frontend-only audit-and-refactor effort — no backend changes required.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/` at repository root
- Pages: `frontend/src/pages/`
- Agent Catalog components: `frontend/src/components/agents/`
- Orbital Map components: `frontend/src/components/board/`
- Shared components: `frontend/src/components/common/`
- Design tokens: `frontend/src/index.css`

---

## Phase 1: Setup (Audit Baseline)

**Purpose**: Establish audit baseline — verify existing tests pass and no pre-existing regressions

- [x] T001 Run existing test suite (`npx vitest run`) and document any pre-existing failures in frontend/
- [x] T002 Run type-check (`npm run type-check`) and lint (`npm run lint`) to establish baseline in frontend/
- [x] T003 Review design token reference in frontend/src/index.css — document the full Celestial token set (colors, custom classes, focus styles) for use during audit

---

## Phase 2: Foundational (Cross-Cutting Token & Pattern Inventory)

**Purpose**: Identify all hardcoded values and missing patterns across Agents page components before story-specific fixes begin

**⚠️ CRITICAL**: No user story work can begin until this inventory phase is complete

- [x] T004 Audit all agent components for hardcoded color values (hex, rgb, hsl, named Tailwind colors not in design system) across frontend/src/components/agents/ and frontend/src/components/board/
- [x] T005 [P] Audit z-index usage across all Agents page components — document all z-[120], z-[140], z-[9999], z-50 values in frontend/src/components/agents/ and frontend/src/components/board/
- [x] T006 [P] Audit all interactive elements for missing `.celestial-focus` or equivalent `focus-visible:ring-*` classes across frontend/src/components/agents/ and frontend/src/components/board/
- [x] T007 [P] Audit all ARIA attributes — document missing roles, labels, and live regions across all Agents page components per contracts/component-contracts.yaml

**Checkpoint**: Audit inventory complete — story-specific implementation can begin

---

## Phase 3: User Story 1 — Visually Consistent Agents Page (Priority: P1) 🎯 MVP

**Goal**: Replace all hardcoded colors, ensure design-token-only usage, and verify light/dark theme consistency across every Agents page component

**Independent Test**: Visually compare Agents page against Projects/Settings pages — all shared elements (headings, buttons, cards, icons, spacing, badges) must use identical design tokens and styling patterns. Toggle light/dark mode and verify no visual artifacts.

### Implementation for User Story 1

- [x] T008 [P] [US1] Replace hardcoded `border-emerald-300/40`, `bg-emerald-50/80` badge colors with `solar-chip-success` design tokens in frontend/src/components/agents/AgentsPanel.tsx
- [x] T009 [P] [US1] Replace hardcoded `text-green-700 dark:text-green-400` success message colors with design-token equivalents in frontend/src/components/agents/AgentCard.tsx
- [x] T010 [P] [US1] Replace hardcoded source badge colors (`bg-blue-100 dark:bg-blue-900/30`, `bg-green-100 dark:bg-green-900/30`) with design-token badges in frontend/src/components/board/AddAgentPopover.tsx
- [x] T011 [P] [US1] Replace hardcoded inline SVG colors (inline `hsl(var(--gold))`, `hsl(var(--glow))` with magic opacity) with CSS custom property references via Tailwind in frontend/src/components/board/AgentTile.tsx
- [x] T012 [P] [US1] Audit and normalize hardcoded amber colors (`border-amber-300/60`, `bg-amber-50/80`) in unsaved-change indicators in frontend/src/components/agents/AddAgentModal.tsx and frontend/src/components/agents/AgentInlineEditor.tsx
- [x] T013 [P] [US1] Verify status badge colors (Active → `solar-chip-success`, Pending Creation → `solar-chip-violet`, Pending Deletion → `solar-chip-danger`) are consistent across all card variants in frontend/src/components/agents/AgentCard.tsx
- [x] T014 [P] [US1] Verify source badge colors (builtin → `solar-chip-neutral`, repository → `solar-chip-success`, shared → `solar-chip-violet`, local → `solar-chip`) are consistent across AgentCard and AddAgentPopover in frontend/src/components/agents/AgentCard.tsx and frontend/src/components/board/AddAgentPopover.tsx
- [x] T015 [P] [US1] Verify all icons across agent cards, action buttons, and Orbital Map come from Lucide React and are consistently sized (16px in compact, 18–20px in default) in frontend/src/components/agents/ and frontend/src/components/board/
- [x] T016 [P] [US1] Verify radial gradient overlays, border radii, and shadow values in agent cards and panels align with Celestial design system tokens in frontend/src/components/agents/AgentsPanel.tsx and frontend/src/components/agents/AgentCard.tsx
- [x] T017 [P] [US1] Verify `font-display` and `font-sans` usage in headings and body text matches other pages (Projects, Settings) in frontend/src/pages/AgentsPage.tsx
- [x] T018 [US1] Test light mode and dark mode switching — verify all elements render correctly with no visual artifacts, unreadable text, or missing styles across all Agents page components
- [x] T019 [US1] Run existing tests (`npx vitest run`) to verify no regressions from US1 changes

**Checkpoint**: User Story 1 complete — Agents page is visually consistent with the rest of Project Solune

---

## Phase 4: User Story 2 — Bug-Free and Complete Page States (Priority: P1)

**Goal**: Verify and fix all page states (loading, empty, populated, pending, error) render correctly with appropriate messaging and no layout breaks

**Independent Test**: Trigger each page state (loading skeleton, empty catalog, no project selected, populated catalog with featured/all/pending, error state, no board columns) and verify correct rendering with appropriate messaging.

### Implementation for User Story 2

- [x] T020 [P] [US2] Add error handling for `pipelineList` query failure — show error state or graceful fallback in frontend/src/pages/AgentsPage.tsx
- [x] T021 [P] [US2] Add error handling for `pipelineAssignment` query failure — show error state or graceful fallback in frontend/src/pages/AgentsPage.tsx
- [x] T022 [P] [US2] Verify loading skeleton (animated placeholder cards) displays correctly and is visually consistent with loading states on other pages in frontend/src/components/agents/AgentsPanel.tsx
- [x] T023 [P] [US2] Verify `ProjectSelectionEmptyState` renders correctly with no layout breaks when no project is selected in frontend/src/pages/AgentsPage.tsx
- [x] T024 [P] [US2] Verify empty agent catalog state displays "Create the first agent" prompt with no visual glitches in frontend/src/components/agents/AgentsPanel.tsx
- [x] T025 [P] [US2] Verify pending agents section renders with correct status badges ("Pending PR", "Pending Deletion") and no layout collisions in frontend/src/components/agents/AgentsPanel.tsx
- [x] T026 [P] [US2] Verify error state displays red error box with clear description in frontend/src/components/agents/AgentsPanel.tsx
- [x] T027 [P] [US2] Verify featured agents algorithm (top 3 by usage, supplemented by recent) works correctly and catalog grid displays without overflow in frontend/src/components/agents/AgentsPanel.tsx
- [x] T028 [P] [US2] Verify "No board columns available" dashed border message renders correctly when no columns exist in frontend/src/pages/AgentsPage.tsx
- [x] T029 [P] [US2] Verify AgentPresetSelector handles `savedPipelines` query loading state — add loading indicator if missing in frontend/src/components/board/AgentPresetSelector.tsx
- [x] T030 [P] [US2] Add error dismissal mechanism for persistent error messages in AgentPresetSelector in frontend/src/components/board/AgentPresetSelector.tsx
- [x] T031 [P] [US2] Verify BulkModelUpdateDialog handles mutation failure with visible error and dismissal in frontend/src/components/agents/BulkModelUpdateDialog.tsx
- [x] T032 [P] [US2] Add error handling for failed icon save in AgentIconPickerModal in frontend/src/components/agents/AgentIconPickerModal.tsx
- [x] T033 [US2] Run existing tests (`npx vitest run`) to verify no regressions from US2 changes

**Checkpoint**: User Story 2 complete — all page states render correctly with no broken or confusing views

---

## Phase 5: User Story 3 — Accessible Agents Page (Priority: P2)

**Goal**: Achieve WCAG AA compliance — add missing ARIA attributes, focus indicators, focus management, keyboard navigation, and contrast compliance across all Agents page components

**Independent Test**: Navigate entire Agents page using only keyboard — every interactive element reachable via Tab, visible focus indicator present, screen reader announces all elements. Run automated accessibility scanner (jest-axe) — zero critical/serious violations.

### Implementation for User Story 3

#### Focus Indicators

- [x] T034 [P] [US3] Add `celestial-focus` class to all interactive elements (buttons, links, toggles) missing focus indicators in frontend/src/components/agents/AgentCard.tsx (icon, edit, delete buttons)
- [x] T035 [P] [US3] Add `celestial-focus` class to interactive elements in frontend/src/components/agents/AgentsPanel.tsx (search input, sort toggle, add button)
- [x] T036 [P] [US3] Add `celestial-focus` class to interactive elements in frontend/src/components/board/AgentTile.tsx (tile container, action buttons)
- [x] T037 [P] [US3] Add `celestial-focus` class to expand toggle in frontend/src/components/board/AgentConfigRow.tsx
- [x] T038 [P] [US3] Add focus indicators to reorder/remove buttons in frontend/src/components/agents/ToolsEditor.tsx
- [x] T039 [P] [US3] Add focus indicators to icon selection buttons in frontend/src/components/agents/AgentIconCatalog.tsx

#### ARIA Roles and Labels

- [x] T040 [P] [US3] Fix `role="presentation"` to `role="dialog"` with `aria-modal="true"` on modal content in frontend/src/components/agents/AgentIconPickerModal.tsx
- [x] T041 [P] [US3] Add `role="status"` and `aria-live="polite"` to save bar container in frontend/src/components/board/AgentSaveBar.tsx
- [x] T042 [P] [US3] Add `role="region"` and `aria-label="Agent column assignments"` to container in frontend/src/components/board/AgentConfigRow.tsx
- [x] T043 [P] [US3] Add `role="list"` to agents container in frontend/src/components/board/AgentColumnCell.tsx
- [x] T044 [P] [US3] Add `role="listitem"` to tile wrapper in frontend/src/components/board/AgentTile.tsx
- [x] T045 [P] [US3] Add `aria-expanded` attribute to dropdown trigger in frontend/src/components/board/AddAgentPopover.tsx
- [x] T046 [P] [US3] Add `aria-expanded` attribute to saved pipelines dropdown trigger in frontend/src/components/board/AgentPresetSelector.tsx
- [x] T047 [P] [US3] Add `role="listbox"` on option container and `role="option"` on each agent item in frontend/src/components/board/AddAgentPopover.tsx
- [x] T048 [P] [US3] Add `role="radiogroup"` on icon grid and `role="radio"` with `aria-checked` on each icon button in frontend/src/components/agents/AgentIconCatalog.tsx
- [x] T049 [P] [US3] Add `aria-hidden="true"` to decorative drag handle braille character in frontend/src/components/board/AgentDragOverlay.tsx
- [x] T050 [P] [US3] Add card-level accessible description for screen readers in frontend/src/components/agents/AgentCard.tsx
- [x] T051 [P] [US3] Add `aria-label` on move up/down/remove buttons in frontend/src/components/agents/ToolsEditor.tsx
- [x] T052 [P] [US3] Add `aria-busy="true"` during loading state in frontend/src/components/board/AddAgentPopover.tsx

#### Focus Management

- [x] T053 [P] [US3] Verify focus trap completeness in AddAgentModal — Tab cannot escape modal in frontend/src/components/agents/AddAgentModal.tsx
- [x] T054 [P] [US3] Implement focus trap in AgentIconPickerModal in frontend/src/components/agents/AgentIconPickerModal.tsx
- [x] T055 [P] [US3] Verify focus trap in BulkModelUpdateDialog in frontend/src/components/agents/BulkModelUpdateDialog.tsx
- [x] T056 [P] [US3] Implement focus trap in AgentPresetSelector confirmation dialogs in frontend/src/components/board/AgentPresetSelector.tsx
- [x] T057 [P] [US3] Implement focus trap in AddAgentPopover dropdown in frontend/src/components/board/AddAgentPopover.tsx
- [x] T058 [P] [US3] Add focus-move-to-editor on open and focus-restore-to-card on close in frontend/src/components/agents/AgentInlineEditor.tsx
- [x] T059 [P] [US3] Verify focus restoration to triggering element on close for AddAgentModal in frontend/src/components/agents/AddAgentModal.tsx
- [x] T060 [P] [US3] Verify focus restoration to triggering element on close for AgentIconPickerModal in frontend/src/components/agents/AgentIconPickerModal.tsx

#### Contrast and Keyboard

- [x] T061 [US3] Verify all `text-muted-foreground` and opacity-reduced text meets WCAG AA 4.5:1 contrast ratio against backgrounds across all Agents page components
- [x] T062 [US3] Verify Escape key closes all dropdowns and modals (AddAgentPopover, AgentPresetSelector dropdown, AddAgentModal, AgentIconPickerModal, BulkModelUpdateDialog)
- [x] T063 [US3] Run existing tests (`npx vitest run`) to verify no regressions from US3 changes

**Checkpoint**: User Story 3 complete — Agents page meets WCAG AA accessibility standards

---

## Phase 6: User Story 4 — Responsive Layout Across Screen Sizes (Priority: P2)

**Goal**: Verify and fix responsive behavior at desktop (1280px+), tablet (768px–1279px), and mobile (<768px) breakpoints — no horizontal scrolling, overlapping elements, or truncated content

**Independent Test**: Resize browser window to desktop, tablet, and mobile breakpoints — verify agent catalog and column assignments panels, agent card grid, modals, and inline editors reflow correctly.

### Implementation for User Story 4

- [x] T064 [P] [US4] Verify two-panel grid layout (`xl:grid-cols-[minmax(0,1fr)_22rem]`) stacks correctly below xl breakpoint in frontend/src/pages/AgentsPage.tsx
- [x] T065 [P] [US4] Verify agent card grid (`md:grid-cols-2 xl:grid-cols-3`) has no overflow at each breakpoint in frontend/src/components/agents/AgentsPanel.tsx
- [x] T066 [P] [US4] Add `overflow-x-auto` wrapper to Orbital Map dynamic grid (`gridTemplateColumns: repeat(...)`) for small screens in frontend/src/components/board/AgentConfigRow.tsx
- [x] T067 [P] [US4] Verify inline editor grid (`xl:grid-cols-[minmax(0,1.2fr)_minmax(20rem,0.8fr)]`) collapses correctly on smaller screens in frontend/src/components/agents/AgentInlineEditor.tsx
- [x] T068 [P] [US4] Verify modals (AddAgentModal, AgentIconPickerModal, BulkModelUpdateDialog) display full-width on mobile screens in frontend/src/components/agents/
- [x] T069 [P] [US4] Verify icon selection grid (`grid-cols-2 sm:grid-cols-3 lg:grid-cols-4`) renders correctly at all breakpoints in frontend/src/components/agents/AgentIconCatalog.tsx
- [x] T070 [P] [US4] Verify touch targets are minimum 44×44px on interactive elements on mobile — audit buttons, icon selectors, and tile controls in frontend/src/components/agents/ and frontend/src/components/board/
- [x] T071 [P] [US4] Verify AgentPresetSelector dropdown positioning doesn't go off-screen on narrow viewports in frontend/src/components/board/AgentPresetSelector.tsx
- [x] T072 [P] [US4] Verify AddAgentPopover portal positioning doesn't overflow viewport on narrow screens in frontend/src/components/board/AddAgentPopover.tsx
- [x] T073 [US4] Verify smooth layout transitions when resizing browser across breakpoints — no broken intermediate states
- [x] T074 [US4] Verify content remains readable and usable at 200% browser zoom with no horizontal scroll
- [x] T075 [US4] Run existing tests (`npx vitest run`) to verify no regressions from US4 changes

**Checkpoint**: User Story 4 complete — Agents page is fully responsive across desktop, tablet, and mobile

---

## Phase 7: User Story 5 — Well-Functioning Interactive Elements (Priority: P2)

**Goal**: Verify all interactive elements work correctly with proper visual feedback — buttons show hover/focus/loading states, modals open/close correctly, search filters in real time, drag-and-drop operates smoothly

**Independent Test**: Exercise every interactive element on the page (create agent, edit inline, delete agent, pick icon, search catalog, bulk update models, assign agents to columns, apply presets) — each produces correct result with appropriate feedback.

### Implementation for User Story 5

- [x] T076 [P] [US5] Verify Add Agent button → modal open → form validation → save → success flow with loading spinner during processing in frontend/src/components/agents/AddAgentModal.tsx
- [x] T077 [P] [US5] Verify edit button → inline editor opens → save/discard controls → success feedback flow in frontend/src/components/agents/AgentInlineEditor.tsx
- [x] T078 [P] [US5] Verify delete button → confirmation dialog → confirm/cancel → success/error feedback flow in frontend/src/components/agents/AgentCard.tsx
- [x] T079 [P] [US5] Verify search field filters agents in real time with no lag or layout shift (useDeferredValue) in frontend/src/components/agents/AgentsPanel.tsx
- [x] T080 [P] [US5] Verify sort toggle (name/usage) works correctly in frontend/src/components/agents/AgentsPanel.tsx
- [x] T081 [P] [US5] Verify icon picker modal → select icon → save flow with loading state in frontend/src/components/agents/AgentIconPickerModal.tsx
- [x] T082 [P] [US5] Verify bulk model update dialog → select model → review affected agents → confirm flow in frontend/src/components/agents/BulkModelUpdateDialog.tsx
- [x] T083 [P] [US5] Verify column assignments — add agent via popover → drag reorder → clone → remove → save/discard flow in frontend/src/components/board/AgentConfigRow.tsx
- [x] T084 [P] [US5] Verify preset selector — apply preset → confirmation → apply with dirty state tracking in frontend/src/components/board/AgentPresetSelector.tsx
- [x] T085 [P] [US5] Verify saved pipelines dropdown — open → select → confirmation → apply flow in frontend/src/components/board/AgentPresetSelector.tsx
- [x] T086 [P] [US5] Verify all buttons show hover states and loading spinners during async processing across all Agents page components
- [x] T087 [P] [US5] Verify unsaved changes mechanism blocks navigation with confirmation prompt when inline editor has pending changes in frontend/src/components/agents/AgentInlineEditor.tsx via useUnsavedChanges hook
- [x] T088 [P] [US5] Verify unsaved column assignment changes trigger warning before project switching in frontend/src/pages/AgentsPage.tsx
- [x] T089 [US5] Run existing tests (`npx vitest run`) to verify no regressions from US5 changes

**Checkpoint**: User Story 5 complete — all interactive elements function correctly with proper feedback

---

## Phase 8: User Story 6 — Performance and Code Quality (Priority: P3)

**Goal**: Audit component structure for best practices, verify no unnecessary re-renders, confirm data-fetching patterns follow caching strategies, and ensure clean code quality

**Independent Test**: Profile page with React DevTools — no unnecessary re-renders observed. Inspect network tab — no duplicate/redundant API requests. Verify page remains responsive with 50+ agents.

### Implementation for User Story 6

- [x] T090 [P] [US6] Review component boundaries in AgentsPanel for single responsibility — verify child components don't have overlapping concerns in frontend/src/components/agents/AgentsPanel.tsx
- [x] T091 [P] [US6] Verify AgentCard does not re-render when sibling cards change (stable references, memoization) in frontend/src/components/agents/AgentCard.tsx
- [x] T092 [P] [US6] Verify `useMemo` dependency arrays are correct in AgentConfigRow constellation SVG computation in frontend/src/components/board/AgentConfigRow.tsx
- [x] T093 [P] [US6] Verify AgentPresetSelector dropdown state changes don't trigger grid re-renders in frontend/src/components/board/AgentPresetSelector.tsx
- [x] T094 [P] [US6] Verify `useDeferredValue` prevents layout shift during search in frontend/src/components/agents/AgentsPanel.tsx
- [x] T095 [P] [US6] Verify no duplicate API requests during normal navigation — check `staleTime` values on TanStack Query hooks in frontend/src/hooks/useAgents.ts and frontend/src/hooks/useAgentConfig.ts
- [x] T096 [P] [US6] Verify data fetching handles rapid project switching via TanStack Query request cancellation in frontend/src/pages/AgentsPage.tsx
- [x] T097 [P] [US6] Review AgentInlineEditor for form submission pattern — consider adding `<form onSubmit>` for Enter key support in frontend/src/components/agents/AgentInlineEditor.tsx
- [x] T098 [P] [US6] Verify AgentDragOverlay width constraints (`min-w-[280px] max-w-[340px]`) are consistent with design scale in frontend/src/components/board/AgentDragOverlay.tsx
- [x] T099 [US6] Run existing tests (`npx vitest run`) to verify no regressions from US6 changes

**Checkpoint**: User Story 6 complete — code quality and performance meet project standards

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, audit summary, and deferred improvements documentation

- [x] T100 [P] Run full test suite (`npx vitest run`), type-check (`npm run type-check`), and lint (`npm run lint`) to confirm zero regressions in frontend/
- [x] T101 [P] Verify all changes work correctly in both light and dark modes across all modified components
- [x] T102 Produce audit summary document listing all findings, changes made, and deferred improvements per FR-014 in spec.md
- [x] T103 Run quickstart.md validation — verify all checklist items from specs/035-audit-agents-page/quickstart.md are addressed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories (establishes audit inventory)
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) — visual token fixes
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) — can run parallel with US1
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2) — can run parallel with US1/US2
- **User Story 4 (Phase 6)**: Depends on Foundational (Phase 2) — can run parallel with US1/US2/US3
- **User Story 5 (Phase 7)**: Depends on US1 + US2 (visual and state fixes must be done before verifying interactions)
- **User Story 6 (Phase 8)**: Depends on US1 through US5 (all functional changes must be complete before performance/quality review)
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 — No dependencies on other stories
- **User Story 2 (P1)**: Can start after Phase 2 — Independent of US1, can run in parallel
- **User Story 3 (P2)**: Can start after Phase 2 — Independent of US1/US2, can run in parallel
- **User Story 4 (P2)**: Can start after Phase 2 — Independent of US1/US2/US3, can run in parallel
- **User Story 5 (P2)**: Depends on US1 + US2 — visual/state fixes should be done before verifying interactions
- **User Story 6 (P3)**: Depends on US1–US5 — all changes should be complete before code quality audit

### Within Each User Story

- Parallel [P] tasks can be worked on simultaneously (they target different files)
- Non-[P] tasks (verification, test runs) should be done after all [P] tasks in that story
- Each story's final task is always a test run to verify no regressions

### Parallel Opportunities

- All Foundational tasks (T004–T007) marked [P] can run in parallel
- US1 tasks T008–T017 target different files and can run in parallel
- US2 tasks T020–T032 target different files and can run in parallel
- US3 focus indicator tasks (T034–T039) can run in parallel
- US3 ARIA tasks (T040–T052) can run in parallel
- US3 focus management tasks (T053–T060) can run in parallel
- US4 tasks T064–T072 target different files and can run in parallel
- US5 tasks T076–T088 target different files and can run in parallel
- US6 tasks T090–T098 target different files and can run in parallel
- **Cross-story parallelism**: US1, US2, US3, US4 can all be worked on simultaneously by different developers

---

## Parallel Example: User Story 1

```bash
# Launch all visual token fix tasks together (all target different files):
Task T008: "Replace emerald badge colors in AgentsPanel.tsx"
Task T009: "Replace green success colors in AgentCard.tsx"
Task T010: "Replace source badge colors in AddAgentPopover.tsx"
Task T011: "Replace SVG inline colors in AgentTile.tsx"
Task T012: "Normalize amber colors in AddAgentModal.tsx and AgentInlineEditor.tsx"
Task T013: "Verify status badge consistency in AgentCard.tsx"
Task T014: "Verify source badge consistency in AgentCard.tsx and AddAgentPopover.tsx"
Task T015: "Verify icon consistency across agents/ and board/"
Task T016: "Verify gradient/shadow alignment in AgentsPanel.tsx and AgentCard.tsx"
Task T017: "Verify font usage in AgentsPage.tsx"
```

## Parallel Example: User Story 3

```bash
# Launch all ARIA role tasks together (all target different files):
Task T040: "Fix role in AgentIconPickerModal.tsx"
Task T041: "Add role/aria-live to AgentSaveBar.tsx"
Task T042: "Add role/aria-label to AgentConfigRow.tsx"
Task T043: "Add role='list' to AgentColumnCell.tsx"
Task T044: "Add role='listitem' to AgentTile.tsx"
Task T045: "Add aria-expanded to AddAgentPopover.tsx"
Task T046: "Add aria-expanded to AgentPresetSelector.tsx"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (verify baseline)
2. Complete Phase 2: Foundational (audit inventory)
3. Complete Phase 3: User Story 1 — visual consistency (P1)
4. Complete Phase 4: User Story 2 — bug-free states (P1)
5. **STOP and VALIDATE**: Run full test suite, check light/dark mode, verify all states
6. Deploy/demo if ready — page is visually polished and state-complete

### Incremental Delivery

1. Complete Setup + Foundational → Audit baseline established
2. Add User Story 1 (visual tokens) → Test independently → visual consistency achieved
3. Add User Story 2 (page states) → Test independently → all states bug-free
4. Add User Story 3 (accessibility) → Test independently → WCAG AA compliant
5. Add User Story 4 (responsive) → Test independently → responsive across breakpoints
6. Add User Story 5 (interactions) → Test independently → all interactions verified
7. Add User Story 6 (performance) → Test independently → code quality audit complete
8. Polish phase → Final validation and audit summary

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (visual tokens)
   - Developer B: User Story 2 (page states)
   - Developer C: User Story 3 (accessibility)
   - Developer D: User Story 4 (responsive)
3. After A + B complete → Developer E: User Story 5 (interactions)
4. After all complete → Developer F: User Story 6 (performance/quality)
5. Final → Polish phase

---

## Notes

- [P] tasks = different files, no dependencies — safe for parallel execution
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- No new tests are required unless accessibility scanning reveals gaps
- Existing tests (AgentSaveBar, AgentTile, ThemedAgentIcon) must pass after each phase
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- This is a frontend-only audit — no backend changes required
- All ~20 components in scope are under `frontend/src/components/agents/`, `frontend/src/components/board/`, and `frontend/src/pages/AgentsPage.tsx`
