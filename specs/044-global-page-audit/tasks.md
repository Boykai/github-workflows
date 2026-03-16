# Tasks: Global Page Audit

**Input**: Design documents from `/specs/044-global-page-audit/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests are REQUIRED by the feature specification in US6 (P3) — SC-010 mandates dedicated test coverage for useGlobalSettings hook and key interactive sub-components. Test tasks are included in the US6 phase.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. The Global Settings section is already well-structured (88-line container, 5 sub-sections, zod schema, TanStack Query hooks), so the audit focuses on state handling, accessibility, UX polish, dirty-state reliability, responsive layout, and code quality/testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Frontend**: `solune/frontend/src/`
- **Components**: `solune/frontend/src/components/settings/`
- **Hooks**: `solune/frontend/src/hooks/`
- **Tests**: Co-located with source files (`.test.tsx` / `.test.ts`)

---

## Phase 1: Setup (Discovery & Assessment)

**Purpose**: Establish baseline state and identify all issues before making changes

- [x] T001 Run baseline lint via `cd solune/frontend && npm run lint` and save output to identify pre-existing warnings in settings files
- [x] T002 [P] Run baseline type-check via `cd solune/frontend && npm run type-check` and save output to identify pre-existing type errors
- [x] T003 [P] Run baseline tests via `cd solune/frontend && npx vitest run` and save output to establish passing test baseline
- [x] T004 [P] Audit `solune/frontend/src/pages/SettingsPage.tsx` (107 lines) — note line count, identify loading/error state handling, check how global settings section is rendered and isolated from user settings failures
- [x] T005 [P] Audit `solune/frontend/src/components/settings/GlobalSettings.tsx` (88 lines) — note line count, identify inline Allowed Models input (lines 69-84), check form validation error rendering, check react-hook-form + zod integration
- [x] T006 [P] Audit `solune/frontend/src/components/settings/SettingsSection.tsx` (100 lines) — note collapsible behavior, save/error/success messaging, aria-expanded usage, focus management
- [x] T007 [P] Audit `solune/frontend/src/components/settings/AISettingsSection.tsx` (56 lines), `DisplaySettings.tsx` (55 lines), `WorkflowSettings.tsx` (53 lines), `NotificationSettings.tsx` (58 lines) — check form field labels, aria attributes, keyboard accessibility
- [x] T008 [P] Audit `solune/frontend/src/components/settings/globalSettingsSchema.ts` (83 lines) — verify flatten/toUpdate handle null nested fields, check schema defaults, validate allowed_models parsing
- [x] T009 [P] Audit `solune/frontend/src/hooks/useSettings.ts` (302 lines) — check useGlobalSettings hook for error handling, mutation onError callbacks, cache invalidation on save, staleTime configuration
- [x] T010 Produce audit findings table — score each checklist item (Pass/Fail/N/A) from parent issue against the Global Settings codebase, document all issues to fix organized by user story

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared infrastructure changes that MUST be complete before user story work begins

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T011 Verify `solune/frontend/src/hooks/useSettings.ts` — confirm useGlobalSettings mutation has `onError` callback that surfaces user-visible feedback (toast or inline error). If missing, add error handling to the mutation
- [x] T012 [P] Verify `solune/frontend/src/components/settings/globalSettingsSchema.ts` — confirm `flatten()` handles null/missing nested fields (e.g., `settings.ai` is null) gracefully with schema defaults. If not, add null guards
- [x] T013 [P] Verify `solune/frontend/src/components/settings/globalSettingsSchema.ts` — confirm `toUpdate()` correctly trims whitespace and filters empty entries from allowed_models comma-separated input. If not, add cleaning logic
- [x] T014 [P] Verify `solune/frontend/src/services/api.ts` — confirm settings API calls use proper TypeScript types for request/response with no `any` types in the settings group
- [x] T015 Remove any `console.log` statements, dead code, or unused imports from all Global Settings-related files: `SettingsPage.tsx`, `GlobalSettings.tsx`, `SettingsSection.tsx`, `AISettingsSection.tsx`, `DisplaySettings.tsx`, `WorkflowSettings.tsx`, `NotificationSettings.tsx`, `globalSettingsSchema.ts`, `useSettings.ts`

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Bug-Free and Complete Page States (Priority: P1) 🎯 MVP

**Goal**: The Global Settings section displays correctly in every state — loading, populated, saving, save success, save error, rate limit error, and validation error — with appropriate messaging and recovery actions.

**Independent Test**: Trigger each section state (loading, populated, save in progress, save success, save error, rate limit error, validation error) and verify that each renders correctly with appropriate messaging and recovery.

### Implementation for User Story 1

- [x] T016 [US1] Verify loading state in `solune/frontend/src/pages/SettingsPage.tsx` — confirm CelestialLoader is displayed while global settings are being fetched, with no blank area or layout shift. If the Global Settings section lacks its own loading indicator, add one using `<CelestialLoader size="md" />`
- [x] T017 [P] [US1] Verify error state in `solune/frontend/src/components/settings/SettingsSection.tsx` — confirm API errors render user-friendly messages following "Could not [action]. [Reason]. [Suggested next step]." format. Add retry action if missing
- [x] T018 [P] [US1] Add rate limit error detection in the Global Settings save flow — use `isRateLimitApiError()` utility in `solune/frontend/src/hooks/useSettings.ts` (useGlobalSettings mutation onError) to detect rate limit errors and display a specific message advising the user to wait before retrying
- [x] T019 [US1] Verify validation error rendering in `solune/frontend/src/components/settings/GlobalSettings.tsx` — confirm react-hook-form validation errors from zod schema are displayed inline next to the relevant fields and that save is prevented until errors are resolved. If missing, add inline error messages below each field using `formState.errors`
- [x] T020 [P] [US1] Verify partial loading isolation in `solune/frontend/src/pages/SettingsPage.tsx` — confirm that when the global settings API call fails, the Global Settings section shows its own error state while user settings sections continue to function normally. Fix if error propagates across sections
- [x] T021 [US1] Verify save-in-progress state in `solune/frontend/src/components/settings/SettingsSection.tsx` — confirm the save button is disabled during mutation and shows saving indicator. Confirm the button is disabled while a save request is in flight to prevent duplicate API calls
- [x] T022 [US1] Run lint, type-check, and tests to validate US1 changes — `cd solune/frontend && npm run lint && npm run type-check && npx vitest run`

**Checkpoint**: All page states render correctly with appropriate messaging. US1 is independently testable and complete.

---

## Phase 4: User Story 2 — Accessible Global Settings (Priority: P1)

**Goal**: The Global Settings section is fully accessible via keyboard, screen reader, and assistive technology.

**Independent Test**: Navigate the entire Global Settings section using only a keyboard, run an automated accessibility scanner, and verify screen reader announcements for all form controls.

### Implementation for User Story 2

- [x] T023 [US2] Audit and fix keyboard navigation in all Global Settings form fields — verify Tab order through section collapse toggle, provider dropdown, model input, temperature slider, theme dropdown, default view dropdown, sidebar checkbox, repository input, assignee input, polling interval input, notification checkboxes, allowed models input, and save button in `solune/frontend/src/components/settings/GlobalSettings.tsx` and all sub-sections
- [x] T024 [P] [US2] Add `aria-expanded` attribute to the collapsible section toggle in `solune/frontend/src/components/settings/SettingsSection.tsx` — confirm it correctly reflects open/closed state and screen readers announce the state change
- [x] T025 [P] [US2] Verify form field labels in `solune/frontend/src/components/settings/AISettingsSection.tsx` — confirm all inputs have associated `<label>` elements with `htmlFor` or `aria-label`. Add missing labels
- [x] T026 [P] [US2] Verify form field labels in `solune/frontend/src/components/settings/DisplaySettings.tsx` — confirm all selects and checkboxes have associated labels. Add missing labels
- [x] T027 [P] [US2] Verify form field labels in `solune/frontend/src/components/settings/WorkflowSettings.tsx` — confirm all text inputs and number inputs have associated labels. Add missing labels
- [x] T028 [P] [US2] Verify form field labels in `solune/frontend/src/components/settings/NotificationSettings.tsx` — confirm all checkboxes have associated labels. Add missing labels
- [x] T029 [US2] Add `aria-valuetext` or equivalent accessible value announcement to the temperature slider in `solune/frontend/src/components/settings/AISettingsSection.tsx` — ensure assistive technology announces the current value when adjusted
- [x] T030 [P] [US2] Verify dropdown keyboard navigation for provider, theme, and default view selects — confirm arrow keys navigate options, Enter selects, Escape closes. Fix in relevant sub-section files if broken
- [x] T031 [US2] Add programmatic error association — when validation errors are displayed, ensure each error message is linked to its input field via `aria-describedby` in `solune/frontend/src/components/settings/GlobalSettings.tsx` and sub-sections
- [x] T032 [P] [US2] Verify focus-visible styles — confirm all interactive elements in Global Settings use `focus-visible:` ring or `celestial-focus` class. Add missing focus styles
- [x] T033 [P] [US2] Verify decorative icons have `aria-hidden="true"` and meaningful icons have `aria-label` across all Global Settings components
- [x] T034 [US2] Run lint, type-check, and tests to validate US2 changes — `cd solune/frontend && npm run lint && npm run type-check && npx vitest run`

**Checkpoint**: All Global Settings form elements are keyboard-accessible, properly labeled, and screen-reader-friendly. US2 is independently testable and complete.

---

## Phase 5: User Story 3 — Consistent and Polished User Experience (Priority: P2)

**Goal**: The Global Settings section looks and feels consistent with the rest of the application, with professional copy, proper feedback, and a polished interface.

**Independent Test**: Compare the Global Settings section visually against other settings sections, verify all user-visible text is final and consistent, validate success feedback on save.

### Implementation for User Story 3

- [x] T035 [US3] Audit all user-visible text in Global Settings components — check field labels, descriptions, placeholder text, and tooltips in `solune/frontend/src/components/settings/AISettingsSection.tsx`, `DisplaySettings.tsx`, `WorkflowSettings.tsx`, `NotificationSettings.tsx`, and `GlobalSettings.tsx` for placeholder text (no "TODO", "Lorem ipsum", "Test") and consistent terminology
- [x] T036 [P] [US3] Verify save button label in `solune/frontend/src/components/settings/SettingsSection.tsx` uses a clear verb phrase (e.g., "Save Settings") rather than a generic noun. Fix if needed
- [x] T037 [P] [US3] Verify success feedback on save — confirm that `solune/frontend/src/components/settings/SettingsSection.tsx` shows clear success feedback (toast, inline message, or status indicator) after a successful save. Fix if missing or unclear
- [x] T038 [P] [US3] Verify error messages are user-friendly — confirm all error messages in the Global Settings save flow follow "Could not [action]. [Reason]. [Suggested next step]." format with no raw error codes or stack traces
- [x] T039 [US3] Verify dark mode support — confirm all Global Settings elements (form controls, labels, collapsible panel, save button) use Tailwind `dark:` variants or CSS variables from the theme in all component files. Fix any hardcoded colors (`#fff`, `bg-white`, etc.)
- [x] T040 [P] [US3] Verify design token consistency — confirm the Global Settings section uses the same typography, spacing, and color tokens as other settings sections. Check for off-palette or hardcoded color values using `cn()` from `solune/frontend/src/lib/utils.ts`
- [x] T041 [P] [US3] Add tooltips or help text for technical fields — if field labels include technical terms (e.g., "Temperature", "Polling Interval", "Allowed Models"), add `<Tooltip>` from `solune/frontend/src/components/ui/tooltip.tsx` with brief explanations
- [x] T042 [US3] Run lint, type-check, and tests to validate US3 changes — `cd solune/frontend && npm run lint && npm run type-check && npx vitest run`

**Checkpoint**: All user-visible text is final, consistent, and professional. Dark mode and design tokens correct. US3 is independently testable and complete.

---

## Phase 6: User Story 4 — Reliable Settings Editing with Dirty State Tracking (Priority: P2)

**Goal**: The form tracks unsaved changes accurately and protects users from accidental data loss.

**Independent Test**: Edit Global Settings fields, verify save button enables/disables based on dirty state, attempt to navigate away to confirm unsaved-changes guard activates.

### Implementation for User Story 4

- [x] T043 [US4] Verify save button disabled/enabled state in `solune/frontend/src/components/settings/GlobalSettings.tsx` and `SettingsSection.tsx` — confirm the save button is disabled when form is in saved state (no changes) and enabled when dirty state is detected
- [x] T044 [P] [US4] Verify unsaved-changes warning in `solune/frontend/src/pages/SettingsPage.tsx` — confirm the `beforeunload` listener activates when Global Settings have pending edits and the user attempts to navigate away. Fix if the dirty state from GlobalSettings is not properly propagated to the page-level guard
- [x] T045 [US4] Verify form reset after save — confirm that after a successful save in `solune/frontend/src/components/settings/GlobalSettings.tsx`, the form resets its dirty state (via react-hook-form `reset()`), the save button returns to disabled, and the user settings cache is invalidated in `solune/frontend/src/hooks/useSettings.ts`
- [x] T046 [P] [US4] Verify revert detection — confirm that when a user modifies the temperature slider (or any field) and then reverts it to the original value, the form correctly detects no changes and the save button remains disabled. Test with react-hook-form's dirty field tracking
- [x] T047 [US4] Verify save button is disabled during in-flight mutation — confirm `solune/frontend/src/components/settings/SettingsSection.tsx` disables the save button while `isPending` is true to prevent duplicate API calls
- [x] T048 [US4] Run lint, type-check, and tests to validate US4 changes — `cd solune/frontend && npm run lint && npm run type-check && npx vitest run`

**Checkpoint**: Dirty state tracking is accurate, unsaved-changes guard works, and save button state is correct. US4 is independently testable and complete.

---

## Phase 7: User Story 5 — Responsive Layout Across Screen Sizes (Priority: P2)

**Goal**: The Global Settings section adapts gracefully from 768px to 1920px without horizontal scrolling or overlapping elements.

**Independent Test**: Resize browser across 768px, 1280px, and 1920px breakpoints and verify form fields, labels, collapsible sections, and save button adapt their layout.

### Implementation for User Story 5

- [x] T049 [US5] Audit responsive layout of `solune/frontend/src/components/settings/GlobalSettings.tsx` — verify form fields stack correctly at 768px, use available space at 1920px, and transition smoothly between breakpoints. Fix any overflow, overlap, or truncation issues
- [x] T050 [P] [US5] Audit responsive layout of `solune/frontend/src/components/settings/AISettingsSection.tsx` — verify the provider dropdown, model input, and temperature slider adapt at different viewport widths. Fix layout issues
- [x] T051 [P] [US5] Audit responsive layout of `solune/frontend/src/components/settings/DisplaySettings.tsx` and `WorkflowSettings.tsx` — verify form fields reflow appropriately at narrow viewports. Fix layout issues
- [x] T052 [P] [US5] Audit responsive layout of `solune/frontend/src/components/settings/NotificationSettings.tsx` — verify checkbox grid/list adapts at narrow viewports. Fix layout issues
- [x] T053 [US5] Verify no inline `style={}` attributes across all Global Settings components — confirm all styling uses Tailwind utility classes with `cn()` for conditional classes. Replace any inline styles found
- [x] T054 [US5] Verify consistent spacing — confirm all Global Settings components use Tailwind spacing scale (`gap-4`, `p-6`) with no arbitrary values like `p-[13px]`. Fix any non-standard spacing
- [x] T055 [US5] Run lint, type-check, and tests to validate US5 changes — `cd solune/frontend && npm run lint && npm run type-check && npx vitest run`

**Checkpoint**: Layout is responsive and correct across all supported viewports. US5 is independently testable and complete.

---

## Phase 8: User Story 6 — Maintainable and Well-Tested Global Settings Code (Priority: P3)

**Goal**: The Global Settings code follows best practices for component structure, state management, type safety, and has adequate test coverage.

**Independent Test**: Review component structure, run type checking with zero errors, run linting with zero warnings, run test suite with all tests passing.

### Structure & Type Safety

- [x] T056 [US6] Verify GlobalSettings component line count — `solune/frontend/src/components/settings/GlobalSettings.tsx` must be ≤250 lines. If over, extract sections (e.g., AllowedModelsField) into `solune/frontend/src/components/settings/AllowedModelsField.tsx`
- [x] T057 [P] [US6] Verify prop drilling depth — trace prop passing through GlobalSettings → sub-sections. Confirm no prop is drilled through more than two levels. If found, refactor to use composition, context, or hook extraction
- [x] T058 [P] [US6] Audit `solune/frontend/src/hooks/useSettings.ts` (302 lines) — if Global Settings hooks can be cleanly separated from signal hooks, consider extracting signal-specific hooks to reduce file complexity. Only refactor if it improves maintainability without breaking imports
- [x] T059 [P] [US6] Verify type safety — audit all Global Settings-related files for `any` types and unsafe type assertions (`as`). Replace with proper types, type guards, or discriminated unions
- [x] T060 [P] [US6] Verify all imports use `@/` alias — audit all Global Settings-related files for relative imports (`../../`). Replace with `@/components/...`, `@/hooks/...`, `@/services/...` paths
- [x] T061 [P] [US6] Verify no magic strings — audit all Global Settings-related files for repeated strings (status values, query keys, route paths). Move to constants if found

### Test Coverage

- [x] T062 [US6] Create test file for useGlobalSettings hook — `solune/frontend/src/hooks/useGlobalSettings.test.ts` — test happy path (fetch + display), save mutation success, save mutation error, rate limit error detection, cache invalidation after save, using `renderHook`, `vi.mock('@/services/api', ...)`, and `createWrapper()` patterns from existing tests
- [x] T063 [P] [US6] Create test file for GlobalSettings component — `solune/frontend/src/components/settings/GlobalSettings.test.tsx` — test form rendering with populated data, form submission, validation error display, and dirty state tracking using existing test patterns
- [x] T064 [P] [US6] Create test file for globalSettingsSchema utilities — `solune/frontend/src/components/settings/globalSettingsSchema.test.ts` — test `flatten()` with null nested fields, `toUpdate()` with whitespace/empty allowed_models, schema validation for temperature range (0-2), polling interval minimum (≥0)
- [x] T065 [P] [US6] Augment existing `solune/frontend/src/components/settings/SettingsSection.test.tsx` — add test cases for rate limit error display, retry action, and aria-expanded attribute if not already covered

### Validation

- [x] T066 [US6] Run full lint check on all Global Settings files — `cd solune/frontend && npx eslint src/pages/SettingsPage.tsx src/components/settings/ src/hooks/useSettings.ts` — must produce 0 warnings
- [x] T067 [P] [US6] Run type check — `cd solune/frontend && npm run type-check` — must produce 0 type errors in Global Settings files
- [x] T068 [US6] Run full test suite — `cd solune/frontend && npx vitest run` — all tests must pass including new tests from T062-T065

**Checkpoint**: Code structure is clean, types are safe, lint is clean, and all tests pass with dedicated coverage for useGlobalSettings and GlobalSettings. US6 is independently testable and complete.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all user stories

- [x] T069 Run full frontend validation suite — `cd solune/frontend && npm run lint && npm run type-check && npx vitest run && npm run build`
- [x] T070 [P] Verify no regressions in non-Global-Settings sections of the Settings page — confirm PrimarySettings, AdvancedSettings, ProjectSettings, and user-level settings sections still function correctly after all audit changes
- [x] T071 Compile audit summary — list every issue found and fixed, organized by audit checklist category (Architecture, Data Fetching, States, Type Safety, a11y, UX, Styling, Performance, Tests, Code Hygiene). Note any deferred improvements for future work
- [x] T072 Cross-reference all changes against the 26 functional requirements (FR-001 through FR-026) in spec.md — confirm each is addressed or explicitly marked N/A with rationale

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1: Page States (Phase 3)**: Depends on Foundational completion
- **US2: Accessibility (Phase 4)**: Depends on Foundational completion — can run in parallel with US1
- **US3: UX Polish (Phase 5)**: Depends on Foundational completion — can run in parallel with US1/US2
- **US4: Dirty State (Phase 6)**: Depends on Foundational completion — can run in parallel with US1/US2/US3
- **US5: Responsive (Phase 7)**: Depends on Foundational completion — can run in parallel with US1-US4
- **US6: Code Quality (Phase 8)**: Depends on US1-US5 completion — code changes must stabilize before structural/testing work
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)** and **US2 (P1)**: Can start in parallel after Foundational phase — both are P1 priority
- **US3 (P2)**, **US4 (P2)**, **US5 (P2)**: Can start in parallel after Foundational phase — independent P2 stories
- **US6 (P3)**: Should wait for US1-US5 to stabilize — test and structure work best done after functional changes

### Within Each User Story

- Audit/assess first, then fix
- Core implementation before edge cases
- Validate with lint + type-check + tests at end of each story
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1**: T002, T003, T004, T005, T006, T007, T008, T009 can all run in parallel (independent assessment tasks)
- **Phase 2**: T012, T013, T014 can run in parallel (independent foundational fixes)
- **Phase 3 (US1)**: T017, T018, T020 can run in parallel (different files/aspects)
- **Phase 4 (US2)**: T024, T025, T026, T027, T028, T030, T032, T033 can run in parallel (different component files)
- **Phase 5 (US3)**: T036, T037, T038, T040, T041 can run in parallel (different aspects)
- **Phase 6 (US4)**: T044, T046 can run in parallel (different files)
- **Phase 7 (US5)**: T050, T051, T052 can run in parallel (different component files)
- **Phase 8 (US6)**: T057, T058, T059, T060, T061 can run in parallel (different files); T062, T063, T064, T065 can run in parallel (different test files)
- **Cross-story**: US1 and US2 (both P1) can run in parallel; US3, US4, US5 (all P2) can run in parallel

---

## Parallel Example: User Story 2 (Accessibility)

```bash
# Launch all independent accessibility audits together:
Task T024: "Add aria-expanded to collapsible section in SettingsSection.tsx"
Task T025: "Verify form labels in AISettingsSection.tsx"
Task T026: "Verify form labels in DisplaySettings.tsx"
Task T027: "Verify form labels in WorkflowSettings.tsx"
Task T028: "Verify form labels in NotificationSettings.tsx"
Task T030: "Verify dropdown keyboard navigation"
Task T032: "Verify focus-visible styles"
Task T033: "Verify icon aria attributes"
```

---

## Parallel Example: User Story 6 (Code Quality)

```bash
# Launch all structural audits together:
Task T057: "Verify prop drilling depth"
Task T058: "Audit useSettings.ts complexity"
Task T059: "Verify type safety — no any types"
Task T060: "Verify @/ import alias usage"
Task T061: "Verify no magic strings"

# Launch all test file creation together:
Task T062: "Create useGlobalSettings hook tests"
Task T063: "Create GlobalSettings component tests"
Task T064: "Create globalSettingsSchema utility tests"
Task T065: "Augment SettingsSection tests"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only — Page States)

1. Complete Phase 1: Setup — establish baseline
2. Complete Phase 2: Foundational — fix shared infrastructure
3. Complete Phase 3: User Story 1 — fix all page states
4. **STOP and VALIDATE**: All loading/error/validation states render correctly
5. Deploy/demo: Settings page reliably shows correct state in all scenarios

### Incremental Delivery

1. Complete Setup + Foundational → Baseline established
2. Add US1 (Page States) + US2 (Accessibility) → Test independently → Deliver (MVP: reliable + accessible!)
3. Add US3 (UX Polish) → Test independently → Deliver (polished settings)
4. Add US4 (Dirty State) + US5 (Responsive) → Test independently → Deliver (reliable editing + responsive)
5. Add US6 (Code Quality) → Test independently → Deliver (well-tested, maintainable code)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (Page States) + US2 (Accessibility) — both P1
   - Developer B: US3 (UX Polish) + US4 (Dirty State) — P2 stories
   - Developer C: US5 (Responsive) — P2 story
3. After US1-US5 stabilize:
   - Any developer: US6 (Code Quality + Tests)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies on other in-progress tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently testable after completion
- GlobalSettings.tsx is already at 88 lines (under 250 limit) — structural refactoring is minimal
- The primary audit focus is on state handling (US1), accessibility (US2), and test coverage (US6)
- Existing test coverage: SettingsSection (114L), DynamicDropdown (113L), useSettingsForm (103L), settings handlers (221L)
- Missing test coverage: useGlobalSettings hook, GlobalSettings component, globalSettingsSchema utilities, sub-section components
- Total task count: 72 tasks across 9 phases
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
