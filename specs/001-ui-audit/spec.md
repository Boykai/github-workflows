# Feature Specification: UI Audit

**Feature Branch**: `001-ui-audit`  
**Created**: 2026-03-27  
**Status**: Draft  
**Input**: User description: "Comprehensive audit of all frontend pages to ensure modern best practices, modular design, accurate text/copy, and zero bugs. Covers component decomposition, accessibility, error/loading/empty states, type safety, test coverage, and UI/UX polish."

## Assumptions

- The audit covers all 12 route-bound pages in the Solune frontend application: LoginPage, AppPage (Dashboard), ProjectsPage, AgentsPipelinePage, AgentsPage, ToolsPage, ChoresPage, SettingsPage, AppsPage, ActivityPage, HelpPage, and NotFoundPage.
- Each page is audited against the same 10-category checklist (component architecture, data fetching, loading/error/empty states, type safety, accessibility, text/copy/UX, styling/layout, performance, test coverage, code hygiene).
- Existing shared components (CelestialLoader, ErrorBoundary, ProjectSelectionEmptyState, ThemedAgentIcon) and UI primitives (Button, Card, Input, Tooltip, ConfirmationDialog, HoverCard) are used as-is and are not themselves targets of this audit.
- The audit does not introduce new features or change business logic—it only improves code quality, accessibility, UX polish, and test coverage of existing functionality.
- Pages are audited in priority order based on user traffic and complexity (highest-complexity pages first).
- The existing design system (Tailwind CSS with dark mode support, cn() utility) is the standard for all styling fixes.
- Industry-standard performance expectations apply: pages should load and become interactive within a few seconds on typical hardware.
- Standard web accessibility guidelines (WCAG AA) apply for all contrast and keyboard requirements.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consistent Loading, Error, and Empty States Across All Pages (Priority: P1)

A user navigating the application encounters a consistent and reassuring experience regardless of which page they visit. When data is loading, the user sees a clear loading indicator. When an API call fails, the user sees a friendly error message with a retry option. When a page has no data to show, the user sees a meaningful empty state with guidance on what to do next. No page ever shows a blank screen, a raw error code, or an empty void.

**Why this priority**: Loading, error, and empty states are the most visible quality issues to every user on every visit. A blank screen or cryptic error message erodes trust immediately. This is the highest-impact improvement across all pages.

**Independent Test**: Can be fully tested by navigating to each page under three conditions (loading, API error, empty data) and verifying the correct state is displayed. Delivers a polished, trustworthy user experience.

**Acceptance Scenarios**:

1. **Given** a user navigates to any page and data is being fetched, **When** the page renders, **Then** a loading indicator is visible (never a blank screen)
2. **Given** a user is on any page and an API call fails, **When** the error occurs, **Then** a user-friendly error message is displayed with a retry action
3. **Given** a user is on any page and the API call fails due to rate limiting, **When** the rate limit error is detected, **Then** the error message specifically informs the user about the rate limit and suggests waiting
4. **Given** a user navigates to a page where the data collection is empty, **When** the page renders, **Then** a meaningful empty state is displayed with guidance or a call-to-action
5. **Given** a page fetches data from multiple independent sources, **When** one source fails, **Then** only that section shows an error state while the rest of the page remains functional

---

### User Story 2 - Fully Keyboard-Accessible and Screen-Reader-Friendly Interface (Priority: P1)

A user who relies on keyboard navigation or a screen reader can fully operate every page in the application. All interactive elements are reachable via Tab, activatable via Enter or Space, and correctly announced by assistive technology. Dialogs and modals trap focus appropriately and return focus to the trigger element when dismissed.

**Why this priority**: Accessibility is both a legal/compliance concern and a core quality standard. Users with disabilities must have equal access to every feature. This is a P1 because it affects a meaningful portion of users and is a non-negotiable quality bar.

**Independent Test**: Can be tested by navigating every page using only keyboard (Tab, Enter, Space, Escape) and verifying all functionality is operable. Can also be validated with automated accessibility scanning tools.

**Acceptance Scenarios**:

1. **Given** a user navigates any page using only the keyboard, **When** they press Tab repeatedly, **Then** every interactive element (buttons, links, inputs, toggles) receives focus in a logical order
2. **Given** a user focuses on any interactive element, **When** they press Enter or Space, **Then** the element activates its intended action
3. **Given** a dialog or modal is open, **When** the user presses Tab, **Then** focus is trapped within the dialog and does not escape to background content
4. **Given** a dialog or modal is dismissed, **When** the dialog closes, **Then** focus returns to the element that triggered the dialog
5. **Given** a screen reader is active, **When** it encounters any custom control (dropdown, toggle, tab), **Then** the control has appropriate ARIA attributes (role, aria-label, aria-expanded, aria-selected)
6. **Given** a form field exists on any page, **When** a screen reader encounters it, **Then** the field has an associated label (visible or via aria-label)

---

### User Story 3 - Modular, Maintainable Page Architecture (Priority: P2)

A developer working on any page in the application finds a clean, modular codebase. Each page file is concise (250 lines or fewer), with functionality decomposed into feature-specific sub-components and custom hooks. There is no prop drilling beyond two levels, no business logic embedded in JSX, and no duplicated functionality.

**Why this priority**: Code maintainability directly impacts the speed and safety of future changes. Large, monolithic page files with deeply nested prop drilling make bugs harder to find and features harder to add. This is P2 because it primarily benefits developer productivity rather than end-user experience directly.

**Independent Test**: Can be tested by measuring page file line counts, verifying sub-component extraction, checking hook usage patterns, and confirming no prop drilling beyond two levels. Delivers cleaner codebase for faster future development.

**Acceptance Scenarios**:

1. **Given** any page file in the application, **When** its line count is measured, **Then** it is 250 lines or fewer
2. **Given** a page has identifiable self-contained sections, **When** the code is reviewed, **Then** each section is extracted into its own sub-component within the feature component directory
3. **Given** a page or component passes props, **When** the prop chain is analyzed, **Then** props are not drilled more than two levels deep
4. **Given** a page or component contains state logic exceeding 15 lines, **When** the code is reviewed, **Then** that logic is extracted into a custom hook
5. **Given** any page's JSX render tree, **When** the JSX is reviewed, **Then** it contains no business logic—all computation and data transformation happens in hooks or helper functions

---

### User Story 4 - Type-Safe, Lint-Clean Codebase (Priority: P2)

A developer reviewing or modifying any page finds fully typed code with no `any` types, no type assertions, and zero linting warnings. All API response types match the backend models accurately. The codebase passes type checking and linting without errors or warnings.

**Why this priority**: Type safety prevents runtime bugs and makes refactoring safe. Lint cleanliness ensures consistent code style and catches common mistakes. This is P2 because it primarily improves developer experience and reduces bug introduction risk.

**Independent Test**: Can be tested by running the type checker and linter across all page files and verifying zero errors and zero warnings. Delivers a safer, more predictable codebase.

**Acceptance Scenarios**:

1. **Given** the entire frontend codebase, **When** the type checker is run, **Then** zero type errors are reported
2. **Given** any page, component, or hook file, **When** its types are reviewed, **Then** no `any` type is used
3. **Given** any page, component, or hook file, **When** its types are reviewed, **Then** no type assertion (as) is used unless accompanied by a runtime type guard
4. **Given** the entire frontend codebase, **When** the linter is run, **Then** zero warnings are reported
5. **Given** API response types, **When** compared to the backend models, **Then** all fields, nullability, and date formats match

---

### User Story 5 - Polished, Consistent Text, Copy, and User Feedback (Priority: P2)

A user interacting with the application encounters professional, consistent text throughout. Action buttons use verb-based labels. Destructive actions always require confirmation. Success and error feedback is clear and actionable. Timestamps are formatted consistently. Long text is truncated with tooltips showing the full content.

**Why this priority**: Text and copy quality directly shape the user's perception of product professionalism. Inconsistent terminology or missing feedback creates confusion. This is P2 because while important, it does not block core functionality.

**Independent Test**: Can be tested by reviewing all user-visible text for consistency, verifying destructive action confirmations, checking success/error feedback on mutations, and validating timestamp formatting. Delivers a professional, trustworthy user experience.

**Acceptance Scenarios**:

1. **Given** any user-visible string in the application, **When** reviewed, **Then** it contains no placeholder text (no "TODO", "Lorem ipsum", "Test")
2. **Given** any action button in the application, **When** its label is reviewed, **Then** the label is a verb phrase ("Create Agent", "Save Settings", "Delete Pipeline")
3. **Given** a user triggers a destructive action (delete, remove, stop), **When** the action is initiated, **Then** a confirmation dialog appears before the action executes
4. **Given** a user completes a mutation (create, update, delete), **When** the mutation succeeds, **Then** the user sees success feedback (toast, status change, or inline message)
5. **Given** a user triggers a mutation that fails, **When** the error occurs, **Then** the error message follows the format: "Could not [action]. [Reason]. [Suggested next step]."
6. **Given** long text (names, descriptions, URLs) in any list or card, **When** the text exceeds its container, **Then** it is truncated with ellipsis and the full text is available via tooltip

---

### User Story 6 - Dark Mode, Responsive Layout, and Visual Consistency (Priority: P3)

A user on any device width (768px to 1920px) in either light or dark mode sees a visually consistent, well-spaced interface. All layouts adapt to the viewport. No hardcoded colors break dark mode. Spacing follows a consistent scale, and content sections use the shared card component.

**Why this priority**: Visual consistency and responsiveness affect perceived quality but are less critical than functional correctness and accessibility. This is P3 because the application likely already works in most viewport sizes and modes, with only edge cases needing attention.

**Independent Test**: Can be tested by resizing the browser viewport from 768px to 1920px on every page and toggling between light and dark mode, verifying no layout breaks or color issues. Delivers a polished visual experience across devices and themes.

**Acceptance Scenarios**:

1. **Given** any page in the application, **When** the viewport is resized between 768px and 1920px, **Then** the layout adapts without breaking, overlapping, or creating horizontal scrollbars
2. **Given** any page in dark mode, **When** all elements are inspected, **Then** no hardcoded light colors (e.g., white backgrounds, light text) appear
3. **Given** any page's styling, **When** reviewed, **Then** all styles use utility classes only (no inline style attributes) and conditional classes use the cn() helper
4. **Given** any content section, **When** its spacing is reviewed, **Then** spacing values come from the standard scale (no arbitrary pixel values)

---

### User Story 7 - Comprehensive Test Coverage for All Pages (Priority: P3)

A developer running the test suite finds that every page has meaningful test coverage for its hooks, components, and user interactions. Tests cover happy paths, error states, loading states, empty states, and edge cases. Tests follow the codebase conventions and use assertion-based testing (no snapshot tests).

**Why this priority**: Test coverage ensures that future changes don't introduce regressions. This is P3 because it supports long-term maintainability rather than immediate user-facing quality—the fixes from P1 and P2 should be validated by these tests.

**Independent Test**: Can be tested by running the test suite and verifying coverage metrics, checking that each page has hook tests and component interaction tests, and confirming edge cases are covered. Delivers confidence in code quality for future development.

**Acceptance Scenarios**:

1. **Given** any page in the application, **When** its test files are reviewed, **Then** at least one test file exists covering its primary user interactions
2. **Given** any custom hook used by a page, **When** its test files are reviewed, **Then** the hook has tests covering success, error, loading, and empty states
3. **Given** any test file, **When** its test patterns are reviewed, **Then** it uses assertion-based testing (no snapshot tests)
4. **Given** the full test suite, **When** it is run, **Then** all tests pass with zero failures

---

### Edge Cases

- What happens when a page component renders but the user's authentication token has expired mid-session?
- How does the application behave when the backend returns an unexpected response shape (missing fields, extra fields)?
- What happens when a user rapidly clicks a destructive action button multiple times before the confirmation dialog appears?
- How does the application handle extremely long text values (e.g., a 500-character project name)?
- What happens when a page has partial data (some API calls succeed, some fail) and the user triggers a retry?
- How does the application behave when JavaScript is slow or the device is low-powered (long render times)?
- What happens when a user navigates away from a page mid-mutation (e.g., during a delete operation)?

## Requirements *(mandatory)*

### Functional Requirements

**Loading, Error, and Empty States:**

- **FR-001**: Every page MUST display a loading indicator while data is being fetched. No page may render a blank screen during loading.
- **FR-002**: Every page MUST display a user-friendly error message when an API call fails. The error message MUST include a retry action.
- **FR-003**: Every page MUST detect rate limit errors and display a specific message informing the user to wait before retrying.
- **FR-004**: Every page with a data collection MUST display a meaningful empty state with guidance when the collection is empty.
- **FR-005**: Pages with multiple independent data sources MUST show per-section loading and error states. A failure in one section MUST NOT block rendering of other sections.
- **FR-006**: Every page MUST be wrapped in an error boundary to prevent unhandled errors from crashing the entire application.

**Accessibility:**

- **FR-007**: All interactive elements (buttons, links, inputs, toggles, custom controls) MUST be reachable via keyboard Tab navigation and activatable via Enter or Space.
- **FR-008**: All dialogs and modals MUST trap focus within themselves when open and return focus to the trigger element when closed.
- **FR-009**: All custom controls (dropdowns, toggles, tabs) MUST have appropriate ARIA attributes (role, aria-label, aria-expanded, aria-selected).
- **FR-010**: All form fields MUST have associated labels (visible label or aria-label).
- **FR-011**: All text MUST meet WCAG AA color contrast requirements (4.5:1 ratio). Status indicators MUST NOT rely on color alone—they MUST use icon plus text.
- **FR-012**: All interactive elements MUST have visible focus styles.
- **FR-013**: Decorative icons MUST have aria-hidden="true". Meaningful icons MUST have aria-label.

**Component Architecture:**

- **FR-014**: Every page file MUST be 250 lines or fewer. Sections exceeding this limit MUST be extracted into sub-components within the feature component directory.
- **FR-015**: Props MUST NOT be drilled more than two levels deep. Deeper data passing MUST use composition, context, or hook extraction.
- **FR-016**: Pages and components MUST use existing shared UI primitives and common components rather than reimplementing equivalent functionality.
- **FR-017**: State logic exceeding 15 lines of stateful hooks MUST be extracted into a dedicated custom hook.
- **FR-018**: JSX render trees MUST NOT contain business logic. All computation and data transformation MUST happen in hooks or helper functions.

**Data Fetching and State Management:**

- **FR-019**: All API calls MUST use the established query library patterns (query hooks and mutation hooks). Raw fetch calls inside effect hooks are not permitted.
- **FR-020**: Query keys MUST follow the established convention pattern.
- **FR-021**: All mutation hooks MUST have error handling that surfaces user-visible feedback.
- **FR-022**: The same data MUST NOT be fetched independently by both a page and its child component.

**Type Safety:**

- **FR-023**: No `any` type MUST exist in any page, component, or hook file.
- **FR-024**: Type assertions (as) MUST NOT be used unless accompanied by a runtime type guard.
- **FR-025**: API response types MUST match the backend models. Date fields MUST be typed as string (ISO format). Nullable fields MUST use | null.
- **FR-026**: All custom hooks MUST have explicit or unambiguously inferrable return types.

**Text, Copy, and UX Polish:**

- **FR-027**: No placeholder text (e.g., "TODO", "Lorem ipsum", "Test") MUST exist in any user-visible string.
- **FR-028**: All action button labels MUST be verb phrases (e.g., "Create Agent", "Save Settings", "Delete Pipeline").
- **FR-029**: All destructive actions (delete, remove, stop) MUST require confirmation via a confirmation dialog before execution.
- **FR-030**: All successful mutations MUST provide user-visible success feedback (toast, status change, or inline message).
- **FR-031**: All error messages MUST be user-friendly and follow the format: "Could not [action]. [Reason, if known]. [Suggested next step]."
- **FR-032**: Timestamps MUST be formatted consistently: relative time for recent events, absolute time for older events.
- **FR-033**: Long text that exceeds its container MUST be truncated with ellipsis and provide the full text via tooltip.

**Styling and Layout:**

- **FR-034**: All styles MUST use utility classes. No inline style attributes are permitted. Conditional classes MUST use the cn() helper.
- **FR-035**: All pages MUST render correctly at viewport widths from 768px to 1920px without layout breaks.
- **FR-036**: All pages MUST support dark mode using theme-aware CSS variables or dark-mode class variants. No hardcoded color values are permitted.
- **FR-037**: All spacing MUST use the standard spacing scale. No arbitrary pixel values are permitted.

**Performance:**

- **FR-038**: List renders MUST use stable, unique keys (item identifiers, not array indices).
- **FR-039**: Expensive computations (sorting, filtering, grouping) MUST be memoized and not recalculated on every render.
- **FR-040**: Lists rendering more than 50 items MUST use virtualization or pagination.

**Test Coverage:**

- **FR-041**: Every page MUST have at least one test file covering its primary user interactions.
- **FR-042**: Every custom hook used by a page MUST have tests covering success, error, loading, and empty states.
- **FR-043**: All tests MUST use assertion-based testing. Snapshot tests are not permitted.
- **FR-044**: Tests MUST follow codebase conventions for mocking, rendering, and assertions.

**Code Hygiene:**

- **FR-045**: No dead code (unused imports, commented-out blocks, unreachable branches) MUST exist in any audited file.
- **FR-046**: No console.log statements MUST exist in any audited file.
- **FR-047**: All project imports MUST use the path alias (@/) format. Relative imports traversing more than one level are not permitted.
- **FR-048**: All files MUST follow naming conventions: PascalCase for components (.tsx), camelCase with use prefix for hooks (.ts), types in the types directory, utilities in the lib directory.
- **FR-049**: Repeated string literals (status values, route paths, query keys) MUST be defined as named constants.
- **FR-050**: All audited files MUST pass linting with zero warnings.

### Key Entities

- **Page**: A top-level route-bound component that represents a distinct screen in the application. Key attributes: route path, data sources, sub-components, custom hooks, line count.
- **Audit Finding**: An individual issue discovered during the audit of a page. Key attributes: page, checklist category, severity (critical/major/minor), description, recommended fix.
- **Audit Report**: The aggregated results of auditing a single page across all 10 checklist categories. Key attributes: page, pass/fail counts per category, overall status (pass/fail), list of findings.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 12 pages pass the 10-category audit checklist with zero critical or major findings remaining
- **SC-002**: Zero pages display a blank screen during loading—every page shows a loading indicator within moments of navigation
- **SC-003**: Every page with data displays a meaningful empty state when no data exists (verified across all 12 pages)
- **SC-004**: All interactive elements on all pages are operable via keyboard alone (Tab, Enter, Space, Escape)
- **SC-005**: Automated accessibility scanning reports zero critical or serious violations across all pages
- **SC-006**: The type checker reports zero errors across the entire frontend codebase
- **SC-007**: The linter reports zero warnings across all audited files
- **SC-008**: All page files are 250 lines or fewer
- **SC-009**: All pages render correctly at viewport widths 768px, 1024px, 1440px, and 1920px in both light and dark mode
- **SC-010**: All existing tests continue to pass after audit changes (zero regressions)
- **SC-011**: Every page has at least one test file with meaningful interaction tests
- **SC-012**: Users complete primary tasks on each page without encountering placeholder text, inconsistent terminology, or missing feedback
