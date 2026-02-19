# Feature Specification: SQLite-Backed Settings Storage

**Feature Branch**: `006-sqlite-settings-storage`
**Created**: 2026-02-19
**Status**: Draft
**Input**: User description: "Add a SQLite-backed storage layer for user configuration and settings, replacing the current volatile in-memory-only persistence. The app currently stores sessions and all user state in a Python dict-based in-memory cache which is lost on every server restart. There is no database in the stack today."

## Clarifications

### Session 2026-02-19

- Q: How should the system handle expired session cleanup from persistent storage? → A: Both — lazy rejection on access AND a periodic background purge for storage hygiene.
- Q: What is the canonical set of notification event types for this version? → A: Four types: task_status_change, agent_completion, new_recommendation, chat_mention.
- Q: What schema migration strategy should be used? → A: Embedded version table — a schema_version table tracks the current version; the app runs numbered migration scripts at startup.
- Q: What should happen if the database schema version is ahead of the application version (e.g., after a rollback)? → A: Refuse to start — log an error and exit to protect data integrity.
- Q: What level of observability/logging should database operations have? → A: Key lifecycle events (startup/migration, errors, cleanup summaries) at INFO; individual read/write at DEBUG.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Persistent User Sessions (Priority: P1)

A user logs in via GitHub OAuth and uses the application. Later, the backend server is restarted (deploy, crash, or container recreation). When the user returns to the application, their session is still valid and they are not forced to re-authenticate.

**Why this priority**: Session persistence is the foundational capability. Without it, every server restart wipes all user state, making the application unreliable. This is the single biggest pain point today and the prerequisite for all other settings persistence.

**Independent Test**: Log in, verify session, restart the backend container, reload the page, and confirm the user is still authenticated with the same session data (selected project, username, avatar).

**Acceptance Scenarios**:

1. **Given** a user has an active session, **When** the backend server is restarted, **Then** the user's session is restored and they remain logged in without re-authentication.
2. **Given** a user has an active session with a selected project, **When** the server restarts, **Then** the selected project is still associated with the session after restart.
3. **Given** a user's session has expired (past the configured expiry window), **When** the user tries to access the application, **Then** they are prompted to re-authenticate regardless of persistence.
4. **Given** a user logs out explicitly, **When** the session is revoked, **Then** it is removed from persistent storage and cannot be reused.

---

### User Story 2 — Database Initialization and Schema Management (Priority: P1)

An operator deploys the application for the first time. The database is automatically created and all required tables are initialized on startup. No manual SQL scripts or migration steps are necessary.

**Why this priority**: The database must exist and be correctly structured before any other feature can persist data. This is a hard dependency for every subsequent user story.

**Independent Test**: Delete the database file (or start with a fresh volume), start the application, and verify all tables are created. Restart again and verify no errors from re-initialization.

**Acceptance Scenarios**:

1. **Given** no database file exists, **When** the application starts, **Then** the database is created with all required tables and the application starts successfully.
2. **Given** the database already exists with the correct schema, **When** the application starts, **Then** the startup completes without errors or data loss.
3. **Given** the database file is stored on a mounted volume, **When** the container is destroyed and recreated, **Then** the database file persists and the application reconnects to existing data.

---

### User Story 3 — User AI Preferences (Priority: P2)

A user wants to customize their AI experience by selecting their preferred AI provider, model, and generation temperature. They navigate to a Settings page, adjust their AI preferences, and save. From that point on, all AI interactions use their personal preferences instead of the system-wide defaults.

**Why this priority**: AI preferences directly affect the core functionality of the application (chat-based project management). Allowing users to tailor their AI experience is high-value and requires the persistence layer from P1 stories.

**Independent Test**: Log in, navigate to Settings, change AI provider and model, save, send a chat message, and confirm the system uses the selected provider. Restart the server and verify preferences are retained.

**Acceptance Scenarios**:

1. **Given** a user has no saved AI preferences, **When** they view the Settings page, **Then** the AI preferences section shows the global default values.
2. **Given** a user changes their preferred AI model and saves, **When** they start a new chat interaction, **Then** the system uses their selected model.
3. **Given** a user has saved AI preferences, **When** the server restarts and the user returns, **Then** their AI preferences are still applied.
4. **Given** a user resets their AI preferences to defaults, **When** they save, **Then** the system reverts to using global default values.

---

### User Story 4 — Frontend Settings Page (Priority: P2)

A user wants to view and manage all their application preferences in one place. They click a "Settings" link in the header navigation and are presented with an organized page showing sections for AI preferences, display preferences, workflow defaults, and notification preferences.

**Why this priority**: The Settings page is the primary user interface for all preference management. Without it, users cannot change any settings, making the persistence layer invisible. This is a prerequisite for all user-facing settings stories.

**Independent Test**: Log in, click the Settings navigation item, verify the page renders with empty/default values, change a setting, save, navigate away and back, and confirm the value persisted.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they click "Settings" in the header navigation, **Then** a Settings page is displayed with organized sections for each preference category.
2. **Given** a user is on the Settings page, **When** they modify a preference and click save, **Then** a confirmation is shown and the preference is persisted to the backend.
3. **Given** a user is on the Settings page, **When** they make changes but navigate away without saving, **Then** they are warned about unsaved changes.
4. **Given** a user is not authenticated, **When** they try to access the Settings page, **Then** they are redirected to the login flow.

---

### User Story 5 — UI/Display Preferences (Priority: P2)

A user prefers dark mode and wants the board view as their default landing page. They configure these preferences in Settings. The theme selection syncs with the existing theme toggle in the header, and their default view is applied on next login.

**Why this priority**: Display preferences directly affect daily user experience. The theme toggle already exists in the frontend (localStorage-based); this story upgrades it to be API-backed and persistent.

**Independent Test**: Log in, go to Settings, set theme to dark and default view to "board", save, log out and log back in, and verify the app loads in dark mode on the board view.

**Acceptance Scenarios**:

1. **Given** a user sets their theme preference to "dark" in Settings, **When** they save, **Then** the application immediately switches to dark mode and the header theme toggle reflects the change.
2. **Given** a user toggles the theme via the header button, **When** the toggle fires, **Then** the preference is also saved to the backend so it persists across devices.
3. **Given** a user sets "board" as their default view, **When** they log in next time, **Then** the application opens directly to the Project Board view.
4. **Given** a user has no saved display preferences, **When** they load the application, **Then** the theme defaults to light mode and the default view is "chat" (matching current behavior).
5. **Given** a user is unauthenticated (offline fallback), **When** they toggle the theme, **Then** the preference is stored in localStorage as it is today.

---

### User Story 6 — Workflow Defaults (Priority: P3)

A user frequently works with the same repository and assignee. They set their default repository and default assignee in Settings, so they don't have to specify them every time they create issues or tasks via chat.

**Why this priority**: Workflow defaults reduce repetitive input and improve efficiency, but the application is functional without them (environment variables provide system-wide defaults).

**Independent Test**: Log in, set a default repository and assignee in Settings, create a task via chat without specifying a repo, and confirm the task is created in the user's default repository with their default assignee.

**Acceptance Scenarios**:

1. **Given** a user sets a default repository in Settings, **When** they create an issue via chat without specifying a repository, **Then** the system uses their configured default repository.
2. **Given** a user sets a default Copilot polling interval, **When** the system polls for Copilot updates, **Then** it uses the user's interval instead of the global default.
3. **Given** a user has not set workflow defaults, **When** they create a task, **Then** the system falls back to global/instance-level defaults (seeded from environment variables).

---

### User Story 7 — Notification Preferences (Priority: P3)

A user wants to control which events trigger notifications. They go to Settings and configure their notification preferences — for example, they opt out of "task status change" notifications but keep "agent completion" alerts.

**Why this priority**: Notification preferences are a quality-of-life improvement. The application is usable without them, and notifications can default to all-on initially.

**Independent Test**: Log in, go to Settings, disable "task status change" notifications, trigger a task status change, and verify no notification is sent. Enable "agent completion" and verify those notifications still arrive.

**Acceptance Scenarios**:

1. **Given** a user disables notifications for "task status changes", **When** a task changes status, **Then** the user does not receive a notification for that event.
2. **Given** a user has not configured notification preferences, **When** an event occurs, **Then** the user receives notifications for all event types (default: all enabled).
3. **Given** a user enables only "agent completion" notifications, **When** an agent finishes work, **Then** they receive a notification, but no notifications for other event types.

---

### User Story 8 — Project-Level Settings (Priority: P3)

A user manages multiple GitHub projects and wants different configurations per project — for example, different agent pipeline mappings or display preferences for each board. They select a project and configure its specific settings in the Settings page.

**Why this priority**: Project-level settings provide advanced customization but require per-user settings to already be working. Most users will be fine with global defaults initially.

**Independent Test**: Log in, select Project A, configure project-specific board preferences, switch to Project B with different settings, and verify each project retains its own configuration independently.

**Acceptance Scenarios**:

1. **Given** a user configures board display preferences for Project A, **When** they switch to Project B, **Then** Project B shows its own settings (or defaults if none configured).
2. **Given** a user sets agent pipeline mappings for a project, **When** they trigger a workflow on that project, **Then** the project-specific pipeline mapping is used.
3. **Given** a user has no project-level settings, **When** they view a project, **Then** the system uses global defaults for all project-level configurations.

---

### User Story 9 — Global/Instance-Level Settings (Priority: P3)

An administrator (or the first authenticated user) wants to configure instance-wide defaults — for example, the default AI provider, allowed models, or global workflow defaults. These serve as the baseline that all users inherit unless they override with personal preferences.

**Why this priority**: Global settings provide the foundation for the settings hierarchy (global → user → project). Environment variables currently serve this role; this story adds a UI to manage them without redeploying.

**Independent Test**: Log in as the first user, navigate to a "Global Settings" section, change the default AI provider, log in as a second user who has no personal AI preference, and confirm they see the updated global default.

**Acceptance Scenarios**:

1. **Given** an administrator changes the global default AI provider, **When** a new user logs in with no personal preferences, **Then** their effective AI provider matches the global default.
2. **Given** global defaults are not yet configured, **When** the application starts, **Then** global settings are seeded from environment variables.
3. **Given** a user has personal preferences that override a global setting, **When** the global setting changes, **Then** the user's personal override is preserved and takes precedence.
4. **Given** any authenticated user accesses global settings, **When** they attempt to modify them, **Then** the changes are accepted (no RBAC enforcement in this version).

---

### User Story 10 — Settings API with Merged Views (Priority: P2)

The frontend needs to retrieve the effective configuration for the current user in a single call. The API returns a merged view that combines global defaults with user-specific overrides, so the frontend does not need to perform merge logic.

**Why this priority**: The merged-view API is a required building block for the frontend Settings page and for any backend service that needs to resolve the effective configuration for a user.

**Independent Test**: Set global defaults, set user overrides for a subset of settings, call the user settings API, and verify the response contains the merged result (user overrides applied on top of global defaults).

**Acceptance Scenarios**:

1. **Given** global defaults exist and a user has no overrides, **When** the frontend calls GET /api/v1/settings/user, **Then** the response contains all global defaults as the effective configuration.
2. **Given** a user has overridden their AI provider but not their theme, **When** the frontend calls GET /api/v1/settings/user, **Then** the AI provider reflects the user's choice and the theme reflects the global default.
3. **Given** a user updates a preference via PUT /api/v1/settings/user, **When** the frontend re-fetches settings, **Then** the updated value is reflected in the merged response.

---

### Edge Cases

- What happens when the database file is corrupted or inaccessible at startup? The application should log a clear error and fail to start rather than silently running without persistence.
- What happens when the database schema version is ahead of the running application version (e.g., after a rollback)? The application MUST refuse to start and log a clear error indicating the version mismatch, to protect data integrity.
- What happens when a user's session references a project that no longer exists? The session should still load; the stale project reference should be handled gracefully (cleared or ignored).
- What happens when two concurrent requests update the same user's settings simultaneously? The last write wins; the system should not crash or produce corrupt data.
- What happens when the database volume is not mounted (e.g., misconfigured Docker setup)? The application should still create a database file in the container, but data will not survive container recreation. A startup warning should be logged.
- What happens when a setting key used by the frontend does not exist in the backend schema? Unknown keys should be ignored or rejected with a clear validation error rather than causing a crash.
- What happens when the global settings are modified while users are actively using the app? Active users should see updated defaults on their next settings fetch, not midway through active sessions (eventual consistency).

## Requirements *(mandatory)*

### Functional Requirements

#### Database & Persistence

- **FR-001**: System MUST persist user sessions to durable storage so they survive backend server restarts.
- **FR-002**: System MUST automatically create the database and all required tables on first startup without manual intervention.
- **FR-003**: System MUST store the database file at a configurable path that can be mapped to a Docker volume for data durability.
- **FR-004**: System MUST include a schema versioning strategy using an embedded version table (`schema_version`) that tracks the current schema version. The application MUST run numbered migration scripts sequentially at startup to evolve the schema without data loss. If the database schema version is ahead of the application's expected version, the application MUST refuse to start and log a clear error.
- **FR-005**: System MUST use asynchronous database access so that database operations do not block the event loop.

#### In-Memory Cache Relationship

- **FR-006**: System MUST retain the existing in-memory cache for short-lived, transient data (e.g., API response caching, OAuth state tokens).
- **FR-007**: System MUST NOT use the in-memory cache as the primary store for any durable user data (sessions, preferences, settings).
- **FR-008**: System MAY use the in-memory cache as a read-through performance layer for frequently accessed settings, with the database as the source of truth.

#### User Sessions

- **FR-009**: System MUST persist the full UserSession model (session ID, GitHub user ID, username, avatar URL, encrypted tokens, token expiry, selected project ID, timestamps) to durable storage.
- **FR-010**: System MUST load sessions from durable storage when looking up a session by ID (with optional in-memory caching for performance).
- **FR-011**: System MUST remove sessions from durable storage when a user logs out or a session is revoked.
- **FR-012**: System MUST support session expiry based on the configured session expiration window. Expired sessions MUST be rejected and deleted on access (lazy cleanup) AND a periodic background task MUST purge expired sessions from persistent storage to prevent unbounded growth.

#### User Preferences

- **FR-013**: System MUST persist per-user AI preferences including: default AI provider, preferred model, and temperature setting.
- **FR-014**: System MUST persist per-user UI/display preferences including: theme (dark/light), default active view (chat/board), and sidebar collapsed state.
- **FR-015**: System MUST persist per-user workflow defaults including: default repository, default assignee, and Copilot polling interval.
- **FR-016**: System MUST persist per-user notification preferences as a set of enabled/disabled event types. The canonical event types for this version are: task_status_change, agent_completion, new_recommendation, and chat_mention. All types default to enabled.

#### Project-Level Settings

- **FR-017**: System MUST persist per-user-per-project settings scoped by both user identity and project identity.
- **FR-018**: System MUST support project-level board/workflow configuration including agent pipeline mappings and display preferences.

#### Global/Instance-Level Settings

- **FR-019**: System MUST persist global/instance-level settings that serve as defaults for all users.
- **FR-020**: System MUST seed global settings from environment variables on first startup when no global settings exist in the database.
- **FR-021**: System MUST NOT overwrite existing global settings with environment variable values on subsequent startups.
- **FR-022**: System MUST allow any authenticated user to view and modify global settings (no RBAC in this version).

#### Settings Hierarchy & Merging

- **FR-023**: System MUST implement a settings hierarchy where per-user overrides take precedence over global defaults.
- **FR-024**: System MUST implement a settings hierarchy where per-user-per-project overrides take precedence over per-user settings, which take precedence over global defaults.
- **FR-025**: System MUST return merged/effective settings views from the API so that clients receive the resolved configuration in a single response.

#### API Endpoints

- **FR-026**: System MUST expose GET /api/v1/settings/user to retrieve the authenticated user's effective preferences (merged with global defaults).
- **FR-027**: System MUST expose PUT /api/v1/settings/user to update the authenticated user's preferences (partial updates supported).
- **FR-028**: System MUST expose GET /api/v1/settings/global to retrieve global/instance-level settings.
- **FR-029**: System MUST expose PUT /api/v1/settings/global to update global/instance-level settings.
- **FR-030**: System MUST expose GET /api/v1/settings/project/{project_id} to retrieve per-project settings for the authenticated user (merged with user and global defaults).
- **FR-031**: System MUST expose PUT /api/v1/settings/project/{project_id} to update per-project settings for the authenticated user.
- **FR-032**: All settings endpoints MUST require authentication; unauthenticated requests MUST be rejected.

#### Frontend Settings Page

- **FR-033**: System MUST provide a "Settings" view accessible from the header navigation alongside the existing Chat and Project Board tabs.
- **FR-034**: The Settings page MUST display organized sections for: AI preferences, display preferences, workflow defaults, notification preferences, project-level settings, and global settings.
- **FR-035**: Theme preference changes on the Settings page MUST synchronize bidirectionally with the existing theme toggle in the header.
- **FR-036**: The Settings page MUST save preferences to the backend API and display confirmation feedback on success.
- **FR-037**: The Settings page MUST warn users about unsaved changes when navigating away.
- **FR-038**: When the user is unauthenticated or offline, the frontend MUST fall back to localStorage for theme preference (maintaining current behavior).

#### Docker & Deployment

- **FR-039**: The Docker Compose configuration MUST include a named volume mount for the database file so data persists across container lifecycle events.

#### Observability

- **FR-040**: System MUST log database startup, schema migration execution, and migration completion at INFO level.
- **FR-041**: System MUST log database connection errors, migration failures, and schema version mismatches at ERROR level.
- **FR-042**: System MUST log periodic session cleanup summaries (number purged) at INFO level.
- **FR-043**: System MUST log individual database read/write operations (session lookups, settings reads/writes) at DEBUG level.

### Key Entities

- **UserSession**: Represents an authenticated user's active session. Contains session ID, GitHub identity (user ID, username, avatar URL), encrypted OAuth tokens (access token, refresh token, expiry), currently selected project ID, and timestamps (created, updated). One user may have multiple concurrent sessions.

- **UserPreferences**: Represents a user's personal configuration overrides. Keyed by GitHub user ID. Contains AI preferences (provider, model, temperature), display preferences (theme, default view, sidebar state), workflow defaults (default repository, default assignee, polling interval), and notification preferences (set of enabled event types). All fields are optional — absence means "use global default."

- **ProjectSettings**: Represents per-user-per-project configuration. Keyed by the combination of GitHub user ID and project ID. Contains project-specific board configuration, agent pipeline mappings, and display preferences. All fields are optional — absence means "use user default or global default."

- **GlobalSettings**: Represents instance-wide default configuration. Singleton record. Contains the same preference categories as UserPreferences (AI, display, workflow, notifications) plus any instance-specific settings (allowed models list). Seeded from environment variables on first startup.

## Assumptions

- The existing GitHub OAuth flow and UserSession Pydantic model will continue to be used; this feature adds persistence underneath without changing the authentication flow.
- OAuth tokens stored in the database are considered sensitive; the current approach of storing tokens as-is in memory is maintained for the database layer (encryption at rest is deferred to a future spec).
- The "first user is admin" pattern means the first user to authenticate can modify global settings; in practice, any authenticated user can modify global settings in this version.
- The frontend Settings page will follow the existing application styling and component patterns (React, TanStack Query, CSS).
- Session expiry logic (currently 8 hours) remains unchanged; the persistence layer stores and respects the existing expiry timestamps.
- The in-memory cache (`InMemoryCache`) continues to exist and serve its current role for API response caching (projects, project items) — this feature does not remove or replace it.
- Notification preferences define which events a user wants to be notified about; the actual notification delivery mechanism (WebSocket, push, etc.) is outside the scope of this spec and assumed to already exist or be handled separately.
- Default theme for new users is "light" and default view is "chat", matching current behavior.

## Non-Goals

- Multi-user admin roles or RBAC — any authenticated user can modify global settings.
- Data export/import of settings.
- Backup/restore functionality for the SQLite database.
- Token encryption at rest (deferred to a future security-focused spec).
- Full offline mode for the frontend — localStorage fallback is limited to theme preference for unauthenticated users.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users remain logged in across backend server restarts — 100% of active sessions are recoverable after a container restart (within the session expiry window).
- **SC-002**: Users can view and modify all preference categories (AI, display, workflow, notifications) from a single Settings page in under 30 seconds for a full preference update.
- **SC-003**: The settings API returns merged effective configuration in a single request, with response times under 500ms for any settings endpoint.
- **SC-004**: The database initializes automatically on first startup with no manual setup required — zero-step database provisioning.
- **SC-005**: Settings data survives container restarts when the Docker volume is correctly configured — 100% data retention across 10 consecutive container recreations.
- **SC-006**: Theme changes on the Settings page are reflected immediately in the UI and persist across page reloads and server restarts.
- **SC-007**: Per-user overrides correctly take precedence over global defaults — when a user sets a preference, it is always reflected in the merged settings response regardless of global default changes.
- **SC-008**: The existing in-memory cache continues to function for API response caching with no degradation in cache hit/miss behavior.
