# Tasks: Audit & Update UI Components for Style Consistency

**Input**: Design documents from `/specs/026-ui-style-consistency/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in the feature specification. Existing tests must pass after changes (FR-008: no visual regressions — existing layouts and functionality remain intact). No new test tasks are included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/` (all changes are frontend-only)
- No backend changes. No new features or components. No design system redesign.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add centralized color constants and verify the existing theme token system before auditing or remediating any components.

- [ ] T001 Review and document existing theme tokens in `frontend/src/index.css` — confirm all CSS custom properties (colors, shadows, fonts, radius) are complete and correct per `contracts/style-tokens.md`
- [ ] T002 Add `STATUS_COLORS` constant to `frontend/src/constants.ts` with success/warning/error/info/neutral entries per `data-model.md` schema
- [ ] T003 Add `AGENT_SOURCE_COLORS` constant to `frontend/src/constants.ts` with builtin/custom/community entries per `data-model.md` schema
- [ ] T004 [P] Verify `cn()` utility exists and is correctly implemented in `frontend/src/lib/utils.ts` (clsx + tailwind-merge)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Produce the full component inventory and audit report that gates all remediation work. No code changes — this is an analysis phase.

**⚠️ CRITICAL**: No remediation (User Story 2) can begin until this phase is complete.

- [ ] T005 Inventory all UI components in `frontend/src/components/ui/` (3 files) — document compliance status per `contracts/components.md` rules
- [ ] T006 [P] Inventory all layout components in `frontend/src/layout/` (7 files) — document compliance status and deviations
- [ ] T007 [P] Inventory all page components in `frontend/src/pages/` (8 files) — document compliance status and deviations
- [ ] T008 [P] Inventory all board components in `frontend/src/components/board/` (~27 files) — document compliance status and deviations
- [ ] T009 [P] Inventory all chat components in `frontend/src/components/chat/` (~13 files) — document compliance status and deviations
- [ ] T010 [P] Inventory all agents components in `frontend/src/components/agents/` (~6 files) — document compliance status and deviations
- [ ] T011 [P] Inventory all chores components in `frontend/src/components/chores/` (~5 files) — document compliance status and deviations
- [ ] T012 [P] Inventory all settings components in `frontend/src/components/settings/` (~15 files) — document compliance status and deviations
- [ ] T013 [P] Inventory auth and common components in `frontend/src/components/auth/` (1 file) and `frontend/src/components/common/` (1 file) — document compliance status
- [ ] T014 Compile complete audit report with prioritized remediation list: critical (18 non-compliant), moderate (29 partially compliant), minor (cosmetic) — output as structured markdown

**Checkpoint**: Audit report complete — all 86 components inventoried with compliance status, deviations, and remediation priority documented.

---

## Phase 3: User Story 1 — Complete Component Inventory and Audit (Priority: P1) 🎯 MVP

**Goal**: Deliver a complete, structured audit report documenting every component's compliance status against the design system, with specific deviations noted and remediation priorities assigned.

**Independent Test**: Navigate every page (App, Projects, Pipeline, Agents, Chores, Settings), verify each component is catalogued with pass/fail status. The audit report should list all non-compliant components with specific deviation types (hardcoded-color, missing-cn, inline-style, missing-dark-variant, inconsistent-radius, inconsistent-shadow, deprecated-component).

### Implementation for User Story 1

- [ ] T015 [US1] Capture baseline screenshots of all 6 pages in light mode (App, Projects, Pipeline, Agents, Chores, Settings) for pre-remediation reference
- [ ] T016 [P] [US1] Capture baseline screenshots of all 6 pages in dark mode for pre-remediation reference
- [ ] T017 [US1] Cross-reference each component against theme tokens from `contracts/style-tokens.md` — verify color, typography, spacing, border-radius, and shadow usage
- [ ] T018 [US1] Identify all components using template literals instead of `cn()` for conditional class composition — flag as `missing-cn` deviation type
- [ ] T019 [P] [US1] Identify all components with hardcoded Tailwind color classes that should use `STATUS_COLORS` or `AGENT_SOURCE_COLORS` — flag as `hardcoded-color` deviation type
- [ ] T020 [P] [US1] Identify all components with `style={{}}` inline styles that have Tailwind equivalents — flag as `inline-style` deviation type
- [ ] T021 [P] [US1] Identify all components with explicit light-mode colors missing `dark:` variants — flag as `missing-dark-variant` deviation type
- [ ] T022 [US1] Document all intentional exceptions (arbitrary Tailwind values in `frontend/src/pages/LoginPage.tsx` and `frontend/src/pages/ProjectsPage.tsx`) with rationale per research.md R5
- [ ] T023 [US1] Finalize audit report with component-by-component findings — assign each component a remediation priority (critical, moderate, minor) per `data-model.md` ComponentAuditEntry schema

**Checkpoint**: User Story 1 complete — structured audit report delivered with all 86 components catalogued, deviations documented, and remediation priorities assigned.

---

## Phase 4: User Story 2 — Remediate Non-Compliant Components (Priority: P1)

**Goal**: Update every non-compliant and partially-compliant component to exclusively use theme tokens, `cn()` for class composition, and centralized color constants. All components render correctly in both light and dark modes after update.

**Independent Test**: For each remediated component, verify it uses `cn()` for conditional classes, references `STATUS_COLORS`/`AGENT_SOURCE_COLORS`/`PRIORITY_COLORS` instead of hardcoded colors, has no inline styles with Tailwind equivalents, and renders correctly in both light and dark modes.

### Implementation for User Story 2

#### Critical Remediations (Non-Compliant Components)

- [ ] T024 [US2] Replace inline `style={{ padding: '2rem', textAlign: 'center' }}` with Tailwind classes `className="p-8 text-center"` in `frontend/src/components/common/ErrorBoundary.tsx`
- [ ] T025 [P] [US2] Adopt `cn()` and replace 6+ hardcoded status color patterns with `STATUS_COLORS` constants in `frontend/src/components/settings/SignalConnection.tsx`
- [ ] T026 [P] [US2] Adopt `cn()` and replace hardcoded green/yellow indicator colors with `STATUS_COLORS` constants in `frontend/src/components/settings/McpSettings.tsx`
- [ ] T027 [P] [US2] Replace 8+ identical hardcoded green patterns with `STATUS_COLORS.success` in `frontend/src/components/board/CleanUpSummary.tsx`
- [ ] T028 [P] [US2] Replace repeated green styling with `STATUS_COLORS.success` in `frontend/src/components/board/CleanUpConfirmModal.tsx`
- [ ] T029 [P] [US2] Replace template literal class composition with `cn()` in `frontend/src/components/chat/MessageBubble.tsx`
- [ ] T030 [P] [US2] Replace status ternary chains with `cn()` + centralized constants in `frontend/src/components/board/IssueDetailModal.tsx`
- [ ] T031 [P] [US2] Replace nested ternary color chains with `cn()` + constants in `frontend/src/components/chat/IssueRecommendationPreview.tsx`
- [ ] T032 [P] [US2] Replace source-type ternary chains with `AGENT_SOURCE_COLORS` constant in `frontend/src/components/board/AddAgentPopover.tsx`

#### Board Component Remediations (~15 files)

- [ ] T033 [US2] Adopt `cn()` for conditional classes and centralize priority colors in `frontend/src/components/board/IssueCard.tsx`
- [ ] T034 [P] [US2] Adopt `cn()` for conditional classes in `frontend/src/components/board/ProjectBoard.tsx`
- [ ] T035 [P] [US2] Remediate remaining non-compliant board components in `frontend/src/components/board/` — adopt `cn()` and replace hardcoded colors with theme tokens (files identified in audit report from T014)
- [ ] T036 [US2] Verify all board components in `frontend/src/components/board/` pass type check (`npx tsc --noEmit`) and lint (`npx eslint src/components/board/`)

#### Chat Component Remediations (~8 files)

- [ ] T037 [P] [US2] Adopt `cn()` and align token usage in `frontend/src/components/chat/ChatPopup.tsx`
- [ ] T038 [P] [US2] Remediate remaining non-compliant chat components in `frontend/src/components/chat/` — adopt `cn()` and replace hardcoded colors (files identified in audit report from T014)
- [ ] T039 [US2] Verify all chat components in `frontend/src/components/chat/` pass type check and lint

#### Settings Component Remediations (~10 files)

- [ ] T040 [P] [US2] Remediate remaining non-compliant settings components in `frontend/src/components/settings/` — adopt `cn()` and replace hardcoded colors with `STATUS_COLORS` constants (files identified in audit report from T014)
- [ ] T041 [US2] Verify all settings components in `frontend/src/components/settings/` pass type check and lint

#### Agents Component Remediations (~4 files)

- [ ] T042 [P] [US2] Adopt `cn()` in `frontend/src/components/agents/AddAgentModal.tsx` and remaining agents components
- [ ] T043 [US2] Verify all agents components in `frontend/src/components/agents/` pass type check and lint

#### Chores Component Remediations (~5 files)

- [ ] T044 [P] [US2] Adopt `cn()` for conditional classes in `frontend/src/components/chores/ChoresPanel.tsx`
- [ ] T045 [P] [US2] Remediate remaining non-compliant chores components in `frontend/src/components/chores/` — adopt `cn()` and replace hardcoded colors (files identified in audit report from T014)
- [ ] T046 [US2] Verify all chores components in `frontend/src/components/chores/` pass type check and lint

#### Layout and Page Remediations

- [ ] T047 [P] [US2] Remediate partially-compliant layout components in `frontend/src/layout/` — minor token alignment (2 files identified in audit)
- [ ] T048 [P] [US2] Remediate partially-compliant page components in `frontend/src/pages/` — token alignment (2 files identified in audit, excluding intentional exceptions documented in T022)
- [ ] T049 [US2] Run full frontend build verification: `cd frontend && npm run build && npx tsc --noEmit && npx eslint src/ && npm run test`

**Checkpoint**: User Story 2 complete — all non-compliant and partially-compliant components remediated. All components use `cn()` for conditional classes, centralized color constants for status/state indicators, and theme tokens for core visual properties.

---

## Phase 5: User Story 3 — Verify No Visual Regressions After Updates (Priority: P1)

**Goal**: Confirm that all style changes preserve existing layouts, interactive behavior, and visual hierarchy across every page and user flow.

**Independent Test**: Execute all user flows — project board drag-and-drop, modal open/close, chat interactions, settings changes, theme toggling — and compare behavior to pre-update baseline screenshots from T015/T016.

### Implementation for User Story 3

- [ ] T050 [US3] Capture post-remediation screenshots of all 6 pages in light mode and compare against baseline screenshots from T015
- [ ] T051 [P] [US3] Capture post-remediation screenshots of all 6 pages in dark mode and compare against baseline screenshots from T016
- [ ] T052 [US3] Verify drag-and-drop interactions on project board page — cards snap into place, columns reorder correctly
- [ ] T053 [P] [US3] Verify all modal components (IssueDetailModal, AddAgentModal, etc.) open at correct size/position, content is visible, backdrop behaves correctly
- [ ] T054 [P] [US3] Verify all input fields, dropdowns, toggles, and form submissions work correctly in settings pages
- [ ] T055 [P] [US3] Verify chat popup opens from any page, accepts messages, and displays responses correctly
- [ ] T056 [US3] Verify responsive layout at common breakpoints (mobile 375px, tablet 768px, desktop 1280px) — no overflow, overlapping elements, or broken grids
- [ ] T057 [US3] Verify hover, focus, active, and disabled states render correctly for all interactive components
- [ ] T058 [US3] Verify theme toggle (light ↔ dark ↔ system) transitions correctly with no flash of unstyled content

**Checkpoint**: User Story 3 complete — zero visual regressions confirmed. All existing layouts, interactions, and responsive behaviors work identically to pre-update baseline.

---

## Phase 6: User Story 4 — Cross-Browser and Cross-Device Consistency (Priority: P2)

**Goal**: Verify updated components render consistently across Chrome, Firefox, Safari, and Edge, and across desktop/tablet/mobile form factors.

**Independent Test**: Load the application in each target browser, navigate all pages, and document any rendering differences between browsers.

### Implementation for User Story 4

- [ ] T059 [US4] Test all updated pages in Chrome — verify layout, colors, fonts, spacing, and shadows render correctly in light and dark modes
- [ ] T060 [P] [US4] Test all updated pages in Firefox — verify consistent rendering and compare against Chrome baseline
- [ ] T061 [P] [US4] Test all updated pages in Safari — verify consistent rendering, especially CSS custom property support and shadow rendering
- [ ] T062 [P] [US4] Test all updated pages in Edge — verify consistent rendering
- [ ] T063 [US4] Test responsive behavior on mobile viewport (375px width) across browsers — verify sidebar, board, and settings adapt correctly
- [ ] T064 [P] [US4] Test theme toggle (light/dark/system) in each browser — verify no color flash or incorrect rendering
- [ ] T065 [US4] Document any browser-specific rendering differences and resolve if caused by CSS token usage

**Checkpoint**: User Story 4 complete — updated components render consistently across all target browsers and device form factors.

---

## Phase 7: User Story 5 — Remove Deprecated and Unused Components (Priority: P2)

**Goal**: Identify and remove any components with zero active import references, reducing codebase maintenance burden.

**Independent Test**: Search the codebase for import statements referencing each component file. If zero references exist, the component is safe to remove. After removal, the application builds and all existing tests pass.

### Implementation for User Story 5

- [ ] T066 [US5] Scan all component files in `frontend/src/components/` for import references — identify any files with zero imports
- [ ] T067 [P] [US5] Cross-reference findings with dynamic import patterns (lazy loading, React.lazy) to avoid false positives
- [ ] T068 [US5] Remove confirmed deprecated components with zero references from `frontend/src/components/`
- [ ] T069 [US5] Run full build and test verification after removal: `cd frontend && npm run build && npx tsc --noEmit && npm run test`
- [ ] T070 [US5] Update audit report to mark removed components as deprecated-and-deleted

**Checkpoint**: User Story 5 complete — all deprecated components removed, application builds and tests pass.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final verification, documentation updates, and cleanup that span multiple user stories.

- [ ] T071 [P] Run final comprehensive build verification: `cd frontend && npm run build && npx tsc --noEmit && npx eslint src/ && npm run test`
- [ ] T072 [P] Verify no hardcoded hex values (`#fff`, `#1a1625`, etc.) remain in component files under `frontend/src/components/`
- [ ] T073 Verify all remediated components use `cn()` for conditional class composition — no template literal class patterns remain
- [ ] T074 [P] Verify all status/state color indicators use centralized constants (`STATUS_COLORS`, `AGENT_SOURCE_COLORS`, and existing `PRIORITY_COLORS`) — no duplicated color strings across files
- [ ] T075 Perform final light/dark mode toggle verification across all 6 pages — confirm all components adapt correctly
- [ ] T076 Document any intentional exceptions with `/* intentional: [reason] */` inline comments per research.md R5
- [ ] T077 Update or create audit summary document confirming 100% component compliance (SC-001, SC-002, SC-003)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion (T002, T003 for color constants) — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion (audit requires constants to be defined)
- **User Story 2 (Phase 4)**: Depends on User Story 1 completion (remediation requires audit report)
- **User Story 3 (Phase 5)**: Depends on User Story 2 completion (regression testing requires remediation to be done)
- **User Story 4 (Phase 6)**: Depends on User Story 3 completion (cross-browser testing after regressions verified)
- **User Story 5 (Phase 7)**: Can start after Foundational (Phase 2) — independent of US1-US4 (removal doesn't require remediation)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Phase 2 — produces audit report that gates US2
- **User Story 2 (P1)**: Depends on US1 — uses audit report to drive remediation
- **User Story 3 (P1)**: Depends on US2 — verifies remediation didn't introduce regressions
- **User Story 4 (P2)**: Depends on US3 — cross-browser check after regression verification
- **User Story 5 (P2)**: Can start after Phase 2 — independent of US1-US4 (parallel opportunity)

### Within Each User Story

- Audit tasks (US1) can be parallelized by component category
- Critical remediations (US2) marked [P] can run in parallel (different files)
- Verification tasks (US3, US4) by page/browser can be parallelized
- Type check and lint verification should follow each component group remediation

### Parallel Opportunities

- All Setup tasks T002-T004 marked [P] can run in parallel
- All Foundational inventory tasks T006-T013 marked [P] can run in parallel
- US1 identification tasks T019-T021 marked [P] can run in parallel
- US2 critical remediation tasks T025-T032 marked [P] can run in parallel (different files)
- US2 component group remediations across board/chat/settings/agents/chores can be parallelized
- US3 verification tasks T051, T053-T055 marked [P] can run in parallel
- US4 browser testing tasks T060-T062, T064 marked [P] can run in parallel
- **US5 can run in parallel with US1-US4** (removal is independent of remediation)

---

## Parallel Example: User Story 2 Critical Remediations

```bash
# Launch all critical remediation tasks together (different files):
Task: "Replace inline styles in frontend/src/components/common/ErrorBoundary.tsx" (T024)
Task: "Adopt cn() + STATUS_COLORS in frontend/src/components/settings/SignalConnection.tsx" (T025)
Task: "Adopt cn() + STATUS_COLORS in frontend/src/components/settings/McpSettings.tsx" (T026)
Task: "Replace hardcoded green with STATUS_COLORS.success in frontend/src/components/board/CleanUpSummary.tsx" (T027)
Task: "Replace hardcoded green with STATUS_COLORS.success in frontend/src/components/board/CleanUpConfirmModal.tsx" (T028)
Task: "Adopt cn() in frontend/src/components/chat/MessageBubble.tsx" (T029)
Task: "Adopt cn() + constants in frontend/src/components/board/IssueDetailModal.tsx" (T030)
Task: "Adopt cn() + constants in frontend/src/components/chat/IssueRecommendationPreview.tsx" (T031)
Task: "Adopt AGENT_SOURCE_COLORS in frontend/src/components/board/AddAgentPopover.tsx" (T032)
```

---

## Parallel Example: Foundational Inventory

```bash
# Launch all component inventory tasks together (different directories):
Task: "Inventory layout components in frontend/src/layout/" (T006)
Task: "Inventory page components in frontend/src/pages/" (T007)
Task: "Inventory board components in frontend/src/components/board/" (T008)
Task: "Inventory chat components in frontend/src/components/chat/" (T009)
Task: "Inventory agents components in frontend/src/components/agents/" (T010)
Task: "Inventory chores components in frontend/src/components/chores/" (T011)
Task: "Inventory settings components in frontend/src/components/settings/" (T012)
Task: "Inventory auth and common components" (T013)
```

---

## Implementation Strategy

### MVP First (User Story 1 + Setup)

1. Complete Phase 1: Setup — add centralized color constants
2. Complete Phase 2: Foundational — inventory all components
3. Complete Phase 3: User Story 1 — deliver audit report
4. **STOP and VALIDATE**: Audit report is complete and actionable
5. Deliver audit report to stakeholders for review

### Incremental Delivery

1. Complete Setup + Foundational + US1 → Audit report delivered (MVP!)
2. Add User Story 2 → All components remediated → Build passes
3. Add User Story 3 → No visual regressions confirmed
4. Add User Story 5 → Dead code removed (can parallel with US3)
5. Add User Story 4 → Cross-browser consistency verified
6. Each story adds confidence without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. One developer completes US1 (audit)
3. Once US1 is done, multiple developers remediate in parallel:
   - Developer A: Board components (T033-T036)
   - Developer B: Chat + Agents components (T037-T043)
   - Developer C: Settings + Chores components (T040-T046)
   - Developer D: User Story 5 (deprecated removal, independent)
4. After remediation, US3 and US4 verification can be split by page/browser

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- No new tests are mandated — existing test suite must pass after changes (FR-008)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All changes are frontend-only (`frontend/src/`) — no backend modifications
- Intentional exceptions (arbitrary Tailwind values) are preserved and documented, not remediated
- Third-party library styles (dnd-kit, Radix) are not modified — only wrapper-level alignment if needed
