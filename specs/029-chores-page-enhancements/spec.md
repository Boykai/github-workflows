# Feature Specification: Chores Page — Counter Fixes, Featured Rituals Panel, Inline Editing, AI Enhance Toggle, Agent Pipeline Config & Auto-Merge PR Flow

**Feature Branch**: `029-chores-page-enhancements`  
**Created**: 2026-03-07  
**Status**: Draft  
**Input**: User description: "On chores page — ensure 'Every x issues' counters track per-Chore GitHub Parent Issue creation since last run; add Featured Rituals panel (next run, most recently run, most run); inline-editable Chore definitions with PR-on-save; AI Enhance toggle controlling Issue Template body vs. metadata-only generation; per-Chore Agent Pipeline selector (saved config or Auto); double-confirmation + auto-merge PR flow for new Chores."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Per-Chore "Every x Issues" Counter Fix (Priority: P1)

As a project maintainer, I want each Chore tile's "Every x issues" counter to reflect the number of GitHub Parent Issues created since that specific Chore last ran, so that I can trust the countdown is accurate and the Chore fires at the correct threshold.

**Why this priority**: The counter is the primary feedback mechanism for issue-triggered Chores. An inaccurate counter means Chores fire at the wrong time or never fire, undermining the entire Chores feature.

**Independent Test**: Can be fully tested by creating a Chore with an "Every 5 issues" trigger, creating several GitHub Parent Issues, and verifying the tile badge decrements correctly from 5 toward 0.

**Acceptance Scenarios**:

1. **Given** a Chore configured with "Every 5 issues" that last ran 3 Parent Issues ago, **When** the user views the Chores page, **Then** the tile counter displays "2 remaining" (5 − 3).
2. **Given** a Chore whose counter has reached 0 (threshold met), **When** the system evaluates trigger conditions, **Then** the Chore executes and its counter resets based on new Parent Issue creation from that point forward.
3. **Given** two Chores with different "Every x issues" thresholds that last ran at different times, **When** the user views the Chores page, **Then** each tile shows an independent counter scoped to its own last-run timestamp.
4. **Given** a Chore that has never run, **When** the user views the Chores page, **Then** the counter reflects all GitHub Parent Issues created since the Chore was first created.

---

### User Story 2 — Featured Rituals Panel (Priority: P1)

As a project maintainer, I want a "Featured Rituals" panel on the Chores page highlighting the next-to-run, most-recently-run, and most-frequently-run Chores, so that I can quickly assess Chore activity and priorities at a glance.

**Why this priority**: Discoverability of Chore status is critical for maintainers managing multiple Chores. Without a summary panel, users must scan every tile to understand what is happening.

**Independent Test**: Can be fully tested by creating several Chores with varying execution histories and verifying the panel correctly identifies and displays the three highlighted Chores.

**Acceptance Scenarios**:

1. **Given** multiple Chores exist with different remaining-issue counts, **When** the user views the Featured Rituals panel, **Then** the "Next Run" card displays the Chore with the fewest remaining issues until its trigger fires.
2. **Given** multiple Chores have been executed at different times, **When** the user views the Featured Rituals panel, **Then** the "Most Recently Run" card displays the Chore with the most recent execution timestamp.
3. **Given** multiple Chores have different total execution counts, **When** the user views the Featured Rituals panel, **Then** the "Most Run" card displays the Chore with the highest all-time execution count.
4. **Given** a Chore highlight card is displayed, **When** the user clicks the quick-action link on the card, **Then** the user is navigated to that Chore's detail or edit view.
5. **Given** no Chores exist yet, **When** the user views the Chores page, **Then** the Featured Rituals panel displays an empty state with guidance to create a first Chore.

---

### User Story 3 — Inline Chore Definition Editing with PR on Save (Priority: P1)

As a project maintainer, I want to edit a Chore's definition fields directly on the Chores page and have my changes saved as a Pull Request, so that I can modify Chores without leaving the UI and all changes are tracked through version control.

**Why this priority**: Editing Chores is a core workflow. Without inline editing, users must manually edit files and create PRs, which is slow and error-prone.

**Independent Test**: Can be fully tested by modifying a Chore's name or description inline, clicking Save, and verifying a PR is opened with the correct file changes.

**Acceptance Scenarios**:

1. **Given** the user is viewing a Chore on the Chores page, **When** the page loads, **Then** Chore definition fields (name, description, trigger configuration, etc.) render as editable inputs and textareas.
2. **Given** the user has modified one or more fields, **When** a field value differs from the last saved state, **Then** a dirty-state indicator (banner or asterisk in the page title) appears.
3. **Given** the user has unsaved changes, **When** the user attempts to navigate away from the Chores page, **Then** a confirmation dialog appears: "You have unsaved changes — are you sure you want to leave?"
4. **Given** the user has made edits and clicks Save, **When** the save completes, **Then** a Pull Request is created against the repository with the updated Chore definition file(s), including an auto-generated PR title and description.
5. **Given** the user has unsaved changes and confirms navigation away, **When** the dialog is accepted, **Then** all unsaved changes are discarded and the user navigates to the target page.

---

### User Story 4 — AI Enhance Toggle for Issue Template Creation (Priority: P2)

As a project maintainer, I want an "AI Enhance" toggle on the Chore creation/editing flow that controls whether the AI rewrites my chat input or uses it verbatim as the GitHub Issue Template body, so that I have full control over the template content when I prefer my own wording.

**Why this priority**: This gives users creative control over Issue Templates. The feature extends an existing workflow and is important for user satisfaction, but the core Chore functionality works without it.

**Independent Test**: Can be fully tested by creating a Chore with AI Enhance OFF, providing specific chat input, and verifying the Issue Template body matches the input exactly while metadata fields are AI-generated.

**Acceptance Scenarios**:

1. **Given** the user is in the Chore creation or editing flow, **When** the form loads, **Then** an "AI Enhance" toggle is visible, styled consistently with the "+ Add Agent" pop-out on the Agents page, defaulting to ON.
2. **Given** AI Enhance is ON, **When** the user provides chat input and proceeds, **Then** the existing AI-driven flow generates both the Issue Template body and metadata (name, about, title, labels, etc.).
3. **Given** AI Enhance is OFF, **When** the user provides chat input and proceeds, **Then** the user's exact chat input is used verbatim as the Issue Template body, and the Chat Agent generates only the metadata fields (name, about, title, labels, assignees) without modifying the body.
4. **Given** AI Enhance is OFF and the user's chat input contains formatting or special characters, **When** the Issue Template is generated, **Then** the body preserves all original formatting, line breaks, and special characters exactly as entered.

---

### User Story 5 — Per-Chore Agent Pipeline Configuration (Priority: P2)

As a project maintainer, I want to assign a specific saved Agent Pipeline configuration (or "Auto") to each Chore, so that different Chores can use different agent configurations while "Auto" always inherits the project's current active pipeline.

**Why this priority**: Pipeline configurability per Chore is important for advanced workflows but not blocking for basic Chore functionality.

**Independent Test**: Can be fully tested by creating a Chore with a specific pipeline selection, verifying it uses that pipeline at execution, then switching to "Auto" and verifying it uses the project's active pipeline.

**Acceptance Scenarios**:

1. **Given** the user is creating or editing a Chore, **When** the configuration form loads, **Then** a "Agent Pipeline" selector is displayed with options for each saved Agent Pipeline configuration and an "Auto" option.
2. **Given** a Chore is configured with a specific saved Agent Pipeline, **When** the Chore executes, **Then** it uses that exact pipeline configuration.
3. **Given** a Chore is configured with "Auto", **When** the Chore executes, **Then** it resolves to the currently active Agent Pipeline configuration for the associated Project at that moment (not a cached value).
4. **Given** a previously saved Agent Pipeline is deleted, **When** a Chore still references that pipeline, **Then** the system falls back to "Auto" behavior and notifies the user that the configured pipeline is no longer available.

---

### User Story 6 — Double-Confirmation & Auto-Merge PR Flow for New Chores (Priority: P2)

As a project maintainer, I want a two-step confirmation modal when saving a new Chore, followed by automatic GitHub Issue creation, PR creation, and PR auto-merge into main, so that new Chores are seamlessly added to the codebase with appropriate user awareness of the action being taken.

**Why this priority**: Auto-merge is a convenience feature that streamlines the Chore creation workflow. The two-step confirmation is a safety mechanism. Both enhance user experience but basic Chore creation works without them.

**Independent Test**: Can be fully tested by creating a new Chore, verifying both confirmation steps appear in sequence, then confirming that a GitHub Issue is created, a PR is opened, and the PR is auto-merged.

**Acceptance Scenarios**:

1. **Given** the user clicks Save on a brand-new Chore, **When** the save action is triggered, **Then** a first confirmation modal appears informing the user that the Chore file will be automatically committed to the code repository.
2. **Given** the user acknowledges the first confirmation, **When** they proceed, **Then** a second confirmation modal appears with a final "Yes, Create Chore" action.
3. **Given** the user confirms both steps, **When** the system processes the request, **Then** it sequentially: (a) creates a GitHub Issue for the Chore, (b) opens a PR containing the new Chore definition file, and (c) automatically merges that PR into the main branch.
4. **Given** the auto-merge succeeds, **When** the process completes, **Then** the user sees a success notification (toast) confirming the Chore has been added to the repository.
5. **Given** the auto-merge fails due to merge conflicts or CI failures, **When** the error occurs, **Then** the user is notified via a toast or status indicator, the PR is left open for manual resolution, and the Chore record is still persisted locally.
6. **Given** the user cancels at either confirmation step, **When** the dialog is dismissed, **Then** no Issue, PR, or merge action occurs and the user returns to the Chore form with their input preserved.

---

### Edge Cases

- What happens when a Chore's "Every x issues" threshold is set to 1 and a Parent Issue is created? The Chore should trigger immediately and the counter should show 0 remaining briefly before resetting.
- What happens when multiple Parent Issues are created simultaneously (e.g., bulk import)? The counter must account for all issues created since the Chore's last run, regardless of creation timing.
- What happens when a Chore has never executed and has no `last_run_at` timestamp? The system should count all Parent Issues created since the Chore's creation date.
- What happens when the user edits a Chore and the underlying file has been modified by another user since the page loaded? The system should detect the conflict and warn the user before creating the PR.
- What happens when the GitHub API is unavailable during PR creation or auto-merge? The system should display an error message, persist the Chore locally, and allow the user to retry the PR/merge operation.
- What happens when a saved Agent Pipeline referenced by a Chore is deleted? The system should fall back to "Auto" and display a notification.
- What happens when no Chores exist for the Featured Rituals panel? The panel should render an empty/onboarding state.
- What happens when the user toggles AI Enhance mid-flow after partially generating content? The toggle change should apply to the next generation step without losing existing input.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST recalculate each Chore's "Every x issues" counter by counting the number of GitHub Parent Issues created since the timestamp of that Chore's most recent execution, scoping the count per-Chore rather than globally.
- **FR-002**: System MUST use the per-Chore Parent Issue count as both the displayed counter on the Chore tile and as the condition evaluated when determining whether the Chore's trigger threshold has been met.
- **FR-003**: System MUST display a "Featured Rituals" panel on the Chores page containing three distinct Chore highlight cards: "Next Run" (fewest remaining issues until trigger), "Most Recently Run" (most recent `last_run_at` timestamp), and "Most Run" (highest total execution count).
- **FR-004**: Each Featured Rituals card MUST display the Chore name, the relevant statistic, and a quick-action link to navigate to that Chore.
- **FR-005**: System MUST render Chore definition fields as editable inputs and textareas and display a dirty-state indicator (unsaved-changes banner or title asterisk) whenever any field value differs from the last saved state.
- **FR-006**: System MUST prompt the user with a "You have unsaved changes — are you sure you want to leave?" confirmation dialog when navigating away from the Chores page with unsaved edits.
- **FR-007**: System MUST, upon saving an edited Chore definition, open a Pull Request against the repository containing the updated Chore definition file(s) with an auto-generated PR title and description summarizing the changes.
- **FR-008**: System MUST provide an "AI Enhance" toggle on the Chore creation/edit form, co-located with the flow controls similarly to the "+ Add Agent" pop-out on the Agents page. The toggle MUST default to ON.
- **FR-009**: When "AI Enhance" is toggled OFF, the system MUST use the user's exact chat input verbatim as the GitHub Issue Template body while the Chat Agent is still invoked to generate all template metadata (name, about, title, labels, assignees) without altering the body content.
- **FR-010**: When "AI Enhance" is toggled ON, the system MUST preserve the existing AI-driven GitHub Issue Template generation flow for both body and metadata.
- **FR-011**: System MUST provide a per-Chore "Agent Pipeline" configuration selector with options for each saved Agent Pipeline configuration and an "Auto" option.
- **FR-012**: The "Auto" Agent Pipeline option MUST resolve to the currently active Agent Pipeline configuration for the associated Project at execution time, not a cached or stored value.
- **FR-013**: System MUST display a two-step confirmation modal when saving a new Chore: step 1 informs the user the Chore file will be automatically added to the code repository and asks for acknowledgment; step 2 presents a final "Yes, Create Chore" confirmation before proceeding.
- **FR-014**: After both confirmations are accepted for a new Chore, the system MUST sequentially: (a) create a GitHub Issue for the Chore, (b) open a PR containing the new Chore definition file, and (c) automatically merge that PR into the main branch.
- **FR-015**: System SHOULD surface merge status (success or failure) of the auto-merge PR back to the user via a toast notification or status indicator on the Chores page.
- **FR-016**: System SHOULD handle PR merge conflicts or CI failures on the auto-merge gracefully by notifying the user and leaving the PR open for manual resolution rather than silently failing.
- **FR-017**: If a saved Agent Pipeline referenced by a Chore is deleted, the system MUST fall back to "Auto" behavior and notify the user.

### Key Entities

- **Chore**: A recurring task definition containing a name, description, trigger configuration (type and threshold), `last_run_at` timestamp, `execution_count`, `ai_enhance_enabled` flag, and `agent_pipeline_id` reference. A Chore belongs to a Project and is stored as a definition file in the code repository.
- **Chore Trigger**: The condition that determines when a Chore should execute. For "Every x issues" triggers, the condition is met when the count of GitHub Parent Issues created since the Chore's `last_run_at` reaches or exceeds the configured threshold.
- **Featured Ritual**: A derived view (not a stored entity) that surfaces a Chore based on one of three ranking criteria: soonest to trigger ("Next Run"), most recent execution ("Most Recently Run"), or highest execution count ("Most Run").
- **Agent Pipeline Configuration**: A saved set of agent settings that can be assigned to a Chore. The special "Auto" value is not a stored configuration but a runtime directive to use the Project's currently active pipeline.
- **GitHub Issue Template**: A structured template containing a body (content) and metadata (name, about, title, labels, assignees). The body source depends on the AI Enhance toggle state; metadata is always AI-generated.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each Chore tile's counter accurately reflects the number of GitHub Parent Issues created since that specific Chore's last execution, with zero drift from the actual count on page load or refresh.
- **SC-002**: The Featured Rituals panel correctly identifies and displays the three highlighted Chores (next run, most recently run, most run) within 2 seconds of page load.
- **SC-003**: Users can edit any Chore definition field inline and save changes in under 30 seconds, resulting in a Pull Request being created automatically.
- **SC-004**: When AI Enhance is OFF, 100% of the user's original chat input appears verbatim in the generated Issue Template body with no AI modifications.
- **SC-005**: When a Chore is set to "Auto" pipeline, it always uses the Project's current active pipeline at execution time, even if the project's pipeline has changed since the Chore was last configured.
- **SC-006**: New Chore creation with double-confirmation and auto-merge completes the full flow (Issue creation → PR creation → merge) within 60 seconds of the user's final confirmation, assuming no merge conflicts.
- **SC-007**: Auto-merge failures are surfaced to the user within 10 seconds of the failure occurring, with a clear message describing the issue and next steps.
- **SC-008**: Users attempting to navigate away with unsaved changes are prompted 100% of the time, preventing accidental data loss.

## Assumptions

- GitHub Parent Issues are identifiable through the existing data model and can be queried with a creation timestamp filter.
- The Chore definition files are stored in a known, consistent location within the repository, and their format supports the fields described in this specification.
- The existing Chat Agent supports structured prompts that can request metadata-only generation (without body modification) for the AI Enhance OFF path.
- Saved Agent Pipeline configurations are managed elsewhere in the system and are available for selection via an existing service or data store.
- The repository's main branch allows programmatic merges (auto-merge is not blocked by branch protection rules that require manual approval beyond what the system can provide).
- The "+ Add Agent" pop-out pattern on the Agents page serves as the established UI pattern for toggle controls in creation/editing flows.
