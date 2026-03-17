# Feature Specification: Solune v0.1.0 Public Release

**Feature Branch**: `050-solune-v010-release`  
**Created**: 2026-03-17  
**Status**: Draft  
**Input**: User description: "Plan: Solune v0.1.0 Public Release"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Reliable Pipeline Execution Without Data Loss (Priority: P1)

As a developer using Solune to orchestrate AI coding agents, I need my pipeline state (which agents ran, which succeeded, which failed) to survive application restarts so that I never lose track of in-progress work or have to manually reconstruct pipeline status after a crash or redeployment.

**Why this priority**: Pipeline state persistence is the foundation for every pipeline-related feature in this release. Without it, users lose all pipeline progress on restart, making the product unreliable for real-world use. This is a release blocker that cascades to all Track A features (label-based state, group execution, pipeline builder).

**Independent Test**: Can be fully tested by starting a multi-stage pipeline, restarting the application mid-execution, and verifying the pipeline resumes from its last known state. Delivers core reliability that makes Solune viable for real development workflows.

**Acceptance Scenarios**:

1. **Given** a pipeline is in progress with 3 of 5 stages completed, **When** the application restarts unexpectedly, **Then** all 5 stage states are preserved and visible on reload within 5 seconds.
2. **Given** the system has accumulated more than 500 pipeline runs over time, **When** a user views historical pipeline data, **Then** all runs are retrievable without any data loss or cap on visible history.
3. **Given** a pipeline run fails mid-execution, **When** the user triggers recovery, **Then** the system rebuilds state from persistent storage and resumes from the last successful stage.
4. **Given** the persistent storage is empty (fresh install), **When** the application starts, **Then** it initializes cleanly with no errors and begins tracking new pipeline runs immediately.

---

### User Story 2 — Secure-by-Default Application (Priority: P1)

As an administrator deploying Solune, I need the application to enforce security best practices out of the box — credentials are never leaked, secrets are encrypted, and project access is scoped to authorized users — so that I can deploy with confidence and meet basic security requirements.

**Why this priority**: Security vulnerabilities are release blockers. Credential leakage, missing encryption, and auth bypasses represent critical risks that could expose user data or allow unauthorized access to code repositories. These must be resolved before any public-facing release.

**Independent Test**: Can be fully tested by deploying the application, attempting to access projects without authorization (expecting 403), verifying cookies are HttpOnly/SameSite=Strict, confirming startup rejects missing encryption secrets, and running an automated scan for hardcoded credentials.

**Acceptance Scenarios**:

1. **Given** a user attempts to access a project they are not a member of, **When** they send a request to that project's resources, **Then** the system returns a 403 Forbidden response.
2. **Given** the application starts without required encryption keys configured, **When** the startup sequence runs, **Then** the application refuses to start and logs a clear error message about missing configuration.
3. **Given** a user logs in successfully, **When** session cookies are set, **Then** all authentication cookies have HttpOnly and SameSite=Strict flags (plus Secure in production/HTTPS).
4. **Given** the full codebase, **When** a security audit is performed, **Then** zero hardcoded secrets, API keys, or credentials are found outside of environment configuration.
5. **Given** any user input field or API endpoint, **When** malformed or malicious input is submitted, **Then** the system validates and sanitizes input before processing, returning appropriate error messages.

---

### User Story 3 — Clean, Maintainable Codebase (Priority: P2)

As a contributor to Solune, I need the codebase to be well-structured with no God classes, minimal dead code, manageable function complexity, and clear module boundaries so that I can understand, modify, and extend the system without excessive risk of regressions.

**Why this priority**: Code quality directly enables velocity for all subsequent feature work. The current 5,338-line service class and functions with cyclomatic complexity up to 123 make changes risky and slow. Cleaning this up before feature work prevents compounding technical debt.

**Independent Test**: Can be fully tested by verifying all source files are under 1,500 lines, all functions have cyclomatic complexity ≤ 25, no duplicate utility functions exist, and static analysis tools report zero errors.

**Acceptance Scenarios**:

1. **Given** the backend codebase after refactoring, **When** file sizes are measured, **Then** no single source file exceeds 1,500 lines.
2. **Given** any function in the codebase, **When** cyclomatic complexity is measured, **Then** no function exceeds a complexity score of 25.
3. **Given** the codebase, **When** searching for duplicate implementations of common utilities (e.g., repository resolution), **Then** each utility exists in exactly one location.
4. **Given** the frontend codebase after decomposition, **When** component and hook file sizes are measured, **Then** no single module exceeds 200 lines.
5. **Given** the refactored code, **When** the full static analysis suite runs, **Then** zero errors are reported.

---

### User Story 4 — Visual Pipeline Builder with Group Execution (Priority: P2)

As a developer configuring CI/CD pipelines, I need a visual drag-and-drop pipeline builder that supports grouping stages into sequential and parallel execution groups so that I can intuitively design complex workflows without writing configuration files by hand.

**Why this priority**: The pipeline builder is the primary UX differentiator for Solune. It transforms pipeline configuration from a code-editing task into a visual, intuitive experience. Combined with group execution and label-based state, it completes the core pipeline feature set.

**Independent Test**: Can be fully tested by creating a new pipeline with mixed sequential/parallel groups via the visual builder, saving the configuration, running it, and verifying stages execute in the correct order with group-level controls.

**Acceptance Scenarios**:

1. **Given** the pipeline configuration page, **When** a user drags stages into groups, **Then** the visual builder reflects the grouping in real-time with clear visual boundaries.
2. **Given** a pipeline with 2 sequential groups (each containing 2 parallel stages), **When** the pipeline executes, **Then** all stages in Group 1 complete before Group 2 begins, and stages within each group run in parallel.
3. **Given** an existing pipeline configuration, **When** a user toggles a group between sequential and parallel mode, **Then** the change is saved and reflected in the next execution.
4. **Given** a pipeline using label-based state tracking, **When** a stage completes, **Then** the corresponding label is updated and API calls for state recovery are reduced by at least 50% compared to polling-based recovery.

---

### User Story 5 — Agent Orchestration and Parallel Layout (Priority: P2)

As a developer working with multiple AI agents simultaneously, I need a side-by-side agent layout with visual differentiation and synchronized MCP (Model Context Protocol) tool configurations so that I can monitor and manage parallel agent activity effectively.

**Why this priority**: Parallel agent execution is a core workflow for Solune users. The current single-agent view limits productivity. Side-by-side layout with MCP sync ensures agents have consistent tooling while users maintain clear oversight.

**Independent Test**: Can be fully tested by launching two agents in parallel, verifying they appear side-by-side with distinct visual indicators, and confirming MCP tool configurations propagate correctly to both agent files.

**Acceptance Scenarios**:

1. **Given** two or more agents are running, **When** the user views the agents page, **Then** agents are displayed side-by-side with distinct visual differentiation (color, icon, or label).
2. **Given** a project's MCP configuration is updated, **When** agent files are generated or refreshed, **Then** the updated MCP tools are propagated to all agent configuration files.
3. **Given** an agent configuration file, **When** the tools setting is inspected, **Then** the file includes the complete tool list as configured in the project MCP settings.

---

### User Story 6 — Accessible, Polished User Interface (Priority: P3)

As any user of Solune, including those with visual impairments or assistive technology, I need the UI to meet accessibility standards with consistent theming, responsive layouts, and no visual bugs so that the application is professional and usable by everyone.

**Why this priority**: Accessibility and visual polish are essential for a public release. WCAG AA compliance is a baseline expectation, and visual inconsistencies undermine user trust. This phase covers theme contrast, page audits, and responsive design across all major pages.

**Independent Test**: Can be fully tested by running an automated contrast audit on both light and dark themes, performing keyboard-only navigation through all major pages, and verifying responsive layouts at standard breakpoints.

**Acceptance Scenarios**:

1. **Given** any text or interactive element in the UI, **When** contrast ratios are measured against both light and dark themes, **Then** all elements meet WCAG AA minimum contrast ratios (4.5:1 for normal text, 3:1 for large text).
2. **Given** the Projects, Pipelines, and Agents pages, **When** a user navigates entirely by keyboard, **Then** all interactive elements are reachable and operable with visible focus indicators.
3. **Given** the application at viewport widths of 320px, 768px, 1024px, and 1920px, **When** each major page is rendered, **Then** all content remains accessible and no elements overflow or overlap.
4. **Given** both light and dark themes, **When** inspecting the stylesheets, **Then** zero hardcoded color values exist outside the theme definition files.

---

### User Story 7 — Chat and Voice Input Enhancements (Priority: P3)

As a developer using Solune's chat interface, I need voice input to work reliably across browsers, file attachments to be uploadable to GitHub issues, and issue descriptions to be pasteable with pipeline config selection so that I can interact with the system efficiently using multiple input methods.

**Why this priority**: Chat and input features enhance daily workflow efficiency. Voice input broken in Firefox, missing attachment support, and manual issue entry are friction points that collectively degrade the user experience for common tasks.

**Independent Test**: Can be fully tested by using voice input in Firefox and Chrome, uploading a file attachment that appears on the linked GitHub issue, and pasting an issue description to verify pipeline config selection works.

**Acceptance Scenarios**:

1. **Given** a user activates voice input in Firefox, **When** they speak a command, **Then** the speech is recognized and transcribed correctly using the browser's native speech recognition capability.
2. **Given** a user activates voice input in Chrome, **When** they speak a command, **Then** the speech is recognized and transcribed correctly.
3. **Given** a chat conversation linked to a GitHub issue, **When** a user uploads a file attachment, **Then** the file appears as an attachment on the corresponding GitHub parent issue.
4. **Given** the issue upload interface, **When** a user pastes an issue description and selects a pipeline configuration, **Then** the system creates the issue with the correct pipeline config association.

---

### User Story 8 — Comprehensive Documentation and Guided Onboarding (Priority: P3)

As a new user installing Solune for the first time, I need up-to-date documentation covering setup, configuration, and usage, plus an interactive onboarding tour that guides me through core features so that I can get started without external help.

**Why this priority**: Documentation and onboarding are critical for a public release. New users must be able to self-serve from README through first successful pipeline run. Stale docs and no onboarding lead to abandonment.

**Independent Test**: Can be fully tested by following the setup guide from scratch on a clean machine, completing the onboarding tour, and verifying all documented features match actual behavior.

**Acceptance Scenarios**:

1. **Given** a new user with no prior Solune experience, **When** they follow the setup documentation, **Then** they can deploy a working Solune instance within 30 minutes.
2. **Given** a first-time user logging into Solune, **When** the onboarding tour begins, **Then** a step-by-step guided tour highlights all major features (projects, pipelines, agents, chat) in sequence.
3. **Given** any documented feature or API endpoint, **When** the user follows the documentation, **Then** the behavior matches exactly what is documented.
4. **Given** the Help page, **When** a user browses FAQs, **Then** answers cover the 10 most common setup and usage questions.

---

### User Story 9 — Performance-Optimized Experience (Priority: P3)

As a developer using Solune during active development, I need the application to be responsive with minimal unnecessary background activity so that the tool does not slow down my workflow or consume excessive resources while idle.

**Why this priority**: Performance directly impacts developer experience. Unnecessary API calls, idle background activity, and slow renders waste resources and create a sluggish feel. Optimization must happen after features stabilize to avoid premature optimization.

**Independent Test**: Can be fully tested by measuring idle network activity before and after optimization, recording page load times and interaction latency, and verifying performance regression tests pass.

**Acceptance Scenarios**:

1. **Given** the application is open but the user is not interacting, **When** network activity is monitored for 60 seconds, **Then** idle API calls are reduced by at least 50% compared to the pre-optimization baseline.
2. **Given** any page in the application, **When** the user navigates to it, **Then** the page is fully interactive within 2 seconds on a standard connection.
3. **Given** a list of 50+ pipeline runs displayed, **When** the user scrolls through the list, **Then** the UI maintains smooth scrolling (60fps) without jank or dropped frames.
4. **Given** a UI interaction (button click, form submission), **When** the user performs the action, **Then** visual feedback appears within 100 milliseconds.

---

### User Story 10 — Production-Ready Release Package (Priority: P1)

As an administrator preparing to deploy Solune v0.1.0, I need a fully validated release package with correct versioning, secure container images, validated environment configuration, and a comprehensive release checklist so that I can deploy with confidence that everything has been verified.

**Why this priority**: Release engineering is a P1 because without it, no other work ships. Version consistency, secure container images, environment validation, and the release checklist are the final quality gate before public availability.

**Independent Test**: Can be fully tested by running the complete Docker Compose stack from scratch using only the example environment file, verifying all services start and become healthy, and confirming version strings are consistent across all configuration files.

**Acceptance Scenarios**:

1. **Given** a `.env` file configured with valid GitHub OAuth credentials (copied from `.env.example` with required secrets filled in), **When** `docker compose up` is executed, **Then** all services (backend, frontend, database) start and report healthy within 120 seconds.
2. **Given** the Docker container images, **When** inspecting the running processes, **Then** no container runs as the root user.
3. **Given** the version strings in the changelog, backend config, and frontend config, **When** they are compared, **Then** all display `0.1.0` consistently.
4. **Given** a production environment configuration, **When** the application starts with insecure settings (e.g., debug mode enabled, default secrets), **Then** startup is rejected with a clear error explaining the insecure configuration.
5. **Given** the complete release checklist, **When** each item is verified, **Then** all tests pass, coverage thresholds are met (≥70% frontend, ≥80% backend), mutation score thresholds are met (≥75% backend, ≥60% frontend), security scans report no critical/high findings, and documentation is current.

---

### Edge Cases

- What happens when the persistent storage becomes corrupted or inaccessible during a pipeline run? The system should detect the corruption, log a warning, and fall back to in-memory state while notifying the administrator.
- How does the system handle concurrent pipeline runs updating the same state storage simultaneously? The system should use transactional writes to prevent data races and ensure consistency.
- What happens when a user attempts to deploy with a partially configured environment file (some required variables present, others missing)? Startup validation should enumerate all missing variables in a single error message rather than failing one at a time.
- How does the pipeline builder handle extremely large pipelines (50+ stages in a single view)? The UI should remain responsive with virtualized rendering and provide zoom/pan controls.
- What happens when voice input is activated in a browser that supports neither the prefixed nor unprefixed Speech Recognition API? The system should display a clear message indicating voice input is unavailable in the current browser.
- How does the onboarding tour behave if the user dismisses it midway and later wants to restart it? The tour state should be persisted per user, with an option to restart from the Help page.
- What happens when a file attachment upload fails during chat-to-issue creation? The message should still be sent with an inline error indicating the attachment failed, and the user should be able to retry the upload.
- How does the system handle theme switching while a modal or overlay is open? Theme changes should apply immediately to all visible elements including modals, without requiring the user to close and reopen them.

## Requirements *(mandatory)*

### Functional Requirements

**Phase 1 — Security & Data Integrity (Release Blockers)**

- **FR-001**: System MUST persist all pipeline run states to durable storage so that no pipeline data is lost on application restart.
- **FR-002**: System MUST rebuild in-progress pipeline state from persistent storage on startup, resuming from the last known state.
- **FR-003**: System MUST NOT impose an arbitrary cap on the number of stored pipeline runs; historical data must remain accessible.
- **FR-004**: System MUST set all authentication cookies with HttpOnly and SameSite=Strict flags; the Secure flag MUST also be set when served over HTTPS.
- **FR-005**: System MUST enforce mandatory encryption key configuration on startup, refusing to start if secrets are missing or set to default values.
- **FR-006**: System MUST enforce project-level access control, returning 403 for unauthorized project access attempts.
- **FR-007**: System MUST NOT contain hardcoded secrets, API keys, or credentials anywhere in the source code.
- **FR-008**: System MUST validate and sanitize all user inputs at API boundaries before processing.

**Phase 2 — Code Quality Foundation**

- **FR-009**: All backend source files MUST NOT exceed 1,500 lines after refactoring.
- **FR-010**: All functions MUST have a cyclomatic complexity score of 25 or less.
- **FR-011**: Common utility functions (e.g., repository resolution) MUST exist in exactly one location with no duplicates.
- **FR-012**: All frontend component and hook modules MUST NOT exceed 200 lines after decomposition.
- **FR-013**: Dead code and unused build artifacts MUST be removed from the repository.
- **FR-014**: State representations MUST use typed enumerations rather than string or emoji-based identifiers.

**Phase 3 — Core Features**

- **FR-015**: System MUST support label-based pipeline state tracking, reducing API calls for state recovery by at least 50%.
- **FR-016**: System MUST support grouping pipeline stages into sequential and parallel execution groups.
- **FR-017**: System MUST provide a visual drag-and-drop pipeline builder with per-group sequential/parallel toggle.
- **FR-018**: System MUST display multiple running agents in a side-by-side layout with distinct visual differentiation.
- **FR-019**: System MUST propagate MCP tool configurations to all agent configuration files when project settings are updated.
- **FR-020**: Voice input MUST function correctly in both Firefox and Chrome browsers using the appropriate Speech Recognition API variant.
- **FR-021**: Users MUST be able to upload file attachments in chat that are forwarded to linked GitHub parent issues.
- **FR-022**: Users MUST be able to paste issue descriptions and select a pipeline configuration for issue creation.
- **FR-023**: The blocking feature MUST be fully removed from UI, backend logic, and data storage.

**Phase 4 — Security Hardening**

- **FR-024**: All container images MUST run as non-root users.
- **FR-025**: System MUST include HTTP security headers: Content Security Policy, Strict-Transport-Security, Referrer-Policy, and Permissions-Policy.
- **FR-026**: System MUST enforce rate limiting on authentication and other sensitive endpoints.
- **FR-027**: System MUST NOT store sensitive data in browser localStorage without encryption.
- **FR-028**: Debug mode MUST be fully decoupled from production configuration and disabled by default.

**Phase 5 — Performance Optimization**

- **FR-029**: System MUST reduce idle background API calls by at least 50% compared to the pre-optimization baseline.
- **FR-030**: System MUST reuse cached data where possible, targeting approximately 30% reduction in redundant requests.
- **FR-031**: System MUST skip data refreshes when the underlying data has not changed.
- **FR-032**: Frontend MUST render only components affected by state changes, avoiding unnecessary full-page rerenders.

**Phase 6 — Visual Polish & Accessibility**

- **FR-033**: All UI elements MUST meet WCAG AA contrast ratios (4.5:1 for normal text, 3:1 for large text) in both light and dark themes.
- **FR-034**: All interactive elements MUST be reachable and operable via keyboard navigation with visible focus indicators.
- **FR-035**: No hardcoded color values MUST exist outside of theme definition files.
- **FR-036**: All pages MUST be responsive and usable at viewport widths from 320px to 1920px.

**Phase 7 — Documentation & Onboarding**

- **FR-037**: All documentation MUST be current and accurately reflect the application's actual behavior and configuration.
- **FR-038**: System MUST provide an interactive, step-by-step onboarding tour for first-time users covering all major features.
- **FR-039**: System MUST include a Help page with answers to the most common setup and usage questions.
- **FR-040**: All API endpoints MUST be documented in an exportable format.

**Phase 8 — Test Coverage**

- **FR-041**: Backend test coverage MUST reach at least 80% line coverage.
- **FR-042**: Frontend test coverage MUST reach at least 70% line coverage.
- **FR-043**: End-to-end tests MUST cover all major user flows including project creation, pipeline configuration, agent execution, and PR review.
- **FR-044**: End-to-end tests MUST include automated accessibility assertions.
- **FR-050**: Backend tests MUST achieve a mutation score of at least 75%, validating that tests effectively detect code changes.
- **FR-051**: Frontend tests MUST achieve a mutation score of at least 60%, validating that tests effectively detect code changes.
- **FR-052**: The test suite MUST maintain reliability with no more than 5 quarantined flaky tests at any time.

**Phase 9 — Release Engineering**

- **FR-045**: All version strings across changelog, backend, and frontend configurations MUST consistently display `0.1.0`.
- **FR-046**: Container images MUST use pinned base image versions (no `latest` tags).
- **FR-047**: The environment example file MUST document all required configuration variables.
- **FR-048**: System MUST reject startup with insecure production configuration (default secrets, debug mode enabled).
- **FR-049**: The release MUST include no open P1 or P2 bugs.

### Key Entities

- **Pipeline Run**: A single execution of a pipeline configuration, with states for each stage, start/end timestamps, and outcome. Related to a Project and Pipeline Configuration.
- **Pipeline Configuration**: A user-defined sequence of stages and groups (sequential/parallel) that defines how agents are orchestrated. Owned by a Project.
- **Stage Group**: A logical grouping of pipeline stages that execute either sequentially or in parallel. Part of a Pipeline Configuration.
- **Project**: A workspace representing a GitHub repository or set of repositories, with associated pipeline configurations, agents, and access controls.
- **Agent**: An AI coding agent instance with an assigned role, MCP tool configuration, and visual identity. Runs within a Pipeline Stage.
- **MCP Tool Configuration**: The set of Model Context Protocol tools available to agents within a project, propagated to agent configuration files.
- **User Session**: An authenticated user's active session, governed by secure cookies and project-level access permissions.
- **Onboarding Tour State**: Per-user tracking of onboarding progress, supporting pause/resume and restart from the Help page.

## Assumptions

- The existing OAuth-based authentication flow will be retained; no new authentication methods are being introduced.
- Docker Compose is the sole supported deployment method for v0.1.0; cloud deployment is explicitly out of scope.
- The "Solune" rebrand and monorepo restructuring are already substantially complete and do not require significant additional work.
- Performance baselines will be established after feature stabilization (Phase 5), not before, to avoid measuring throwaway code paths.
- Standard web application performance expectations apply (sub-2-second page loads, 100ms interaction response) unless specified otherwise.
- The existing database migration framework supports the new persistent storage requirements without introducing a new migration tool.
- Cross-browser support targets current stable versions of Chrome, Firefox, Edge, and Safari at time of release.
- The 9-step onboarding tour follows the existing application's celestial theme for visual consistency.
- Signal integration (QR link for send/receive messages) is an existing feature that must continue working, not a new feature to build.
- The "blocking feature" to be removed in Phase 3 Track D refers to an existing UI/backend feature that is no longer needed, and its full scope is already understood by the team.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero data loss — pipeline state survives 100% of application restarts with full state recovery within 5 seconds.
- **SC-002**: Zero critical or high security findings reported by automated security scanning tools on the final release candidate.
- **SC-003**: All backend source files are under 1,500 lines and all functions have cyclomatic complexity ≤ 25 as verified by static analysis.
- **SC-004**: Users can create a pipeline with mixed sequential/parallel groups using the visual builder in under 5 minutes without reading documentation.
- **SC-005**: Backend test coverage reaches at least 80% line coverage.
- **SC-006**: Frontend test coverage reaches at least 70% line coverage.
- **SC-007**: All UI elements pass WCAG AA contrast ratio requirements in both light and dark themes.
- **SC-008**: A new user completes the onboarding tour and creates their first project within 30 minutes of initial deployment.
- **SC-009**: Idle background API activity is reduced by at least 50% from the pre-optimization baseline.
- **SC-010**: Every page in the application is fully interactive within 2 seconds on a standard broadband connection.
- **SC-011**: Fresh `docker compose up` from a `.env` file populated with the required OAuth credentials results in all services reporting healthy within 120 seconds.
- **SC-012**: Full end-to-end user flow (create project → configure pipeline → run agents → review PR) completes successfully.
- **SC-013**: Voice input functions correctly in both Chrome and Firefox.
- **SC-014**: All version strings consistently display `0.1.0` across all configuration files and the changelog.
- **SC-015**: Zero open P1 or P2 bugs at release time.
- **SC-016**: Backend mutation score reaches at least 75%, confirming tests catch real code defects.
- **SC-017**: Frontend mutation score reaches at least 60%, confirming tests catch real code defects.
- **SC-018**: No more than 5 tests are quarantined for flakiness at any point during the release cycle.

## Risks

- **Frontend coverage gap**: Current frontend test coverage is 49%, and the 70% target represents a significant increase. If 70% is not achievable by release, consider shipping at 60% with a tracked post-release commitment and a documented plan to close the remaining gap.
- **God class refactor**: The largest backend service file is over 5,000 lines and must be split into multiple focused services. This is the highest-risk refactor — complete it early in Phase B to maximize time for regression discovery before release.
- **Prior feature validation**: Features 037–042 are assumed to be already implemented and merged. Confirm all prior feature branches are fully integrated before starting v0.1.0 tasks to avoid scope surprises or merge conflicts.

## Constraints & Decisions

- Docker Compose is the sole supported deployment method for v0.1.0; cloud-hosted deployment options are explicitly out of scope and will ship post-release.
- Coverage targets (≥80% backend, ≥70% frontend) are minimum release gates, not aspirational targets. The separate comprehensive test coverage specification targets higher thresholds for a future milestone.
- Prior features (037–042) are already implemented — v0.1.0 wraps them into a coherent, production-ready package rather than building them from scratch.
- The Azure infrastructure-as-code specification is not a release blocker and will ship independently after v0.1.0.
