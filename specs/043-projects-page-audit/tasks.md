# Tasks: Projects Page Audit

**Input**: Design documents from `/specs/043-projects-page-audit/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are explicitly required by the feature specification (FR-034, FR-035, SC-008: ≥80% coverage target). Test tasks are included in Phase 9 (US7).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. The audit covers 7 user stories across 10 phases.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Project type**: Web application (monorepo)
- **Frontend root**: `solune/frontend/`
- **Pages**: `solune/frontend/src/pages/`
- **Feature components**: `solune/frontend/src/components/board/`
- **Hooks**: `solune/frontend/src/hooks/`
- **Shared UI**: `solune/frontend/src/components/ui/`
- **Shared common**: `solune/frontend/src/components/common/`
- **Types**: `solune/frontend/src/types/`
- **Constants**: `solune/frontend/src/constants/`
- **Utilities**: `solune/frontend/src/utils/`, `solune/frontend/src/lib/`

## Phase 1: Setup (Discovery & Assessment)

**Purpose**: Establish baseline audit findings by running existing tooling and scoring each audit checklist item

- [ ] T001 Run existing project and board tests (`npx vitest run src/pages/ProjectsPage src/hooks/useProjectBoard src/hooks/useProjects src/hooks/useBoardControls src/hooks/useBoardRefresh src/components/board/`) and document pass/fail status
- [ ] T002 [P] Run ESLint on Projects page and board components (`npx eslint src/pages/ProjectsPage.tsx src/components/board/`) and document violations
- [ ] T003 [P] Run type-check (`npm run type-check`) and document type errors
- [ ] T004 Score each audit checklist item (Pass/Fail/N/A) across all 10 categories and produce findings table per specs/043-projects-page-audit/contracts/audit-findings-contract.md schema

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Verify existing infrastructure and prepare extraction targets before any user story work begins

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Verify shared component availability — confirm CelestialLoader, ErrorBoundary, ProjectSelectionEmptyState, ThemedAgentIcon imports resolve correctly from solune/frontend/src/components/common/
- [ ] T006 [P] Verify utility imports — confirm cn() from solune/frontend/src/lib/utils.ts, isRateLimitApiError/extractRateLimitInfo from solune/frontend/src/utils/rateLimit.ts, formatTimeAgo/formatTimeUntil from solune/frontend/src/utils/formatTime.ts resolve correctly
- [ ] T007 [P] Verify existing hook exports — confirm useProjectBoard, useProjects, useBoardControls, useBoardRefresh compile and export expected typed interfaces from solune/frontend/src/hooks/
- [ ] T008 [P] Verify STALE_TIME constants — confirm STALE_TIME_PROJECTS, STALE_TIME_SHORT, STALE_TIME_MEDIUM exist in solune/frontend/src/constants/index.ts

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 2 — Page is Modular and Maintainable (Priority: P1) 🎯 MVP

**Goal**: Decompose the 630-line `ProjectsPage.tsx` into a ≤250-line orchestrator and 4 focused sub-components in `src/components/board/`. All business logic remains in hooks; no prop drilling exceeds 2 levels.

**Independent Test**: Verify `ProjectsPage.tsx` is ≤250 lines (`wc -l`), sub-components exist in `src/components/board/`, and no prop drilling exceeds 2 levels.

**Note**: US2 (modularity) is placed before US1 (loading states) because the decomposed page structure is required for properly implementing per-section loading/error states in US1.

### Implementation for User Story 2

- [ ] T009 [US2] Extract project selector section (~lines 170–270) from ProjectsPage.tsx into solune/frontend/src/components/board/ProjectSelector.tsx — implement ProjectSelectorProps interface per page-decomposition-contract.md (projects, selectedProject, onSelect, isLoading); include internal search state and dropdown open/close state
- [ ] T010 [US2] Extract board header section (~lines 280–380) from ProjectsPage.tsx into solune/frontend/src/components/board/BoardHeader.tsx — implement BoardHeaderProps interface per page-decomposition-contract.md (projectName, syncStatus, lastUpdated, syncLastUpdate, onRefresh, isRefreshing); pure presentation component
- [ ] T011 [US2] Extract rate limit banner section (~lines 380–430) from ProjectsPage.tsx into solune/frontend/src/components/board/RateLimitBanner.tsx — implement RateLimitBannerProps interface per page-decomposition-contract.md (rateLimitInfo, isLow); conditionally renders based on isLow flag; uses formatTimeUntil() for reset countdown
- [ ] T012 [US2] Extract pipeline selector/grid section (~lines 450–580) from ProjectsPage.tsx into solune/frontend/src/components/board/PipelineSelector.tsx — implement PipelineSelectorProps interface per page-decomposition-contract.md (projectId, boardData, availableAgents); includes internal useQuery for pipeline list and useMutation for assignment
- [ ] T013 [US2] Refactor ProjectsPage.tsx to compose extracted sub-components as orchestrator (target ≤250 lines) in solune/frontend/src/pages/ProjectsPage.tsx — follow layout structure from page-decomposition-contract.md: RateLimitBanner → CelestialCatalogHero with ProjectSelector → conditional content (loading/error/empty/board) → IssueDetailModal
- [ ] T014 [US2] Verify no prop drilling exceeds 2 levels — trace data flow from solune/frontend/src/pages/ProjectsPage.tsx through ProjectSelector, BoardHeader, RateLimitBanner, PipelineSelector, BoardToolbar, ProjectBoard per prop flow diagram in page-decomposition-contract.md
- [ ] T015 [US2] Move any remaining inline business logic (computation, data transformation, conditional formatting) from JSX into hooks or helper functions in solune/frontend/src/pages/ProjectsPage.tsx
- [ ] T016 [US2] Run lint (`npx eslint src/pages/ProjectsPage.tsx src/components/board/ProjectSelector.tsx src/components/board/BoardHeader.tsx src/components/board/RateLimitBanner.tsx src/components/board/PipelineSelector.tsx`) and type-check (`npm run type-check`) to verify decomposition introduces no errors

**Checkpoint**: At this point, ProjectsPage.tsx is ≤250 lines and delegates rendering to focused sub-components. User Story 2 is fully functional and testable independently.

---

## Phase 4: User Story 1 — Page Loads Reliably with Clear Feedback (Priority: P1)

**Goal**: Every navigation to the Projects page produces immediate, informative feedback: loading indicator while fetching, user-friendly error with retry on failure, meaningful empty state when no data, rate-limit banner when GitHub API limits are exceeded.

**Independent Test**: Navigate to the Projects page under four conditions (normal load, API failure, empty data, rate limit exceeded) and verify appropriate feedback in each case. No blank screens or raw error codes at any point.

### Implementation for User Story 1

- [ ] T017 [US1] Verify and fix loading state — must use `<CelestialLoader size="md" />` while data loads, never show blank screen in solune/frontend/src/pages/ProjectsPage.tsx
- [ ] T018 [US1] Verify and fix error state — API errors must render user-friendly message per FR-026 format ("Could not [action]. [Reason]. [Suggested next step].") with a retry button that calls refetch() in solune/frontend/src/pages/ProjectsPage.tsx
- [ ] T019 [US1] Verify and fix empty state — no project selected shows `<ProjectSelectionEmptyState />`; zero projects shows meaningful empty state with guidance in solune/frontend/src/pages/ProjectsPage.tsx
- [ ] T020 [US1] Verify and fix rate limit detection — use isRateLimitApiError() for detection, display RateLimitBanner with formatTimeUntil() reset countdown per state-management-contract.md error handling strategy in solune/frontend/src/components/board/RateLimitBanner.tsx
- [ ] T021 [US1] Verify partial loading independence — board section errors must not block the project selector or page header; each section shows its own loading/error state in solune/frontend/src/pages/ProjectsPage.tsx
- [ ] T022 [US1] Verify ErrorBoundary wraps the page at route level in solune/frontend/src/App.tsx (confirmed at line 121 per research.md)
- [ ] T023 [US1] Add `<ConfirmationDialog>` to any destructive actions missing confirmation (pipeline unassignment, board cleanup) in solune/frontend/src/components/board/

**Checkpoint**: At this point, the page loads reliably under all conditions. User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 — Page is Fully Accessible (Priority: P2)

**Goal**: Every interactive element is keyboard-reachable (Tab) and activatable (Enter/Space). Dialogs trap focus. ARIA attributes are correct on all custom controls. Color is never the sole status indicator. Focus styles are visible.

**Independent Test**: Navigate the entire page using only a keyboard and verify all interactions work. Run axe DevTools audit for ARIA compliance and color contrast.

### Implementation for User Story 3

- [ ] T024 [P] [US3] Audit and fix keyboard accessibility (Tab order, Enter/Space activation) for all interactive elements in solune/frontend/src/pages/ProjectsPage.tsx and solune/frontend/src/components/board/
- [ ] T025 [P] [US3] Verify and fix focus trapping in IssueDetailModal — focus must be trapped while open and return to trigger on close in solune/frontend/src/components/board/IssueDetailModal.tsx
- [ ] T026 [P] [US3] Verify and fix focus trapping in CleanUpConfirmModal — focus must be trapped while open and return to trigger on close in solune/frontend/src/components/board/CleanUpConfirmModal.tsx
- [ ] T027 [US3] Add ARIA attributes to ProjectSelector dropdown — role="combobox", aria-expanded, aria-haspopup="listbox" on trigger; role="listbox" on list; role="option" + aria-selected on items per quickstart.md ARIA pattern in solune/frontend/src/components/board/ProjectSelector.tsx
- [ ] T028 [US3] Add ARIA attributes to PipelineSelector dropdown — aria-label="Select pipeline", role="listbox" on list, role="option" on items in solune/frontend/src/components/board/PipelineSelector.tsx
- [ ] T029 [US3] Add ARIA attributes to BoardToolbar filter/sort controls — aria-label on filter buttons, aria-pressed on toggle buttons in solune/frontend/src/components/board/BoardToolbar.tsx
- [ ] T030 [US3] Verify all form fields have associated labels (visible or aria-label) across solune/frontend/src/components/board/ — especially search inputs in ProjectSelector and filter inputs in BoardToolbar
- [ ] T031 [US3] Ensure status indicators use icon or text label alongside color — never color alone per FR-020 in solune/frontend/src/components/board/BoardHeader.tsx (sync status) and solune/frontend/src/components/board/BoardColumn.tsx (column headers)
- [ ] T032 [US3] Add visible focus styles (focus-visible: ring or celestial-focus class) to all interactive elements lacking them in solune/frontend/src/components/board/
- [ ] T033 [US3] Mark decorative icons with aria-hidden="true" and add aria-label to meaningful icons across solune/frontend/src/components/board/

**Checkpoint**: All interactive elements are keyboard-accessible with correct ARIA attributes.

---

## Phase 6: User Story 4 — Text, Copy, and UX Are Polished (Priority: P2)

**Goal**: All user-visible text is final and consistent. Action buttons use verb phrases. Destructive actions require confirmation. Mutations show success/failure feedback. Long text is truncated with tooltip.

**Independent Test**: Review all visible strings for placeholders, verify button labels are verbs, confirm destructive actions show confirmation dialogs, and check mutation feedback.

### Implementation for User Story 4

- [ ] T034 [P] [US4] Audit all user-visible strings for placeholder text, TODOs, lorem ipsum, or "Test" text — replace with final meaningful copy in solune/frontend/src/pages/ProjectsPage.tsx and solune/frontend/src/components/board/
- [ ] T035 [P] [US4] Verify all action button labels use verb phrases (e.g., "Assign Pipeline" not "Pipeline", "Clear Filters" not "Filters", "Create Project" not "New Project") in solune/frontend/src/components/board/
- [ ] T036 [US4] Verify all destructive actions use `<ConfirmationDialog>` — pipeline unassignment, cleanup actions, any delete/remove in solune/frontend/src/components/board/CleanUpButton.tsx and solune/frontend/src/components/board/PipelineSelector.tsx
- [ ] T037 [US4] Verify all mutations show success feedback (toast notification, inline status change, or visual confirmation) per FR-025 — check onSuccess callbacks in solune/frontend/src/hooks/useBoardControls.ts, solune/frontend/src/hooks/useBoardRefresh.ts, and solune/frontend/src/components/board/PipelineSelector.tsx
- [ ] T038 [US4] Verify all mutation error messages follow FR-026 format ("Could not [action]. [Reason, if known]. [Suggested next step].") — check onError callbacks in solune/frontend/src/hooks/useBoardControls.ts, solune/frontend/src/hooks/useBoardRefresh.ts, and solune/frontend/src/components/board/PipelineSelector.tsx
- [ ] T039 [US4] Add `<Tooltip>` for truncated text — project names (>40 chars), descriptions, URLs, status column names use text-ellipsis with tooltip showing full content in solune/frontend/src/components/board/ProjectSelector.tsx, solune/frontend/src/components/board/IssueCard.tsx, and solune/frontend/src/components/board/BoardColumn.tsx

**Checkpoint**: All text is polished, actions provide feedback, and long content has tooltips.

---

## Phase 7: User Story 5 — Styling Is Consistent and Responsive (Priority: P3)

**Goal**: Page renders correctly at 768px–1920px viewports, supports light and dark modes, uses Tailwind utility classes only (no inline styles), and follows the design system spacing scale.

**Independent Test**: Resize viewport from 768px to 1920px and toggle light/dark mode. Verify no layout breaks, contrast failures, or hardcoded colors.

### Implementation for User Story 5

- [ ] T040 [P] [US5] Replace inline style={} attributes with Tailwind utilities or CSS custom properties in solune/frontend/src/pages/ProjectsPage.tsx — known instances: pipeline grid layout (line ~536, use CSS custom property `--grid-cols` with Tailwind `grid-cols-[var(--grid-cols)]`) and status dot color (line ~552, acceptable exception for API-driven dynamic colors per research.md RT-005)
- [ ] T041 [P] [US5] Verify responsive layout at 768px–1920px — fix any horizontal scrolling, overflow, or overlapping elements in solune/frontend/src/pages/ProjectsPage.tsx and solune/frontend/src/components/board/
- [ ] T042 [P] [US5] Verify dark mode support — no hardcoded colors (bg-white, #fff, text-black, etc.); all colors use Tailwind dark: variants or CSS custom properties from the theme in solune/frontend/src/pages/ProjectsPage.tsx and solune/frontend/src/components/board/
- [ ] T043 [US5] Verify consistent spacing — all spacing uses Tailwind scale (gap-4, p-6, etc.), no arbitrary pixel values (p-[13px]) in solune/frontend/src/pages/ProjectsPage.tsx and solune/frontend/src/components/board/
- [ ] T044 [US5] Verify Card/section consistency — content sections use `<Card>` from solune/frontend/src/components/ui/card.tsx with consistent padding and border radius

**Checkpoint**: Styling is consistent, responsive, and theme-aware.

---

## Phase 8: User Story 6 — Page Performs Well Under Load (Priority: P3)

**Goal**: Board renders efficiently with 50+ items. Lists use stable keys. Expensive computations are memoized. No duplicate API calls. No unnecessary re-renders.

**Independent Test**: Load a board with 50+ items and verify smooth scrolling, no jank, and no duplicate API calls in the network panel.

### Implementation for User Story 6

- [ ] T045 [P] [US6] Verify all list renders use stable keys (item.id or unique identifier, never array index) across solune/frontend/src/components/board/BoardColumn.tsx, solune/frontend/src/components/board/IssueCard.tsx, solune/frontend/src/components/board/ProjectSelector.tsx, and solune/frontend/src/components/board/PipelineSelector.tsx
- [ ] T046 [P] [US6] Verify no duplicate API calls — each data source fetched exactly once per state-management-contract.md query key conventions in solune/frontend/src/hooks/useProjectBoard.ts, solune/frontend/src/hooks/useProjects.ts, and solune/frontend/src/components/board/PipelineSelector.tsx
- [ ] T047 [US6] Wrap expensive computations (sorting, filtering, grouping board items) in useMemo where missing in solune/frontend/src/hooks/useBoardControls.ts
- [ ] T048 [US6] Verify React.memo() on expensive pure components (IssueCard, BoardColumn, AgentTile) and useCallback on handlers passed to memoized children in solune/frontend/src/components/board/

**Checkpoint**: Page performs well with large datasets and no wasteful re-renders.

---

## Phase 9: User Story 7 — Comprehensive Test Coverage (Priority: P3)

**Goal**: All custom hooks and key interactive components have automated tests covering happy path, error state, loading state, empty state, and edge cases. Tests follow codebase conventions (vi.mock, renderHook, waitFor, createWrapper). Target ≥80% coverage.

**Independent Test**: Run `npx vitest run` and verify all project-related tests pass. Check coverage for hooks and key components.

### Tests for User Story 7 ⚠️

> **NOTE: Tests are explicitly required by spec FR-034, FR-035, SC-008.**

- [ ] T049 [P] [US7] Update hook tests for useProjectBoard — add coverage for error response, loading state, empty board data, and staleTime behavior in solune/frontend/src/hooks/useProjectBoard.test.tsx
- [ ] T050 [P] [US7] Update hook tests for useProjects — add coverage for error response, loading state, empty project list, and project selection mutation in solune/frontend/src/hooks/useProjects.test.tsx
- [ ] T051 [P] [US7] Update hook tests for useBoardControls — add edge case coverage for rapid project switching, null board data, drag-and-drop with missing fields in solune/frontend/src/hooks/useBoardControls.test.tsx
- [ ] T052 [P] [US7] Update hook tests for useBoardRefresh — add rate limit scenario coverage (isRateLimitApiError detection, reset countdown, auto-recovery) in solune/frontend/src/hooks/useBoardRefresh.test.tsx
- [ ] T053 [P] [US7] Write component tests for ProjectSelector — test search filtering, project selection callback, keyboard navigation, loading state, empty list in solune/frontend/src/components/board/ProjectSelector.test.tsx
- [ ] T054 [P] [US7] Write component tests for PipelineSelector — test pipeline selection, mutation success/error feedback, confirmation dialog for override, loading state in solune/frontend/src/components/board/PipelineSelector.test.tsx
- [ ] T055 [P] [US7] Write component tests for BoardHeader — test sync status display (connected/disconnected/syncing), refresh button interaction, timestamp display in solune/frontend/src/components/board/BoardHeader.test.tsx
- [ ] T056 [P] [US7] Write component tests for RateLimitBanner — test conditional visibility, reset countdown display, role="alert" attribute in solune/frontend/src/components/board/RateLimitBanner.test.tsx
- [ ] T057 [US7] Write component tests for BoardToolbar — test filter/sort interactions, keyboard accessibility, aria-label attributes in solune/frontend/src/components/board/BoardToolbar.test.tsx
- [ ] T058 [US7] Verify edge case coverage — null/missing optional fields, rate limit errors, long strings (>60 char titles), rapid project switching, WebSocket disconnect/reconnect in solune/frontend/src/pages/ProjectsPage.test.tsx

**Checkpoint**: All hooks and key interactive components have comprehensive test coverage.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Code hygiene, dead code removal, and final validation across all user stories

- [ ] T059 [P] Remove dead code — unused imports, commented-out blocks, unreachable branches in solune/frontend/src/pages/ProjectsPage.tsx and solune/frontend/src/components/board/
- [ ] T060 [P] Remove any console.log statements in solune/frontend/src/pages/ProjectsPage.tsx and solune/frontend/src/components/board/
- [ ] T061 [P] Verify all imports use @/ alias — no deep relative paths (../../) in solune/frontend/src/pages/ProjectsPage.tsx, solune/frontend/src/components/board/, and solune/frontend/src/hooks/
- [ ] T062 Define repeated strings (status values, route paths, query keys) as constants in solune/frontend/src/constants/index.ts — verify no magic strings in page or component files
- [ ] T063 Run ESLint — 0 warnings: `npx eslint src/pages/ProjectsPage.tsx src/components/board/ src/hooks/useProjectBoard.ts src/hooks/useProjects.ts src/hooks/useBoardControls.ts src/hooks/useBoardRefresh.ts`
- [ ] T064 Run type-check — 0 errors: `npm run type-check`
- [ ] T065 Run full test suite — all tests pass: `npx vitest run`
- [ ] T066 Run quickstart.md validation steps — verify loading state, error state, empty state, rate limit banner, dark mode, responsive layout, keyboard navigation per specs/043-projects-page-audit/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US2 Modular (Phase 3)**: Depends on Foundational — BLOCKS US1, US3, US4, US5, US6 (page structure must be decomposed first)
- **US1 Reliable Loading (Phase 4)**: Depends on US2 completion (needs decomposed page structure for per-section states)
- **US3 Accessible (Phase 5)**: Depends on US2 completion (needs finalized component structure for ARIA attributes)
- **US4 UX Polish (Phase 6)**: Depends on US2 completion (needs finalized components for text/copy review)
- **US5 Styling (Phase 7)**: Can start after US2 completion — independent of US1, US3, US4
- **US6 Performance (Phase 8)**: Can start after US2 completion — independent of US1, US3, US4
- **US7 Test Coverage (Phase 9)**: Depends on US1, US2, US3, US4 completion (tests validate implemented behavior)
- **Polish (Phase 10)**: Depends on all user stories being complete

### User Story Dependencies

- **US2 (P1) Modular**: Can start after Foundational (Phase 2) — 🎯 MVP — BLOCKS all other stories
- **US1 (P1) Reliable Loading**: Depends on US2 — needs decomposed page structure
- **US3 (P2) Accessible**: Depends on US2 — needs finalized component structure
- **US4 (P2) UX Polish**: Depends on US2 — needs finalized components
- **US5 (P3) Styling**: Depends on US2 — can parallel with US1, US3, US4
- **US6 (P3) Performance**: Depends on US2 — can parallel with US1, US3, US4
- **US7 (P3) Test Coverage**: Depends on US1+US2+US3+US4 — tests validate all implemented behavior

### Within Each User Story

- Models/types before services
- Services before endpoints/components
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1**: T002, T003 can run in parallel with each other (different tooling)
- **Phase 2**: T005, T006, T007, T008 can all run in parallel (different verification targets)
- **Phase 3 (US2)**: T009–T012 are sequential (all extract from the same source file ProjectsPage.tsx); T014–T015 sequential after T013
- **Phase 4 (US1)**: T017–T022 are mostly sequential (modifying the same page structure)
- **Phase 5 (US3)**: T024, T025, T026 can run in parallel (different files); T027, T028, T029 can run in parallel (different components)
- **Phase 6 (US4)**: T034, T035 can run in parallel (different concern areas)
- **Phase 7 (US5)**: T040, T041, T042 can run in parallel (different concern areas)
- **Phase 8 (US6)**: T045, T046 can run in parallel (different files)
- **Phase 9 (US7)**: T049–T056 can all run in parallel (different test files); T057–T058 sequential (depend on prior stories)
- **Phase 10**: T059, T060, T061 can run in parallel (different concerns)
- **Cross-phase**: After US2 completes, US5 and US6 can run in parallel with US1, US3, US4

---

## Parallel Example: User Story 2 (Phase 3)

```bash
# Sequential — all extract from the same ProjectsPage.tsx source:
Task T009: "Extract project selector into ProjectSelector.tsx"
Task T010: "Extract board header into BoardHeader.tsx"
Task T011: "Extract rate limit banner into RateLimitBanner.tsx"
Task T012: "Extract pipeline selector into PipelineSelector.tsx"
Task T013: "Refactor ProjectsPage.tsx to compose sub-components"

# Then parallel verification:
Task T014: "Verify prop drilling ≤2 levels"  (parallel with T015)
Task T015: "Move inline business logic"       (parallel with T014)
```

## Parallel Example: User Story 7 (Phase 9)

```bash
# All test files can be written in parallel (different files):
Task T049: "Update useProjectBoard tests"     (parallel)
Task T050: "Update useProjects tests"          (parallel)
Task T051: "Update useBoardControls tests"     (parallel)
Task T052: "Update useBoardRefresh tests"      (parallel)
Task T053: "Write ProjectSelector tests"       (parallel)
Task T054: "Write PipelineSelector tests"      (parallel)
Task T055: "Write BoardHeader tests"           (parallel)
Task T056: "Write RateLimitBanner tests"       (parallel)
```

## Parallel Example: Cross-Phase After US2

```bash
# Once US2 (Phase 3) completes, these phases can run in parallel:
Phase 4 (US1): Reliable Loading   — Developer A
Phase 5 (US3): Accessibility      — Developer B
Phase 7 (US5): Styling            — Developer C
Phase 8 (US6): Performance        — Developer D
```

---

## Implementation Strategy

### MVP First (User Story 2 Only)

1. Complete Phase 1: Setup (discovery & assessment)
2. Complete Phase 2: Foundational (verify infrastructure)
3. Complete Phase 3: User Story 2 (page decomposition)
4. **STOP and VALIDATE**: Verify ProjectsPage.tsx is ≤250 lines, all 4 sub-components exist, app builds and tests pass
5. Deploy/demo if ready — the page is now modular and maintainable

### Incremental Delivery

1. Complete Setup + Foundational → Assessment complete
2. Add User Story 2 → Test independently → **MVP! Page is decomposed**
3. Add User Story 1 → Test independently → Page loads reliably
4. Add User Story 3 → Test independently → Page is accessible
5. Add User Story 4 → Test independently → UX is polished
6. Add User Story 5 → Test independently → Styling is consistent
7. Add User Story 6 → Test independently → Performance is optimized
8. Add User Story 7 → Test independently → Test coverage is comprehensive
9. Polish phase → Final validation → Audit complete
10. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. One developer completes US2 (decomposition) — this blocks other stories
3. Once US2 is done:
   - Developer A: US1 (Reliable Loading) + US4 (UX Polish)
   - Developer B: US3 (Accessibility)
   - Developer C: US5 (Styling) + US6 (Performance)
4. After A, B, C complete: Developer D writes tests (US7)
5. Team runs Polish phase together

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable (after US2 decomposition)
- Tests are explicitly required by FR-034, FR-035, SC-008
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Dynamic `style={{ backgroundColor }}` for API-driven status colors is an acceptable exception per research.md RT-005
- All new components placed in existing `src/components/board/` directory per research.md RT-001
- No new dependencies required — all changes use existing dependency set per plan.md
