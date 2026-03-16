# Tasks: Apps Page Audit

**Input**: Design documents from `/specs/043-apps-page-audit/`
**Prerequisites**: spec.md (required for user stories)

**Tests**: Tests are REQUIRED by the feature specification — FR-030 (hook tests), FR-031 (component interaction tests), FR-032 (edge case tests). See [spec.md](spec.md) for full requirement definitions. User Story 4 (P3) covers comprehensive test coverage for hooks, components, and edge cases.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. This is a frontend-only audit — no backend changes required.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/frontend/src/`
- Pages: `solune/frontend/src/pages/`
- Apps components: `solune/frontend/src/components/apps/`
- Hooks: `solune/frontend/src/hooks/`
- Types: `solune/frontend/src/types/`
- Shared UI: `solune/frontend/src/components/ui/`
- Shared common: `solune/frontend/src/components/common/`
- Services: `solune/frontend/src/services/`

## Current Architecture

| File | Lines | Role |
|------|-------|------|
| AppsPage.tsx | 242 | Main page — list view, detail routing, create dialog |
| AppCard.tsx | 101 | Card component — status badge, action buttons |
| AppDetailView.tsx | 141 | Detail view — metadata grid, lifecycle controls, preview |
| AppPreview.tsx | 63 | Live preview iframe with sandbox security |
| useApps.ts | 92 | 7 hooks (useApps, useApp, useCreateApp, useUpdateApp, useDeleteApp, useStartApp, useStopApp) |
| types/apps.ts | 42 | App, AppCreate, AppUpdate, AppStatusResponse, AppStatus, RepoType |
| AppsPage.test.tsx | 104 | 3 tests (create dialog, submit, error handling) |
| AppPage.test.tsx | 34 | 2 tests (launcher button, navigation) |

---

## Phase 1: Setup (Audit Baseline)

**Purpose**: Establish audit baseline — verify existing tests pass and no pre-existing regressions

- [ ] T001 Run existing test suite (`cd solune/frontend && npx vitest run`) and document any pre-existing failures
- [ ] T002 [P] Run type-check (`cd solune/frontend && npx tsc --noEmit`) and lint (`cd solune/frontend && npx eslint src/pages/AppsPage.tsx src/components/apps/`) to establish baseline
- [ ] T003 [P] Review shared components available for reuse — catalog CelestialLoader, ErrorBoundary, ConfirmationDialog, Card, Tooltip, HoverCard in solune/frontend/src/components/ui/ and solune/frontend/src/components/common/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add missing shared component integrations and type safety improvements that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Add `onError` callback support to `useDeleteApp` mutation with user-friendly error message surfacing (toast or inline) in solune/frontend/src/hooks/useApps.ts
- [ ] T005 [P] Add `onError` callback support to `useStartApp` mutation with user-friendly error message surfacing in solune/frontend/src/hooks/useApps.ts
- [ ] T006 [P] Add `onError` callback support to `useStopApp` mutation with user-friendly error message surfacing in solune/frontend/src/hooks/useApps.ts
- [ ] T007 [P] Replace unsafe type assertion `error as ApiError` (line ~70) with a type guard function `isApiError()` in solune/frontend/src/pages/AppsPage.tsx
- [ ] T008 Import and integrate `isRateLimitApiError()` utility for rate-limit detection in error handling across Apps page files

**Checkpoint**: Foundation ready — mutation error handling and type safety improvements in place for all user stories

---

## Phase 3: User Story 1 — Reliable App Management with Proper Feedback (Priority: P1) 🎯 MVP

**Goal**: Every user action provides clear, immediate feedback: loading indicators, meaningful errors, empty states, and confirmation dialogs on destructive actions

**Independent Test**: Navigate to Apps page with various data conditions (no apps, many apps, API failure, slow network) and verify that each state renders appropriately with user-friendly messaging and that destructive actions always present a confirmation dialog.

### Implementation for User Story 1

#### Loading, Error & Empty States

- [ ] T009 [US1] Replace custom inline spinner with `<CelestialLoader size="md" />` for loading state in solune/frontend/src/pages/AppsPage.tsx (lines ~96-100)
- [ ] T010 [P] [US1] Replace custom inline spinner with `<CelestialLoader size="md" />` for loading state in solune/frontend/src/components/apps/AppDetailView.tsx (lines ~21-26)
- [ ] T011 [P] [US1] Add rate-limit error detection using `isRateLimitApiError()` to error state display with specific messaging in solune/frontend/src/pages/AppsPage.tsx (lines ~149-156)
- [ ] T012 [P] [US1] Add retry button to error state that calls `refetch()` in solune/frontend/src/pages/AppsPage.tsx
- [ ] T013 [P] [US1] Add retry button to error state in solune/frontend/src/components/apps/AppDetailView.tsx (lines ~29-34)
- [ ] T014 [US1] Verify empty state renders meaningful call-to-action ("Create your first app") in solune/frontend/src/pages/AppsPage.tsx (lines ~103-114)

#### Confirmation Dialogs on Destructive Actions

- [ ] T015 [US1] Import and integrate `<ConfirmationDialog>` for delete app action in solune/frontend/src/pages/AppsPage.tsx — wrap `deleteApp.mutate()` with confirmation ("Delete app '{name}'? This action cannot be undone.")
- [ ] T016 [P] [US1] Import and integrate `<ConfirmationDialog>` for stop app action in solune/frontend/src/pages/AppsPage.tsx — wrap `stopApp.mutate()` with confirmation ("Stop app '{name}'?")
- [ ] T017 [P] [US1] Add confirmation dialog state management (pending action name, dialog visibility) in solune/frontend/src/pages/AppsPage.tsx
- [ ] T018 [P] [US1] Import and integrate `<ConfirmationDialog>` for delete action in solune/frontend/src/components/apps/AppDetailView.tsx
- [ ] T019 [P] [US1] Import and integrate `<ConfirmationDialog>` for stop action in solune/frontend/src/components/apps/AppDetailView.tsx

#### Success Feedback

- [ ] T020 [US1] Add success feedback (toast or inline status update) after successful create, start, stop, and delete mutations in solune/frontend/src/pages/AppsPage.tsx
- [ ] T021 [P] [US1] Add success feedback after successful start, stop, and delete mutations in solune/frontend/src/components/apps/AppDetailView.tsx

#### Error Boundary

- [ ] T022 [US1] Wrap Apps page content with `<ErrorBoundary>` from `@/components/common/` in solune/frontend/src/pages/AppsPage.tsx

#### Mutation Button States

- [ ] T023 [P] [US1] Add `disabled={mutation.isPending}` to Start, Stop, Delete action buttons in solune/frontend/src/components/apps/AppCard.tsx to prevent double-clicks
- [ ] T024 [US1] Run existing tests (`cd solune/frontend && npx vitest run`) to verify no regressions from US1 changes

**Checkpoint**: User Story 1 complete — all page states render correctly, destructive actions require confirmation, mutations show success/error feedback

---

## Phase 4: User Story 2 — Accessible and Polished App Management Experience (Priority: P2)

**Goal**: Full keyboard accessibility, screen reader support, dark mode, consistent copy, truncation with tooltips, and responsive layout

**Independent Test**: Navigate the entire Apps page using only keyboard inputs and verify all interactive elements are reachable, dialogs trap focus, screen readers announce elements correctly. Toggle dark mode and verify all elements are visible with proper contrast.

### Accessibility — ARIA Attributes

- [ ] T025 [P] [US2] Add `role="dialog"`, `aria-modal="true"`, and `aria-labelledby` to create app dialog overlay in solune/frontend/src/pages/AppsPage.tsx (lines ~134-239)
- [ ] T026 [P] [US2] Add `aria-label` to Start button ("Start app {name}"), Stop button ("Stop app {name}"), Delete button ("Delete app {name}") in solune/frontend/src/components/apps/AppCard.tsx
- [ ] T027 [P] [US2] Add `aria-label` to back button ("Back to apps list") in solune/frontend/src/components/apps/AppDetailView.tsx (line ~48)
- [ ] T028 [P] [US2] Add `aria-label` to action buttons (Start, Stop, Delete) in solune/frontend/src/components/apps/AppDetailView.tsx (lines ~89-123)
- [ ] T029 [P] [US2] Add `aria-hidden="true"` to decorative icons (Lucide icons used for visual-only purposes) in solune/frontend/src/components/apps/AppCard.tsx, solune/frontend/src/components/apps/AppDetailView.tsx, and solune/frontend/src/components/apps/AppPreview.tsx
- [ ] T030 [P] [US2] Add `aria-live="polite"` to loading/error state containers for screen reader announcement in solune/frontend/src/pages/AppsPage.tsx
- [ ] T031 [P] [US2] Add `aria-busy="true"` to app list container during loading state in solune/frontend/src/pages/AppsPage.tsx

### Accessibility — Focus Management

- [ ] T032 [US2] Implement focus trap in create app dialog — Tab cannot escape modal while open in solune/frontend/src/pages/AppsPage.tsx
- [ ] T033 [P] [US2] Restore focus to trigger button ("Create App" button) when create dialog closes in solune/frontend/src/pages/AppsPage.tsx
- [ ] T034 [P] [US2] Add visible focus indicators (`celestial-focus` class or Tailwind `focus-visible:` ring) to all interactive elements in solune/frontend/src/components/apps/AppCard.tsx
- [ ] T035 [P] [US2] Add visible focus indicators to all interactive elements in solune/frontend/src/components/apps/AppDetailView.tsx
- [ ] T036 [P] [US2] Add visible focus indicators to form inputs and buttons in create dialog in solune/frontend/src/pages/AppsPage.tsx

### Text, Copy & UX Polish

- [ ] T037 [P] [US2] Verify all action buttons use verb-based labels ("Create App", "Start App", "Stop App", "Delete App") — update any that don't in solune/frontend/src/pages/AppsPage.tsx
- [ ] T038 [P] [US2] Verify all action buttons use verb-based labels in solune/frontend/src/components/apps/AppCard.tsx and solune/frontend/src/components/apps/AppDetailView.tsx
- [ ] T039 [P] [US2] Add text truncation with `<Tooltip>` for long app names and descriptions in solune/frontend/src/components/apps/AppCard.tsx — use `text-ellipsis truncate` with full text in tooltip on hover
- [ ] T040 [P] [US2] Add text truncation with `<Tooltip>` for long app names and descriptions in solune/frontend/src/components/apps/AppDetailView.tsx
- [ ] T041 [P] [US2] Replace `toLocaleDateString()` with relative time format ("2 hours ago") for recent timestamps and absolute for older ones in solune/frontend/src/components/apps/AppDetailView.tsx (line ~83)
- [ ] T042 [P] [US2] Wrap date output in semantic `<time>` element with `datetime` attribute in solune/frontend/src/components/apps/AppDetailView.tsx
- [ ] T043 [P] [US2] Verify all user-visible error messages follow the format "Could not [action]. [Reason]. [Suggested next step]." in solune/frontend/src/pages/AppsPage.tsx and solune/frontend/src/components/apps/AppDetailView.tsx

### Dark Mode & Styling

- [ ] T044 [P] [US2] Audit all hardcoded color values in status badges (`bg-blue-100/90`, `text-blue-700`, `bg-emerald-100/90`, etc.) and add corresponding `dark:` variants in solune/frontend/src/components/apps/AppCard.tsx (STATUS_STYLES object, lines ~9-30)
- [ ] T045 [P] [US2] Audit and add `dark:` variants to all color classes in create dialog in solune/frontend/src/pages/AppsPage.tsx
- [ ] T046 [P] [US2] Audit and add `dark:` variants to all color classes in solune/frontend/src/components/apps/AppDetailView.tsx
- [ ] T047 [P] [US2] Audit and add `dark:` variants to all color classes in solune/frontend/src/components/apps/AppPreview.tsx
- [ ] T048 [P] [US2] Verify no hardcoded colors (`#fff`, `bg-white`, etc.) exist — replace with theme-aware Tailwind classes in solune/frontend/src/pages/AppsPage.tsx, solune/frontend/src/components/apps/AppCard.tsx, solune/frontend/src/components/apps/AppDetailView.tsx, and solune/frontend/src/components/apps/AppPreview.tsx

### Responsive Layout

- [ ] T049 [P] [US2] Verify app card grid layout adapts correctly from 768px to 1920px viewport widths without broken layouts or horizontal scroll in solune/frontend/src/pages/AppsPage.tsx
- [ ] T050 [P] [US2] Verify detail view info grid (4 columns) collapses correctly on smaller viewports in solune/frontend/src/components/apps/AppDetailView.tsx (lines ~63-86)
- [ ] T051 [P] [US2] Verify create dialog is responsive and displays correctly on small viewports in solune/frontend/src/pages/AppsPage.tsx

- [ ] T052 [US2] Run existing tests (`cd solune/frontend && npx vitest run`) to verify no regressions from US2 changes

**Checkpoint**: User Story 2 complete — Apps page is fully accessible, dark-mode ready, responsive, and polished

---

## Phase 5: User Story 3 — Well-Structured, Maintainable Apps Page Codebase (Priority: P2)

**Goal**: Clean, modular codebase — page file ≤250 lines, feature folder structure, extracted hooks, full type safety, zero dead code, all imports use `@/` alias

**Independent Test**: Run linting, type checking, and verify page file ≤250 lines, all sub-components in feature folder, hooks extracted for complex state, zero type-safety escape hatches or lint violations.

### Component Architecture

- [ ] T053 [US3] Assess AppsPage.tsx line count (currently 242 lines) — if create dialog extraction reduces it below 250 lines, proceed; otherwise extract create dialog into `solune/frontend/src/components/apps/CreateAppDialog.tsx`
- [ ] T054 [P] [US3] Verify all sub-components (AppCard, AppDetailView, AppPreview) live in `solune/frontend/src/components/apps/` — move any that are inline in the page file
- [ ] T055 [P] [US3] Verify no prop drilling >2 levels exists in solune/frontend/src/pages/AppsPage.tsx → solune/frontend/src/components/apps/AppCard.tsx → child chain — use composition or hook extraction if found

### Hook Extraction

- [ ] T056 [US3] Assess complex state logic in AppsPage.tsx — if create dialog state + confirmation dialog state + error state exceeds 15 lines of useState/useEffect/useCallback, extract into `solune/frontend/src/hooks/useAppPageState.ts`

### Type Safety

- [ ] T057 [P] [US3] Audit all Apps files for `any` types — eliminate any found in solune/frontend/src/pages/AppsPage.tsx, solune/frontend/src/components/apps/, solune/frontend/src/hooks/useApps.ts
- [ ] T058 [P] [US3] Audit for unsafe type assertions (`as`) in solune/frontend/src/pages/AppsPage.tsx, solune/frontend/src/components/apps/AppCard.tsx, solune/frontend/src/components/apps/AppDetailView.tsx, and solune/frontend/src/hooks/useApps.ts — replace with type guards
- [ ] T059 [P] [US3] Add explicit return type annotations to all custom hooks in solune/frontend/src/hooks/useApps.ts if not already inferrable without ambiguity
- [ ] T060 [P] [US3] Verify event handler types are explicit (e.g., `React.FormEvent<HTMLFormElement>`) — no generic `any` in form handlers in solune/frontend/src/pages/AppsPage.tsx

### Data Fetching Conventions

- [ ] T061 [P] [US3] Verify `appKeys` query key factory follows `[feature].all / .list() / .detail(id)` convention in solune/frontend/src/hooks/useApps.ts
- [ ] T062 [P] [US3] Verify no duplicate API calls between solune/frontend/src/pages/AppsPage.tsx and solune/frontend/src/components/apps/AppDetailView.tsx — ensure AppDetailView uses `useApp(name)` without overlapping page-level `useApps()` fetch
- [ ] T063 [P] [US3] Verify `staleTime` is configured appropriately (30s for lists, 60s for detail) in solune/frontend/src/hooks/useApps.ts

### Code Hygiene

- [ ] T064 [P] [US3] Remove all dead code — unused imports, commented-out blocks, unreachable branches in solune/frontend/src/pages/AppsPage.tsx, solune/frontend/src/components/apps/*.tsx, and solune/frontend/src/hooks/useApps.ts
- [ ] T065 [P] [US3] Remove all `console.log` statements in solune/frontend/src/pages/AppsPage.tsx, solune/frontend/src/components/apps/*.tsx, and solune/frontend/src/hooks/useApps.ts
- [ ] T066 [P] [US3] Verify all project imports use `@/` alias — no relative path imports crossing module boundaries in any Apps files
- [ ] T067 [P] [US3] Verify file naming conventions — components PascalCase `.tsx`, hooks `use*.ts`, types in `types/` in solune/frontend/src/components/apps/, solune/frontend/src/hooks/useApps.ts, and solune/frontend/src/types/apps.ts
- [ ] T068 [P] [US3] Replace any magic strings (status values, route paths, query keys) with named constants in solune/frontend/src/pages/AppsPage.tsx and solune/frontend/src/components/apps/AppCard.tsx

### Shared Component Integration

- [ ] T069 [P] [US3] Replace custom card styling with shared `<Card>` component from `solune/frontend/src/components/ui/card.tsx` in AppCard if not already using it
- [ ] T070 [P] [US3] Use `cn()` from `@/lib/utils` for all conditional class compositions in solune/frontend/src/components/apps/AppCard.tsx, solune/frontend/src/components/apps/AppDetailView.tsx, and solune/frontend/src/pages/AppsPage.tsx

### Validation

- [ ] T071 [US3] Run linter (`cd solune/frontend && npx eslint src/pages/AppsPage.tsx src/components/apps/ src/hooks/useApps.ts`) — verify zero warnings
- [ ] T072 [P] [US3] Run type checker (`cd solune/frontend && npx tsc --noEmit`) — verify zero errors
- [ ] T073 [US3] Run existing tests (`cd solune/frontend && npx vitest run`) to verify no regressions from US3 changes

**Checkpoint**: User Story 3 complete — Apps codebase is clean, modular, type-safe, and lint-clean

---

## Phase 6: User Story 4 — Comprehensive Test Coverage for Apps Features (Priority: P3)

**Goal**: Tests cover primary user interactions, edge cases, and custom hooks. Tests follow codebase conventions with assertion-based testing (no snapshot tests).

**Independent Test**: Run test suite for all Apps-related files and verify that tests exist for hooks, components, and page interactions covering happy paths, error states, empty states, and edge cases.

### Hook Tests

- [ ] T074 [P] [US4] Create hook test file solune/frontend/src/hooks/useApps.test.ts — test `useApps()` hook: successful data fetch, loading state, error state, staleTime behavior
- [ ] T075 [P] [US4] Add tests for `useApp(name)` hook: successful fetch, enabled/disabled behavior, error state in solune/frontend/src/hooks/useApps.test.ts
- [ ] T076 [P] [US4] Add tests for `useCreateApp()` mutation: successful creation, cache invalidation, error handling in solune/frontend/src/hooks/useApps.test.ts
- [ ] T077 [P] [US4] Add tests for `useDeleteApp()`, `useStartApp()`, `useStopApp()` mutations: successful execution, cache invalidation, error handling in solune/frontend/src/hooks/useApps.test.ts

### Component Tests

- [ ] T078 [P] [US4] Create component test file solune/frontend/src/components/apps/AppCard.test.tsx — test: renders app name/status, Start/Stop/Delete button visibility by status, button click handlers
- [ ] T079 [P] [US4] Add tests for AppCard: disabled state during pending mutations, status badge display for all 4 statuses in solune/frontend/src/components/apps/AppCard.test.tsx
- [ ] T080 [P] [US4] Create component test file solune/frontend/src/components/apps/AppDetailView.test.tsx — test: loading state, error/not-found state, metadata display, action buttons
- [ ] T081 [P] [US4] Create component test file solune/frontend/src/components/apps/AppPreview.test.tsx — test: active with port, inactive state, loading state, error state

### Page Integration Tests

- [ ] T082 [US4] Expand existing tests in solune/frontend/src/pages/AppsPage.test.tsx — add test for loading state display
- [ ] T083 [P] [US4] Add test for empty state display ("no apps" message with create CTA) in solune/frontend/src/pages/AppsPage.test.tsx
- [ ] T084 [P] [US4] Add test for error state display with retry action in solune/frontend/src/pages/AppsPage.test.tsx
- [ ] T085 [P] [US4] Add test for confirmation dialog on delete action in solune/frontend/src/pages/AppsPage.test.tsx
- [ ] T086 [P] [US4] Add test for confirmation dialog on stop action in solune/frontend/src/pages/AppsPage.test.tsx

### Edge Case Tests

- [ ] T087 [P] [US4] Add test for app with null port, null error_message, null associated_pipeline_id in solune/frontend/src/components/apps/AppCard.test.tsx
- [ ] T088 [P] [US4] Add test for app with extremely long name (64 chars) — verify truncation in solune/frontend/src/components/apps/AppCard.test.tsx
- [ ] T089 [P] [US4] Add test for rate-limit error detection and specific messaging in solune/frontend/src/pages/AppsPage.test.tsx
- [ ] T090 [P] [US4] Add test for rapid click prevention (buttons disabled during pending mutation) in solune/frontend/src/components/apps/AppCard.test.tsx
- [ ] T091 [P] [US4] Add test for form validation — whitespace-only name rejected, required fields enforced in solune/frontend/src/pages/AppsPage.test.tsx

### Test Conventions

- [ ] T092 [US4] Verify all tests follow codebase conventions: `vi.mock('@/services/api', ...)`, `renderHook`, `waitFor`, `createWrapper()` — no snapshot tests in any Apps test files
- [ ] T093 [US4] Run full test suite (`cd solune/frontend && npx vitest run`) — verify all new and existing tests pass

**Checkpoint**: User Story 4 complete — comprehensive test coverage for hooks, components, page interactions, and edge cases

---

## Phase 7: User Story 5 — Performant App List Rendering (Priority: P3)

**Goal**: Efficient rendering with stable keys, memoized computations, no duplicate data fetching, and graceful handling of large datasets

**Independent Test**: Load the Apps page with a large dataset (50+ apps) and verify smooth rendering, no jank, stable scroll, and no duplicate network requests.

### Stable Keys & Rendering

- [ ] T094 [P] [US5] Verify all array renders in Apps page use `key={app.name}` (stable unique key) — never `key={index}` in solune/frontend/src/pages/AppsPage.tsx
- [ ] T095 [P] [US5] Verify all array renders in AppDetailView use stable keys in solune/frontend/src/components/apps/AppDetailView.tsx

### Memoization

- [ ] T096 [P] [US5] Wrap any expensive data transformations (sorting, filtering) in `useMemo` if present in solune/frontend/src/pages/AppsPage.tsx
- [ ] T097 [P] [US5] Wrap callback functions passed to memoized children in `useCallback` if needed in solune/frontend/src/pages/AppsPage.tsx

### Duplicate Fetch Prevention

- [ ] T098 [US5] Verify no duplicate API calls — AppDetailView should use the same query instance as page or use `useApp(name)` without overlapping with page-level `useApps()` in solune/frontend/src/components/apps/AppDetailView.tsx

### Large List Handling

- [ ] T099 [US5] Assess whether pagination or virtualization is needed for >50 apps — if app list can grow large, add pagination or consider `react-window` in solune/frontend/src/pages/AppsPage.tsx

### Lazy Loading

- [ ] T100 [P] [US5] Add `loading="lazy"` to non-critical images and icons if any exist in Apps components

- [ ] T101 [US5] Run existing tests (`cd solune/frontend && npx vitest run`) to verify no regressions from US5 changes

**Checkpoint**: User Story 5 complete — Apps page renders efficiently with stable keys, memoized computations, and no duplicate fetches

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, code cleanup, and cross-cutting improvements that span multiple user stories

- [ ] T102 [P] Verify all user-visible strings are finalized copy — no placeholder text, TODOs, or lorem ipsum in solune/frontend/src/pages/AppsPage.tsx, solune/frontend/src/components/apps/AppCard.tsx, solune/frontend/src/components/apps/AppDetailView.tsx, and solune/frontend/src/components/apps/AppPreview.tsx
- [ ] T103 [P] Verify consistent spacing using Tailwind spacing scale (`gap-4`, `p-6`) — no arbitrary values like `p-[13px]` in solune/frontend/src/pages/AppsPage.tsx and solune/frontend/src/components/apps/*.tsx
- [ ] T104 [P] Verify content sections use shared `<Card>` component with consistent padding/rounding in solune/frontend/src/pages/AppsPage.tsx and solune/frontend/src/components/apps/AppCard.tsx
- [ ] T105 Run full lint check: `cd solune/frontend && npx eslint src/pages/AppsPage.tsx src/components/apps/ src/hooks/useApps.ts` — verify 0 warnings
- [ ] T106 [P] Run type check: `cd solune/frontend && npx tsc --noEmit` — verify 0 errors
- [ ] T107 [P] Run full test suite: `cd solune/frontend && npx vitest run` — verify all tests pass
- [ ] T108 Manual browser check — light mode, dark mode, responsive (768px–1920px), keyboard-only navigation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational — core page states and confirmation dialogs
- **User Story 2 (Phase 4)**: Depends on Foundational — can run in parallel with US1 if targeting different files
- **User Story 3 (Phase 5)**: Depends on US1 and US2 — structural refactoring after functional changes
- **User Story 4 (Phase 6)**: Depends on US1, US2, US3 — tests validate final implementations
- **User Story 5 (Phase 7)**: Depends on Foundational — can run in parallel with US1/US2
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — some tasks can run in parallel with US1 (different files)
- **User Story 3 (P2)**: Should start after US1 and US2 — structural refactoring should happen after functional changes to avoid rework
- **User Story 4 (P3)**: Should start after US1, US2, US3 — tests should validate final implementations
- **User Story 5 (P3)**: Can start after Foundational (Phase 2) — performance work is independent

### Within Each User Story

- Loading/error/empty states before confirmation dialogs
- ARIA attributes can be added in parallel across different files
- Focus management after ARIA attributes
- Validation/test run at the end of each story

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (T004–T008)
- US1: Loading state tasks (T009–T014) can run in parallel, confirmation dialog tasks (T015–T019) can run in parallel
- US2: ARIA tasks (T025–T031) can run in parallel, focus tasks (T032–T036) can run in parallel, dark mode tasks (T044–T048) can run in parallel
- US3: Type safety tasks (T057–T060) can run in parallel, code hygiene tasks (T064–T068) can run in parallel
- US4: All hook tests (T074–T077) can run in parallel, all component tests (T078–T081) can run in parallel, all edge case tests (T087–T091) can run in parallel
- US5: Stable keys and memoization tasks (T094–T097) can run in parallel
- **Cross-story parallelism**: US1 and US2 can be worked on simultaneously by different developers (mostly different files)

---

## Parallel Example: User Story 1

```bash
# Launch all loading/error state fixes together (target different files):
Task T009: "Replace spinner with CelestialLoader in AppsPage.tsx"
Task T010: "Replace spinner with CelestialLoader in AppDetailView.tsx"
Task T011: "Add rate-limit error detection in AppsPage.tsx"
Task T012: "Add retry button to error state in AppsPage.tsx"
Task T013: "Add retry button to error state in AppDetailView.tsx"

# Launch all confirmation dialog tasks together (target different files):
Task T015: "Add ConfirmationDialog for delete in AppsPage.tsx"
Task T016: "Add ConfirmationDialog for stop in AppsPage.tsx"
Task T018: "Add ConfirmationDialog for delete in AppDetailView.tsx"
Task T019: "Add ConfirmationDialog for stop in AppDetailView.tsx"
```

## Parallel Example: User Story 4

```bash
# Launch all hook tests together (same test file, parallel test cases):
Task T074: "Test useApps() hook"
Task T075: "Test useApp(name) hook"
Task T076: "Test useCreateApp() mutation"
Task T077: "Test useDeleteApp/useStartApp/useStopApp mutations"

# Launch all component test files together (different test files):
Task T078: "Create AppCard.test.tsx"
Task T080: "Create AppDetailView.test.tsx"
Task T081: "Create AppPreview.test.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify baseline)
2. Complete Phase 2: Foundational (mutation error handling, type safety)
3. Complete Phase 3: User Story 1 — reliable states and confirmation dialogs (P1)
4. **STOP and VALIDATE**: Run full test suite, check all page states, verify confirmation dialogs
5. Deploy/demo if ready — page is reliable and safe

### Incremental Delivery

1. Complete Setup + Foundational → Audit baseline established
2. Add User Story 1 (states + confirmations) → Test independently → reliable page (MVP!)
3. Add User Story 2 (accessibility + polish) → Test independently → accessible, polished page
4. Add User Story 3 (code structure) → Test independently → clean, maintainable codebase
5. Add User Story 4 (test coverage) → Run test suite → comprehensive safety net
6. Add User Story 5 (performance) → Test independently → efficient rendering
7. Polish phase → Final validation and audit summary
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (states + confirmations)
   - Developer B: User Story 2 (accessibility + polish — non-overlapping files)
   - Developer C: User Story 5 (performance — independent)
3. After A + B complete:
   - Developer D: User Story 3 (structural refactoring)
4. After all code changes complete:
   - Developer E: User Story 4 (test coverage validates everything)
5. Final → Polish phase

---

## Notes

- [P] tasks = different files, no dependencies — safe for parallel execution
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Tests are required by FR-030, FR-031, FR-032 and are included in User Story 4
- Existing tests (AppsPage.test.tsx, AppPage.test.tsx) must pass after each phase
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- This is a frontend-only audit — no backend changes required
- All components in scope: AppsPage.tsx (242L), AppCard.tsx (101L), AppDetailView.tsx (141L), AppPreview.tsx (63L), useApps.ts (92L)
- Shared components to integrate: CelestialLoader, ErrorBoundary, ConfirmationDialog, Card, Tooltip
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
