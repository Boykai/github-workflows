# Tasks: Pipeline Page Audit

**Input**: Design documents from `/specs/043-pipeline-page-audit/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/component-contracts.yaml, quickstart.md

**Tests**: Test tasks are included because the feature specification explicitly requires them (FR-025, SC-011). Key interactive components missing test coverage (PipelineToolbar, UnsavedChangesDialog, ExecutionGroupCard) need dedicated test files.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. This is a frontend-only audit — no backend changes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Project root**: `solune/frontend/` (all paths below are relative to repository root)
- **Components**: `solune/frontend/src/components/pipeline/`
- **Hooks**: `solune/frontend/src/hooks/`
- **Page**: `solune/frontend/src/pages/AgentsPipelinePage.tsx`
- **Design tokens**: `solune/frontend/src/index.css`
- **Shared UI**: `solune/frontend/src/components/ui/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify development environment, establish baseline, and prepare for audit work

- [ ] T001 Install frontend dependencies and verify dev environment by running `npm install` in solune/frontend/
- [ ] T002 Run baseline tests, linting, and type-check (`npx vitest run && npm run lint && npm run type-check`) to establish starting state in solune/frontend/
- [ ] T003 [P] Review Celestial design token reference and custom utility classes in solune/frontend/src/index.css to document audit baseline

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Decompose AgentsPipelinePage.tsx from ~417 lines to ≤250 lines (FR-021). This refactoring MUST complete before user story work begins since it restructures the files that all stories touch.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Analyze AgentsPipelinePage.tsx to identify extraction boundaries and plan sub-component split in solune/frontend/src/pages/AgentsPipelinePage.tsx
- [ ] T005 Extract pipeline editor/board orchestration section into a dedicated sub-component in solune/frontend/src/components/pipeline/
- [ ] T006 [P] Extract saved workflows sidebar section into a dedicated sub-component in solune/frontend/src/components/pipeline/
- [ ] T007 [P] Extract analytics dashboard section into a dedicated sub-component in solune/frontend/src/components/pipeline/
- [ ] T008 Refactor AgentsPipelinePage.tsx to compose extracted sections with ≤250 lines target in solune/frontend/src/pages/AgentsPipelinePage.tsx
- [ ] T009 [P] Update barrel export with any new sub-components in solune/frontend/src/components/pipeline/index.ts
- [ ] T010 Run existing test suite and type-check to confirm zero regressions after decomposition in solune/frontend/

**Checkpoint**: Page decomposition complete — AgentsPipelinePage.tsx ≤250 lines, all existing tests pass, zero type errors

---

## Phase 3: User Story 1 — Bug-Free and Complete Page States (Priority: P1) 🎯 MVP

**Goal**: Every page state (loading, empty, populated, saving, error, rate-limit) renders correctly with appropriate messaging and recovery actions. Users never see a blank screen, raw error codes, or broken layout.

**Independent Test**: Trigger each page state (loading, no project selected, empty pipeline board, populated board, save in progress, save error, rate limit error, deleted pipeline) and verify each renders correctly with appropriate messaging and recovery actions.

### Implementation for User Story 1

- [ ] T011 [US1] Audit and fix loading state to display CelestialLoader with no blank screen or layout shift in solune/frontend/src/pages/AgentsPipelinePage.tsx
- [ ] T012 [P] [US1] Audit and fix no-project-selected state to render ProjectSelectionEmptyState with guidance text in solune/frontend/src/pages/AgentsPipelinePage.tsx
- [ ] T013 [P] [US1] Audit and fix empty pipeline board state with illustrative icon and create-pipeline CTA in solune/frontend/src/components/pipeline/PipelineBoard.tsx
- [ ] T014 [P] [US1] Audit and fix save error display to follow "Could not [action]. [Reason]. [Next step]." format (FR-004) in solune/frontend/src/components/pipeline/PipelineToolbar.tsx
- [ ] T015 [P] [US1] Audit and fix rate limit error detection using isRateLimitApiError() and specific user messaging (FR-005) in solune/frontend/src/hooks/usePipelineBoardMutations.ts
- [ ] T016 [P] [US1] Audit and fix deleted/missing pipeline handling to show graceful fallback without crash in solune/frontend/src/hooks/usePipelineConfig.ts
- [ ] T017 [US1] Audit and fix section-level error isolation so pipeline list, assignment, and analytics fail independently (FR-006) across solune/frontend/src/components/pipeline/PipelineBoard.tsx, SavedWorkflowsList.tsx, and PipelineAnalytics.tsx
- [ ] T018 [US1] Audit all mutation onError handlers for user-friendly message format and rate limit detection across solune/frontend/src/hooks/usePipelineBoardMutations.ts and solune/frontend/src/hooks/usePipelineConfig.ts

**Checkpoint**: At this point, User Story 1 should be fully functional — every page state renders correctly with appropriate messaging

---

## Phase 4: User Story 2 — Accessible Pipeline Page (Priority: P1)

**Goal**: Full WCAG AA compliance — every interactive element is keyboard-accessible, has proper ARIA attributes, and works with screen readers. Dialogs trap focus, status is conveyed via icon+text, and form inputs have associated labels.

**Independent Test**: Navigate the entire Pipeline page using only a keyboard; run an automated accessibility scanner (jest-axe); verify screen reader announcements for all interactive elements including toolbar, stage cards, agent nodes, execution groups, saved workflow cards, and dialogs.

### Implementation for User Story 2

- [ ] T019 [US2] Audit and fix keyboard navigation (Tab order, Enter/Space activation, visible focus indicators) across all pipeline components in solune/frontend/src/components/pipeline/
- [ ] T020 [P] [US2] Refactor saved workflow cards to proper interactive elements (button or link, not styled div) with keyboard activation and screen reader announcements (FR-026) in solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx
- [ ] T021 [P] [US2] Audit and fix dialog focus trapping, Escape-to-close, and focus return to trigger element (FR-014) in solune/frontend/src/components/pipeline/UnsavedChangesDialog.tsx
- [ ] T022 [P] [US2] Audit and fix execution mode toggle with role="switch" and aria-checked state (FR-013) in solune/frontend/src/components/pipeline/ExecutionGroupCard.tsx
- [ ] T023 [P] [US2] Audit and fix form input labels (visible label or aria-label) for pipeline name and stage name fields (FR-016) in solune/frontend/src/components/pipeline/PipelineToolbar.tsx and solune/frontend/src/components/pipeline/StageCard.tsx
- [ ] T024 [P] [US2] Audit and fix status indicators to convey meaning via icon+text, not color alone (FR-015) in solune/frontend/src/components/pipeline/ExecutionGroupCard.tsx and solune/frontend/src/components/pipeline/PresetBadge.tsx
- [ ] T025 [P] [US2] Audit and fix validation error association via aria-describedby for name inputs in solune/frontend/src/components/pipeline/StageCard.tsx and solune/frontend/src/components/pipeline/PipelineToolbar.tsx
- [ ] T026 [P] [US2] Audit and fix decorative icons with aria-hidden="true" and meaningful icons with aria-label across all components in solune/frontend/src/components/pipeline/
- [ ] T027 [US2] Audit and fix ModelSelector keyboard navigation (arrow keys, Enter to select, Escape to close) and ARIA attributes (aria-haspopup, aria-expanded, role="option") in solune/frontend/src/components/pipeline/ModelSelector.tsx

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently — full keyboard navigation and screen reader support verified

---

## Phase 5: User Story 3 — Consistent and Polished User Experience (Priority: P2)

**Goal**: Visual consistency with the Celestial design system, professional copy, proper feedback for all actions, and polished light/dark mode support across the entire Pipeline page.

**Independent Test**: Visually compare the Pipeline page against other pages (Agents, Projects, Settings); verify all text is final and consistent; check destructive actions require confirmation; validate mutations provide success feedback; toggle light/dark mode.

### Implementation for User Story 3

- [ ] T028 [US3] Audit and replace all hardcoded colors (hex values, bg-white, text-gray-*, text-black) with Celestial design tokens (bg-card, text-card-foreground, border-border, bg-muted) across all files in solune/frontend/src/components/pipeline/
- [ ] T029 [P] [US3] Audit and fix all user-visible text for final meaningful copy with consistent terminology ("pipeline" not "workflow", "stage" not "step") across all components in solune/frontend/src/components/pipeline/
- [ ] T030 [P] [US3] Audit and fix destructive action confirmations via ConfirmationDialog before delete pipeline, remove stage, remove agent, and discard changes (FR-007) in solune/frontend/src/components/pipeline/PipelineToolbar.tsx, solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx, and solune/frontend/src/components/pipeline/StageCard.tsx
- [ ] T031 [P] [US3] Audit and fix success feedback (toast notifications) for save, create, duplicate, and delete mutations (FR-008) in solune/frontend/src/hooks/usePipelineBoardMutations.ts and solune/frontend/src/hooks/usePipelineConfig.ts
- [ ] T032 [P] [US3] Audit and fix light/dark mode rendering for all pipeline components including flow graph, analytics, and dialogs in solune/frontend/src/components/pipeline/
- [ ] T033 [P] [US3] Audit and fix text truncation with ellipsis and tooltip for long pipeline names, agent names, and model names (FR-018) in solune/frontend/src/components/pipeline/AgentNode.tsx, solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx, and solune/frontend/src/components/pipeline/StageCard.tsx
- [ ] T034 [P] [US3] Audit and fix button labels to use verb phrases ("Save Pipeline", "Delete Pipeline", "Discard Changes") instead of generic nouns (FR-019) in solune/frontend/src/components/pipeline/PipelineToolbar.tsx
- [ ] T035 [US3] Audit and fix timestamp formatting to use relative time for recent and absolute dates for older entries in solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently — visual consistency, professional copy, and proper feedback verified

---

## Phase 6: User Story 4 — Reliable Pipeline Editing and Navigation Guards (Priority: P2)

**Goal**: Unsaved changes are never lost — the editor protects work via in-app navigation guards, browser beforeunload, and the UnsavedChangesDialog with Save/Discard/Cancel options.

**Independent Test**: Create/edit a pipeline, make unsaved changes, then attempt to navigate away, close the browser tab, create a new pipeline, or load a different saved pipeline — verify the unsaved-changes guard activates correctly in each case with proper Save/Discard/Cancel behavior.

### Implementation for User Story 4

- [ ] T036 [US4] Audit and fix in-app navigation guard (useBlocker from react-router) for unsaved changes on route navigation in solune/frontend/src/hooks/usePipelineConfig.ts
- [ ] T037 [P] [US4] Audit and fix browser beforeunload warning when closing tab with unsaved changes in solune/frontend/src/hooks/usePipelineConfig.ts
- [ ] T038 [US4] Audit and fix unsaved-changes guard when user clicks to load a different saved pipeline in solune/frontend/src/hooks/usePipelineConfig.ts and solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx
- [ ] T039 [US4] Audit and fix unsaved-changes guard when user clicks "Create New Pipeline" with pending edits in solune/frontend/src/hooks/usePipelineConfig.ts
- [ ] T040 [US4] Audit and fix UnsavedChangesDialog three-option behavior (Save/Discard/Cancel) and save-error state handling in solune/frontend/src/components/pipeline/UnsavedChangesDialog.tsx
- [ ] T041 [P] [US4] Audit and fix discard action to revert to last saved snapshot with no residual dirty state in solune/frontend/src/hooks/usePipelineReducer.ts
- [ ] T042 [US4] Audit and fix save-from-dialog to continue pending action automatically on success in solune/frontend/src/hooks/usePipelineConfig.ts
- [ ] T043 [US4] Audit and fix pipeline name conflict error (HTTP 409) with user-friendly message identifying the conflicting name (FR-012) in solune/frontend/src/hooks/usePipelineBoardMutations.ts

**Checkpoint**: At this point, User Stories 1–4 should all work independently — unsaved changes protection verified across all trigger scenarios

---

## Phase 7: User Story 5 — Responsive Layout Across Screen Sizes (Priority: P2)

**Goal**: The Pipeline page adapts gracefully from 768px to 1920px — sections reflow, grids adjust column count, and the flow graph scales with container width. No horizontal scrolling or overlapping elements.

**Independent Test**: Resize the browser window across supported breakpoints (768px, 1024px, 1280px, 1920px) and verify the pipeline editor, stage board, saved workflows list, and analytics dashboard adapt their layout without horizontal scrolling, overlapping elements, or truncated controls.

### Implementation for User Story 5

- [ ] T044 [US5] Audit and fix desktop layout (1920px) for effective space usage and appropriate section spacing in solune/frontend/src/pages/AgentsPipelinePage.tsx
- [ ] T045 [P] [US5] Audit and fix PipelineBoard stage grid column adaptation at 1280px and 768px breakpoints using Tailwind responsive utilities in solune/frontend/src/components/pipeline/PipelineBoard.tsx
- [ ] T046 [P] [US5] Audit and fix PipelineFlowGraph responsive scaling to fit container width in solune/frontend/src/components/pipeline/PipelineFlowGraph.tsx
- [ ] T047 [P] [US5] Audit and fix SavedWorkflowsList responsive behavior (collapse or adapt) at narrow viewports in solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx
- [ ] T048 [US5] Audit and fix section stacking, smooth layout transitions at 768px breakpoint, and verify no broken intermediate states in solune/frontend/src/pages/AgentsPipelinePage.tsx

**Checkpoint**: All user stories 1–5 should now be independently functional — responsive layout verified at all target breakpoints

---

## Phase 8: User Story 6 — Maintainable and Well-Tested Pipeline Code (Priority: P3)

**Goal**: Code quality meets project conventions — zero lint warnings, zero type errors, no prop drilling >2 levels, no `any` types, all data fetching via React Query, and key interactive components have dedicated test files (FR-025, SC-011).

**Independent Test**: Run linter with zero warnings, type-check with zero errors, full test suite passes, and verify component structure follows project conventions (file organization, hook extraction, prop patterns).

### Implementation for User Story 6

- [ ] T049 [US6] Verify AgentsPipelinePage.tsx is ≤250 lines after Phase 2 extraction (FR-021) in solune/frontend/src/pages/AgentsPipelinePage.tsx
- [ ] T050 [P] [US6] Audit and fix any remaining prop drilling exceeding 2 levels by using composition, context, or hook extraction (FR-022) across all pipeline components in solune/frontend/src/components/pipeline/
- [ ] T051 [P] [US6] Verify all data fetching uses React Query patterns with no raw fetch calls in useEffect (FR-023) across all hooks in solune/frontend/src/hooks/usePipeline*.ts
- [ ] T052 [P] [US6] Fix all linting warnings in pipeline-related files (FR-024) in solune/frontend/src/pages/AgentsPipelinePage.tsx, solune/frontend/src/components/pipeline/, and solune/frontend/src/hooks/usePipeline*.ts
- [ ] T053 [P] [US6] Fix all TypeScript type errors, remove `any` types and unsafe `as` assertions in pipeline-related files (FR-024) in solune/frontend/src/
- [ ] T054 [P] [US6] Remove dead code, unused imports, and console.log statements across all pipeline files in solune/frontend/src/components/pipeline/ and solune/frontend/src/hooks/
- [ ] T055 [P] [US6] Add test coverage for PipelineToolbar covering save/discard/delete interactions and disabled states in solune/frontend/src/components/pipeline/PipelineToolbar.test.tsx
- [ ] T056 [P] [US6] Add test coverage for UnsavedChangesDialog covering three-option behavior, focus management, and save error state in solune/frontend/src/components/pipeline/UnsavedChangesDialog.test.tsx
- [ ] T057 [P] [US6] Add test coverage for ExecutionGroupCard covering execution mode toggle and agent list rendering in solune/frontend/src/components/pipeline/ExecutionGroupCard.test.tsx
- [ ] T058 [US6] Run full test suite and verify all pipeline-related tests pass with complete changes in solune/frontend/

**Checkpoint**: Code quality verified — zero lint warnings, zero type errors, key components have test coverage, all tests pass

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all user stories and comprehensive quality check

- [ ] T059 [P] Run full lint check confirming zero warnings across all pipeline files in solune/frontend/
- [ ] T060 [P] Run full type-check confirming zero type errors in pipeline-related files in solune/frontend/
- [ ] T061 Run complete test suite (`npx vitest run`) and confirm all tests pass in solune/frontend/
- [ ] T062 Run quickstart.md validation checklist covering all priority sections (P1, P2, P3) from specs/043-pipeline-page-audit/quickstart.md
- [ ] T063 Final visual review of Pipeline page in light mode, dark mode, and at 768px, 1280px, and 1920px viewports in solune/frontend/

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories (page decomposition must complete first)
- **User Stories (Phases 3–8)**: All depend on Foundational phase completion
  - US1 and US2 are both P1 — can proceed in parallel or sequentially
  - US3, US4, US5 are all P2 — can proceed in parallel after Foundational
  - US6 (P3) can proceed in parallel but test tasks should run after audit fixes are complete
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) — Independent of US1/US2 but benefits from their fixes
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) — Independent of other stories
- **User Story 5 (P2)**: Can start after Foundational (Phase 2) — Independent of other stories
- **User Story 6 (P3)**: Can start after Foundational (Phase 2) — Test tasks (T055–T057) should run after US1–US5 audit fixes for comprehensive coverage

### Within Each User Story

- Audit/fix tasks touching the same file should be done sequentially
- Tasks touching different files (marked [P]) can be done in parallel
- Cross-file audit tasks (T017, T019, T026, T028) should be done after file-specific tasks

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (T006 and T007 touch different files)
- Once Foundational completes, US1 and US2 can start in parallel (different audit concerns)
- US3, US4, and US5 can all proceed in parallel (mostly different files and concerns)
- Within US6, all [P] tasks touch different files or concerns and can run in parallel

---

## Parallel Example: Foundational Phase

```text
# After T004 (analysis) and T005 (editor extraction) complete sequentially:
# Launch remaining extractions in parallel:
Task T006: "Extract saved workflows sidebar section into sub-component"
Task T007: "Extract analytics dashboard section into sub-component"
Task T009: "Update barrel export in index.ts"
```

## Parallel Example: User Story 1

```text
# After T011 (loading state) completes:
# Launch independent page-state audits in parallel:
Task T012: "Audit no-project-selected state in AgentsPipelinePage.tsx"
Task T013: "Audit empty pipeline board state in PipelineBoard.tsx"
Task T014: "Audit save error display in PipelineToolbar.tsx"
Task T015: "Audit rate limit error detection in usePipelineBoardMutations.ts"
Task T016: "Audit deleted pipeline handling in usePipelineConfig.ts"
```

## Parallel Example: User Story 2

```text
# Launch independent a11y audits in parallel (all touch different files):
Task T020: "Refactor saved workflow cards in SavedWorkflowsList.tsx"
Task T021: "Audit dialog focus trapping in UnsavedChangesDialog.tsx"
Task T022: "Audit execution mode toggle ARIA in ExecutionGroupCard.tsx"
Task T023: "Audit form input labels in PipelineToolbar.tsx and StageCard.tsx"
Task T024: "Audit status indicators in ExecutionGroupCard.tsx and PresetBadge.tsx"
```

## Parallel Example: User Story 6

```text
# Launch independent code quality tasks in parallel:
Task T050: "Audit prop drilling violations across pipeline components"
Task T051: "Verify React Query usage in pipeline hooks"
Task T052: "Fix linting warnings in pipeline files"
Task T053: "Fix TypeScript errors in pipeline files"
Task T054: "Remove dead code across pipeline files"
Task T055: "Add PipelineToolbar test file"
Task T056: "Add UnsavedChangesDialog test file"
Task T057: "Add ExecutionGroupCard test file"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — page decomposition blocks all stories)
3. Complete Phase 3: User Story 1 — Bug-Free Page States
4. **STOP and VALIDATE**: Test every page state independently (loading, empty, error, populated, saving)
5. Deploy/demo if ready — users will have a reliable, bug-free Pipeline page

### Incremental Delivery

1. Complete Setup + Foundational → Page decomposed, foundation ready
2. Add User Story 1 (P1) → Test independently → Bug-free states verified (MVP!)
3. Add User Story 2 (P1) → Test independently → Full accessibility compliance
4. Add User Story 3 (P2) → Test independently → Visual consistency and polish
5. Add User Story 4 (P2) → Test independently → Unsaved changes protection
6. Add User Story 5 (P2) → Test independently → Responsive layout verified
7. Add User Story 6 (P3) → Test independently → Code quality and test coverage
8. Each story adds audit quality without breaking previous fixes

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Bug-Free States) + User Story 2 (Accessibility)
   - Developer B: User Story 3 (UX Polish) + User Story 4 (Editing Guards)
   - Developer C: User Story 5 (Responsive) + User Story 6 (Code Quality)
3. Stories complete and integrate independently — all touch different audit concerns

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- This is an **audit/refactor** — no new features, no backend changes, no new API endpoints
- All changes target `solune/frontend/src/` — primarily `pages/AgentsPipelinePage.tsx` and `components/pipeline/`
- Design token reference: `solune/frontend/src/index.css` (Celestial theme custom properties)
- Use `cn()` from `solune/frontend/src/lib/utils.ts` for conditional Tailwind classes
- Use `isRateLimitApiError()` from `solune/frontend/src/utils/rateLimit.ts` for rate limit detection
- Legacy compatibility: `syncLegacyAgents()` and `ensureDefaultGroups()` must continue to work
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
