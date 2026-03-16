# Tasks: Pipeline Page Audit

**Input**: Design documents from `/specs/043-pipeline-page-audit/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/component-contracts.yaml ✅, quickstart.md ✅

**Tests**: Tests are included for US6 (Code Quality) where the spec requires key interactive components to have dedicated test files (FR-025). Existing test files are maintained; new test tasks are scoped to gap coverage only.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/frontend/src/` for all frontend source files
- **Tests**: Co-located with source (e.g., `ComponentName.test.tsx` next to `ComponentName.tsx`)
- **Hooks**: `solune/frontend/src/hooks/usePipeline*.ts`
- **Types**: `solune/frontend/src/types/index.ts`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Discovery, assessment, and project-level preparation before any audit changes

- [ ] T001 Read and document current state of `solune/frontend/src/pages/AgentsPipelinePage.tsx` — note line count, sub-components used, hooks consumed, API calls made, and all identified issues against the 10-category audit checklist
- [ ] T002 Read all pipeline components in `solune/frontend/src/components/pipeline/` and catalog each file's line count, props interface, state management pattern, accessibility gaps, and design token compliance
- [ ] T003 Read all pipeline hooks in `solune/frontend/src/hooks/usePipelineConfig.ts`, `solune/frontend/src/hooks/usePipelineBoardMutations.ts`, `solune/frontend/src/hooks/usePipelineReducer.ts`, `solune/frontend/src/hooks/usePipelineModelOverride.ts`, `solune/frontend/src/hooks/usePipelineValidation.ts`, and `solune/frontend/src/hooks/useSelectedPipeline.ts` — note error handling, type safety, and mutation feedback patterns
- [ ] T004 Run existing pipeline tests (`npx vitest run src/components/pipeline/ src/hooks/usePipeline*`) and record pass/fail status, coverage gaps, and missing test files
- [ ] T005 Run linter (`npx eslint src/pages/AgentsPipelinePage.tsx src/components/pipeline/ src/hooks/usePipeline*`) and record all warnings/errors
- [ ] T006 Run type checker (`npx tsc --noEmit`) and record any type errors in pipeline-related files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Structural refactoring that MUST be complete before user story–specific fixes can be applied cleanly

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 Extract pipeline board section from `solune/frontend/src/pages/AgentsPipelinePage.tsx` into `solune/frontend/src/components/pipeline/PipelineBoardSection.tsx` — move board rendering logic including empty state, loading state, and error state into a dedicated sub-component
- [ ] T008 Extract saved workflows section from `solune/frontend/src/pages/AgentsPipelinePage.tsx` into `solune/frontend/src/components/pipeline/SavedWorkflowsSection.tsx` — move saved pipelines list rendering with its own loading/error handling
- [ ] T009 Extract analytics dashboard section from `solune/frontend/src/pages/AgentsPipelinePage.tsx` into `solune/frontend/src/components/pipeline/PipelineAnalyticsSection.tsx` — move analytics rendering with independent error state
- [ ] T010 Verify `solune/frontend/src/pages/AgentsPipelinePage.tsx` is now ≤250 lines after extraction, composes sub-components cleanly, and no prop is drilled more than 2 levels (FR-021, FR-022)
- [ ] T011 Update barrel export in `solune/frontend/src/components/pipeline/index.ts` to include newly extracted sub-components
- [ ] T012 [P] Verify all pipeline hooks return `rawError` for rate-limit detection — update `solune/frontend/src/hooks/usePipelineConfig.ts` to expose `rawError` and `refetch` if not already present
- [ ] T013 [P] Verify all data fetching in pipeline hooks uses React Query (`useQuery`/`useMutation`) with `pipelineKeys` factory — audit `solune/frontend/src/hooks/usePipelineBoardMutations.ts` for any raw `useEffect` + `fetch` patterns (FR-023)

**Checkpoint**: Foundation ready — page is ≤250 lines, sub-components extracted, hooks expose error details. User story implementation can now begin in parallel.

---

## Phase 3: User Story 1 — Bug-Free and Complete Page States (Priority: P1) 🎯 MVP

**Goal**: Ensure every page state (loading, empty, populated, saving, error, rate-limit, deleted pipeline) renders correctly with appropriate messaging and recovery actions.

**Independent Test**: Trigger each page state and verify correct rendering — loading shows CelestialLoader, no-project shows ProjectSelectionEmptyState, empty board shows CTA, save error shows user-friendly message, rate-limit shows specific message, deleted pipeline handled gracefully, section failures isolated.

### Implementation for User Story 1

- [ ] T014 [US1] Add or verify loading state in `solune/frontend/src/components/pipeline/PipelineBoardSection.tsx` — render `<CelestialLoader size="md" />` while pipeline data query `isLoading` is true; never show blank screen (FR-001)
- [ ] T015 [US1] Add or verify no-project-selected state in `solune/frontend/src/pages/AgentsPipelinePage.tsx` — render `<ProjectSelectionEmptyState>` with guidance text when no project is selected (FR-002)
- [ ] T016 [US1] Add or verify empty pipeline board state in `solune/frontend/src/components/pipeline/PipelineBoardSection.tsx` — render empty state with illustrative icon and "Create Pipeline" call-to-action when board has no stages (FR-003)
- [ ] T017 [P] [US1] Add user-friendly error messages for save failures in `solune/frontend/src/hooks/usePipelineBoardMutations.ts` — format errors as "Could not save pipeline. [Reason]. [Next step]." using `friendlyErrorMessage()` utility; handle name conflict (HTTP 409) with specific message (FR-004, FR-012)
- [ ] T018 [P] [US1] Add rate-limit error detection in `solune/frontend/src/hooks/usePipelineBoardMutations.ts` — use `isRateLimitApiError()` from `@/utils/rateLimit` in all mutation `onError` handlers to surface specific rate-limit messaging (FR-005)
- [ ] T019 [US1] Implement independent error states for each section — `solune/frontend/src/components/pipeline/PipelineBoardSection.tsx`, `solune/frontend/src/components/pipeline/SavedWorkflowsSection.tsx`, and `solune/frontend/src/components/pipeline/PipelineAnalyticsSection.tsx` each handle their own query errors with retry actions (FR-006)
- [ ] T020 [US1] Handle deleted/missing pipeline gracefully in `solune/frontend/src/hooks/usePipelineConfig.ts` — when selected pipeline returns 404, clear selection and display fallback message instead of crashing
- [ ] T021 [US1] Disable save button during save operation (`isSaving` state) in `solune/frontend/src/components/pipeline/PipelineToolbar.tsx` to prevent duplicate API calls from rapid clicks

**Checkpoint**: At this point, User Story 1 should be fully functional — every page state renders correctly with user-friendly messaging.

---

## Phase 4: User Story 2 — Accessible Pipeline Page (Priority: P1)

**Goal**: Ensure full keyboard accessibility, ARIA compliance, focus management in dialogs, and non-color-dependent status indicators across the Pipeline page.

**Independent Test**: Navigate the entire Pipeline page using only keyboard — Tab through all interactive elements, open/close dialogs with Escape, verify screen reader announcements, run automated a11y scanner.

### Implementation for User Story 2

- [ ] T022 [P] [US2] Add keyboard accessibility and ARIA attributes to saved workflow cards in `solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx` — convert styled divs to proper interactive elements (buttons) with `role`, `aria-label`, keyboard activation via Enter/Space (FR-026, FR-013)
- [ ] T023 [P] [US2] Add ARIA attributes to execution mode toggle in `solune/frontend/src/components/pipeline/ExecutionGroupCard.tsx` — add `role="switch"`, `aria-checked`, `aria-label` for execution mode (sequential/parallel) toggle control (FR-013)
- [ ] T024 [P] [US2] Add focus management to `solune/frontend/src/components/pipeline/UnsavedChangesDialog.tsx` — verify focus trap while open, Escape closes dialog, focus returns to trigger element on close (FR-014)
- [ ] T025 [P] [US2] Add visible focus indicators to all interactive elements in `solune/frontend/src/components/pipeline/PipelineToolbar.tsx` — ensure all buttons use `celestial-focus` class or Tailwind `focus-visible:` ring styles (FR-013)
- [ ] T026 [P] [US2] Add ARIA attributes and keyboard navigation to `solune/frontend/src/components/pipeline/ModelSelector.tsx` — ensure dropdown is keyboard-navigable (Arrow keys, Enter to select, Escape to close), with `aria-expanded`, `aria-label`, `role="listbox"` (FR-013)
- [ ] T027 [P] [US2] Add labels and `aria-describedby` for validation errors on pipeline name input in `solune/frontend/src/components/pipeline/PipelineBoard.tsx` and stage name inputs in `solune/frontend/src/components/pipeline/StageCard.tsx` — associate error messages programmatically with input fields (FR-016, FR-011)
- [ ] T028 [P] [US2] Add non-color-dependent status indicators across pipeline components — ensure execution mode indicators in `solune/frontend/src/components/pipeline/ExecutionGroupCard.tsx`, pipeline save state in `solune/frontend/src/components/pipeline/PipelineToolbar.tsx`, and analytics metrics in `solune/frontend/src/components/pipeline/PipelineAnalytics.tsx` use icon + text, not color alone (FR-015)
- [ ] T029 [P] [US2] Add `aria-hidden="true"` to decorative Lucide icons and `aria-label` to meaningful icons across all pipeline components in `solune/frontend/src/components/pipeline/`
- [ ] T030 [US2] Verify logical tab order across the full Pipeline page — toolbar → board → saved workflows → analytics — and fix any tab order issues in `solune/frontend/src/pages/AgentsPipelinePage.tsx`

**Checkpoint**: At this point, User Story 2 should be fully functional — all interactive elements are keyboard-accessible with proper ARIA attributes and focus management.

---

## Phase 5: User Story 3 — Consistent and Polished User Experience (Priority: P2)

**Goal**: Align all visual elements with Celestial design tokens, finalize copy/terminology, add confirmation dialogs on destructive actions, and provide success feedback for all mutations.

**Independent Test**: Compare Pipeline page visually against other pages (Agents, Projects, Settings) for consistency; verify all text is final; test destructive actions trigger confirmation; test mutations produce success feedback; toggle light/dark mode.

### Implementation for User Story 3

- [ ] T031 [P] [US3] Audit and replace all hardcoded colors in `solune/frontend/src/components/pipeline/PipelineBoard.tsx` with Celestial design tokens (`bg-card`, `text-foreground`, `border-border`, etc.) — remove any raw hex/rgb values or `bg-white`/`text-gray-*` classes (FR-017)
- [ ] T032 [P] [US3] Audit and replace all hardcoded colors in `solune/frontend/src/components/pipeline/StageCard.tsx` with Celestial design tokens (FR-017)
- [ ] T033 [P] [US3] Audit and replace all hardcoded colors in `solune/frontend/src/components/pipeline/AgentNode.tsx` with Celestial design tokens (FR-017)
- [ ] T034 [P] [US3] Audit and replace all hardcoded colors in `solune/frontend/src/components/pipeline/PipelineFlowGraph.tsx` with Celestial design tokens — verify SVG/canvas elements use theme-aware colors for dark mode support (FR-017)
- [ ] T035 [P] [US3] Audit and replace all hardcoded colors in `solune/frontend/src/components/pipeline/PipelineAnalytics.tsx` with Celestial design tokens (FR-017)
- [ ] T036 [P] [US3] Audit and replace all hardcoded colors in `solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx` with Celestial design tokens (FR-017)
- [ ] T037 [P] [US3] Audit and replace all hardcoded colors in `solune/frontend/src/components/pipeline/ExecutionGroupCard.tsx`, `solune/frontend/src/components/pipeline/ModelSelector.tsx`, `solune/frontend/src/components/pipeline/PipelineModelDropdown.tsx`, and `solune/frontend/src/components/pipeline/PresetBadge.tsx` with Celestial design tokens (FR-017)
- [ ] T038 [US3] Audit all user-visible text across all files in `solune/frontend/src/components/pipeline/` and `solune/frontend/src/pages/AgentsPipelinePage.tsx` for placeholder text ("TODO", "Lorem ipsum", "Test") and inconsistent terminology — replace "workflow" with "pipeline" in user-facing strings, ensure button labels are verb phrases ("Save Pipeline", "Delete Pipeline", "Discard Changes"), and verify all copy is final and meaningful (FR-018, FR-019)
- [ ] T039 [P] [US3] Add confirmation dialogs for all destructive actions missing them — verify delete pipeline, remove stage, remove agent, and discard changes all use `<ConfirmationDialog>` in `solune/frontend/src/components/pipeline/PipelineToolbar.tsx`, `solune/frontend/src/components/pipeline/StageCard.tsx`, and `solune/frontend/src/components/pipeline/ExecutionGroupCard.tsx` (FR-007)
- [ ] T040 [P] [US3] Add success feedback (toast notifications) for all mutations in `solune/frontend/src/hooks/usePipelineBoardMutations.ts` — save, create, duplicate, and delete operations should provide visible success confirmation (FR-008)
- [ ] T041 [P] [US3] Add text truncation with tooltips for long pipeline names, agent names, model names, and descriptions in `solune/frontend/src/components/pipeline/AgentNode.tsx`, `solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx`, and `solune/frontend/src/components/pipeline/StageCard.tsx` — use `text-ellipsis` with `<Tooltip>` for full text (FR-018)
- [ ] T042 [P] [US3] Verify timestamps use relative format ("2 hours ago") for recent entries and absolute format for older entries in `solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx` — use `formatTimeAgo` from `@/utils/formatTime` (FR-018)
- [ ] T043 [US3] Verify light/dark mode rendering for all pipeline components in `solune/frontend/src/components/pipeline/` and `solune/frontend/src/pages/AgentsPipelinePage.tsx` — test theme switching and confirm no visual artifacts, unreadable text, or missing styles across the pipeline board, flow graph, analytics dashboard, and dialogs

**Checkpoint**: At this point, User Story 3 should be fully functional — visual consistency, final copy, confirmation dialogs, and success feedback all in place.

---

## Phase 6: User Story 4 — Reliable Pipeline Editing and Navigation Guards (Priority: P2)

**Goal**: Ensure unsaved-changes guards activate correctly for all navigation/action triggers, the dialog offers Save/Discard/Cancel, and save failures are handled gracefully within the dialog.

**Independent Test**: Make changes to a pipeline, then attempt to: navigate away, close browser tab, load a different pipeline, create a new pipeline — verify unsaved-changes dialog appears each time with correct behavior for all three options.

### Implementation for User Story 4

- [ ] T044 [US4] Verify unsaved-changes guard activates on in-app navigation in `solune/frontend/src/hooks/usePipelineConfig.ts` — confirm `useBlocker` from react-router triggers when `isDirty` is true and user navigates away (FR-009)
- [ ] T045 [P] [US4] Verify browser `beforeunload` warning on tab close in `solune/frontend/src/hooks/usePipelineConfig.ts` — confirm `beforeunload` event listener is attached when `isDirty` is true (FR-009)
- [ ] T046 [US4] Verify unsaved-changes guard activates when loading a different saved pipeline in `solune/frontend/src/components/pipeline/SavedWorkflowsSection.tsx` — confirm dialog appears before loading new pipeline data (FR-009)
- [ ] T047 [US4] Verify unsaved-changes guard activates when creating a new pipeline in `solune/frontend/src/components/pipeline/PipelineToolbar.tsx` — confirm dialog appears before resetting board state (FR-009)
- [ ] T048 [US4] Verify `solune/frontend/src/components/pipeline/UnsavedChangesDialog.tsx` offers three options: "Save Pipeline", "Discard Changes", and "Cancel" with correct behavior — Save triggers save mutation then continues pending action on success, Discard reverts to last snapshot and continues pending action, Cancel closes dialog with no side effects (FR-010)
- [ ] T049 [US4] Handle save failure within the unsaved-changes dialog in `solune/frontend/src/components/pipeline/UnsavedChangesDialog.tsx` — if save fails during "Save and Continue", dialog stays open with user-friendly error message and save button re-enabled
- [ ] T050 [US4] Verify pipeline name conflict handling in `solune/frontend/src/hooks/usePipelineBoardMutations.ts` — HTTP 409 conflict error displays "Could not save pipeline. The name '[name]' is already in use. Please try a different name." and preserves all other unsaved changes (FR-012)

**Checkpoint**: At this point, User Story 4 should be fully functional — unsaved-changes guards work correctly for all triggers with graceful error handling.

---

## Phase 7: User Story 5 — Responsive Layout Across Screen Sizes (Priority: P2)

**Goal**: Ensure the Pipeline page layout adapts gracefully from 768px to 1920px without horizontal scrolling, overlapping elements, or truncated controls.

**Independent Test**: Resize browser window across breakpoints (768px, 1024px, 1280px, 1920px) and verify layout reflow — sections stack at narrow widths, board adapts column count, flow graph scales, all controls remain accessible.

### Implementation for User Story 5

- [ ] T051 [P] [US5] Add responsive layout classes to `solune/frontend/src/pages/AgentsPipelinePage.tsx` — use Tailwind responsive utilities (`md:`, `lg:`, `xl:`) for multi-column to stacked layout transition across the board, saved workflows, and analytics sections (FR-020)
- [ ] T052 [P] [US5] Add responsive grid adaptation to `solune/frontend/src/components/pipeline/PipelineBoard.tsx` — stage card grid adapts column count based on viewport width using Tailwind grid responsive classes (FR-020)
- [ ] T053 [P] [US5] Add responsive scaling to `solune/frontend/src/components/pipeline/PipelineFlowGraph.tsx` — flow graph visualization scales with container width, no fixed pixel widths (FR-020)
- [ ] T054 [P] [US5] Add responsive behavior to `solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx` — list adapts layout for narrow viewports, collapsible panel or stacked view at `md:` breakpoint (FR-020)
- [ ] T055 [P] [US5] Add responsive behavior to `solune/frontend/src/components/pipeline/PipelineAnalytics.tsx` — analytics dashboard adapts grid layout for narrow viewports (FR-020)
- [ ] T056 [US5] Verify smooth layout transitions when resizing across breakpoints — no broken intermediate states, overlapping elements, or horizontal scrolling in `solune/frontend/src/pages/AgentsPipelinePage.tsx` and all sub-components

**Checkpoint**: At this point, User Story 5 should be fully functional — layout adapts gracefully across all supported viewport widths.

---

## Phase 8: User Story 6 — Maintainable and Well-Tested Pipeline Code (Priority: P3)

**Goal**: Ensure code quality meets project conventions — zero lint warnings, zero type errors, no `any` types, no dead code, proper imports, and key interactive components have test coverage.

**Independent Test**: Run `npx eslint`, `npx tsc --noEmit`, and `npx vitest run` on all pipeline-related files — all pass with zero warnings/errors. Review component structure for convention adherence.

### Tests for User Story 6

> **NOTE: Write tests for interactive components that lack dedicated test coverage (FR-025)**

- [ ] T057 [P] [US6] Add test file for PipelineToolbar in `solune/frontend/src/components/pipeline/PipelineToolbar.test.tsx` — cover button rendering, disabled states during save, click handlers, and keyboard activation
- [ ] T058 [P] [US6] Add test file for ExecutionGroupCard in `solune/frontend/src/components/pipeline/ExecutionGroupCard.test.tsx` — cover execution mode toggle, agent list rendering, and accessibility attributes
- [ ] T059 [P] [US6] Add test file for UnsavedChangesDialog in `solune/frontend/src/components/pipeline/UnsavedChangesDialog.test.tsx` — cover three-option behavior (save, discard, cancel), focus management, and Escape key handling
- [ ] T060 [P] [US6] Add test file for usePipelineBoardMutations hook in `solune/frontend/src/hooks/usePipelineBoardMutations.test.ts` — cover mutation success/error handling, rate-limit detection, and user-friendly error message formatting

### Implementation for User Story 6

- [ ] T061 [P] [US6] Remove all `any` types and unsafe type assertions (`as`) from pipeline components and hooks — add explicit type annotations in `solune/frontend/src/components/pipeline/` and `solune/frontend/src/hooks/usePipeline*.ts` (FR-024)
- [ ] T062 [P] [US6] Remove dead code — unused imports, commented-out blocks, unreachable branches, and `console.log` statements from all pipeline files in `solune/frontend/src/components/pipeline/` and `solune/frontend/src/hooks/usePipeline*.ts`
- [ ] T063 [P] [US6] Fix import paths in all files under `solune/frontend/src/components/pipeline/` and `solune/frontend/src/hooks/usePipeline*.ts` — ensure all project imports use `@/` alias (`@/components/...`, `@/hooks/...`, `@/services/...`) instead of relative `../../` paths
- [ ] T064 [P] [US6] Extract repeated magic strings in `solune/frontend/src/components/pipeline/` and `solune/frontend/src/hooks/usePipeline*.ts` — status values, route paths, query keys into named constants or existing constant modules
- [ ] T065 [US6] Run `npx eslint src/pages/AgentsPipelinePage.tsx src/components/pipeline/ src/hooks/usePipeline*` and fix all remaining warnings to achieve 0 warnings (FR-024)
- [ ] T066 [US6] Run `npx tsc --noEmit` and fix all type errors in pipeline-related files to achieve 0 type errors (FR-024)
- [ ] T067 [US6] Run `npx vitest run` and verify all existing and new pipeline tests pass

**Checkpoint**: All user stories should now be independently functional with zero lint warnings, zero type errors, and full test coverage for key interactive components.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cross-cutting improvements that affect multiple user stories

- [ ] T068 [P] Verify `solune/frontend/src/components/pipeline/PipelineBoard.tsx` uses stable `key={item.id}` for all list renders — never `key={index}` for stages, groups, or agent nodes
- [ ] T069 [P] Wrap expensive derived computations in `useMemo` — model override derivation in `solune/frontend/src/hooks/usePipelineModelOverride.ts`, analytics calculations in `solune/frontend/src/components/pipeline/PipelineAnalytics.tsx`, and stage grouping in `solune/frontend/src/components/pipeline/PipelineBoard.tsx`
- [ ] T070 [P] Add `React.memo()` to frequently-rendered list items — `solune/frontend/src/components/pipeline/StageCard.tsx`, `solune/frontend/src/components/pipeline/AgentNode.tsx`, and `solune/frontend/src/components/pipeline/ExecutionGroupCard.tsx` — if not already memoized and receiving stable props
- [ ] T071 [P] Verify `useCallback` usage for mutation handlers passed to memoized child components in `solune/frontend/src/hooks/usePipelineBoardMutations.ts`
- [ ] T072 Run full validation suite — `npx eslint src/pages/AgentsPipelinePage.tsx src/components/pipeline/ src/hooks/usePipeline*` (0 warnings), `npx tsc --noEmit` (0 errors), `npx vitest run` (all pass)
- [ ] T073 Run quickstart.md validation — execute setup steps from `specs/043-pipeline-page-audit/quickstart.md` to confirm audit workflow is reproducible

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories (page must be ≤250 lines before story-specific fixes)
- **User Story 1 (Phase 3)**: Depends on Phase 2 — can start after foundational extraction
- **User Story 2 (Phase 4)**: Depends on Phase 2 — can run in parallel with US1
- **User Story 3 (Phase 5)**: Depends on Phase 2 — can run in parallel with US1/US2
- **User Story 4 (Phase 6)**: Depends on Phase 2 — can run in parallel with US1/US2/US3
- **User Story 5 (Phase 7)**: Depends on Phase 2 (extracted sub-components) — can run in parallel with other stories
- **User Story 6 (Phase 8)**: Depends on Phases 3–7 (audit changes should be in place before final code quality pass)
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 — No dependencies on other stories
- **User Story 2 (P1)**: Can start after Phase 2 — No dependencies on other stories
- **User Story 3 (P2)**: Can start after Phase 2 — No dependencies on other stories; benefits from US1 error handling being in place
- **User Story 4 (P2)**: Can start after Phase 2 — No dependencies on other stories; shares mutation hooks with US1
- **User Story 5 (P2)**: Can start after Phase 2 — No dependencies on other stories
- **User Story 6 (P3)**: Should start after Phases 3–7 — covers all audit changes for lint/type/test validation

### Within Each User Story

- Hooks/utilities before component changes
- Components before page-level integration
- Independent sections can be parallelized (different files)
- Story complete before moving to next priority (recommended, not required)

### Parallel Opportunities

- All Setup tasks (T001–T006) are sequential (assessment feeds into planning)
- Foundational tasks T012 and T013 can run in parallel
- US1 tasks T017 and T018 can run in parallel (different error handling concerns in same file — hooks)
- US2 tasks T022–T029 can ALL run in parallel (different component files)
- US3 tasks T031–T037 can ALL run in parallel (design token audit of different files)
- US3 tasks T039–T042 can run in parallel (different concerns)
- US5 tasks T051–T055 can ALL run in parallel (responsive layout in different files)
- US6 tests T057–T060 can ALL run in parallel (new test files)
- US6 implementation T061–T064 can ALL run in parallel (different cleanup concerns)
- Polish tasks T068–T071 can ALL run in parallel (different performance concerns)
- **Cross-story parallelism**: US1 through US5 can be worked on in parallel after Phase 2, as they modify different files

---

## Parallel Example: User Story 2 (Accessibility)

```bash
# Launch all accessibility fixes in parallel (different component files):
Task T022: "Add keyboard accessibility to saved workflow cards in SavedWorkflowsList.tsx"
Task T023: "Add ARIA attributes to execution mode toggle in ExecutionGroupCard.tsx"
Task T024: "Add focus management to UnsavedChangesDialog.tsx"
Task T025: "Add visible focus indicators to PipelineToolbar.tsx"
Task T026: "Add ARIA attributes and keyboard navigation to ModelSelector.tsx"
Task T027: "Add labels and aria-describedby to PipelineBoard.tsx and StageCard.tsx"
Task T028: "Add non-color-dependent status indicators across multiple components"
Task T029: "Add aria-hidden to decorative icons across pipeline components"
```

---

## Parallel Example: User Story 3 (Design Token Audit)

```bash
# Launch all design token audit fixes in parallel (different component files):
Task T031: "Audit hardcoded colors in PipelineBoard.tsx"
Task T032: "Audit hardcoded colors in StageCard.tsx"
Task T033: "Audit hardcoded colors in AgentNode.tsx"
Task T034: "Audit hardcoded colors in PipelineFlowGraph.tsx"
Task T035: "Audit hardcoded colors in PipelineAnalytics.tsx"
Task T036: "Audit hardcoded colors in SavedWorkflowsList.tsx"
Task T037: "Audit hardcoded colors in ExecutionGroupCard.tsx, ModelSelector.tsx, PipelineModelDropdown.tsx, PresetBadge.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (discovery & assessment)
2. Complete Phase 2: Foundational (extract page to ≤250 lines)
3. Complete Phase 3: User Story 1 (bug-free page states)
4. **STOP and VALIDATE**: Test all page states independently — loading, empty, error, rate-limit, deleted pipeline, partial section failures
5. Deploy/demo if ready — the Pipeline page now has complete, user-friendly state handling

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (page refactored, hooks expose errors)
2. Add User Story 1 (P1) → Test page states → Deploy/Demo (**MVP!**)
3. Add User Story 2 (P1) → Test keyboard/a11y → Deploy/Demo (WCAG AA compliant)
4. Add User Story 3 (P2) → Test visual consistency → Deploy/Demo (polished UX)
5. Add User Story 4 (P2) → Test unsaved-changes guards → Deploy/Demo (reliable editing)
6. Add User Story 5 (P2) → Test responsive layout → Deploy/Demo (responsive)
7. Add User Story 6 (P3) → Run lint/type/test → Deploy/Demo (code quality)
8. Complete Polish phase → Full validation → Final release

### Parallel Team Strategy

With multiple developers after Phase 2 completion:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (page states) + User Story 4 (editing guards) — related mutation hooks
   - Developer B: User Story 2 (accessibility) — component-level ARIA/keyboard fixes
   - Developer C: User Story 3 (design tokens + UX polish) + User Story 5 (responsive) — visual/layout work
3. Developer D (or any): User Story 6 (code quality + tests) — after stories 1–5 merge
4. All: Polish phase as final validation

---

## Notes

- [P] tasks = different files, no dependencies on other in-progress tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- This is an audit/refactor feature — no new backend API changes, no new entities, no new features
- Existing test files (PipelineBoard.test.tsx, PipelineFlowGraph.test.tsx, StageCard.test.tsx, AgentNode.test.tsx, SavedWorkflowsList.test.tsx) must continue to pass after all changes
- Total tasks: 73 (T001–T073)
- Key reference files: `specs/043-pipeline-page-audit/research.md` (design system tokens), `specs/043-pipeline-page-audit/contracts/component-contracts.yaml` (component interfaces), `specs/043-pipeline-page-audit/data-model.md` (entity relationships)
