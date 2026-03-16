# Tasks: Agents Page Audit

**Input**: Design documents from `/specs/043-agents-page-audit/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/component-contracts.yaml, quickstart.md

**Tests**: Tests are explicitly requested in User Story 6 (P3). Test tasks are included in Phase 8.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. US1 (P1) must complete before US2–US5 since decomposition restructures the components those stories modify.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/frontend/src/` at repository root
- All file paths below are relative to `solune/frontend/`

---

## Phase 1: Setup (Baseline Verification)

**Purpose**: Establish baseline state of the codebase before making any changes

- [ ] T001 Run baseline lint on all agent-related files and document current warnings: `npx eslint src/pages/AgentsPage.tsx src/components/agents/ src/components/board/`
- [ ] T002 [P] Run baseline type-check and document current errors: `npx tsc --noEmit`
- [ ] T003 [P] Run baseline tests for agent-related files and document current results: `npx vitest run src/components/agents/ src/components/board/ src/hooks/useAgent`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Verify and fix agentKeys query key factory to follow `[feature].all / .list(id) / .detail(id)` pattern in `src/hooks/useAgents.ts` (FR-023)
- [ ] T005 [P] Verify ErrorBoundary wraps AgentsPage at route level or page level — add if missing in `src/pages/AgentsPage.tsx` or `src/App.tsx` (FR-007)

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Modular Component Architecture (Priority: P1) 🎯 MVP

**Goal**: Decompose all oversized components (7 files exceed 250-line limit) into focused sub-components and extract complex state logic into dedicated hooks. Every component file ≤250 lines.

**Independent Test**: Verify by running `wc -l` on all agent component files to confirm ≤250 lines each. Run lint + type-check + existing tests to confirm no regressions.

### Catalog Component Decompositions

#### AgentsPanel.tsx (565 → ≤250 lines)

- [ ] T006 [P] [US1] Extract AgentSearch sub-component (search input + filter logic) into `src/components/agents/AgentSearch.tsx`
- [ ] T007 [P] [US1] Extract AgentSortControls sub-component (sort dropdown + direction toggle) into `src/components/agents/AgentSortControls.tsx`
- [ ] T008 [P] [US1] Extract SpotlightSection sub-component (featured/spotlight agent cards) into `src/components/agents/SpotlightSection.tsx`
- [ ] T009 [P] [US1] Extract AgentGrid sub-component (main catalog grid of agent cards) into `src/components/agents/AgentGrid.tsx`
- [ ] T010 [P] [US1] Extract PendingAgentsSection sub-component (pending creation/deletion agents list) into `src/components/agents/PendingAgentsSection.tsx`
- [ ] T011 [US1] Extract useAgentsPanel hook (search state, sort state, filter logic, 8+ useState calls) into `src/hooks/useAgentsPanel.ts` (FR-002)
- [ ] T012 [US1] Refactor AgentsPanel.tsx to compose extracted sub-components and hook — verify ≤250 lines in `src/components/agents/AgentsPanel.tsx`

#### AddAgentModal.tsx (520 → ≤250 lines)

- [ ] T013 [P] [US1] Extract AgentFormFields sub-component (name, description, system prompt, model fields) into `src/components/agents/AgentFormFields.tsx`
- [ ] T014 [P] [US1] Extract AgentToolsSection sub-component (tools configuration wrapping ToolsEditor) into `src/components/agents/AgentToolsSection.tsx`
- [ ] T015 [US1] Extract useAgentForm hook (form state, validation, AI enhance, submit logic) into `src/hooks/useAgentForm.ts` (FR-002)
- [ ] T016 [US1] Refactor AddAgentModal.tsx to compose extracted sub-components and hook — verify ≤250 lines in `src/components/agents/AddAgentModal.tsx`

#### AgentCard.tsx (286 → ≤250 lines)

- [ ] T017 [P] [US1] Extract AgentCardActions sub-component (edit, delete, chat action buttons) into `src/components/agents/AgentCardActions.tsx`
- [ ] T018 [P] [US1] Extract AgentCardMetadata sub-component (status badge, source badge, tools count, usage stats) into `src/components/agents/AgentCardMetadata.tsx`
- [ ] T019 [US1] Refactor AgentCard.tsx to compose extracted sub-components — verify ≤250 lines in `src/components/agents/AgentCard.tsx`

#### AgentInlineEditor.tsx (272 → ≤250 lines)

- [ ] T020 [P] [US1] Extract AgentEditForm sub-component (editor form fields and controls) into `src/components/agents/AgentEditForm.tsx`
- [ ] T021 [US1] Extract useAgentEditor hook (editor state, expand/collapse, save/cancel logic) into `src/hooks/useAgentEditor.ts` (FR-002)
- [ ] T022 [US1] Refactor AgentInlineEditor.tsx to compose extracted sub-component and hook — verify ≤250 lines in `src/components/agents/AgentInlineEditor.tsx`

### Board Component Decompositions

#### AgentPresetSelector.tsx (519 → ≤250 lines)

- [ ] T023 [P] [US1] Extract PresetButtonGroup sub-component (preset action buttons) into `src/components/board/PresetButtonGroup.tsx`
- [ ] T024 [P] [US1] Extract SavedPipelinesDropdown sub-component (saved pipelines selection dropdown) into `src/components/board/SavedPipelinesDropdown.tsx`
- [ ] T025 [P] [US1] Extract PresetConfirmDialog sub-component (confirmation dialogs for preset changes) into `src/components/board/PresetConfirmDialog.tsx`
- [ ] T026 [US1] Extract usePresetSelector hook (preset state, dropdown toggle, confirmation logic) into `src/hooks/usePresetSelector.ts` (FR-002)
- [ ] T027 [US1] Refactor AgentPresetSelector.tsx to compose extracted sub-components and hook — verify ≤250 lines in `src/components/board/AgentPresetSelector.tsx`

#### AgentConfigRow.tsx (480 → ≤250 lines)

- [ ] T028 [P] [US1] Extract ConstellationSvg sub-component (SVG visualization for agent connections) into `src/components/board/ConstellationSvg.tsx`
- [ ] T029 [P] [US1] Extract ColumnMappingGrid sub-component (droppable column grid layout) into `src/components/board/ColumnMappingGrid.tsx`
- [ ] T030 [US1] Extract useAgentDnd hook (DnD context setup, sensors, collision detection, handlers) into `src/hooks/useAgentDnd.ts` (FR-002)
- [ ] T031 [US1] Refactor AgentConfigRow.tsx to compose extracted sub-components and hook — verify ≤250 lines in `src/components/board/AgentConfigRow.tsx`

#### AgentTile.tsx (308 → ≤250 lines)

- [ ] T032 [P] [US1] Extract AgentTileActions sub-component (clone, remove, model change action buttons) into `src/components/board/AgentTileActions.tsx`
- [ ] T033 [P] [US1] Extract AgentTileContent sub-component (agent name, model display, source badge) into `src/components/board/AgentTileContent.tsx`
- [ ] T034 [US1] Refactor AgentTile.tsx to compose extracted sub-components — verify ≤250 lines in `src/components/board/AgentTile.tsx`

### Hook Splitting

- [ ] T035 [US1] Extract useAvailableAgents from useAgentConfig.ts into `src/hooks/useAvailableAgents.ts` — update all import sites
- [ ] T036 [US1] Verify useAgentConfig.ts is properly scoped after extraction — assess if further splitting is needed in `src/hooks/useAgentConfig.ts`

### Verification

- [ ] T037 [US1] Run lint, type-check, and existing tests to verify all decompositions compile and pass: `npx eslint src/pages/AgentsPage.tsx src/components/agents/ src/components/board/ && npx tsc --noEmit && npx vitest run`

**Checkpoint**: All component files are ≤250 lines. Complex state is in dedicated hooks. User Stories 2–7 can now proceed.

---

## Phase 4: User Story 2 — Reliable Loading, Error, and Empty States (Priority: P1)

**Goal**: Every data-dependent section shows appropriate loading, error, empty, and rate-limit states. Users never see a blank screen.

**Independent Test**: Simulate loading delays, API failures, rate limit errors, and empty agent lists — confirm appropriate UI renders for each scenario.

### Implementation for User Story 2

- [ ] T038 [US2] Add or verify loading state (CelestialLoader or skeleton cards) in AgentsPanel catalog section in `src/components/agents/AgentsPanel.tsx` (FR-003)
- [ ] T039 [P] [US2] Add or verify error state with retry action and rate-limit detection via `isRateLimitApiError()` in AgentsPanel in `src/components/agents/AgentsPanel.tsx` (FR-004)
- [ ] T040 [P] [US2] Add or verify meaningful empty state with "Create Agent" CTA in AgentsPanel when agents list is empty in `src/components/agents/AgentsPanel.tsx` (FR-005)
- [ ] T041 [US2] Add independent loading/error states for board column assignments section in `src/pages/AgentsPage.tsx` (FR-006)
- [ ] T042 [P] [US2] Add independent loading/error states for pipeline data in AgentPresetSelector in `src/components/board/AgentPresetSelector.tsx` (FR-006)
- [ ] T043 [US2] Verify ErrorBoundary wraps AgentsPage with recovery UI and retry option in `src/pages/AgentsPage.tsx` (FR-007)
- [ ] T044 [US2] Add user-friendly error messages following "Could not [action]. [Reason]. [Next step]." format for all mutation onError handlers in `src/hooks/useAgents.ts` (FR-014, FR-024)
- [ ] T045 [P] [US2] Add onError handlers with user-visible feedback to all useMutation calls in `src/hooks/useAgentConfig.ts` (FR-024)
- [ ] T046 [P] [US2] Add loading state to AddAgentModal submit button while mutation is pending in `src/components/agents/AddAgentModal.tsx` (FR-003)
- [ ] T047 [P] [US2] Add loading state to BulkModelUpdateDialog submit while mutation is pending in `src/components/agents/BulkModelUpdateDialog.tsx` (FR-003)
- [ ] T048 [US2] Verify search-no-results state shows "No matching agents" message when search active but filtered list is empty in `src/components/agents/AgentsPanel.tsx`

**Checkpoint**: All data states (loading, error, empty, rate-limit, partial failure) render appropriate UI. No blank screens possible.

---

## Phase 5: User Story 3 — Accessible Agent Management (Priority: P2)

**Goal**: Full WCAG AA compliance — all interactive elements keyboard-accessible, all controls properly labeled, focus management correct in all modals/dialogs.

**Independent Test**: Navigate the entire Agents page using only keyboard (Tab, Enter, Space, Escape). Run automated accessibility audit (axe DevTools) for zero critical violations.

### Implementation for User Story 3

#### ARIA Attributes & Roles

- [ ] T049 [P] [US3] Add or verify aria-label on search input and sort controls in AgentsPanel in `src/components/agents/AgentsPanel.tsx` (FR-010)
- [ ] T050 [P] [US3] Fix AgentIconPickerModal ARIA: change role="presentation" to role="dialog" with aria-modal="true" in `src/components/agents/AgentIconPickerModal.tsx`
- [ ] T051 [P] [US3] Add card-level accessible description (aria-label or aria-describedby) to AgentCard in `src/components/agents/AgentCard.tsx` (FR-010)
- [ ] T052 [P] [US3] Add role="region" and aria-label="Agent column assignments" to AgentConfigRow in `src/components/board/AgentConfigRow.tsx`
- [ ] T053 [P] [US3] Add role="list" to the agent container in AgentColumnCell in `src/components/board/AgentColumnCell.tsx`
- [ ] T054 [P] [US3] Add role="listitem" to AgentTile in `src/components/board/AgentTile.tsx`
- [ ] T055 [P] [US3] Add role="status" and aria-live="polite" to AgentSaveBar in `src/components/board/AgentSaveBar.tsx`
- [ ] T056 [P] [US3] Add aria-expanded and aria-controls to saved pipelines dropdown in AgentPresetSelector in `src/components/board/AgentPresetSelector.tsx`
- [ ] T057 [P] [US3] Add role="listbox" on options list and aria-expanded to AddAgentPopover in `src/components/board/AddAgentPopover.tsx`

#### Focus Management

- [ ] T058 [US3] Verify focus trapping in AddAgentModal — Tab should not escape to background in `src/components/agents/AddAgentModal.tsx` (FR-009)
- [ ] T059 [P] [US3] Verify focus trapping in BulkModelUpdateDialog — Tab should not escape to background in `src/components/agents/BulkModelUpdateDialog.tsx` (FR-009)
- [ ] T060 [P] [US3] Verify focus trapping in AgentIconPickerModal — Tab should not escape to background in `src/components/agents/AgentIconPickerModal.tsx` (FR-009)
- [ ] T061 [US3] Verify focus returns to trigger element on close for all modals (AddAgentModal, BulkModelUpdateDialog, AgentIconPickerModal, ConfirmationDialogs) (FR-009)
- [ ] T062 [US3] Add focus restoration on expand/collapse in AgentInlineEditor in `src/components/agents/AgentInlineEditor.tsx` (FR-009)

#### Focus Indicators & Keyboard Navigation

- [ ] T063 [US3] Add celestial-focus class or focus-visible ring to all interactive elements missing visible focus indicators across agent catalog components in `src/components/agents/` (FR-008)
- [ ] T064 [P] [US3] Add celestial-focus class or focus-visible ring to all interactive elements missing visible focus indicators across board components in `src/components/board/` (FR-008)
- [ ] T065 [US3] Verify keyboard navigation (Tab order, Enter/Space activation) through AgentIconCatalog icon grid in `src/components/agents/AgentIconCatalog.tsx` (FR-008)
- [ ] T066 [P] [US3] Verify keyboard operability of tool reordering in ToolsEditor in `src/components/agents/ToolsEditor.tsx` (FR-008)

#### Labels & Status Indicators

- [ ] T067 [US3] Ensure all form fields (name, description, system prompt, model) have visible labels or aria-label in AddAgentModal in `src/components/agents/AddAgentModal.tsx` (FR-010)
- [ ] T068 [P] [US3] Ensure all form fields have visible labels or aria-label in AgentInlineEditor in `src/components/agents/AgentInlineEditor.tsx` (FR-010)
- [ ] T069 [US3] Ensure status indicators (active, pending_creation, pending_deletion) use icon + text, not color alone in AgentCard in `src/components/agents/AgentCard.tsx` (FR-011)
- [ ] T070 [P] [US3] Add aria-hidden="true" to decorative icons and aria-label to meaningful icons across agent components (FR-010)

**Checkpoint**: All interactive elements keyboard-accessible. All ARIA attributes correct. Focus trapped in modals and returned on close. WCAG AA compliance achieved.

---

## Phase 6: User Story 4 — Polished Text, Copy, and User Experience (Priority: P2)

**Goal**: All user-facing text is final, consistent, and professional. All destructive actions require confirmation. All mutations provide success/error feedback.

**Independent Test**: Review all user-facing strings for placeholder text. Verify destructive actions show ConfirmationDialog. Confirm success/error messages follow established format.

### Implementation for User Story 4

#### Text & Copy Audit

- [ ] T071 [US4] Audit all user-visible strings for placeholder text (TODO, Lorem ipsum, Test) across all agent and board components in `src/components/agents/` and `src/components/board/`
- [ ] T072 [P] [US4] Verify and fix action button labels to use verbs ("Create Agent", "Save Changes", "Delete Agent") across all agent components
- [ ] T073 [US4] Verify consistent terminology across all agent components — no "workflow" vs "pipeline", "task" vs "chore" inconsistencies

#### Destructive Action Confirmations

- [ ] T074 [US4] Add or verify ConfirmationDialog for agent delete action in AgentCard in `src/components/agents/AgentCard.tsx` (FR-012)
- [ ] T075 [P] [US4] Add or verify ConfirmationDialog for "clear pending agents" action in AgentsPanel/PendingAgentsSection in `src/components/agents/PendingAgentsSection.tsx` (FR-012)
- [ ] T076 [P] [US4] Add or verify ConfirmationDialog for destructive preset changes in AgentPresetSelector in `src/components/board/AgentPresetSelector.tsx` (FR-012)
- [ ] T077 [P] [US4] Add or verify ConfirmationDialog for agent removal from column in AgentTile in `src/components/board/AgentTile.tsx` (FR-012)

#### Mutation Feedback

- [ ] T078 [US4] Add success feedback (toast or inline message) for create agent mutation in `src/hooks/useAgents.ts` (FR-013)
- [ ] T079 [P] [US4] Add success feedback for update agent mutation in `src/hooks/useAgents.ts` (FR-013)
- [ ] T080 [P] [US4] Add success feedback for delete agent mutation in `src/hooks/useAgents.ts` (FR-013)
- [ ] T081 [P] [US4] Add success feedback for bulk model update mutation in `src/hooks/useAgents.ts` (FR-013)
- [ ] T082 [US4] Add success feedback for save agent column configuration in `src/hooks/useAgentConfig.ts` (FR-013)

#### Truncation & Formatting

- [ ] T083 [P] [US4] Add Tooltip for truncated agent names (text-ellipsis + full text on hover) in AgentCard in `src/components/agents/AgentCard.tsx` (FR-015)
- [ ] T084 [P] [US4] Add Tooltip for truncated agent names in AgentTile in `src/components/board/AgentTile.tsx` (FR-015)
- [ ] T085 [P] [US4] Add Tooltip for truncated agent descriptions in AgentCard in `src/components/agents/AgentCard.tsx` (FR-015)
- [ ] T086 [US4] Format timestamps consistently — relative for recent ("2 hours ago"), absolute for older — in AgentCard in `src/components/agents/AgentCard.tsx`

**Checkpoint**: All text is final and consistent. All destructive actions require confirmation. All mutations show success/error feedback. Long text truncated with tooltips.

---

## Phase 7: User Story 5 — Consistent Styling and Responsive Layout (Priority: P3)

**Goal**: All styling uses Tailwind utilities and design tokens — no hardcoded colors, no inline styles. Layout responsive from 768px to 1920px. Dark mode fully supported.

**Independent Test**: View the Agents page at 768px, 1024px, 1440px, 1920px in both light and dark modes. Confirm no layout breaks, no hardcoded colors, no inline styles.

### Implementation for User Story 5

#### Design Token Compliance

- [ ] T087 [P] [US5] Replace hardcoded `border-emerald-300/40`, `bg-emerald-50/80` with `solar-chip-success` design token in AgentsPanel in `src/components/agents/AgentsPanel.tsx` (FR-017)
- [ ] T088 [P] [US5] Replace hardcoded `text-green-700 dark:text-green-400` with design token in AgentCard in `src/components/agents/AgentCard.tsx` (FR-017)
- [ ] T089 [P] [US5] Replace hardcoded `bg-blue-100 dark:bg-blue-900/30`, `bg-green-100 dark:bg-green-900/30` with design tokens in AddAgentPopover in `src/components/board/AddAgentPopover.tsx` (FR-017)
- [ ] T090 [P] [US5] Replace inline SVG hardcoded HSL values with CSS custom properties via Tailwind classes in AgentTile in `src/components/board/AgentTile.tsx` (FR-017)
- [ ] T091 [P] [US5] Replace `min-w-[280px] max-w-[340px]` with consistent design scale values in AgentDragOverlay in `src/components/board/AgentDragOverlay.tsx` (FR-017)
- [ ] T092 [US5] Standardize z-index values (`z-[120]`, `z-[140]`, `z-[9999]`, `z-50`) to a consistent z-layer system across agent and board components (FR-017)

#### Inline Styles & Spacing

- [ ] T093 [US5] Remove any inline `style={}` attributes and replace with Tailwind utility classes using `cn()` across all agent components in `src/components/agents/` and `src/components/board/` (FR-017)
- [ ] T094 [P] [US5] Replace arbitrary spacing values (e.g., `p-[13px]`) with standard Tailwind spacing scale across all agent components (FR-017)

#### Responsive Layout

- [ ] T095 [US5] Verify and fix responsive layout at 768px viewport width — no overflow, overlapping, or hidden content in `src/pages/AgentsPage.tsx` (FR-016)
- [ ] T096 [P] [US5] Verify and fix responsive layout at 1024px viewport width in `src/pages/AgentsPage.tsx` (FR-016)
- [ ] T097 [P] [US5] Verify and fix responsive layout at 1440px and 1920px viewport widths in `src/pages/AgentsPage.tsx` (FR-016)
- [ ] T098 [US5] Add `overflow-x-auto` wrapper and minimum column widths to Orbital Map column grid in AgentConfigRow in `src/components/board/AgentConfigRow.tsx` (FR-016)

#### Dark Mode & Visual Consistency

- [ ] T099 [US5] Verify dark mode renders correctly for all agent catalog components — no hardcoded colors in `src/components/agents/` (FR-017)
- [ ] T100 [P] [US5] Verify dark mode renders correctly for all board components — no hardcoded colors in `src/components/board/` (FR-017)
- [ ] T101 [US5] Verify Card component usage is consistent across all agent content sections — use `<Card>` from `src/components/ui/card.tsx` (FR-017)

**Checkpoint**: All styling uses design tokens. No inline styles. Layout responsive at all target breakpoints. Dark mode fully functional.

---

## Phase 8: User Story 6 — Comprehensive Test Coverage (Priority: P3)

**Goal**: Hook tests via `renderHook()` for all custom hooks. Component interaction tests for key components. Edge cases covered. No snapshot tests.

**Independent Test**: Run `npx vitest run src/hooks/useAgent* src/components/agents/ src/components/board/` — all tests pass with coverage for happy path, error, loading, and edge cases.

### Hook Tests

- [ ] T102 [P] [US6] Create hook tests for useAgents (useAgentsList, useCreateAgent, useUpdateAgent, useDeleteAgent, useBulkUpdateModels — happy path, error, loading, rate limit) in `src/hooks/useAgents.test.ts` (FR-019)
- [ ] T103 [P] [US6] Create hook tests for useAgentConfig (addAgent, removeAgent, cloneAgent, reorderAgents, moveAgentToColumn, applyPreset, save, discard, dirty tracking) in `src/hooks/useAgentConfig.test.ts` (FR-019)
- [ ] T104 [P] [US6] Create hook tests for useAgentTools (tool list query, add tool, remove tool) in `src/hooks/useAgentTools.test.ts` (FR-019)
- [ ] T105 [P] [US6] Create hook tests for extracted useAgentsPanel (search, sort, filter state management) in `src/hooks/useAgentsPanel.test.ts` (FR-019)
- [ ] T106 [P] [US6] Create hook tests for extracted useAgentForm (form state, validation, submit, reset) in `src/hooks/useAgentForm.test.ts` (FR-019)

### Component Interaction Tests

- [ ] T107 [P] [US6] Update AgentsPanel tests to cover loading, error, empty, rate-limit, and search-no-results states in `src/components/agents/AgentsPanel.test.tsx` (FR-020)
- [ ] T108 [P] [US6] Update AddAgentModal tests to cover form submission, validation errors, edit mode, and success feedback in `src/components/agents/AddAgentModal.test.tsx` (FR-020)
- [ ] T109 [P] [US6] Create AgentCard interaction tests (click edit, click delete with confirmation, status badge rendering, spotlight variant) in `src/components/agents/AgentCard.test.tsx` (FR-020)
- [ ] T110 [P] [US6] Create BulkModelUpdateDialog interaction tests (two-step flow, confirmation, error handling) in `src/components/agents/BulkModelUpdateDialog.test.tsx` (FR-020)

### Edge Case Tests

- [ ] T111 [US6] Add edge case tests across test files: empty agent list + populated board, rate limit error on mutation, agent name >200 chars, null optional fields (icon_name, description, model), orphaned assignment (FR-020)
- [ ] T112 [US6] Verify no snapshot tests exist in agent-related test files — replace any found with explicit behavioral assertions

### Verification

- [ ] T113 [US6] Run full agent-related test suite and verify all tests pass: `npx vitest run --reporter=verbose src/hooks/useAgent* src/components/agents/ src/components/board/`

**Checkpoint**: All custom hooks have test coverage. Key components have interaction tests. Edge cases covered. Zero snapshot tests.

---

## Phase 9: User Story 7 — Performance and Code Hygiene (Priority: P3)

**Goal**: Zero `any` types, zero type assertions, zero dead code, zero `console.log`, all imports use `@/` alias, expensive computations memoized, zero ESLint warnings.

**Independent Test**: Run `npx eslint` (0 warnings), `npx tsc --noEmit` (0 errors), search for `any`/`as`/`console.log` (0 results).

### Type Safety

- [ ] T114 [US7] Eliminate all `any` types in agent-related files — replace with proper types or `unknown` + type guards in `src/pages/AgentsPage.tsx`, `src/components/agents/`, `src/components/board/`, `src/hooks/useAgent*.ts` (FR-018)
- [ ] T115 [P] [US7] Eliminate all type assertions (`as`) in agent-related files — replace with type guards or discriminated unions (FR-018)
- [ ] T116 [P] [US7] Add explicit return type annotations to custom hooks where inference is ambiguous in `src/hooks/useAgent*.ts`

### Dead Code & Debugging Artifacts

- [ ] T117 [US7] Remove all dead code (unused imports, commented-out blocks, unreachable branches) from agent-related files in `src/components/agents/`, `src/components/board/`, `src/hooks/useAgent*.ts` (FR-022)
- [ ] T118 [P] [US7] Remove all `console.log` statements from agent-related files (FR-022)

### Import Hygiene

- [ ] T119 [US7] Convert all relative imports (`../../`) to `@/` alias imports in agent-related files (FR-022)

### Performance Optimization

- [ ] T120 [US7] Verify all list renders use `key={item.id}` — never `key={index}` — across agent-related components (FR-018)
- [ ] T121 [P] [US7] Wrap expensive computations (sorting, filtering, usage count aggregation) in `useMemo` where appropriate in agent components
- [ ] T122 [P] [US7] Wrap callbacks passed to memoized children in `useCallback` where appropriate in agent components

### Constants & Conventions

- [ ] T123 [US7] Define repeated magic strings (agent status values, query keys, route paths) as named constants in `src/constants/` (FR-022)
- [ ] T124 [P] [US7] Verify staleTime configured appropriately (30s for agent lists, 60s for config) on all React Query hooks in `src/hooks/useAgents.ts` (FR-023)
- [ ] T125 [P] [US7] Verify all mutations use `invalidateQueries` on success for cache consistency in `src/hooks/useAgents.ts` and `src/hooks/useAgentConfig.ts` (FR-024)
- [ ] T126 [US7] Verify file naming conventions: PascalCase `.tsx` for components, `use*.ts` for hooks, types in `src/types/` (FR-022)

**Checkpoint**: Zero `any` types. Zero type assertions. Zero dead code. Zero `console.log`. All imports use `@/` alias. Expensive operations memoized.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all user stories

- [ ] T127 Run ESLint on all agent-related files and fix to zero warnings: `npx eslint src/pages/AgentsPage.tsx src/components/agents/ src/components/board/` (FR-021)
- [ ] T128 [P] Run TypeScript type-check and fix to zero errors: `npx tsc --noEmit`
- [ ] T129 Run full test suite and verify all tests pass: `npx vitest run`
- [ ] T130 Verify all component files ≤250 lines: automated line count check on all files in `src/components/agents/`, `src/components/board/`, `src/pages/AgentsPage.tsx`
- [ ] T131 [P] Verify all extracted hooks follow naming conventions and are properly exported in `src/hooks/`
- [ ] T132 Run quickstart.md validation steps (lint, type-check, tests, dev server)
- [ ] T133 Final FR coverage review: verify all FR-001 through FR-024 are addressed with at least one task

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — BLOCKS US2 through US5 (decomposition restructures components)
- **US2 (Phase 4)**: Depends on US1 completion (needs decomposed components)
- **US3 (Phase 5)**: Depends on US1 completion (needs decomposed components); can run in parallel with US2
- **US4 (Phase 6)**: Depends on US1 completion (needs decomposed components); can run in parallel with US2, US3
- **US5 (Phase 7)**: Depends on US1 completion (needs final component structure); can run in parallel with US2–US4
- **US6 (Phase 8)**: Depends on US1–US5 completion (tests should cover final implementations)
- **US7 (Phase 9)**: Can start after US1; can run incrementally alongside US2–US6
- **Polish (Phase 10)**: Depends on all user stories being complete

### User Story Dependencies

```text
Phase 1 (Setup)
    │
    ▼
Phase 2 (Foundational)
    │
    ▼
Phase 3 (US1: Decomposition) ◄── BLOCKS ALL
    │
    ├───────────┬───────────┬───────────┐
    ▼           ▼           ▼           ▼
Phase 4      Phase 5     Phase 6     Phase 7
(US2: States) (US3: a11y) (US4: UX)  (US5: Styling)
    │           │           │           │
    └───────────┴───────────┴───────────┘
                    │
                    ▼
              Phase 8 (US6: Tests)
                    │
                    ▼
              Phase 9 (US7: Hygiene) ◄── Can start after US1, runs incrementally
                    │
                    ▼
              Phase 10 (Polish)
```

### Within Each User Story

- Extraction/creation tasks before refactoring/composition tasks
- Hook extraction before component refactoring
- Sub-component creation before parent simplification
- Core implementation before verification tasks

### Parallel Opportunities

- **Phase 1**: T001, T002, T003 — all independent baseline checks
- **Phase 3 (US1)**: Sub-component extractions within each component group (T006–T010, T013–T014, T017–T018, T023–T025, T028–T029, T032–T033) — different output files
- **Phase 4 (US2)**: T039–T042, T045–T047 — different component files
- **Phase 5 (US3)**: T049–T057 — ARIA additions to different files
- **Phase 6 (US4)**: T074–T077, T078–T081, T083–T085 — different files
- **Phase 7 (US5)**: T087–T091, T094, T096–T097, T100 — different files
- **Phase 8 (US6)**: T102–T110 — independent test files
- **Phase 9 (US7)**: T115, T118, T121–T122, T124–T125 — independent concerns
- **Phases 4–7**: Can all run in parallel after US1 completes (different concern areas, different files)
- **Total parallelizable tasks**: 81 of 133 tasks marked [P]

---

## Parallel Example: User Story 1 (AgentsPanel Decomposition)

```bash
# Launch all sub-component extractions in parallel (different output files):
Task T006: "Extract AgentSearch into src/components/agents/AgentSearch.tsx"
Task T007: "Extract AgentSortControls into src/components/agents/AgentSortControls.tsx"
Task T008: "Extract SpotlightSection into src/components/agents/SpotlightSection.tsx"
Task T009: "Extract AgentGrid into src/components/agents/AgentGrid.tsx"
Task T010: "Extract PendingAgentsSection into src/components/agents/PendingAgentsSection.tsx"

# Then sequentially:
Task T011: "Extract useAgentsPanel hook into src/hooks/useAgentsPanel.ts"
Task T012: "Refactor AgentsPanel.tsx to compose all extracted sub-components"
```

## Parallel Example: User Stories 2–5 (After US1 Completes)

```bash
# Launch all four stories in parallel (different concern areas):
Developer A → Phase 4 (US2: Loading/Error/Empty states)
Developer B → Phase 5 (US3: Accessibility)
Developer C → Phase 6 (US4: Text/Copy/UX polish)
Developer D → Phase 7 (US5: Styling/Responsive)
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (3 tasks)
2. Complete Phase 2: Foundational (2 tasks)
3. Complete Phase 3: User Story 1 — Decomposition (32 tasks)
4. **STOP and VALIDATE**: All files ≤250 lines, lint/type-check/tests pass
5. Complete Phase 4: User Story 2 — Loading/Error/Empty States (11 tasks)
6. **STOP and VALIDATE**: All data states render correctly, no blank screens
7. Deploy/demo if ready — **this is your MVP** (48 tasks total)

### Incremental Delivery

1. Setup + Foundational → Foundation ready (5 tasks)
2. Add US1 (Decomposition) → Validate → Deploy/Demo (37 tasks cumulative)
3. Add US2 (States) → Validate → Deploy/Demo (48 tasks — **MVP!**)
4. Add US3 (Accessibility) → Validate → Deploy/Demo (70 tasks)
5. Add US4 (Text/UX) → Validate → Deploy/Demo (86 tasks)
6. Add US5 (Styling) → Validate → Deploy/Demo (101 tasks)
7. Add US6 (Tests) → Validate → Deploy/Demo (113 tasks)
8. Add US7 (Hygiene) + Polish → Final validation (133 tasks — **complete**)

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational + US1 together (critical path)
2. Once US1 is done:
   - Developer A: US2 (Loading/Error states)
   - Developer B: US3 (Accessibility)
   - Developer C: US4 (Text/UX polish)
   - Developer D: US5 (Styling/Responsive)
3. Once US2–US5 complete:
   - Any developer: US6 (Test coverage)
   - Any developer: US7 (Code hygiene) — can start earlier
4. Final: Polish phase (team)

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks in the same phase
- [Story] label maps task to specific user story for traceability
- US1 must complete before US2–US5 since decomposition changes the file structure
- US6 (tests) should wait for US1–US5 so tests cover final implementations
- US7 (hygiene) can start after US1 and run incrementally alongside other stories
- All paths are relative to `solune/frontend/` unless otherwise noted
- Verify tests pass after each component decomposition group to catch regressions early
- Reference quickstart.md for development workflow and validation commands
- Reference research.md for decomposition strategy decisions
- Reference component-contracts.yaml for expected props, states, and ARIA requirements per component
