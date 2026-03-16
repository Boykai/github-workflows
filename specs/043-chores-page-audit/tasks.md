# Tasks: Chores Page Audit — Modern Best Practices, Modular Design, and Zero Bugs

**Input**: Design documents from `/specs/043-chores-page-audit/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/component-contracts.yaml, quickstart.md

**Tests**: Tests are REQUIRED by the feature specification (User Story 7, P3). Test tasks are included in the US7 phase. Existing test files (4 files, 757 lines) will be verified and extended.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. The 8 user stories map to the 10 audit categories from the parent issue checklist.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- **No Story label**: Setup (Phase 1), Foundational (Phase 2), and Polish (Phase 11) tasks are cross-cutting and intentionally unlabeled
- Include exact file paths in descriptions

## Path Conventions

- **Frontend**: `solune/frontend/src/`
- **Page**: `solune/frontend/src/pages/ChoresPage.tsx`
- **Components**: `solune/frontend/src/components/chores/`
- **Hooks**: `solune/frontend/src/hooks/useChores.ts`
- **Types**: `solune/frontend/src/types/index.ts`
- **Tests**: `solune/frontend/src/components/chores/__tests__/`

---

## Phase 1: Setup

**Purpose**: Establish baseline state and verify development environment before making any changes

- [ ] T001 Install frontend dependencies via `cd solune/frontend && npm install`
- [ ] T002 Run baseline tests via `cd solune/frontend && npx vitest run` and record current pass/fail state
- [ ] T003 [P] Run baseline lint via `cd solune/frontend && npm run lint` and record current warnings/errors
- [ ] T004 [P] Run baseline type-check via `cd solune/frontend && npm run type-check` and record current errors
- [ ] T005 [P] Run chores-specific tests via `cd solune/frontend && npx vitest run src/components/chores/` and record coverage

---

## Phase 2: Foundational (Discovery & Assessment)

**Purpose**: Read and assess all Chores page files to produce a findings table scoring each audit checklist item as Pass/Fail/N/A. This assessment MUST be complete before any implementation work begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Read and assess `solune/frontend/src/pages/ChoresPage.tsx` (166 lines) — note line count, sub-components rendered, hooks used, page states handled, and any inline business logic
- [ ] T007 [P] Read and assess `solune/frontend/src/components/chores/ChoresPanel.tsx` (543 lines) — note line count violation (>250), extractable sections (toolbar, grid, save-all bar), prop drilling depth, and inline logic
- [ ] T008 [P] Read and assess `solune/frontend/src/components/chores/ChoreCard.tsx` (584 lines) — note line count violation (>250), extractable sections (header, actions, stats, settings), prop drilling depth, and inline logic
- [ ] T009 [P] Read and assess `solune/frontend/src/components/chores/AddChoreModal.tsx` (356 lines) — note line count violation (>250), extractable sections (template selector, creation form), focus management, and ARIA attributes
- [ ] T010 [P] Read and assess remaining chores components: `solune/frontend/src/components/chores/FeaturedRitualsPanel.tsx` (204 lines), `ChoreChatFlow.tsx` (191 lines), `ChoreInlineEditor.tsx` (115 lines), `ChoreScheduleConfig.tsx` (93 lines), `ConfirmChoreModal.tsx` (92 lines), `PipelineSelector.tsx` (85 lines)
- [ ] T011 [P] Read and assess `solune/frontend/src/hooks/useChores.ts` (192 lines) — note query key conventions, staleTime configuration, mutation error handlers (onError with user feedback), and duplicate API call risks
- [ ] T012 [P] Read and assess Chore types in `solune/frontend/src/types/index.ts` (lines 882–1023) — note any `any` types, type assertions (`as`), missing nullable fields, and alignment with data-model.md entities
- [ ] T013 [P] Read and assess choresApi in `solune/frontend/src/services/api.ts` (lines 654–783) — note 10 endpoints, request/response types, and error handling patterns
- [ ] T014 [P] Read and assess existing test files in `solune/frontend/src/components/chores/__tests__/` — `AddChoreModal.test.tsx` (255 lines), `ChoreScheduleConfig.test.tsx` (188 lines), `ChoresPanel.test.tsx` (242 lines), `FeaturedRitualsPanel.test.tsx` (72 lines) — note coverage gaps per spec edge cases
- [ ] T098 [P] Read and assess `CelestialCatalogHero` usage in `solune/frontend/src/pages/ChoresPage.tsx` — note props passed (eyebrow, title, description, stats, actions), accessibility attributes (heading hierarchy, ARIA on stat/action elements), and responsive behavior of the hero section
- [ ] T015 Produce a findings table scoring each of the 10 audit checklist categories (Component Architecture, Data Fetching, Loading/Error/Empty States, Type Safety, Accessibility, Text/Copy/UX, Styling/Layout, Performance, Test Coverage, Code Hygiene) as Pass/Fail/N/A with specific file references for all failures

**Checkpoint**: Assessment complete — all audit findings documented. User story implementation can now begin in priority order.

---

## Phase 3: User Story 1 — Correct and Complete Page States (Priority: P1) 🎯 MVP

**Goal**: Ensure the Chores page displays correctly in every state — loading, empty (no project selected), empty (no chores), populated, error, and rate-limited — so users always understand what is happening and never encounter a broken or confusing view.

**Independent Test**: Trigger each page state (initial load, no project selected, empty chore list, populated chore list, API error, rate-limited response) and verify each renders correctly with appropriate messaging and no console errors.

### Implementation for User Story 1

- [ ] T016 [US1] Audit and fix loading state in `solune/frontend/src/pages/ChoresPage.tsx` — verify `<CelestialLoader>` renders during data fetch, not a blank screen
- [ ] T017 [US1] Audit and fix no-project-selected state in `solune/frontend/src/pages/ChoresPage.tsx` — verify `<ProjectSelectionEmptyState>` renders with clear messaging and no layout breaks
- [ ] T018 [US1] Audit and fix empty chores state in `solune/frontend/src/pages/ChoresPage.tsx` — verify meaningful empty state message with call-to-action to create first chore when `chores.length === 0`
- [ ] T019 [US1] Audit and fix error state in `solune/frontend/src/pages/ChoresPage.tsx` — verify user-friendly error banner with retry action renders on API failure
- [ ] T020 [US1] Audit and fix rate-limit detection in `solune/frontend/src/pages/ChoresPage.tsx` — verify `isRateLimitApiError()` from `solune/frontend/src/utils/rateLimit.ts` is used for specific rate-limit handling with informational banner
- [ ] T021 [US1] Audit and fix partial loading in `solune/frontend/src/pages/ChoresPage.tsx` — verify independent sections (chores list, templates, board data) show their own loading/error states without blocking other sections
- [ ] T022 [US1] Audit and verify `<ErrorBoundary>` wraps the Chores page at route level in `solune/frontend/src/App.tsx` or within `ChoresPage.tsx`
- [ ] T023 [US1] Verify zero console errors across all page states — check for unhandled promise rejections, missing-key warnings, and deprecation warnings in all states
- [ ] T099 [US1] Audit and fix deleted-pipeline fallback in ChoreCard components — verify graceful display (e.g., "Auto" or "pipeline not found" warning) when a chore's `agent_pipeline_id` references a deleted pipeline, rather than crash or blank
- [ ] T100 [US1] Audit and fix real-time sync connection drop handling in `solune/frontend/src/pages/ChoresPage.tsx` — verify stale-data indication and manual refresh option when the sync connection is lost, without page crash

**Checkpoint**: All 6 page states (loading, no-project, empty, populated, error, rate-limited) render correctly with appropriate messaging. Edge cases (deleted pipeline, sync drop) handled gracefully.

---

## Phase 4: User Story 2 — Modular Component Architecture and Type Safety (Priority: P1)

**Goal**: Decompose oversized components (ChoresPanel 543L, ChoreCard 584L, AddChoreModal 356L) into ≤250-line focused sub-components with full type safety and zero `any` types.

**Independent Test**: Verify every component file is ≤250 lines, no prop drilling >2 levels, zero `any` types or `as` assertions, and the page functions identically after refactoring.

### Decompose ChoresPanel (543 → ≤250 + sub-components)

- [ ] T024 [US2] Extract `ChoresToolbar.tsx` from `solune/frontend/src/components/chores/ChoresPanel.tsx` into `solune/frontend/src/components/chores/ChoresToolbar.tsx` — search input, sort controls, add-chore button with proper ARIA labels
- [ ] T025 [P] [US2] Extract `ChoresGrid.tsx` from `solune/frontend/src/components/chores/ChoresPanel.tsx` into `solune/frontend/src/components/chores/ChoresGrid.tsx` — grid layout rendering ChoreCard items with stable keys (`key={chore.id}`)
- [ ] T026 [P] [US2] Extract `ChoresSaveAllBar.tsx` from `solune/frontend/src/components/chores/ChoresPanel.tsx` into `solune/frontend/src/components/chores/ChoresSaveAllBar.tsx` — save-all action bar for batch dirty edits with count indicator
- [ ] T027 [US2] Refactor `solune/frontend/src/components/chores/ChoresPanel.tsx` to compose extracted sub-components (ChoresToolbar, ChoresGrid, ChoresSaveAllBar) — verify ≤250 lines, no prop drilling >2 levels

### Decompose ChoreCard (584 → ≤250 + sub-components)

- [ ] T028 [US2] Extract `ChoreCardHeader.tsx` from `solune/frontend/src/components/chores/ChoreCard.tsx` into `solune/frontend/src/components/chores/ChoreCardHeader.tsx` — name (truncated with Tooltip), status badge, template path
- [ ] T029 [P] [US2] Extract `ChoreCardActions.tsx` from `solune/frontend/src/components/chores/ChoreCard.tsx` into `solune/frontend/src/components/chores/ChoreCardActions.tsx` — trigger, pause/resume, delete action buttons with aria-labels and disabled state during mutations
- [ ] T030 [P] [US2] Extract `ChoreCardStats.tsx` from `solune/frontend/src/components/chores/ChoreCard.tsx` into `solune/frontend/src/components/chores/ChoreCardStats.tsx` — execution count, last triggered (relative time), next checkpoint
- [ ] T031 [P] [US2] Extract `ChoreCardSettings.tsx` from `solune/frontend/src/components/chores/ChoreCard.tsx` into `solune/frontend/src/components/chores/ChoreCardSettings.tsx` — schedule config, pipeline selector, AI enhancement toggle
- [ ] T032 [US2] Refactor `solune/frontend/src/components/chores/ChoreCard.tsx` to compose extracted sub-components (ChoreCardHeader, ChoreCardActions, ChoreCardStats, ChoreCardSettings) — verify ≤250 lines, no prop drilling >2 levels

### Decompose AddChoreModal (356 → ≤250 + sub-components)

- [ ] T033 [US2] Extract `TemplateSelector.tsx` from `solune/frontend/src/components/chores/AddChoreModal.tsx` into `solune/frontend/src/components/chores/TemplateSelector.tsx` — template list with search and selection
- [ ] T034 [P] [US2] Extract `ChoreCreationForm.tsx` from `solune/frontend/src/components/chores/AddChoreModal.tsx` into `solune/frontend/src/components/chores/ChoreCreationForm.tsx` — name input, content editor, schedule config, submission
- [ ] T035 [US2] Refactor `solune/frontend/src/components/chores/AddChoreModal.tsx` to compose extracted sub-components (TemplateSelector, ChoreCreationForm) — verify ≤250 lines, modal shell with step flow

### Type Safety Audit

- [ ] T036 [P] [US2] Audit and eliminate all `any` types in `solune/frontend/src/components/chores/*.tsx` — replace with explicit types from `solune/frontend/src/types/index.ts`
- [ ] T037 [P] [US2] Audit and eliminate all type assertions (`as`) in `solune/frontend/src/components/chores/*.tsx` — replace with type guards or discriminated unions
- [ ] T038 [P] [US2] Audit and add explicit types to all event handlers in `solune/frontend/src/components/chores/*.tsx` — use `React.FormEvent<HTMLFormElement>`, `React.ChangeEvent<HTMLInputElement>`, etc. instead of generic types
- [ ] T039 [P] [US2] Audit and add explicit return types to custom hooks in `solune/frontend/src/hooks/useChores.ts` — ensure all 11 exports have inferrable or explicit return type annotations
- [ ] T040 [US2] Audit and extract any complex state logic (>15 lines of useState/useEffect/useCallback) from components into hooks in `solune/frontend/src/hooks/` — move business logic out of JSX render tree

**Checkpoint**: All component files ≤250 lines, zero `any` types, zero type assertions, no prop drilling >2 levels, business logic in hooks not JSX.

---

## Phase 5: User Story 3 — Accessible Chores Page (Priority: P2)

**Goal**: Ensure the Chores page is fully accessible — keyboard navigable, screen reader compatible, WCAG AA compliant — so all users can create, edit, schedule, trigger, and manage chores without barriers.

**Independent Test**: Navigate the entire page using only a keyboard, run an automated accessibility scanner, and verify screen reader announcements for all interactive elements including modals, toggles, and the inline editor.

### Implementation for User Story 3

- [ ] T041 [US3] Audit and fix keyboard navigation in `solune/frontend/src/components/chores/ChoresPanel.tsx` (and extracted ChoresToolbar) — verify Tab order through search input, sort controls, add-chore button; ensure Enter/Space activation on all controls
- [ ] T042 [P] [US3] Audit and fix focus management in `solune/frontend/src/components/chores/AddChoreModal.tsx` — verify focus trap when open, Escape key closes modal, focus returns to "Create Chore" button on close
- [ ] T043 [P] [US3] Audit and fix focus management in `solune/frontend/src/components/chores/ConfirmChoreModal.tsx` — verify `role="alertdialog"`, `aria-modal="true"`, focus trap, Escape cancels (does not confirm), focus returns to trigger on close
- [ ] T044 [P] [US3] Audit and fix ARIA attributes on status toggle (active/paused) in ChoreCard components — add `role="switch"`, `aria-checked`, `aria-label="Toggle chore status"`
- [ ] T045 [P] [US3] Audit and fix ARIA attributes on AI enhancement toggle in ChoreCard components — add `role="switch"`, `aria-checked`, `aria-label="Toggle AI enhancement"`
- [ ] T046 [P] [US3] Audit and fix ARIA attributes in `solune/frontend/src/components/chores/PipelineSelector.tsx` — add `aria-label="Select pipeline"`, `aria-expanded`, `role="option"` with `aria-selected`, Escape to close, keyboard navigation through options
- [ ] T047 [P] [US3] Audit and fix ARIA attributes in `solune/frontend/src/components/chores/ChoreScheduleConfig.tsx` — add labels on schedule type selector and value input, `aria-label` on all form fields
- [ ] T048 [US3] Audit and fix form field labels across all chores components — ensure every `<input>`, `<select>`, `<textarea>` (search input, schedule value, chore name, template content) has a visible label or `aria-label`
- [ ] T049 [US3] Audit and fix focus-visible styles across all interactive elements in `solune/frontend/src/components/chores/*.tsx` — ensure `celestial-focus` class or Tailwind `focus-visible:ring-*` classes are present
- [ ] T050 [US3] Audit and fix screen reader text across all chores components — ensure decorative icons have `aria-hidden="true"` and meaningful icons have `aria-label`
- [ ] T051 [US3] Audit and fix color contrast for status badges, muted text, and schedule indicators — verify WCAG AA 4.5:1 ratio for normal text, 3:1 for large text/UI components; ensure status communicated via icon + text, not color alone
- [ ] T101 [US3] Audit and fix accessibility of `CelestialCatalogHero` as used in `solune/frontend/src/pages/ChoresPage.tsx` — verify semantic heading hierarchy, ARIA attributes on stats/action elements, and keyboard accessibility of hero action buttons

**Checkpoint**: All interactive elements keyboard-accessible, modals trap focus, ARIA attributes complete, contrast ratios met, screen reader compatible, hero section accessible.

---

## Phase 6: User Story 4 — Polished Text, Copy, and User Experience (Priority: P2)

**Goal**: Ensure all text is clear, consistent, and helpful — with proper confirmation on destructive actions and meaningful feedback on all mutations.

**Independent Test**: Exercise every user-visible string, trigger all destructive actions, and verify confirmation dialogs and success/error feedback.

### Implementation for User Story 4

- [ ] T052 [US4] Audit all user-visible text in `solune/frontend/src/components/chores/*.tsx` — verify no placeholder text ("TODO", "Lorem ipsum", "Test") exists; all strings are final meaningful copy
- [ ] T053 [P] [US4] Audit and fix terminology consistency across all chores components — verify "chore" not "task", "pipeline" not "workflow", "trigger" not "run" throughout `solune/frontend/src/components/chores/*.tsx` and `solune/frontend/src/pages/ChoresPage.tsx`
- [ ] T054 [P] [US4] Audit and fix action button labels in ChoreCard action components — verify verb-based labels ("Trigger Chore", "Save Changes", "Delete Chore") not noun-based
- [ ] T055 [US4] Audit and fix destructive action confirmation — verify all delete/discard actions in ChoreCard and ChoreInlineEditor use `<ConfirmationDialog>` from `solune/frontend/src/components/ui/confirmation-dialog.tsx`, never immediate execution
- [ ] T056 [US4] Audit and fix mutation success feedback — verify all `useMutation` calls in `solune/frontend/src/hooks/useChores.ts` (create, update, delete, trigger, inline update, create-with-auto-merge, chat) provide success indication (toast, inline status change, or confirmation message)
- [ ] T057 [US4] Audit and fix error message format — verify all `onError` handlers in `solune/frontend/src/hooks/useChores.ts` produce messages following "Could not [action]. [Reason, if known]. [Suggested next step]." format with no raw error codes or stack traces
- [ ] T058 [P] [US4] Audit and fix long text truncation — verify chore names, template paths, and descriptions in ChoreCard and AddChoreModal use `text-ellipsis` with full text in `<Tooltip>` from `solune/frontend/src/components/ui/tooltip.tsx`
- [ ] T059 [P] [US4] Audit and fix timestamp formatting — verify `last_triggered_at` and `next_checkpoint` in ChoreCardStats use relative time ("2 hours ago") for recent times and absolute format for older times via `solune/frontend/src/utils/formatTime.ts`
- [ ] T102 [US4] Audit and fix session-expiry behavior during inline editing — verify that unsaved edits in `ChoreInlineEditor` are preserved when the user's session expires, and a re-authentication prompt appears without losing the user's work
- [ ] T103 [US4] Audit and fix network error handling in `solune/frontend/src/components/chores/ChoreChatFlow.tsx` — verify that a network error mid-conversation displays an error message with retry option and preserves conversation context

**Checkpoint**: All text is final copy, terminology consistent, destructive actions confirmed, mutations provide feedback, error messages are user-friendly, session-expiry and chat-flow errors handled gracefully.

---

## Phase 7: User Story 5 — Responsive Layout and Visual Consistency (Priority: P2)

**Goal**: Ensure the Chores page layout adapts gracefully across desktop (1280px+), tablet (768px–1279px), and mobile (<768px) and looks visually consistent with the Celestial design system.

**Independent Test**: Resize browser across all three breakpoints, verify layout adaptation, toggle dark mode, and compare styling with other application pages.

### Implementation for User Story 5

- [ ] T060 [US5] Audit and fix responsive grid layout in ChoresGrid — verify responsive column count (3–4 desktop, 2 tablet, 1 mobile) using Tailwind `sm:`, `md:`, `lg:` prefixes
- [ ] T061 [P] [US5] Audit and fix responsive layout in `solune/frontend/src/components/chores/FeaturedRitualsPanel.tsx` — verify three spotlight cards wrap correctly on smaller screens (row on desktop/tablet, stack on mobile)
- [ ] T062 [P] [US5] Audit and fix responsive layout in ChoresToolbar — verify search input and sort controls stack vertically on mobile
- [ ] T063 [P] [US5] Audit and fix touch targets in ChoreCardActions — verify trigger, edit, delete buttons meet minimum 44×44px touch targets on mobile
- [ ] T064 [P] [US5] Audit and fix modal responsiveness in `solune/frontend/src/components/chores/AddChoreModal.tsx` and `solune/frontend/src/components/chores/ConfirmChoreModal.tsx` — verify full-width on mobile
- [ ] T065 [US5] Audit and fix dark mode compliance across all chores components — verify no hardcoded colors (`#fff`, `bg-white`, `text-black`), all use Tailwind `dark:` variants or CSS variables from `solune/frontend/src/index.css`
- [ ] T066 [US5] Audit and fix Tailwind utility compliance across all chores components — verify no inline `style={}` attributes, all conditional classes use `cn()` from `solune/frontend/src/lib/utils.ts`, spacing uses Tailwind scale (no arbitrary `p-[13px]` values)
- [ ] T067 [US5] Audit and fix card consistency in ChoreCard — verify uses `<Card>` from `solune/frontend/src/components/ui/card.tsx` with consistent padding/rounding matching other pages
- [ ] T104 [US5] Audit and verify page legibility at 320px viewport width — verify no critical elements are cut off or overlapping and the page remains usable at extreme narrow widths
- [ ] T105 [US5] Audit and fix touch targets across all interactive elements (search input, sort controls, filter buttons, modal controls, inline editor buttons) — verify all meet minimum 44×44px size on touch-capable screens per FR-009, not just ChoreCardActions
- [ ] T106 [US5] Audit and verify hover states on all interactive elements in chores components — verify buttons, cards, toggles, and links show visual hover feedback using Tailwind `hover:` variants consistent with other pages per FR-004
- [ ] T107 [P] [US5] Audit and fix responsive behavior of `CelestialCatalogHero` in `solune/frontend/src/pages/ChoresPage.tsx` — verify hero stats and action buttons adapt correctly across desktop/tablet/mobile breakpoints

**Checkpoint**: Layout adapts at all breakpoints including 320px, dark mode renders correctly, all styles use Tailwind utilities and design tokens, all touch targets meet 44×44px minimum, hover states present on all interactive elements.

---

## Phase 8: User Story 6 — Data Fetching Best Practices and Performance (Priority: P2)

**Goal**: Ensure all API calls use TanStack Query with proper caching, no duplicate requests, and the page remains responsive with 50+ chores.

**Independent Test**: Profile network requests during page load and interaction, verify query key conventions, check staleTime, and confirm no duplicate API calls.

### Implementation for User Story 6

- [ ] T068 [US6] Audit and verify all API calls in `solune/frontend/src/hooks/useChores.ts` use `useQuery`/`useMutation` from TanStack React Query — verify no raw `useEffect` + `fetch` patterns exist anywhere in `solune/frontend/src/components/chores/*.tsx`
- [ ] T069 [P] [US6] Audit and verify query key conventions in `solune/frontend/src/hooks/useChores.ts` — verify `choreKeys` factory follows `choreKeys.all` / `choreKeys.list(projectId)` / `choreKeys.templates(projectId)` convention consistent with `pipelineKeys`, `appKeys` examples
- [ ] T070 [P] [US6] Audit and fix staleTime configuration in `solune/frontend/src/hooks/useChores.ts` — add `staleTime: 30_000` for chores list queries and `staleTime: 60_000` for template queries if not already configured
- [ ] T071 [US6] Audit and verify no duplicate API calls between `solune/frontend/src/pages/ChoresPage.tsx`, `solune/frontend/src/components/chores/ChoresPanel.tsx`, and child components — ensure chores list fetched once at appropriate level and shared via props
- [ ] T072 [US6] Audit and fix mutation error handling in `solune/frontend/src/hooks/useChores.ts` — verify all 8 mutations (`useCreateChore`, `useUpdateChore`, `useDeleteChore`, `useTriggerChore`, `useChoreChat`, `useInlineUpdateChore`, `useCreateChoreWithAutoMerge`, seed presets) have `onError` with user-visible feedback
- [ ] T073 [P] [US6] Audit and verify mutation success handling in `solune/frontend/src/hooks/useChores.ts` — verify successful mutations call `invalidateQueries` with appropriate `choreKeys` to refresh the chore list
- [ ] T074 [P] [US6] Audit and verify evaluate-triggers polling efficiency in `solune/frontend/src/hooks/useChores.ts` — verify 60s polling interval respects component unmount (no memory leak)
- [ ] T075 [US6] Audit and fix performance for large lists — verify ChoreCard components use `React.memo()` or equivalent with stable callback references via `useCallback` from parent; verify `key={chore.id}` (not `key={index}`) on list renders; verify sorting/filtering wrapped in `useMemo`
- [ ] T076 [US6] Audit rapid-click prevention on trigger button in ChoreCardActions — verify button disabled during `useTriggerChore` mutation (`isPending` state) to prevent duplicate triggers

**Checkpoint**: All API calls use React Query, proper caching, no duplicates, mutations have error/success handling, performance optimized.

---

## Phase 9: User Story 7 — Comprehensive Test Coverage (Priority: P3)

**Goal**: Ensure thorough automated test coverage for hooks, components, and edge cases to catch regressions after audit refactoring.

**Independent Test**: Run `cd solune/frontend && npx vitest run src/components/chores/ src/hooks/useChores` — all pass with coverage of happy path, error, loading, empty, rate-limit, and edge cases.

### Hook Tests

- [ ] T077 [US7] Write or update hook tests for `useChoresList` in `solune/frontend/src/hooks/__tests__/useChores.test.ts` — cover happy path (returns chore list), loading state, error state, empty state, and rate-limit error using `renderHook()` with mocked API via `vi.mock('@/services/api', ...)`
- [ ] T078 [P] [US7] Write or update hook tests for `useChoreTemplates` in `solune/frontend/src/hooks/__tests__/useChores.test.ts` — cover happy path (returns templates), loading state, error state, and empty state
- [ ] T079 [P] [US7] Write or update hook tests for mutation hooks (`useCreateChore`, `useDeleteChore`, `useTriggerChore`, `useInlineUpdateChore`) in `solune/frontend/src/hooks/__tests__/useChores.test.ts` — cover success with query invalidation, error with user feedback, and loading states

### Component Tests

- [ ] T080 [US7] Update `solune/frontend/src/components/chores/__tests__/ChoresPanel.test.tsx` — add tests for search filtering, sort toggling, empty search results state, and save-all bar interaction after ChoresPanel decomposition
- [ ] T081 [P] [US7] Write component tests for ChoreCard (and extracted sub-components) in `solune/frontend/src/components/chores/__tests__/ChoreCard.test.tsx` — cover trigger button click (disabled during mutation), pause/resume toggle, delete with confirmation dialog, inline editor toggle
- [ ] T082 [P] [US7] Update `solune/frontend/src/components/chores/__tests__/AddChoreModal.test.tsx` — add tests for template selection, form validation, modal open/close with focus management after AddChoreModal decomposition
- [ ] T083 [P] [US7] Update `solune/frontend/src/components/chores/__tests__/FeaturedRitualsPanel.test.tsx` — add tests for empty chores (null spotlight), relative time display, and all three spotlight categories

### Edge Case Tests

- [ ] T084 [US7] Write edge case tests in `solune/frontend/src/components/chores/__tests__/ChoreEdgeCases.test.tsx` — cover rate-limit error rendering, 200-character chore name truncation with tooltip, null `last_triggered_at` / `next_checkpoint` handling, rapid trigger button clicks, partial save-all failure indication, deleted-pipeline fallback display, session-expiry edit preservation, ChoreChatFlow network error mid-conversation, and 320px viewport rendering
- [ ] T085 [US7] Verify all test patterns follow codebase conventions — uses `vi.mock('@/services/api', ...)`, `renderHook`, `waitFor`, `createWrapper()`, assertion-based tests (no snapshot tests)

**Checkpoint**: All hooks tested, key components tested, edge cases covered, zero snapshot tests, all tests pass.

---

## Phase 10: User Story 8 — Clean Code and Zero Lint Violations (Priority: P3)

**Goal**: Ensure Chores page code is clean, well-organized, and free of lint violations.

**Independent Test**: Run ESLint on all Chores files with zero warnings/errors, TypeScript compiler with zero errors, and verify no dead code, console.log, relative imports, or magic strings.

### Implementation for User Story 8

- [ ] T086 [US8] Remove all dead code from `solune/frontend/src/components/chores/*.tsx` — unused imports, commented-out blocks, unreachable branches
- [ ] T087 [P] [US8] Remove all `console.log` statements from `solune/frontend/src/components/chores/*.tsx`, `solune/frontend/src/pages/ChoresPage.tsx`, and `solune/frontend/src/hooks/useChores.ts`
- [ ] T088 [P] [US8] Convert all relative imports to `@/` alias in `solune/frontend/src/components/chores/*.tsx` — replace any `../../` paths with `@/components/...`, `@/hooks/...`, `@/services/...`, `@/types/...`
- [ ] T089 [P] [US8] Extract magic strings to constants — define repeated strings (chore status values, query keys, route paths, tooltip keys) as constants in `solune/frontend/src/constants/` or at the top of relevant files
- [ ] T090 [US8] Run ESLint on all chores files via `npx eslint solune/frontend/src/pages/ChoresPage.tsx solune/frontend/src/components/chores/ solune/frontend/src/hooks/useChores.ts` — fix all warnings and errors to reach zero
- [ ] T091 [US8] Run TypeScript compiler via `cd solune/frontend && npm run type-check` — fix all type errors in chores-related files to reach zero

**Checkpoint**: Zero dead code, zero console.log, all @/ imports, no magic strings, ESLint clean, TypeScript clean.

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, audit summary, and cross-cutting improvements that affect multiple user stories

- [ ] T092 Verify file naming conventions — all new extracted components are PascalCase `.tsx` in `solune/frontend/src/components/chores/`, hooks are `use*.ts` in `solune/frontend/src/hooks/`
- [ ] T093 [P] Run full test suite via `cd solune/frontend && npx vitest run` — verify all tests pass including new and updated tests
- [ ] T094 [P] Run full lint check via `cd solune/frontend && npm run lint` — verify zero warnings and zero errors
- [ ] T095 [P] Run full type check via `cd solune/frontend && npm run type-check` — verify zero type errors
- [ ] T096 Produce audit summary document listing: all findings from Phase 2 assessment, all changes made (with file references), all improvements deferred for future work (with justification), per FR-023
- [ ] T097 Run `specs/043-chores-page-audit/quickstart.md` validation — execute all verification steps (lint, type-check, test, browser check at multiple viewports, keyboard navigation, screen reader labels)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 assessment — start with page states before decomposition
- **US2 (Phase 4)**: Depends on Phase 2 assessment — component decomposition is the largest structural change
- **US3 (Phase 5)**: Depends on US2 completion (accessibility fixes target decomposed components)
- **US4 (Phase 6)**: Depends on US2 completion (text/copy fixes target decomposed components)
- **US5 (Phase 7)**: Depends on US2 completion (responsive fixes target decomposed components)
- **US6 (Phase 8)**: Can start after Phase 2 — data fetching audit is independent of decomposition
- **US7 (Phase 9)**: Depends on US1 + US2 completion (tests target final component structure)
- **US8 (Phase 10)**: Depends on US1–US6 completion (code hygiene is final cleanup)
- **Polish (Phase 11)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no dependencies on other stories
- **US2 (P1)**: Can start after Phase 2 — no dependencies on other stories, but US1 may overlap
- **US3 (P2)**: Best after US2 (accessibility fixes apply to final component structure)
- **US4 (P2)**: Best after US2 (text/copy fixes apply to final component structure)
- **US5 (P2)**: Best after US2 (responsive fixes apply to final component structure)
- **US6 (P2)**: Can start after Phase 2 — hooks/API audit is independent of component decomposition
- **US7 (P3)**: MUST wait for US1 + US2 (tests target final, stable code)
- **US8 (P3)**: MUST wait for US1–US6 (cleanup is the final pass)

### Within Each User Story

- Assessment findings (Phase 2) inform which tasks need "fix" vs. "verify"
- Decomposition (US2) must complete sub-component extraction before integration refactor
- Tests (US7) should be written against the final post-decomposition component structure
- Code hygiene (US8) is always the last step before validation

### Parallel Opportunities

- Phase 2: T007–T014, T098 can all run in parallel (independent file reads)
- US2 ChoresPanel decomposition: T025, T026 can run in parallel (different new files)
- US2 ChoreCard decomposition: T029, T030, T031 can run in parallel (different new files)
- US2 Type safety: T036, T037, T038, T039 can all run in parallel (different audit scopes)
- US3 Accessibility: T042, T043, T044, T045, T046, T047 can all run in parallel (different components)
- US4 Text/Copy: T053, T054, T058, T059 can run in parallel (different audit scopes)
- US5 Responsive: T061, T062, T063, T064, T107 can run in parallel (different components)
- US6 Data Fetching: T069, T070, T073, T074 can run in parallel (different audit scopes)
- US7 Tests: T078, T079, T081, T082, T083 can run in parallel (different test files)
- US8 Code Hygiene: T087, T088, T089 can run in parallel (different cleanup scopes)

---

## Parallel Example: User Story 2 (Component Decomposition)

```bash
# Launch ChoresPanel sub-component extraction in parallel:
Task T025: "Extract ChoresGrid.tsx from ChoresPanel.tsx"
Task T026: "Extract ChoresSaveAllBar.tsx from ChoresPanel.tsx"

# Then sequential: T027 refactors main ChoresPanel.tsx to compose them

# Launch ChoreCard sub-component extraction in parallel:
Task T029: "Extract ChoreCardActions.tsx from ChoreCard.tsx"
Task T030: "Extract ChoreCardStats.tsx from ChoreCard.tsx"
Task T031: "Extract ChoreCardSettings.tsx from ChoreCard.tsx"

# Then sequential: T032 refactors main ChoreCard.tsx to compose them

# Launch type safety audits in parallel:
Task T036: "Eliminate any types in chores components"
Task T037: "Eliminate type assertions in chores components"
Task T038: "Add explicit event handler types"
Task T039: "Add explicit hook return types"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational assessment
3. Complete Phase 3: US1 — Page states (loading, error, empty, rate-limit)
4. Complete Phase 4: US2 — Component decomposition + type safety
5. **STOP and VALIDATE**: All page states correct, all files ≤250 lines, zero `any` types
6. Run `npx vitest run` + `npm run lint` + `npm run type-check`

### Incremental Delivery

1. Setup + Foundational → Assessment complete
2. US1 → All page states verified → Deploy/Demo (page works correctly in all states)
3. US2 → Components decomposed + type-safe → Deploy/Demo (code quality improved)
4. US3 → Accessible → Deploy/Demo (WCAG AA compliant)
5. US4 → Polished text/UX → Deploy/Demo (professional user experience)
6. US5 → Responsive → Deploy/Demo (works on all devices)
7. US6 → Optimized data fetching → Deploy/Demo (fast and efficient)
8. US7 → Tests added → Deploy/Demo (regression-safe)
9. US8 → Clean code → Deploy/Demo (zero lint, zero type errors)
10. Polish → Audit summary → Final validation

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once assessment is done:
   - Developer A: US1 (Page States) + US2 (Decomposition) — P1 MVP
   - Developer B: US6 (Data Fetching) — independent of decomposition
3. After US2 completes:
   - Developer A: US3 (Accessibility) + US4 (Text/Copy)
   - Developer B: US5 (Responsive) + US7 (Tests)
4. Final pass: US8 (Clean Code) + Polish

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- This is a frontend-only audit — no backend changes required
- Three components require decomposition: ChoresPanel (543→≤250), ChoreCard (584→≤250), AddChoreModal (356→≤250)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same-file conflicts, unnecessary cross-story dependencies. Structural dependencies (e.g., US3–US5 depend on US2 decomposition, US7 tests target final code) are documented in the Dependencies section above
- **Total tasks**: 107 (T001–T097 + T098–T107)
- **Analysis remediation**: Tasks T098–T107 address coverage gaps F2–F7 and F16 identified in `analysis-report.md`. Path prefix drift (F1) is consistent at `solune/frontend/src/` throughout tasks.md. Component list mismatch (F15) is covered by T010 (assesses ChoreInlineEditor, PipelineSelector) and T098 (assesses CelestialCatalogHero)
