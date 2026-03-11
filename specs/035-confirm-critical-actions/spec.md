# Feature Specification: Add Confirmation Step to Critical Actions

**Feature Branch**: `035-confirm-critical-actions`  
**Created**: 2026-03-11  
**Status**: Draft  
**Input**: User description: "Implement a confirmation mechanism for critical or irreversible actions to prevent accidental execution. This ensures users are prompted to explicitly verify their intent before the system proceeds."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Confirmation Before Destructive Deletion (Priority: P1)

A user managing their project accidentally clicks "Delete" on an agent, chore, pipeline, or tool. Before the system carries out the deletion, a confirmation prompt appears describing exactly what will be destroyed and that the action cannot be undone. The user reads the message, decides they clicked by mistake, and cancels. The system returns to its previous state with no data lost. Alternatively, the user confirms and the deletion proceeds as expected.

**Why this priority**: Deletions are the most irreversible actions in the system. An accidental deletion can destroy configuration, history, and active work. Preventing unintended deletions provides the highest safety value.

**Independent Test**: Can be tested by triggering a delete action on any entity (agent, chore, pipeline, tool) and verifying that a confirmation prompt appears before execution, and that canceling leaves the entity unchanged.

**Acceptance Scenarios**:

1. **Given** a user viewing an entity (agent, chore, pipeline, or tool), **When** the user clicks a delete button, **Then** a confirmation prompt appears before any deletion occurs.
2. **Given** a confirmation prompt is displayed for a delete action, **When** the user cancels the prompt, **Then** the entity remains unchanged and the application returns to its prior state.
3. **Given** a confirmation prompt is displayed for a delete action, **When** the user confirms, **Then** the deletion proceeds and the user sees appropriate feedback (success or error).
4. **Given** a confirmation prompt for deleting a tool that is in use by active agents, **When** the prompt is displayed, **Then** the message explicitly lists the affected agents so the user can make an informed decision.

---

### User Story 2 - Clear and Contextual Confirmation Messaging (Priority: P1)

A user encounters a confirmation prompt and immediately understands what action they are about to take and what the consequences will be. The prompt title names the specific action (e.g., "Delete Agent"), the body describes what will happen and any downstream effects, and the confirm button uses an action-specific label (e.g., "Yes, Delete Agent") rather than a generic "OK". This clarity prevents users from blindly confirming without reading.

**Why this priority**: A confirmation prompt that is vague or generic defeats its purpose — users will click through it reflexively. Clear, contextual messaging is essential for confirmations to actually prevent accidents.

**Independent Test**: Can be tested by triggering each type of critical action and verifying the prompt title, body text, and button labels are specific to the action being confirmed.

**Acceptance Scenarios**:

1. **Given** any critical action triggers a confirmation prompt, **When** the prompt appears, **Then** the title clearly names the action (e.g., "Delete Pipeline", "Clean Up Repository").
2. **Given** any confirmation prompt, **When** the user reads the body text, **Then** it describes the consequences of proceeding (e.g., "This will permanently remove the agent and open a pull request to delete its configuration files. This cannot be undone.").
3. **Given** any confirmation prompt, **When** the user views the action buttons, **Then** the confirm button uses an action-specific label (e.g., "Yes, Delete", "Proceed with Cleanup") and the cancel button is clearly labeled.
4. **Given** a confirmation for an action with downstream effects (e.g., deleting a tool used by agents), **When** the prompt appears, **Then** the body lists all affected resources.

---

### User Story 3 - Accessible Confirmation Experience (Priority: P1)

A user who relies on keyboard navigation or a screen reader encounters a confirmation prompt. They can navigate to the cancel and confirm buttons using the Tab key, dismiss the prompt with the Escape key, and hear the prompt content read aloud by their screen reader. The prompt traps focus so the user cannot accidentally interact with the background, and focus is returned to the triggering element when the prompt is dismissed.

**Why this priority**: Accessibility is a fundamental requirement, not an enhancement. Confirmation prompts that are inaccessible create a barrier for users with disabilities and may violate accessibility standards.

**Independent Test**: Can be tested by triggering a confirmation prompt using only the keyboard and verifying focus management, keyboard navigation, and screen reader announcements.

**Acceptance Scenarios**:

1. **Given** a confirmation prompt is displayed, **When** the user presses Tab, **Then** focus cycles between the cancel and confirm buttons (focus is trapped within the prompt).
2. **Given** a confirmation prompt is displayed, **When** the user presses Escape, **Then** the prompt is dismissed and the action is canceled.
3. **Given** a confirmation prompt is displayed, **When** a screen reader encounters the prompt, **Then** the prompt title and body text are announced automatically.
4. **Given** a confirmation prompt is dismissed (via cancel, confirm, or Escape), **When** the prompt closes, **Then** focus returns to the element that triggered the prompt.
5. **Given** a confirmation prompt is displayed, **When** the user attempts to interact with elements behind the prompt, **Then** those interactions are blocked by a backdrop overlay.

---

### User Story 4 - Protection Against Rapid or Duplicate Submissions (Priority: P2)

A user clicks the confirm button on a confirmation prompt, but the action takes a moment to complete (e.g., a network request). The user impatiently clicks confirm again, or double-clicks. The system processes the action exactly once, showing a loading state on the confirm button to indicate the action is in progress. If the action fails, the error is displayed within the prompt and the user can retry or cancel.

**Why this priority**: Double-submissions can cause duplicate side effects (e.g., multiple deletion requests, duplicate pull requests). This is a common usability issue that must be handled but is secondary to ensuring confirmations exist and are clear.

**Independent Test**: Can be tested by triggering a confirmation, clicking the confirm button rapidly multiple times, and verifying the action executes only once and the button shows a loading state.

**Acceptance Scenarios**:

1. **Given** a user clicks the confirm button on a confirmation prompt, **When** the action is processing, **Then** the confirm button shows a loading indicator and becomes non-interactive.
2. **Given** a user rapidly clicks the confirm button multiple times, **When** the first click initiates the action, **Then** subsequent clicks are ignored and the action executes exactly once.
3. **Given** the confirmed action fails (e.g., network error), **When** the error occurs, **Then** the error message is displayed within the prompt and the user can retry or cancel.
4. **Given** a confirmation prompt is in a loading state, **When** the user presses Escape or clicks cancel, **Then** the dismiss action is blocked until the in-progress action completes or fails.

---

### User Story 5 - Unsaved Changes Warning Before Navigation (Priority: P2)

A user is editing a pipeline configuration or agent settings and has unsaved changes. They attempt to navigate away (e.g., clicking a different page link or the browser back button). A warning prompt appears informing them that they have unsaved changes and offering options to save, discard, or cancel the navigation. If they cancel, they remain on the current page with their edits intact.

**Why this priority**: Losing unsaved work is frustrating and can waste significant user effort. While not as severe as a deletion, it is a common source of user dissatisfaction.

**Independent Test**: Can be tested by making edits to a pipeline or agent configuration, attempting to navigate away, and verifying the warning prompt appears with save/discard/cancel options.

**Acceptance Scenarios**:

1. **Given** a user has unsaved changes in a configuration editor, **When** they attempt to navigate away, **Then** a warning prompt appears informing them of unsaved changes.
2. **Given** the unsaved changes warning is displayed, **When** the user chooses to save, **Then** changes are saved and navigation proceeds.
3. **Given** the unsaved changes warning is displayed, **When** the user chooses to discard, **Then** changes are discarded and navigation proceeds.
4. **Given** the unsaved changes warning is displayed, **When** the user chooses to cancel, **Then** they remain on the current page with their edits intact.

---

### User Story 6 - Repository Cleanup Confirmation with Impact Summary (Priority: P3)

A user initiates a repository cleanup operation. Before executing, the system performs a preflight check to determine what will be affected (e.g., stale branches, closed issues, orphaned files). A detailed confirmation prompt presents the impact summary — listing exactly what will be removed or modified — so the user can review before proceeding.

**Why this priority**: Repository cleanup affects multiple resources simultaneously and is a bulk operation. While important, it is less frequently performed than individual deletions.

**Independent Test**: Can be tested by initiating a repository cleanup, verifying the preflight check runs, and confirming the impact summary is displayed before execution.

**Acceptance Scenarios**:

1. **Given** a user initiates a repository cleanup, **When** the preflight check completes, **Then** a confirmation prompt displays a detailed summary of what will be affected.
2. **Given** the cleanup confirmation displays an impact summary, **When** the user reviews the summary, **Then** the list clearly categorizes items by type (branches, issues, files) with counts.
3. **Given** the user cancels the cleanup confirmation, **When** the prompt closes, **Then** no cleanup actions are performed and the repository is unchanged.

---

### Edge Cases

- What happens when a user triggers a delete action while another confirmation prompt is already open? The system queues the second confirmation and presents it after the first is resolved, preventing overlapping prompts.
- What happens when the user's session expires while a confirmation prompt is displayed? The subsequent action (confirm or cancel) encounters an authentication error and displays an appropriate error message within the prompt.
- What happens when the entity being deleted is modified by another user between the prompt appearing and the user confirming? The deletion proceeds against the current state of the entity; the confirmation prompt does not guarantee a snapshot.
- How does the system handle a browser refresh while a confirmation prompt is open? The prompt is dismissed and the action is not executed (safe default).
- What happens if a confirmation action triggers a secondary confirmation (e.g., deleting a tool shows affected agents, then asks for final confirmation)? Multi-step confirmations are supported, with each step clearly indicating progress (e.g., "Step 1 of 2").

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display a confirmation prompt before executing any destructive action, including: deleting an agent, deleting a chore, deleting a pipeline, deleting a tool, deleting a repository MCP server, and performing repository cleanup.
- **FR-002**: System MUST ensure that canceling any confirmation prompt leaves the application state completely unchanged — no data is modified, no side effects occur.
- **FR-003**: System MUST provide contextual messaging in every confirmation prompt, including: a title that names the specific action, a body that describes consequences, and an action-specific confirm button label.
- **FR-004**: System MUST support a danger variant for irreversible actions (deletions, destructive operations) with visually distinct styling to signal severity.
- **FR-005**: System MUST support a warning variant for significant but reversible actions (e.g., discarding unsaved changes) with a visually distinct style.
- **FR-006**: System MUST trap keyboard focus within the confirmation prompt, cycle focus between interactive elements with Tab, and dismiss the prompt on Escape key press.
- **FR-007**: System MUST return focus to the triggering element when a confirmation prompt is dismissed.
- **FR-008**: System MUST block interaction with background content while a confirmation prompt is displayed (modal backdrop).
- **FR-009**: System MUST announce confirmation prompt content to screen readers when the prompt appears, using appropriate roles and labels.
- **FR-010**: System MUST prevent duplicate action execution by disabling the confirm button and showing a loading indicator while the confirmed action is in progress.
- **FR-011**: System MUST display errors within the confirmation prompt if the confirmed action fails, allowing the user to retry or cancel.
- **FR-012**: System MUST handle confirmation prompt queuing — if a second critical action is triggered while a prompt is already open, the second is queued and presented after the first is resolved.
- **FR-013**: System MUST warn users about unsaved changes when they attempt to navigate away from an editor with modifications, offering save, discard, and cancel options.
- **FR-014**: System MUST support multi-step confirmations for actions that require a preflight check (e.g., tool deletion that checks for affected agents, repository cleanup with impact summary).
- **FR-015**: System MUST ensure all confirmation prompts are visually consistent — using the same layout, typography, button placement, and interaction patterns across the application.

### Key Entities

- **Confirmation Prompt**: A modal dialog that intercepts a critical action, presents the action description and consequences to the user, and requires explicit confirmation or cancellation before proceeding.
- **Confirmation Variant**: A visual classification of the prompt's severity level — danger (red, for irreversible actions), warning (amber, for significant actions), or info (blue, for informational confirmations).
- **Critical Action**: Any user-initiated operation that is destructive, irreversible, or has significant consequences — including deletions, bulk operations, and discarding unsaved work.
- **Preflight Check**: An optional validation step that runs before displaying a confirmation prompt, gathering information about the impact of the action (e.g., listing affected resources) to present in the confirmation message.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of identified critical actions (deletions, cleanup, tool removal) display a confirmation prompt before execution — no destructive action can be performed with a single click.
- **SC-002**: Users can cancel any confirmation prompt and return to the prior application state with zero data loss or side effects.
- **SC-003**: All confirmation prompts are fully keyboard-navigable — users can trigger, navigate, confirm, cancel, and dismiss prompts using only the keyboard.
- **SC-004**: Confirmation messaging accurately describes the action and its consequences for every critical action — verified by reviewing each prompt's title, body, and button labels.
- **SC-005**: Rapid or repeated clicks on the confirm button result in exactly one execution of the action, with no duplicate side effects.
- **SC-006**: Users with unsaved changes are warned before navigation — no unsaved work is silently lost.
- **SC-007**: 95% of users can correctly identify what action they are confirming from the prompt messaging alone (without additional context).
- **SC-008**: Confirmation prompts meet accessibility standards — focus trapping, screen reader announcements, Escape key dismissal, and focus restoration all function correctly.

### Assumptions

- The application already has a foundation for confirmation dialogs that can be extended and standardized across all critical actions.
- All critical actions are initiated from the frontend UI — there are no backend-only destructive operations that bypass the user interface.
- The current set of critical actions (agent deletion, chore deletion, pipeline deletion, tool deletion, MCP server deletion, repository cleanup, unsaved changes) represents the complete list; new critical actions added in the future will follow the same confirmation pattern.
- Confirmation prompts are client-side only and do not require backend changes — the backend already supports the operations, and the frontend gates them with user confirmation.
- Standard web accessibility guidelines (WCAG 2.1 AA) apply to all confirmation prompts.
- Multi-step confirmations (preflight + confirm) are needed only for operations where the impact cannot be determined without a server-side check.

### Dependencies

- Existing confirmation infrastructure (confirmation hook and dialog component) that provides the baseline for this feature.
- Existing unsaved changes detection and warning mechanism in the pipeline and agent editors.
- Existing preflight check mechanism for repository cleanup operations.
- Existing tool deletion flow that checks for affected agents before confirming.

### Scope Boundaries

**In scope:**

- Ensuring all identified critical actions have confirmation prompts
- Standardizing confirmation messaging (titles, descriptions, button labels) across all prompts
- Ensuring all confirmation prompts meet accessibility requirements (keyboard navigation, screen reader support, focus management)
- Handling edge cases: double-clicks, rapid submissions, queued confirmations, error display within prompts
- Unsaved changes warnings for configuration editors
- Multi-step confirmation flows for preflight-dependent actions
- Visual consistency across all confirmation prompt variants

**Out of scope:**

- Adding new destructive actions to the application (this feature covers confirmation for existing actions)
- Backend-side confirmation or idempotency mechanisms (frontend is the confirmation layer)
- Undo/redo functionality as an alternative to confirmation (deferred to a future iteration)
- Confirmation for non-destructive actions (e.g., creating a new entity, saving changes)
- Custom confirmation prompt themes or per-user confirmation preferences
- Batch/bulk deletion operations (individual entity confirmations only for this iteration)
