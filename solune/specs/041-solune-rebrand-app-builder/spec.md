# Feature Specification: Solune Rebrand & App Builder Architecture

**Feature Branch**: `041-solune-rebrand-app-builder`  
**Created**: 2026-03-14  
**Status**: Draft  
**Input**: User description: "Plan: Solune Rebrand + App Builder Architecture"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Monorepo Restructure and Archive (Priority: P1)

A platform maintainer archives the current repository state, then restructures the project into a monorepo layout with two top-level directories: one for the core platform (containing existing backend, frontend, docs, scripts, and specs) and one for generated applications. The `.github/` directory is relocated to the repository root so that workflows and agent configurations serve the entire monorepo. All internal paths in configuration files, build contexts, CI workflows, and scripts are updated to reflect the new directory structure.

**Why this priority**: This is the foundational structural change that every other phase depends on. Without the monorepo layout in place, rebranding targets the wrong paths, app management has no `apps/` directory to scaffold into, and CI/CD pipelines break. If only this story is delivered, the project has a clean, future-proof structure.

**Independent Test**: Can be fully tested by verifying that the repository builds and all existing tests pass from the new directory structure, that the archive tag exists, and that the `apps/` directory is present at the repository root.

**Acceptance Scenarios**:

1. **Given** the current repository has all source files at the top level, **When** the restructure is executed, **Then** all existing source files reside under the `solune/` subdirectory while `.github/` remains at the repository root.
2. **Given** the restructure is complete, **When** a developer checks the repository root, **Then** it contains exactly: `solune/`, `apps/`, `.github/`, root-level `README.md`, and root-level `docker-compose.yml`.
3. **Given** configuration files reference old paths (e.g., `./backend`), **When** paths are updated, **Then** all build contexts, volume mounts, and script references point to the new `./solune/backend` (or equivalent) locations.
4. **Given** the archive process has run, **When** a developer looks for the pre-restructure state, **Then** a tag or zip archive exists capturing the repository as it was before the migration.
5. **Given** the `apps/` directory is created, **When** a developer lists its contents, **Then** it contains a `.gitkeep` file so the empty directory is tracked by version control.

---

### User Story 2 - Full Product Rebrand to Solune (Priority: P1)

A platform maintainer performs a comprehensive rebrand across the entire codebase, replacing all occurrences of the old product name and related identifiers with the new "Solune" branding. This includes project configuration files, service names, volume names, data paths, frontend page headings, login branding, sidebar marks, README content, and developer documentation. The README is rewritten to reflect Solune's identity as an agent-driven development platform.

**Why this priority**: The rebrand establishes the product identity and must land early to provide a clean baseline for all subsequent work. Rebranding after other features are built would require re-doing string replacements across new code. Co-equal with Story 1 because it can proceed in parallel once the monorepo structure is established.

**Independent Test**: Can be fully tested by performing a case-insensitive search across the entire codebase for old brand strings ("Agent Projects", "ghchat-", "github-workflows") and verifying zero matches remain, then confirming the application launches with correct branding on all visible pages.

**Acceptance Scenarios**:

1. **Given** configuration files contain old project names (e.g., `agent-projects-backend`, `ghchat-network`), **When** the rebrand is applied, **Then** every occurrence is replaced with the corresponding Solune equivalent (`solune-backend`, `solune-network`).
2. **Given** the frontend displays "Agent Projects" on the main page heading, **When** the rebrand is applied, **Then** the heading displays "Solune".
3. **Given** data paths reference `/var/lib/ghchat/data`, **When** the rebrand is applied, **Then** all references point to `/var/lib/solune/data`.
4. **Given** the old README describes "GitHub Workflows Chat", **When** the README is rewritten, **Then** it presents Solune as an "Agent-driven development platform" with updated product pitch, feature descriptions, and badges.
5. **Given** developer documentation references the old repository name, **When** docs are updated, **Then** all internal links, badges, and references use the new "solune" name.
6. **Given** the application is launched after the rebrand, **When** a user visits the login page, main page, and sidebar, **Then** all visible branding consistently shows "Solune" with no remnants of old names.

---

### User Story 3 - App Management and Lifecycle (Priority: P2)

A platform user creates a new application through the system by providing a name, description, and optional pipeline association. The system validates the name, scaffolds the application directory with standard project files, creates a tracking issue, and registers the application in the platform. The user can subsequently list all applications, view details of a specific app, start it, stop it, or delete it. Each application has a clear lifecycle status (creating, active, stopped, error).

**Why this priority**: App management is the core new capability that transforms Solune from a single-project tool into a multi-app platform. It depends on the monorepo structure (Story 1) for the `apps/` directory but is otherwise independently deliverable. This story enables all subsequent app-related features (preview, context switching).

**Independent Test**: Can be fully tested by creating an application, verifying the scaffolded directory and tracking issue exist, then cycling through start/stop/delete operations and confirming each status transition and the final cleanup.

**Acceptance Scenarios**:

1. **Given** a user provides a valid app name and description, **When** the app is created, **Then** a directory is scaffolded under `apps/<app-name>/` with standard project files (README, configuration placeholder, source directory, changelog).
2. **Given** a user provides an app name with invalid characters (spaces, path traversal sequences, special characters), **When** creation is attempted, **Then** the system rejects the request with a clear validation error.
3. **Given** an application exists in "active" status, **When** the user stops it, **Then** the status transitions to "stopped" and the app's processes are terminated gracefully.
4. **Given** an application exists, **When** the user requests its details, **Then** the system returns the app's name, display name, description, status, associated pipeline, creation date, and directory path.
5. **Given** multiple applications exist, **When** the user lists all apps, **Then** every registered application is returned with its current status.
6. **Given** a user deletes an application, **When** deletion completes, **Then** the app directory is removed, the tracking issue is closed, and the app no longer appears in listings.
7. **Given** an app creation includes a pipeline association, **When** the app is created, **Then** a parent tracking issue is created linking the app to the specified pipeline.

---

### User Story 4 - Apps Page with Live Preview (Priority: P2)

A platform user navigates to the Apps page in the frontend to see all registered applications displayed as cards with their name, description, status, and action controls. Selecting an application opens a detail view with an embedded live preview of the running app alongside start and stop controls. The preview loads the application's local URL in an isolated frame, and users can interact with the running app directly from the platform.

**Why this priority**: The Apps page is the primary user interface for the multi-app capability. Without it, app management exists only as a backend feature. It depends on app management (Story 3) being functional but can be developed in parallel with mock data.

**Independent Test**: Can be fully tested by navigating to the Apps page, verifying card rendering for multiple apps in various states, opening a detail view for a running app, and confirming the preview frame loads and the start/stop controls update the app status correctly.

**Acceptance Scenarios**:

1. **Given** three applications exist (one active, one stopped, one in error state), **When** the user opens the Apps page, **Then** all three are displayed as cards with their correct name, description, and status indicator.
2. **Given** an application is in "active" status, **When** the user selects it, **Then** a detail view opens with an embedded preview frame showing the running application.
3. **Given** an application is stopped, **When** the user clicks the start button, **Then** the application transitions to "active" and the preview frame loads within 10 seconds.
4. **Given** an application is running, **When** the user clicks the stop button, **Then** the application transitions to "stopped" and the preview frame displays an appropriate offline state.
5. **Given** an application is in "error" status, **When** the user views the card, **Then** the status indicator clearly conveys the error state and provides access to relevant error information.

---

### User Story 5 - Slash Command Context Switching (Priority: P3)

A platform user types a slash command in the chat interface using the format `/<app-name>` to switch the active context to a specific application. Once the context is switched, all subsequent chat interactions, agent operations, and pipeline executions target the selected application's directory and configuration. The user can see which app context is currently active and switch between apps without losing conversation history.

**Why this priority**: Context switching is an ergonomic enhancement that makes working with multiple apps fluid. It depends on both app management (Story 3) and the chat infrastructure but is not required for the core platform to function. Users can still manually manage apps without this feature.

**Independent Test**: Can be fully tested by creating two apps, typing `/<app-name>` in the chat, verifying the context indicator changes, and confirming that subsequent agent operations target the correct application directory.

**Acceptance Scenarios**:

1. **Given** two applications exist ("app-alpha" and "app-beta"), **When** the user types `/app-alpha` in the chat, **Then** the active context switches to app-alpha and a visible indicator shows the current context.
2. **Given** the user is in app-alpha context, **When** the user types `/app-beta`, **Then** the context switches to app-beta and the indicator updates accordingly.
3. **Given** the user types a slash command for a non-existent app, **When** the command is processed, **Then** the system returns an informative error suggesting available app names.
4. **Given** the user switches context, **When** they review their conversation history, **Then** previous messages are preserved and visible regardless of context switches.

---

### User Story 6 - Admin Guard for Self-Editing Protection (Priority: P3)

The platform provides two guard mechanisms (`@admin` and `@adminlock`) that prevent automated agents from modifying the platform's own core files during app-building operations. The `@admin` guard routes requests that would affect the `solune/` directory through an elevated permission check, and `@adminlock` prevents any agent modification to designated protected paths entirely. This ensures that agents building applications in `apps/` cannot accidentally or intentionally alter the platform itself.

**Why this priority**: Self-editing protection is a safety guardrail that becomes important once agents are actively building apps. It depends on the monorepo structure to distinguish between platform code (`solune/`) and app code (`apps/`). While critical for production safety, the platform functions without it during development.

**Independent Test**: Can be fully tested by configuring protected paths, then attempting agent operations that target both `solune/` (should be blocked or require elevation) and `apps/` (should proceed normally), verifying correct enforcement.

**Acceptance Scenarios**:

1. **Given** an agent is operating in app-building mode, **When** it attempts to modify a file in the `solune/` directory, **Then** the `@admin` guard intercepts the request and requires elevated permission before proceeding.
2. **Given** a path is designated with `@adminlock`, **When** any agent attempts to modify files in that path, **Then** the modification is rejected entirely with a clear explanation.
3. **Given** an agent is operating on files within `apps/<app-name>/`, **When** it creates, modifies, or deletes files, **Then** no guard intervention occurs and operations proceed normally.
4. **Given** the guard configuration is updated to add a new protected path, **When** subsequent agent operations target that path, **Then** the protection is enforced immediately without requiring a restart.

---

### Edge Cases

- What happens when the monorepo restructure encounters files with hardcoded absolute paths? The update process should identify and correct all internal path references; any paths that cannot be automatically resolved should be flagged for manual review.
- How does the system handle an app name collision (attempting to create an app with the same name as an existing one)? The system should reject the creation with a clear "name already in use" error and suggest an alternative.
- What happens when a running application crashes during the preview? The preview frame should display an error state and the app status should transition to "error" with accessible log information.
- What happens when an agent operation spans both `solune/` and `apps/` directories in a single request? The `@admin` guard should evaluate each file path individually and block only the protected paths while allowing the app paths.
- How does the system handle the deletion of an app that is currently running? The system should stop the app first, then proceed with deletion, or reject the deletion and require the user to stop it first.
- What happens when a user switches context to an app that is in "creating" state? The system should allow the context switch but clearly indicate that the app is still being set up and some operations may not be available yet.

## Requirements *(mandatory)*

### Functional Requirements

**Phase 1 — Monorepo Structure**

- **FR-001**: System MUST archive the current repository state as a tag or zip before any restructuring begins, providing a recovery point.
- **FR-002**: System MUST relocate all existing source files (backend, frontend, docs, scripts, specs, configuration files, changelog) into a `solune/` subdirectory at the repository root.
- **FR-003**: System MUST create an `apps/` directory at the repository root with a `.gitkeep` file for version control tracking.
- **FR-004**: System MUST move the `.github/` directory to the repository root so that workflows and agent configurations serve the entire monorepo.
- **FR-005**: System MUST create a root-level `README.md` and root-level `docker-compose.yml` that orchestrate the entire monorepo.
- **FR-006**: System MUST update all internal path references (build contexts, volume mounts, CI workflows, scripts, dev container configuration, MCP configuration) to reflect the new `solune/` subdirectory structure.

**Phase 2 — Rebrand**

- **FR-007**: System MUST replace all occurrences of old product names and identifiers with Solune equivalents across the entire codebase (approximately 70+ files), including project names, service names, volume names, network names, and data paths.
- **FR-008**: System MUST update frontend branding on all user-visible pages (main page heading, login page, sidebar brand mark) to display "Solune".
- **FR-009**: System MUST rewrite the README to present Solune as an agent-driven development platform with an updated product pitch, feature descriptions, and repository badges.
- **FR-010**: System MUST rewrite the developer instructions document to reflect the new monorepo structure, Solune's role as a platform, how agents operate on `apps/` subdirectories, and the `@admin`/`@adminlock` routing model.
- **FR-011**: System MUST ensure zero occurrences of old brand strings ("Agent Projects", "ghchat-", "GitHub Workflows Chat", "github-workflows" as product name) remain in the codebase after the rebrand.

**Phase 3 — App Management**

- **FR-012**: System MUST provide a data model for applications that tracks: name (unique identifier), display name, description, directory path, associated pipeline, status (creating, active, stopped, error), repository type (same-repo or external-repo), external repository URL, and creation timestamp.
- **FR-013**: System MUST provide operations to create, list, retrieve, update, start, stop, and delete applications.
- **FR-014**: System MUST validate application names to allow only alphanumeric characters and hyphens, rejecting any input containing path traversal sequences, spaces, or special characters.
- **FR-015**: System MUST scaffold a new application directory under `apps/<app-name>/` on creation, including a README, configuration placeholder, source directory, and changelog.
- **FR-016**: System MUST create a parent tracking issue on application creation and close it upon deletion.
- **FR-017**: System MUST enforce valid status transitions: creating → active, active → stopped, stopped → active, any → error, and creating/stopped/error → deleted.
- **FR-018**: System MUST prevent deletion of a running application, requiring the user to stop it first or performing an automatic graceful stop before deletion.

**Phase 4 — Apps Page Frontend**

- **FR-019**: System MUST provide an Apps page accessible from the main navigation that displays all registered applications as cards showing name, description, and status.
- **FR-020**: System MUST provide a detail view for each application that includes an embedded live preview of running applications and start/stop controls.
- **FR-021**: System MUST display appropriate visual indicators for each application status (creating, active, stopped, error) using distinct colors or icons.
- **FR-022**: System MUST load the application preview within an isolated embedded frame pointing to the app's local URL when the app is in "active" status.

**Phase 5 — Slash Command Context Switching**

- **FR-023**: System MUST support a `/<app-name>` slash command in the chat interface that switches the active working context to the specified application.
- **FR-024**: System MUST display a visible indicator in the chat interface showing the currently active application context.
- **FR-025**: System MUST validate slash commands against the list of existing applications and return an informative error with suggestions for non-existent app names.
- **FR-026**: System MUST preserve conversation history across context switches, allowing users to review previous messages regardless of context changes.

**Phase 6 — Admin Guard**

- **FR-027**: System MUST provide an `@admin` guard that intercepts agent operations targeting the `solune/` directory and requires elevated permission before allowing modifications.
- **FR-028**: System MUST provide an `@adminlock` guard that unconditionally blocks any agent modification to designated protected paths.
- **FR-029**: System MUST allow agent operations on files within `apps/` directories to proceed without guard intervention.
- **FR-030**: System MUST evaluate guard rules on a per-file basis when an operation spans multiple directories, blocking only the protected paths.

### Key Entities

- **Application (App)**: A user-created project managed by the platform. Key attributes: unique name (alphanumeric + hyphens), display name, description, status (creating/active/stopped/error), associated pipeline, repository type (same-repo or external-repo), directory path within `apps/`, and creation timestamp.
- **Application Status**: The lifecycle state of an application. Valid values: creating (being scaffolded), active (running and previewable), stopped (not running), error (failed operation). Transitions are constrained to valid sequences.
- **Pipeline Association**: The link between an application and an agent pipeline that drives its development. An app may optionally be associated with one pipeline at creation time.
- **App Context**: The active working scope in the chat interface. Determines which application's directory and configuration are targeted by subsequent agent operations and pipeline executions.
- **Guard Rule**: A protection configuration that maps file paths to access levels. `@admin` requires elevated permission; `@adminlock` blocks all agent modifications. Rules are evaluated per-file for mixed-path operations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All existing tests (backend and frontend) pass after the monorepo restructure — zero regressions from the directory migration.
- **SC-002**: The application builds and starts successfully from the new monorepo structure with all services communicating correctly.
- **SC-003**: A case-insensitive search across the entire codebase for old brand strings returns zero matches after the rebrand.
- **SC-004**: All user-visible pages (login, main page, sidebar, README) consistently display "Solune" branding with no remnants of old names.
- **SC-005**: Users can create a new application in under 1 minute, from name entry to seeing the scaffolded directory and tracking issue.
- **SC-006**: All application lifecycle transitions (create → start → stop → delete) complete successfully with correct status updates visible within 5 seconds.
- **SC-007**: The Apps page loads and displays all registered applications within 3 seconds, with correct status indicators for each state.
- **SC-008**: The embedded app preview loads a running application within 10 seconds of opening the detail view.
- **SC-009**: Context switching via `/<app-name>` completes within 2 seconds and subsequent agent operations target the correct application directory.
- **SC-010**: Agent operations targeting `solune/` are blocked by the guard, while operations targeting `apps/` proceed unimpeded — verified by attempting modifications to both paths.
- **SC-011**: Application name validation rejects 100% of invalid inputs (path traversal, special characters, spaces) while accepting all valid names (alphanumeric + hyphens).

## Assumptions

- The existing codebase is functional and all current tests pass before restructuring begins.
- The archive of the pre-restructure state (tag or zip) provides an adequate recovery mechanism if the migration encounters issues.
- Frontend branding in `index.html` already references "Solune" and does not need updating.
- Application name uniqueness is enforced at the platform level — no two apps can share the same name.
- Applications run on dynamically assigned local ports, and the platform manages port allocation for preview URLs.
- The chat infrastructure already supports slash commands or can be extended to support them without a fundamental redesign.
- Agent operations go through a routing layer where guard rules can be evaluated before file system access is granted.
- The `same-repo` repository type means the app lives in the `apps/` directory; `external-repo` means it references a separate repository URL for future extensibility.
- The root-level service orchestration configuration manages all services (Solune platform + any running apps) through a single entry point.
- Guard configurations are stored alongside the platform's configuration and can be updated without service restart.
