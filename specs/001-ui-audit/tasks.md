# Tasks: UI Audit

**Input**: Design documents from `/specs/001-ui-audit/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests are explicitly requested in the specification (FR-040, FR-041, FR-042, User Story 6). Test tasks are included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. Each page is an independent audit unit within its story phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/frontend/src/`
- Pages: `solune/frontend/src/pages/`
- Feature components: `solune/frontend/src/components/[feature]/`
- Hooks: `solune/frontend/src/hooks/`
- Services: `solune/frontend/src/services/api.ts`
- Types: `solune/frontend/src/types/`
- UI primitives: `solune/frontend/src/components/ui/`
- Common components: `solune/frontend/src/components/common/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish audit framework and baseline assessment

- [ ] T001 Create audit scoring template with all 10 checklist categories and ~60 individual items per page
- [ ] T002 [P] Run `npx eslint` across all 12 page files and their feature component directories to establish baseline lint status
- [ ] T003 [P] Run `npx tsc --noEmit` to establish baseline type-check status
- [ ] T004 [P] Run `npx vitest run` to establish baseline test status and coverage

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Audit discovery pass for all 12 pages — score every checklist item before any remediation begins

**⚠️ CRITICAL**: No remediation work can begin until discovery is complete for the target page

- [ ] T005 [P] Audit discovery: `solune/frontend/src/pages/ProjectsPage.tsx` and `solune/frontend/src/components/board/` — score all checklist items (pass/fail/N/A), note line count (503), identify sub-components, hooks, API calls
- [ ] T006 [P] Audit discovery: `solune/frontend/src/pages/AppsPage.tsx` and `solune/frontend/src/components/apps/` — score all checklist items, note line count (325)
- [ ] T007 [P] Audit discovery: `solune/frontend/src/pages/AgentsPipelinePage.tsx` and `solune/frontend/src/components/pipeline/` — score all checklist items, note line count (313)
- [ ] T008 [P] Audit discovery: `solune/frontend/src/pages/ActivityPage.tsx` and `solune/frontend/src/components/activity/` — score all checklist items, note line count (251)
- [ ] T009 [P] Audit discovery: `solune/frontend/src/pages/AgentsPage.tsx` and `solune/frontend/src/components/agents/` — score all checklist items, note line count (238)
- [ ] T010 [P] Audit discovery: `solune/frontend/src/pages/HelpPage.tsx` and `solune/frontend/src/components/help/` — score all checklist items, note line count (221)
- [ ] T011 [P] Audit discovery: `solune/frontend/src/pages/ChoresPage.tsx` and `solune/frontend/src/components/chores/` — score all checklist items, note line count (181)
- [ ] T012 [P] Audit discovery: `solune/frontend/src/pages/AppPage.tsx` and `solune/frontend/src/components/apps/` — score all checklist items, note line count (141)
- [ ] T013 [P] Audit discovery: `solune/frontend/src/pages/LoginPage.tsx` and `solune/frontend/src/components/auth/` — score all checklist items, note line count (119)
- [ ] T014 [P] Audit discovery: `solune/frontend/src/pages/SettingsPage.tsx` and `solune/frontend/src/components/settings/` — score all checklist items, note line count (107)
- [ ] T015 [P] Audit discovery: `solune/frontend/src/pages/ToolsPage.tsx` and `solune/frontend/src/components/tools/` — score all checklist items, note line count (104)
- [ ] T016 [P] Audit discovery: `solune/frontend/src/pages/NotFoundPage.tsx` — score all checklist items, note line count (29)

**Checkpoint**: All 12 pages have discovery scores. Remediation can begin per-page in priority order.

---

## Phase 3: User Story 1 — Page Architecture Meets Quality Standards (Priority: P1) 🎯 MVP

**Goal**: Every page follows single-responsibility principles, uses shared primitives, and keeps business logic out of JSX

**Independent Test**: Pick any single page, measure line count, verify sub-components in correct feature folder, confirm no prop drilling >2 levels, verify shared primitives from ui/ and common/

### Implementation for User Story 1

- [ ] T017 [US1] Extract `solune/frontend/src/pages/ProjectsPage.tsx` (503 lines) into sub-components in `solune/frontend/src/components/board/` — target ≤250 lines in page file
- [ ] T018 [US1] Extract `solune/frontend/src/pages/AppsPage.tsx` (325 lines) into sub-components in `solune/frontend/src/components/apps/` — target ≤250 lines
- [ ] T019 [US1] Extract `solune/frontend/src/pages/AgentsPipelinePage.tsx` (313 lines) into sub-components in `solune/frontend/src/components/pipeline/` — target ≤250 lines
- [ ] T020 [US1] Extract `solune/frontend/src/pages/ActivityPage.tsx` (251 lines) into sub-components in `solune/frontend/src/components/activity/` — target ≤250 lines
- [ ] T021 [P] [US1] Audit and fix prop drilling violations across all 12 pages — replace with composition, context, or hook extraction where drilling exceeds 2 levels
- [ ] T022 [P] [US1] Audit and fix shared primitive usage — replace any reimplemented Button, Card, Input, Tooltip, ConfirmationDialog, HoverCard with imports from `solune/frontend/src/components/ui/`
- [ ] T023 [P] [US1] Audit and fix shared common component usage — replace any reimplemented CelestialLoader, ErrorBoundary, ProjectSelectionEmptyState, ThemedAgentIcon with imports from `solune/frontend/src/components/common/`
- [ ] T024 [P] [US1] Extract complex state logic (>15 lines) from page files into dedicated hooks in `solune/frontend/src/hooks/`
- [ ] T025 [P] [US1] Move business logic out of JSX render trees into hooks or helper functions across all pages

**Checkpoint**: All pages ≤250 lines, shared primitives used, business logic extracted. US1 independently verifiable.

---

## Phase 4: User Story 2 — Reliable Loading, Error, and Empty States (Priority: P1) 🎯 MVP

**Goal**: Every page shows clear feedback during loading, helpful errors with retry, and meaningful empty states

**Independent Test**: For any page, simulate loading, error, and empty-data states and verify appropriate UI

### Implementation for User Story 2

- [ ] T026 [P] [US2] Add/verify loading state (CelestialLoader or skeleton) for all data-fetching pages: ProjectsPage, AppsPage, AgentsPipelinePage, ActivityPage, AgentsPage, ChoresPage, AppPage, ToolsPage, SettingsPage
- [ ] T027 [P] [US2] Add/verify error state with user-friendly message, retry action, and rate-limit detection (`isRateLimitApiError()`) for all data-fetching pages
- [ ] T028 [P] [US2] Add/verify empty state with meaningful guidance for all pages displaying collections: ProjectsPage, AppsPage, AgentsPage, ChoresPage, ActivityPage, ToolsPage
- [ ] T029 [P] [US2] Add/verify partial loading for pages with multiple data sources — ensure one failed section does not block the rest: ProjectsPage, AgentsPipelinePage, AppsPage
- [ ] T030 [P] [US2] Verify all pages are wrapped in ErrorBoundary (at route level in App.tsx or within the page)

**Checkpoint**: All data-fetching pages have loading, error, empty, and partial-failure states. US2 independently verifiable.

---

## Phase 5: User Story 3 — Accessible and Keyboard-Navigable Interface (Priority: P2)

**Goal**: Every interactive element is keyboard-accessible and properly labeled for screen readers

**Independent Test**: For any page, tab through all elements, confirm ARIA attributes, verify focus management in dialogs

### Implementation for User Story 3

- [ ] T031 [P] [US3] Audit and fix keyboard navigation across all 12 pages — ensure all interactive elements reachable via Tab, activatable via Enter/Space
- [ ] T032 [P] [US3] Audit and fix focus management in all dialogs and modals — ensure focus trap and focus return to trigger on dismissal
- [ ] T033 [P] [US3] Add missing ARIA attributes (role, aria-label, aria-expanded, aria-selected) to all custom controls across all pages
- [ ] T034 [P] [US3] Add missing labels (visible or aria-label) to all form inputs across all pages
- [ ] T035 [P] [US3] Verify WCAG AA color contrast (4.5:1) across all pages and ensure status indicators use icon + text, not color alone
- [ ] T036 [P] [US3] Add visible focus indicators (celestial-focus class or focus-visible: ring) to all interactive elements
- [ ] T037 [P] [US3] Add aria-hidden="true" to decorative icons and aria-label to meaningful icons across all pages

**Checkpoint**: All pages keyboard-navigable and screen-reader accessible. US3 independently verifiable.

---

## Phase 6: User Story 4 — Polished, Consistent User Experience (Priority: P2)

**Goal**: Consistent terminology, helpful feedback, user-friendly errors, and properly formatted content

**Independent Test**: For any page, verify final copy, verb-based buttons, destructive action confirmation, mutation feedback, truncated text with tooltips

### Implementation for User Story 4

- [ ] T038 [P] [US4] Audit and fix all user-visible strings — remove TODO markers, placeholder text, lorem ipsum across all pages
- [ ] T039 [P] [US4] Audit and fix button labels — ensure all action buttons use verb-based phrasing across all pages
- [ ] T040 [P] [US4] Add ConfirmationDialog to all destructive actions (delete, remove, stop) across all pages
- [ ] T041 [P] [US4] Add success feedback (toast, inline message, or status change) to all mutations across all pages
- [ ] T042 [P] [US4] Fix error messages to follow pattern: "Could not [action]. [Reason]. [Suggested next step]." — no raw error codes across all pages
- [ ] T043 [P] [US4] Add text truncation with ellipsis and Tooltip for long content (names, descriptions, URLs) across all pages
- [ ] T044 [P] [US4] Fix timestamp formatting — relative time for recent, absolute for older — using `solune/frontend/src/lib/time-utils.ts` consistently

**Checkpoint**: All pages have polished, consistent UX. US4 independently verifiable.

---

## Phase 7: User Story 5 — Type-Safe and Performant Codebase (Priority: P3)

**Goal**: Full type safety with no `any` types, and rendering performance avoids unnecessary re-renders

**Independent Test**: Run type checker with zero errors, verify no `any` types, confirm stable list keys, validate memoized computations

### Implementation for User Story 5

- [ ] T045 [P] [US5] Audit and fix all `any` type annotations across all page files and their components — replace with explicit types
- [ ] T046 [P] [US5] Audit and minimize type assertions (`as`) — replace with type guards or discriminated unions, document unavoidable assertions
- [ ] T047 [P] [US5] Fix list rendering to use stable unique keys (`key={item.id}`) — never array index — across all pages
- [ ] T048 [P] [US5] Wrap expensive synchronous computations (sorting, filtering, grouping) in `useMemo` across all pages
- [ ] T049 [P] [US5] Add `React.memo()` to expensive components with stable props; add virtualization or pagination for lists >50 items

**Checkpoint**: Zero type errors, no `any` types, stable keys, memoized computations. US5 independently verifiable.

---

## Phase 8: User Story 6 — Comprehensive Test Coverage (Priority: P3)

**Goal**: Meaningful test coverage for hooks, components, and edge cases

**Independent Test**: Run test suite and confirm hook tests, component interaction tests, and edge-case tests exist and pass

### Tests for User Story 6

- [ ] T050 [P] [US6] Write/update hook tests for all page-specific hooks — cover happy path, error, loading, empty states using `renderHook()` with mocked API
- [ ] T051 [P] [US6] Write/update component tests for key interactive components — cover user interactions (clicks, form submissions, dialog confirmations) using `vi.mock('@/services/api', ...)`
- [ ] T052 [P] [US6] Add edge-case tests: empty collections, error responses, rate-limit errors, long strings, null/missing data
- [ ] T053 [US6] Verify all tests use assertion-based validation — no snapshot tests — and follow codebase conventions (`waitFor`, `createWrapper()`)

**Checkpoint**: All hooks and key components have tests. Edge cases covered. US6 independently verifiable.

---

## Phase 9: User Story 7 — Clean, Consistent Code (Priority: P3)

**Goal**: Consistent file naming, import aliasing, and code hygiene with no dead code

**Independent Test**: Run linter with zero warnings, verify alias imports, no dead code, no console.log, no magic strings

### Implementation for User Story 7

- [ ] T054 [P] [US7] Remove dead code (unused imports, commented-out blocks, unreachable branches) across all page files and feature components
- [ ] T055 [P] [US7] Remove all `console.log` statements across all page files and feature components
- [ ] T056 [P] [US7] Fix imports to use `@/` path alias — replace all relative multi-level imports across all page files
- [ ] T057 [P] [US7] Extract magic strings (status values, route paths, query keys) into named constants
- [ ] T058 [US7] Run `npx eslint` across all audited files and fix all remaining warnings to reach zero

**Checkpoint**: Zero linter warnings, no dead code, consistent imports. US7 independently verifiable.

---

## Phase 10: Styling & Layout Compliance

**Purpose**: Cross-cutting styling concerns that affect multiple user stories

- [ ] T059 [P] Remove inline `style={}` attributes — replace with Tailwind utility classes using `cn()` from `solune/frontend/src/lib/utils.ts`
- [ ] T060 [P] Verify responsive design at 768px, 1024px, 1440px, and 1920px viewports across all pages
- [ ] T061 [P] Verify dark mode support — no hardcoded colors (`#fff`, `bg-white`), use `dark:` variants or CSS variables
- [ ] T062 [P] Fix arbitrary spacing values — use Tailwind spacing scale (`gap-4`, `p-6`) instead of custom values like `p-[13px]`

---

## Phase 11: Final Validation

**Purpose**: End-to-end validation across all pages

- [ ] T063 Run `npx eslint solune/frontend/src/pages/ solune/frontend/src/components/` — 0 warnings
- [ ] T064 Run `npx tsc --noEmit` — 0 type errors
- [ ] T065 Run `npx vitest run` — all tests pass
- [ ] T066 Manual browser verification: light mode, dark mode, 768px–1920px viewports
- [ ] T067 Keyboard-only navigation test: Tab through all interactive elements, Enter/Space activation
- [ ] T068 Screen reader audit: verify labels and ARIA attributes read correctly

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Discovery (Phase 2)**: Depends on Setup — BLOCKS all remediation
- **User Stories (Phases 3–9)**: All depend on Discovery completion for target pages
  - P1 stories (US1, US2) should complete before P2 stories (US3, US4)
  - P2 stories before P3 stories (US5, US6, US7)
  - Within the same priority, stories can proceed in parallel
- **Styling (Phase 10)**: Can run in parallel with later user stories
- **Validation (Phase 11)**: Depends on all remediation phases being complete

### User Story Dependencies

- **US1 (Architecture, P1)**: Can start after Discovery — no dependencies on other stories
- **US2 (States, P1)**: Can start after Discovery — may integrate with US1 structural changes
- **US3 (Accessibility, P2)**: Can start after Discovery — independent of US1/US2
- **US4 (UX Polish, P2)**: Can start after Discovery — may benefit from US2 error state work
- **US5 (Type Safety, P3)**: Can start after Discovery — independent
- **US6 (Testing, P3)**: Should start after US1–US5 remediation is stable to avoid test churn
- **US7 (Hygiene, P3)**: Can start after Discovery — independent

### Parallel Opportunities

- All Discovery tasks (T005–T016) can run in parallel
- Within each user story, tasks marked [P] can run in parallel
- US1 and US2 can proceed in parallel (both P1)
- US3 and US4 can proceed in parallel (both P2)
- US5, US6, US7 can proceed in parallel (all P3), though US6 benefits from waiting

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Pages are audited independently — each page is a self-contained audit unit
- "Not applicable" is a valid result for checklist items that don't apply to a given page
