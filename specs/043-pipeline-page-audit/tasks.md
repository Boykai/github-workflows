# Tasks: Pipeline Page Audit

**Input**: Design documents from `/specs/043-pipeline-page-audit/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/component-contracts.yaml, quickstart.md

**Tests**: Tests are NOT mandated for this audit. Existing tests (PipelineBoard, PipelineFlowGraph, StageCard, AgentNode, SavedWorkflowsList, usePipelineConfig, usePipelineReducer) will be verified to pass. Test tasks appear only in US6 (P3 — code quality) where the spec explicitly calls for test coverage verification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. Six user stories span P1–P3. US1 and US2 (P1) form the MVP.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Frontend**: `solune/frontend/src/`
- **Page**: `solune/frontend/src/pages/AgentsPipelinePage.tsx`
- **Components**: `solune/frontend/src/components/pipeline/`
- **Hooks**: `solune/frontend/src/hooks/usePipeline*.ts`
- **Types**: `solune/frontend/src/types/index.ts`
- **API Service**: `solune/frontend/src/services/api.ts`
- **Utilities**: `solune/frontend/src/utils/`, `solune/frontend/src/lib/utils.ts`
- **Shared UI**: `solune/frontend/src/components/ui/`, `solune/frontend/src/components/common/`
- **Design tokens**: `solune/frontend/src/index.css`

---

## Phase 1: Setup

**Purpose**: Establish baseline state and verify existing Pipeline page functionality

- [ ] T001 Install frontend dependencies via `cd solune/frontend && npm install`
- [ ] T002 [P] Run baseline tests for pipeline files via `cd solune/frontend && npx vitest run src/components/pipeline/ src/hooks/usePipeline*` and record pass/fail counts
- [ ] T003 [P] Run baseline lint on pipeline files via `cd solune/frontend && npx eslint src/pages/AgentsPipelinePage.tsx src/components/pipeline/ src/hooks/usePipeline*` and record warning count
- [ ] T004 [P] Run baseline type-check via `cd solune/frontend && npx tsc --noEmit` and record error count
- [ ] T005 Record line counts for all pipeline files: `solune/frontend/src/pages/AgentsPipelinePage.tsx` (~417), all 18 files in `solune/frontend/src/components/pipeline/`, and all 7 hooks in `solune/frontend/src/hooks/usePipeline*.ts`

---

## Phase 2: Foundational (Discovery & Assessment)

**Purpose**: Read all pipeline code, catalog current state against the audit checklist, and identify every issue that needs fixing

**⚠️ CRITICAL**: No user story work can begin until this phase is complete — the assessment produces the findings that guide all subsequent phases

- [ ] T006 Read and catalog `solune/frontend/src/pages/AgentsPipelinePage.tsx` — note line count, sub-components composed, hooks used, API calls, state variables, and prop passing depth
- [ ] T007 [P] Read and catalog all 18 component files in `solune/frontend/src/components/pipeline/` — note line counts, props interfaces, states handled (loading/error/empty), ARIA attributes present, and design token usage
- [ ] T008 [P] Read and catalog all 7 hooks: `solune/frontend/src/hooks/usePipelineConfig.ts` (~232 lines), `solune/frontend/src/hooks/usePipelineBoardMutations.ts` (~418 lines), `solune/frontend/src/hooks/usePipelineReducer.ts` (~115 lines), `solune/frontend/src/hooks/usePipelineModelOverride.ts` (~98 lines), `solune/frontend/src/hooks/usePipelineValidation.ts` (~38 lines), `solune/frontend/src/hooks/useSelectedPipeline.ts`, `solune/frontend/src/hooks/useConfirmation.ts` — note return types, error handling, React Query usage, and mutation onError handlers
- [ ] T009 [P] Read pipeline-related types in `solune/frontend/src/types/index.ts` — verify PipelineConfig, PipelineStage, ExecutionGroup, PipelineAgentNode, PipelineConfigSummary, PipelineValidationErrors, PipelineModelOverride, PipelineBoardState match data-model.md; note any `any` types or unsafe assertions
- [ ] T010 [P] Read pipeline API group in `solune/frontend/src/services/api.ts` — catalog all 9 pipeline endpoints (list, get, create, update, delete, seedPresets, getAssignment, setAssignment, launch), verify React Query key conventions, and note staleTime/cacheTime configuration
- [ ] T011 [P] Read utility files `solune/frontend/src/utils/rateLimit.ts`, `solune/frontend/src/utils/formatTime.ts`, `solune/frontend/src/utils/formatAgentName.ts` — confirm isRateLimitApiError(), formatTimeAgo, formatAgentName are available for use
- [ ] T012 Score each audit checklist item from the parent issue (10 categories, ~60 items) as Pass / Fail / N/A — produce a findings summary documenting every issue discovered, grouped by user story

**Checkpoint**: Discovery complete — every issue is identified, categorized, and mapped to a user story. Implementation can now proceed in priority order.

---

## Phase 3: User Story 1 — Bug-Free and Complete Page States (Priority: P1) 🎯 MVP

**Goal**: Ensure the Pipeline page displays correctly in every state — loading, empty, populated, saving, and error — so users always understand what is happening and never encounter a broken or confusing view (FR-001 through FR-006, FR-008)

**Independent Test**: Trigger each page state (loading, no project selected, empty pipeline board, populated board, save in progress, save error, rate limit error, deleted pipeline, section-level failure) and verify each renders correctly with appropriate messaging and recovery actions.

### Loading State (FR-001)

- [ ] T013 [US1] Audit loading state in `solune/frontend/src/pages/AgentsPipelinePage.tsx` — verify CelestialLoader is displayed while pipeline data fetches, never a blank screen; if missing, add `<CelestialLoader size="md" />` centered in the content area with `role="status"` and `aria-live="polite"`

### No-Project-Selected State (FR-002)

- [ ] T014 [US1] Audit no-project-selected state in `solune/frontend/src/pages/AgentsPipelinePage.tsx` — verify `<ProjectSelectionEmptyState />` from `solune/frontend/src/components/common/ProjectSelectionEmptyState.tsx` renders with clear guidance when no project is selected; fix if missing or broken

### Empty Board State (FR-003)

- [ ] T015 [US1] Audit empty pipeline board state in `solune/frontend/src/components/pipeline/PipelineBoard.tsx` — verify meaningful empty state renders when pipeline has no stages, including an illustrative icon and a "Create Pipeline" or "Add Stage" call-to-action; add if missing

### Error States (FR-004, FR-005, FR-006)

- [ ] T016 [US1] Audit save error handling in `solune/frontend/src/hooks/usePipelineConfig.ts` and `solune/frontend/src/hooks/usePipelineBoardMutations.ts` — verify all `useMutation` onError handlers format errors as "Could not [action]. [Reason, if known]. [Suggested next step]." with no raw error codes or stack traces; fix non-compliant handlers
- [ ] T017 [P] [US1] Audit rate limit error detection in `solune/frontend/src/hooks/usePipelineConfig.ts` — verify `isRateLimitApiError()` from `solune/frontend/src/utils/rateLimit.ts` is used in mutation onError to show specific rate-limit messaging; add if missing
- [ ] T018 [P] [US1] Audit rate limit error detection in `solune/frontend/src/hooks/usePipelineBoardMutations.ts` — verify all mutations (save, delete, duplicate, assign, launch) use `isRateLimitApiError()` for rate-limit-specific messaging; add if missing
- [ ] T019 [US1] Audit section-level error isolation in `solune/frontend/src/pages/AgentsPipelinePage.tsx` — verify pipeline list, pipeline assignment, and analytics sections each render their own loading/error states independently so one failure does not block other sections (FR-006); refactor if coupled

### Section-Level Error States (FR-006)

- [ ] T020 [P] [US1] Audit error state in `solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx` — verify pipeline list loading failure shows error message with retry action inside the saved workflows section only; add if missing
- [ ] T021 [P] [US1] Audit error state in `solune/frontend/src/components/pipeline/PipelineAnalytics.tsx` — verify analytics loading failure shows error message with retry action inside the analytics section only; add if missing
- [ ] T022 [P] [US1] Audit empty state in `solune/frontend/src/components/pipeline/PipelineAnalytics.tsx` — verify "No pipeline executions yet" or equivalent empty state renders when analytics data is empty, not blank charts or zeroed metrics

### Success Feedback (FR-008)

- [ ] T023 [US1] Audit success feedback for all pipeline mutations in `solune/frontend/src/hooks/usePipelineConfig.ts` and `solune/frontend/src/hooks/usePipelineBoardMutations.ts` — verify save, create, duplicate, delete, and assign operations show visible success feedback (toast notification or inline message) on completion; add toast calls if missing

### Edge Cases

- [ ] T024 [US1] Audit deleted pipeline fallback — verify that when a user selects a pipeline that has been deleted externally, the system handles missing data gracefully in `solune/frontend/src/pages/AgentsPipelinePage.tsx` without crashing, showing a meaningful fallback message
- [ ] T025 [US1] Audit rapid save protection — verify save button is disabled during `isSaving` state in `solune/frontend/src/components/pipeline/PipelineToolbar.tsx` to prevent duplicate API calls from rapid clicks
- [ ] T026 [P] [US1] Audit empty save validation — verify saving a pipeline with zero stages displays a clear validation error message in `solune/frontend/src/hooks/usePipelineValidation.ts`; extend validation if missing
- [ ] T027 [P] [US1] Audit missing agent indicator — verify that when an agent referenced in a pipeline stage is deleted from the system, `solune/frontend/src/components/pipeline/AgentNode.tsx` displays the agent gracefully with a "missing agent" indicator rather than crashing

**Checkpoint**: Pipeline page renders correctly in all states — loading, empty, populated, saving, error, rate-limited, and edge cases. Each section handles errors independently. Users always see appropriate messaging.

---

## Phase 4: User Story 2 — Accessible Pipeline Page (Priority: P1)

**Goal**: Ensure the Pipeline page is fully accessible via keyboard navigation and assistive technology so all users can create, edit, and manage pipelines without barriers (FR-013 through FR-016, FR-026)

**Independent Test**: Navigate the entire Pipeline page using only a keyboard; run automated accessibility scanner; verify screen reader announcements for toolbar, stage cards, agent nodes, execution groups, saved workflow cards, and dialogs.

### Keyboard Navigation (FR-013)

- [ ] T028 [US2] Audit keyboard accessibility of toolbar buttons in `solune/frontend/src/components/pipeline/PipelineToolbar.tsx` — verify all buttons (Save, Discard, Delete, Copy) are reachable via Tab and activated via Enter/Space with visible `celestial-focus` or `focus-visible:` ring styles; fix if missing
- [ ] T029 [P] [US2] Audit keyboard accessibility of stage name inline editing in `solune/frontend/src/components/pipeline/StageCard.tsx` — verify stage name input is reachable, editable, and confirm/cancel via Enter/Escape with visible focus indicator
- [ ] T030 [P] [US2] Audit keyboard accessibility of execution mode toggle in `solune/frontend/src/components/pipeline/ExecutionGroupCard.tsx` — verify toggle is reachable via Tab and activated via Enter/Space
- [ ] T031 [P] [US2] Audit keyboard accessibility of model selection in `solune/frontend/src/components/pipeline/ModelSelector.tsx` — verify dropdown is keyboard navigable (arrow keys to move, Enter to select, Escape to close)
- [ ] T032 [P] [US2] Audit keyboard accessibility of agent picker/add controls in `solune/frontend/src/components/pipeline/StageCard.tsx` — verify "Add Agent" button and any agent picker dropdown are keyboard accessible

### Saved Workflow Cards (FR-026)

- [ ] T033 [US2] Audit saved workflow cards in `solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx` — verify each pipeline card is rendered as a proper interactive element (`<button>` or `<a>`) — not a styled `<div>` with onClick — so it responds to keyboard activation (Enter/Space) and is announced correctly by screen readers; refactor if non-compliant

### Dialog Focus Management (FR-014)

- [ ] T034 [US2] Audit focus management in `solune/frontend/src/components/pipeline/UnsavedChangesDialog.tsx` — verify focus is trapped within the dialog when open, Escape closes it, and focus returns to the triggering element on close; fix if missing
- [ ] T035 [P] [US2] Audit focus management for all confirmation dialogs on the Pipeline page (delete pipeline, remove stage, remove agent) — verify each uses `<ConfirmationDialog>` from `solune/frontend/src/components/ui/confirmation-dialog.tsx` with proper focus trapping

### ARIA Attributes

- [ ] T036 [US2] Audit ARIA attributes on execution mode toggle in `solune/frontend/src/components/pipeline/ExecutionGroupCard.tsx` — verify toggle has `role="switch"` with `aria-checked` state reflecting current mode (sequential/parallel); add if missing
- [ ] T037 [P] [US2] Audit ARIA attributes on model selector dropdown in `solune/frontend/src/components/pipeline/ModelSelector.tsx` — verify `aria-haspopup="listbox"`, `aria-expanded`, options have `role="option"` with `aria-selected`; add if missing
- [ ] T038 [P] [US2] Audit ARIA attributes on saved workflow list in `solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx` — verify selected pipeline has `aria-selected="true"` or `aria-current="true"`, assigned pipeline has visual + text indicator

### Form Labels (FR-016)

- [ ] T039 [US2] Audit form input labels for pipeline name input in `solune/frontend/src/pages/AgentsPipelinePage.tsx` or `solune/frontend/src/components/pipeline/PipelineToolbar.tsx` — verify input has visible label or `aria-label`; add if missing
- [ ] T040 [P] [US2] Audit form input labels for stage name inputs in `solune/frontend/src/components/pipeline/StageCard.tsx` — verify each inline editing input has `aria-label` (e.g., "Stage name"); add if missing

### Status Indicators (FR-015)

- [ ] T041 [US2] Audit status indicators across all pipeline components — verify stage execution mode, pipeline save state, assignment status, and analytics metrics convey meaning through icon + text, not color alone; fix any color-only indicators in `solune/frontend/src/components/pipeline/ExecutionGroupCard.tsx`, `solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx`, and `solune/frontend/src/components/pipeline/PipelineAnalytics.tsx`

### Screen Reader Text

- [ ] T042 [US2] Audit decorative icons in all pipeline components — verify all decorative Lucide icons have `aria-hidden="true"` and all meaningful icons have `aria-label`; fix in `solune/frontend/src/components/pipeline/AgentNode.tsx`, `solune/frontend/src/components/pipeline/StageCard.tsx`, `solune/frontend/src/components/pipeline/PipelineToolbar.tsx`, and `solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx`
- [ ] T043 [P] [US2] Audit validation error association in `solune/frontend/src/components/pipeline/PipelineToolbar.tsx` and `solune/frontend/src/components/pipeline/StageCard.tsx` — verify validation error messages are programmatically linked to input fields via `aria-describedby`; add if missing

**Checkpoint**: Pipeline page is fully keyboard navigable, screen reader accessible, and WCAG AA compliant. All interactive elements have appropriate ARIA attributes, focus indicators, and labels.

---

## Phase 5: User Story 3 — Consistent and Polished User Experience (Priority: P2)

**Goal**: Ensure the Pipeline page looks and feels consistent with the rest of the application — professional copy, proper feedback for all actions, design token compliance, and a polished interface (FR-017 through FR-019, FR-007, FR-008)

**Independent Test**: Visually compare the Pipeline page against other pages; verify all text is final and consistent; check destructive actions require confirmation; validate mutations provide success feedback; test light/dark mode.

### Design Token Compliance (FR-017)

- [ ] T044 [US3] Audit `solune/frontend/src/pages/AgentsPipelinePage.tsx` for hardcoded colors, inline styles, or off-palette values — replace with Celestial design tokens (`bg-card`, `text-card-foreground`, `border-border`, `bg-muted`, etc.) and `cn()` helper; remove any `style={}` attributes
- [ ] T045 [P] [US3] Audit `solune/frontend/src/components/pipeline/PipelineBoard.tsx` for hardcoded colors and non-token styling — replace with design tokens and ensure `celestial-panel` class is used for board container
- [ ] T046 [P] [US3] Audit `solune/frontend/src/components/pipeline/StageCard.tsx` for hardcoded colors — replace with Card component from `solune/frontend/src/components/ui/card.tsx` and design tokens for all visual properties
- [ ] T047 [P] [US3] Audit `solune/frontend/src/components/pipeline/ExecutionGroupCard.tsx` for hardcoded colors — replace with design tokens; ensure mode indicator uses token-based styling
- [ ] T048 [P] [US3] Audit `solune/frontend/src/components/pipeline/AgentNode.tsx` for hardcoded colors — replace with design tokens for card/chip styling
- [ ] T049 [P] [US3] Audit `solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx` for hardcoded colors — replace with design tokens; ensure selected/assigned states use token-based highlighting
- [ ] T050 [P] [US3] Audit `solune/frontend/src/components/pipeline/PipelineAnalytics.tsx` for hardcoded colors — replace with design tokens for charts, metrics, and section containers
- [ ] T051 [P] [US3] Audit `solune/frontend/src/components/pipeline/PipelineFlowGraph.tsx` for hardcoded colors in SVG/canvas rendering — replace with CSS custom properties from design tokens for all graph elements; verify dark mode support
- [ ] T052 [P] [US3] Audit `solune/frontend/src/components/pipeline/ModelSelector.tsx` for hardcoded colors — replace with design tokens consistent with other selectors in the app
- [ ] T053 [P] [US3] Audit `solune/frontend/src/components/pipeline/PipelineToolbar.tsx` for hardcoded colors — verify button variants use standard primary/destructive/outline tokens
- [ ] T054 [P] [US3] Audit `solune/frontend/src/components/pipeline/PipelineModelDropdown.tsx`, `solune/frontend/src/components/pipeline/PresetBadge.tsx`, and `solune/frontend/src/components/pipeline/ParallelStageGroup.tsx` for hardcoded colors — replace with design tokens
- [ ] T055 [P] [US3] Audit `solune/frontend/src/components/pipeline/UnsavedChangesDialog.tsx` for hardcoded colors — verify it uses ConfirmationDialog or equivalent from `solune/frontend/src/components/ui/` with token-based styling

### Dark Mode Verification

- [ ] T056 [US3] Verify light/dark mode rendering for all pipeline components — confirm all elements (stage board, agent nodes, flow graph, analytics, dialogs) correctly reflect the selected theme with no visual artifacts, unreadable text, or missing styles; fix any components that break in dark mode

### Text and Copy Audit (FR-018, FR-019)

- [ ] T057 [US3] Audit all user-visible text on the Pipeline page for placeholder content — search all files in `solune/frontend/src/pages/AgentsPipelinePage.tsx` and `solune/frontend/src/components/pipeline/` for "TODO", "Lorem ipsum", "Test", "placeholder", or any non-final copy; replace with meaningful text
- [ ] T058 [P] [US3] Audit terminology consistency across all pipeline components — verify "pipeline" not "workflow" in user-facing text, "stage" not "step", and other terms match the rest of the application; fix inconsistencies
- [ ] T059 [P] [US3] Audit action button labels in `solune/frontend/src/components/pipeline/PipelineToolbar.tsx` — verify all buttons use verb phrases ("Save Pipeline", "Delete Pipeline", "Discard Changes") not generic nouns; fix non-compliant labels (FR-019)
- [ ] T060 [P] [US3] Audit action button labels in `solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx` — verify duplicate/delete/assign buttons use verb phrases; fix non-compliant labels

### Truncation and Tooltips (FR-018)

- [ ] T061 [US3] Audit long text truncation in `solune/frontend/src/components/pipeline/AgentNode.tsx` — verify long agent names and model names are truncated with `text-ellipsis` and full text available via `<Tooltip>` from `solune/frontend/src/components/ui/tooltip.tsx`; add if missing
- [ ] T062 [P] [US3] Audit long text truncation in `solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx` — verify long pipeline names and descriptions are truncated with tooltip; add if missing
- [ ] T063 [P] [US3] Audit long text truncation in `solune/frontend/src/components/pipeline/StageCard.tsx` — verify long stage names are truncated with tooltip; add if missing

### Destructive Action Confirmations (FR-007)

- [ ] T064 [US3] Audit destructive actions across all pipeline components — verify delete pipeline, remove stage, remove agent, and discard changes all trigger `<ConfirmationDialog>` from `solune/frontend/src/components/ui/confirmation-dialog.tsx` before executing; add missing confirmation dialogs

### Timestamp Formatting

- [ ] T065 [P] [US3] Audit timestamp display in `solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx` — verify recent timestamps show relative time ("2 hours ago") using `formatTimeAgo` from `solune/frontend/src/utils/formatTime.ts` and older timestamps show absolute dates; fix if inconsistent

### Spacing and Layout Tokens

- [ ] T066 [US3] Audit spacing across all pipeline components — verify Tailwind spacing scale is used consistently (`gap-4`, `p-6`, etc.) with no arbitrary values like `p-[13px]`; fix any non-standard spacing values

**Checkpoint**: Pipeline page is visually consistent with the Celestial design system; all text is final, meaningful copy; all destructive actions require confirmation; all mutations provide success feedback; dark mode works correctly.

---

## Phase 6: User Story 4 — Reliable Pipeline Editing and Navigation Guards (Priority: P2)

**Goal**: Ensure the editor protects unsaved work and provides reliable editing controls so users never accidentally lose changes (FR-009 through FR-012)

**Independent Test**: Create and edit a pipeline, make unsaved changes, then attempt to navigate away, close the browser tab, create a new pipeline, or load a different saved pipeline — verify the unsaved-changes guard activates correctly in each case.

### Unsaved Changes Guard (FR-009)

- [ ] T067 [US4] Audit navigation guard in `solune/frontend/src/hooks/usePipelineConfig.ts` — verify `useBlocker` from react-router-dom triggers the unsaved-changes dialog when user has dirty state and navigates away; fix if missing or broken
- [ ] T068 [P] [US4] Audit browser tab close guard in `solune/frontend/src/hooks/usePipelineConfig.ts` — verify `beforeunload` event listener is registered when `isDirty` is true and removed when false; fix if missing
- [ ] T069 [US4] Audit pipeline load guard — verify that when a user has unsaved changes and clicks to load a different saved pipeline in `solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx`, the unsaved-changes dialog appears before new data is loaded; fix if missing
- [ ] T070 [US4] Audit new pipeline guard — verify that when a user has unsaved changes and clicks "Create New Pipeline", the unsaved-changes dialog appears before the board is reset; fix if missing

### Dialog Behavior (FR-010)

- [ ] T071 [US4] Audit UnsavedChangesDialog options in `solune/frontend/src/components/pipeline/UnsavedChangesDialog.tsx` — verify three clear options are offered: "Save Changes", "Discard Changes", and "Cancel"; verify button labels are verb phrases
- [ ] T072 [US4] Audit discard behavior — verify choosing "Discard" in the unsaved-changes dialog reverts pipeline state to the last saved snapshot with no residual dirty state or stale data in `solune/frontend/src/hooks/usePipelineReducer.ts`
- [ ] T073 [US4] Audit save-and-continue behavior — verify choosing "Save" in the unsaved-changes dialog saves the pipeline and, on success, continues the pending action (navigation, load, or create) automatically
- [ ] T074 [US4] Audit save failure in dialog — verify that if save fails during "Save and Continue", the dialog remains open with a user-friendly error message and buttons re-enabled

### Name Validation (FR-011, FR-012)

- [ ] T075 [US4] Audit pipeline name validation in `solune/frontend/src/hooks/usePipelineValidation.ts` — verify saving with an empty name is prevented with a clear inline error message associated with the input field; extend validation if missing
- [ ] T076 [US4] Audit pipeline name conflict handling in `solune/frontend/src/hooks/usePipelineConfig.ts` — verify HTTP 409 responses display "Could not save pipeline. The name '[name]' is already in use. Please try a different name." rather than a raw error; fix if missing
- [ ] T077 [P] [US4] Audit copy pipeline name generation — verify that when duplicating a pipeline whose name already has a "(Copy)" suffix, a non-conflicting name is generated (e.g., appending a number) in the relevant mutation handler

**Checkpoint**: All unsaved-changes guards work correctly across navigation, tab close, pipeline load, and new pipeline creation. Discard reverts cleanly. Save-and-continue flows work. Name validation and conflict handling are user-friendly.

---

## Phase 7: User Story 5 — Responsive Layout Across Screen Sizes (Priority: P2)

**Goal**: Ensure the Pipeline page adapts gracefully to viewport widths from 768px to 1920px so all sections remain usable on different screen sizes (FR-020)

**Independent Test**: Resize the browser window across supported breakpoints (768px, 1024px, 1280px, 1920px) and verify pipeline editor, stage board, saved workflows list, and analytics dashboard adapt without horizontal scrolling, overlapping elements, or truncated controls.

### Desktop Layout (1920px)

- [ ] T078 [US5] Audit desktop layout at 1920px in `solune/frontend/src/pages/AgentsPipelinePage.tsx` — verify the layout uses available space effectively with appropriate spacing between toolbar, stage board, saved workflows, and analytics sections; fix any wasted space or overflow issues

### Laptop Layout (1280px)

- [ ] T079 [US5] Audit laptop layout at 1280px — verify all sections are visible and functional, stage board adapts column count via Tailwind responsive classes (`lg:`, `xl:`), and no horizontal scrolling is required in `solune/frontend/src/components/pipeline/PipelineBoard.tsx`

### Tablet Layout (768px)

- [ ] T080 [US5] Audit minimum-width layout at 768px — verify sections stack appropriately using Tailwind `md:` breakpoint, stage board remains usable with scrolling if needed, and all controls remain accessible in `solune/frontend/src/pages/AgentsPipelinePage.tsx`

### Component-Level Responsiveness

- [ ] T081 [P] [US5] Audit pipeline board grid responsiveness in `solune/frontend/src/components/pipeline/PipelineBoard.tsx` — verify grid/flex layout adapts column count across breakpoints using Tailwind responsive utilities; fix any fixed-width values
- [ ] T082 [P] [US5] Audit saved workflows list responsiveness in `solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx` — verify list adapts layout at narrower viewports (may collapse to dropdown or slide-out panel); fix if broken
- [ ] T083 [P] [US5] Audit pipeline flow graph responsiveness in `solune/frontend/src/components/pipeline/PipelineFlowGraph.tsx` — verify visualization scales with container width and does not overflow at 768px
- [ ] T084 [P] [US5] Audit analytics dashboard responsiveness in `solune/frontend/src/components/pipeline/PipelineAnalytics.tsx` — verify charts and metrics adapt layout at narrower viewports without overlap

### Smooth Transitions

- [ ] T085 [US5] Verify layout transitions across breakpoints — resize browser smoothly from 768px to 1920px and confirm no broken intermediate states, overlapping elements, or visual jumps

**Checkpoint**: Pipeline page is fully functional and visually coherent at all viewport widths from 768px to 1920px.

---

## Phase 8: User Story 6 — Maintainable and Well-Tested Pipeline Code (Priority: P3)

**Goal**: Ensure Pipeline page code follows best practices for component structure, state management, type safety, and test coverage so the page is easy to maintain and extend (FR-021 through FR-025)

**Independent Test**: Review component structure; run `npx tsc --noEmit` with zero errors; run `npx eslint` with zero warnings; run `npx vitest run` with all tests passing; verify page file is ≤250 lines.

### Page Decomposition (FR-021)

- [ ] T086 [US6] Decompose `solune/frontend/src/pages/AgentsPipelinePage.tsx` from ~417 lines to ≤250 lines — extract self-contained sections into sub-components in `solune/frontend/src/components/pipeline/` (e.g., PipelinePageContent, PipelineEditorSection, PipelinePageHeader) following single-responsibility principle
- [ ] T087 [US6] Verify extracted sub-components are properly exported from `solune/frontend/src/components/pipeline/index.ts` barrel file

### Prop Drilling Audit (FR-022)

- [ ] T088 [US6] Audit prop passing depth across the Pipeline component tree — verify no props are drilled through more than 2 levels; if found, refactor using composition, context, or hook extraction

### Hook Extraction

- [ ] T089 [P] [US6] Audit `solune/frontend/src/hooks/usePipelineBoardMutations.ts` (~418 lines) for decomposition opportunities — if individual mutation functions exceed 15 lines of inline state logic, consider extracting into smaller focused hooks
- [ ] T090 [P] [US6] Verify all custom pipeline hooks have explicit or unambiguously inferrable return types — check `solune/frontend/src/hooks/usePipelineConfig.ts`, `solune/frontend/src/hooks/usePipelineBoardMutations.ts`, `solune/frontend/src/hooks/usePipelineReducer.ts`, `solune/frontend/src/hooks/usePipelineModelOverride.ts`, `solune/frontend/src/hooks/usePipelineValidation.ts`

### Type Safety (FR-024)

- [ ] T091 [US6] Audit all pipeline files for `any` types — search `solune/frontend/src/pages/AgentsPipelinePage.tsx`, `solune/frontend/src/components/pipeline/`, `solune/frontend/src/hooks/usePipeline*.ts` for `: any`, `as any`, `<any>` and replace with proper types
- [ ] T092 [P] [US6] Audit all pipeline files for unsafe type assertions — search for `as ` type assertions and replace with type guards or discriminated unions where possible
- [ ] T093 [P] [US6] Verify pipeline API response types in `solune/frontend/src/types/index.ts` match backend Pydantic models — date fields are `string` (ISO), nullable fields use `| null`

### React Query Compliance (FR-023)

- [ ] T094 [US6] Audit all pipeline data fetching for raw `useEffect` + `fetch` patterns — replace any found with `useQuery` / `useMutation` from TanStack Query in relevant hooks; verify query key conventions follow `pipelineKeys` factory pattern

### Performance Optimization

- [ ] T095 [P] [US6] Audit list rendering keys in `solune/frontend/src/components/pipeline/PipelineBoard.tsx`, `solune/frontend/src/components/pipeline/StageCard.tsx`, `solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx` — verify all array renders use `key={item.id}` never `key={index}`; fix if found
- [ ] T096 [P] [US6] Audit memoization in `solune/frontend/src/components/pipeline/StageCard.tsx` and `solune/frontend/src/components/pipeline/AgentNode.tsx` — verify expensive components are wrapped in `React.memo()` where props are stable; add targeted memoization if missing
- [ ] T097 [P] [US6] Audit derived state computations — verify heavy transforms (sorting, filtering, grouping) in `solune/frontend/src/hooks/usePipelineModelOverride.ts` and `solune/frontend/src/components/pipeline/PipelineAnalytics.tsx` are wrapped in `useMemo`; add if missing
- [ ] T098 [P] [US6] Audit saved workflows list for large-list handling — if the list can render 50+ items, consider adding pagination or virtualization in `solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx`

### Code Hygiene

- [ ] T099 [US6] Remove dead code across all pipeline files — remove unused imports, commented-out blocks, unreachable branches, and `console.log` statements from `solune/frontend/src/pages/AgentsPipelinePage.tsx`, `solune/frontend/src/components/pipeline/`, and `solune/frontend/src/hooks/usePipeline*.ts`
- [ ] T100 [P] [US6] Audit import paths — verify all project imports in pipeline files use `@/` alias (`@/components/...`, `@/hooks/...`, `@/services/...`) not relative `../../` paths; fix non-compliant imports
- [ ] T101 [P] [US6] Audit magic strings — verify repeated strings (status values, route paths, query keys, board states) are defined as constants, not inline strings; extract to constants if found
- [ ] T102 [P] [US6] Verify file naming conventions — components are PascalCase `.tsx`, hooks are `use*.ts`, types in `types/`, utilities in `lib/` or `utils/`

### Existing Test Verification (FR-025)

- [ ] T103 [US6] Run all existing pipeline tests via `cd solune/frontend && npx vitest run src/components/pipeline/ src/hooks/usePipeline*` — verify all pass; fix any broken tests
- [ ] T104 [P] [US6] Verify test coverage inventory — confirm test files exist for: `solune/frontend/src/components/pipeline/PipelineBoard.test.tsx`, `solune/frontend/src/components/pipeline/PipelineFlowGraph.test.tsx`, `solune/frontend/src/components/pipeline/StageCard.test.tsx`, `solune/frontend/src/components/pipeline/AgentNode.test.tsx`, `solune/frontend/src/components/pipeline/SavedWorkflowsList.test.tsx`; note any missing component test files

**Checkpoint**: Pipeline page code is well-structured (page ≤250 lines), type-safe, lint-clean, and all existing tests pass.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, cross-cutting improvements, and verification that all user stories work together

- [ ] T105 Run full lint check: `cd solune/frontend && npx eslint src/pages/AgentsPipelinePage.tsx src/components/pipeline/ src/hooks/usePipeline*` — resolve any remaining warnings to achieve 0 warnings (SC-009)
- [ ] T106 [P] Run full type check: `cd solune/frontend && npx tsc --noEmit` — resolve any remaining type errors to achieve 0 errors in pipeline-related files (SC-010)
- [ ] T107 [P] Run full test suite: `cd solune/frontend && npx vitest run` — verify all tests pass including pipeline-specific tests (SC-011)
- [ ] T108 Run quickstart.md validation — walk through `specs/043-pipeline-page-audit/quickstart.md` audit checklist to verify all items pass
- [ ] T109 [P] Verify no duplicate API calls — confirm the same data is not fetched in both the page and a child component independently by reviewing React Query devtools or code inspection
- [ ] T110 Final manual review — verify Pipeline page in browser: light mode, dark mode, viewport 768px → 1280px → 1920px, keyboard-only navigation through all interactive elements

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational phase — can start after Phase 2
- **US2 (Phase 4)**: Depends on Foundational phase — can start after Phase 2, parallel with US1
- **US3 (Phase 5)**: Depends on Foundational phase — can start after Phase 2, parallel with US1/US2
- **US4 (Phase 6)**: Depends on Foundational phase — can start after Phase 2, parallel with US1/US2/US3
- **US5 (Phase 7)**: Depends on Foundational phase — can start after Phase 2, parallel with other stories
- **US6 (Phase 8)**: Depends on US1, US2, US3, US4, US5 — should be done last since page decomposition (T086) must happen after all component-level changes are complete
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 — No dependencies on other stories
- **User Story 2 (P1)**: Can start after Phase 2 — No dependencies on other stories; can run in parallel with US1
- **User Story 3 (P2)**: Can start after Phase 2 — No dependencies on other stories; design token changes are independent
- **User Story 4 (P2)**: Can start after Phase 2 — No dependencies on other stories; guard logic is self-contained
- **User Story 5 (P2)**: Can start after Phase 2 — No dependencies on other stories; responsive changes are CSS/layout focused
- **User Story 6 (P3)**: Should start after US1–US5 — page decomposition should incorporate all changes from prior stories

### Within Each User Story

- Discovery findings (Phase 2) guide which tasks apply vs. N/A
- Component-level fixes can be parallelized (different files)
- Page-level fixes (T013, T014, T019, T044) should be sequential to avoid merge conflicts
- Cross-component audits (T041, T042, T064) should follow individual component fixes

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T002, T003, T004)
- All Foundational tasks marked [P] can run in parallel (T007, T008, T009, T010, T011)
- US1: Section-level error state tasks are parallelizable (T020, T021, T022); rate limit tasks (T017, T018); edge case tasks (T026, T027)
- US2: Component-level keyboard/ARIA audits are highly parallelizable (T029–T032, T035, T037–T038, T040, T043)
- US3: Design token audits per component are all parallelizable (T045–T055); text/copy audits (T058–T060); truncation tasks (T062, T063)
- US4: Browser guard (T068) and copy name (T077) are parallelizable
- US5: Component-level responsive audits are all parallelizable (T081–T084)
- US6: Type safety, performance, and code hygiene tasks are mostly parallelizable (T092–T102, T104)
- Polish: Lint, type-check, and test suite can run in parallel (T106, T107)

---

## Parallel Example: User Story 1

```bash
# Launch all section-level error state audits together (different files):
Task: T020 — "Audit error state in SavedWorkflowsList.tsx"
Task: T021 — "Audit error state in PipelineAnalytics.tsx"
Task: T022 — "Audit empty state in PipelineAnalytics.tsx"

# Launch rate limit audits together (different hooks):
Task: T017 — "Audit rate limit in usePipelineConfig.ts"
Task: T018 — "Audit rate limit in usePipelineBoardMutations.ts"

# Launch edge case audits together (different files):
Task: T026 — "Audit empty save validation in usePipelineValidation.ts"
Task: T027 — "Audit missing agent indicator in AgentNode.tsx"
```

## Parallel Example: User Story 2

```bash
# Launch component-level keyboard audits together (different files):
Task: T029 — "Audit keyboard in StageCard.tsx"
Task: T030 — "Audit keyboard in ExecutionGroupCard.tsx"
Task: T031 — "Audit keyboard in ModelSelector.tsx"
Task: T032 — "Audit keyboard in StageCard.tsx (agent picker)"

# Launch ARIA attribute audits together (different files):
Task: T037 — "Audit ARIA in ModelSelector.tsx"
Task: T038 — "Audit ARIA in SavedWorkflowsList.tsx"
Task: T040 — "Audit form labels in StageCard.tsx"
```

## Parallel Example: User Story 3

```bash
# Launch design token audits together (all different component files):
Task: T045 — "Audit tokens in PipelineBoard.tsx"
Task: T046 — "Audit tokens in StageCard.tsx"
Task: T047 — "Audit tokens in ExecutionGroupCard.tsx"
Task: T048 — "Audit tokens in AgentNode.tsx"
Task: T049 — "Audit tokens in SavedWorkflowsList.tsx"
Task: T050 — "Audit tokens in PipelineAnalytics.tsx"
Task: T051 — "Audit tokens in PipelineFlowGraph.tsx"
Task: T052 — "Audit tokens in ModelSelector.tsx"
Task: T053 — "Audit tokens in PipelineToolbar.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 + User Story 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational Discovery & Assessment
3. Complete Phase 3: User Story 1 — Bug-Free Page States (P1)
4. Complete Phase 4: User Story 2 — Accessible Pipeline Page (P1)
5. **STOP and VALIDATE**: Test US1 + US2 independently — all page states render correctly, keyboard navigation works, ARIA attributes correct
6. Deploy/demo if ready — this is a production-quality MVP

### Incremental Delivery

1. Complete Setup + Foundational → Discovery complete, findings documented
2. Add User Story 1 → Test independently → All page states render correctly (MVP foundation!)
3. Add User Story 2 → Test independently → Full keyboard + screen reader accessibility
4. Add User Story 3 → Test independently → Visual consistency and polished UX
5. Add User Story 4 → Test independently → Unsaved changes guards work in all scenarios
6. Add User Story 5 → Test independently → Responsive across 768px–1920px
7. Add User Story 6 → Test independently → Code quality, page decomposition, lint/type clean
8. Polish phase → Final validation → All user stories verified together

### Parallel Team Strategy

With multiple developers after Phase 2 (Foundational) is complete:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (P1 — page states)
   - Developer B: User Story 2 (P1 — accessibility)
   - Developer C: User Story 3 (P2 — UX polish) + User Story 4 (P2 — editing guards)
   - Developer D: User Story 5 (P2 — responsive layout)
3. After all P1/P2 stories complete:
   - Developer A: User Story 6 (P3 — code quality + decomposition)
   - Developer B: Polish phase (final validation)

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All paths use `solune/frontend/src/` prefix per repository convention
- This is a frontend-only audit — no backend changes required
- Existing tests are maintained, not replaced; new tests only if US6 assessment reveals critical gaps
- Legacy backward compatibility (syncLegacyAgents, stage.agents[]) must be preserved
