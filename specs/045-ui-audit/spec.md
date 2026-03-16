# Feature Specification: UI Audit Issue Template

**Feature Branch**: `045-ui-audit`  
**Created**: 2026-03-16  
**Status**: Draft  
**Input**: User description: "Review and merge the issue template for UI Audit"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Create a Page Audit from the Template (Priority: P1)

As a developer preparing to audit a UI page, I open the repository's issue creation screen, select the "UI Audit" template, and receive a fully structured checklist pre-populated with all ten audit categories. I fill in the page name to personalise the checklist and create the issue so the team can track audit progress.

**Why this priority**: Without a usable template, there is no standardised way to perform or track a page audit. This is the foundational user journey — every other story depends on the template existing and being selectable.

**Independent Test**: Navigate to the repository's "New Issue" page, select the UI Audit template, verify the issue body contains all ten audit sections with checkbox items, and confirm the issue can be created successfully.

**Acceptance Scenarios**:

1. **Given** a developer is on the "New Issue" page, **When** they choose the "UI Audit" template, **Then** the issue form is pre-filled with the full audit checklist containing all ten categories
2. **Given** the template is loaded, **When** the developer replaces every `[PAGE_NAME]` placeholder with the actual page name and updates the default title to append that page name, **Then** the resulting issue clearly identifies which page is being audited
3. **Given** the developer has filled in the page name, **When** they submit the issue, **Then** the issue is created with the "chore" label applied automatically
4. **Given** the created issue, **When** viewing it in the issue list, **Then** the title follows the format `[CHORE] UI Audit` so it is easily filterable

---

### User Story 2 — Track Audit Progress Across All Categories (Priority: P1)

As a developer performing a page audit, I use the checklist items within the issue to track progress across all ten audit categories (Component Architecture, Data Fetching, States, Type Safety, Accessibility, UX Polish, Styling, Performance, Tests, Code Hygiene). Each checkbox can be independently checked off as I complete that item.

**Why this priority**: The checklist is the primary value of the template. If the items are unclear, incomplete, or untestable, the audit cannot be performed consistently. This story validates the content quality of every checklist item.

**Independent Test**: Open an issue created from the template, work through each checklist category, and verify that every item describes a clear, pass/fail condition that can be evaluated against a real page.

**Acceptance Scenarios**:

1. **Given** an open audit issue, **When** a developer reviews a page against the "Component Architecture & Modularity" section, **Then** every item describes a concrete, observable condition (e.g., "Page file is ≤250 lines")
2. **Given** an open audit issue, **When** a developer checks off items in "Data Fetching & State Management", **Then** each item references a specific pattern to verify (e.g., React Query usage, query key conventions)
3. **Given** an open audit issue, **When** a developer reaches the "Accessibility" section, **Then** each item maps to a verifiable keyboard-navigation or assistive-technology criterion
4. **Given** an open audit issue, **When** a developer checks or unchecks checklist items, **Then** GitHub reflects the updated checklist progress in the issue UI
5. **Given** an open audit issue, **When** all items across all ten categories are checked, **Then** the audit is considered complete

---

### User Story 3 — Follow the Phased Implementation Guide (Priority: P2)

As a developer who has completed the audit checklist, I follow the six-phase implementation guide embedded in the template to fix the identified issues in a logical order: Discovery → Structural Fixes → States & Error Handling → Accessibility & UX Polish → Testing → Validation.

**Why this priority**: The phased guide prevents developers from making fixes in a disorganised order (e.g., writing tests before fixing structural issues). While the checklist itself is sufficient to identify problems, the implementation guide ensures efficient remediation.

**Independent Test**: Read through the implementation steps section and verify that each phase references specific, actionable steps and that phases build on each other in a logical sequence.

**Acceptance Scenarios**:

1. **Given** a developer reads Phase 1 (Discovery & Assessment), **When** they follow the listed steps, **Then** they can produce a complete findings table by reading the page file, components, hooks, and running lint and tests
2. **Given** a developer reads Phase 2 (Structural Fixes), **When** they follow the steps, **Then** they know exactly when and how to extract sub-components, hooks, and replace raw data-fetching patterns
3. **Given** a developer reads Phase 6 (Validation), **When** they follow the verification steps, **Then** they can confirm zero lint warnings, zero type errors, all tests passing, and correct visual and keyboard behaviour
4. **Given** the implementation guide, **When** reviewing all six phases, **Then** each phase depends only on the phases before it (no circular dependencies)

---

### User Story 4 — Identify Relevant Files for a Specific Page (Priority: P2)

As a developer starting an audit, I use the "Relevant Files" section of the template to understand which files, directories, hooks, types, and shared components are involved for the page I am auditing. I fill in the placeholders to create a reference list.

**Why this priority**: Knowing which files to inspect is essential for an accurate audit. The template's file reference section prevents developers from missing related components, hooks, or type definitions.

**Independent Test**: Open the template's "Relevant Files" section, replace placeholders with a real page name, and verify the resulting file paths align with the repository's actual directory structure.

**Acceptance Scenarios**:

1. **Given** the "Relevant Files" section, **When** a developer substitutes `[PageName]`, `[Feature]`, and `[feature]` placeholders, **Then** the resulting paths point to valid page, hook, component, and test locations in the frontend source directory tree
2. **Given** the "Relevant Files" section, **When** a developer reviews the shared components list, **Then** it references actual shared UI primitives (Button, Card, Input, Tooltip, ConfirmationDialog) and common components (CelestialLoader, ErrorBoundary)
3. **Given** a completed "Relevant Files" section, **When** a developer starts the audit, **Then** they have a complete inventory of page, component, hook, API, type, and test files to review

---

### User Story 5 — Run Verification Commands After Remediation (Priority: P2)

As a developer who has completed fixes based on the audit findings, I run the verification commands listed at the bottom of the template to confirm the page meets quality standards before closing the issue.

**Why this priority**: Without verification steps, a developer may close the audit issue prematurely. The verification commands provide an objective, repeatable quality gate.

**Independent Test**: Run each verification command listed in the template against a sample page and confirm they produce pass/fail results.

**Acceptance Scenarios**:

1. **Given** the "Verification" section, **When** a developer runs the lint command with the page and component paths, **Then** the output reports zero warnings or lists remaining violations
2. **Given** the "Verification" section, **When** a developer runs the type-check command, **Then** the output reports zero type errors or lists remaining issues
3. **Given** the "Verification" section, **When** a developer runs the test suite, **Then** all tests pass or failures are clearly identified
4. **Given** the "Verification" section, **When** a developer performs the manual browser checks (light mode, dark mode, responsive, keyboard navigation), **Then** they have a clear list of what to verify visually

---

### User Story 6 — Reuse the Template Across Multiple Pages (Priority: P3)

As a team lead, I create multiple audit issues — one per page in the application — using the same template. Each issue is self-contained and tracks the audit for a single page independently.

**Why this priority**: The template must be generic enough to apply to any page. This story validates that the placeholder-based design works across different page types without modification to the template itself.

**Independent Test**: Create two audit issues for different pages (e.g., Projects page and Agents page), fill in the page-specific placeholders, and verify both issues are complete and make sense for their respective pages.

**Acceptance Scenarios**:

1. **Given** the UI Audit template, **When** a team lead creates an audit issue for one page, **Then** the checklist items are relevant and applicable to that page
2. **Given** the UI Audit template, **When** a team lead creates an audit issue for a different page, **Then** the same checklist items are relevant and applicable
3. **Given** multiple audit issues created from the template, **When** the creator appends the audited page name to the default title and fills in the placeholders, **Then** each issue is distinguishable by its page name in the title and body

---

### Edge Cases

- What happens when a page has no associated hook or data-fetching calls? The developer skips the "Data Fetching & State Management" items that do not apply and adds a note indicating they are not applicable.
- What happens when a page is entirely new and has no existing tests? The "Test Coverage" section still applies — the developer creates tests from scratch as part of the audit.
- What happens when multiple developers audit the same page simultaneously? The issue's checkbox state may conflict; teams should assign one developer per audit issue.
- What happens when the template references shared components that do not yet exist in the codebase? The developer flags this as a prerequisite and creates a separate issue to add the missing shared component.
- What happens when a checklist item is not applicable to a specific page (e.g., "Large lists virtualized" for a settings page with no lists)? The developer checks the item and adds a note indicating it is not applicable.

## Scope Boundaries

### In Scope

- Reviewing and correcting the Markdown issue template at `.github/ISSUE_TEMPLATE/chore-ui-audit.md`
- Ensuring the template's placeholder instructions, file references, and verification commands match the current `solune/frontend/` layout
- Documenting the manual issue-creation workflow required to personalise the template for a specific page, including title updates

### Out of Scope

- Implementing or refactoring frontend pages, hooks, or shared UI components referenced by the template
- Adding repository-wide automation for Markdown or issue-template validation
- Changing the backend chore-template generation flow or GitHub issue-template infrastructure

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The issue template MUST be selectable from the repository's "New Issue" page under the template name "UI Audit"
- **FR-002**: The template MUST pre-populate the issue body with all ten audit categories: Component Architecture & Modularity, Data Fetching & State Management, Loading/Error/Empty States, Type Safety, Accessibility, Text/Copy & UX Polish, Styling & Layout, Performance, Test Coverage, and Code Hygiene
- **FR-003**: Each audit category MUST contain actionable checklist items formatted as GitHub-compatible checkboxes (`- [ ]`)
- **FR-004**: Every checklist item MUST describe a single, pass/fail condition that a developer can evaluate against a specific page
- **FR-005**: The template MUST include `[PAGE_NAME]`, `[PageName]`, `[Feature]`, and `[feature]` placeholders that developers replace with page-specific values when creating an issue
- **FR-006**: The template MUST include a six-phase implementation guide (Discovery, Structural Fixes, States & Error Handling, Accessibility & UX Polish, Testing, Validation) with numbered steps
- **FR-007**: The template MUST include a "Relevant Files" section with placeholder paths that map to the repository's frontend source directory structure
- **FR-008**: The template MUST include a "Verification" section with specific commands for linting, type-checking, testing, and manual browser validation
- **FR-009**: The template MUST automatically apply the "chore" label to issues created from it
- **FR-010**: The template MUST set the issue title to `[CHORE] UI Audit` by default, allowing the developer to append the page name
- **FR-011**: Every checklist item MUST be written in clear, unambiguous language that does not require external documentation to understand
- **FR-012**: The checklist MUST cover a minimum of 59 individual audit items across all ten categories

### Key Entities

- **Audit Issue**: A GitHub issue created from the UI Audit template. Contains the full checklist, implementation guide, relevant files list, and verification steps for a single page.
- **Audit Category**: One of the ten thematic sections (e.g., "Accessibility", "Performance") grouping related checklist items.
- **Checklist Item**: A single, actionable audit criterion within a category. Formatted as a GitHub checkbox. Describes a pass/fail condition.
- **Page Under Audit**: The specific frontend page being evaluated. Referenced throughout the issue via the `[PAGE_NAME]` placeholder.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can create a new audit issue from the template in under 2 minutes, including filling in the page name placeholder
- **SC-002**: 100% of checklist items describe a single, verifiable pass/fail condition — no item requires subjective judgement to evaluate
- **SC-003**: The template covers all ten audit categories with no category containing fewer than 4 checklist items
- **SC-004**: A developer unfamiliar with the codebase can understand every checklist item without referencing external documentation
- **SC-005**: The six-phase implementation guide can be followed sequentially — each phase's inputs are produced by a preceding phase
- **SC-006**: The verification section commands produce clear pass/fail results when run against any audited page
- **SC-007**: The template can be reused for any page in the application without modification to the template file itself (only placeholder substitution)
- **SC-008**: All audit issues created from the template have the "chore" label applied automatically

## Assumptions

- The repository uses GitHub Issues with support for issue templates in `.github/ISSUE_TEMPLATE/`.
- The frontend codebase follows the directory structure `solune/frontend/src/` with pages, components, hooks, services, and types subdirectories.
- Shared UI components (Button, Card, Input, Tooltip, ConfirmationDialog) and common components (CelestialLoader, ErrorBoundary) exist in the codebase.
- The "chore" label already exists in the repository's label set.
- Developers running audits have access to run linting, type-checking, and test tools locally.
