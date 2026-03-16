# Feature Specification: Settings Page Refactor with Secrets

**Feature Branch**: `048-settings-page-refactor`  
**Created**: 2026-03-16  
**Status**: Draft  
**Input**: User description: "Refactor the Settings page from a monolithic form dump (18 components, 5 sections behind a collapsible) into a clean tabbed layout showing only essentials by default, with a new GitHub Repository Environment Secrets feature for MCP API keys (e.g. COPILOT_MCP_CONTEXT7_API_KEY)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Essential AI Settings at a Glance (Priority: P1)

As a user, I want the Settings page to open directly to my most-used AI configuration options — provider, model, and temperature — so that I can adjust them quickly without scrolling through unrelated settings.

Currently the Settings page shows a primary section with AI configuration plus a collapsed "Advanced Settings" accordion hiding 5 additional sections. Most users only need to change their AI provider or model. The new tabbed layout places these essential controls on the default "Essential" tab, immediately visible on page load.

**Why this priority**: This is the core UX improvement and the reason for the refactor. Over 90% of settings visits are to change AI provider or model. Placing these front and center removes friction for the majority of users.

**Independent Test**: Can be fully tested by navigating to the Settings page and verifying that the Essential tab is active by default, displaying AI provider, chat model, agent model, and temperature controls. All other settings are accessible via separate tabs, not via scrolling or expanding an accordion.

**Acceptance Scenarios**:

1. **Given** a logged-in user navigates to the Settings page, **When** the page loads, **Then** the "Essential" tab is active and displays AI provider selection, chat model dropdown, agent model dropdown, and temperature slider.
2. **Given** a user is on the Essential tab, **When** they change the AI provider, **Then** the model dropdowns refresh to show models for the newly selected provider, and any previously selected model is cleared.
3. **Given** a user modifies the temperature slider on the Essential tab, **When** they click Save, **Then** the new temperature value persists and is reflected on the next page load.
4. **Given** a user has unsaved changes on the Essential tab, **When** they attempt to navigate away from the Settings page, **Then** a browser warning prompts them to confirm leaving.

---

### User Story 2 — Tabbed Navigation Across All Settings (Priority: P1)

As a user, I want all settings organized into clearly labeled tabs (Essential, Secrets, Preferences, Admin) so that I can find and manage specific settings categories without wading through a long scrollable page or expanding hidden sections.

**Why this priority**: The tab structure is the architectural foundation for the entire refactor. Without it, the Secrets feature (User Story 3) and admin separation (User Story 5) cannot be delivered. It also directly addresses the UX complaint of hidden settings behind a collapsible.

**Independent Test**: Can be tested by navigating to the Settings page and clicking each tab to verify it activates the correct content panel. The URL hash should update to reflect the active tab.

**Acceptance Scenarios**:

1. **Given** a user is on the Settings page, **When** they view the tab bar, **Then** they see tabs labeled "Essential", "Secrets", "Preferences", and optionally "Admin" (if they are an admin user).
2. **Given** a user clicks the "Preferences" tab, **When** the tab activates, **Then** the URL updates to `/settings#preferences` and the panel shows display preferences, workflow defaults, notification preferences, and Signal connection settings.
3. **Given** a user navigates directly to `/settings#secrets`, **When** the page loads, **Then** the Secrets tab is automatically selected and its content is displayed.
4. **Given** a non-admin user views the Settings page, **When** they inspect the tab bar, **Then** the "Admin" tab is not visible.
5. **Given** a user switches between tabs, **When** they return to a previously edited tab, **Then** any unsaved changes on that tab are preserved (not lost on tab switch).

---

### User Story 3 — Manage GitHub Environment Secrets for MCP API Keys (Priority: P1)

As a user, I want to securely store and manage API keys (such as `COPILOT_MCP_CONTEXT7_API_KEY`) as GitHub repository environment secrets so that MCP servers integrated with GitHub Copilot can access the keys I configure without exposing them in plain text.

GitHub Copilot's MCP integration expects secrets prefixed with `COPILOT_MCP_` stored as environment secrets in a `copilot` environment. This feature provides a UI to manage those secrets without leaving Solune or manually using the GitHub API.

**Why this priority**: This is the primary new functionality being delivered. Without secrets management, users must manually configure MCP API keys through the GitHub web interface — a multi-step, error-prone process. This story is the core value proposition of the feature.

**Independent Test**: Can be tested end-to-end by selecting a repository, setting a secret value via the UI, verifying the secret appears as "Set" in the list, then deleting it and confirming removal. Verification against GitHub can confirm the secret exists in the repository's `copilot` environment.

**Acceptance Scenarios**:

1. **Given** a user navigates to the Secrets tab, **When** the tab loads, **Then** they see a repository selector populated with their available repositories, a list of known MCP secrets with status badges ("Set" or "Not Set"), and an option to add custom secrets.
2. **Given** a user selects a repository and a known secret shows "Not Set", **When** they click the "Set" button and enter a value, **Then** the secret is encrypted and stored in the repository's `copilot` environment, and the status badge updates to "Set".
3. **Given** a user wants to update an existing secret, **When** they click "Update" on a secret showing "Set" and enter a new value, **Then** the secret is replaced with the new encrypted value. The previous value is never displayed.
4. **Given** a user wants to remove a secret, **When** they click "Remove" on a secret showing "Set" and confirm the action, **Then** the secret is deleted from the repository's `copilot` environment and the status badge changes to "Not Set".
5. **Given** a user enters a secret value, **When** they view the input field, **Then** it is a password-type input with a show/hide toggle, autocomplete is disabled, and the value is never pre-filled from the server (GitHub does not return secret values).
6. **Given** a user wants to add a custom secret not in the known list, **When** they use the "Add Custom Secret" form and enter a name and value, **Then** the name must match the pattern `^[A-Z][A-Z0-9_]*$` (max 255 characters) and the value must not exceed 64 KB. A warning is shown if the name does not start with `COPILOT_MCP_`.

---

### User Story 4 — Preferences Tab for Display, Workflow, and Notification Settings (Priority: P2)

As a user, I want my display preferences, workflow defaults, notification preferences, and Signal connection settings consolidated in a single "Preferences" tab so that all personal customization options are grouped logically and are easy to find.

**Why this priority**: This is a reorganization of existing functionality. The settings themselves already work — they just need to be moved from the collapsed Advanced section into a dedicated tab. No new backend work is required.

**Independent Test**: Can be tested by navigating to the Preferences tab and verifying that all four preference sections (display, workflow, notifications, Signal) are present, each with its own save button. Changing a preference and saving should persist correctly.

**Acceptance Scenarios**:

1. **Given** a user clicks the "Preferences" tab, **When** the tab panel loads, **Then** it displays four card sections: Display Preferences, Workflow Defaults, Notification Preferences, and Signal Connection.
2. **Given** a user changes a display preference (e.g., theme from dark to light), **When** they click the section's Save button, **Then** only the display preferences are saved — other sections remain unchanged.
3. **Given** a user has unsaved changes in the Workflow Defaults section, **When** they switch to the Essential tab and back to Preferences, **Then** the unsaved workflow changes are still present.
4. **Given** a user modifies notification preferences, **When** the save succeeds, **Then** a success confirmation is shown and the saved state reflects the new values.

---

### User Story 5 — Admin-Only Tab for Global and Project Settings (Priority: P2)

As an admin user, I want a dedicated "Admin" tab containing global AI defaults, allowed model lists, and project board configuration so that administrative controls are separated from regular user settings and hidden from non-admin users.

**Why this priority**: Separating admin controls improves security posture (non-admins don't even see admin options) and reduces cognitive load for regular users. The admin check already exists in the backend; the frontend just needs to conditionally render the tab.

**Independent Test**: Can be tested by logging in as an admin user and verifying the Admin tab appears with global settings and project settings. Then logging in as a non-admin and verifying the Admin tab is absent.

**Acceptance Scenarios**:

1. **Given** a user whose `github_user_id` matches the configured `admin_github_user_id`, **When** they navigate to the Settings page, **Then** they see an "Admin" tab in the tab bar.
2. **Given** a non-admin user, **When** they navigate to the Settings page, **Then** they do not see the "Admin" tab and cannot access admin settings.
3. **Given** an admin on the Admin tab, **When** they modify the global default AI provider and save, **Then** the global settings are updated and apply as defaults for all users.
4. **Given** an admin on the Admin tab, **When** they edit the allowed models list, **Then** only models in the allowed list appear as options in other users' model dropdowns.
5. **Given** a non-admin user navigates directly to `/settings#admin`, **When** the page loads, **Then** the Essential tab is shown instead (graceful fallback, no error).

---

### User Story 6 — MCP Preset Secret Status Indicators (Priority: P3)

As a user, I want to see a warning on the Tools page when an MCP preset requires an API key that I have not yet configured, so that I can quickly identify and resolve missing configuration before using the tool.

**Why this priority**: This is a quality-of-life integration feature that connects the Secrets tab to the existing MCP presets on the Tools page. It is not required for secrets management to function but significantly improves discoverability.

**Independent Test**: Can be tested by adding an MCP preset that requires a secret, verifying the "API key not configured" warning appears, then setting the secret and confirming the warning disappears.

**Acceptance Scenarios**:

1. **Given** an MCP preset (e.g., Context7) has a required secret that is not yet configured for the selected repository, **When** the user views the preset on the Tools page, **Then** a warning badge shows "API key not configured".
2. **Given** the user clicks the warning badge or associated link, **When** the action fires, **Then** they are navigated to `/settings#secrets` with the Secrets tab active.
3. **Given** the user sets the required secret for a preset, **When** they return to the Tools page, **Then** the warning badge is no longer shown for that preset.

---

### User Story 7 — Cleanup of Redundant Components (Priority: P3)

As a developer, I want redundant settings components removed and consolidated into the new tab structure so that the codebase is simpler, easier to maintain, and free of dead code.

**Why this priority**: This is a housekeeping story. The refactored tabs replace the old component hierarchy. Removing dead code reduces confusion for future contributors and eliminates maintenance burden.

**Independent Test**: Can be tested by verifying that deleted component files (e.g., `AIPreferences.tsx`, `AISettingsSection.tsx`, `DisplaySettings.tsx`, `WorkflowSettings.tsx`, `NotificationSettings.tsx`, `AdvancedSettings.tsx`) are no longer in the source tree, and that no import references to them remain. Existing tests referencing deleted components are updated or removed.

**Acceptance Scenarios**:

1. **Given** the tab refactor is complete, **When** a developer searches the codebase for imports of `AdvancedSettings`, **Then** no references are found.
2. **Given** the full test suite runs after cleanup, **When** all tests execute, **Then** there are no failures caused by missing or renamed components.
3. **Given** a developer reviews the settings directory, **When** they list the files, **Then** only the active components remain: `EssentialSettings.tsx`, `SecretsManager.tsx`, `PreferencesTab.tsx`, `AdminTab.tsx`, `SettingsSection.tsx`, `DynamicDropdown.tsx`, `DisplayPreferences.tsx`, `WorkflowDefaults.tsx`, `NotificationPreferences.tsx`, `SignalConnection.tsx`, `GlobalSettings.tsx`, `ProjectSettings.tsx`, and `globalSettingsSchema.ts`.

---

### Edge Cases

- What happens when the user has no repositories? The Secrets tab should display a clear message ("No repositories available") and disable the secret management controls.
- What happens when the GitHub API rate limit is exceeded during secrets operations? The system should display a user-friendly error message with a retry option and show the rate-limit reset time.
- What happens when the `copilot` environment does not exist in the selected repository? The system should automatically create the environment before attempting to store the first secret.
- What happens when a user tries to set a secret with an empty value? The system should reject the submission with a validation error ("Secret value cannot be empty").
- What happens when a user enters a secret name that does not start with `COPILOT_MCP_`? The system should display a warning ("GitHub Copilot only exposes secrets prefixed with COPILOT_MCP_ to MCP servers") but still allow the operation.
- What happens when the admin user ID is not configured? The Admin tab is not shown to any user; admin-only settings remain accessible only via the existing backend admin endpoints.
- What happens when a user is on the Secrets tab and their session expires? The system should redirect them to the login page; upon re-authentication, they should return to the Secrets tab.
- What happens if the repository's encryption public key cannot be fetched? The system should show an error ("Unable to encrypt secret — cannot reach GitHub API") and prevent the save operation.

## Requirements *(mandatory)*

### Functional Requirements

**Tab-Based Layout**

- **FR-001**: The Settings page MUST display a tabbed interface with four tabs: "Essential", "Secrets", "Preferences", and "Admin".
- **FR-002**: The "Essential" tab MUST be the default active tab when the Settings page loads without a URL hash.
- **FR-003**: Each tab MUST update the URL hash fragment (e.g., `#essential`, `#secrets`, `#preferences`, `#admin`) when selected.
- **FR-004**: Navigating directly to a URL with a tab hash fragment MUST activate the corresponding tab on page load.
- **FR-005**: The "Admin" tab MUST only be visible to users whose identity matches the configured admin user. Non-admin users MUST NOT see or access the Admin tab.
- **FR-006**: Unsaved changes within a tab MUST be preserved when switching between tabs and restored when the user returns.
- **FR-007**: The per-section save button pattern MUST be preserved — each settings card saves independently.

**Essential Tab**

- **FR-008**: The Essential tab MUST display: AI provider selection, chat model dropdown (dynamic), agent model dropdown (dynamic), and temperature slider.
- **FR-009**: The Essential tab MUST NOT include Signal Connection settings (moved to Preferences).

**Preferences Tab**

- **FR-010**: The Preferences tab MUST display: Display Preferences, Workflow Defaults, Notification Preferences, and Signal Connection, each in its own card section.
- **FR-011**: Each card section in the Preferences tab MUST have its own independent Save button.

**Admin Tab**

- **FR-012**: The Admin tab MUST display: Global AI defaults (provider, model, temperature), allowed models list management, and project board configuration.
- **FR-013**: The Admin tab MUST reuse existing validation logic for global settings.
- **FR-014**: If a non-admin user navigates to `/settings#admin`, the system MUST fall back to the Essential tab without showing an error.

**Secrets Management — Backend**

- **FR-015**: The system MUST provide an endpoint to list secret names and metadata (created date, updated date) for a given repository environment. Secret values MUST never be returned.
- **FR-016**: The system MUST provide an endpoint to create or update a secret in a repository environment. The secret value MUST be encrypted using NaCl sealed-box encryption with the repository's public key before being sent to GitHub.
- **FR-017**: The system MUST provide an endpoint to delete a secret from a repository environment.
- **FR-018**: The system MUST automatically create the `copilot` environment in the repository if it does not already exist, before performing any secret operations.
- **FR-019**: Secret names MUST match the pattern `^[A-Z][A-Z0-9_]*$` and MUST NOT exceed 255 characters.
- **FR-020**: Secret values MUST NOT exceed 64 KB in size.
- **FR-021**: All secrets endpoints MUST require an authenticated user session.

**Secrets Management — Frontend**

- **FR-022**: The Secrets tab MUST display a repository selector populated with the user's available repositories.
- **FR-023**: The Secrets tab MUST display a "Known Secrets" section listing predefined MCP secrets with friendly labels (e.g., `COPILOT_MCP_CONTEXT7_API_KEY` → "Context7 API Key") and a status badge indicating whether each secret is currently set.
- **FR-024**: The Secrets tab MUST provide Set, Update, and Remove actions for each known secret.
- **FR-025**: The Secrets tab MUST provide an "Add Custom Secret" form for user-defined secrets with name and value fields.
- **FR-026**: Secret value inputs MUST use password-type fields with a show/hide toggle, MUST NOT pre-fill values from the server, and MUST have autocomplete disabled.
- **FR-027**: The system MUST display a warning (not a blocking error) when a custom secret name does not start with `COPILOT_MCP_`.

**MCP Preset Integration**

- **FR-028**: MCP presets MUST declare which secrets they require (e.g., Context7 requires `COPILOT_MCP_CONTEXT7_API_KEY`).
- **FR-029**: The system MUST provide an endpoint to check whether specific secrets are set for a given repository environment, returning a name-to-boolean map.
- **FR-030**: The Tools page MUST display a warning indicator on MCP presets whose required secrets are not configured.

**Accessibility**

- **FR-031**: Tab panels MUST have `role="tabpanel"` and `aria-labelledby` attributes linked to their corresponding tab trigger.
- **FR-032**: Secret inputs MUST have `aria-label` attributes and `autocomplete="off"`.
- **FR-033**: Focus MUST automatically move to the active tab panel content when a tab is selected.

**Cleanup**

- **FR-034**: The following components MUST be removed after their functionality is consolidated into the new tab structure: `AIPreferences.tsx`, `AISettingsSection.tsx`, `DisplaySettings.tsx`, `WorkflowSettings.tsx`, `NotificationSettings.tsx`, `AdvancedSettings.tsx`.
- **FR-035**: All tests referencing deleted components MUST be updated or removed.

### Key Entities

- **Secret**: A named credential stored as a GitHub repository environment secret. Attributes: name (uppercase alphanumeric with underscores), created date, updated date. Values are write-only (never returned by GitHub). Associated with a specific repository and environment.
- **Environment**: A GitHub deployment environment (default: `copilot`) that scopes secrets. Created automatically if it does not exist. Associated with a repository.
- **Known Secret**: A predefined MCP secret with a machine name (e.g., `COPILOT_MCP_CONTEXT7_API_KEY`) and a human-friendly label (e.g., "Context7 API Key"). Defined as a constant list, driven by MCP preset requirements.
- **MCP Preset**: An existing entity representing a pre-configured MCP tool integration. Extended with a `required_secrets` list indicating which secrets must be set for the preset to function.

### Assumptions

- The GitHub `copilot` environment naming convention is stable and follows the established pattern for `$COPILOT_MCP_*` secret access by MCP servers.
- Users have sufficient GitHub permissions (repository admin or environment management rights) to create environments and manage secrets in their repositories.
- The existing `require_session` authentication dependency provides adequate authorization for secrets operations — any authenticated user can manage secrets in repositories they have access to.
- The known secrets list is maintainable as a static constant and will be updated manually when new MCP presets are added.
- The existing per-section save button pattern is the expected UX contract and should not be changed to a global save.
- NaCl sealed-box encryption is the only encryption method accepted by the GitHub API for secret values.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can locate and modify their AI provider and model settings within 2 clicks (navigate to Settings → change setting) without scrolling or expanding hidden sections.
- **SC-002**: 100% of settings previously accessible via the collapsed "Advanced Settings" accordion are accessible via the new tab structure with no functionality loss.
- **SC-003**: Users can complete a full secrets round-trip (set a secret, verify it shows as "Set", delete it, verify removal) in under 60 seconds.
- **SC-004**: Non-admin users never see admin-only settings tabs or controls — 0% visibility of admin content for non-admin users.
- **SC-005**: All existing settings (user, global, project) save and load correctly after the refactor with no regressions.
- **SC-006**: Direct URL navigation with tab hash fragments (e.g., `/settings#secrets`) correctly activates the target tab 100% of the time.
- **SC-007**: The Settings page initial load time does not increase by more than 10% compared to the pre-refactor baseline.
- **SC-008**: The total number of source files in the settings module decreases by at least 5 through consolidation and removal of redundant code.
- **SC-009**: MCP presets with unconfigured required secrets display a visible warning indicator on the Tools page, achieving 100% coverage of presets with required secrets.
- **SC-010**: All secret inputs pass accessibility audit for password fields (aria-label present, autocomplete disabled, proper role attributes on tab panels).
