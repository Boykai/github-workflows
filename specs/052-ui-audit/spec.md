# Feature Specification: UI Audit

**Feature Branch**: `052-ui-audit`  
**Created**: 2026-03-18  
**Status**: Draft  
**Input**: User description: "UI Audit"

## Overview

A comprehensive, repeatable audit of every user-facing page in the Solune frontend to ensure modern best practices across ten quality dimensions: component architecture, data fetching and state management, loading/error/empty states, type safety, accessibility, text and UX polish, styling and layout, performance, test coverage, and code hygiene. Each page is evaluated against a standardized checklist, findings are documented, and defects are remediated — resulting in a uniformly high-quality user experience across the entire application.

### Assumptions

- The audit scope covers all pages within `src/pages/` and their associated feature components, hooks, and types
- Each page is audited independently — one page can pass the audit even if other pages have outstanding issues
- Existing shared UI primitives (buttons, cards, inputs, tooltips, confirmation dialogs) and common components (loaders, error boundaries, empty states) are considered the standard and should be reused rather than reimplemented
- The application supports both light and dark modes, and all audited pages must function correctly in both
- The target viewport range for responsive design is 320px to 1920px (aligned with the v0.1.0 release spec)
- Accessibility compliance targets WCAG AA level (4.5:1 contrast ratio, full keyboard navigation, proper ARIA attributes)
- The audit does not introduce new features — it identifies and remediates defects, gaps, and inconsistencies in existing pages
- Standard web application performance expectations apply (interactions feel instant, lists render smoothly)
- The page-level audit checklist from the parent issue defines the evaluation criteria

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Page Passes All Audit Categories (Priority: P1)

As a developer performing a UI audit on a page, I need a clear, standardized checklist covering all ten quality dimensions so that I can systematically evaluate the page and document findings for every category.

**Why this priority**: The audit checklist is the foundation of the entire feature. Without a structured evaluation framework, audits would be ad hoc and inconsistent across pages.

**Independent Test**: Can be fully tested by selecting any page, running through the checklist, and producing a scored findings table (Pass/Fail/N/A per item) that covers all ten dimensions.

**Acceptance Scenarios**:

1. **Given** a developer selects a page to audit, **When** they evaluate the page against all ten checklist categories, **Then** they can produce a findings table with a Pass, Fail, or N/A status for every checklist item.
2. **Given** a page has no issues across all categories, **When** the audit is complete, **Then** the page is marked as "Audit Passed" with all items scored as Pass or N/A.
3. **Given** a page has failures in one or more categories, **When** the audit is complete, **Then** each failure is documented with a specific description of the issue and the affected code location.

---

### User Story 2 - Component Architecture Compliance (Priority: P1)

As a developer auditing a page, I need to verify that the page follows modular component architecture so that the codebase remains maintainable, testable, and free of prop drilling or inline business logic.

**Why this priority**: Poor component architecture causes cascading maintainability issues. Pages that exceed the line-count threshold or contain deeply nested prop drilling become difficult to test and refactor.

**Independent Test**: Can be fully tested by measuring the page file's line count, checking that sub-components live in the correct feature directory, verifying no prop drilling exceeds two levels, and confirming all shared UI primitives are reused rather than reimplemented.

**Acceptance Scenarios**:

1. **Given** a page file exceeds 250 lines, **When** the audit identifies this, **Then** the finding specifies which sections should be extracted into sub-components within the feature directory.
2. **Given** a page passes props through more than two component levels, **When** the audit identifies this, **Then** the finding recommends composition, context, or hook extraction as the remedy.
3. **Given** a page reimplements a UI element that already exists in the shared primitives library, **When** the audit identifies this, **Then** the finding specifies which shared component should replace the custom implementation.
4. **Given** a page contains business logic (computation or data transformation) inline in JSX, **When** the audit identifies this, **Then** the finding recommends extracting the logic into a hook or helper function.

---

### User Story 3 - Loading, Error, and Empty State Coverage (Priority: P1)

As a user of the application, I need every page to handle loading, error, and empty data states gracefully so that I never see a blank screen, a cryptic error message, or a confusingly empty page.

**Why this priority**: Missing state handling is the most visible class of UI defect. Users encountering a blank screen or unhandled error lose trust in the application immediately.

**Independent Test**: Can be fully tested by simulating loading delays, API errors (including rate limit errors), and empty data collections for each page and verifying the correct state is rendered.

**Acceptance Scenarios**:

1. **Given** a page is loading data, **When** the data has not yet arrived, **Then** the page displays a loading indicator or skeleton — never a blank screen.
2. **Given** an API call fails, **When** the error is rendered, **Then** the page displays a user-friendly error message with a retry action.
3. **Given** a rate limit error occurs, **When** the error is detected, **Then** the page displays a specific rate-limit message distinct from generic errors.
4. **Given** a page has loaded data but the collection is empty, **When** the page renders, **Then** a meaningful empty state with guidance or a call-to-action is shown.
5. **Given** a page has multiple independent data sources, **When** one source fails, **Then** only the affected section shows an error — the rest of the page remains functional.

---

### User Story 4 - Accessibility Compliance (Priority: P1)

As a user who relies on keyboard navigation or assistive technology, I need every page to meet accessibility standards so that I can use all features without a mouse and with a screen reader.

**Why this priority**: Accessibility is both a legal and ethical requirement. Pages that lack keyboard navigation, ARIA attributes, or proper focus management exclude users with disabilities.

**Independent Test**: Can be fully tested by navigating the page using only the keyboard (Tab, Enter, Space, Escape), verifying ARIA attributes on custom controls, checking focus management in dialogs, and running a contrast checker.

**Acceptance Scenarios**:

1. **Given** a page has interactive elements (buttons, links, toggles), **When** a user navigates with the keyboard, **Then** all interactive elements are reachable via Tab and activatable via Enter or Space.
2. **Given** a page opens a dialog or modal, **When** the dialog is open, **Then** focus is trapped within the dialog and returns to the trigger element when the dialog closes.
3. **Given** a page has custom controls (dropdowns, toggles, tabs), **When** a screen reader encounters them, **Then** appropriate ARIA attributes (role, aria-label, aria-expanded, aria-selected) are present.
4. **Given** a page has form fields, **When** a screen reader encounters them, **Then** every input has an associated visible label or aria-label.
5. **Given** a page displays status indicators, **When** the indicator uses color, **Then** an icon and/or text accompaniment is also present so color is not the sole differentiator.

---

### User Story 5 - Type Safety and Data Fetching Compliance (Priority: P2)

As a developer auditing a page, I need to verify that all data fetching uses the standard query library pattern and that all code is fully typed so that runtime errors from untyped data or inconsistent fetching patterns are eliminated.

**Why this priority**: Type safety prevents an entire class of runtime bugs. Inconsistent data fetching patterns lead to duplicate API calls, missing error handling, and stale data.

**Independent Test**: Can be fully tested by running the type checker with strict mode on the page and its associated hooks, and verifying that all API calls use the standard query pattern with proper query keys.

**Acceptance Scenarios**:

1. **Given** a page or hook uses a raw fetch-in-effect pattern, **When** the audit identifies this, **Then** the finding recommends converting to the standard query library pattern.
2. **Given** a page or hook contains an `any` type, **When** the audit identifies this, **Then** the finding specifies the correct type to replace it with.
3. **Given** a page makes an API call that duplicates a call already made by a parent or child component, **When** the audit identifies this, **Then** the finding recommends consolidating the call.
4. **Given** a mutation lacks error handling, **When** the audit identifies this, **Then** the finding recommends adding user-visible error feedback.

---

### User Story 6 - UX Polish and Text Quality (Priority: P2)

As a user of the application, I need all text, labels, and feedback messages to be consistent, clear, and professional so that the application feels polished and trustworthy.

**Why this priority**: Inconsistent terminology, placeholder text, or raw error codes erode user confidence and make the application feel unfinished.

**Independent Test**: Can be fully tested by reading all user-visible text on the page, checking button labels use verb phrases, confirming destructive actions require confirmation, and verifying error messages follow the standard format.

**Acceptance Scenarios**:

1. **Given** a page contains placeholder text ("TODO", "Lorem ipsum", "Test"), **When** the audit identifies this, **Then** the finding specifies the placeholder and its location.
2. **Given** a destructive action (delete, remove, stop) exists on the page, **When** a user triggers it, **Then** a confirmation dialog appears before the action executes.
3. **Given** a mutation succeeds, **When** the result is shown to the user, **Then** a success message (toast, status change, or inline feedback) confirms the action.
4. **Given** a page displays timestamps, **When** timestamps are rendered, **Then** recent timestamps use relative format ("2 hours ago") and older timestamps use absolute format.
5. **Given** a page displays long text (names, descriptions, URLs), **When** the text overflows, **Then** it is truncated with an ellipsis and the full text is available via tooltip.

---

### User Story 7 - Styling, Performance, and Code Hygiene (Priority: P2)

As a developer auditing a page, I need to verify that the page follows the project's styling conventions, avoids performance pitfalls, and maintains clean code so that the codebase remains consistent and performant.

**Why this priority**: While less user-visible than state handling or accessibility, these dimensions prevent technical debt accumulation and ensure the application performs well at scale.

**Independent Test**: Can be fully tested by checking for inline styles, hardcoded colors, index-based list keys, unnecessary re-renders, dead code, and console.log statements on the page.

**Acceptance Scenarios**:

1. **Given** a page uses inline `style={}` attributes, **When** the audit identifies this, **Then** the finding recommends converting to utility classes.
2. **Given** a page uses hardcoded color values, **When** the audit identifies this, **Then** the finding recommends using theme variables or dark-mode-aware variants.
3. **Given** a page renders a list using array index as the key, **When** the audit identifies this, **Then** the finding recommends using a stable identifier.
4. **Given** a page contains unused imports, commented-out code, or console.log statements, **When** the audit identifies this, **Then** the finding lists each instance for removal.
5. **Given** a page passes the linter with zero warnings, the type checker with zero errors, and all related tests pass, **When** the audit concludes, **Then** the page is marked as meeting code hygiene standards.

---

### User Story 8 - Test Coverage Verification (Priority: P3)

As a developer auditing a page, I need to verify that the page's hooks and interactive components have meaningful test coverage so that regressions are caught before reaching users.

**Why this priority**: Test coverage is the safety net for all other audit categories. Without tests, fixes from the audit could regress in future changes. Ranked P3 because creating the tests is a remediation step after findings are documented.

**Independent Test**: Can be fully tested by running the existing test suite for the page's hooks and components, checking that tests exist for loading, error, empty, and interaction scenarios.

**Acceptance Scenarios**:

1. **Given** a page has a custom hook, **When** the audit checks for tests, **Then** a test file exists that covers the hook's happy path, error state, loading state, and empty state.
2. **Given** a page has interactive components (forms, dialogs, toggles), **When** the audit checks for tests, **Then** test files exist that simulate user interactions and assert expected outcomes.
3. **Given** a page has no tests at all, **When** the audit identifies this, **Then** the finding lists the specific test scenarios that must be added.

---

### Edge Cases

- What happens when a page has no API calls (purely static content)? Data fetching and state management items should be marked N/A rather than Fail.
- What happens when a page uses a third-party component that does not conform to the project's accessibility standards? The finding should document the component and recommend a wrapper or alternative.
- What happens when a page is under active development and its structure is expected to change significantly? The audit should still be performed but findings should note which items may be affected by upcoming changes.
- What happens when the shared primitives library does not have a component that fits the page's needs? The finding should recommend adding to the shared library rather than building a one-off component.
- What happens when a page has complex state that is not easily extractable into a single hook? The finding should recommend splitting into multiple focused hooks rather than one monolithic hook.

## Requirements *(mandatory)*

### Functional Requirements

**Audit Framework**

- **FR-001**: Each page audit MUST evaluate all ten quality dimensions: component architecture, data fetching and state management, loading/error/empty states, type safety, accessibility, text and UX polish, styling and layout, performance, test coverage, and code hygiene.
- **FR-002**: Each checklist item MUST be scored as Pass, Fail, or N/A — no items may be left unscored.
- **FR-003**: Each Fail finding MUST include a description of the issue, the affected file and location, and a recommended remediation.

**Component Architecture & Modularity**

- **FR-004**: Page files MUST NOT exceed 250 lines; sections beyond this threshold MUST be extracted into sub-components within the feature component directory.
- **FR-005**: Sub-components MUST reside in the designated feature component directory, not inline in the page file.
- **FR-006**: Prop drilling MUST NOT exceed two component levels; deeper data passing MUST use composition, context, or hook extraction.
- **FR-007**: Pages MUST reuse existing shared UI primitives and common components rather than reimplementing equivalent functionality.
- **FR-008**: Complex state logic exceeding 15 lines of stateful hooks MUST be extracted into dedicated custom hooks.
- **FR-009**: Business logic (computation, data transformation) MUST NOT appear inline in JSX; it MUST reside in hooks or helper functions.

**Data Fetching & State Management**

- **FR-010**: All API calls MUST use the standard query library pattern — raw fetch-in-effect patterns MUST be replaced.
- **FR-011**: Query keys MUST follow the established naming convention pattern.
- **FR-012**: Mutations MUST invalidate relevant queries on success to keep the UI consistent.
- **FR-013**: Mutations MUST include error handling that surfaces user-visible feedback.
- **FR-014**: The same data MUST NOT be fetched independently by both a page and its child components.

**Loading, Error & Empty States**

- **FR-015**: Pages MUST display a loading indicator or skeleton while data is being fetched — blank screens during loading are not acceptable.
- **FR-016**: API errors MUST render a user-friendly error message with a retry action.
- **FR-017**: Rate limit errors MUST be detected and communicated with a specific message distinct from generic errors.
- **FR-018**: Empty data collections MUST render a meaningful empty state, not simply show nothing.
- **FR-019**: Pages with multiple data sources MUST handle each section's loading and error states independently.
- **FR-020**: Pages MUST be wrapped in an error boundary at either the route level or within the page itself.

**Type Safety**

- **FR-021**: No `any` types MUST exist in page code, component props, state, or API responses.
- **FR-022**: Type assertions (`as`) MUST be avoided in favor of type guards or discriminated unions.
- **FR-023**: API response types MUST align with backend models, with date fields as ISO strings and nullable fields using the union-with-null pattern.
- **FR-024**: Event handler types MUST be explicit, not generic.

**Accessibility**

- **FR-025**: All interactive elements MUST be reachable via keyboard (Tab) and activatable via Enter or Space.
- **FR-026**: Dialogs and modals MUST trap focus and return focus to the trigger element on close.
- **FR-027**: Custom controls MUST have appropriate ARIA attributes (role, aria-label, aria-expanded, aria-selected).
- **FR-028**: Every form field MUST have an associated visible label or aria-label.
- **FR-029**: Text MUST meet WCAG AA contrast ratio (4.5:1), and status indicators MUST NOT rely on color alone.
- **FR-030**: Interactive elements MUST have visible focus styles.
- **FR-031**: Decorative icons MUST be hidden from screen readers; meaningful icons MUST have aria-labels.

**Text, Copy & UX Polish**

- **FR-032**: No placeholder or draft text (TODO, Lorem ipsum, Test) MUST remain in user-visible strings.
- **FR-033**: Terminology MUST be consistent with the rest of the application.
- **FR-034**: Action button labels MUST use verb phrases (e.g., "Create Agent" not "New Agent").
- **FR-035**: Destructive actions MUST require confirmation via a confirmation dialog.
- **FR-036**: Mutations MUST provide success feedback (toast, status change, or inline message).
- **FR-037**: Error messages MUST be user-friendly: "Could not [action]. [Reason]. [Suggested next step]."
- **FR-038**: Timestamps MUST use relative format for recent times and absolute format for older times.
- **FR-039**: Long text MUST be truncated with an ellipsis and full text available via tooltip.

**Styling & Layout**

- **FR-040**: Pages MUST use utility classes exclusively — no inline style attributes.
- **FR-041**: Pages MUST be responsive across viewport widths from 320px to 1920px.
- **FR-042**: Pages MUST support dark mode using theme-aware variables — no hardcoded colors.
- **FR-043**: Spacing MUST use the project's standard spacing scale — no arbitrary values.
- **FR-044**: Content sections MUST use the shared Card component with consistent padding and rounding.

**Performance**

- **FR-045**: List renders MUST use stable identifiers as keys — never array indices.
- **FR-046**: Lists exceeding 50 items MUST use virtualization or pagination.
- **FR-047**: Heavy transforms (sorting, filtering, grouping) MUST be memoized.

**Test Coverage**

- **FR-048**: Custom hooks for each page MUST have test files covering happy path, error, loading, and empty states.
- **FR-049**: Interactive components MUST have test files covering user interactions.
- **FR-050**: Tests MUST follow the project's established testing conventions and patterns.
- **FR-051**: Tests MUST NOT use snapshot testing; assertion-based tests are required.

**Code Hygiene**

- **FR-052**: Dead code (unused imports, commented-out blocks, unreachable branches) MUST be removed.
- **FR-053**: Console.log statements MUST be removed.
- **FR-054**: Cross-feature project imports MUST use the path alias (`@/`). Same-folder relative imports (e.g., within `__tests__/` or a feature directory) are acceptable.
- **FR-055**: Repeated strings (status values, route paths, query keys) MUST be defined as constants.
- **FR-056**: The linter MUST report zero warnings for all audited files.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of pages in the application have been audited against all ten quality dimensions with a scored findings table.
- **SC-002**: All audited pages display a loading indicator or skeleton during data fetching — zero blank screens across the application.
- **SC-003**: All audited pages show user-friendly error messages with retry actions when API calls fail — zero raw error codes or stack traces shown to users.
- **SC-004**: All interactive elements on audited pages are reachable and activatable via keyboard alone (Tab, Enter, Space).
- **SC-005**: All audited pages render correctly in both light and dark modes across viewport widths from 320px to 1920px.
- **SC-006**: Zero instances of placeholder text (TODO, Lorem ipsum, Test) remain in user-visible strings across audited pages.
- **SC-007**: All destructive actions across audited pages require confirmation before execution.
- **SC-008**: The linter reports zero warnings and the type checker reports zero errors for all audited page files and their associated components, hooks, and types.
- **SC-009**: All custom hooks and key interactive components on audited pages have test files with assertion-based tests covering at minimum happy path, error state, loading state, and empty state.
- **SC-010**: Users can complete their primary task on any audited page within a consistent, predictable experience — no inconsistencies in terminology, button labeling, feedback patterns, or visual styling between pages.
