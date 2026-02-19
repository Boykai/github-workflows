# Feature Specification: SQLite-Backed Durable Settings & Session Persistence

**Feature Branch**: `005-sqlite-settings-persistence`  
**Created**: 2026-02-19  
**Status**: Draft  
**Input**: User description: "Add a SQLite-backed storage layer for user configuration and settings, replacing the current volatile in-memory-only persistence. The app currently stores sessions and all user state in a Python dict-based in-memory cache which is lost on every server restart. There is no database in the stack today."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Persistent User Sessions (Priority: P1)

As a Tech Connect user, I want my login session to survive server restarts so that I do not have to re-authenticate every time the backend container is restarted or redeployed.

**Why this priority**: Session persistence is the foundational requirement. Without it, every other settings feature is meaningless because user identity is lost on restart. This directly impacts every authenticated user on every restart.

**Independent Test**: Can be fully tested by logging in, restarting the backend container, and confirming the user remains authenticated without needing to log in again.

**Acceptance Scenarios**:

1. **Given** a user is logged in with an active session, **When** the backend server is restarted, **Then** the user's session is still valid and they remain authenticated without re-login.
2. **Given** a user's session has expired (beyond the configured session lifetime), **When** the user attempts an authenticated action, **Then** the system rejects the request and prompts re-authentication.
3. **Given** no database file exists on first startup, **When** the backend starts, **Then** the system creates the database and all required tables automatically.

---

### User Story 2 — Per-User AI & Workflow Preferences (Priority: P2)

As a Tech Connect user, I want to save my AI preferences (default provider, preferred model, temperature) and workflow defaults (default repository, default assignee, Copilot polling interval) so that my personalized configuration persists across sessions and server restarts.

**Why this priority**: AI and workflow preferences directly affect daily productivity. Users currently rely on environment variables for workflow defaults and have no per-user AI preference overrides. Persisting these removes the need for manual reconfiguration.

**Independent Test**: Can be fully tested by saving AI and workflow preferences via the Settings page, restarting the server, and confirming the saved preferences are still in effect.

**Acceptance Scenarios**:

1. **Given** a user is on the Settings page, **When** they change their default AI provider to "azure_openai" and save, **Then** the preference is stored and subsequent AI operations use the selected provider.
2. **Given** a user has saved workflow defaults (e.g., default repository = "my-org/my-repo"), **When** the user opens a new workflow, **Then** the saved repository is pre-selected.
3. **Given** no user-specific preferences have been saved, **When** the user views their settings, **Then** the system displays the global/instance-level defaults as the effective values.

---

### User Story 3 — UI & Display Preferences with Bidirectional Theme Sync (Priority: P2)

As a Tech Connect user, I want my UI preferences (theme, default view, sidebar state) persisted on the server and synchronized with local storage, so that my display preferences follow me across devices and remain consistent when toggled from any control.

**Why this priority**: Theme and display preferences are currently localStorage-only, meaning they do not roam across devices. Server-backed persistence with localStorage fallback improves cross-device consistency while maintaining offline resilience.

**Independent Test**: Can be fully tested by changing the theme on the Settings page, verifying it applies immediately, then toggling theme from the existing dark mode toggle and confirming the Settings page reflects the change.

**Acceptance Scenarios**:

1. **Given** a user changes their theme to "dark" on the Settings page, **When** the change is saved, **Then** the dark mode class is applied immediately and the existing theme toggle reflects the updated state.
2. **Given** a user toggles dark mode using the existing theme toggle (outside the Settings page), **When** the toggle occurs, **Then** the Settings page reflects the updated theme preference on next visit.
3. **Given** the user is unauthenticated or the backend is unreachable, **When** the user changes their theme, **Then** the preference is stored in localStorage and the UI updates normally (graceful fallback).
4. **Given** a user sets their default active view to "board", **When** they next open the application, **Then** the board view is displayed by default instead of chat.

---

### User Story 4 — Notification Preferences (Priority: P3)

As a Tech Connect user, I want to choose which events I receive notifications for (task status changes, agent completions, new recommendations) so that I only see relevant alerts.

**Why this priority**: Notification preferences add personalization but are not blocking for core functionality. The notification delivery mechanism itself is a separate concern; this story focuses on persisting the user's notification choices.

**Independent Test**: Can be fully tested by toggling notification preference checkboxes on the Settings page, saving, and confirming the preferences persist after page refresh and server restart.

**Acceptance Scenarios**:

1. **Given** a user is on the Notification Preferences section of the Settings page, **When** they uncheck "agent completions" and save, **Then** the preference is stored and the user no longer receives agent completion notifications.
2. **Given** a new user with no saved notification preferences, **When** they view their notification settings, **Then** all notification types are enabled by default (matching global defaults).

---

### User Story 5 — Project-Level Settings (Priority: P3)

As a Tech Connect user, I want to configure per-project settings (board/workflow configurations, agent pipeline mappings, display preferences) so that each project can have its own customized workflow.

**Why this priority**: Project-level settings provide granular customization but require the foundational per-user settings to be in place first. Most users start with a single project before needing per-project overrides.

**Independent Test**: Can be fully tested by selecting a project, configuring project-specific settings, switching projects, and confirming each project retains its own configuration.

**Acceptance Scenarios**:

1. **Given** a user has two projects, **When** they configure agent pipeline mappings for Project A, **Then** Project B's settings remain independent and unaffected.
2. **Given** a user has not configured project-specific settings, **When** they view a project's settings, **Then** the system displays the user's general defaults as the effective project settings.

---

### User Story 6 — Global/Instance-Level Settings (Priority: P3)

As an instance administrator (any authenticated user), I want to configure global defaults (default AI provider, allowed models, global workflow defaults) that serve as the baseline for all users, so that the instance has a consistent starting configuration.

**Why this priority**: Global settings provide the foundation for the settings hierarchy but can be seeded from existing environment variables on first boot, so immediate manual configuration is not required. This story adds the ability to modify those defaults at runtime.

**Independent Test**: Can be fully tested by changing a global setting (e.g., default AI provider), then logging in as a different user and confirming the new default is reflected.

**Acceptance Scenarios**:

1. **Given** an administrator changes the global default AI provider to "azure_openai", **When** a user with no personal AI preference override views their effective settings, **Then** they see "azure_openai" as their effective provider.
2. **Given** a user has a personal AI provider override set to "copilot", **When** the global default is changed to "azure_openai", **Then** the user's effective provider remains "copilot" (personal overrides take precedence).
3. **Given** the system starts for the first time, **When** the database is initialized, **Then** global settings are seeded from the current environment variables (AI_PROVIDER, DEFAULT_REPOSITORY, DEFAULT_ASSIGNEE, COPILOT_POLLING_INTERVAL).
4. **Given** the system starts after global settings have been previously saved, **When** the database already contains global settings, **Then** the existing values are preserved and environment variables do not overwrite them.

---

### User Story 7 — Dedicated Settings Page (Priority: P2)

As a Tech Connect user, I want a dedicated Settings page accessible from the header navigation so that I have a single place to manage all my preferences.

**Why this priority**: The Settings page is the primary interface for all preference management stories. Without it, users have no way to interact with the persisted settings.

**Independent Test**: Can be fully tested by navigating to the Settings page from the header, verifying all preference sections are visible, modifying a setting, and confirming save feedback (success/error indication).

**Acceptance Scenarios**:

1. **Given** a user is on any page, **When** they click the "Settings" tab in the header navigation, **Then** the Settings page is displayed with clearly organized sections for each preference category.
2. **Given** a user modifies a setting and clicks save, **When** the save completes successfully, **Then** a success indicator (toast or inline feedback) is displayed.
3. **Given** a user modifies a setting and the save fails (network error), **When** the error occurs, **Then** an error indicator is displayed and the unsaved changes are preserved in the form.

---

### Edge Cases

- What happens when the database file is corrupted or unreadable at startup? The system should log an error and attempt to recreate the database, starting fresh if necessary.
- What happens when a user attempts to save settings while the backend is temporarily unreachable? The frontend should display an error message and retain the unsaved form state so the user can retry.
- What happens when concurrent requests attempt to update the same user's settings simultaneously? The system should handle this gracefully — last write wins is acceptable for user preferences.
- What happens when the database volume mount is missing in the container? The system should still start (using an in-container path) but log a warning that data will not persist across container recreation.
- What happens when a user's session references a deleted or invalid project ID in project-level settings? The system should return the user's general defaults and discard the stale project reference.
- What happens when environment variable values change between restarts but global settings have already been saved? The previously saved global settings take precedence; environment variables are only used for initial seeding.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST persist user sessions to a durable store so that sessions survive server and container restarts.
- **FR-002**: System MUST create the database and all required tables automatically on first startup without manual intervention (schema initialization).
- **FR-003**: System MUST support forward-compatible schema evolution so that future updates can add or modify tables without losing existing data.
- **FR-004**: System MUST persist the database file via a container volume mount so that data survives container restarts and image rebuilds.
- **FR-005**: System MUST expose a settings retrieval endpoint for the authenticated user that returns the merged effective configuration (global defaults overlaid with user-specific overrides) in a single response.
- **FR-006**: System MUST expose a settings update endpoint for the authenticated user to save their personal preferences.
- **FR-007**: System MUST expose global settings retrieval and update endpoints accessible to any authenticated user for managing instance-level defaults.
- **FR-008**: System MUST expose per-project settings retrieval and update endpoints scoped to the authenticated user and a specific project identifier.
- **FR-009**: System MUST persist per-user AI preferences: default AI provider (copilot or azure_openai), preferred model, and temperature.
- **FR-010**: System MUST persist per-user UI/display preferences: theme (dark/light), default active view (chat/board), and sidebar collapsed state.
- **FR-011**: System MUST persist per-user workflow defaults: default repository, default assignee, and Copilot polling interval.
- **FR-012**: System MUST persist per-user notification preferences: opt-in/out for task status changes, agent completions, and new recommendations.
- **FR-013**: System MUST persist per-user-per-project settings: board/workflow configurations, agent pipeline mappings, and display preferences.
- **FR-014**: System MUST seed global settings from existing environment variables (AI_PROVIDER, DEFAULT_REPOSITORY, DEFAULT_ASSIGNEE, COPILOT_POLLING_INTERVAL) on first startup only; subsequent admin changes via the settings endpoint must not be overwritten on restart.
- **FR-015**: System MUST keep the existing in-memory cache operational as a read-through performance layer for transient data (e.g., API response caching). The in-memory cache must NOT be used as the source of truth for any durable user data.
- **FR-016**: System MUST implement bidirectional theme synchronization on the frontend: changing the theme on the Settings page must update the existing theme toggle state, and toggling theme elsewhere must be reflected on the Settings page.
- **FR-017**: System MUST fall back to localStorage for UI preferences (theme, sidebar state, default active view) when the user is unauthenticated or the backend is unreachable, maintaining backward compatibility with current behavior.
- **FR-018**: System MUST add a "Settings" view to the header navigation alongside existing Chat and Project Board tabs, wired into the application's active view state.
- **FR-019**: System MUST provide clear save feedback (success or error indication) when a user saves settings on the Settings page.
- **FR-020**: System MUST apply the settings precedence hierarchy: per-user settings override global defaults; per-project settings override per-user defaults for that project.
- **FR-021**: System MUST handle the case where the database file does not exist at startup by creating it and initializing the schema.

### Key Entities

- **User Session**: Represents an authenticated user's login session. Key attributes: session identifier, GitHub user identifier, GitHub username, encrypted access token, encrypted refresh token, token expiration timestamp, selected project identifier, creation timestamp, last-updated timestamp.
- **User Settings**: Represents a user's personal preferences across all categories. Key attributes: user identifier, AI preferences (provider, model, temperature), UI preferences (theme, default view, sidebar state), workflow defaults (repository, assignee, polling interval), notification preferences (task status changes, agent completions, new recommendations).
- **Project Settings**: Represents per-user configuration for a specific project. Key attributes: user identifier, project identifier, board/workflow configuration, agent pipeline mappings, display preferences.
- **Global Settings**: Represents instance-wide defaults that apply to all users. Key attributes: setting key-value pairs for AI provider, allowed models, workflow defaults. Seeded from environment variables on first startup.

## Assumptions

- The existing GitHub OAuth authentication flow continues to be the sole authentication mechanism. No new auth methods are introduced.
- "Any authenticated user" may modify global settings for now; a full RBAC/admin role system is explicitly out of scope.
- Data export/import and backup/restore of the database are out of scope.
- Session expiration policy remains as currently configured (SESSION_EXPIRE_HOURS environment variable, defaulting to 8 hours).
- The notification preferences feature persists user choices only; the notification delivery mechanism is a separate concern.
- The system runs as a single-instance deployment (not horizontally scaled), which is compatible with file-based storage.
- Standard web application performance expectations apply (settings page loads in under 2 seconds, save operations complete in under 1 second) unless otherwise specified.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users remain logged in after a server/container restart — 100% of valid (non-expired) sessions survive a restart cycle.
- **SC-002**: Users can view and update all six settings categories (AI preferences, UI/display, workflow defaults, notification preferences, project settings, global settings) from a single Settings page in under 2 minutes.
- **SC-003**: The Settings page loads the user's effective (merged) configuration in under 2 seconds on a standard connection.
- **SC-004**: Theme changes made on the Settings page are reflected in the application within 1 second, and vice versa (bidirectional sync).
- **SC-005**: When the backend is unreachable, UI preferences (theme, sidebar state, active view) continue to function using local fallback storage with no user-visible errors.
- **SC-006**: Global settings seeded from environment variables are present on first startup without any manual database configuration.
- **SC-007**: Per-user settings correctly override global defaults — when a user has a personal override, the merged settings endpoint returns the user's value, not the global default.
- **SC-008**: The database and schema are created automatically on first startup with zero manual steps required.
