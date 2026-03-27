# Tasks: UI Audit

**Input**: Design documents from `/specs/001-ui-audit/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Test tasks are included as required by User Story 6 (Comprehensive Test Coverage, P3).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. Within each user story, tasks are further organized per page since each page is an independent audit unit.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/frontend/src/` at repository root
- All paths below are relative to repository root unless stated otherwise

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the audit framework, capture baseline metrics, and prepare tooling for systematic page-by-page audit.

- [ ] T001 Run baseline lint across all page files: `npx eslint src/pages/*.tsx` from `solune/frontend/` and record current warning count
- [ ] T002 Run baseline type-check: `npx tsc --noEmit` from `solune/frontend/` and record current error count
- [ ] T003 Run baseline test suite: `npx vitest run` from `solune/frontend/` and record current pass/fail counts
- [ ] T004 [P] Inventory each page's line count, hooks used, API calls, and sub-components — produce findings table per plan.md page inventory

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Ensure shared infrastructure components referenced by the audit checklist exist and are correct before auditing individual pages.

**⚠️ CRITICAL**: No page-level audit work can begin until this phase is complete.

- [ ] T005 Verify `solune/frontend/src/components/common/CelestialLoader.tsx` supports `size` prop variants (sm, md, lg) needed by loading-state audit
- [ ] T006 [P] Verify `solune/frontend/src/components/common/ErrorBoundary.tsx` is available and correctly wraps child components
- [ ] T007 [P] Verify `solune/frontend/src/components/common/EmptyState.tsx` and `solune/frontend/src/components/common/ProjectSelectionEmptyState.tsx` accept customizable messages and actions
- [ ] T008 [P] Verify `solune/frontend/src/components/ui/confirmation-dialog.tsx` exists and is importable for destructive-action confirmations
- [ ] T009 [P] Verify `solune/frontend/src/components/ui/tooltip.tsx` exists and supports wrapping truncated text
- [ ] T010 [P] Verify `solune/frontend/src/components/ui/skeleton.tsx` exists for skeleton loading states
- [ ] T011 Verify `solune/frontend/src/services/api.ts` exports an `isRateLimitApiError()` utility or equivalent for rate-limit detection (FR-012)

**Checkpoint**: Foundation ready — page-level audit work can now begin in parallel.

---

## Phase 3: User Story 1 — Page Architecture Meets Quality Standards (Priority: P1) 🎯 MVP

**Goal**: Every page follows single-responsibility principles, uses shared UI primitives, keeps business logic out of the render tree, and has properly extracted hooks.

**Independent Test**: For any single page, measure its line count (≤250), verify sub-components live in the correct feature folder, confirm no prop drilling beyond 2 levels, and verify all shared primitives come from shared UI/common libraries.

### Implementation for User Story 1

**ProjectsPage (503 lines — OVER LIMIT)**:
- [ ] T012 [US1] Audit `solune/frontend/src/pages/ProjectsPage.tsx` — identify inline sub-components, business logic in JSX, and prop-drilling paths
- [ ] T013 [US1] Extract sub-components from ProjectsPage into `solune/frontend/src/components/board/` to bring page under 250 lines (FR-001)
- [ ] T014 [US1] Extract complex state logic (>15 lines) from ProjectsPage into hooks in `solune/frontend/src/hooks/` (FR-005)
- [ ] T015 [US1] Replace any reimplemented UI primitives in ProjectsPage with shared components from `solune/frontend/src/components/ui/` (FR-002)
- [ ] T016 [US1] Remove business logic from ProjectsPage render tree in `solune/frontend/src/pages/ProjectsPage.tsx` — move to hooks or helper functions (FR-006)

**AppsPage (325 lines — OVER LIMIT)**:
- [ ] T017 [P] [US1] Audit `solune/frontend/src/pages/AppsPage.tsx` — identify inline sub-components, business logic in JSX, and prop-drilling paths
- [ ] T018 [US1] Extract sub-components from AppsPage into `solune/frontend/src/components/apps/` to bring page under 250 lines (FR-001)
- [ ] T019 [US1] Extract complex state logic from AppsPage into hooks in `solune/frontend/src/hooks/` (FR-005)
- [ ] T020 [US1] Replace any reimplemented UI primitives in AppsPage with shared components from `solune/frontend/src/components/ui/` (FR-002)
- [ ] T021 [US1] Remove business logic from AppsPage render tree in `solune/frontend/src/pages/AppsPage.tsx` — move to hooks or helper functions (FR-006)

**AgentsPipelinePage (313 lines — OVER LIMIT)**:
- [ ] T022 [P] [US1] Audit `solune/frontend/src/pages/AgentsPipelinePage.tsx` — identify inline sub-components, business logic in JSX, and prop-drilling paths
- [ ] T023 [US1] Extract sub-components from AgentsPipelinePage into `solune/frontend/src/components/pipeline/` to bring page under 250 lines (FR-001)
- [ ] T024 [US1] Extract complex state logic from AgentsPipelinePage into hooks in `solune/frontend/src/hooks/` (FR-005)
- [ ] T025 [US1] Replace any reimplemented UI primitives in AgentsPipelinePage with shared components from `solune/frontend/src/components/ui/` (FR-002)
- [ ] T026 [US1] Remove business logic from AgentsPipelinePage render tree in `solune/frontend/src/pages/AgentsPipelinePage.tsx` — move to hooks or helper functions (FR-006)

**ActivityPage (251 lines — OVER LIMIT, borderline)**:
- [ ] T027 [P] [US1] Audit `solune/frontend/src/pages/ActivityPage.tsx` — identify inline sub-components, business logic in JSX, and prop-drilling paths
- [ ] T028 [US1] Extract sub-components from ActivityPage into `solune/frontend/src/components/activity/` to bring page to 250 lines or under (FR-001)
- [ ] T029 [US1] Extract complex state logic from ActivityPage into hooks in `solune/frontend/src/hooks/` (FR-005)

**Remaining pages (under 250 lines — audit only)**:
- [ ] T030 [P] [US1] Audit `solune/frontend/src/pages/AgentsPage.tsx` (238 lines) — verify architecture, shared primitives, hook extraction, no business logic in JSX
- [ ] T031 [P] [US1] Audit `solune/frontend/src/pages/HelpPage.tsx` (221 lines) — verify architecture, shared primitives, hook extraction, no business logic in JSX
- [ ] T032 [P] [US1] Audit `solune/frontend/src/pages/ChoresPage.tsx` (181 lines) — verify architecture, shared primitives, hook extraction, no business logic in JSX
- [ ] T033 [P] [US1] Audit `solune/frontend/src/pages/AppPage.tsx` (141 lines) — verify architecture, shared primitives, hook extraction, no business logic in JSX
- [ ] T034 [P] [US1] Audit `solune/frontend/src/pages/LoginPage.tsx` (119 lines) — verify architecture, shared primitives, hook extraction, no business logic in JSX
- [ ] T035 [P] [US1] Audit `solune/frontend/src/pages/SettingsPage.tsx` (107 lines) — verify architecture, shared primitives, hook extraction, no business logic in JSX
- [ ] T036 [P] [US1] Audit `solune/frontend/src/pages/ToolsPage.tsx` (104 lines) — verify architecture, shared primitives, hook extraction, no business logic in JSX
- [ ] T037 [P] [US1] Audit `solune/frontend/src/pages/NotFoundPage.tsx` (29 lines) — verify architecture (mark most items N/A for this minimal page)
- [ ] T038 [US1] Remediate all US1 findings across remaining pages — fix any shared-primitive, prop-drilling, or business-logic-in-JSX violations found in T030–T037

**Checkpoint**: All 12 pages are ≤250 lines, use shared primitives, have extracted hooks, and keep business logic out of the render tree.

---

## Phase 4: User Story 2 — Reliable Loading, Error, and Empty States (Priority: P1)

**Goal**: Every page that fetches data shows clear loading feedback, helpful error messages with retry, rate-limit detection, and meaningful empty states. No blank screens ever.

**Independent Test**: For any single page, simulate loading, error, empty-data, and rate-limit states — verify correct UI in each case.

### Implementation for User Story 2

**Data-fetching pages (10 pages — excludes HelpPage and NotFoundPage)**:

- [ ] T039 [P] [US2] Audit loading, error, and empty states in `solune/frontend/src/pages/ProjectsPage.tsx` — check for CelestialLoader/skeleton during loading, user-friendly error with retry, rate-limit detection, meaningful empty state, ErrorBoundary wrapping, independent section states (FR-010–FR-015)
- [ ] T040 [US2] Remediate ProjectsPage loading/error/empty state findings — add missing CelestialLoader, error message with retry, `isRateLimitApiError()` check, and empty state component in `solune/frontend/src/pages/ProjectsPage.tsx`

- [ ] T041 [P] [US2] Audit loading, error, and empty states in `solune/frontend/src/pages/AppsPage.tsx` (FR-010–FR-015)
- [ ] T042 [US2] Remediate AppsPage loading/error/empty state findings in `solune/frontend/src/pages/AppsPage.tsx`

- [ ] T043 [P] [US2] Audit loading, error, and empty states in `solune/frontend/src/pages/AgentsPipelinePage.tsx` (FR-010–FR-015)
- [ ] T044 [US2] Remediate AgentsPipelinePage loading/error/empty state findings in `solune/frontend/src/pages/AgentsPipelinePage.tsx`

- [ ] T045 [P] [US2] Audit loading, error, and empty states in `solune/frontend/src/pages/ActivityPage.tsx` (FR-010–FR-015)
- [ ] T046 [US2] Remediate ActivityPage loading/error/empty state findings in `solune/frontend/src/pages/ActivityPage.tsx`

- [ ] T047 [P] [US2] Audit loading, error, and empty states in `solune/frontend/src/pages/AgentsPage.tsx` (FR-010–FR-015)
- [ ] T048 [US2] Remediate AgentsPage loading/error/empty state findings in `solune/frontend/src/pages/AgentsPage.tsx`

- [ ] T049 [P] [US2] Audit loading, error, and empty states in `solune/frontend/src/pages/ChoresPage.tsx` (FR-010–FR-015)
- [ ] T050 [US2] Remediate ChoresPage loading/error/empty state findings in `solune/frontend/src/pages/ChoresPage.tsx`

- [ ] T051 [P] [US2] Audit loading, error, and empty states in `solune/frontend/src/pages/AppPage.tsx` (FR-010–FR-015)
- [ ] T052 [US2] Remediate AppPage loading/error/empty state findings in `solune/frontend/src/pages/AppPage.tsx`

- [ ] T053 [P] [US2] Audit loading, error, and empty states in `solune/frontend/src/pages/LoginPage.tsx` (FR-010–FR-015, minimal — may be N/A for empty state)
- [ ] T054 [US2] Remediate LoginPage loading/error/empty state findings in `solune/frontend/src/pages/LoginPage.tsx`

- [ ] T055 [P] [US2] Audit loading, error, and empty states in `solune/frontend/src/pages/SettingsPage.tsx` (FR-010–FR-015)
- [ ] T056 [US2] Remediate SettingsPage loading/error/empty state findings in `solune/frontend/src/pages/SettingsPage.tsx`

- [ ] T057 [P] [US2] Audit loading, error, and empty states in `solune/frontend/src/pages/ToolsPage.tsx` (FR-010–FR-015)
- [ ] T058 [US2] Remediate ToolsPage loading/error/empty state findings in `solune/frontend/src/pages/ToolsPage.tsx`

- [ ] T059 [US2] Verify all `useMutation` calls across all pages have `onError` that surfaces user-visible feedback (FR-009) — check `solune/frontend/src/hooks/` for mutation hooks
- [ ] T060 [US2] Verify all pages with data fetching use React Query (`useQuery`/`useMutation`) — no raw `useEffect` + `fetch` patterns (FR-007)
- [ ] T061 [US2] Verify query key conventions follow `[feature].all / .list(id) / .detail(id)` pattern across all hooks in `solune/frontend/src/hooks/` (FR-008)

**Checkpoint**: All data-fetching pages display loading indicator, error with retry (including rate-limit), and meaningful empty state. No blank screens.

---

## Phase 5: User Story 3 — Accessible and Keyboard-Navigable Interface (Priority: P2)

**Goal**: Every interactive element on every page is keyboard-accessible, properly ARIA-labeled, has visible focus indicators, and dialogs trap focus correctly.

**Independent Test**: For any single page, tab through every element, verify Enter/Space activation, check ARIA attributes on custom controls, and test focus management in dialogs.

### Implementation for User Story 3

- [ ] T062 [P] [US3] Audit keyboard accessibility and ARIA attributes in `solune/frontend/src/pages/ProjectsPage.tsx` and `solune/frontend/src/components/board/` — Tab order, Enter/Space, ARIA roles/labels, focus-visible styles, screen reader text (FR-018–FR-024)
- [ ] T063 [US3] Remediate ProjectsPage accessibility findings — add missing ARIA attributes, keyboard handlers, focus-visible styles, and screen reader labels

- [ ] T064 [P] [US3] Audit keyboard accessibility and ARIA attributes in `solune/frontend/src/pages/AppsPage.tsx` and `solune/frontend/src/components/apps/` (FR-018–FR-024)
- [ ] T065 [US3] Remediate AppsPage accessibility findings — add missing ARIA attributes, keyboard handlers, focus-visible styles

- [ ] T066 [P] [US3] Audit keyboard accessibility and ARIA attributes in `solune/frontend/src/pages/AgentsPipelinePage.tsx` and `solune/frontend/src/components/pipeline/` (FR-018–FR-024)
- [ ] T067 [US3] Remediate AgentsPipelinePage accessibility findings — add missing ARIA attributes, keyboard handlers, focus-visible styles

- [ ] T068 [P] [US3] Audit keyboard accessibility and ARIA attributes in `solune/frontend/src/pages/ActivityPage.tsx` and `solune/frontend/src/components/activity/` (FR-018–FR-024)
- [ ] T069 [US3] Remediate ActivityPage accessibility findings

- [ ] T070 [P] [US3] Audit keyboard accessibility and ARIA attributes in `solune/frontend/src/pages/AgentsPage.tsx` and `solune/frontend/src/components/agents/` (FR-018–FR-024)
- [ ] T071 [US3] Remediate AgentsPage accessibility findings

- [ ] T072 [P] [US3] Audit keyboard accessibility and ARIA attributes in `solune/frontend/src/pages/HelpPage.tsx` and `solune/frontend/src/components/help/` (FR-018–FR-024)
- [ ] T073 [US3] Remediate HelpPage accessibility findings

- [ ] T074 [P] [US3] Audit keyboard accessibility and ARIA attributes in `solune/frontend/src/pages/ChoresPage.tsx` and `solune/frontend/src/components/chores/` (FR-018–FR-024)
- [ ] T075 [US3] Remediate ChoresPage accessibility findings

- [ ] T076 [P] [US3] Audit keyboard accessibility and ARIA attributes in `solune/frontend/src/pages/AppPage.tsx` (FR-018–FR-024)
- [ ] T077 [US3] Remediate AppPage accessibility findings

- [ ] T078 [P] [US3] Audit keyboard accessibility and ARIA attributes in `solune/frontend/src/pages/LoginPage.tsx` and `solune/frontend/src/components/auth/` (FR-018–FR-024)
- [ ] T079 [US3] Remediate LoginPage accessibility findings — ensure form fields have labels, focus management on login flow

- [ ] T080 [P] [US3] Audit keyboard accessibility and ARIA attributes in `solune/frontend/src/pages/SettingsPage.tsx` and `solune/frontend/src/components/settings/` (FR-018–FR-024)
- [ ] T081 [US3] Remediate SettingsPage accessibility findings

- [ ] T082 [P] [US3] Audit keyboard accessibility and ARIA attributes in `solune/frontend/src/pages/ToolsPage.tsx` and `solune/frontend/src/components/tools/` (FR-018–FR-024)
- [ ] T083 [US3] Remediate ToolsPage accessibility findings

- [ ] T084 [US3] Verify all dialogs/modals across all pages trap focus and return focus to trigger on dismissal (FR-019) — check ConfirmationDialog usage in all feature components
- [ ] T085 [US3] Verify all decorative icons have `aria-hidden="true"` and meaningful icons have `aria-label` across all pages (FR-024)

**Checkpoint**: All 12 pages are fully keyboard-navigable with correct ARIA attributes, focus indicators, and screen-reader support.

---

## Phase 6: User Story 4 — Polished, Consistent User Experience (Priority: P2)

**Goal**: Consistent terminology, verb-based button labels, confirmation on destructive actions, success/failure feedback on all mutations, user-friendly error messages, proper truncation, and consistent timestamp formatting.

**Independent Test**: For any page, verify all strings are final copy, buttons use verbs, destructive actions require confirmation, mutations provide feedback, and long text truncates with tooltip.

### Implementation for User Story 4

- [ ] T086 [P] [US4] Audit text, copy, and UX polish in `solune/frontend/src/pages/ProjectsPage.tsx` and `solune/frontend/src/components/board/` — placeholder text, terminology, button labels, confirmation dialogs, success/error feedback, truncation, timestamps (FR-025–FR-032)
- [ ] T087 [US4] Remediate ProjectsPage UX findings — fix copy, add missing ConfirmationDialog, add success toasts, fix error messages, add Tooltip on truncated text

- [ ] T088 [P] [US4] Audit text, copy, and UX polish in `solune/frontend/src/pages/AppsPage.tsx` and `solune/frontend/src/components/apps/` (FR-025–FR-032)
- [ ] T089 [US4] Remediate AppsPage UX findings

- [ ] T090 [P] [US4] Audit text, copy, and UX polish in `solune/frontend/src/pages/AgentsPipelinePage.tsx` and `solune/frontend/src/components/pipeline/` (FR-025–FR-032)
- [ ] T091 [US4] Remediate AgentsPipelinePage UX findings

- [ ] T092 [P] [US4] Audit text, copy, and UX polish in `solune/frontend/src/pages/ActivityPage.tsx` and `solune/frontend/src/components/activity/` (FR-025–FR-032)
- [ ] T093 [US4] Remediate ActivityPage UX findings

- [ ] T094 [P] [US4] Audit text, copy, and UX polish in `solune/frontend/src/pages/AgentsPage.tsx` and `solune/frontend/src/components/agents/` (FR-025–FR-032)
- [ ] T095 [US4] Remediate AgentsPage UX findings

- [ ] T096 [P] [US4] Audit text, copy, and UX polish in `solune/frontend/src/pages/HelpPage.tsx` and `solune/frontend/src/components/help/` (FR-025–FR-032)
- [ ] T097 [US4] Remediate HelpPage UX findings

- [ ] T098 [P] [US4] Audit text, copy, and UX polish in `solune/frontend/src/pages/ChoresPage.tsx` and `solune/frontend/src/components/chores/` (FR-025–FR-032)
- [ ] T099 [US4] Remediate ChoresPage UX findings

- [ ] T100 [P] [US4] Audit text, copy, and UX polish in `solune/frontend/src/pages/AppPage.tsx` (FR-025–FR-032)
- [ ] T101 [US4] Remediate AppPage UX findings

- [ ] T102 [P] [US4] Audit text, copy, and UX polish in `solune/frontend/src/pages/LoginPage.tsx` and `solune/frontend/src/components/auth/` (FR-025–FR-032)
- [ ] T103 [US4] Remediate LoginPage UX findings

- [ ] T104 [P] [US4] Audit text, copy, and UX polish in `solune/frontend/src/pages/SettingsPage.tsx` and `solune/frontend/src/components/settings/` (FR-025–FR-032)
- [ ] T105 [US4] Remediate SettingsPage UX findings

- [ ] T106 [P] [US4] Audit text, copy, and UX polish in `solune/frontend/src/pages/ToolsPage.tsx` and `solune/frontend/src/components/tools/` (FR-025–FR-032)
- [ ] T107 [US4] Remediate ToolsPage UX findings

- [ ] T108 [P] [US4] Audit text, copy, and UX polish in `solune/frontend/src/pages/NotFoundPage.tsx` (FR-025–FR-032, most items N/A)
- [ ] T109 [US4] Remediate NotFoundPage UX findings (if any)

**Checkpoint**: All 12 pages have polished, consistent UX — final copy, verb buttons, confirmation dialogs, feedback, truncation, timestamps.

---

## Phase 7: User Story 5 — Type-Safe and Performant Codebase (Priority: P3)

**Goal**: Zero `any` types, no unsafe type assertions, stable list keys, memoized expensive computations, and no unnecessary re-renders.

**Independent Test**: For any page, run type checker with zero errors, search for `any` types, verify list keys use stable IDs, confirm heavy computations are memoized.

### Implementation for User Story 5

**Type safety audit (all pages)**:
- [ ] T110 [P] [US5] Search for `any` type annotations across all page files in `solune/frontend/src/pages/` and their feature components — list all occurrences (FR-016)
- [ ] T111 [P] [US5] Search for type assertions (`as` keyword) across all page files in `solune/frontend/src/pages/` and their feature components — list all occurrences (FR-017)
- [ ] T112 [US5] Replace all `any` types with explicit types in `solune/frontend/src/pages/` and `solune/frontend/src/components/` (FR-016)
- [ ] T113 [US5] Replace type assertions with type guards or discriminated unions in `solune/frontend/src/pages/` and `solune/frontend/src/components/`; add justification comments for unavoidable assertions (FR-017)
- [ ] T114 [US5] Verify API response types in `solune/frontend/src/types/index.ts` and `solune/frontend/src/types/apps.ts` match backend Pydantic models — date fields are `string` (ISO), nullable fields use `| null`
- [ ] T115 [US5] Add explicit return type annotations to custom hooks in `solune/frontend/src/hooks/` where return types are ambiguous

**Performance audit (all pages)**:
- [ ] T116 [P] [US5] Search for `key={index}` or `key={i}` patterns across all page files and feature components — list all occurrences (FR-037)
- [ ] T117 [US5] Replace all array-index keys with stable unique identifiers (`key={item.id}`) in `solune/frontend/src/pages/` and `solune/frontend/src/components/` (FR-037)
- [ ] T118 [US5] Audit expensive synchronous computations (sorting, filtering, grouping) in all pages — wrap in `useMemo` where needed (FR-039)
- [ ] T119 [US5] Audit unnecessary re-renders in `solune/frontend/src/pages/` and `solune/frontend/src/components/` — wrap expensive components with stable props in `React.memo()` and stabilize callbacks with `useCallback` where passed to memoized children (FR-037)
- [ ] T120 [US5] Audit list rendering in `solune/frontend/src/pages/` and `solune/frontend/src/components/` — any page rendering >50 items should use virtualization (`react-window`) or pagination (FR-038)

**Styling audit (all pages)**:
- [ ] T121 [P] [US5] Search for inline `style={}` attributes across all page files and feature components (FR-033)
- [ ] T122 [US5] Replace inline `style={}` attributes with Tailwind utility classes using `cn()` from `solune/frontend/src/lib/utils.ts` (FR-033)
- [ ] T123 [US5] Audit responsive design — verify all pages render correctly at 768px, 1024px, 1440px, 1920px viewport widths (FR-034)
- [ ] T124 [US5] Audit dark mode — verify all pages use Tailwind `dark:` variants or CSS variables, no hardcoded colors (FR-035)
- [ ] T125 [US5] Audit spacing consistency in `solune/frontend/src/pages/` and `solune/frontend/src/components/` — replace arbitrary spacing values with Tailwind spacing scale (FR-036)

- [ ] T126 [US5] Run `npx tsc --noEmit` from `solune/frontend/` — verify zero type errors after all type fixes (FR-016, FR-017)

**Checkpoint**: Zero `any` types, no unsafe assertions, stable list keys, memoized computations, Tailwind-only styling, responsive and dark-mode correct.

---

## Phase 8: User Story 6 — Comprehensive Test Coverage (Priority: P3)

**Goal**: Every page's custom hooks and interactive components have meaningful tests covering happy path, error, loading, empty, and edge-case scenarios.

**Independent Test**: For any page, run its test suite and confirm hook tests, component tests, and edge-case tests exist and pass.

### Implementation for User Story 6

**Hook tests (per page)**:
- [ ] T127 [P] [US6] Audit and update hook tests for ProjectsPage hooks in `solune/frontend/src/hooks/useProjects.test.ts` and `solune/frontend/src/hooks/useProjectBoard.test.ts` — cover happy path, error, loading, empty states (FR-040)
- [ ] T128 [P] [US6] Audit and update hook tests for AppsPage hooks in `solune/frontend/src/hooks/useApps.test.ts` — cover happy path, error, loading, empty states (FR-040)
- [ ] T129 [P] [US6] Audit and update hook tests for AgentsPipelinePage hooks in `solune/frontend/src/hooks/useSelectedPipeline.test.ts`, `solune/frontend/src/hooks/usePipelineConfig.test.ts`, and related pipeline hooks — cover happy path, error, loading, empty states (FR-040)
- [ ] T130 [P] [US6] Audit and update hook tests for ActivityPage hooks in `solune/frontend/src/hooks/useActivityFeed.test.ts` — cover happy path, error, loading, empty states (FR-040)
- [ ] T131 [P] [US6] Audit and update hook tests for AgentsPage hooks in `solune/frontend/src/hooks/useAgents.test.ts` — cover happy path, error, loading, empty states (FR-040)
- [ ] T132 [P] [US6] Audit and update hook tests for ChoresPage hooks in `solune/frontend/src/hooks/useChores.test.ts` — cover happy path, error, loading, empty states (FR-040)
- [ ] T133 [P] [US6] Audit and update hook tests for SettingsPage hooks in `solune/frontend/src/hooks/useSettings.test.ts` and `solune/frontend/src/hooks/useSettingsForm.test.ts` — cover happy path, error, loading, empty states (FR-040)
- [ ] T134 [P] [US6] Audit and update hook tests for ToolsPage hooks in `solune/frontend/src/hooks/useTools.test.ts` — cover happy path, error, loading, empty states (FR-040)

**Component/page tests**:
- [ ] T135 [P] [US6] Audit and update page tests for `solune/frontend/src/pages/ProjectsPage.test.tsx` — cover user interactions, loading/error/empty rendering (FR-041)
- [ ] T136 [P] [US6] Audit and update page tests for `solune/frontend/src/pages/AppsPage.test.tsx` — cover user interactions, loading/error/empty rendering (FR-041)
- [ ] T137 [P] [US6] Audit and update page tests for `solune/frontend/src/pages/AgentsPipelinePage.test.tsx` — cover user interactions, loading/error/empty rendering (FR-041)
- [ ] T138 [P] [US6] Audit and update page tests for `solune/frontend/src/pages/ActivityPage.test.tsx` — cover user interactions, loading/error/empty rendering (FR-041)
- [ ] T139 [P] [US6] Audit and update page tests for `solune/frontend/src/pages/AgentsPage.test.tsx` — cover user interactions, loading/error/empty rendering (FR-041)
- [ ] T140 [P] [US6] Audit and update page tests for `solune/frontend/src/pages/ChoresPage.test.tsx` — cover user interactions, loading/error/empty rendering (FR-041)
- [ ] T141 [P] [US6] Audit and update page tests for `solune/frontend/src/pages/AppPage.test.tsx` — cover user interactions, loading/error/empty rendering (FR-041)
- [ ] T142 [P] [US6] Audit and update page tests for `solune/frontend/src/pages/LoginPage.test.tsx` — cover form interaction, error states (FR-041)
- [ ] T143 [P] [US6] Audit and update page tests for `solune/frontend/src/pages/SettingsPage.test.tsx` — cover user interactions, form submissions (FR-041)
- [ ] T144 [P] [US6] Audit and update page tests for `solune/frontend/src/pages/ToolsPage.test.tsx` — cover user interactions, loading/error/empty rendering (FR-041)
- [ ] T145 [P] [US6] Audit and update page tests for `solune/frontend/src/pages/HelpPage.test.tsx` — cover rendering and interactions (FR-041)
- [ ] T146 [P] [US6] Audit and update page tests for `solune/frontend/src/pages/NotFoundPage.test.tsx` — verify rendering (FR-041)

**Edge case and convention validation**:
- [ ] T147 [US6] Verify all tests follow codebase conventions: `vi.mock('@/services/api', ...)`, `renderHook`, `waitFor`, `createWrapper()` — no snapshot tests (FR-042)
- [ ] T148 [US6] Verify edge cases covered across all test files: empty collections, error responses, rate-limit errors, long strings, null/missing data (FR-042)

**Checkpoint**: All pages have hook tests, component tests, and edge-case coverage. All tests pass.

---

## Phase 9: User Story 7 — Clean, Consistent Code (Priority: P3)

**Goal**: Zero linter warnings, all imports use `@/` alias, no dead code, no `console.log`, no magic strings, consistent file naming.

**Independent Test**: For any page, run the linter with zero warnings, verify imports, confirm no dead code or console logs, and check for magic strings.

### Implementation for User Story 7

- [ ] T149 [P] [US7] Search for and remove dead code (unused imports, commented-out blocks, unreachable branches) across all page files in `solune/frontend/src/pages/` (FR-044)
- [ ] T150 [P] [US7] Search for and remove `console.log` statements across all page files and feature components in `solune/frontend/src/pages/` and `solune/frontend/src/components/` (FR-044)
- [ ] T151 [P] [US7] Search for relative multi-level imports (e.g., `../../`) across all page files and feature components — replace with `@/` alias imports (FR-045)
- [ ] T152 [P] [US7] Search for magic strings (repeated status values, route paths, query keys) across all page files and feature components — extract to named constants (FR-044)
- [ ] T153 [US7] Verify file naming conventions: components are PascalCase `.tsx`, hooks are `use*.ts`, types in `types/`, utilities in `lib/`
- [ ] T154 [US7] Run `npx eslint src/pages/ src/components/ src/hooks/` from `solune/frontend/` — fix all remaining warnings to reach zero (FR-043)

**Checkpoint**: Zero linter warnings, clean imports, no dead code, no console logs, no magic strings.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all pages and cross-cutting improvements.

- [ ] T155 [P] Run final lint validation: `npx eslint src/pages/ src/components/ src/hooks/` from `solune/frontend/` — confirm 0 warnings (SC-008)
- [ ] T156 [P] Run final type-check validation: `npx tsc --noEmit` from `solune/frontend/` — confirm 0 errors (SC-009)
- [ ] T157 [P] Run final test suite: `npx vitest run` from `solune/frontend/` — confirm all tests pass (SC-010)
- [ ] T158 Perform manual browser check — light mode, dark mode, viewport 768px → 1920px for all 12 pages (SC-007)
- [ ] T159 Perform keyboard-only navigation check — Tab through all interactive elements on all 12 pages, Enter/Space to activate (SC-005)
- [ ] T160 Verify all destructive actions across all pages require confirmation dialog before execution (SC-011)
- [ ] T161 Verify all mutations across all pages provide visible success or failure feedback within 2 seconds (SC-012)
- [ ] T162 Produce final audit summary — pass/fail/N/A per checklist category per page, total remediation count (SC-001, SC-002)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 Architecture (Phase 3)**: Depends on Foundational phase — can start after Phase 2
- **US2 States (Phase 4)**: Depends on US1 (architecture must be clean before adding states) — can start after Phase 3
- **US3 Accessibility (Phase 5)**: Depends on Foundational — can run in parallel with US1/US2 if needed, but ideally after US1
- **US4 UX Polish (Phase 6)**: Depends on Foundational — can run in parallel with US3, but ideally after US2
- **US5 Type Safety & Performance (Phase 7)**: Depends on Foundational — can start after Phase 2, benefits from US1 being complete
- **US6 Test Coverage (Phase 8)**: Depends on US1–US5 being complete (tests should cover final behavior)
- **US7 Code Hygiene (Phase 9)**: Depends on US1–US5 being complete (cleanup after all changes)
- **Polish (Phase 10)**: Depends on ALL user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **US2 (P1)**: Best after US1 (architecture should be clean first) — can be independent if needed
- **US3 (P2)**: Can start after Foundational — independent of US1/US2
- **US4 (P2)**: Can start after Foundational — independent of US1/US2/US3
- **US5 (P3)**: Can start after Foundational — independent of other stories
- **US6 (P3)**: Best after US1–US5 (tests should verify final behavior)
- **US7 (P3)**: Best after US1–US5 (cleanup after all changes are made)

### Within Each User Story

- Audit tasks (discover findings) BEFORE remediation tasks (fix findings)
- Per-page audit tasks marked [P] can run in parallel across different pages
- Remediation tasks depend on their corresponding audit task
- Cross-cutting validation tasks come after all per-page tasks

### Parallel Opportunities

- All Setup tasks (T001–T004) can run in parallel
- All Foundational verification tasks (T005–T011) marked [P] can run in parallel
- Within each US phase, per-page audit tasks marked [P] can run in parallel (different files)
- US3 (accessibility) and US4 (UX polish) can run in parallel with each other
- US5 (type safety) sub-audits (type search, key search, style search) can run in parallel
- US6 (tests) — all per-hook and per-page test tasks marked [P] can run in parallel
- US7 (hygiene) — all search-and-fix tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch per-page architecture audits in parallel (different files):
Task: "Audit ProjectsPage architecture in solune/frontend/src/pages/ProjectsPage.tsx"         # T012
Task: "Audit AppsPage architecture in solune/frontend/src/pages/AppsPage.tsx"                  # T017
Task: "Audit AgentsPipelinePage architecture in solune/frontend/src/pages/AgentsPipelinePage.tsx" # T022
Task: "Audit ActivityPage architecture in solune/frontend/src/pages/ActivityPage.tsx"           # T027
Task: "Audit AgentsPage architecture in solune/frontend/src/pages/AgentsPage.tsx"              # T030
Task: "Audit HelpPage architecture in solune/frontend/src/pages/HelpPage.tsx"                  # T031
Task: "Audit ChoresPage architecture in solune/frontend/src/pages/ChoresPage.tsx"              # T032
Task: "Audit AppPage architecture in solune/frontend/src/pages/AppPage.tsx"                    # T033
Task: "Audit LoginPage architecture in solune/frontend/src/pages/LoginPage.tsx"                # T034
Task: "Audit SettingsPage architecture in solune/frontend/src/pages/SettingsPage.tsx"          # T035
Task: "Audit ToolsPage architecture in solune/frontend/src/pages/ToolsPage.tsx"                # T036
Task: "Audit NotFoundPage architecture in solune/frontend/src/pages/NotFoundPage.tsx"          # T037
```

## Parallel Example: User Story 6

```bash
# Launch all hook test audits in parallel (different test files):
Task: "Audit hook tests for useProjects in solune/frontend/src/hooks/useProjects.test.ts"     # T127
Task: "Audit hook tests for useApps in solune/frontend/src/hooks/useApps.test.ts"              # T128
Task: "Audit hook tests for pipeline hooks in solune/frontend/src/hooks/"                       # T129
Task: "Audit hook tests for useActivityFeed in solune/frontend/src/hooks/useActivityFeed.test.ts" # T130

# Launch all page test audits in parallel (different test files):
Task: "Audit page tests for ProjectsPage in solune/frontend/src/pages/ProjectsPage.test.tsx"  # T135
Task: "Audit page tests for AppsPage in solune/frontend/src/pages/AppsPage.test.tsx"           # T136
```

---

## Implementation Strategy

### MVP First (User Story 1 + User Story 2)

1. Complete Phase 1: Setup — establish baseline metrics
2. Complete Phase 2: Foundational — verify shared components
3. Complete Phase 3: User Story 1 (Architecture) — all pages ≤250 lines, extracted hooks
4. Complete Phase 4: User Story 2 (States) — all pages have loading/error/empty states
5. **STOP and VALIDATE**: `npx tsc --noEmit && npx eslint src/pages/ && npx vitest run`
6. Deploy/demo — pages are architecturally sound and never show blank screens

### Incremental Delivery

1. Setup + Foundational → Framework ready
2. Add US1 (Architecture) → Pages are well-structured → Validate
3. Add US2 (States) → Pages are resilient → Validate (MVP!)
4. Add US3 (Accessibility) → Pages are inclusive → Validate
5. Add US4 (UX Polish) → Pages are polished → Validate
6. Add US5 (Type Safety + Performance) → Pages are optimized → Validate
7. Add US6 (Tests) → Pages are covered → Validate
8. Add US7 (Code Hygiene) → Codebase is clean → Validate
9. Final Polish → Full audit complete → Deploy

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done, split by page or by story:
   - **By page**: Each developer takes 2–3 pages and runs all US1–US7 for those pages
   - **By story**: Developer A: US1 (all pages), Developer B: US2 (all pages), Developer C: US3+US4 (all pages)
3. US6 (Tests) and US7 (Hygiene) run after all other stories converge

---

## Notes

- [P] tasks = different files, no dependencies — safe to parallelize
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Audit tasks discover issues; remediation tasks fix them — audit before remediate
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Pages listed as N/A for certain audit items (e.g., NotFoundPage for data fetching) should be scored as N/A, not forced to comply
- Total: 162 tasks across 10 phases
