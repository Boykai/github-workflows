# Tasks: Deep UX/UI Review, Polish & Meaningful Frontend Test Coverage

**Input**: Design documents from `/specs/014-ux-ui-review-testing/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/audit-standards.md, quickstart.md

**Tests**: Explicitly requested in the feature specification (FR-003, FR-010). All test tasks are included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. 6 user stories (3× P1, 2× P2, 1× P3) mapped from spec.md.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- All paths are relative to repository root
- Test files co-located with source: `ComponentName.test.tsx` next to `ComponentName.tsx`
- E2E tests in `frontend/e2e/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install new dependencies and configure shared tooling required by all user stories

- [ ] T001 Install `eslint-plugin-jsx-a11y` as devDependency in `frontend/package.json`
- [ ] T002 Install `jest-axe` and `@types/jest-axe` as devDependencies in `frontend/package.json` for automated accessibility assertions
- [ ] T003 [P] Configure `eslint-plugin-jsx-a11y` recommended rules in `frontend/eslint.config.js`
- [ ] T004 [P] Create accessibility test helper with `toHaveNoViolations` matcher in `frontend/src/test/a11y-helpers.ts`
- [ ] T005 [P] Create findings log template at `frontend/docs/findings-log.md` with columns: ID, category, severity, affected_view, affected_component, description, expected_behavior, status, regression_test, requirement_ref

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared test infrastructure and audit utilities that MUST be complete before any user story work begins

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Add Playwright viewport preset constants (mobile: 375×667, tablet: 768×1024, desktop: 1280×800) in `frontend/e2e/viewports.ts`
- [ ] T007 [P] Create shared component render helper for a11y testing that wraps `renderWithProviders` with axe-core assertion in `frontend/src/test/a11y-helpers.ts`
- [ ] T008 [P] Add `test:a11y` npm script to `frontend/package.json` that runs vitest with a11y test file pattern

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 — Visual Consistency & Interactive Element Audit (Priority: P1) 🎯 MVP

**Goal**: Audit every customer-facing view for visual consistency (typography, color, spacing, iconography) and verify all interactive elements have correct hover, focus, active, and disabled states with accessible focus indicators. Centralize any remaining hardcoded design tokens.

**Independent Test**: Navigate every customer-facing view, inspect each UI component against design system standards from `contracts/audit-standards.md`, verify interactive states via keyboard and mouse. Confirm all design tokens centralized in `frontend/src/index.css` with no hardcoded inline values.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Write integration test for Button component interactive states (hover, focus, active, disabled) in `frontend/src/components/ui/button.test.tsx`
- [ ] T010 [P] [US1] Write integration test for Input component interactive states (focus, disabled, placeholder) in `frontend/src/components/ui/input.test.tsx`
- [ ] T011 [P] [US1] Write integration test for Card component rendering and visual structure in `frontend/src/components/ui/card.test.tsx`
- [ ] T012 [P] [US1] Write integration test for IssueCard interactive states (hover, keyboard activation via Enter/Space) in `frontend/src/components/board/IssueCard.test.tsx`
- [ ] T013 [P] [US1] Write integration test for IssueDetailModal open/close and keyboard dismiss in `frontend/src/components/board/IssueDetailModal.test.tsx`

### Implementation for User Story 1

- [ ] T014 [P] [US1] Audit all UI primitives (button, card, input) in `frontend/src/components/ui/` for design token compliance — no hardcoded hex/rgb/hsl values, all colors via Tailwind classes
- [ ] T015 [P] [US1] Audit all board components (11 files) in `frontend/src/components/board/` for visual consistency — typography scale, spacing, icon sizing, color token usage
- [ ] T016 [P] [US1] Audit all chat components (6 files) in `frontend/src/components/chat/` for visual consistency — typography, spacing, icon sizing, color token usage
- [ ] T017 [P] [US1] Audit all settings components (12 files) in `frontend/src/components/settings/` for visual consistency — typography, spacing, icon sizing, color token usage
- [ ] T018 [P] [US1] Audit auth and common components in `frontend/src/components/auth/LoginButton.tsx` and `frontend/src/components/common/ErrorBoundary.tsx` for visual consistency
- [ ] T019 [US1] Verify all interactive elements in `frontend/src/components/board/` have correct hover (`hover:bg-*`), focus (`focus-visible:ring-2`), active, and disabled (`disabled:opacity-50`) states per `contracts/audit-standards.md`
- [ ] T020 [US1] Verify all interactive elements in `frontend/src/components/chat/ChatInterface.tsx` and `frontend/src/components/chat/ChatPopup.tsx` have correct hover, focus, active, and disabled states
- [ ] T021 [US1] Verify all interactive elements in `frontend/src/components/settings/` (dropdowns, inputs, save buttons) have correct hover, focus, active, and disabled states
- [ ] T022 [US1] Fix any hardcoded style values found during audit — replace with Tailwind utility classes referencing design tokens from `frontend/src/index.css`
- [ ] T023 [US1] Verify Lucide React icon consistency across all components — decorative icons have `aria-hidden="true"`, consistent sizing (`h-4 w-4` inline, `h-5 w-5` buttons)
- [ ] T024 [US1] Log all User Story 1 findings in `frontend/docs/findings-log.md` with severity ratings and requirement refs (FR-001, FR-002, FR-008)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently — all views visually consistent, interactive states correct, design tokens centralized

---

## Phase 4: User Story 2 — Accessibility Compliance & UI State Handling (Priority: P1)

**Goal**: Achieve WCAG AA accessibility compliance on all customer-facing views (color contrast, keyboard nav, ARIA) and ensure every data-driven component handles loading, empty, error, and success states with clear user feedback.

**Independent Test**: Run automated axe-core accessibility audit on every customer-facing view. Manually trigger each UI state (loading, empty, error, success) in data-fetching components and verify correct rendering and user feedback.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T025 [P] [US2] Write accessibility assertion test for ProjectBoardPage using axe-core in `frontend/src/pages/ProjectBoardPage.test.tsx`
- [ ] T026 [P] [US2] Write accessibility assertion test for SettingsPage using axe-core in `frontend/src/pages/SettingsPage.test.tsx`
- [ ] T027 [P] [US2] Write accessibility assertion test for App root (Home view) using axe-core in `frontend/src/App.test.tsx`
- [ ] T028 [P] [US2] Write integration test for DynamicDropdown loading/empty/error/success states in `frontend/src/components/settings/DynamicDropdown.test.tsx`
- [ ] T029 [P] [US2] Write integration test for McpSettings loading/empty/error/success states in `frontend/src/components/settings/McpSettings.test.tsx`
- [ ] T030 [P] [US2] Write integration test for ChatInterface loading/empty/sending states in `frontend/src/components/chat/ChatInterface.test.tsx`
- [ ] T031 [P] [US2] Write integration test for BoardColumn empty state rendering in `frontend/src/components/board/BoardColumn.test.tsx`

### Implementation for User Story 2

- [ ] T032 [P] [US2] Audit color contrast ratios across all theme tokens in `frontend/src/index.css` (light and dark modes) — verify minimum 4.5:1 for normal text, 3:1 for large text
- [ ] T033 [P] [US2] Audit keyboard navigability on ProjectBoardPage — verify all interactive elements reachable via Tab, custom interactive divs have `role="button"` + `tabIndex={0}` + `onKeyDown`
- [ ] T034 [P] [US2] Audit keyboard navigability on SettingsPage — verify all form inputs, dropdowns, toggles, and save buttons are keyboard-accessible
- [ ] T035 [US2] Audit ARIA attributes across all components — verify `aria-label` on icon-only buttons, `aria-hidden="true"` on decorative elements, `aria-live` on dynamic status regions, `aria-expanded` on collapsible sections
- [ ] T036 [US2] Verify semantic HTML across all pages — heading hierarchy (h1→h2→h3), `<nav>` landmarks, `<main>` landmark, `<label>` elements on form inputs
- [ ] T037 [US2] Audit loading state handling in all data-fetching components — verify clear loading indicators in `McpSettings.tsx`, `DynamicDropdown.tsx`, `ChatInterface.tsx`, `ProjectBoard.tsx`
- [ ] T038 [US2] Audit empty state handling — verify meaningful empty messages in `McpSettings.tsx`, `ChatInterface.tsx`, `BoardColumn.tsx`
- [ ] T039 [US2] Audit error state handling — verify error messages with retry options in `McpSettings.tsx`, `DynamicDropdown.tsx`, `SettingsSection.tsx`
- [ ] T040 [US2] Audit success state handling — verify success feedback in `McpSettings.tsx`, `SettingsSection.tsx` with auto-dismiss behavior
- [ ] T041 [US2] Fix any accessibility or UI state issues discovered during audit — update component files as needed
- [ ] T042 [US2] Log all User Story 2 findings in `frontend/docs/findings-log.md` with severity ratings and requirement refs (FR-004, FR-005)

**Checkpoint**: At this point, User Story 2 should be fully functional and testable independently — all views WCAG AA compliant, all UI states handled correctly

---

## Phase 5: User Story 3 — Form Validation & Content Integrity (Priority: P1)

**Goal**: Ensure all forms display inline validation messages for required fields, format errors, and submission failures without full-page reloads. Eliminate any placeholder/lorem ipsum copy, broken images, or console errors from customer-facing views.

**Independent Test**: Submit each form with invalid data and verify inline error messages appear without page reload. Scan every customer-facing view for placeholder text, broken images, and console errors.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T043 [P] [US3] Write integration test for McpSettings form validation (required name, URL format) and submission error handling in `frontend/src/components/settings/McpSettings.test.tsx`
- [ ] T044 [P] [US3] Write integration test for AgentConfigRow save/discard flow and dirty state tracking in `frontend/src/components/board/AgentConfigRow.test.tsx`
- [ ] T045 [P] [US3] Write integration test for GlobalSettings numeric input validation (min/max/step constraints) in `frontend/src/components/settings/GlobalSettings.test.tsx`
- [ ] T046 [P] [US3] Write integration test for ChatInterface form submission (empty message prevention, submit via Enter key) in `frontend/src/components/chat/ChatInterface.test.tsx`

### Implementation for User Story 3

- [ ] T047 [US3] Audit MCP Settings form (`frontend/src/components/settings/McpSettings.tsx`) — verify inline validation on name/URL fields, error clearing on correction, `preventDefault()` on submit
- [ ] T048 [US3] Audit Agent Config form (`frontend/src/components/board/AgentConfigRow.tsx`) — verify save/discard workflow, dirty state tracking, confirmation for destructive operations
- [ ] T049 [US3] Audit Global Settings form (`frontend/src/components/settings/GlobalSettings.tsx`) — verify numeric input constraints, dropdown validation, inline error messages
- [ ] T050 [US3] Audit Chat Input form (`frontend/src/components/chat/ChatInterface.tsx`) — verify `preventDefault()`, disabled state during sending, empty message prevention
- [ ] T051 [US3] Verify all form error messages follow the standard from `contracts/audit-standards.md` — field-level errors below input with `aria-describedby`, form-level errors with `role="alert"`
- [ ] T052 [US3] Scan all customer-facing views for placeholder/lorem ipsum text — inspect `ProjectBoardPage.tsx`, `SettingsPage.tsx`, `App.tsx`, and all rendered components
- [ ] T053 [US3] Scan all customer-facing views for broken images — verify all `<img>` tags have valid `src` and `alt` attributes, verify fallback states for failed image loads
- [ ] T054 [US3] Verify no console errors in customer-facing views — check for unhandled promise rejections, missing key props, invalid DOM nesting
- [ ] T055 [US3] Fix any form validation or content integrity issues discovered during audit
- [ ] T056 [US3] Log all User Story 3 findings in `frontend/docs/findings-log.md` with severity ratings and requirement refs (FR-006, FR-007)

**Checkpoint**: At this point, User Story 3 should be fully functional and testable independently — all forms validate inline, no placeholder content or console errors

---

## Phase 6: User Story 4 — Meaningful Automated Test Coverage for Critical User Flows (Priority: P2)

**Goal**: Add meaningful automated tests (integration and E2E) covering all critical user flows using behavior-driven approach. Use `getByRole`/`getByLabelText` over test IDs. Add regression tests for every bug fixed during the US1–US3 audit.

**Independent Test**: Run the automated test suite and verify that navigation, form submission, data display, authentication, and real-time sync flows are covered. Verify tests use behavior-driven queries.

### Tests for User Story 4

- [ ] T057 [P] [US4] Write integration test for ProjectBoardPage — project selection, board column display, issue card rendering in `frontend/src/pages/ProjectBoardPage.test.tsx`
- [ ] T058 [P] [US4] Write integration test for SettingsPage — section navigation, settings form interaction, save/cancel flow in `frontend/src/pages/SettingsPage.test.tsx`
- [ ] T059 [P] [US4] Write integration test for ChatPopup — open/close, message sending, response rendering in `frontend/src/components/chat/ChatPopup.test.tsx`
- [ ] T060 [P] [US4] Write integration test for MessageBubble — user vs assistant message rendering, markdown content in `frontend/src/components/chat/MessageBubble.test.tsx`
- [ ] T061 [P] [US4] Write integration test for IssueRecommendationPreview — confirm/reject workflow in `frontend/src/components/chat/IssueRecommendationPreview.test.tsx`
- [ ] T062 [P] [US4] Write integration test for TaskPreview — task proposal display and confirmation in `frontend/src/components/chat/TaskPreview.test.tsx`
- [ ] T063 [P] [US4] Write integration test for StatusChangePreview — status change confirmation in `frontend/src/components/chat/StatusChangePreview.test.tsx`
- [ ] T064 [P] [US4] Write integration test for ProjectBoard — column rendering, drag-and-drop context setup in `frontend/src/components/board/ProjectBoard.test.tsx`
- [ ] T065 [P] [US4] Write integration test for SettingsSection — save state lifecycle (idle→saving→success/error) and auto-dismiss in `frontend/src/components/settings/SettingsSection.test.tsx`
- [ ] T066 [P] [US4] Write integration test for PrimarySettings — user/project settings display and update in `frontend/src/components/settings/PrimarySettings.test.tsx`
- [ ] T067 [P] [US4] Write integration test for SignalConnection — connection status display and phone number management in `frontend/src/components/settings/SignalConnection.test.tsx`
- [ ] T068 [P] [US4] Write integration test for DisplayPreferences — theme toggle interaction in `frontend/src/components/settings/DisplayPreferences.test.tsx`
- [ ] T069 [P] [US4] Write integration test for ThemeProvider — light/dark/system theme switching and localStorage persistence in `frontend/src/components/ThemeProvider.test.tsx`
- [ ] T070 [P] [US4] Write integration test for AgentPresetSelector — preset selection and agent configuration in `frontend/src/components/board/AgentPresetSelector.test.tsx`
- [ ] T071 [P] [US4] Write integration test for AgentTile — agent display and action triggers in `frontend/src/components/board/AgentTile.test.tsx`
- [ ] T072 [P] [US4] Write integration test for AddAgentPopover — popover open/close and agent addition in `frontend/src/components/board/AddAgentPopover.test.tsx`
- [ ] T073 [P] [US4] Write integration test for AgentSaveBar — save/discard visibility and actions in `frontend/src/components/board/AgentSaveBar.test.tsx`
- [ ] T074 [P] [US4] Write integration test for AgentColumnCell — column agent display and edit trigger in `frontend/src/components/board/AgentColumnCell.test.tsx`

### E2E Tests for User Story 4

- [ ] T075 [P] [US4] Write Playwright E2E test for board navigation flow — load app, select project, view columns, click issue card, view detail modal in `frontend/e2e/board-navigation.spec.ts`
- [ ] T076 [P] [US4] Write Playwright E2E test for settings flow — navigate to settings, change a setting, verify save/success feedback in `frontend/e2e/settings-flow.spec.ts`
- [ ] T077 [P] [US4] Write Playwright E2E test for chat interaction flow — open chat, send message, verify response display in `frontend/e2e/chat-interaction.spec.ts`

### Regression Tests for User Story 4

- [ ] T078 [US4] Add regression tests for all critical/major bugs fixed during US1–US3 audit — one test per fix, co-located with the fixed component

**Checkpoint**: At this point, User Story 4 should be fully functional and testable independently — all critical user flows covered by automated tests with behavior-driven queries

---

## Phase 7: User Story 5 — Responsive Layout Review (Priority: P2)

**Goal**: Review and fix responsive layouts across mobile (≤768px), tablet (769–1024px), and desktop (≥1025px) breakpoints on all customer-facing views. Ensure no overflow, overlap, or broken elements.

**Independent Test**: Resize browser to each breakpoint and verify all content is visible, readable, and no elements overflow or overlap on every customer-facing view.

### Tests for User Story 5

- [ ] T079 [P] [US5] Write Playwright E2E test for ProjectBoardPage responsive layout at mobile/tablet/desktop viewports using viewport presets from `frontend/e2e/viewports.ts` in `frontend/e2e/responsive-board.spec.ts`
- [ ] T080 [P] [US5] Write Playwright E2E test for SettingsPage responsive layout at mobile/tablet/desktop viewports in `frontend/e2e/responsive-settings.spec.ts`
- [ ] T081 [P] [US5] Write Playwright E2E test for Home/App view responsive layout at mobile/tablet/desktop viewports in `frontend/e2e/responsive-home.spec.ts`

### Implementation for User Story 5

- [ ] T082 [US5] Audit ProjectBoardPage layout at mobile (≤768px) — verify board columns stack or scroll horizontally, issue cards are readable, modals are full-width
- [ ] T083 [US5] Audit ProjectBoardPage layout at tablet (769–1024px) — verify columns fit without overflow, sidebar collapses appropriately
- [ ] T084 [US5] Audit SettingsPage layout at mobile (≤768px) — verify settings sections stack vertically, form inputs are full-width, dropdowns don't overflow
- [ ] T085 [US5] Audit SettingsPage layout at tablet (769–1024px) — verify sidebar/main layout adapts, no content clipping
- [ ] T086 [US5] Audit ChatPopup responsive behavior — verify chat popup is usable and doesn't overflow at mobile viewport in `frontend/src/components/chat/ChatPopup.tsx`
- [ ] T087 [US5] Fix any responsive layout issues discovered — update Tailwind responsive classes (`sm:`, `md:`, `lg:`) in affected component files
- [ ] T088 [US5] Log all User Story 5 findings in `frontend/docs/findings-log.md` with severity ratings and requirement ref (FR-009)

**Checkpoint**: At this point, User Story 5 should be fully functional and testable independently — all views render correctly at all breakpoints

---

## Phase 8: User Story 6 — Performance Audit & Findings Documentation (Priority: P3)

**Goal**: Audit page-level performance indicators (LCP, CLS, INP) on all customer-facing views, flag views with poor Core Web Vitals, and compile the complete structured findings log with all issues from all user stories.

**Independent Test**: Run performance audit on every customer-facing view, verify LCP/CLS/INP scores are measured, verify findings log exists with severity-rated entries for all discovered issues.

### Implementation for User Story 6

- [ ] T089 [P] [US6] Run Lighthouse performance audit on Home page and record LCP, CLS, INP scores in `frontend/docs/findings-log.md`
- [ ] T090 [P] [US6] Run Lighthouse performance audit on Project Board page and record LCP, CLS, INP scores in `frontend/docs/findings-log.md`
- [ ] T091 [P] [US6] Run Lighthouse performance audit on Settings page and record LCP, CLS, INP scores in `frontend/docs/findings-log.md`
- [ ] T092 [US6] Analyze frontend bundle size via `npm run build` — check `frontend/dist/assets/` for large chunks, identify optimization opportunities (lazy loading, code splitting)
- [ ] T093 [US6] Flag any views with poor Core Web Vitals (LCP > 2.5s, INP > 200ms, CLS > 0.1) and document recommended fixes in `frontend/docs/findings-log.md`
- [ ] T094 [US6] Compile final findings log in `frontend/docs/findings-log.md` — verify every entry has ID, category, severity, affected view/component, description, expected behavior, status, requirement ref
- [ ] T095 [US6] Verify all critical and major findings from the log are resolved (status: `fixed` or `wont-fix` with rationale)

**Checkpoint**: At this point, User Story 6 should be complete — all performance scores documented, findings log comprehensive and finalized

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories, final validation, and cleanup

- [ ] T096 [P] Verify `eslint-plugin-jsx-a11y` rules pass across entire `frontend/src/` codebase — run `npm run lint` and fix remaining violations
- [ ] T097 [P] Verify all new tests pass — run `npm test` in `frontend/` and confirm zero failures
- [ ] T098 Run Playwright E2E test suite — run `npm run test:e2e` in `frontend/` and confirm zero failures
- [ ] T099 [P] Verify TypeScript compilation — run `npm run type-check` in `frontend/` and confirm zero errors
- [ ] T100 [P] Verify production build — run `npm run build` in `frontend/` and confirm successful build with no warnings
- [ ] T101 Review findings log completeness — every finding has a severity rating, every fixed finding has a regression test path, every `wont-fix` has rationale
- [ ] T102 Run quickstart.md validation — execute all commands from `specs/014-ux-ui-review-testing/quickstart.md` and verify they succeed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) completion — BLOCKS all user stories
- **User Stories (Phases 3–8)**: All depend on Foundational (Phase 2) completion
  - P1 stories (US1, US2, US3) can proceed in parallel or sequentially
  - P2 stories (US4, US5) can start after P1 stories or in parallel if team allows
  - P3 story (US6) should start after P1/P2 to capture all findings
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 — No dependencies on other stories
- **User Story 2 (P1)**: Can start after Phase 2 — No dependencies on other stories; benefits from US1 design token fixes but not blocked by them
- **User Story 3 (P1)**: Can start after Phase 2 — No dependencies on other stories
- **User Story 4 (P2)**: Best started after US1–US3 to write regression tests for discovered bugs (T078); E2E tests can start in parallel
- **User Story 5 (P2)**: Can start after Phase 2 — Independent of other stories
- **User Story 6 (P3)**: Should start after US1–US5 to compile comprehensive findings log; performance audit can start independently

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Audit/review tasks before fix tasks
- Fixes before findings log documentation
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T003, T004, T005)
- All Foundational tasks marked [P] can run in parallel (T007, T008)
- Once Foundational phase completes, US1, US2, and US3 can start in parallel
- All tests within a user story marked [P] can run in parallel
- All audit tasks within US1 marked [P] can run in parallel (T014–T018)
- All US4 integration tests marked [P] can run in parallel (T057–T074)
- All US4 E2E tests marked [P] can run in parallel (T075–T077)
- US5 Playwright tests marked [P] can run in parallel (T079–T081)
- US6 Lighthouse audits marked [P] can run in parallel (T089–T091)

---

## Parallel Example: User Story 1

```bash
# Launch all US1 tests together (all [P] — different files):
Task: "Write integration test for Button interactive states in frontend/src/components/ui/button.test.tsx"
Task: "Write integration test for Input interactive states in frontend/src/components/ui/input.test.tsx"
Task: "Write integration test for Card rendering in frontend/src/components/ui/card.test.tsx"
Task: "Write integration test for IssueCard interactive states in frontend/src/components/board/IssueCard.test.tsx"
Task: "Write integration test for IssueDetailModal in frontend/src/components/board/IssueDetailModal.test.tsx"

# Launch all US1 audit tasks together (all [P] — different component categories):
Task: "Audit UI primitives in frontend/src/components/ui/"
Task: "Audit board components in frontend/src/components/board/"
Task: "Audit chat components in frontend/src/components/chat/"
Task: "Audit settings components in frontend/src/components/settings/"
Task: "Audit auth and common components"
```

## Parallel Example: User Story 4

```bash
# Launch all US4 integration tests together (all [P] — different files):
Task: "Write integration test for ProjectBoardPage in frontend/src/pages/ProjectBoardPage.test.tsx"
Task: "Write integration test for SettingsPage in frontend/src/pages/SettingsPage.test.tsx"
Task: "Write integration test for ChatPopup in frontend/src/components/chat/ChatPopup.test.tsx"
Task: "Write integration test for MessageBubble in frontend/src/components/chat/MessageBubble.test.tsx"
# ... (18 parallel test tasks)

# Launch all E2E tests together (all [P] — different spec files):
Task: "Write E2E test for board navigation in frontend/e2e/board-navigation.spec.ts"
Task: "Write E2E test for settings flow in frontend/e2e/settings-flow.spec.ts"
Task: "Write E2E test for chat interaction in frontend/e2e/chat-interaction.spec.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (install deps, configure ESLint, create helpers)
2. Complete Phase 2: Foundational (test infrastructure, viewport presets)
3. Complete Phase 3: User Story 1 — Visual Consistency & Interactive States
4. **STOP and VALIDATE**: Run tests, lint, type-check, build
5. Deploy/demo if ready — visually consistent, interaction-polished application

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Visual Consistency) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (Accessibility & UI States) → Test independently → Deploy/Demo
4. Add User Story 3 (Forms & Content) → Test independently → Deploy/Demo
5. Add User Story 4 (Test Coverage) → Run full test suite → Deploy/Demo
6. Add User Story 5 (Responsive) → Test at all breakpoints → Deploy/Demo
7. Add User Story 6 (Performance & Docs) → Final findings log → Deploy/Demo
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Visual Consistency)
   - Developer B: User Story 2 (Accessibility & UI States)
   - Developer C: User Story 3 (Forms & Content)
3. After P1 stories complete:
   - Developer A: User Story 4 (Test Coverage — benefits from US1–US3 fixes)
   - Developer B: User Story 5 (Responsive)
   - Developer C: User Story 6 (Performance & Documentation)
4. All developers: Phase 9 Polish & final validation

---

## Notes

- [P] tasks = different files, no dependencies — safe to parallelize
- [Story] label maps each task to its specific user story for traceability
- Each user story is independently completable and testable
- Tests use behavior-driven approach: `getByRole` > `getByLabelText` > `getByText` (never `getByTestId` unless justified)
- Snapshot tests used sparingly and only where intentional visual lock-in is desired
- All test infrastructure reuses existing `createMockApi()`, `renderWithProviders()`, and factory functions from `frontend/src/test/`
- axe-core assertions integrated into component tests — no new CI steps required
- Findings log documents every issue with category, severity, affected view, status, and requirement ref
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
