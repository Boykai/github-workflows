# Feature Specification: Settings Page Refactor with Secrets

**Feature Branch**: `047-settings-page-refactor`  
**Created**: 2026-03-16  
**Status**: Draft  
**Input**: User description: "Refactor the Settings page from a monolithic form dump (18 components, 5 sections behind a collapsible) into a clean tabbed layout showing only essentials by default, with a new GitHub Repository Environment Secrets feature for MCP API keys (e.g. COPILOT_MCP_CONTEXT7_API_KEY)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Tab-Based Settings Navigation (Priority: P1)

As a user, I want the Settings page to be organized into clearly labeled tabs so I can quickly find and change the settings I need without scrolling through a long collapsible form.

The current Settings page presents 18 components across 5 sections behind a single collapsible panel, making it difficult to locate specific settings. The new layout replaces this with a tab-based design where the most commonly used settings (AI provider, model, temperature) are immediately visible on the default "Essential" tab. Less frequently used settings are organized into separate "Preferences" and "Secrets" tabs, with admin-only settings in a conditionally visible "Admin" tab.

**Why this priority**: This is the foundational UX improvement. 90% of users only need to configure their AI provider, model, and temperature. Surfacing these immediately reduces time-to-task and eliminates confusion. All other stories depend on this tab structure being in place.

**Independent Test**: Can be fully tested by navigating to the Settings page and verifying that four tabs are visible (three for non-admin users), the Essential tab is selected by default, and each tab shows the correct group of settings.

**Acceptance Scenarios**:

1. **Given** a user navigates to the Settings page, **When** the page loads, **Then** a tab bar with "Essential", "Secrets", and "Preferences" tabs is displayed and "Essential" is selected by default.
2. **Given** an admin user navigates to the Settings page, **When** the page loads, **Then** a fourth "Admin" tab is also visible in the tab bar.
3. **Given** a non-admin user navigates to the Settings page, **When** the page loads, **Then** the "Admin" tab is not visible.
4. **Given** a user is viewing the Essential tab, **When** they click the "Preferences" tab, **Then** the display, workflow, notification, and Signal messaging settings are shown.
5. **Given** a user has unsaved changes in one tab, **When** they attempt to navigate away from the Settings page, **Then** they receive a warning about unsaved changes.
6. **Given** a user clicks a tab, **When** the tab content loads, **Then** the URL fragment updates to match the tab name (e.g., `#essential`, `#preferences`).
7. **Given** a user navigates to `/settings#preferences`, **When** the page loads, **Then** the Preferences tab is automatically selected.

---

### User Story 2 — Managing MCP API Key Secrets (Priority: P2)

As a user, I want to securely store and manage API keys required by MCP tool presets (such as the Context7 API key) directly from the Settings page, so that my MCP integrations can authenticate with external services without me having to configure secrets manually in GitHub.

The system stores secrets as GitHub Repository Environment Secrets under a dedicated `copilot` environment. Secret values are encrypted before transmission and are never displayed after being set — only the secret name and status (set or not set) are visible. A curated list of well-known secrets is presented with friendly labels, and users may also add custom secrets following the `COPILOT_MCP_*` naming convention.

**Why this priority**: This is the primary new capability of the feature. Without it, users must manually configure GitHub environment secrets through the GitHub UI, which is error-prone and disconnected from the tool configuration workflow. This story enables a seamless in-app experience for secret management.

**Independent Test**: Can be fully tested by navigating to the Secrets tab, selecting a repository, setting a known secret, verifying its status changes to "Set", then removing it and verifying it returns to "Not Set".

**Acceptance Scenarios**:

1. **Given** a user opens the Secrets tab, **When** the tab loads, **Then** a repository selector populated with the user's repositories is displayed, and the environment defaults to "copilot".
2. **Given** a user has selected a repository, **When** the secrets list loads, **Then** each well-known secret (e.g., "Context7 API Key") shows a status badge indicating whether it is currently set or not set.
3. **Given** a user clicks "Set" on an unset known secret, **When** they enter a value in the password input and confirm, **Then** the secret is encrypted and stored in the selected repository's `copilot` environment, and the status badge updates to "Set".
4. **Given** a user clicks "Update" on an already-set secret, **When** they enter a new value and confirm, **Then** the existing secret value is replaced.
5. **Given** a user clicks "Remove" on a set secret, **When** they confirm the removal, **Then** the secret is deleted from the repository environment and the status returns to "Not Set".
6. **Given** a user wants to add a custom secret, **When** they enter a secret name and value in the "Add Custom Secret" form, **Then** the system validates the name matches the uppercase naming pattern and the value does not exceed 64 KB before storing it.
7. **Given** a user enters an invalid secret name (e.g., lowercase, special characters, exceeds 255 characters), **When** they attempt to save, **Then** a validation error is displayed and the secret is not created.
8. **Given** a user sets a secret, **When** they return to the Secrets tab later, **Then** the secret value is never pre-filled in the input — only the name and set/not-set status are visible.

---

### User Story 3 — MCP Preset Secret Status Integration (Priority: P3)

As a user, I want to see a warning on the Tools page when an MCP preset requires an API key that has not been configured, so I can quickly identify and resolve missing credentials before attempting to use the tool.

Each MCP preset may declare one or more required secrets. When viewing presets on the Tools page, any preset with an unconfigured required secret displays a visible warning badge. Clicking the warning or a related prompt navigates the user directly to the Secrets tab on the Settings page.

**Why this priority**: This bridges the gap between tool configuration and secret management, reducing user confusion when an MCP tool fails due to missing credentials. It depends on both the tab layout (US1) and secrets management (US2) being functional.

**Independent Test**: Can be fully tested by adding an MCP preset that requires a secret, verifying the warning badge appears on the Tools page, then setting the required secret and verifying the warning disappears.

**Acceptance Scenarios**:

1. **Given** a user views the Tools page, **When** an MCP preset has required secrets that are not configured, **Then** a warning badge (e.g., "⚠ API key not configured") is displayed on that preset.
2. **Given** a user clicks the warning badge or related prompt, **When** the navigation completes, **Then** the Settings page opens with the Secrets tab selected (`/settings#secrets`).
3. **Given** all required secrets for a preset are configured, **When** the user views the Tools page, **Then** no warning badge is displayed for that preset.
4. **Given** a user adds a new MCP preset that requires an unconfigured secret, **When** the preset is added, **Then** a notification prompts the user to configure the missing API key with a link to the Secrets tab.

---

### User Story 4 — Consolidated Preferences Management (Priority: P3)

As a user, I want all my non-essential preferences (display, workflow, notifications, Signal messaging) consolidated into a single "Preferences" tab with clearly grouped sections, so I can manage all secondary settings in one place without navigating a collapsible panel.

**Why this priority**: This is a UX consolidation story. The current collapsible layout makes these settings hard to discover. Grouping them in a dedicated tab improves discoverability while keeping the Essential tab clean. Each preference group retains its own save button to match the existing per-section save behavior.

**Independent Test**: Can be fully tested by navigating to the Preferences tab and verifying that display, workflow, notification, and Signal messaging settings are all present and each section can be independently saved.

**Acceptance Scenarios**:

1. **Given** a user opens the Preferences tab, **When** the tab loads, **Then** display preferences, workflow defaults, notification preferences, and Signal connection settings are each shown in distinct card-grouped sections.
2. **Given** a user changes a display preference, **When** they click the save button in the display section, **Then** only the display preferences are saved and a success confirmation is shown.
3. **Given** a user has unsaved changes in the workflow section, **When** they save the notification section, **Then** the workflow section still shows unsaved changes (sections are independent).

---

### User Story 5 — Admin-Only Settings Tab (Priority: P3)

As an admin user, I want a dedicated "Admin" tab on the Settings page where I can manage instance-wide defaults (global AI settings, allowed models, display defaults, workflow defaults, notification defaults) and per-project configuration, so that these powerful settings are clearly separated from personal preferences and hidden from non-admin users.

**Why this priority**: Separating admin settings reduces cognitive load for regular users and prevents confusion about which settings are personal vs. instance-wide. The admin check is enforced both in the UI (tab visibility) and on the server side (existing admin-only backend validation).

**Independent Test**: Can be fully tested by logging in as an admin and verifying the Admin tab is visible and functional, then logging in as a non-admin and verifying it is absent.

**Acceptance Scenarios**:

1. **Given** an admin user opens the Settings page, **When** the page loads, **Then** the Admin tab is visible and contains global defaults, allowed models configuration, and project board settings.
2. **Given** a non-admin user opens the Settings page, **When** the page loads, **Then** the Admin tab is not rendered in the tab bar.
3. **Given** an admin changes the global AI model default, **When** they save, **Then** the new default is applied instance-wide for users who have not set a personal override.

---

### Edge Cases

- What happens when the user's GitHub token lacks permissions to manage environment secrets? The system displays a clear permission error and suggests the user verify their repository access.
- What happens when the `copilot` environment does not yet exist in the repository? The system automatically creates the environment before attempting to store the first secret.
- What happens when a user attempts to set a secret with an empty value? The system rejects the request with a validation error.
- What happens when the GitHub API is temporarily unavailable while managing secrets? The system displays an appropriate error message and allows the user to retry.
- What happens when a secret name conflicts with an existing secret? The system performs an upsert (update) and notifies the user that the existing value will be replaced.
- What happens when a user navigates to `/settings#admin` but is not an admin? The URL fragment is ignored and the default Essential tab is selected.
- What happens when the user has no repositories? The Secrets tab displays an empty state explaining that a repository is required.
- What happens when a secret value exceeds 64 KB? The system rejects the request with a validation error before attempting encryption.

## Requirements *(mandatory)*

### Functional Requirements

**Tab Navigation**

- **FR-001**: The Settings page MUST present settings in a tabbed layout with tabs labeled "Essential", "Secrets", "Preferences", and "Admin".
- **FR-002**: The "Essential" tab MUST be selected by default when no URL fragment is specified.
- **FR-003**: The "Admin" tab MUST only be visible to users identified as administrators.
- **FR-004**: Each tab MUST update the URL fragment when selected (e.g., `#essential`, `#secrets`, `#preferences`, `#admin`).
- **FR-005**: The Settings page MUST select the corresponding tab when loaded with a URL fragment.
- **FR-006**: The unsaved-changes warning MUST continue to function across all tabs.

**Essential Tab**

- **FR-007**: The Essential tab MUST display the AI provider selector, model selector, and temperature slider.
- **FR-008**: The Essential tab MUST NOT display Signal messaging, display, workflow, or notification settings.

**Secrets Tab**

- **FR-009**: The Secrets tab MUST display a repository selector populated from the user's available repositories.
- **FR-010**: The Secrets tab MUST default the environment name to "copilot".
- **FR-011**: The system MUST display a list of well-known secrets with friendly labels and set/not-set status badges.
- **FR-012**: Users MUST be able to set, update, and remove individual secrets.
- **FR-013**: Secret values MUST be encrypted before transmission to the storage backend.
- **FR-014**: Secret values MUST never be displayed or pre-filled after being set — only the name and status are shown.
- **FR-015**: Users MUST be able to add custom secrets via an "Add Custom Secret" form.
- **FR-016**: Secret names MUST match the pattern `^[A-Z][A-Z0-9_]*$` and not exceed 255 characters.
- **FR-017**: Secret values MUST not exceed 64 KB in size.
- **FR-018**: The system MUST automatically create the target environment if it does not already exist.
- **FR-019**: Secret input fields MUST use password-type inputs with show/hide toggle and `autocomplete="off"`.

**Preferences Tab**

- **FR-020**: The Preferences tab MUST consolidate display preferences, workflow defaults, notification preferences, and Signal connection settings.
- **FR-021**: Each preference group MUST have its own independent save button.
- **FR-022**: Saving one preference group MUST NOT affect unsaved changes in other groups.

**Admin Tab**

- **FR-023**: The Admin tab MUST display global AI settings, display defaults, workflow defaults, notification defaults, allowed models configuration, and project board settings.
- **FR-024**: Admin tab visibility MUST be enforced in the UI by checking the user's admin status.
- **FR-025**: Admin settings mutations MUST be validated server-side (existing backend enforcement).

**MCP Preset Integration**

- **FR-026**: Each MCP preset definition MUST be able to declare a list of required secret names.
- **FR-027**: The system MUST provide a way to check whether specific secrets are configured for a given repository and environment.
- **FR-028**: The Tools page MUST display a warning badge on any MCP preset that has unconfigured required secrets.
- **FR-029**: The warning badge or an associated prompt MUST link to the Settings page Secrets tab (`/settings#secrets`).

**Accessibility**

- **FR-030**: Tab panels MUST include appropriate accessibility roles and labels.
- **FR-031**: Secret input fields MUST include descriptive accessibility labels.
- **FR-032**: Focus MUST move to the tab panel content when a tab is selected.

### Key Entities

- **Secret**: A named credential stored in a GitHub Repository Environment. Attributes: name (unique per environment, uppercase with underscores), status (set or not set), created timestamp, last updated timestamp. The actual value is write-only and never retrievable.
- **Environment**: A GitHub Repository Environment (e.g., `copilot`) that serves as a namespace for secrets. Automatically created if it does not exist.
- **Known Secret**: A predefined secret with a friendly display label, mapped to an MCP preset's required credentials (e.g., `COPILOT_MCP_CONTEXT7_API_KEY` → "Context7 API Key").
- **MCP Preset**: An existing tool configuration that may declare required secrets. The preset's required secrets list determines which known secrets appear in the Secrets Manager and which presets show warning badges.
- **Settings Tab**: One of four organizational groups (Essential, Secrets, Preferences, Admin) that segment the Settings page. Each tab represents an independently navigable section.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can locate and change their AI provider, model, and temperature settings within 10 seconds of opening the Settings page (down from the current experience of scrolling/expanding to find them).
- **SC-002**: Users can set, update, or remove an MCP API key secret in under 30 seconds from the Settings page without leaving the application.
- **SC-003**: 100% of secret values are encrypted before leaving the client, and no secret value is ever displayed or pre-filled after being stored.
- **SC-004**: Non-admin users never see the Admin tab — zero admin-only settings are exposed to regular users in the UI.
- **SC-005**: All existing settings (user, global, project) continue to save and load correctly with no regressions after the refactor.
- **SC-006**: Deep links using URL fragments (e.g., `/settings#secrets`) correctly select the target tab on page load 100% of the time.
- **SC-007**: The number of visible settings components on initial page load is reduced from 18+ to 3–4 (AI provider, model, temperature, and optionally agent model) for the default Essential tab.
- **SC-008**: Users on the Tools page can identify MCP presets with missing API keys at a glance via visible warning badges, without trial-and-error.
- **SC-009**: Tab navigation, secret management, and all settings interactions are fully operable via keyboard with appropriate focus management and accessibility labels.

## Assumptions

- The existing backend admin enforcement (server-side validation on global settings endpoints) is sufficient; no new admin authorization logic is needed beyond UI tab visibility.
- GitHub's environment secrets API uses NaCl sealed-box encryption, which requires a dedicated encryption library on the backend.
- The `copilot` environment name follows GitHub's convention for Copilot MCP secrets (`$COPILOT_MCP_*` prefix).
- Users have sufficient GitHub permissions (repository admin or environment write access) to manage environment secrets for their repositories.
- The existing `GitHubClientFactory` client pooling pattern is appropriate for the secrets service.
- Per-section save buttons (one save button per settings group) is the expected UX contract and should be preserved in the new tab layout.
- The list of well-known secrets is a small, curated set driven by MCP preset definitions and does not need a dynamic discovery mechanism.
- Custom secrets are limited to the `COPILOT_MCP_*` prefix convention by recommendation (warning), not by hard enforcement.
- Signal connection settings are classified as a "preference" rather than an "essential" setting, since most users do not use Signal integration.
