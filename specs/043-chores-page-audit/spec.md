# Feature Specification: Chores Page Audit — Modern Best Practices, Modular Design, and Zero Bugs

**Feature Branch**: `043-chores-page-audit`
**Created**: 2026-03-16
**Status**: Draft
**Input**: User description: "Comprehensive audit of the Chores page to ensure modern best practices, modular design, accurate text/copy, and zero bugs. Covers component decomposition, accessibility, error/loading/empty states, type safety, test coverage, and UI/UX polish."

## Assumptions

- The Project Solune design system (the "Celestial" theme) is the authoritative source of truth for visual consistency — all typography, spacing, color tokens, iconography, shadows, and animation patterns must align with its defined tokens.
- WCAG AA is the minimum accessibility target, consistent with standard web application expectations.
- "Supported screen sizes" means desktop (1280px and above), tablet (768px–1279px), and mobile (below 768px), aligning with standard responsive breakpoints.
- Performance expectations follow standard web application norms: pages should become interactive within 3 seconds and user actions should reflect immediately (under 1 second perceived response time).
- The audit scope covers the Chores page (`ChoresPage.tsx`) and all components rendered within it — `ChoresPanel`, `ChoreCard`, `AddChoreModal`, `ChoreScheduleConfig`, `ChoreChatFlow`, `ConfirmChoreModal`, `FeaturedRitualsPanel`, and `CelestialCatalogHero` — but does not extend to shared layout elements (navigation, sidebar) unless they exhibit issues unique to the Chores page context.
- Existing shared primitives (`Button`, `Card`, `Input`, `Tooltip`, `ConfirmationDialog`, `HoverCard`) from `src/components/ui/` and shared components (`CelestialLoader`, `ErrorBoundary`, `ProjectSelectionEmptyState`, `ThemedAgentIcon`) from `src/components/common/` are considered correct and should be reused rather than reimplemented.
- Page file size target is ≤250 lines per component file. Files exceeding this threshold should be decomposed into focused sub-components under the feature folder.
- All data fetching must use the application's established data fetching library with proper caching — no manual fetch-in-effect patterns. Query keys must follow the established `[feature].all / .list(id) / .detail(id)` convention.
- Issues discovered during the audit that cannot be resolved within scope will be documented and tracked as follow-up tasks rather than blocking completion.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Correct and Complete Page States (Priority: P1)

As a user, I want the Chores page to display correctly in every state — loading, empty (no project selected), empty (no chores), populated, error, and rate-limited — so that I always understand what is happening and never encounter a broken or confusing view.

**Why this priority**: Broken or missing states directly block users from completing tasks. A page that shows blank content, crashes on API errors, or displays misleading information is a critical usability failure. The Chores page has multiple data sources (chores list, templates, board data, pipeline options) that each need independent loading/error handling to prevent one failed request from blocking the entire page.

**Independent Test**: Can be fully tested by triggering each page state (initial load, no project selected, empty chore list, populated chore list, API error, rate-limited response) and verifying that each renders correctly with appropriate messaging and no console errors.

**Acceptance Scenarios**:

1. **Given** the Chores page is fetching data, **When** the user arrives on the page, **Then** a loading indicator is displayed that matches the loading patterns used on other pages (e.g., `CelestialLoader` or skeleton).
2. **Given** no project is selected, **When** the user views the Chores page, **Then** a clear empty state (`ProjectSelectionEmptyState`) is shown explaining how to select a project, with no layout breaks.
3. **Given** a project is selected but has no chores, **When** the user views the Chores page, **Then** an empty state is displayed with a meaningful message and a call-to-action to create the first chore.
4. **Given** a network error occurs while loading chore data, **When** the user is on the Chores page, **Then** an error state is displayed with a clear user-friendly message and a retry action.
5. **Given** the user encounters a rate limit, **When** the rate-limit response is received, **Then** an informational message is displayed using `isRateLimitApiError()` detection and the page handles the condition gracefully without crashing.
6. **Given** the Chores page has multiple data sources (chores, templates, board data), **When** one data source fails while others succeed, **Then** only the affected section shows an error state while other sections remain functional.
7. **Given** any state of the Chores page, **When** the browser developer console is open, **Then** no unhandled errors, missing-key warnings, or deprecation warnings are present.

---

### User Story 2 — Modular Component Architecture and Type Safety (Priority: P1)

As a developer maintaining the Chores page, I want every component to follow single-responsibility principles with full type safety, so that the codebase is maintainable, easy to extend, and free of runtime type errors.

**Why this priority**: The Chores page contains several large components (ChoresPanel at 543 lines, ChoreCard at 584 lines, AddChoreModal at 356 lines) that likely exceed the 250-line target. Decomposing these into focused sub-components and ensuring strict type safety directly prevents bugs and reduces the cost of future changes.

**Independent Test**: Can be fully tested by reviewing each component file for line count, prop drilling depth, type annotations, and adherence to the feature folder structure — then verifying that the page functions identically after refactoring.

**Acceptance Scenarios**:

1. **Given** a developer reviews the Chores page code, **When** they examine any single component file, **Then** no file exceeds 250 lines and each component has a single clear responsibility.
2. **Given** a developer reviews the component hierarchy, **When** they trace prop passing, **Then** no props are drilled more than 2 levels deep — composition, context, or hook extraction is used instead.
3. **Given** a developer reviews type annotations, **When** they search for `any` types or type assertions (`as`), **Then** zero instances are found — all props, state, API responses, and event handlers are fully typed.
4. **Given** a developer reviews custom hooks, **When** they examine hook return types, **Then** all hooks have explicit return type annotations or are inferrable without ambiguity.
5. **Given** a developer reviews the component tree, **When** they look for business logic in JSX, **Then** all computation and data transformation is in hooks or helper functions, not inline in the render tree.
6. **Given** a developer reviews the feature folder, **When** they inspect file organization, **Then** all Chores sub-components live in `src/components/chores/`, hooks in `src/hooks/`, and types in `src/types/`.

---

### User Story 3 — Accessible Chores Page (Priority: P2)

As a user who relies on assistive technology or keyboard navigation, I want the Chores page to be fully accessible so that I can create, edit, schedule, trigger, and manage chores without barriers.

**Why this priority**: Accessibility determines whether the page is usable at all for users with disabilities. The Chores page has complex interactive elements — inline editors, schedule configuration modals, pipeline selector popups, confirmation dialogs, and filter controls — that all require careful keyboard and screen reader support.

**Independent Test**: Can be fully tested by navigating the entire Chores page using only a keyboard, running an automated accessibility scanner, and verifying screen reader announcements for all interactive elements including modals, toggles, and the inline editor.

**Acceptance Scenarios**:

1. **Given** a user navigates the Chores page using only the keyboard, **When** they Tab through all interactive elements (filter buttons, sort selector, search input, chore cards, action buttons, modals), **Then** every element is reachable, focus order is logical, and a visible focus indicator is present.
2. **Given** a screen reader user visits the Chores page, **When** the page renders, **Then** all interactive elements have appropriate accessible names and roles — buttons are labeled, toggles announce their state, dropdowns indicate expanded/collapsed.
3. **Given** a user opens the AddChoreModal or ChoreScheduleConfig modal, **When** the modal is open, **Then** focus is trapped within the modal, pressing Escape closes it, and focus returns to the triggering element on close.
4. **Given** the Chores page is viewed at standard zoom levels, **When** a contrast checker is applied to all text and interactive elements, **Then** all elements meet WCAG AA minimum contrast ratios (4.5:1 for normal text, 3:1 for large text and UI components).
5. **Given** a user views status badges, schedule indicators, and chore states, **When** they inspect these elements, **Then** status is communicated through both icon and text — never color alone.
6. **Given** decorative icons on the Chores page, **When** a screen reader encounters them, **Then** they are hidden with `aria-hidden="true"`, and meaningful icons have appropriate `aria-label` attributes.

---

### User Story 4 — Polished Text, Copy, and User Experience (Priority: P2)

As a user, I want all text on the Chores page to be clear, consistent, and helpful — with proper confirmation on destructive actions and meaningful feedback on all mutations — so that I can confidently manage my chores without confusion or accidental data loss.

**Why this priority**: Text quality and UX polish directly affect whether users trust the application. Inconsistent terminology, missing confirmation dialogs on destructive actions (like deleting a chore), and unhelpful error messages erode confidence and increase support burden.

**Independent Test**: Can be fully tested by exercising every user-visible string (button labels, empty state messages, error messages, toast notifications), triggering all destructive actions (delete, discard changes), and verifying confirmation dialogs and success/error feedback.

**Acceptance Scenarios**:

1. **Given** a user reads any text on the Chores page, **When** they examine button labels, headings, descriptions, and messages, **Then** all text is final meaningful copy with no placeholder text ("TODO", "Lorem ipsum", "Test").
2. **Given** a user encounters the same concept across the Chores page and other pages, **When** they compare terminology, **Then** consistent terms are used throughout (e.g., "chore" not "task", "pipeline" not "workflow", "trigger" not "run").
3. **Given** a user clicks a delete or discard action, **When** the action is initiated, **Then** a confirmation dialog (`ConfirmationDialog`) is shown before the action executes — never immediate.
4. **Given** a user successfully creates, updates, triggers, or deletes a chore, **When** the mutation completes, **Then** a clear success indicator is shown (toast, inline status change, or confirmation message).
5. **Given** a mutation fails, **When** the error is displayed, **Then** the message follows the format "Could not [action]. [Reason, if known]. [Suggested next step]." with no raw error codes or stack traces.
6. **Given** long chore names, template paths, or descriptions, **When** they exceed available space, **Then** text is truncated with `text-ellipsis` and full text is available in a `Tooltip`.
7. **Given** timestamps on the Chores page (last triggered, next checkpoint), **When** they are displayed, **Then** recent times use relative format ("2 hours ago") and older times use absolute format, consistent with the rest of the application.
8. **Given** action buttons on ChoreCards, **When** a user reads button labels, **Then** all labels are verb-based ("Trigger Chore", "Save Changes", "Delete Chore") rather than noun-based.

---

### User Story 5 — Responsive Layout and Visual Consistency (Priority: P2)

As a user accessing the Chores page on different screen sizes, I want the layout to adapt gracefully and look visually consistent with the rest of the application, so that the experience is professional and usable on any device.

**Why this priority**: Visual cohesion and responsive design ensure the page works for all users regardless of device. The Chores page uses a catalog-style grid layout with cards, featured rituals panels, and inline editors that must reflow correctly at different breakpoints.

**Independent Test**: Can be fully tested by resizing the browser window across desktop (1280px+), tablet (768px–1279px), and mobile (below 768px) breakpoints and verifying layout adaptation, theme consistency, and visual cohesion with other application pages.

**Acceptance Scenarios**:

1. **Given** a user views the Chores page on a desktop screen (1280px and above), **When** the page renders, **Then** the full chore catalog grid, featured rituals panel, and toolbar controls are visible and well-spaced.
2. **Given** a user views the Chores page on a tablet screen (768px–1279px), **When** the page renders, **Then** the grid layout adapts (fewer columns) and all controls remain accessible without horizontal scrolling.
3. **Given** a user views the Chores page on a mobile screen (below 768px), **When** the page renders, **Then** chore cards stack vertically, inline editors remain usable, and all touch targets meet minimum 44×44px size.
4. **Given** a user switches between light mode and dark mode, **When** they view the Chores page, **Then** all components correctly reflect the selected theme — no hardcoded colors, visual artifacts, or unreadable text.
5. **Given** a user compares the Chores page styling with other pages, **When** they inspect typography, spacing, colors, and icons, **Then** all elements use the application's design tokens with no ad-hoc or off-palette values.
6. **Given** the Chores page uses styling utilities, **When** a developer reviews the code, **Then** all styles use Tailwind utility classes and `cn()` for conditional classes — no inline `style={}` attributes.

---

### User Story 6 — Data Fetching Best Practices and Performance (Priority: P2)

As a user, I want the Chores page to load quickly, avoid unnecessary network requests, and remain responsive even with many chores, so that managing my chores is fast and reliable.

**Why this priority**: The Chores page fetches from multiple endpoints (chores list, templates, board data, pipeline options) and polls evaluate-triggers every 60 seconds. Proper data fetching patterns, caching, and render performance are critical to prevent duplicate requests, stale data, and UI jank.

**Independent Test**: Can be fully tested by profiling network requests during page load and interaction, verifying query key conventions, checking staleTime configuration, and confirming no duplicate API calls occur between parent and child components.

**Acceptance Scenarios**:

1. **Given** the Chores page loads, **When** network requests are observed, **Then** all API calls use TanStack Query (`useQuery` / `useMutation`) — no raw `useEffect` + `fetch` patterns exist.
2. **Given** query keys on the Chores page, **When** a developer reviews them, **Then** they follow the `choreKeys.all / .list(id) / .detail(id)` convention consistent with other features.
3. **Given** the Chores page and its child components, **When** the same data is needed, **Then** it is fetched once at the appropriate level and shared — no duplicate API calls between parent and child components.
4. **Given** a mutation succeeds (create, update, delete, trigger), **When** the response is received, **Then** relevant queries are invalidated and the UI reflects the change without a full page reload.
5. **Given** a mutation fails, **When** the error handler runs, **Then** user-visible feedback is provided (toast or inline error) for every `useMutation` call.
6. **Given** the chore list grows to 50+ items, **When** the user scrolls through the catalog, **Then** the page remains responsive with no perceptible lag — large lists use pagination or virtualization.
7. **Given** the Chores page during typical interactions, **When** render behavior is profiled, **Then** no unnecessary re-renders are observed for components whose inputs have not changed.

---

### User Story 7 — Comprehensive Test Coverage (Priority: P3)

As a developer, I want the Chores page to have thorough automated test coverage for hooks, components, and edge cases, so that regressions are caught early and refactoring is safe.

**Why this priority**: Test coverage is essential for long-term maintainability, especially after the refactoring work in this audit. While less directly user-facing than other stories, comprehensive tests ensure that future changes do not reintroduce the bugs and inconsistencies this audit fixes.

**Independent Test**: Can be fully tested by running the test suite for all Chores-related files and verifying coverage of happy paths, error states, loading states, empty states, rate limit errors, and user interactions.

**Acceptance Scenarios**:

1. **Given** custom hooks for the Chores page, **When** tests are run, **Then** each hook is tested via `renderHook()` with mocked API covering happy path, error, loading, and empty states.
2. **Given** key interactive components (ChoreCard, AddChoreModal, ChoresPanel, ChoreScheduleConfig), **When** tests are run, **Then** each has test files covering user interactions (clicks, form submissions, keyboard navigation, dialog confirmations).
3. **Given** test files for the Chores feature, **When** a developer reviews test patterns, **Then** tests follow codebase conventions (`vi.mock('@/services/api', ...)`, `renderHook`, `waitFor`, `createWrapper()`).
4. **Given** edge cases (empty state, error state, loading state, rate limit error, long strings, null/missing data, rapid clicks), **When** tests are run, **Then** each edge case has at least one dedicated test.
5. **Given** the Chores test suite, **When** a developer reviews test types, **Then** no snapshot tests are present — all assertions are explicit and behavior-based.

---

### User Story 8 — Clean Code and Zero Lint Violations (Priority: P3)

As a developer, I want the Chores page code to be clean, well-organized, and free of lint violations, so that the codebase remains consistent and maintainable.

**Why this priority**: Code hygiene affects long-term maintenance velocity. Dead code, console.log statements, magic strings, and lint warnings accumulate as technical debt. Cleaning these up as part of the audit ensures the Chores page matches the quality bar of the rest of the application.

**Independent Test**: Can be fully tested by running ESLint on all Chores-related files, running the TypeScript compiler with `--noEmit`, and reviewing for dead code, console.log statements, relative imports, and magic strings.

**Acceptance Scenarios**:

1. **Given** all Chores page source files, **When** ESLint is run, **Then** zero warnings and zero errors are reported.
2. **Given** all Chores page source files, **When** the TypeScript compiler is run with `--noEmit`, **Then** zero type errors are reported.
3. **Given** a developer reviews the Chores page code, **When** they search for dead code, **Then** no unused imports, commented-out blocks, or unreachable branches are found.
4. **Given** a developer reviews the Chores page code, **When** they search for `console.log`, **Then** zero instances are found.
5. **Given** all project imports in Chores files, **When** a developer reviews import paths, **Then** all use the `@/` alias — no relative `../../` paths are present.
6. **Given** repeated strings in Chores files (status values, route paths, query keys), **When** a developer reviews the code, **Then** all are defined as constants — no magic strings.

---

### Edge Cases

- What happens when the user's session expires while editing a chore inline? The page should preserve unsaved state and prompt re-authentication without losing the user's edits.
- What happens when the polling evaluate-triggers call fires while the user is in the middle of editing a chore? The trigger evaluation response should not overwrite or disrupt the user's in-progress edits.
- What happens when a chore's assigned pipeline is deleted? The ChoreCard should display a graceful fallback (e.g., "Auto" or a "pipeline not found" warning) rather than crashing or showing a blank.
- What happens when the user rapidly clicks the "Trigger" button multiple times? The button should be disabled during the mutation to prevent duplicate triggers.
- What happens when the AddChoreModal sparse-input chat flow encounters a network error mid-conversation? The chat should display an error message and allow the user to retry without losing conversation context.
- What happens when the user has 100+ chores in a single project? The catalog should remain performant — no UI freezing, and filtering/sorting should be fast.
- What happens when a chore name is 200 characters (the maximum)? The name should display correctly in the card, inline editor, and any truncated contexts with a tooltip showing the full text.
- What happens when the "Save All" action partially fails (some chores save, others fail)? The page should clearly indicate which saves succeeded and which failed, keeping the failed chores in their dirty edit state.
- What happens when the browser window is extremely narrow (below 320px)? The page should still render legibly without critical elements being cut off or overlapping.
- What happens when the real-time sync connection drops while viewing chores? The page should indicate stale data and allow manual refresh without crashing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: All visual elements on the Chores page MUST use the application's design tokens for colors, typography, spacing, shadows, and border radii — no hard-coded or off-palette values.
- **FR-002**: The Chores page MUST render correctly in both light and dark themes with no visual artifacts, unreadable text, or missing styles.
- **FR-003**: The Chores page MUST display appropriate, visually consistent states for loading, empty (no project selected), empty (no chores), populated, error, and rate-limited conditions — each section that fetches data independently MUST show its own loading/error state.
- **FR-004**: All interactive elements (buttons, toggles, filter controls, sort selector, search input, inline editors, modals, pipeline selector popup) MUST respond to user input and provide immediate visual feedback (hover states, focus indicators, loading spinners, disabled states during processing).
- **FR-005**: The Chores page MUST be navigable entirely via keyboard, with a logical tab order and visible focus indicators (`celestial-focus` class or `focus-visible:` ring) on all interactive elements.
- **FR-006**: All interactive elements MUST have appropriate accessible names and roles (`aria-label`, `aria-expanded`, `aria-selected`, `role`), and modals MUST trap focus and return focus to the triggering element on close.
- **FR-007**: All text and interactive elements on the Chores page MUST meet WCAG AA contrast ratio requirements (4.5:1 for normal text, 3:1 for large text and UI components). Status indicators MUST NOT rely on color alone.
- **FR-008**: The Chores page layout MUST adapt to desktop (1280px and above), tablet (768px–1279px), and mobile (below 768px) screen sizes without horizontal scrolling, overlapping elements, or truncated interactive content.
- **FR-009**: All touch targets on the Chores page MUST be at least 44×44px on touch-capable screen sizes.
- **FR-010**: The Chores page MUST produce no unhandled errors, missing-key warnings, or deprecation warnings in the browser console during normal usage across all states.
- **FR-011**: No individual component file on the Chores page MUST exceed 250 lines. Files currently exceeding this limit MUST be decomposed into focused sub-components within the `src/components/chores/` feature folder.
- **FR-012**: Props MUST NOT be drilled more than 2 levels deep. Components requiring deeply nested data MUST use composition, context, or hook extraction instead.
- **FR-013**: All data fetching on the Chores page MUST use TanStack Query (`useQuery` / `useMutation`). No raw `useEffect` + `fetch` patterns are permitted.
- **FR-014**: Query keys MUST follow the established `choreKeys.all / .list(id) / .detail(id)` convention. The same data MUST NOT be fetched independently by both a parent and child component.
- **FR-015**: All `useMutation` calls MUST have `onError` handlers that surface user-visible feedback (toast or inline error message). All successful mutations MUST provide success feedback.
- **FR-016**: All destructive actions (delete chore, discard unsaved changes) MUST require confirmation via `ConfirmationDialog` — never immediate execution.
- **FR-017**: All user-visible text MUST be final, meaningful copy. No placeholder text, TODO markers, or raw error codes are permitted. Error messages MUST follow the format "Could not [action]. [Reason, if known]. [Suggested next step]."
- **FR-018**: All code in Chores page files MUST have zero `any` types, zero type assertions (`as`), and all event handlers MUST use explicit types.
- **FR-019**: Complex state logic (more than 15 lines of useState/useEffect/useCallback) MUST be extracted into custom hooks in `src/hooks/`.
- **FR-020**: Long text (chore names, template paths, descriptions, URLs) MUST be truncated with `text-ellipsis` and full text available in a `Tooltip`.
- **FR-021**: Timestamps (last triggered, next checkpoint) MUST use relative format for recent times and absolute format for older times, consistent with application patterns.
- **FR-022**: All Chores page source files MUST pass ESLint with zero warnings and zero errors, and the TypeScript compiler MUST report zero type errors.
- **FR-023**: An audit summary MUST be produced documenting all findings, all changes made, and any improvements deferred for future work.

### Key Entities

- **Chore**: A recurring repository maintenance task; key attributes include name, status (active/paused), schedule configuration (type and value), execution count, last triggered timestamp, AI enhancement flag, associated pipeline, and template content.
- **Chore Template**: A repository-defined issue template from `.github/ISSUE_TEMPLATE/`; key attributes include name, description ("about"), file path, and content. Represents chores available to create but not yet configured.
- **Chore Schedule**: The trigger configuration for a chore; defined by schedule type (time-based or count-based) and schedule value (number of days or number of issues). Determines when automatic triggers fire.
- **Chore Edit State**: The in-progress editing state for inline chore editing; tracks original values, current modifications, dirty flag, and file SHA for conflict detection.
- **Featured Ritual**: A computed spotlight card derived from chore data; includes "Next Run" (closest to trigger), "Most Recently Run" (latest trigger date), and "Most Run" (highest execution count).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of visual elements on the Chores page pass a design token compliance check — zero off-palette colors, inconsistent spacing, or mismatched typography when compared against the application's design system.
- **SC-002**: The Chores page renders correctly in all defined states (loading, empty-no-project, empty-no-chores, populated, error, rate-limited) across all supported screen sizes with zero layout breaks or visual glitches.
- **SC-003**: The Chores page achieves zero critical or serious violations when evaluated with an automated accessibility scanner targeting WCAG AA.
- **SC-004**: All interactive elements on the Chores page are reachable and operable via keyboard alone, with 100% of focusable elements displaying a visible focus indicator.
- **SC-005**: Users can complete core tasks on the Chores page (create a chore, edit a chore inline, configure a schedule, trigger a chore, delete a chore) in under 5 seconds per task on a standard connection.
- **SC-006**: No individual component file exceeds 250 lines after decomposition, and zero instances of prop drilling beyond 2 levels exist.
- **SC-007**: The Chores page remains responsive (no perceptible lag or frame drops) when displaying 100+ chores with active filtering and sorting.
- **SC-008**: Zero type-safety violations exist in Chores page source files — all variables, parameters, return values, and event handlers have explicit type annotations with no escape hatches.
- **SC-009**: All Chores-related custom hooks have dedicated tests covering happy path, error, loading, and empty states.
- **SC-010**: All key interactive components have test files covering user interactions, with zero snapshot tests.
- **SC-011**: The browser console shows zero unhandled errors or warnings during a complete walkthrough of all Chores page states and interactions.
- **SC-012**: All Chores-related source files pass the project's linting and type-checking tools with zero warnings and zero errors.
- **SC-013**: An audit summary document is produced listing all findings, all changes made, and any improvements deferred for future work.
