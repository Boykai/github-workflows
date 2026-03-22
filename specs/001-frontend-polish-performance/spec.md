# Feature Specification: Frontend Polish & Performance — Lucide Barrel File, ChoresPanel Bug Fix, Error Recovery Hints

**Feature Branch**: `001-frontend-polish-performance`  
**Created**: 2026-03-22  
**Status**: Draft  
**Input**: User description: "Phase 6 — Frontend Polish & Performance: Lucide Barrel File, ChoresPanel Bug Fix, Error Recovery Hints"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Accurate Chore Template Counts (Priority: P1)

As a user viewing the Chores page, I want the chore template indicators to accurately reflect which templates have already been created, so that I can trust the interface and avoid re-creating chores that already exist.

Currently, the ChoresPanel relies on a paginated, filtered list of chores to determine template membership. When the user has applied filters or is on a later page, some existing chores are excluded from the membership check, causing templates to incorrectly appear as "uncreated." This fix introduces a dedicated lightweight endpoint that returns all chore names for the project — unpaginated and unfiltered — so the template membership check is always accurate regardless of the user's current view state.

**Why this priority**: This is a user-facing data correctness bug. Incorrect template indicators directly mislead users, causing duplicate chore creation and eroding trust in the product. Fixing this delivers immediate, visible value.

**Independent Test**: Can be fully tested by creating several chores, applying filters or navigating to a later page, and verifying that all previously created chore templates still show as "already created." Delivers accurate chore status regardless of filter or pagination state.

**Acceptance Scenarios**:

1. **Given** a project with 50 chores created from templates and the user has applied a name filter that hides 30 of them, **When** the user views the chore templates panel, **Then** all 50 templates correctly display as "already created."
2. **Given** a project with chores spread across multiple pages, **When** the user navigates to page 3 of the chore list, **Then** templates corresponding to chores on pages 1 and 2 still show as "already created."
3. **Given** a project with zero chores, **When** the user views the chore templates panel, **Then** all templates display as "not yet created."
4. **Given** the chore names endpoint is temporarily unavailable, **When** the user views the templates panel, **Then** the system gracefully degrades (e.g., shows a loading state or falls back to the previous behavior) without crashing.

---

### User Story 2 - Actionable Error Recovery Hints (Priority: P2)

As a user encountering an error (authentication failure, rate limiting, network issue, or server error), I want to see a clear, actionable hint alongside the error message that tells me what I can do to recover, so that I can resolve the problem without contacting support or guessing.

Error hints appear as a muted paragraph below the existing error message in error boundaries and error banners, accompanied by an informational icon. Each hint is tailored to the error type: authentication errors suggest re-logging in, rate limit errors show the reset time and a suggestion to adjust polling settings, and network errors suggest checking connectivity. The hints are concise and English-language.

**Why this priority**: Error recovery is a high-impact user experience improvement. Users currently see generic error messages with no guidance, leading to frustration, support tickets, and session abandonment. Actionable hints reduce confusion and improve self-service recovery.

**Independent Test**: Can be fully tested by simulating each error class (401, 403, 404, 422, 429, 500, network failure, CORS error) and verifying the correct hint text, icon, and optional action link appear below the error message. Delivers contextual error recovery for every error surface in the application.

**Acceptance Scenarios**:

1. **Given** the user receives a 401 Unauthorized error, **When** the error is displayed in any error boundary or banner, **Then** a hint appears stating the session may have expired with a direct link to the login page.
2. **Given** the user receives a 403 Forbidden error, **When** the error is displayed, **Then** a hint appears suggesting the user check their permissions for the resource.
3. **Given** the user hits a 429 Rate Limit error, **When** the rate limit banner is displayed, **Then** the banner shows the reset time and a suggestion to reduce polling frequency in Settings.
4. **Given** the user encounters a network or CORS failure, **When** the error is displayed, **Then** a hint suggests checking network connectivity or trying again later.
5. **Given** the user encounters a 500+ server error, **When** the error is displayed, **Then** a hint suggests waiting a moment and retrying, or contacting support if the issue persists.
6. **Given** the user encounters a 404 Not Found error, **When** the error is displayed, **Then** a hint suggests the resource may have been moved or deleted.
7. **Given** the user encounters a 422 Validation error, **When** the error is displayed, **Then** a hint suggests reviewing the submitted data for correctness.
8. **Given** an error-variant empty state is shown on the Agents, Tools, or Chores page, **When** the error is an authentication or network error, **Then** the empty state includes the contextual recovery hint text.

---

### User Story 3 - Centralized Icon Import System (Priority: P3)

As a developer working on the frontend codebase, I want all icon imports to come from a single centralized barrel file instead of directly from the icon library, so that the codebase remains consistent, icon usage is easy to audit, and import drift is prevented at lint time.

This is a purely organizational improvement — it does not change any user-facing behavior or visual appearance. All existing icon imports are consolidated into a barrel file, and a lint rule prevents future direct imports from the icon library.

**Why this priority**: While important for long-term maintainability and developer experience, this change has no user-facing impact. It is organizational housekeeping that prevents import drift and makes icon auditing easier. It can be implemented independently without affecting users.

**Independent Test**: Can be fully tested by running a codebase search confirming zero direct icon library imports remain, verifying the lint rule blocks new direct imports, and confirming the production build bundle size is unchanged or smaller. Delivers consistent, auditable icon imports enforced by tooling.

**Acceptance Scenarios**:

1. **Given** the barrel file has been created with all used icons, **When** a developer searches the source code for direct icon library imports, **Then** zero results are found (all imports reference the barrel file).
2. **Given** the lint rule is in place, **When** a developer adds a direct import from the icon library, **Then** the linter produces an error directing them to use the barrel file instead.
3. **Given** all imports have been migrated to the barrel file, **When** a production build is performed, **Then** the icon vendor chunk size is unchanged or smaller compared to the previous build.
4. **Given** a developer needs to add a new icon to the project, **When** they follow the established pattern, **Then** they add the icon to the barrel file and import it from there.

---

### Edge Cases

- What happens when the chore names endpoint returns an empty list for a new project with no chores? The template panel should display all templates as "not yet created."
- What happens when the chore names endpoint fails (network error, server error)? The system should degrade gracefully — either show a loading indicator, retry, or fall back to the previous paginated check without crashing.
- What happens when a new error status code is encountered that is not in the hint mapping (e.g., 418 I'm a Teapot)? The system should display a generic fallback hint (e.g., "An unexpected error occurred — please try again or contact support").
- What happens when the error object has no HTTP status code (e.g., a client-side exception)? The system should classify it as a generic error and provide a sensible default hint.
- What happens when rate limit errors include a reset timestamp in the past? The hint should still display gracefully (e.g., "Rate limit should be lifted now — try refreshing").
- What happens if a Lucide icon is used in the codebase but not exported from the barrel file? The build should fail with a clear import error, prompting the developer to add the icon to the barrel file.
- What happens when the EmptyState component is rendered without the optional hint prop? It should render exactly as before, with no visual changes.

## Requirements *(mandatory)*

### Functional Requirements

**Phase A — Centralized Icon Imports (independent, no user-facing change)**

- **FR-001**: System MUST provide a centralized barrel file that re-exports all Lucide icons currently used across the frontend codebase, serving as the single source of truth for icon imports.
- **FR-002**: System MUST update all existing icon import sites to reference the barrel file instead of importing directly from the icon library.
- **FR-003**: System MUST enforce the barrel file pattern at lint time by adding a restricted-imports rule that produces an error when a developer imports directly from the icon library.
- **FR-004**: System MUST NOT change the production build bundle size (the icon vendor chunk must remain the same size or smaller after migration).

**Phase B — ChoresPanel Bug Fix (independent, logic fix only)**

- **FR-005**: System MUST provide a backend endpoint that returns a complete, unpaginated, unfiltered list of all chore names for a given project.
- **FR-006**: System MUST provide a frontend data-fetching hook that queries the chore names endpoint with a 60-second stale time, delivering the complete set of chore names for template membership checks.
- **FR-007**: System MUST update the ChoresPanel template membership check to use the complete chore names list instead of the paginated/filtered list, ensuring accuracy regardless of the user's current filter or page state.

**Phase C — Error Recovery Hints (independent)**

- **FR-008**: System MUST provide an error classification utility that accepts an error and returns a structured object containing a title, a human-readable recovery hint, and an optional action (e.g., a link or button).
- **FR-009**: Error classification MUST be based on HTTP status codes (401/403, 404, 422, 429, 500+, network/CORS failure), never on parsing error message strings, to ensure robustness across API changes.
- **FR-010**: System MUST integrate error hints into all error boundary and error banner components so that every error surface displays a contextual hint below the error message.
- **FR-011**: Rate limit error banners MUST display both the rate limit reset time and a suggestion to adjust polling frequency in Settings.
- **FR-012**: Authentication error banners (401) MUST include a direct link to the login page.
- **FR-013**: System SHOULD extend the EmptyState component to accept an optional hint prop and update error-variant empty states on the Agents, Tools, and Chores pages to display contextual recovery hints.
- **FR-014**: Error hint strings MUST be hardcoded in English. Internationalization is deferred as a separate cross-cutting concern.
- **FR-015**: All changes across all phases MUST pass existing lint checks and test coverage requirements.

### Key Entities

- **ErrorHint**: Represents a structured error recovery hint. Contains a title (short error classification label), a hint (actionable recovery suggestion text), and an optional action (a link URL or action identifier for direct navigation, e.g., "/login" for auth errors or "/settings" for rate limit errors).
- **ChoreName**: Represents a lightweight chore identifier (name string only) returned by the chore names endpoint. Used exclusively for set-membership checks against template names — not a full chore object.

### Assumptions

- The current icon set consists of approximately 77 unique Lucide icons used across approximately 88 import sites. These numbers will be confirmed during implementation by scanning the codebase.
- The existing build system (Vite) already performs tree-shaking and isolates icons into a vendor chunk. The barrel file adds organizational consistency, not additional performance optimization.
- The chore names endpoint returns only plain string names (not full chore objects) to minimize payload size for what is effectively a set-membership check.
- Error hints are English-only for this phase. A future i18n effort will externalize all user-facing strings.
- The barrel file will be manually maintained initially. An auto-generation script is only needed if the icon set changes frequently.
- Items 6.2 (route-based code splitting), 6.4 (skeleton loading states), 6.5 (SpotlightTour onboarding), and 6.7 (sync status chip + RateLimitBar) are already fully implemented and require no changes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A codebase search for direct icon library imports returns zero results, confirming all icon imports use the centralized barrel file.
- **SC-002**: The lint rule successfully blocks any new direct icon library import, producing a clear error message directing the developer to the barrel file.
- **SC-003**: The production build icon vendor chunk size is unchanged or smaller after barrel file migration.
- **SC-004**: Chore templates correctly display their creation status regardless of active filters or pagination — verified by creating chores, applying filters, and confirming all created templates still show as "already created."
- **SC-005**: 100% of error categories (401, 403, 404, 422, 429, 500+, network, CORS) produce a relevant, actionable recovery hint when displayed in the UI.
- **SC-006**: Users encountering a 401 error can navigate directly to the login page from the error hint without manual URL entry.
- **SC-007**: Users encountering a rate limit error can see the reset time and find a direct path to polling settings from the error banner.
- **SC-008**: All existing lint checks pass after changes are applied.
- **SC-009**: All existing tests pass with no reduction in code coverage after changes are applied.
