# Tasks: Agents Page Audit

**Input**: Design documents from `/specs/043-agents-page-audit/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/component-contracts.yaml, quickstart.md

**Tests**: Tests are explicitly requested in User Story 6 (P3). Existing tests (AgentsPanel, AddAgentModal, AgentSaveBar, AgentTile, ThemedAgentIcon) must continue to pass. New hook tests and component interaction tests are scoped to US6.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. This is a frontend-only audit-and-refactor effort — no backend changes required. All changes target `solune/frontend/src/`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/frontend/src/` at repository root
- Pages: `solune/frontend/src/pages/`
- Agent Catalog components: `solune/frontend/src/components/agents/`
- Orbital Map components: `solune/frontend/src/components/board/`
- Shared components: `solune/frontend/src/components/common/`
- Hooks: `solune/frontend/src/hooks/`
- Types: `solune/frontend/src/types/`
- Design tokens: `solune/frontend/src/index.css`
- Constants: `solune/frontend/src/constants/`

---

## Phase 1: Setup (Audit Baseline)

**Purpose**: Establish audit baseline — verify existing tests pass and document current state

- [ ] T001 Run existing test suite (`npx vitest run`) and document any pre-existing failures in solune/frontend/
- [ ] T002 Run type-check (`npm run type-check`) and lint (`npm run lint`) to establish baseline in solune/frontend/
- [ ] T003 [P] Review design token reference in solune/frontend/src/index.css — document the full Celestial token set (colors, custom classes, focus styles) for use during audit
- [ ] T004 [P] Count lines in all audit-target files and document which exceed the 250-line limit per FR-001: solune/frontend/src/pages/AgentsPage.tsx, solune/frontend/src/components/agents/*.tsx, solune/frontend/src/components/board/Agent*.tsx

---

## Phase 2: Foundational (Cross-Cutting Audit Inventory)

**Purpose**: Identify all issues across Agents page components before story-specific fixes begin

**⚠️ CRITICAL**: No user story work can begin until this inventory phase is complete

- [ ] T005 Audit all agent components for hardcoded color values (hex, rgb, hsl, named Tailwind colors not in design system) across solune/frontend/src/components/agents/ and solune/frontend/src/components/board/Agent*.tsx
- [ ] T006 [P] Audit z-index usage across all Agents page components — document all arbitrary z-index values (z-[120], z-[140], z-[9999]) in solune/frontend/src/components/agents/ and solune/frontend/src/components/board/
- [ ] T007 [P] Audit all interactive elements for missing `.celestial-focus` or equivalent `focus-visible:ring-*` classes across solune/frontend/src/components/agents/ and solune/frontend/src/components/board/
- [ ] T008 [P] Audit all ARIA attributes — document missing roles, labels, and live regions across all Agents page components per specs/043-agents-page-audit/contracts/component-contracts.yaml
- [ ] T009 [P] Audit all agent-related files for `any` types, type assertions (`as`), dead code, `console.log` statements, and relative imports in solune/frontend/src/components/agents/, solune/frontend/src/components/board/Agent*.tsx, and solune/frontend/src/hooks/useAgent*.ts

**Checkpoint**: Audit inventory complete — story-specific implementation can begin

---

## Phase 3: User Story 1 — Modular Component Architecture (Priority: P1) 🎯 MVP

**Goal**: Decompose all oversized components to ≤250 lines, extract complex state into dedicated hooks, and ensure single-responsibility per file

**Independent Test**: Verify no component file exceeds 250 lines, each sub-component lives in `src/components/agents/` or `src/components/board/`, and complex state logic (>15 lines of useState/useEffect/useCallback) is extracted into dedicated hooks.

### Implementation for User Story 1

#### AgentsPanel Decomposition (565 → ≤250 lines)

- [ ] T010 [P] [US1] Extract search section into AgentSearch component in solune/frontend/src/components/agents/AgentSearch.tsx
- [ ] T011 [P] [US1] Extract sort controls into AgentSortControls component in solune/frontend/src/components/agents/AgentSortControls.tsx
- [ ] T012 [P] [US1] Extract spotlight/featured agents section into SpotlightSection component in solune/frontend/src/components/agents/SpotlightSection.tsx
- [ ] T013 [P] [US1] Extract agent grid listing into AgentGrid component in solune/frontend/src/components/agents/AgentGrid.tsx
- [ ] T014 [P] [US1] Extract pending agents section into PendingAgentsSection component in solune/frontend/src/components/agents/PendingAgentsSection.tsx
- [ ] T015 [US1] Extract complex state logic (8+ useState calls with interdependencies) from AgentsPanel into useAgentsPanel hook in solune/frontend/src/hooks/useAgentsPanel.ts
- [ ] T016 [US1] Refactor AgentsPanel to compose extracted sub-components — verify ≤250 lines in solune/frontend/src/components/agents/AgentsPanel.tsx

#### AddAgentModal Decomposition (520 → ≤250 lines)

- [ ] T017 [P] [US1] Extract form fields section into AgentFormFields component in solune/frontend/src/components/agents/AgentFormFields.tsx
- [ ] T018 [P] [US1] Extract form actions (submit/cancel/AI enhance) into AgentFormActions component in solune/frontend/src/components/agents/AgentFormActions.tsx
- [ ] T019 [US1] Extract form state and validation logic into useAgentForm hook in solune/frontend/src/hooks/useAgentForm.ts
- [ ] T020 [US1] Refactor AddAgentModal to compose extracted sub-components — verify ≤250 lines in solune/frontend/src/components/agents/AddAgentModal.tsx

#### AgentConfigRow Decomposition (480 → ≤250 lines)

- [ ] T021 [P] [US1] Extract constellation SVG visualization into ConstellationSvg component in solune/frontend/src/components/board/ConstellationSvg.tsx
- [ ] T022 [P] [US1] Extract column grid layout into ColumnGrid component in solune/frontend/src/components/board/ColumnGrid.tsx
- [ ] T023 [US1] Extract DnD orchestration logic into useAgentDnd hook in solune/frontend/src/hooks/useAgentDnd.ts
- [ ] T024 [US1] Refactor AgentConfigRow to compose extracted sub-components — verify ≤250 lines in solune/frontend/src/components/board/AgentConfigRow.tsx

#### AgentPresetSelector Decomposition (519 → ≤250 lines)

- [ ] T025 [P] [US1] Extract preset buttons group into PresetButtonGroup component in solune/frontend/src/components/board/PresetButtonGroup.tsx
- [ ] T026 [P] [US1] Extract saved pipelines dropdown into SavedPipelinesDropdown component in solune/frontend/src/components/board/SavedPipelinesDropdown.tsx
- [ ] T027 [US1] Extract preset selection logic into usePresetSelector hook in solune/frontend/src/hooks/usePresetSelector.ts
- [ ] T028 [US1] Refactor AgentPresetSelector to compose extracted sub-components — verify ≤250 lines in solune/frontend/src/components/board/AgentPresetSelector.tsx

#### Minor Extractions (Components slightly over 250 lines)

- [ ] T029 [P] [US1] Extract action buttons (edit, delete, icon change) into AgentCardActions component from AgentCard (286 → ≤250 lines) in solune/frontend/src/components/agents/AgentCardActions.tsx
- [ ] T030 [US1] Refactor AgentCard to compose AgentCardActions — verify ≤250 lines in solune/frontend/src/components/agents/AgentCard.tsx
- [ ] T031 [P] [US1] Extract editor form section into AgentEditorForm component from AgentInlineEditor (272 → ≤250 lines) in solune/frontend/src/components/agents/AgentEditorForm.tsx
- [ ] T032 [US1] Refactor AgentInlineEditor to compose AgentEditorForm — verify ≤250 lines in solune/frontend/src/components/agents/AgentInlineEditor.tsx
- [ ] T033 [P] [US1] Extract tile content and action buttons into AgentTileActions and AgentTileContent from AgentTile (308 → ≤250 lines) in solune/frontend/src/components/board/AgentTileActions.tsx and solune/frontend/src/components/board/AgentTileContent.tsx
- [ ] T034 [US1] Refactor AgentTile to compose extracted sub-components — verify ≤250 lines in solune/frontend/src/components/board/AgentTile.tsx

#### useAgentConfig Splitting

- [ ] T035 [US1] Extract `useAvailableAgents` into its own file at solune/frontend/src/hooks/useAvailableAgents.ts (currently co-located in useAgentConfig.ts)
- [ ] T036 [US1] Verify useAgentConfig.ts is properly scoped after extraction — review 349-line file for further splitting opportunities in solune/frontend/src/hooks/useAgentConfig.ts

#### Validation

- [ ] T037 [US1] Run line count check on all modified files — verify every component file is ≤250 lines across solune/frontend/src/components/agents/ and solune/frontend/src/components/board/
- [ ] T038 [US1] Run existing tests (`npx vitest run`) to verify no regressions from US1 decomposition changes

**Checkpoint**: User Story 1 complete — all components are ≤250 lines with proper separation of concerns

---

## Phase 4: User Story 2 — Reliable Loading, Error, and Empty States (Priority: P1)

**Goal**: Ensure every data-dependent section displays appropriate loading, error, and empty states — users never see a blank screen or cryptic error

**Independent Test**: Simulate loading delays, API failures, rate limit errors, and empty agent lists — verify appropriate UI states render for each scenario.

### Implementation for User Story 2

#### Loading States

- [ ] T039 [P] [US2] Verify loading state in AgentsPanel — CelestialLoader or skeleton grid renders during agent data fetch in solune/frontend/src/components/agents/AgentsPanel.tsx
- [ ] T040 [P] [US2] Verify loading state in AgentConfigRow — CelestialLoader renders while board data loads in solune/frontend/src/components/board/AgentConfigRow.tsx
- [ ] T041 [P] [US2] Add loading indicator for `savedPipelines` query in AgentPresetSelector — show spinner while pipelines load in solune/frontend/src/components/board/AgentPresetSelector.tsx

#### Error States

- [ ] T042 [P] [US2] Add/verify error handling for agent list query failure — user-friendly message with retry action in solune/frontend/src/components/agents/AgentsPanel.tsx
- [ ] T043 [P] [US2] Add rate limit error detection via `isRateLimitApiError()` with specific retry guidance in agent list error handling in solune/frontend/src/components/agents/AgentsPanel.tsx
- [ ] T044 [P] [US2] Add error handling for `pipelineList` query failure — show error state or graceful fallback in solune/frontend/src/pages/AgentsPage.tsx
- [ ] T045 [P] [US2] Add error handling for `pipelineAssignment` query failure — show error state or graceful fallback in solune/frontend/src/pages/AgentsPage.tsx
- [ ] T046 [P] [US2] Add error dismissal mechanism for persistent error messages in AgentPresetSelector in solune/frontend/src/components/board/AgentPresetSelector.tsx
- [ ] T047 [P] [US2] Verify BulkModelUpdateDialog handles mutation failure with visible error and dismissal in solune/frontend/src/components/agents/BulkModelUpdateDialog.tsx
- [ ] T048 [P] [US2] Add error handling for failed icon save in AgentIconPickerModal in solune/frontend/src/components/agents/AgentIconPickerModal.tsx

#### Empty States

- [ ] T049 [P] [US2] Verify empty agent catalog state displays meaningful empty state with "Create Agent" call-to-action in solune/frontend/src/components/agents/AgentsPanel.tsx
- [ ] T050 [P] [US2] Verify `ProjectSelectionEmptyState` renders correctly when no project is selected in solune/frontend/src/pages/AgentsPage.tsx
- [ ] T051 [P] [US2] Verify "No board columns available" message renders correctly when no columns exist in solune/frontend/src/pages/AgentsPage.tsx
- [ ] T052 [P] [US2] Verify search-no-results state displays "No matching agents" message when search yields zero results in solune/frontend/src/components/agents/AgentsPanel.tsx

#### Independent Section Loading

- [ ] T053 [US2] Verify multiple data sources (agents, pipelines, board columns) render independently — one failure does not block other sections in solune/frontend/src/pages/AgentsPage.tsx

#### Error Boundary

- [ ] T054 [US2] Verify page is wrapped in ErrorBoundary — recovery UI with retry on unexpected rendering error in solune/frontend/src/pages/AgentsPage.tsx

#### Validation

- [ ] T055 [US2] Run existing tests (`npx vitest run`) to verify no regressions from US2 changes

**Checkpoint**: User Story 2 complete — all loading, error, and empty states render correctly with clear user feedback

---

## Phase 5: User Story 3 — Accessible Agent Management (Priority: P2)

**Goal**: Achieve WCAG AA accessibility compliance — all interactive elements keyboard-accessible, proper ARIA attributes, focus management in dialogs, visible focus indicators

**Independent Test**: Navigate the entire Agents page using only keyboard (Tab, Enter, Space, Escape) — all interactive elements reachable and operable. Run automated accessibility audit (axe DevTools) for zero critical violations.

### Implementation for User Story 3

#### Focus Indicators

- [ ] T056 [P] [US3] Add `.celestial-focus` or `focus-visible:ring-*` class to all interactive elements in solune/frontend/src/components/agents/AgentCard.tsx
- [ ] T057 [P] [US3] Add `.celestial-focus` or `focus-visible:ring-*` class to all interactive elements in solune/frontend/src/components/agents/AgentInlineEditor.tsx
- [ ] T058 [P] [US3] Add `.celestial-focus` or `focus-visible:ring-*` class to all interactive elements in solune/frontend/src/components/board/AgentTile.tsx
- [ ] T059 [P] [US3] Add `.celestial-focus` or `focus-visible:ring-*` class to all interactive elements in solune/frontend/src/components/board/AgentPresetSelector.tsx
- [ ] T060 [P] [US3] Add `.celestial-focus` or `focus-visible:ring-*` class to all interactive elements in solune/frontend/src/components/board/AddAgentPopover.tsx
- [ ] T061 [P] [US3] Add `.celestial-focus` or `focus-visible:ring-*` class to all interactive elements in solune/frontend/src/components/board/AgentConfigRow.tsx

#### ARIA Attributes

- [ ] T062 [P] [US3] Fix AgentIconPickerModal — change `role="presentation"` to `role="dialog"` with `aria-modal="true"` in solune/frontend/src/components/agents/AgentIconPickerModal.tsx
- [ ] T063 [P] [US3] Add `role="status"` and `aria-live="polite"` to AgentSaveBar for screen reader announcements in solune/frontend/src/components/board/AgentSaveBar.tsx
- [ ] T064 [P] [US3] Add `role="region"` and `aria-label` to AgentConfigRow container in solune/frontend/src/components/board/AgentConfigRow.tsx
- [ ] T065 [P] [US3] Add `role="list"` to AgentColumnCell droppable container in solune/frontend/src/components/board/AgentColumnCell.tsx
- [ ] T066 [P] [US3] Add `role="listitem"` to AgentTile sortable tile in solune/frontend/src/components/board/AgentTile.tsx
- [ ] T067 [P] [US3] Add `aria-expanded` attribute to dropdown trigger in AddAgentPopover in solune/frontend/src/components/board/AddAgentPopover.tsx
- [ ] T068 [P] [US3] Add `aria-expanded` attribute to dropdown trigger in AgentPresetSelector in solune/frontend/src/components/board/AgentPresetSelector.tsx
- [ ] T069 [P] [US3] Add card-level accessible description to AgentCard in solune/frontend/src/components/agents/AgentCard.tsx
- [ ] T070 [P] [US3] Verify all form fields (search, agent name, description, system prompt) have visible labels or `aria-label` in solune/frontend/src/components/agents/AgentsPanel.tsx and solune/frontend/src/components/agents/AddAgentModal.tsx

#### Status Indicators

- [ ] T071 [US3] Verify all status indicators (active, pending_creation, pending_deletion) convey meaning through icon + text, not color alone — audit solune/frontend/src/components/agents/AgentCard.tsx and solune/frontend/src/components/board/AgentTile.tsx

#### Screen Reader Support

- [ ] T072 [P] [US3] Verify all decorative icons have `aria-hidden="true"` and all meaningful icons have `aria-label` across solune/frontend/src/components/agents/ and solune/frontend/src/components/board/

#### Focus Management

- [ ] T073 [P] [US3] Verify focus trapping in AddAgentModal — Tab does not escape to background in solune/frontend/src/components/agents/AddAgentModal.tsx
- [ ] T074 [P] [US3] Verify focus trapping in AgentIconPickerModal in solune/frontend/src/components/agents/AgentIconPickerModal.tsx
- [ ] T075 [P] [US3] Verify focus trapping in BulkModelUpdateDialog in solune/frontend/src/components/agents/BulkModelUpdateDialog.tsx
- [ ] T076 [P] [US3] Verify focus returns to trigger element on dialog close for all modals (AddAgentModal, IconPicker, BulkUpdate, ConfirmationDialog) in solune/frontend/src/components/agents/
- [ ] T077 [P] [US3] Verify focus restoration on AgentInlineEditor expand/collapse in solune/frontend/src/components/agents/AgentInlineEditor.tsx

#### Validation

- [ ] T078 [US3] Run existing tests (`npx vitest run`) to verify no regressions from US3 changes

**Checkpoint**: User Story 3 complete — Agents page is WCAG AA accessible with full keyboard operability

---

## Phase 6: User Story 4 — Polished Text, Copy, and User Experience (Priority: P2)

**Goal**: Ensure all user-facing text is final, consistent, and professional — verb-based labels, confirmation dialogs on destructive actions, user-friendly error messages, truncation with tooltips

**Independent Test**: Review all user-facing strings for placeholder text, verify destructive actions require confirmation, confirm success/error messages follow established format.

### Implementation for User Story 4

#### Placeholder Text Removal

- [ ] T079 [P] [US4] Audit and remove all placeholder text ("TODO", "Lorem ipsum", "Test") across solune/frontend/src/components/agents/ and solune/frontend/src/components/board/

#### Button Labels

- [ ] T080 [P] [US4] Verify all action buttons use verb-based labels ("Create Agent", "Save Settings", "Delete Agent") — audit and fix any noun-only labels across solune/frontend/src/components/agents/ and solune/frontend/src/components/board/

#### Destructive Action Confirmations

- [ ] T081 [P] [US4] Verify delete agent action uses ConfirmationDialog in solune/frontend/src/components/agents/AgentCard.tsx
- [ ] T082 [P] [US4] Verify clear pending agents action uses ConfirmationDialog in solune/frontend/src/components/agents/AgentsPanel.tsx
- [ ] T083 [P] [US4] Verify destructive preset changes (overwriting current assignments) use ConfirmationDialog in solune/frontend/src/components/board/AgentPresetSelector.tsx
- [ ] T084 [P] [US4] Verify remove agent from column uses ConfirmationDialog (or appropriate confirmation) in solune/frontend/src/components/board/AgentTile.tsx

#### Success Feedback

- [ ] T085 [P] [US4] Verify create agent mutation shows success feedback (toast or inline message) in solune/frontend/src/components/agents/AddAgentModal.tsx
- [ ] T086 [P] [US4] Verify update agent mutation shows success feedback in solune/frontend/src/components/agents/AgentInlineEditor.tsx
- [ ] T087 [P] [US4] Verify delete agent mutation shows success feedback in solune/frontend/src/components/agents/AgentCard.tsx
- [ ] T088 [P] [US4] Verify bulk model update mutation shows success feedback in solune/frontend/src/components/agents/BulkModelUpdateDialog.tsx
- [ ] T089 [P] [US4] Verify column assignment save mutation shows success feedback in solune/frontend/src/components/board/AgentSaveBar.tsx

#### Error Message Format

- [ ] T090 [US4] Verify all error messages follow format: "Could not [action]. [Reason, if known]. [Suggested next step]." — no raw error codes or stack traces across all Agents page mutation handlers

#### Text Truncation

- [ ] T091 [P] [US4] Add/verify `text-ellipsis` truncation with Tooltip for long agent names in solune/frontend/src/components/agents/AgentCard.tsx
- [ ] T092 [P] [US4] Add/verify `text-ellipsis` truncation with Tooltip for long agent names in solune/frontend/src/components/board/AgentTile.tsx
- [ ] T093 [P] [US4] Add/verify `text-ellipsis` truncation with Tooltip for long descriptions and URLs across solune/frontend/src/components/agents/AgentInlineEditor.tsx

#### Timestamp Formatting

- [ ] T094 [US4] Verify timestamps use relative format ("2 hours ago") for recent and absolute format for older — audit agent creation dates in solune/frontend/src/components/agents/AgentCard.tsx

#### Consistent Terminology

- [ ] T095 [US4] Verify consistent terminology across Agents page matches the rest of the app (e.g., "pipeline" not "workflow", no conflicting terms) in all agent-related components

#### Validation

- [ ] T096 [US4] Run existing tests (`npx vitest run`) to verify no regressions from US4 changes

**Checkpoint**: User Story 4 complete — all text, copy, and UX feedback is polished and professional

---

## Phase 7: User Story 5 — Consistent Styling and Responsive Layout (Priority: P3)

**Goal**: Ensure the page adapts gracefully across viewport sizes (768px–1920px), dark mode renders correctly, all styling uses Tailwind utilities with design tokens

**Independent Test**: View the Agents page at viewport widths 768px, 1024px, 1440px, and 1920px in both light and dark modes — no layout breaks, unreadable text, or hardcoded colors.

### Implementation for User Story 5

#### Hardcoded Color Replacement

- [ ] T097 [P] [US5] Replace hardcoded `border-emerald-300/40`, `bg-emerald-50/80` badge colors with `solar-chip-success` design tokens in solune/frontend/src/components/agents/AgentsPanel.tsx
- [ ] T098 [P] [US5] Replace hardcoded `text-green-700 dark:text-green-400` success colors with design-token equivalents in solune/frontend/src/components/agents/AgentCard.tsx
- [ ] T099 [P] [US5] Replace hardcoded source badge colors (`bg-blue-100 dark:bg-blue-900/30`, `bg-green-100 dark:bg-green-900/30`) with design-token badges in solune/frontend/src/components/board/AddAgentPopover.tsx
- [ ] T100 [P] [US5] Replace hardcoded inline SVG colors (inline `hsl(var(--gold))`, `hsl(var(--glow))` with magic opacity) with Tailwind CSS custom property references in solune/frontend/src/components/board/AgentTile.tsx
- [ ] T101 [P] [US5] Audit and normalize hardcoded amber colors (`border-amber-300/60`, `bg-amber-50/80`) in unsaved-change indicators in solune/frontend/src/components/agents/AddAgentModal.tsx and solune/frontend/src/components/agents/AgentInlineEditor.tsx

#### Inline Style Removal

- [ ] T102 [P] [US5] Replace any inline `style={}` attributes with Tailwind utility classes using `cn()` across solune/frontend/src/components/agents/ and solune/frontend/src/components/board/

#### Spacing Normalization

- [ ] T103 [P] [US5] Replace arbitrary spacing values (e.g., `p-[13px]`) with standard Tailwind spacing scale values across solune/frontend/src/components/agents/ and solune/frontend/src/components/board/

#### Responsive Layout Verification

- [ ] T104 [P] [US5] Verify two-panel grid layout (`xl:grid-cols-[minmax(0,1fr)_22rem]`) stacks correctly below xl breakpoint in solune/frontend/src/pages/AgentsPage.tsx
- [ ] T105 [P] [US5] Verify agent card grid (`md:grid-cols-2 xl:grid-cols-3`) has no overflow at each breakpoint in solune/frontend/src/components/agents/AgentsPanel.tsx
- [ ] T106 [P] [US5] Add `overflow-x-auto` wrapper to Orbital Map dynamic grid for narrow viewports in solune/frontend/src/components/board/AgentConfigRow.tsx
- [ ] T107 [P] [US5] Verify modals display full-width on smaller viewports in solune/frontend/src/components/agents/AddAgentModal.tsx, solune/frontend/src/components/agents/AgentIconPickerModal.tsx, and solune/frontend/src/components/agents/BulkModelUpdateDialog.tsx
- [ ] T108 [P] [US5] Verify touch targets are minimum 44×44px on all interactive elements on mobile in solune/frontend/src/components/agents/ and solune/frontend/src/components/board/
- [ ] T109 [P] [US5] Verify AgentPresetSelector dropdown positioning doesn't go off-screen on narrow viewports in solune/frontend/src/components/board/AgentPresetSelector.tsx
- [ ] T110 [P] [US5] Verify AddAgentPopover portal positioning doesn't overflow viewport on narrow screens in solune/frontend/src/components/board/AddAgentPopover.tsx

#### Card/Section Consistency

- [ ] T111 [US5] Verify all content sections use Card component from `src/components/ui/card.tsx` with consistent padding and border-radius across Agents page components

#### Dark Mode Verification

- [ ] T112 [US5] Test light mode and dark mode switching — verify all elements render correctly with no visual artifacts across all modified components

#### Validation

- [ ] T113 [US5] Run existing tests (`npx vitest run`) to verify no regressions from US5 changes

**Checkpoint**: User Story 5 complete — Agents page is responsive, dark-mode-safe, and uses only design tokens

---

## Phase 8: User Story 6 — Comprehensive Test Coverage (Priority: P3)

**Goal**: Add hook tests via `renderHook()`, component interaction tests, and edge case coverage for all Agents page functionality

**Independent Test**: Run `npx vitest run --reporter=verbose src/components/agents/ src/components/board/ src/hooks/useAgent` — all tests pass covering happy path, error, loading, and edge cases.

### Tests for User Story 6

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation fixes**

#### Hook Tests

- [ ] T114 [P] [US6] Create hook test for useAgents (useAgentsList) — happy path, error, loading, rate limit in solune/frontend/src/hooks/useAgents.test.ts
- [ ] T115 [P] [US6] Create hook test for useAgents mutations (useCreateAgent, useUpdateAgent, useDeleteAgent) — success, error, cache invalidation in solune/frontend/src/hooks/useAgents.test.ts
- [ ] T116 [P] [US6] Create hook test for useBulkUpdateModels — success, error, cache invalidation in solune/frontend/src/hooks/useAgents.test.ts
- [ ] T117 [P] [US6] Create hook test for useAgentConfig — state mutations, dirty tracking, save, discard in solune/frontend/src/hooks/useAgentConfig.test.ts
- [ ] T118 [P] [US6] Create hook test for useAvailableAgents — happy path, error, loading in solune/frontend/src/hooks/useAvailableAgents.test.ts
- [ ] T119 [P] [US6] Create hook test for useAgentTools — tool list query, add/remove mutations in solune/frontend/src/hooks/useAgentTools.test.ts

#### Component Interaction Tests

- [ ] T120 [P] [US6] Verify/update AgentsPanel test coverage — add tests for search filtering, sort toggle, empty state, error state in solune/frontend/src/components/agents/AgentsPanel.test.tsx
- [ ] T121 [P] [US6] Verify/update AddAgentModal test coverage — add tests for form validation, submit flow, edit mode, error handling in solune/frontend/src/components/agents/AddAgentModal.test.tsx
- [ ] T122 [P] [US6] Create AgentCard test — click actions (edit, delete), status rendering, truncation in solune/frontend/src/components/agents/AgentCard.test.tsx

#### Edge Case Coverage

- [ ] T123 [P] [US6] Add test for empty agent list state rendering in solune/frontend/src/components/agents/AgentsPanel.test.tsx
- [ ] T124 [P] [US6] Add test for rate limit error handling and display in solune/frontend/src/components/agents/AgentsPanel.test.tsx
- [ ] T125 [P] [US6] Add test for long strings (agent name >200 chars) truncation behavior in solune/frontend/src/components/agents/AgentCard.test.tsx
- [ ] T126 [P] [US6] Add test for null/missing optional fields (iconName, statusColumn, githubIssueNumber) rendering in solune/frontend/src/components/agents/AgentCard.test.tsx

#### Test Convention Compliance

- [ ] T127 [US6] Verify all new tests follow codebase conventions: `vi.mock('@/services/api', ...)`, `renderHook`, `waitFor`, `createWrapper()` — no snapshot tests

#### Validation

- [ ] T128 [US6] Run full agent-related test suite (`npx vitest run --reporter=verbose src/components/agents/ src/components/board/ src/hooks/useAgent`) to verify all tests pass

**Checkpoint**: User Story 6 complete — comprehensive test coverage for hooks, components, and edge cases

---

## Phase 9: User Story 7 — Performance and Code Hygiene (Priority: P3)

**Goal**: Eliminate dead code, fix type safety issues, optimize performance, and ensure ESLint compliance across all agent-related files

**Independent Test**: Run `npx eslint` with zero warnings, `npx tsc --noEmit` with zero errors, verify no `any` types or `console.log` statements exist, confirm memoization on expensive computations.

### Implementation for User Story 7

#### Type Safety

- [ ] T129 [P] [US7] Eliminate all `any` types in solune/frontend/src/components/agents/ — replace with proper typed interfaces
- [ ] T130 [P] [US7] Eliminate all `any` types in solune/frontend/src/components/board/Agent*.tsx — replace with proper typed interfaces
- [ ] T131 [P] [US7] Eliminate all type assertions (`as`) in agent-related files — replace with type guards or discriminated unions in solune/frontend/src/components/agents/ and solune/frontend/src/hooks/useAgent*.ts
- [ ] T132 [P] [US7] Add explicit return type annotations to custom hooks where return type is ambiguous in solune/frontend/src/hooks/useAgents.ts, solune/frontend/src/hooks/useAgentConfig.ts, and solune/frontend/src/hooks/useAgentTools.ts
- [ ] T133 [P] [US7] Verify event handler types are explicit (React.FormEvent, React.MouseEvent) — no generic `any` handlers across solune/frontend/src/components/agents/

#### Dead Code Removal

- [ ] T134 [P] [US7] Remove unused imports across all agent-related files in solune/frontend/src/components/agents/ and solune/frontend/src/components/board/
- [ ] T135 [P] [US7] Remove commented-out code blocks and unreachable branches across all agent-related files
- [ ] T136 [P] [US7] Remove all `console.log` statements across all agent-related files

#### Import Cleanup

- [ ] T137 [US7] Verify all imports use `@/` alias — replace any relative paths (`../../`) with aliased imports across all agent-related files

#### React Query Patterns

- [ ] T138 [P] [US7] Verify query key factory pattern follows `agentKeys.all / .list(id) / .detail(id)` convention in solune/frontend/src/hooks/useAgents.ts
- [ ] T139 [P] [US7] Verify `staleTime` is configured appropriately (30s for agent lists, 60s for settings-like data) in solune/frontend/src/hooks/useAgents.ts and solune/frontend/src/hooks/useAgentConfig.ts
- [ ] T140 [P] [US7] Verify all `useMutation` calls have `onError` handling that surfaces user-visible feedback in solune/frontend/src/hooks/useAgents.ts
- [ ] T141 [P] [US7] Verify successful mutations call `invalidateQueries` with correct keys in solune/frontend/src/hooks/useAgents.ts
- [ ] T142 [P] [US7] Verify no duplicate API calls between parent and child components on the Agents page

#### Performance Optimization

- [ ] T143 [P] [US7] Verify list renders use stable keys (`key={item.id}`, not `key={index}`) across all agent-related components
- [ ] T144 [P] [US7] Verify expensive computations (sorting, filtering, usage counting) are wrapped in `useMemo` in solune/frontend/src/components/agents/AgentsPanel.tsx
- [ ] T145 [P] [US7] Verify `useDeferredValue` prevents layout shift during search filtering in solune/frontend/src/components/agents/AgentsPanel.tsx
- [ ] T146 [P] [US7] Verify callbacks passed to memoized children use `useCallback` where appropriate across agent-related components

#### Magic String Elimination

- [ ] T147 [US7] Extract repeated strings (status values, route paths, query keys) into constants — verify no magic strings in agent-related files

#### ESLint Compliance

- [ ] T148 [US7] Run `npx eslint src/pages/AgentsPage.tsx src/components/agents/ src/components/board/` — fix all warnings to reach zero warnings

#### Validation

- [ ] T149 [US7] Run full type-check (`npm run type-check`) and lint (`npm run lint`) — zero errors, zero warnings
- [ ] T150 [US7] Run existing tests (`npx vitest run`) to verify no regressions from US7 changes

**Checkpoint**: User Story 7 complete — clean, well-typed, performant code with zero ESLint warnings

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, audit summary, and cross-cutting improvements

- [ ] T151 [P] Run full test suite (`npx vitest run`), type-check (`npm run type-check`), and lint (`npm run lint`) — confirm zero regressions in solune/frontend/
- [ ] T152 [P] Verify all changes work correctly in both light and dark modes across all modified components
- [ ] T153 [P] Verify keyboard-only navigation through entire Agents page — Tab through all interactive elements, Enter/Space to activate
- [ ] T154 Produce audit summary listing all findings, changes made, and deferred improvements
- [ ] T155 Run quickstart.md validation — verify all checklist items from specs/043-agents-page-audit/quickstart.md are addressed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories (establishes audit inventory)
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) — component decomposition
- **User Story 2 (Phase 4)**: Depends on US1 (Phase 3) — loading/error/empty states built on decomposed components
- **User Story 3 (Phase 5)**: Depends on US1 (Phase 3) — accessibility added to decomposed components
- **User Story 4 (Phase 6)**: Depends on US1 (Phase 3) — text/copy polish on decomposed components
- **User Story 5 (Phase 7)**: Depends on US1 (Phase 3) — styling applied to decomposed components
- **User Story 6 (Phase 8)**: Depends on US1–US5 — tests cover final component shapes after all refactoring
- **User Story 7 (Phase 9)**: Depends on US1–US5 — code hygiene applied to final component shapes
- **Polish (Phase 10)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — MUST be first (all other stories depend on decomposed components)
- **User Story 2 (P1)**: Depends on US1 — states built into decomposed component structure
- **User Story 3 (P2)**: Can start after US1 — can run parallel with US2, US4, US5
- **User Story 4 (P2)**: Can start after US1 — can run parallel with US2, US3, US5
- **User Story 5 (P3)**: Can start after US1 — can run parallel with US2, US3, US4
- **User Story 6 (P3)**: Depends on US1–US5 — tests must cover final component shapes
- **User Story 7 (P3)**: Depends on US1–US5 — hygiene cleanup is final pass before tests

### Within Each User Story

- Parallel [P] tasks can be worked on simultaneously (they target different files)
- Non-[P] tasks (integration, validation, test runs) should be done after all [P] tasks in that story
- Each story's final task is always a test run to verify no regressions
- US1: Decomposition tasks within a component must be sequential (extract → refactor parent)

### Parallel Opportunities

- All Setup tasks (T001–T004) marked [P] can run in parallel
- All Foundational audit tasks (T005–T009) marked [P] can run in parallel
- US1: Extractions across different components (AgentsPanel, AddAgentModal, AgentConfigRow, AgentPresetSelector, AgentCard, AgentInlineEditor, AgentTile) can run in parallel
- US2: All loading/error/empty state tasks (T039–T052) target different files and can run in parallel
- US3: Focus indicator tasks (T056–T061) can run in parallel; ARIA tasks (T062–T072) can run in parallel; focus management tasks (T073–T077) can run in parallel
- US4: All text/copy tasks (T079–T095) can run in parallel
- US5: All styling tasks (T097–T112) can run in parallel
- US6: All hook tests (T114–T119) can run in parallel; all component tests (T120–T126) can run in parallel
- US7: All type safety, dead code, and React Query tasks can run in parallel
- **Cross-story parallelism**: US2, US3, US4, US5 can all be worked on simultaneously after US1 completes

---

## Parallel Example: User Story 1

```bash
# Launch all AgentsPanel extraction tasks together (independent new files):
Task T010: "Extract AgentSearch in AgentSearch.tsx"
Task T011: "Extract AgentSortControls in AgentSortControls.tsx"
Task T012: "Extract SpotlightSection in SpotlightSection.tsx"
Task T013: "Extract AgentGrid in AgentGrid.tsx"
Task T014: "Extract PendingAgentsSection in PendingAgentsSection.tsx"

# In parallel, launch extractions for OTHER components:
Task T017: "Extract AgentFormFields in AgentFormFields.tsx"
Task T018: "Extract AgentFormActions in AgentFormActions.tsx"
Task T021: "Extract ConstellationSvg in ConstellationSvg.tsx"
Task T022: "Extract ColumnGrid in ColumnGrid.tsx"
Task T025: "Extract PresetButtonGroup in PresetButtonGroup.tsx"
Task T026: "Extract SavedPipelinesDropdown in SavedPipelinesDropdown.tsx"
Task T029: "Extract AgentCardActions in AgentCardActions.tsx"
Task T031: "Extract AgentEditorForm in AgentEditorForm.tsx"
Task T033: "Extract AgentTileActions and AgentTileContent"
```

## Parallel Example: User Story 6

```bash
# Launch all hook tests together (all are independent test files):
Task T114: "Test useAgentsList hook in useAgents.test.ts"
Task T115: "Test useAgents mutations in useAgents.test.ts"
Task T116: "Test useBulkUpdateModels in useAgents.test.ts"
Task T117: "Test useAgentConfig in useAgentConfig.test.ts"
Task T118: "Test useAvailableAgents in useAvailableAgents.test.ts"
Task T119: "Test useAgentTools in useAgentTools.test.ts"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (verify baseline)
2. Complete Phase 2: Foundational (audit inventory)
3. Complete Phase 3: User Story 1 — component decomposition (P1)
4. Complete Phase 4: User Story 2 — loading/error/empty states (P1)
5. **STOP and VALIDATE**: Run full test suite, verify all page states, check no component exceeds 250 lines
6. Deploy/demo if ready — page is modular and state-complete

### Incremental Delivery

1. Complete Setup + Foundational → Audit baseline established
2. Add User Story 1 (decomposition) → Test independently → all components ≤250 lines ✓
3. Add User Story 2 (page states) → Test independently → all states render correctly ✓
4. Add User Story 3 (accessibility) → Test independently → WCAG AA compliant ✓
5. Add User Story 4 (text/copy) → Test independently → polished UX ✓
6. Add User Story 5 (styling/responsive) → Test independently → responsive + dark mode ✓
7. Add User Story 6 (test coverage) → Test independently → comprehensive tests ✓
8. Add User Story 7 (code hygiene) → Test independently → zero warnings ✓
9. Polish phase → Final validation and audit summary

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. All developers work on US1 (decomposition) — split by component:
   - Developer A: AgentsPanel + AddAgentModal
   - Developer B: AgentConfigRow + AgentPresetSelector
   - Developer C: AgentCard + AgentInlineEditor + AgentTile
3. Once US1 is done, split remaining stories:
   - Developer A: User Story 2 (page states)
   - Developer B: User Story 3 (accessibility)
   - Developer C: User Story 4 (text/copy)
   - Developer D: User Story 5 (styling)
4. After US2–US5 complete:
   - Developer A: User Story 6 (test coverage)
   - Developer B: User Story 7 (code hygiene)
5. Final → Polish phase

---

## Notes

- [P] tasks = different files, no dependencies — safe for parallel execution
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable after US1 is done
- Tests explicitly requested in US6 (P3) per FR-019 and FR-020
- Existing tests (AgentsPanel, AddAgentModal, AgentSaveBar, AgentTile, ThemedAgentIcon) must pass after each phase
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- This is a frontend-only audit — no backend changes required
- All ~20 components in scope are under `solune/frontend/src/components/agents/`, `solune/frontend/src/components/board/`, and `solune/frontend/src/pages/AgentsPage.tsx`
- The 250-line limit may be exceeded by up to 10% (275 lines) if splitting would create artificial boundaries that harm readability
