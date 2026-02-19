# Feature Specification: SQLite-Backed Durable Persistence Layer with Settings UI

**Feature Branch**: `005-sqlite-settings-persistence`  
**Created**: 2026-02-19  
**Status**: Draft  
**Input**: User description: "Add a SQLite-backed storage layer for user configuration and settings, replacing the current volatile in-memory-only persistence. The app currently stores sessions and all user state in a Python dict-based in-memory cache (backend/src/services/cache.py) which is lost on every server restart. There is no database in the stack today."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Persistent User Sessions Across Restarts (Priority: P1)

As an authenticated user, I want my login session to survive server and container restarts so that I do not have to re-authenticate every time the backend process restarts.

**Why this priority**: Session persistence is the foundation for all other settings — without it, users cannot stay logged in, and per-user preferences become meaningless. This eliminates the most painful consequence of the current in-memory-only cache.

**Independent Test**: Can be fully tested by logging in, restarting the backend container, and verifying the session token still works without re-authenticating.

**Acceptance Scenarios**:

1. **Given** a user is authenticated and has an active session, **When** the backend server restarts, **Then** the user's session remains valid and they can continue using the application without re-authenticating.
2. **Given** a user's session has been persisted, **When** the session's time-to-live expires, **Then** the session is invalidated and the user must re-authenticate.
3. **Given** the application starts for the first time with no existing database, **When** the server initializes, **Then** all required database tables are created automatically and the application starts without errors.

---

### User Story 2 - Manage AI and Workflow Preferences (Priority: P2)

As an authenticated user, I want to configure my default AI provider, preferred model, temperature, default repository, default assignee, and Copilot polling interval from a dedicated Settings page so that my workflow is personalized to my needs and persists across sessions.

**Why this priority**: AI and workflow preferences directly impact the core functionality of the application (chat completions, project board behavior). Allowing users to override environment-variable defaults provides immediate value.

**Independent Test**: Can be fully tested by navigating to the Settings page, changing the AI provider and default repository, saving, refreshing the page, and confirming the preferences are retained.

**Acceptance Scenarios**:

1. **Given** an authenticated user navigates to the Settings page, **When** they change the default AI provider from "copilot" to "azure_openai" and save, **Then** the preference is persisted and reflected on subsequent page loads.
2. **Given** an authenticated user has set a preferred model and temperature, **When** they initiate a chat completion, **Then** the system uses the user's preferred settings rather than the global defaults.
3. **Given** an authenticated user has not configured any workflow defaults, **When** they view the Settings page, **Then** the fields display the current global/environment-variable defaults as placeholders.
4. **Given** an authenticated user changes the default repository and Copilot polling interval, **When** they save and return to the Project Board, **Then** the updated defaults are applied.

---

### User Story 3 - Settings Page Navigation and UI/Display Preferences (Priority: P2)

As an authenticated user, I want to access a dedicated Settings tab in the header navigation and manage my UI preferences (theme, default view, sidebar state) so that my display configuration persists and syncs across components.

**Why this priority**: The Settings page is the primary interface through which all user preferences are managed. Theme synchronization and navigation integration provide a polished user experience that makes all other settings accessible.

**Independent Test**: Can be fully tested by clicking the Settings tab, toggling the theme, changing the default view, and verifying changes are immediately reflected in the app and persist across page reloads.

**Acceptance Scenarios**:

1. **Given** an authenticated user is on any page, **When** they click the "Settings" tab in the header navigation, **Then** the Settings page is displayed with organized sections for all preference categories.
2. **Given** a user toggles the theme from dark to light on the Settings page, **When** the toggle changes, **Then** the application theme updates immediately without a page reload, and the existing theme hook reflects the change.
3. **Given** a user changes the theme via the existing theme toggle (outside the Settings page), **When** they navigate to the Settings page, **Then** the theme preference on the Settings page reflects the current theme state.
4. **Given** an authenticated user sets their default active view to "board", **When** they log in next time, **Then** the application opens to the Project Board view instead of Chat.
5. **Given** a user is not authenticated or offline, **When** they change the theme, **Then** the preference is stored in localStorage as a fallback and applied on next visit.

---

### User Story 4 - Notification Preferences (Priority: P3)

As an authenticated user, I want to configure which event types I receive notifications for so that I only see alerts relevant to my workflow.

**Why this priority**: Notification preferences are a secondary concern — they enhance the user experience but do not block core functionality. The notification system itself may be basic initially.

**Independent Test**: Can be fully tested by toggling notification preferences on the Settings page and verifying the selections are persisted and returned by the API.

**Acceptance Scenarios**:

1. **Given** an authenticated user navigates to the Notification Preferences section of the Settings page, **When** they disable notifications for "agent completions", **Then** the preference is saved and persists across sessions.
2. **Given** a user has not configured notification preferences, **When** they view the section, **Then** all notification types are enabled by default.

---

### User Story 5 - Project-Level Settings (Priority: P3)

As an authenticated user, I want to configure per-project settings (board/workflow configurations, agent pipeline mappings, display preferences) scoped to specific projects so that each project can have its own customization.

**Why this priority**: Project-level settings add depth to the configuration model but are only relevant once users work with multiple projects. This is an important extension but not required for initial value delivery.

**Independent Test**: Can be fully tested by selecting a project, configuring project-specific display preferences, switching to a different project, and verifying each project retains its own settings.

**Acceptance Scenarios**:

1. **Given** an authenticated user has selected a project, **When** they navigate to the Project Settings section on the Settings page, **Then** they see settings scoped to that specific project.
2. **Given** a user has configured different display preferences for two projects, **When** they switch between projects, **Then** each project reflects its own configuration.
3. **Given** a user has not configured any project-level settings, **When** they view the Project Settings section, **Then** the settings default to the global/user-level values.

---

### User Story 6 - Global/Instance-Level Settings (Priority: P3)

As an administrator (or any authenticated user in the current simple auth model), I want to view and update global/instance-level settings that serve as defaults for all users so that the instance is configured appropriately.

**Why this priority**: Global settings provide the baseline configuration layer. They must exist for the merged-settings model to work, but since environment variables currently serve this role, persisting them is an enhancement rather than a critical blocker.

**Independent Test**: Can be fully tested by updating a global setting (e.g., default AI provider), logging in as another user (or clearing user overrides), and confirming the global default is reflected.

**Acceptance Scenarios**:

1. **Given** an authenticated user navigates to the Global Settings section, **When** they update the default AI provider, **Then** the change is saved and reflected as the default for all users who have not set a personal override.
2. **Given** the application starts for the first time, **When** no global settings exist in the database, **Then** the system seeds global settings from environment variables.
3. **Given** a user has set a personal AI provider preference, **When** they retrieve their effective settings, **Then** the personal preference takes precedence over the global default.

---

### Edge Cases

- What happens when the database file is corrupted or inaccessible at startup? The system should log a clear error and fail to start gracefully rather than silently falling back to in-memory-only mode.
- What happens when a user's session references a project that has been deleted or is no longer accessible? Project-level settings should return empty/default values, not errors.
- What happens when multiple concurrent requests attempt to update the same user's settings simultaneously? The last write should win, and the system should not corrupt data.
- What happens when the persistent storage volume mount path does not exist or has incorrect permissions? The application should log a descriptive error on startup.
- What happens when a user saves settings with values outside expected ranges (e.g., negative temperature)? The system should validate inputs and return clear error messages.
- What happens when the frontend cannot reach the settings API (network error)? The UI should display an error notification and retain the last-known settings in localStorage.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST persist user sessions (based on the existing UserSession model) to a durable database so that sessions survive server and container restarts.
- **FR-002**: System MUST create all required database tables automatically on first startup if they do not already exist, using a schema initialization strategy that supports future evolution.
- **FR-003**: System MUST retain the existing in-memory cache as an optional read-through performance layer for transient/short-lived data (e.g., API response caching) while routing all durable user data through the database.
- **FR-004**: System MUST persist per-user AI preferences including default AI provider (copilot or azure_openai), preferred model, and temperature setting.
- **FR-005**: System MUST persist per-user UI/display preferences including theme (dark/light), default active view (chat/board/settings), and sidebar collapsed state.
- **FR-006**: System MUST persist per-user workflow defaults including default repository, default assignee, and Copilot polling interval, serving as user-level overrides of the current environment-variable values.
- **FR-007**: System MUST persist per-user notification preferences as a set of toggleable event subscriptions covering at minimum: task status changes, agent completions, and new recommendations.
- **FR-008**: System MUST persist per-user-per-project settings scoped by project identifier, including board/workflow configurations, agent pipeline mappings, and display preferences.
- **FR-009**: System MUST persist global/instance-level settings (default AI provider, allowed models, global workflow defaults) seeded from environment variables on first startup.
- **FR-010**: System MUST merge settings so that per-user preferences take precedence over global defaults in all API responses returning effective configuration.
- **FR-011**: System MUST expose a settings retrieval endpoint for the authenticated user's effective merged preferences (global defaults combined with user overrides).
- **FR-012**: System MUST expose a settings update endpoint for the authenticated user's preferences.
- **FR-013**: System MUST expose a settings retrieval endpoint for global/instance-level settings.
- **FR-014**: System MUST expose a settings update endpoint for global/instance-level settings, accessible by any authenticated user (no RBAC required).
- **FR-015**: System MUST expose a settings retrieval endpoint for per-project settings scoped to the authenticated user and a specific project identifier.
- **FR-016**: System MUST expose a settings update endpoint for per-project settings scoped to the authenticated user and a specific project identifier.
- **FR-017**: System MUST mount the database file via a persistent storage volume in the container orchestration configuration so data persists across container restarts.
- **FR-018**: System MUST add a "Settings" tab to the header navigation integrated with the existing view-switching mechanism in the frontend.
- **FR-019**: System MUST organize the Settings page into clearly labeled sections: AI Preferences, UI & Display, Workflow Defaults, Notification Preferences, Project Settings, and Global Settings.
- **FR-020**: System SHOULD sync theme preference bidirectionally between the Settings page and the existing theme toggle mechanism with no page reload required.
- **FR-021**: System MUST use localStorage as a fallback for UI preferences when the user is not authenticated or the API is unreachable.
- **FR-022**: System MUST provide visible success or error feedback when settings are saved.
- **FR-023**: System MUST validate settings input values and return clear error messages for invalid data (e.g., temperature out of range, empty required fields).
- **FR-024**: System MUST NOT implement multi-user RBAC, settings data export/import, or database backup/restore functionality.

### Key Entities

- **UserSession**: Represents an authenticated user's active session. Key attributes: session identifier, user identifier, access token, refresh token, username, avatar URL, selected project identifier, creation timestamp, expiration timestamp. Persisted to survive restarts.
- **UserPreferences**: Represents an individual user's personal settings. Key attributes: user identifier, AI preferences (provider, model, temperature), UI preferences (theme, default view, sidebar state), workflow defaults (default repository, default assignee, polling interval), notification preferences (set of enabled event types). One record per user.
- **ProjectSettings**: Represents per-user-per-project configuration. Key attributes: user identifier, project identifier, board/workflow configuration, agent pipeline mappings, display preferences. One record per user-project combination.
- **GlobalSettings**: Represents instance-wide defaults that apply to all users. Key attributes: setting key, setting value, last updated timestamp. Seeded from environment variables on first startup. One set of records per application instance.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Authenticated user sessions persist across server restarts — users do not need to re-authenticate after a restart within their session's time-to-live window.
- **SC-002**: Users can access the Settings page from the header navigation in one click and see all preference categories organized into distinct sections.
- **SC-003**: Users can update any preference category, save, and have the change persist across page refreshes and server restarts.
- **SC-004**: Theme changes made on the Settings page take effect immediately (under 1 second) without a page reload, and vice versa — changes from the existing toggle are reflected on the Settings page.
- **SC-005**: The settings API returns merged effective configuration (global defaults + user overrides) in a single response, eliminating the need for multiple calls.
- **SC-006**: All database tables are created automatically on first startup — no manual setup or migration commands required from the operator.
- **SC-007**: Container data survives restarts — restarting the container does not result in loss of any persisted sessions or settings.
- **SC-008**: Settings page provides visible feedback (success or error notification) within 2 seconds of saving any preference.
- **SC-009**: When the settings API is unreachable, the frontend falls back to localStorage-based preferences without crashing or showing a blank screen.
- **SC-010**: Invalid settings input (e.g., out-of-range temperature, missing required fields) is rejected with a clear, user-facing error message.

## Assumptions

- The current GitHub OAuth flow remains the sole authentication mechanism; no new auth methods are introduced.
- The "first user is admin" pattern or "any authenticated user can modify global settings" is acceptable for this iteration; fine-grained RBAC is out of scope.
- The existing session time-to-live (8 hours, configurable via environment variable) continues to govern session expiration even when persisted in the database.
- Notification preferences are stored and returned via the API but the actual notification delivery mechanism (e.g., real-time push, in-app banners) is out of scope for this feature — this feature only persists the preferences.
- The database is single-instance; there is no requirement for multi-instance or distributed database support.
- The allowed AI providers are "copilot" and "azure_openai" as defined in the current configuration; new providers are out of scope.
- Data migration from existing localStorage values to the database is best-effort on first authenticated load — no offline migration tool is needed.
