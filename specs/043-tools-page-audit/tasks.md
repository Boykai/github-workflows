# Tasks: Tools Page Audit

**Input**: Design documents from `/specs/043-tools-page-audit/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/component-contracts.md, quickstart.md

**Tests**: Tests are REQUIRED by the feature specification (FR-022: hook tests and component tests covering happy path, error, loading, and empty states). Test tasks are included in User Story 5.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify dev environment and establish baseline state for the audit

- [ ] T001 Install frontend dependencies via `cd solune/frontend && npm install`
- [ ] T002 [P] Run existing tests baseline via `cd solune/frontend && npx vitest run src/components/tools/ src/hooks/useTools.ts` and record current pass/fail state
- [ ] T003 [P] Run linter baseline via `cd solune/frontend && npx eslint src/pages/ToolsPage.tsx src/components/tools/ src/hooks/useTools.ts src/hooks/useAgentTools.ts src/hooks/useRepoMcpConfig.ts src/hooks/useMcpPresets.ts` and record current warnings

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Read shared component APIs and audit current state to inform all subsequent user stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Read and audit all tools page files — note line counts, identify loading/error/empty state gaps, accessibility gaps, and type safety issues across `solune/frontend/src/pages/ToolsPage.tsx`, `solune/frontend/src/components/tools/`, and `solune/frontend/src/hooks/useTools.ts`
- [ ] T005 [P] Read shared component APIs (CelestialLoader, ConfirmationDialog, ErrorBoundary, Tooltip, `isRateLimitApiError()`) in `solune/frontend/src/components/common/`, `solune/frontend/src/components/ui/`, and `solune/frontend/src/utils/rateLimit.ts` for integration reference

**Checkpoint**: Foundation ready — audit findings documented, shared component contracts understood. User story implementation can now begin.

---

## Phase 3: User Story 1 — Reliable Tool Management Without Errors (Priority: P1) 🎯 MVP

**Goal**: Every tool operation (upload, edit, sync, delete) provides clear feedback. Loading, error, and empty states are present for all data-dependent sections. Destructive actions require confirmation. Rate-limit errors are detected and communicated.

**Independent Test**: Perform each tool operation (upload, edit, sync, delete) under normal conditions and under failure conditions (network error, rate limit, server error) and verify appropriate feedback is shown in every case.

### Implementation for User Story 1

- [x] T006 [P] [US1] ✅ Add `<CelestialLoader size="md" />` loading state, error state with retry action button, and `isRateLimitApiError()` rate-limit detection to RepoConfigPanel in `solune/frontend/src/components/tools/RepoConfigPanel.tsx`
- [x] T007 [P] [US1] ✅ Add `<CelestialLoader size="md" />` loading state, error state with retry action button, `isRateLimitApiError()` rate-limit detection, and meaningful empty state with call-to-action to McpPresetsGallery in `solune/frontend/src/components/tools/McpPresetsGallery.tsx`
- [ ] T008 [US1] Add rate-limit error detection using `isRateLimitApiError()` from `@/utils/rateLimit` and format all mutation error messages to "Could not [action]. [Reason]. [Suggested next step]." pattern in `solune/frontend/src/hooks/useTools.ts`
- [ ] T009 [US1] Add loading state with `<CelestialLoader>`, error state with retry action and rate-limit message, and meaningful empty state with call-to-action for the tools list section in `solune/frontend/src/components/tools/ToolsPanel.tsx`
- [ ] T010 [US1] Ensure independent section loading — tools list, repo config, and presets each display their own loading/error states without one failed section blocking others in `solune/frontend/src/components/tools/ToolsPanel.tsx`
- [ ] T011 [US1] Replace inline delete confirmation with `<ConfirmationDialog>` component for tool deletion — display tool name and list of affected agents in the dialog in `solune/frontend/src/components/tools/ToolsPanel.tsx`
- [ ] T012 [P] [US1] Add `<ConfirmationDialog>` for repo server deletion with server name display and destructive variant in `solune/frontend/src/components/tools/RepoConfigPanel.tsx`
- [ ] T013 [US1] Add success toast or inline feedback for upload, edit, sync, and delete mutation completions in `solune/frontend/src/components/tools/ToolsPanel.tsx`

**Checkpoint**: At this point, User Story 1 should be fully functional — all sections have loading/error/empty states, destructive actions require confirmation, mutations show success/error feedback, and rate-limit errors are clearly communicated.

---

## Phase 4: User Story 2 — Accessible and Keyboard-Navigable Tools Page (Priority: P2)

**Goal**: The Tools page is fully navigable via keyboard, properly labeled for screen readers, and visually distinguishable for focus states. All interactive elements are reachable via Tab and activatable via Enter/Space.

**Independent Test**: Navigate the entire Tools page using only the keyboard (Tab, Enter, Space, Escape) and verify all interactive elements are reachable, activatable, and properly announced by a screen reader.

### Implementation for User Story 2

- [ ] T014 [P] [US2] Add `aria-label` attributes to unlabeled form fields (file upload input, paste/upload mode toggle, JSON textarea) in `solune/frontend/src/components/tools/UploadMcpModal.tsx`
- [ ] T015 [P] [US2] Add `aria-label` attributes to search input field and tool selection tiles in `solune/frontend/src/components/tools/ToolSelectorModal.tsx`
- [ ] T016 [P] [US2] Add text labels alongside color-coded sync status indicators so status is conveyed by icon + text, not color alone in `solune/frontend/src/components/tools/ToolCard.tsx`
- [x] T017 [P] [US2] ✅ Add `aria-label` to preset action buttons describing preset name and action in `solune/frontend/src/components/tools/McpPresetsGallery.tsx`
- [ ] T018 [US2] Add `aria-hidden="true"` to all decorative icons and `aria-label` to all meaningful icons across tools components in `solune/frontend/src/components/tools/`
- [ ] T019 [US2] Add visible focus indicators using `focus-visible:ring` or `celestial-focus` class to all interactive elements across tools components in `solune/frontend/src/components/tools/`
- [ ] T020 [US2] Verify and fix keyboard navigation — ensure logical Tab order, Enter/Space activation for all buttons, links, toggles, and custom controls across `solune/frontend/src/components/tools/`
- [ ] T021 [US2] Verify modal focus trapping in UploadMcpModal, EditRepoMcpModal, and ToolSelectorModal — ensure focus is trapped while open and returns to the trigger element on close in `solune/frontend/src/components/tools/UploadMcpModal.tsx`, `solune/frontend/src/components/tools/EditRepoMcpModal.tsx`, `solune/frontend/src/components/tools/ToolSelectorModal.tsx`

**Checkpoint**: At this point, User Story 2 should be fully functional — all elements are keyboard-accessible, screen reader labels are present, focus indicators are visible, and modals trap focus correctly.

---

## Phase 5: User Story 3 — Consistent and Polished User Experience (Priority: P2)

**Goal**: The Tools page uses consistent terminology, verb-based button labels, proper timestamp formatting, tooltip truncation, and full dark mode support matching the rest of the application.

**Independent Test**: Review all visible text, button labels, timestamps, and visual elements against the application's established conventions and verify consistency across light and dark themes.

### Implementation for User Story 3

- [ ] T022 [US3] Audit and update all button labels to verb-based naming (e.g., "Upload Config" not "New Config", "Sync Tool" not "Sync", "Delete Tool" not "Remove") across all tools components in `solune/frontend/src/components/tools/`
- [ ] T023 [P] [US3] Add `<Tooltip>` wrapper for truncated tool names, descriptions, and URLs — use `text-ellipsis` with `overflow-hidden` and show full text on hover in `solune/frontend/src/components/tools/ToolCard.tsx`
- [ ] T024 [P] [US3] Add `<Tooltip>` wrapper for truncated server names and configuration paths in `solune/frontend/src/components/tools/RepoConfigPanel.tsx`
- [ ] T025 [P] [US3] Format timestamps — display relative time ("2 hours ago") for events within 24 hours and absolute dates for older events for `synced_at` and `created_at` fields in `solune/frontend/src/components/tools/ToolCard.tsx`
- [ ] T026 [US3] Verify and fix dark mode compatibility — remove any hardcoded color values (e.g., `#fff`, `bg-white`); ensure all elements use Tailwind `dark:` variants or CSS theme variables across all tools components in `solune/frontend/src/components/tools/`
- [ ] T027 [US3] Fix silent catch blocks — add user-visible error feedback (toast or inline error) where operations currently fail silently in `solune/frontend/src/components/tools/ToolsPanel.tsx`

**Checkpoint**: At this point, User Story 3 should be fully functional — button labels are verb-based, long text is truncated with tooltips, timestamps are formatted consistently, dark mode is fully supported, and no operations fail silently.

---

## Phase 6: User Story 4 — Responsive and Performant Tools Page (Priority: P3)

**Goal**: The page layout adapts gracefully from 768px to 1920px viewports. Lists render efficiently with stable keys. Heavy computations are memoized. Large lists are paginated.

**Independent Test**: Resize the browser from 768px to 1920px width and verify layout adapts without breaking. Load the page with 50+ tools and verify performance remains acceptable.

### Implementation for User Story 4

- [ ] T028 [US4] Verify and fix responsive layout at 768px, 1024px, 1440px, and 1920px viewports — fix grid/flex breakpoints if broken, ensure no horizontal overflow or overlapping elements in `solune/frontend/src/components/tools/ToolsPanel.tsx` and `solune/frontend/src/components/tools/McpPresetsGallery.tsx`
- [ ] T029 [P] [US4] Replace array-index keys (`key={index}`) with stable keys (`key={item.id}` or content-derived key) in list rendering in `solune/frontend/src/components/tools/GitHubMcpConfigGenerator.tsx`
- [ ] T030 [P] [US4] Wrap heavy computations (tool filtering, sorting, grouping) in `useMemo` and memoize callbacks passed to memoized children with `useCallback` where needed in `solune/frontend/src/components/tools/ToolsPanel.tsx`
- [ ] T031 [US4] Add pagination or load-more pattern for tools list when item count exceeds 50 to prevent performance degradation in `solune/frontend/src/components/tools/ToolsPanel.tsx`

**Checkpoint**: At this point, User Story 4 should be fully functional — responsive layout works across all target viewports, list rendering uses stable keys, expensive computations are memoized, and large lists are handled efficiently.

---

## Phase 7: User Story 5 — Maintainable and Well-Tested Codebase (Priority: P3)

**Goal**: The code follows project conventions — modular components (≤250 lines for page file), extracted hooks, full type safety with zero `any` types, zero lint warnings, and meaningful test coverage for hooks and key interactive components.

**Independent Test**: Run `npx eslint` with zero warnings, `npx tsc --noEmit` with zero errors, and `npx vitest run` with all tests passing. Verify page file stays within line-count limit.

### Implementation for User Story 5

- [ ] T032 [US5] Verify ToolsPage.tsx is ≤250 lines (currently 84 lines — expected pass) in `solune/frontend/src/pages/ToolsPage.tsx`
- [ ] T033 [US5] Verify all complex state logic (>15 lines of useState/useEffect/useCallback) is extracted into dedicated custom hooks — extract any inline state logic if needed in `solune/frontend/src/hooks/useTools.ts` and component files
- [ ] T034 [US5] Remove all `any` types, unnecessary type assertions (`as`), dead code (unused imports, commented-out blocks), `console.log` statements, and magic strings across all tools files in `solune/frontend/src/components/tools/` and `solune/frontend/src/hooks/useTools.ts`
- [ ] T035 [US5] Ensure all project imports use `@/` alias paths (e.g., `@/components/...`, `@/hooks/...`) — replace any relative `../../` imports across tools files in `solune/frontend/src/components/tools/` and `solune/frontend/src/hooks/`
- [ ] T036 [P] [US5] Write hook tests for `useToolsList` covering happy path (tools loaded), error state (API failure), loading state, empty state (no tools), and rate-limit error detection in `solune/frontend/src/hooks/useTools.test.ts`
- [ ] T036a [P] [US5] Write hook tests for `useRepoMcpConfig` covering happy path (config loaded), error state (API failure), loading state, empty config, and CRUD operations in `solune/frontend/src/hooks/useRepoMcpConfig.test.ts`
- [ ] T036b [P] [US5] Write hook tests for `useMcpPresets` covering happy path (presets loaded), error state (API failure), loading state, and empty presets list in `solune/frontend/src/hooks/useMcpPresets.test.ts`
- [ ] T037 [P] [US5] Write component tests for ToolsPanel covering tool upload flow, tool edit flow, tool delete with confirmation dialog, and success/error feedback display in `solune/frontend/src/components/tools/ToolsPanel.test.tsx`
- [ ] T038 [P] [US5] Write component tests for ToolCard covering sync status display, action button interactions, and truncated text tooltip behavior in `solune/frontend/src/components/tools/ToolCard.test.tsx`
- [ ] T039 [P] [US5] Write edge case tests — rate-limit error rendering, null/missing data handling, extremely long strings (500+ chars), and rapid click protection — in `solune/frontend/src/components/tools/ToolsEnhancements.test.tsx`
- [ ] T040 [US5] Run linter via `cd solune/frontend && npx eslint src/pages/ToolsPage.tsx src/components/tools/ src/hooks/useTools.ts src/hooks/useAgentTools.ts src/hooks/useRepoMcpConfig.ts src/hooks/useMcpPresets.ts` and fix all warnings to reach zero violations

**Checkpoint**: At this point, User Story 5 should be complete — page file is within line limit, state is properly extracted into hooks, type safety is enforced, lint is clean, and comprehensive tests cover hooks, components, and edge cases.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements that span multiple user stories and full validation

- [ ] T041 Wrap ToolsPage content with `<ErrorBoundary>` for uncaught rendering errors in `solune/frontend/src/pages/ToolsPage.tsx`
- [ ] T042 Run full type checker via `cd solune/frontend && npm run type-check` and fix all type errors in tools-related files
- [ ] T043 Run full test suite via `cd solune/frontend && npx vitest run` and verify all tests pass (existing + new)
- [ ] T044 Final manual validation — verify light mode, dark mode, responsive viewports (768px, 1024px, 1440px, 1920px), and keyboard-only navigation across `solune/frontend/src/pages/ToolsPage.tsx` and `solune/frontend/src/components/tools/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational — P1 reliability is the highest priority
- **User Story 2 (Phase 4)**: Depends on Foundational — can run in parallel with US3
- **User Story 3 (Phase 5)**: Depends on Foundational — can run in parallel with US2
- **User Story 4 (Phase 6)**: Depends on US1 completion (loading states must exist before responsive fixes)
- **User Story 5 (Phase 7)**: Depends on US1–US4 (tests validate all prior changes; lint/type checks run against final code)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — Independent of other stories; a11y fixes work regardless of state management changes
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) — Independent of other stories; UX polish is additive
- **User Story 4 (P3)**: Best started after US1 (responsive fixes should account for loading/error/empty state layouts)
- **User Story 5 (P3)**: Best done last — tests should cover final code; lint/type checks validate all accumulated changes

### Within Each User Story

- Tasks targeting different files (marked [P]) can run in parallel
- Tasks targeting the same file should run sequentially
- Integration/verification tasks run after implementation tasks

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T002, T003)
- All Foundational tasks marked [P] can run in parallel (T004, T005)
- US1: RepoConfigPanel tasks (T006, T012) can run in parallel with McpPresetsGallery tasks (T007) and useTools tasks (T008)
- US2: All aria-label tasks (T014–T017) target different files and can run in parallel
- US3: Tooltip and timestamp tasks (T023–T025) target different files and can run in parallel
- US4: GitHubMcpConfigGenerator fix (T029) can run in parallel with ToolsPanel memoization (T030)
- US5: All test-writing tasks (T036–T039) target different files and can run in parallel
- US2 and US3 can proceed in parallel (different concerns, mostly different files)

---

## Parallel Example: User Story 1

```bash
# Launch parallel tasks targeting different files:
Task: T006 "Add loading/error/rate-limit states to RepoConfigPanel.tsx"  # RepoConfigPanel.tsx
Task: T007 "Add loading/error/rate-limit/empty states to McpPresetsGallery.tsx"  # McpPresetsGallery.tsx
Task: T008 "Add rate-limit detection and error formatting to useTools.ts"  # useTools.ts

# After T006–T008 complete, proceed with ToolsPanel tasks sequentially:
Task: T009 "Add loading/error/empty states for tools list in ToolsPanel.tsx"
Task: T010 "Ensure independent section loading in ToolsPanel.tsx"
Task: T011 "Replace inline delete with ConfirmationDialog in ToolsPanel.tsx"
Task: T013 "Add success feedback for mutations in ToolsPanel.tsx"

# T012 (RepoConfigPanel ConfirmationDialog) can run in parallel with T009–T013:
Task: T012 "Add ConfirmationDialog for repo server deletion in RepoConfigPanel.tsx"
```

## Parallel Example: User Story 5 (Tests)

```bash
# All test-writing tasks target different files and can run in parallel:
Task: T036 "Write hook tests for useToolsList in useTools.test.ts"
Task: T037 "Write component tests for ToolsPanel in ToolsPanel.test.tsx"
Task: T038 "Write component tests for ToolCard in ToolCard.test.tsx"
Task: T039 "Write edge case tests in ToolsEnhancements.test.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (audit + shared component reference)
3. Complete Phase 3: User Story 1 — Reliable Tool Management
4. **STOP and VALIDATE**: Test all tool operations under normal and failure conditions
5. Deploy/demo if ready — users get loading states, error handling, confirmations, and success feedback

### Incremental Delivery

1. Complete Setup + Foundational → Baseline established
2. Add User Story 1 (P1) → Test independently → Deploy/Demo (**MVP!**)
3. Add User Story 2 (P2) + User Story 3 (P2) → Test independently → Deploy/Demo (a11y + UX polish)
4. Add User Story 4 (P3) → Test independently → Deploy/Demo (responsive + performance)
5. Add User Story 5 (P3) → Test independently → Deploy/Demo (code quality + test coverage)
6. Complete Polish phase → Final validation → Ship

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Developer A: User Story 1 (P1) — blocking reliability fixes
3. Once US1 is done:
   - Developer A: User Story 4 (P3) — responsive/performance
   - Developer B: User Story 2 (P2) — accessibility
   - Developer C: User Story 3 (P2) — UX polish
4. Developer D (or any): User Story 5 (P3) — tests and code quality (after all others complete)
5. Final validation as a team

---

## Notes

- [P] tasks = different files, no dependencies — safe to run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- FR-022 mandates tests — hook tests (useToolsList) and component tests (ToolsPanel, ToolCard) with edge cases
- Shared components (CelestialLoader, ConfirmationDialog, ErrorBoundary, Tooltip) are read-only references — use as-is, do not modify
- All file paths are relative to `solune/frontend/` directory
- Verification commands are documented in `specs/043-tools-page-audit/quickstart.md`
- Commit after each task or logical group
- Stop at any checkpoint to validate the story independently
