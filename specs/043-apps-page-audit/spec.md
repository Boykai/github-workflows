# Feature Specification: Apps Page Audit

**Feature Branch**: `043-apps-page-audit`  
**Created**: 2026-03-16  
**Status**: Draft  
**Input**: User description: "Plan: Apps Page Audit — Comprehensive audit of the Apps page to ensure modern best practices, modular design, accurate text/copy, and zero bugs. Covers component decomposition, accessibility, error/loading/empty states, type safety, test coverage, and UI/UX polish."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reliable App Management with Proper Feedback (Priority: P1)

A user visits the Apps page to create, view, start, stop, and delete applications. Every action provides clear, immediate feedback: loading indicators appear while data loads, meaningful error messages display when something goes wrong, and empty states guide the user when no apps exist. Destructive actions (delete, stop) always require explicit confirmation before executing.

**Why this priority**: Users depend on the Apps page as their primary interface for managing applications. If loading states are missing, errors are cryptic, or destructive actions fire without confirmation, users lose trust in the tool and may lose data. Reliable state handling is the foundation for every other improvement.

**Independent Test**: Can be fully tested by navigating to the Apps page with various data conditions (no apps, many apps, API failure, slow network) and verifying that each state renders appropriately with user-friendly messaging and that destructive actions always present a confirmation dialog.

**Acceptance Scenarios**:

1. **Given** the user navigates to the Apps page, **When** the app list is loading, **Then** a visible loading indicator is displayed (never a blank screen).
2. **Given** the API returns an error while loading the app list, **When** the error state renders, **Then** a user-friendly error message appears with a retry action, and rate-limit errors are detected and communicated clearly.
3. **Given** the user has no apps, **When** the empty app list renders, **Then** a meaningful empty state is displayed with a clear call-to-action to create the first app.
4. **Given** the user clicks "Delete" on an app, **When** the action is triggered, **Then** a confirmation dialog appears requiring explicit confirmation before the app is deleted.
5. **Given** the user clicks "Stop" on a running app, **When** the action is triggered, **Then** a confirmation dialog appears before the app is stopped.
6. **Given** the user submits the Create App form, **When** the creation fails, **Then** an error message appears in the dialog describing what went wrong in plain language (no raw error codes).
7. **Given** the user successfully creates, starts, stops, or deletes an app, **When** the mutation completes, **Then** a success indication is shown (toast, status update, or inline message) and the app list refreshes automatically.
8. **Given** the Apps page has multiple independent data sections, **When** one section fails to load, **Then** only that section shows an error state while the rest of the page remains functional.

---

### User Story 2 - Accessible and Polished App Management Experience (Priority: P2)

A user interacts with the Apps page entirely via keyboard or with a screen reader. All buttons, form fields, dialogs, and interactive controls are reachable via Tab, activated via Enter/Space, and announced correctly. The page adapts seamlessly to dark mode, and long text (app names, descriptions, URLs) is truncated with full text available on hover. All copy is consistent, action buttons use verb-based labels, and timestamps are formatted in a human-friendly manner.

**Why this priority**: Accessibility and UX polish directly affect usability for all users, including those with disabilities. Inconsistent copy, missing keyboard support, or broken dark mode degrades the experience even when core functionality works. This builds on the reliable foundation from P1.

**Independent Test**: Can be fully tested by navigating the entire Apps page (list view, detail view, create dialog) using only keyboard inputs and verifying all interactive elements are reachable, dialogs trap focus, and screen readers announce elements correctly. Dark mode can be tested by toggling themes and verifying all elements remain visible with proper contrast.

**Acceptance Scenarios**:

1. **Given** the user is on the Apps page, **When** they press Tab repeatedly, **Then** focus moves through all interactive elements (buttons, form fields, links) in a logical order with visible focus indicators.
2. **Given** the create app dialog is open, **When** focus enters the dialog, **Then** focus is trapped within the dialog and returns to the trigger button when the dialog closes.
3. **Given** an app has a long name or description, **When** it renders in the card grid, **Then** the text is truncated with an ellipsis and the full text is available via a tooltip on hover.
4. **Given** the user is in dark mode, **When** they view the Apps page, **Then** all elements (cards, dialogs, buttons, text, status badges) use theme-appropriate colors with no hardcoded light-mode values.
5. **Given** the user is on the Apps page, **When** they inspect action buttons, **Then** all buttons use verb-based labels (e.g., "Create App", "Start App", "Stop App", "Delete App") and consistent terminology.
6. **Given** an app was created recently, **When** the timestamp displays, **Then** it shows relative time (e.g., "2 hours ago") for recent entries and absolute format for older ones.
7. **Given** an interactive control exists (status badge, dropdown, toggle), **When** a screen reader encounters it, **Then** it has appropriate ARIA attributes (role, label, expanded state) and decorative icons are hidden from assistive technology.
8. **Given** the user views the Apps page at different viewport widths (768px–1920px), **When** the layout renders, **Then** the grid adapts responsively without broken layouts, overlapping elements, or horizontal scroll.

---

### User Story 3 - Well-Structured, Maintainable Apps Page Codebase (Priority: P2)

A developer working on the Apps page finds a clean, modular codebase. The page file is concise (≤250 lines), with self-contained sub-components extracted into a feature folder. Complex state logic lives in dedicated hooks. All data types are explicitly defined with no escape hatches. There are no dead code blocks, no console logs, and all imports use the project alias convention.

**Why this priority**: Maintainability directly affects the team's ability to iterate quickly and safely. A monolithic page file with inline business logic, untyped data, and dead code increases the risk of regressions and slows down every future change. This is equal priority to UX polish because both affect long-term product velocity.

**Independent Test**: Can be fully tested by running static analysis (linting, type checking) and verifying the page file is under 250 lines, all sub-components live in the feature folder, hooks are extracted for complex state, and there are zero type-safety escape hatches or lint violations.

**Acceptance Scenarios**:

1. **Given** the Apps page file, **When** the line count is measured, **Then** it is ≤250 lines with additional logic extracted into sub-components or hooks.
2. **Given** the app feature components, **When** inspecting the folder structure, **Then** all sub-components live in the designated feature component directory (not inline in the page file).
3. **Given** the codebase, **When** searching for type escape hatches, **Then** there are no `any` types and no unsafe type assertions (`as`) in any Apps-related files.
4. **Given** the Apps-related hooks, **When** inspecting their structure, **Then** complex state logic (>15 lines of state management) is extracted into dedicated hook files with clear return types.
5. **Given** the Apps page and its components, **When** running the linter, **Then** zero warnings or errors are reported.
6. **Given** the Apps page codebase, **When** inspecting imports, **Then** all project imports use the `@/` alias convention and there are no relative path imports crossing module boundaries.
7. **Given** the Apps page codebase, **When** searching for dead code, **Then** there are no unused imports, commented-out blocks, or unreachable branches.

---

### User Story 4 - Comprehensive Test Coverage for Apps Features (Priority: P3)

A developer modifying the Apps page can run the test suite and have confidence that existing functionality is not broken. Tests cover the primary user interactions (create, view, start, stop, delete), edge cases (empty state, error state, loading state, rate-limit errors, long strings, null data), and custom hooks. Tests follow codebase conventions and use assertion-based testing (no snapshot tests).

**Why this priority**: Test coverage is the safety net that enables all other improvements to be delivered with confidence. Without tests covering edge cases and interactions, refactoring risks introducing regressions. This is prioritized after structural and UX improvements since tests validate those changes.

**Independent Test**: Can be fully tested by running the test suite for all Apps-related files and verifying that tests exist for hooks, components, and page interactions, covering happy paths, error states, empty states, and edge cases.

**Acceptance Scenarios**:

1. **Given** the Apps custom hooks, **When** running hook tests, **Then** tests cover successful data fetching, error handling, loading states, and cache invalidation behavior.
2. **Given** the Apps page and components, **When** running component tests, **Then** tests cover create dialog interaction, form validation, app card actions, detail view navigation, and confirmation dialogs.
3. **Given** the test suite, **When** testing edge cases, **Then** tests verify behavior for empty app list, API errors, rate-limit errors, apps with null fields, and extremely long app names or descriptions.
4. **Given** the test files, **When** inspecting test patterns, **Then** all tests follow codebase conventions (mocked API, render helpers, waitFor patterns) and use assertion-based testing (no snapshot tests).

---

### User Story 5 - Performant App List Rendering (Priority: P3)

A user with many applications sees the Apps page render efficiently without jank or unnecessary delays. Lists use stable keys, expensive computations are memoized, and the page avoids duplicate data fetching. If the app list grows large (>50 items), the interface handles it gracefully through pagination or virtualization.

**Why this priority**: Performance is a quality-of-life improvement that matters as usage scales. While not blocking core functionality, poor performance degrades the experience for power users with many apps. This builds on top of the structural and UX improvements.

**Independent Test**: Can be fully tested by loading the Apps page with a large dataset (50+ apps) and verifying smooth rendering, no visible jank, stable scroll performance, and no duplicate network requests in the browser developer tools.

**Acceptance Scenarios**:

1. **Given** the app list renders, **When** inspecting the rendered items, **Then** each app card uses a stable, unique key based on the app identifier (never array index).
2. **Given** the Apps page loads, **When** monitoring network requests, **Then** no duplicate requests are made for the same data (the page and child components do not independently fetch the same resource).
3. **Given** a user has more than 50 apps, **When** the list renders, **Then** the interface handles the volume gracefully (pagination, virtualization, or performant full render).
4. **Given** the Apps page with computed or transformed data, **When** the component re-renders, **Then** expensive operations (sorting, filtering, grouping) are memoized and do not recompute unnecessarily.

---

### Edge Cases

- What happens when the user creates an app with a name that already exists? The system should display a clear conflict error message, not a generic failure.
- What happens when the user rapidly clicks Start/Stop on the same app? Buttons should be disabled during pending mutations to prevent race conditions.
- What happens when an app has a `null` port, `null` error_message, or `null` associated pipeline? The UI should handle nullable fields gracefully without rendering "null" or crashing.
- What happens when an app has an extremely long name (64 characters) or description? Text should truncate with an ellipsis and the full text should be available via tooltip.
- What happens when the user navigates directly to a detail view URL for an app that does not exist? The system should display a clear "app not found" message with navigation back to the list.
- What happens when the API returns a rate-limit error? The system should detect the rate limit and display a specific message with a suggested wait time rather than a generic error.
- What happens when the user has the Apps page open in two tabs and deletes an app in one? The stale tab should handle the missing app gracefully when it next fetches data.
- What happens when the live preview iframe fails to load or the app port is not yet assigned? A clear placeholder or error state should appear instead of a broken iframe.
- What happens when the Create App form is submitted with whitespace-only values? Trim validation should catch this and require meaningful input.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Apps page MUST display a loading indicator while the app list is being fetched — never a blank screen.
- **FR-002**: The Apps page MUST display a user-friendly error message with a retry action when the API call fails, with specific messaging for rate-limit errors.
- **FR-003**: The Apps page MUST display a meaningful empty state with a call-to-action when the user has no apps.
- **FR-004**: All destructive actions (delete app, stop app) MUST present a confirmation dialog before executing.
- **FR-005**: All mutation operations (create, start, stop, delete) MUST display success feedback upon completion (toast, status change, or inline message).
- **FR-006**: All mutation error messages MUST be user-friendly, following the format: "Could not [action]. [Reason]. [Suggested next step]." — no raw error codes or stack traces.
- **FR-007**: The page MUST be wrapped in an error boundary to catch unexpected rendering errors gracefully.
- **FR-008**: All interactive elements (buttons, form fields, links, dialogs) MUST be reachable via keyboard Tab navigation and activated via Enter/Space.
- **FR-009**: Modal dialogs (create app, confirmation) MUST trap focus while open and return focus to the trigger element when closed.
- **FR-010**: All form fields MUST have associated labels (visible or via ARIA attributes) for screen reader accessibility.
- **FR-011**: Custom controls and status indicators MUST have appropriate ARIA attributes (role, aria-label, aria-expanded) and MUST NOT rely solely on color to convey meaning.
- **FR-012**: All interactive elements MUST have visible focus indicators that meet the project's focus styling conventions.
- **FR-013**: Decorative icons MUST be hidden from assistive technology; meaningful icons MUST have accessible labels.
- **FR-014**: Long text (app names, descriptions, URLs) MUST be truncated with an ellipsis and MUST show full text via tooltip on hover.
- **FR-015**: Action buttons MUST use verb-based labels (e.g., "Create App", "Start App", "Delete App") consistent with the rest of the application.
- **FR-016**: Timestamps MUST be formatted as relative time for recent entries and absolute format for older entries, consistent across the application.
- **FR-017**: The Apps page MUST support dark mode using theme variables — no hardcoded light-mode colors.
- **FR-018**: The Apps page layout MUST be responsive across viewports from 768px to 1920px without broken layouts or horizontal scrolling.
- **FR-019**: The Apps page MUST use only design system spacing values — no arbitrary or magic-number spacing.
- **FR-020**: Content sections MUST use the shared Card component with consistent padding and rounding.
- **FR-021**: The Apps page file MUST be ≤250 lines, with additional logic extracted into sub-components in the feature component directory.
- **FR-022**: Complex state logic (>15 lines) MUST be extracted into dedicated hook files.
- **FR-023**: All data types MUST be explicitly defined — no `any` types or unsafe type assertions.
- **FR-024**: All data fetching MUST use the project's query library conventions with proper query key patterns and configured stale times.
- **FR-025**: The page and its child components MUST NOT independently fetch the same data (no duplicate API calls).
- **FR-026**: Array renders MUST use stable, unique keys based on item identifiers — never array index.
- **FR-027**: All Apps-related files MUST pass linting with zero warnings or errors.
- **FR-028**: All project imports MUST use the alias path convention — no relative path imports crossing module boundaries.
- **FR-029**: There MUST be no dead code (unused imports, commented-out blocks, unreachable branches) or console log statements.
- **FR-030**: Custom hooks for this feature MUST have tests covering happy paths, error states, loading states, and cache invalidation.
- **FR-031**: Key interactive components MUST have tests covering user interactions, form submissions, and confirmation dialogs.
- **FR-032**: Edge cases (empty state, error state, rate-limit error, null fields, long strings) MUST be covered by tests.
- **FR-033**: All user-visible strings MUST be finalized copy — no placeholder text, TODOs, or lorem ipsum.

### Key Entities

- **App**: A user-created application with a name, display name, description, status (creating, active, stopped, error), associated pipeline, repository type, port, and error message. Created and updated timestamps track lifecycle.
- **App Status**: The lifecycle state of an application — creating (being provisioned), active (running), stopped (not running), or error (failed). Each status has a distinct visual representation.
- **App Card**: A summary representation of an app in the list view, displaying the app's name, status, description, and available actions.
- **App Detail View**: A full-page view of a single app, showing all metadata, action controls, error messages, and a live preview when the app is active.
- **App Preview**: An embedded live view of a running application, sandboxed for security, with appropriate loading and error fallback states.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users always see a loading indicator, error message, or content on the Apps page — blank screens occur 0% of the time across all data states (loading, error, empty, populated).
- **SC-002**: 100% of destructive actions (delete, stop) require confirmation before executing.
- **SC-003**: All interactive elements on the Apps page are reachable and operable via keyboard-only navigation (Tab, Enter, Space, Escape).
- **SC-004**: The Apps page passes accessibility audit with zero critical or serious violations across all views (list, detail, create dialog).
- **SC-005**: The Apps page renders correctly in both light and dark modes with all elements meeting WCAG AA color contrast (4.5:1 ratio).
- **SC-006**: The Apps page layout adapts without visual breakage across viewport widths from 768px to 1920px.
- **SC-007**: All Apps-related files pass linting and type checking with zero warnings and zero errors.
- **SC-008**: Test coverage exists for all custom hooks, key component interactions, and identified edge cases (empty, error, rate-limit, null fields, long strings).
- **SC-009**: The Apps page file is ≤250 lines, and all sub-components reside in the designated feature directory.
- **SC-010**: Users can create a new app and see it appear in the list within 3 seconds of successful creation (no manual refresh required).

## Assumptions

- The existing shared component library (Button, Card, Input, Tooltip, ConfirmationDialog, CelestialLoader, ErrorBoundary) is functional and can be used as-is without modification.
- The existing React Query setup and query key conventions (appKeys pattern) are correct and should be followed.
- The existing API endpoints and type definitions accurately reflect the backend contracts.
- Dark mode theming infrastructure (CSS variables, Tailwind dark: variants) is already in place and functional.
- The audit scope is limited to the Apps page and its directly related components, hooks, and types — shared components are reference-only.
- Rate-limit error detection utilities (e.g., `isRateLimitApiError()`) exist in the codebase and can be reused.
- No backend changes are required; all improvements are frontend-only.
- The Create App form validation rules (name: 2-64 chars, lowercase+numbers+hyphens; display name: up to 128 chars; branch: required) are correct and should be preserved.
