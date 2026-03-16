# Tasks: Pipeline Page Audit — Modern Best Practices, Modular Design, and Zero Bugs

**Input**: Design documents from `/specs/043-pipeline-page-audit/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/component-contracts.yaml, quickstart.md

**Tests**: Existing test files (5 component tests: PipelineBoard, PipelineFlowGraph, StageCard, AgentNode, SavedWorkflowsList; 2 hook tests: usePipelineConfig, usePipelineReducer) will be verified to pass. New test creation is addressed in US6 (P3) per FR-025 for components currently lacking test coverage (PipelineToolbar, UnsavedChangesDialog, ExecutionGroupCard, ModelSelector).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. The 6 user stories map to the 10 audit categories from the parent issue checklist.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Frontend**: `solune/frontend/src/`
- **Page**: `solune/frontend/src/pages/AgentsPipelinePage.tsx`
- **Components**: `solune/frontend/src/components/pipeline/`
- **Hooks**: `solune/frontend/src/hooks/`
- **Types**: `solune/frontend/src/types/index.ts`
- **API**: `solune/frontend/src/services/api.ts`
- **Utils**: `solune/frontend/src/utils/`
- **UI**: `solune/frontend/src/components/ui/`
- **Common**: `solune/frontend/src/components/common/`

---

## Phase 1: Setup

**Purpose**: Establish baseline state and verify development environment before making any changes

- [ ] T001 Install frontend dependencies via `cd solune/frontend && npm install`
- [ ] T002 Run baseline tests via `cd solune/frontend && npx vitest run` and record current pass/fail state
- [ ] T003 [P] Run baseline lint via `cd solune/frontend && npm run lint` and record current warnings/errors
- [ ] T004 [P] Run baseline type-check via `cd solune/frontend && npm run type-check` and record current errors
- [ ] T005 [P] Run pipeline-specific tests via `cd solune/frontend && npx vitest run src/components/pipeline/ src/hooks/usePipeline*` and record coverage

---

## Phase 2: Foundational (Discovery & Assessment)

**Purpose**: Read and assess all Pipeline page files to produce a findings table scoring each audit checklist item as Pass/Fail/N/A. This assessment MUST be complete before any implementation work begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Read and assess `solune/frontend/src/pages/AgentsPipelinePage.tsx` (~417 lines) — note line count violation (>250), sub-components rendered, hooks used (usePipelineConfig, usePipelineBoardMutations, usePipelineReducer, usePipelineModelOverride, usePipelineValidation, useSelectedPipeline, useConfirmation), page states handled (no-project, loading, empty, creating, editing, saving, error), and any inline business logic
- [ ] T007 [P] Read and assess large pipeline components: `solune/frontend/src/components/pipeline/StageCard.tsx` (~362 lines, >250 violation), `PipelineBoard.tsx` (~299 lines, borderline), `PipelineAnalytics.tsx` (~295 lines, borderline), `ModelSelector.tsx` (~290 lines, borderline) — note extractable sections, prop drilling depth, inline logic
- [ ] T008 [P] Read and assess remaining pipeline components: `solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx` (~237 lines), `PipelineFlowGraph.tsx` (~235 lines), `ExecutionGroupCard.tsx` (~223 lines), `AgentNode.tsx` (~187 lines), `PipelineToolbar.tsx` (~172 lines), `PipelineModelDropdown.tsx` (~117 lines), `UnsavedChangesDialog.tsx` (~69 lines), `PresetBadge.tsx` (~55 lines), `ParallelStageGroup.tsx` (~30 lines)
- [ ] T009 [P] Read and assess pipeline hooks: `solune/frontend/src/hooks/usePipelineBoardMutations.ts` (~418 lines — largest hook), `usePipelineConfig.ts` (~232 lines), `usePipelineReducer.ts` (~115 lines), `usePipelineModelOverride.ts` (~98 lines), `usePipelineValidation.ts` (~38 lines), `useSelectedPipeline.ts`, `useConfirmation.ts` — note query key conventions, staleTime, mutation error handlers, duplicate API call risks
- [ ] T010 [P] Read and assess Pipeline types in `solune/frontend/src/types/index.ts` — review PipelineConfig, PipelineStage, ExecutionGroup, PipelineAgentNode, PipelineConfigCreate, PipelineConfigUpdate, PipelineConfigListResponse, PipelineConfigSummary, PipelineIssueLaunchRequest, ProjectPipelineAssignment, PipelineBoardState, PipelineModelOverride, PipelineValidationErrors, PresetPipelineDefinition, PresetSeedResult — note any `any` types, type assertions, missing nullable fields, alignment with data-model.md
- [ ] T011 [P] Read and assess pipelinesApi in `solune/frontend/src/services/api.ts` — review 9 endpoints (list, get, create, update, delete, seedPresets, getAssignment, setAssignment, launch), request/response types, error handling patterns
- [ ] T012 [P] Read and assess existing test files: `solune/frontend/src/components/pipeline/PipelineBoard.test.tsx`, `PipelineFlowGraph.test.tsx`, `StageCard.test.tsx`, `AgentNode.test.tsx`, `SavedWorkflowsList.test.tsx` (component tests) and hook tests for `usePipelineConfig`, `usePipelineReducer` — note coverage gaps per spec edge cases
- [ ] T013 Produce a findings table scoring each of the 10 audit checklist categories (Component Architecture, Data Fetching, Loading/Error/Empty States, Type Safety, Accessibility, Text/Copy/UX, Styling/Layout, Performance, Test Coverage, Code Hygiene) as Pass/Fail/N/A with specific file references for all failures

**Checkpoint**: Assessment complete — all audit findings documented. User story implementation can now begin in priority order.

---

## Phase 3: User Story 1 — Bug-Free and Complete Page States (Priority: P1) 🎯 MVP

**Goal**: Ensure the Pipeline page displays correctly in every state — loading, empty, populated, saving, and error — so users always understand what is happening and never encounter a broken or confusing view.

**Independent Test**: Trigger each page state (loading, no project selected, empty pipeline board, populated board, save in progress, save error, rate limit error, deleted pipeline, section-level error) and verify each renders correctly with appropriate messaging, recovery actions, and no console errors.

### Implementation for User Story 1

- [ ] T014 [US1] Audit and fix loading state in `solune/frontend/src/pages/AgentsPipelinePage.tsx` — verify `<CelestialLoader size="md" />` from `solune/frontend/src/components/common/CelestialLoader.tsx` renders centered in content area during pipeline data fetch, not a blank screen (FR-001)
- [ ] T015 [US1] Audit and fix no-project-selected state in `solune/frontend/src/pages/AgentsPipelinePage.tsx` — verify `<ProjectSelectionEmptyState>` from `solune/frontend/src/components/common/ProjectSelectionEmptyState.tsx` renders with clear guidance on how to select a project (FR-002)
- [ ] T016 [US1] Audit and fix empty pipeline board state in `solune/frontend/src/components/pipeline/PipelineBoard.tsx` — verify meaningful empty state with illustrative icon and "Create Pipeline" call-to-action when board has no stages (FR-003)
- [ ] T017 [US1] Audit and fix save error state in `solune/frontend/src/pages/AgentsPipelinePage.tsx` and `solune/frontend/src/hooks/usePipelineConfig.ts` — verify user-friendly error message following "Could not [action]. [Reason, if known]. [Suggested next step]." format, no raw error codes or stack traces (FR-004)
- [ ] T018 [US1] Audit and fix rate-limit error detection in `solune/frontend/src/hooks/usePipelineConfig.ts` and `solune/frontend/src/hooks/usePipelineBoardMutations.ts` — verify `isRateLimitApiError()` from `solune/frontend/src/utils/rateLimit.ts` is used in all mutation `onError` handlers with specific rate-limit message advising user to wait (FR-005)
- [ ] T019 [US1] Audit and fix deleted pipeline handling in `solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx` and `solune/frontend/src/hooks/usePipelineConfig.ts` — verify selecting a deleted pipeline shows a meaningful fallback message without crashing
- [ ] T020 [US1] Audit and fix section-level error isolation in `solune/frontend/src/pages/AgentsPipelinePage.tsx` — verify pipeline list, pipeline assignment, and analytics dashboard each display their own loading/error states independently so one failed section does not block others (FR-006)
- [ ] T021 [US1] Verify `<ErrorBoundary>` wraps the Pipeline page at route level in `solune/frontend/src/App.tsx` or within `solune/frontend/src/pages/AgentsPipelinePage.tsx`
- [ ] T022 [US1] Verify zero console errors across all page states — check for unhandled promise rejections, missing-key warnings, and deprecation warnings in loading, empty, populated, error, and rate-limit states

**Checkpoint**: All page states (loading, no-project, empty board, populated, saving, save error, rate-limit error, deleted pipeline, section error) render correctly with appropriate messaging and recovery actions.

---

## Phase 4: User Story 2 — Accessible Pipeline Page (Priority: P1)

**Goal**: Ensure the Pipeline page is fully accessible via keyboard navigation, screen readers, and assistive technology — all interactive elements reachable, dialogs trap focus, custom controls have proper ARIA attributes, and status is conveyed through icon + text.

**Independent Test**: Navigate the entire Pipeline page using only keyboard (Tab, Enter, Space, Escape), run an automated accessibility scanner, and verify screen reader announcements for all interactive elements including toolbar, stage cards, agent nodes, execution group controls, saved workflow cards, model selector, and dialogs.

### Implementation for User Story 2

- [ ] T023 [US2] Audit and fix keyboard navigation for toolbar buttons in `solune/frontend/src/components/pipeline/PipelineToolbar.tsx` — verify Save, Discard, Delete, Copy buttons reachable via Tab and activated via Enter/Space with visible focus indicators (FR-013)
- [ ] T024 [P] [US2] Audit and fix keyboard navigation for stage card controls in `solune/frontend/src/components/pipeline/StageCard.tsx` — verify stage name inline editing, add agent button, remove stage button, and agent removal all keyboard-accessible (FR-013)
- [ ] T025 [P] [US2] Audit and fix saved workflow cards in `solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx` — ensure each card is a proper interactive element (`<button>` or `<a>`, not a styled `<div>` with `onClick`) that responds to keyboard activation (Enter/Space) and is announced correctly to screen readers (FR-026)
- [ ] T026 [P] [US2] Audit and fix keyboard navigation for model selector in `solune/frontend/src/components/pipeline/ModelSelector.tsx` — verify `aria-haspopup="listbox"`, `aria-expanded`, arrow key navigation, Enter to select, Escape to close (contract: ModelSelector accessibility)
- [ ] T027 [US2] Audit and fix focus management in `solune/frontend/src/components/pipeline/UnsavedChangesDialog.tsx` — verify focus trapped within dialog when open, Escape closes dialog, focus returns to triggering element on close (FR-014)
- [ ] T028 [P] [US2] Audit and fix ARIA attributes on execution mode toggle in `solune/frontend/src/components/pipeline/ExecutionGroupCard.tsx` — verify `role="switch"` or equivalent with `aria-checked` state, label reads "Sequential" or "Parallel" with current state announced (contract: ExecutionGroupCard accessibility)
- [ ] T029 [P] [US2] Audit and fix ARIA attributes on agent nodes in `solune/frontend/src/components/pipeline/AgentNode.tsx` — verify remove button has descriptive `aria-label` (e.g., "Remove agent [name]"), decorative Lucide icons have `aria-hidden="true"` (contract: AgentNode accessibility)
- [ ] T030 [US2] Audit and fix form input labels across pipeline components — verify pipeline name input in `solune/frontend/src/pages/AgentsPipelinePage.tsx` and stage name inputs in `solune/frontend/src/components/pipeline/StageCard.tsx` have visible labels or `aria-label` associated via `htmlFor` (FR-016)
- [ ] T031 [P] [US2] Audit and fix status indicators to use icon + text, not color alone — verify stage execution mode indicator, pipeline save state, and assignment status in `solune/frontend/src/components/pipeline/ExecutionGroupCard.tsx`, `PipelineToolbar.tsx`, and `SavedWorkflowsList.tsx` convey meaning through both icon/text and color (FR-015)
- [ ] T032 [P] [US2] Audit and fix focus-visible styles on all interactive elements across `solune/frontend/src/components/pipeline/*.tsx` — verify `celestial-focus` class or Tailwind `focus-visible:` ring is applied to all buttons, links, inputs, toggles, and custom controls
- [ ] T033 [P] [US2] Audit and fix validation error association — verify pipeline name validation errors in `solune/frontend/src/pages/AgentsPipelinePage.tsx` and stage name validation errors in `solune/frontend/src/components/pipeline/StageCard.tsx` are programmatically associated with input fields via `aria-describedby` (FR-016)
- [ ] T034 [P] [US2] Audit and fix screen reader text across all pipeline components — verify decorative icons (Lucide) have `aria-hidden="true"` and meaningful icons have `aria-label` in `solune/frontend/src/components/pipeline/*.tsx`

**Checkpoint**: All interactive elements keyboard-accessible with visible focus, dialogs trap focus, custom controls have ARIA attributes, status conveyed via icon + text, form inputs labeled, validation errors associated with inputs.

---

## Phase 5: User Story 3 — Consistent and Polished User Experience (Priority: P2)

**Goal**: Ensure the Pipeline page looks and feels consistent with the rest of the application — design token compliance, professional copy, proper confirmation on destructive actions, success feedback on mutations, dark mode support, and polished text handling.

**Independent Test**: Visually compare the Pipeline page with other pages (Agents, Projects, Settings), verify all text is final and consistent, check destructive actions require confirmation, validate mutations provide success feedback, and toggle dark mode.

### Implementation for User Story 3

- [ ] T035 [US3] Audit and fix design token compliance across all pipeline components in `solune/frontend/src/components/pipeline/*.tsx` and `solune/frontend/src/pages/AgentsPipelinePage.tsx` — verify no hardcoded colors (`#fff`, `bg-white`, `text-black`, `text-gray-*`), all use Tailwind theme classes (`bg-card`, `text-card-foreground`, `border-border`, `bg-muted`) and CSS variables from `solune/frontend/src/index.css` (FR-017)
- [ ] T036 [P] [US3] Audit and fix all user-visible text across pipeline components — verify no placeholder text ("TODO", "Lorem ipsum", "Test"), all strings are final meaningful copy
- [ ] T037 [P] [US3] Audit and fix terminology consistency across all pipeline components — verify "pipeline" not "workflow" in user-facing text, "stage" not "step", consistent with rest of application terminology
- [ ] T038 [US3] Audit and fix destructive action confirmation — verify delete pipeline in `solune/frontend/src/components/pipeline/PipelineToolbar.tsx`, remove stage in `StageCard.tsx`, remove agent in `AgentNode.tsx`, and discard changes all use `<ConfirmationDialog>` from `solune/frontend/src/components/ui/confirmation-dialog.tsx` — no destructive action happens immediately on click (FR-007)
- [ ] T039 [US3] Audit and fix mutation success feedback — verify all successful mutations (save, create, duplicate, delete) in `solune/frontend/src/hooks/usePipelineConfig.ts` and `solune/frontend/src/hooks/usePipelineBoardMutations.ts` provide visible success feedback (toast notification, inline message, or status change) (FR-008)
- [ ] T040 [P] [US3] Audit and fix dark mode compliance across all pipeline components — verify all elements in `solune/frontend/src/components/pipeline/*.tsx` render correctly in dark mode with no visual artifacts, unreadable text, or missing styles; all use Tailwind `dark:` variants or CSS variable overrides
- [ ] T041 [P] [US3] Audit and fix long text truncation — verify pipeline names, agent names, model names, and descriptions in `solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx`, `AgentNode.tsx`, `StageCard.tsx`, and `PipelineToolbar.tsx` are truncated with `text-ellipsis` and full text available via `<Tooltip>` from `solune/frontend/src/components/ui/tooltip.tsx` (FR-018)
- [ ] T042 [P] [US3] Audit and fix action button labels — verify all buttons use verb phrases ("Save Pipeline", "Delete Pipeline", "Add Stage", "Remove Agent", "Discard Changes") not generic nouns in `solune/frontend/src/components/pipeline/PipelineToolbar.tsx`, `StageCard.tsx`, `AgentNode.tsx`, `SavedWorkflowsList.tsx` (FR-019)
- [ ] T043 [P] [US3] Audit and fix timestamp formatting — verify `updated_at` in `solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx` uses relative time ("2 hours ago") for recent timestamps and absolute format for older timestamps via `solune/frontend/src/utils/formatTime.ts`
- [ ] T044 [US3] Audit and fix error message format — verify all `onError` handlers in `solune/frontend/src/hooks/usePipelineConfig.ts` and `solune/frontend/src/hooks/usePipelineBoardMutations.ts` produce messages following "Could not [action]. [Reason, if known]. [Suggested next step]." format with no raw error codes or stack traces (FR-004)
- [ ] T045 [US3] Audit and fix pipeline name conflict error — verify HTTP 409 conflict response produces user-friendly message "Could not save pipeline. The name '[name]' is already in use. Please try a different name." in `solune/frontend/src/hooks/usePipelineConfig.ts` (FR-012)

**Checkpoint**: All visual elements use design tokens, text is final and consistent, destructive actions confirmed, mutations provide feedback, dark mode correct, long text truncated with tooltips, error messages user-friendly.

---

## Phase 6: User Story 4 — Reliable Pipeline Editing and Navigation Guards (Priority: P2)

**Goal**: Ensure the pipeline editor protects unsaved work with reliable navigation guards, dirty state tracking, and a clear save/discard/cancel dialog — users never accidentally lose their changes.

**Independent Test**: Create and edit a pipeline, make unsaved changes, then attempt to navigate away, close the browser tab, create a new pipeline, and load a different saved pipeline — verify the unsaved-changes guard activates correctly in each case with proper save/discard/cancel flow.

### Implementation for User Story 4

- [ ] T046 [US4] Audit and fix navigation guard activation in `solune/frontend/src/hooks/usePipelineConfig.ts` — verify unsaved-changes guard activates when user has pending edits and attempts to: navigate to a different page (via `useBlocker` from react-router), close the browser tab (via `beforeunload` event), load a different saved pipeline, or create a new pipeline (FR-009)
- [ ] T047 [P] [US4] Audit and fix unsaved-changes dialog options in `solune/frontend/src/components/pipeline/UnsavedChangesDialog.tsx` — verify dialog offers three clear options: "Save Changes", "Discard Changes", and "Cancel" with verb-phrase labels (FR-010, FR-019)
- [ ] T048 [US4] Audit and fix discard behavior in `solune/frontend/src/hooks/usePipelineReducer.ts` — verify choosing "Discard" reverts pipeline state to the last saved snapshot with no residual dirty state or stale data
- [ ] T049 [US4] Audit and fix save-and-continue behavior in `solune/frontend/src/hooks/usePipelineConfig.ts` — verify choosing "Save" in the unsaved-changes dialog saves the pipeline and then continues the pending navigation or action automatically on success
- [ ] T050 [US4] Audit and fix save failure handling in unsaved-changes dialog — verify if save fails during "Save and Continue", the dialog remains open with a user-friendly error message and buttons re-enabled (contract: UnsavedChangesDialog save-error state)
- [ ] T051 [US4] Audit and fix pipeline name validation in `solune/frontend/src/hooks/usePipelineValidation.ts` — verify empty name prevented with clear validation error message associated with the input field via `aria-describedby` (FR-011)
- [ ] T052 [US4] Audit and fix rapid-save prevention in `solune/frontend/src/components/pipeline/PipelineToolbar.tsx` — verify Save button is disabled during save operation (`isSaving=true`) to prevent duplicate API calls (spec edge case: rapid clicks)
- [ ] T053 [US4] Audit and fix browser beforeunload warning in `solune/frontend/src/hooks/usePipelineConfig.ts` — verify native browser "unsaved changes" warning displays when user has dirty state and attempts to close/refresh the tab (FR-009)

**Checkpoint**: Unsaved-changes guard activates on all navigation/load/create triggers, dialog offers save/discard/cancel, discard reverts to snapshot, save-and-continue works, save failures handled gracefully, name validation enforced.

---

## Phase 7: User Story 5 — Responsive Layout Across Screen Sizes (Priority: P2)

**Goal**: Ensure the Pipeline page layout adapts gracefully across desktop (1280px+), tablet/laptop (768px–1279px), and minimum width (768px) without horizontal scrolling, overlapping elements, or broken controls.

**Independent Test**: Resize browser across supported breakpoints (768px, 1024px, 1280px, 1920px), verify pipeline editor, stage board, saved workflows list, and analytics dashboard adapt layout, and verify pipeline flow graph scales with container width.

### Implementation for User Story 5

- [ ] T054 [US5] Audit and fix desktop layout (1920px) in `solune/frontend/src/pages/AgentsPipelinePage.tsx` — verify effective use of available space with appropriate spacing between toolbar, stage board, saved workflows, and analytics sections (FR-020)
- [ ] T055 [P] [US5] Audit and fix laptop layout (1280px) in `solune/frontend/src/pages/AgentsPipelinePage.tsx` — verify all sections visible and functional, stage board adapts column count via Tailwind responsive classes (`md:`, `lg:`, `xl:`), no horizontal scrolling required (FR-020)
- [ ] T056 [P] [US5] Audit and fix minimum width layout (768px) in `solune/frontend/src/pages/AgentsPipelinePage.tsx` — verify sections stack appropriately, stage board remains usable with scrolling if needed, all controls remain accessible (FR-020)
- [ ] T057 [P] [US5] Audit and fix responsive stage board grid in `solune/frontend/src/components/pipeline/PipelineBoard.tsx` — verify responsive column count using Tailwind grid/flex classes that adapt to container width at `md:` and `lg:` breakpoints (contract: PipelineBoard responsive)
- [ ] T058 [P] [US5] Audit and fix responsive pipeline flow graph in `solune/frontend/src/components/pipeline/PipelineFlowGraph.tsx` — verify visualization scales to fit container width and handles layout transitions smoothly across breakpoints (contract: PipelineFlowGraph responsive)
- [ ] T059 [US5] Audit and fix Tailwind utility compliance across all pipeline components — verify no inline `style={}` attributes, all conditional classes use `cn()` from `solune/frontend/src/lib/utils.ts`, spacing uses Tailwind scale (`gap-4`, `p-6`) with no arbitrary values like `p-[13px]`
- [ ] T060 [P] [US5] Audit and fix card/section consistency in pipeline components — verify content sections use `<Card>` from `solune/frontend/src/components/ui/card.tsx` with consistent padding and border radius matching other application pages

**Checkpoint**: Layout adapts at all breakpoints (768px–1920px), no horizontal scrolling, stage board grid responsive, flow graph scales, all styles use Tailwind utilities and design tokens.

---

## Phase 8: User Story 6 — Maintainable and Well-Tested Pipeline Code (Priority: P3)

**Goal**: Ensure the Pipeline page code follows current best practices — page file ≤250 lines with extracted sub-components, no prop drilling >2 levels, full type safety with zero `any` types, all data fetching via React Query, existing tests pass and key interactive components have dedicated test coverage, zero lint warnings, and zero type errors.

**Independent Test**: Verify page file is ≤250 lines, run `npx eslint` with zero warnings, run `npm run type-check` with zero errors, run `npx vitest run` with all tests passing, and review component structure for adherence to project conventions.

### Decompose AgentsPipelinePage (417 → ≤250 + sub-components)

- [ ] T061 [US6] Analyze `solune/frontend/src/pages/AgentsPipelinePage.tsx` (417 lines) and identify extractable sections: pipeline editor section (toolbar + board), saved workflows sidebar, analytics dashboard section, unsaved changes dialog integration
- [ ] T062 [US6] Extract `PipelineEditorSection.tsx` from `solune/frontend/src/pages/AgentsPipelinePage.tsx` into `solune/frontend/src/components/pipeline/PipelineEditorSection.tsx` — toolbar + pipeline board composition with pipeline state management props
- [ ] T063 [P] [US6] Extract `PipelineSidebarSection.tsx` from `solune/frontend/src/pages/AgentsPipelinePage.tsx` into `solune/frontend/src/components/pipeline/PipelineSidebarSection.tsx` — saved workflows list + pipeline assignment controls
- [ ] T064 [US6] Refactor `solune/frontend/src/pages/AgentsPipelinePage.tsx` to compose extracted sub-components (PipelineEditorSection, PipelineSidebarSection, PipelineAnalytics, UnsavedChangesDialog) — verify ≤250 lines, no prop drilling >2 levels (FR-021, FR-022)

### Decompose StageCard (362 → ≤250 + sub-components)

- [ ] T065 [US6] Extract `StageCardHeader.tsx` from `solune/frontend/src/components/pipeline/StageCard.tsx` into `solune/frontend/src/components/pipeline/StageCardHeader.tsx` — stage name display with inline editing, validation, and remove stage button
- [ ] T066 [P] [US6] Extract `StageCardContent.tsx` from `solune/frontend/src/components/pipeline/StageCard.tsx` into `solune/frontend/src/components/pipeline/StageCardContent.tsx` — execution groups rendering, agent node list, add agent controls
- [ ] T067 [US6] Refactor `solune/frontend/src/components/pipeline/StageCard.tsx` to compose extracted sub-components (StageCardHeader, StageCardContent) — verify ≤250 lines, no prop drilling >2 levels

### Review Borderline Components

- [ ] T068 [P] [US6] Review `solune/frontend/src/components/pipeline/PipelineBoard.tsx` (~299 lines) — if >250 lines after audit changes, extract board empty state or stage list into a sub-component; otherwise document as acceptable
- [ ] T069 [P] [US6] Review `solune/frontend/src/components/pipeline/PipelineAnalytics.tsx` (~295 lines) — if >250 lines after audit changes, extract analytics sections into sub-components; otherwise document as acceptable
- [ ] T070 [P] [US6] Review `solune/frontend/src/components/pipeline/ModelSelector.tsx` (~290 lines) — if >250 lines after audit changes, extract model option list or mode display into sub-components; otherwise document as acceptable

### Type Safety Audit

- [ ] T071 [P] [US6] Audit and eliminate all `any` types in `solune/frontend/src/components/pipeline/*.tsx` — replace with explicit types from `solune/frontend/src/types/index.ts`
- [ ] T072 [P] [US6] Audit and eliminate all type assertions (`as`) in `solune/frontend/src/components/pipeline/*.tsx` and `solune/frontend/src/hooks/usePipeline*.ts` — replace with type guards or discriminated unions
- [ ] T073 [P] [US6] Audit and add explicit types to all event handlers in pipeline components — use `React.FormEvent<HTMLFormElement>`, `React.ChangeEvent<HTMLInputElement>`, `React.MouseEvent<HTMLButtonElement>`, etc. instead of generic types
- [ ] T074 [P] [US6] Audit and verify return types on custom hooks in `solune/frontend/src/hooks/usePipelineConfig.ts`, `usePipelineBoardMutations.ts`, `usePipelineReducer.ts`, `usePipelineModelOverride.ts`, `usePipelineValidation.ts` — ensure all have explicit or unambiguously inferrable return type annotations
- [ ] T075 [US6] Audit and extract any remaining complex state logic (>15 lines of useState/useEffect/useCallback) from pipeline components into hooks in `solune/frontend/src/hooks/` — move business logic out of JSX render tree

### Data Fetching & Performance Audit

- [ ] T076 [US6] Audit and verify all API calls use `useQuery`/`useMutation` from TanStack React Query — verify no raw `useEffect` + `fetch` patterns exist in `solune/frontend/src/pages/AgentsPipelinePage.tsx` or `solune/frontend/src/components/pipeline/*.tsx` (FR-023)
- [ ] T077 [P] [US6] Audit and verify query key conventions in `solune/frontend/src/hooks/usePipelineConfig.ts` — verify `pipelineKeys` factory follows `pipelineKeys.all` / `pipelineKeys.list(projectId)` / `pipelineKeys.detail(id)` pattern consistent with `appKeys` examples
- [ ] T078 [P] [US6] Audit and fix staleTime configuration in pipeline query hooks — add reasonable `staleTime` (e.g., `30_000` for lists, `60_000` for settings) if not already configured
- [ ] T079 [US6] Audit and verify no duplicate API calls between `solune/frontend/src/pages/AgentsPipelinePage.tsx` and child components — ensure pipeline data fetched once at appropriate level and shared via props or context
- [ ] T080 [P] [US6] Audit and verify mutation success handling — verify successful mutations call `invalidateQueries` with appropriate `pipelineKeys` to refresh pipeline list in `solune/frontend/src/hooks/usePipelineConfig.ts` and `usePipelineBoardMutations.ts`
- [ ] T081 [P] [US6] Audit and fix performance for list rendering — verify StageCard, AgentNode, and saved workflow items use `key={item.id}` (never `key={index}`), expensive components wrapped in `React.memo()` where props are stable, callbacks use `useCallback` when passed to memoized children
- [ ] T082 [P] [US6] Audit and fix derived computations — verify heavy transforms (stage grouping, agent counting, model override mode derivation) in pipeline hooks wrapped in `useMemo`
- [ ] T083 [P] [US6] Audit and fix pipeline flow graph memoization in `solune/frontend/src/components/pipeline/PipelineFlowGraph.tsx` — verify rendering memoized to prevent recalculation on unrelated state changes

### Test Coverage

- [ ] T084 [US6] Verify all existing pipeline tests pass — run `cd solune/frontend && npx vitest run src/components/pipeline/ src/hooks/usePipeline*` and fix any failures introduced by audit changes
- [ ] T085 [P] [US6] Write or extend tests for `solune/frontend/src/components/pipeline/PipelineToolbar.tsx` — cover save/discard/delete button interactions, disabled states during save, verb-phrase button labels
- [ ] T086 [P] [US6] Write or extend tests for `solune/frontend/src/components/pipeline/UnsavedChangesDialog.tsx` — cover three-option dialog (save/discard/cancel), focus trapping, save failure error display
- [ ] T087 [P] [US6] Write or extend tests for `solune/frontend/src/components/pipeline/ExecutionGroupCard.tsx` — cover execution mode toggle, ARIA switch attributes, agent list rendering
- [ ] T088 [US6] Verify edge cases covered in existing tests — empty state, error state, loading state, rate limit error, long strings, null/missing data, rapid save clicks, deleted agent handling

### Code Hygiene

- [ ] T089 [US6] Remove all dead code from `solune/frontend/src/components/pipeline/*.tsx`, `solune/frontend/src/pages/AgentsPipelinePage.tsx`, and `solune/frontend/src/hooks/usePipeline*.ts` — unused imports, commented-out blocks, unreachable branches
- [ ] T090 [P] [US6] Remove all `console.log` statements from pipeline-related files
- [ ] T091 [P] [US6] Convert all relative imports to `@/` alias in pipeline-related files — replace any `../../` paths with `@/components/...`, `@/hooks/...`, `@/services/...`, `@/types/...`
- [ ] T092 [P] [US6] Extract magic strings to constants — define repeated strings (pipeline status values, query keys, route paths, tooltip text) as constants in relevant files or a shared constants module
- [ ] T093 [US6] Run ESLint on all pipeline files via `npx eslint solune/frontend/src/pages/AgentsPipelinePage.tsx solune/frontend/src/components/pipeline/ solune/frontend/src/hooks/usePipeline*` — fix all warnings and errors to reach zero (FR-024)
- [ ] T094 [US6] Run TypeScript compiler via `cd solune/frontend && npm run type-check` — fix all type errors in pipeline-related files to reach zero (FR-024)

**Checkpoint**: Page file ≤250 lines, all components ≤250 lines, zero `any` types, all React Query, existing tests pass, key components have test coverage, zero lint warnings, zero type errors.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, audit summary, and cross-cutting improvements that affect multiple user stories

- [ ] T095 Verify file naming conventions — all new extracted components are PascalCase `.tsx` in `solune/frontend/src/components/pipeline/`, hooks are `use*.ts` in `solune/frontend/src/hooks/`
- [ ] T096 [P] Run full test suite via `cd solune/frontend && npx vitest run` — verify all tests pass including any new or updated tests
- [ ] T097 [P] Run full lint check via `cd solune/frontend && npm run lint` — verify zero warnings and zero errors
- [ ] T098 [P] Run full type check via `cd solune/frontend && npm run type-check` — verify zero type errors
- [ ] T099 Produce audit summary document listing: all findings from Phase 2 assessment, all changes made (with file references), all improvements deferred for future work (with justification)
- [ ] T100 Run `specs/043-pipeline-page-audit/quickstart.md` validation — execute all verification steps (lint, type-check, test, browser check at 768px/1280px/1920px, dark mode toggle, keyboard navigation, screen reader label verification)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 assessment — fixes page states first as highest-impact MVP
- **US2 (Phase 4)**: Depends on Phase 2 assessment — accessibility fixes on current component structure
- **US3 (Phase 5)**: Depends on Phase 2 assessment — UX polish on current component structure
- **US4 (Phase 6)**: Depends on Phase 2 assessment — editing guard verification on current hooks
- **US5 (Phase 7)**: Depends on Phase 2 assessment — responsive fixes on current layout
- **US6 (Phase 8)**: Depends on US1–US5 completion preferred — decomposition and code quality as final structural pass; test tasks target final component structure
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no dependencies on other stories
- **US2 (P1)**: Can start after Phase 2 — no dependencies on other stories; may overlap with US1
- **US3 (P2)**: Can start after Phase 2 — UX polish is independent of structural changes
- **US4 (P2)**: Can start after Phase 2 — hook behavior audit is independent
- **US5 (P2)**: Can start after Phase 2 — responsive layout is independent
- **US6 (P3)**: Best after US1–US5 — decomposition applies to code after functional fixes; tests target final stable structure

### Within Each User Story

- Assessment findings (Phase 2) inform which tasks need "fix" vs. "verify"
- Decomposition (US6) must complete sub-component extraction before integration refactor
- Tests (US6) should be written against the final post-audit component structure
- Code hygiene (US6) is always the last step before validation

### Parallel Opportunities

- Phase 2: T007–T012 can all run in parallel (independent file reads)
- US1: T014, T015 (different page states) can be worked on together
- US2: T024, T025, T026 (different components) can run in parallel; T028, T029, T031, T032, T033, T034 can run in parallel
- US3: T036, T037, T040, T041, T042, T043 can run in parallel (different audit scopes)
- US4: T047 can run in parallel with other US4 tasks targeting different files
- US5: T055, T056, T057, T058, T060 can run in parallel (different components/breakpoints)
- US6 Decomposition: T063 can run in parallel with T062; T066 in parallel with T065; T068, T069, T070 all in parallel
- US6 Type Safety: T071, T072, T073, T074 can all run in parallel (different audit scopes)
- US6 Data Fetching: T077, T078, T080, T081, T082, T083 can run in parallel
- US6 Tests: T085, T086, T087 can run in parallel (different test files)
- US6 Code Hygiene: T090, T091, T092 can run in parallel (different cleanup scopes)

---

## Parallel Example: User Story 6 (Component Decomposition)

```bash
# Launch page sub-component extraction:
Task T062: "Extract PipelineEditorSection.tsx from AgentsPipelinePage.tsx"
Task T063: "Extract PipelineSidebarSection.tsx from AgentsPipelinePage.tsx"
# Then sequential: T064 refactors main AgentsPipelinePage.tsx to compose them

# Launch StageCard sub-component extraction:
Task T065: "Extract StageCardHeader.tsx from StageCard.tsx"
Task T066: "Extract StageCardContent.tsx from StageCard.tsx"
# Then sequential: T067 refactors main StageCard.tsx to compose them

# Launch borderline component reviews in parallel:
Task T068: "Review PipelineBoard.tsx (~299 lines)"
Task T069: "Review PipelineAnalytics.tsx (~295 lines)"
Task T070: "Review ModelSelector.tsx (~290 lines)"

# Launch type safety audits in parallel:
Task T071: "Eliminate any types in pipeline components"
Task T072: "Eliminate type assertions in pipeline code"
Task T073: "Add explicit event handler types"
Task T074: "Verify hook return types"

# Launch test creation in parallel:
Task T085: "Write tests for PipelineToolbar"
Task T086: "Write tests for UnsavedChangesDialog"
Task T087: "Write tests for ExecutionGroupCard"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational assessment
3. Complete Phase 3: US1 — Bug-Free Page States (loading, error, empty, rate-limit, section isolation)
4. **STOP and VALIDATE**: All page states correct, no blank screens, no raw error codes
5. Run `npx vitest run` + `npm run lint` + `npm run type-check`

### Incremental Delivery

1. Setup + Foundational → Assessment complete
2. US1 → All page states verified → Deploy/Demo (page works correctly in all states)
3. US2 → Accessible → Deploy/Demo (WCAG AA keyboard + ARIA compliant)
4. US3 → Polished UX → Deploy/Demo (professional user experience, confirmations, feedback)
5. US4 → Editing guards reliable → Deploy/Demo (no accidental data loss)
6. US5 → Responsive → Deploy/Demo (works on all desktop/laptop sizes)
7. US6 → Decomposed + type-safe + tested + clean → Deploy/Demo (maintainable code)
8. Polish → Audit summary → Final validation

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once assessment is done:
   - Developer A: US1 (Page States) + US2 (Accessibility) — P1 MVP
   - Developer B: US3 (UX Polish) + US4 (Editing Guards) — P2
3. After P1 + P2 complete:
   - Developer A: US5 (Responsive Layout) — P2
   - Developer B: US6 Decomposition + Type Safety — P3
4. Final pass: US6 Tests + Code Hygiene + Polish

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- This is a frontend-only audit — no backend changes required
- Two components require mandatory decomposition: AgentsPipelinePage (417→≤250 lines), StageCard (362→≤250 lines)
- Three components are borderline (290–299 lines): PipelineBoard, PipelineAnalytics, ModelSelector — review after audit changes
- Largest hook is usePipelineBoardMutations (418 lines) — review for decomposition opportunities
- Legacy backward compatibility: `syncLegacyAgents()` keeps `stage.agents[]` in sync with `stage.groups[].agents[]` — handle gracefully
- Existing tests: 5 component test files + 2 hook test files — verify all pass, extend coverage per FR-025
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same-file conflicts, unnecessary cross-story dependencies
