# Feature Specification: SQLite-Backed Durable Persistence for Settings & Sessions

**Feature Branch**: `005-sqlite-settings-persistence`  
**Created**: 2026-02-19  
**Status**: Draft  
**Input**: User description: "Add SQLite-backed durable persistence layer for user configuration, sessions, and settings with dedicated Settings UI"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Persistent Sessions Across Restarts (Priority: P1)

As an authenticated user, I want my login session to survive server and container restarts so that I do not have to re-authenticate every time the backend process cycles.

**Why this priority**: Session loss is the most disruptive consequence of the current in-memory-only storage. Every restart forces every user to log in again, breaking ongoing work. Solving this is the foundation for all other durable settings.

**Independent Test**: Log in, restart the backend container, and verify the session is still valid without re-authenticating.

**Acceptance Scenarios**:

1. **Given** a user is authenticated and has an active session, **When** the backend server restarts, **Then** the user's session is still valid and the user remains logged in.
2. **Given** a user is authenticated, **When** the Docker container is stopped and started again, **Then** the session data persists because the database file is stored on a volume that survives container lifecycle events.
3. **Given** a session has exceeded the configured expiration time (default 8 hours), **When** the user makes a request, **Then** the session is treated as expired and the user is prompted to log in again.
4. **Given** the application starts for the first time with no existing database file, **When** the backend initializes, **Then** the database and all required tables are created automatically.

---

### User Story 2 — Manage AI Preferences via Settings Page (Priority: P1)

As a user, I want to configure my default AI provider, preferred model, and temperature from a dedicated Settings page so that every AI-powered interaction uses my preferred configuration without me having to specify it each time.

**Why this priority**: AI preferences directly affect every chat and workflow interaction. Providing a UI to manage these is core to the feature's value proposition and exercises the full settings persistence round-trip (frontend → API → database → API → frontend).

**Independent Test**: Open the Settings page, change the AI provider and model, save, refresh the page, and verify the saved values are loaded.

**Acceptance Scenarios**:

1. **Given** the user navigates to the Settings page, **When** the page loads, **Then** the AI Preferences section displays the user's current effective settings (personal overrides merged over global defaults).
2. **Given** the user changes the AI provider from "copilot" to "azure_openai" and clicks Save, **When** the save completes, **Then** the system displays a success message and the new preference is persisted.
3. **Given** the user has not set any AI preferences, **When** the Settings page loads, **Then** the AI Preferences section shows the global default values (seeded from environment variables).

---

### User Story 3 — Settings Page Navigation and Theme Sync (Priority: P2)

As a user, I want to access a Settings tab in the header navigation and manage my UI preferences — including theme — from a centralized page that stays in sync with the existing theme toggle.

**Why this priority**: A dedicated Settings page is the primary UI surface for this feature. Theme sync demonstrates the bidirectional binding pattern that all other UI preferences will follow.

**Independent Test**: Click the Settings tab, toggle the theme from the Settings page, and verify the app theme changes immediately. Then toggle the theme from the header button and verify the Settings page reflects the change.

**Acceptance Scenarios**:

1. **Given** the user is authenticated, **When** they look at the header navigation, **Then** they see a "Settings" tab alongside "Chat" and "Project Board."
2. **Given** the user clicks the Settings tab, **When** the Settings page loads, **Then** it displays organized sections for AI Preferences, UI & Display, Workflow Defaults, Notification Preferences, and Project Settings.
3. **Given** the user toggles the theme to dark mode on the Settings page, **When** the toggle changes, **Then** the application theme switches to dark mode immediately without a page reload, and the header theme button reflects the new state.
4. **Given** the user toggles the theme using the existing header theme button, **When** the Settings page is open, **Then** the theme toggle on the Settings page reflects the updated state.
5. **Given** the user changes the default active view to "board" and saves, **When** they next open the application, **Then** the default view shown is the Project Board.

---

### User Story 4 — Workflow Defaults and Notification Preferences (Priority: P2)

As a user, I want to override the system-wide workflow defaults (default repository, default assignee, Copilot polling interval) and configure which event notifications I receive, so that the application behaves according to my personal workflow.

**Why this priority**: Workflow defaults and notification preferences personalize the application behavior and are currently locked to environment variables or not configurable at all. This story completes the per-user settings picture.

**Independent Test**: Set a personal default repository in Settings, create a new issue via chat, and verify it targets the user-specified repository instead of the environment-variable default.

**Acceptance Scenarios**:

1. **Given** the user opens the Workflow Defaults section in Settings, **When** the page loads, **Then** the fields show the user's personal overrides or fall back to the global defaults.
2. **Given** the user sets a personal default repository and saves, **When** the user later triggers an action that uses the default repository, **Then** the system uses the user's override rather than the global default.
3. **Given** the user enables notifications for "task status changes" and disables "agent completions," **When** they save and reload the page, **Then** the notification preferences reflect the saved state.

---

### User Story 5 — Project-Level Settings (Priority: P3)

As a user, I want to configure settings scoped to a specific project — such as board display preferences and agent pipeline mappings — so that different projects can have different configurations.

**Why this priority**: Project-level settings add a scoping dimension beyond global and per-user. This is important but less urgent than establishing the core persistence and Settings UI.

**Independent Test**: Open Settings, select a project, configure a project-specific display preference, save, switch to another project, verify the setting differs, switch back, and verify the original project retains its setting.

**Acceptance Scenarios**:

1. **Given** the user opens the Project Settings section, **When** they select a project, **Then** the section displays settings scoped to that project (or defaults if no project-specific settings exist).
2. **Given** the user changes a display preference for Project A and saves, **When** they switch to Project B, **Then** the display preference for Project B is unaffected.
3. **Given** the user has not set any project-specific settings, **When** they view the Project Settings section, **Then** the system shows the user's global preference values as defaults.

---

### User Story 6 — Global/Instance-Level Settings (Priority: P3)

As an administrator (or the first authenticated user), I want to configure global defaults — such as the default AI provider, allowed models, and global workflow defaults — so that all users start with a sensible baseline that I control.

**Why this priority**: Global settings provide the foundation for the merged-settings pattern but do not block individual user value until per-user overrides are in place.

**Independent Test**: Set a global default AI provider to "azure_openai," log in as a different user who has not set a personal preference, and verify the AI Preferences section on their Settings page shows "azure_openai."

**Acceptance Scenarios**:

1. **Given** the application starts for the first time, **When** the global settings are loaded, **Then** they are seeded from the current environment variables (AI_PROVIDER, COPILOT_MODEL, DEFAULT_REPOSITORY, DEFAULT_ASSIGNEE, COPILOT_POLLING_INTERVAL).
2. **Given** an authenticated user opens the Global Settings section, **When** they update the default AI provider and save, **Then** the new global default is persisted and returned to all users who have not set a personal override.
3. **Given** a user has a personal AI provider override, **When** the global AI provider default is changed, **Then** the user's personal override still takes precedence in their merged settings response.

---

### Edge Cases

- What happens when the SQLite database file is deleted or corrupted while the application is running? The system should detect initialization failures at startup and create a new database with the default schema if the file is missing. If corruption is detected during a query, the system should log the error and return a clear error response rather than crashing.
- What happens when a user saves settings with invalid values (e.g., a temperature outside the valid range, an unrecognized AI provider)? The system should validate inputs and return meaningful error messages without persisting invalid data.
- What happens when the frontend attempts to save settings while offline or the backend is unreachable? The frontend should retain the last-known values in localStorage and display an error message indicating the save failed.
- What happens when two browser tabs save conflicting settings simultaneously? The system should use a last-write-wins strategy; the most recently saved value is the one that persists.
- What happens when a user's session references a project that no longer exists? The project-level settings endpoint should return a 404 or empty defaults and not crash.
- What happens when the global settings have never been initialized (fresh database, no env vars for optional fields)? The system should use sensible built-in defaults (e.g., ai_provider: "copilot", copilot_model: "gpt-4o", temperature: 0.7).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST store all durable user data (sessions, preferences, settings) in a persistent database, replacing the current in-memory-only approach for these data types. The existing in-memory cache may be retained exclusively for transient, short-lived API response caching.
- **FR-002**: System MUST persist the existing UserSession model to the database so that authenticated sessions survive server and container restarts.
- **FR-003**: System MUST persist per-user AI preferences including: default AI provider (copilot or azure_openai), preferred model name, and temperature value.
- **FR-004**: System MUST persist per-user UI/display preferences including: theme (dark or light), default active view (chat, board, or settings), and sidebar collapsed state (true/false).
- **FR-005**: System MUST persist per-user workflow defaults including: default repository (owner/repo format), default assignee (GitHub username), and Copilot polling interval (in seconds). These override the environment-variable-based global defaults on a per-user basis.
- **FR-006**: System MUST persist per-user notification preferences as a set of toggleable event subscriptions. The minimum required event types are: task_status_changes, agent_completions, and new_recommendations.
- **FR-007**: System MUST persist per-user-per-project settings scoped by a project identifier. Project settings include board/workflow display preferences and agent pipeline mappings.
- **FR-008**: System MUST persist global/instance-level settings including: default AI provider, allowed model names, and global workflow defaults. Global settings MUST be seeded from environment variables on first startup. Per-user settings MUST take precedence over global defaults in all merged responses.
- **FR-009**: System MUST expose a GET endpoint for retrieving the authenticated user's effective merged preferences (global defaults + user overrides) and a PUT endpoint for updating the user's personal overrides.
- **FR-010**: System MUST expose a GET endpoint for retrieving global/instance-level settings and a PUT endpoint for updating them. Any authenticated user may modify global settings (no RBAC required).
- **FR-011**: System MUST expose a GET endpoint for retrieving per-project settings for the authenticated user and a PUT endpoint for updating them, both scoped by a project identifier.
- **FR-012**: System MUST persist the database file on a Docker volume so that data survives container restarts when deployed via docker-compose.
- **FR-013**: System MUST include a schema initialization strategy that creates all required tables on first startup and supports future schema evolution (e.g., versioned migrations or idempotent create-if-not-exists scripts).
- **FR-014**: System MUST add a "Settings" tab to the header navigation in the frontend, integrated with the existing view-switching mechanism alongside "Chat" and "Project Board."
- **FR-015**: System SHOULD synchronize the theme preference bidirectionally between the Settings page and the existing theme toggle in the header, so that changes in either location are immediately reflected in the other without a page reload.
- **FR-016**: System MUST validate all settings inputs on the server side (e.g., temperature within 0.0–2.0, AI provider is a recognized value) and return descriptive error messages for invalid data.
- **FR-017**: System MUST NOT implement multi-user RBAC, settings data export/import, or database backup/restore functionality.

### Key Entities

- **UserSession**: Represents an authenticated user's session. Key attributes: session identifier, GitHub user ID, GitHub username, avatar URL, access token (encrypted), refresh token (encrypted), token expiration, selected project, creation timestamp, last-updated timestamp. One session per user at a time.
- **UserSettings**: Represents the complete set of per-user preferences. Key attributes: GitHub user ID (owner), AI preferences (provider, model, temperature), UI preferences (theme, default view, sidebar state), workflow defaults (repository, assignee, polling interval), notification preferences (set of enabled event types). One record per user.
- **ProjectSettings**: Represents per-user-per-project configuration. Key attributes: GitHub user ID, project identifier, board/workflow display preferences, agent pipeline mappings. One record per user-project combination.
- **GlobalSettings**: Represents instance-level defaults that apply to all users. Key attributes: default AI provider, allowed models list, global workflow defaults (repository, assignee, polling interval). Singleton record seeded from environment variables on first run.

### Assumptions

- The existing GitHub OAuth authentication flow will continue to be used; this feature does not introduce a new authentication mechanism.
- The application has a single-instance deployment model (one backend process); multi-instance/distributed locking for the database is not required.
- Temperature values for AI models follow the standard range of 0.0 to 2.0.
- The "first user is admin" pattern is not required for the initial implementation; any authenticated user can modify global settings. This simplification is acceptable per the stated non-goals.
- Agent pipeline mappings in project settings follow the existing AgentAssignment model structure already defined in the codebase.
- Session expiration follows the existing SESSION_EXPIRE_HOURS configuration (default 8 hours).
- The in-memory cache will continue to be used for transient API response caching (project lists, project items) and does not need to be modified for those use cases.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Authenticated user sessions persist across server restarts — a user who was logged in before a restart remains logged in after the restart with zero re-authentication required (100% of valid, non-expired sessions survive).
- **SC-002**: Users can view and update all preference categories (AI, UI, workflow, notifications, project) from the Settings page and see their changes reflected within 2 seconds of saving.
- **SC-003**: Settings page loads the user's effective merged preferences (global defaults + personal overrides) in a single request, completing in under 1 second under normal conditions.
- **SC-004**: Theme changes made on the Settings page are reflected in the application UI immediately (within 200 milliseconds) without a page reload, and vice versa for changes made via the header toggle.
- **SC-005**: All settings data persists across Docker container restarts — stopping and starting the container does not lose any user preferences, project settings, or global configuration.
- **SC-006**: The database and all required tables are created automatically on first startup without any manual intervention or migration commands.
- **SC-007**: 100% of settings inputs are validated server-side; invalid values (out-of-range temperature, unrecognized provider) return descriptive error messages and are not persisted.
- **SC-008**: The Settings page is accessible via a clearly labeled tab in the header navigation, discoverable on first use without documentation.
