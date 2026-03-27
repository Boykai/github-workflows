# Feature Specification: Chores Page — Type Header Toggle (Select All) for Clean Up Deletion

**Feature Branch**: `001-type-header-toggle`  
**Created**: 2026-03-27  
**Status**: Draft  
**Input**: User description: "On Chores page, the Clean Up button UX - the user should be able to select item type headers like 'branch' and 'pull request' to toggle all the branches or pull requests for deletion. 'main' branch can NEVER be deleted by the user. Disable the option."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Bulk-Select All Branches via Header Toggle (Priority: P1)

As a user on the Chores page Clean Up view, I want to click the "Branches" type header checkbox so that all eligible branch items beneath it are selected for deletion at once, saving me from checking each branch individually.

**Why this priority**: This is the core interaction that the feature delivers. Without the header toggle, users must manually select each item — which is the pain point the feature solves. This single story provides the primary value and can ship as a standalone improvement.

**Independent Test**: Can be fully tested by opening the Chores page, triggering Clean Up, clicking the "Branches" header checkbox, and verifying that every eligible branch row becomes checked while the 'main' branch remains unchecked and disabled.

**Acceptance Scenarios**:

1. **Given** the Clean Up view is open and displays a "Branches" group with 5 branch items (including 'main'), **When** I click the "Branches" header checkbox, **Then** the 4 eligible branches are selected and the 'main' branch remains unselected and disabled.
2. **Given** all 4 eligible branches are already selected, **When** I click the "Branches" header checkbox again, **Then** all 4 eligible branches are deselected (toggled off) and the 'main' branch remains unchanged.
3. **Given** 2 of 4 eligible branches are manually selected, **When** I click the "Branches" header checkbox, **Then** all 4 eligible branches become selected (select-all behaviour when in partial state).

---

### User Story 2 — 'main' Branch Protection (Priority: P1)

As a user on the Chores page, I need assurance that the 'main' branch can never be accidentally queued for deletion, regardless of any toggle or individual click action.

**Why this priority**: Deleting the 'main' branch is a destructive, irreversible mistake. Protecting it is a hard safety requirement that must be present from the very first release of the toggle feature.

**Independent Test**: Can be fully tested by confirming the 'main' branch checkbox is visually disabled and non-interactive, clicking the "Branches" header toggle multiple times, and verifying 'main' is never included in the deletion payload.

**Acceptance Scenarios**:

1. **Given** the Clean Up view is open and the 'main' branch is listed, **When** the view renders, **Then** the 'main' branch row displays a disabled, non-interactive checkbox with a visual indicator (e.g., tooltip or lock icon) explaining it cannot be deleted.
2. **Given** the 'main' branch row is visible, **When** I click directly on its checkbox, **Then** nothing happens — the checkbox does not toggle.
3. **Given** I have selected several branches for deletion (not including 'main'), **When** I confirm the Clean Up action, **Then** the deletion request never includes the 'main' branch.

---

### User Story 3 — Indeterminate Header Checkbox State (Priority: P2)

As a user, I want the type header checkbox to visually reflect whether all, some, or none of its child items are selected, so I can immediately understand the current selection state at a glance.

**Why this priority**: The indeterminate (partial) state is a standard UX convention that prevents user confusion. It adds significant polish but the feature is still usable (select-all / deselect-all) without it.

**Independent Test**: Can be fully tested by manually selecting a subset of items in a group and verifying the header checkbox displays the indeterminate visual indicator.

**Acceptance Scenarios**:

1. **Given** no items are selected under the "Branches" header, **When** I look at the header checkbox, **Then** it displays an unchecked state.
2. **Given** all eligible items are selected under the "Branches" header, **When** I look at the header checkbox, **Then** it displays a fully-checked state.
3. **Given** some (but not all) eligible items are selected under the "Branches" header, **When** I look at the header checkbox, **Then** it displays an indeterminate (dash/minus) state.
4. **Given** 'main' is the only branch in the group, **When** I look at the "Branches" header, **Then** the header checkbox is disabled (no eligible items to toggle).

---

### User Story 4 — Bulk-Select All Pull Requests via Header Toggle (Priority: P2)

As a user, I want to click the "Pull Requests" type header checkbox to select or deselect all pull request items for deletion, applying the same toggle pattern used for branches.

**Why this priority**: Extends the toggle pattern to a second item type. The pattern is identical to branches but without the protected-item complexity. Adds breadth but the core UX pattern is already delivered by Story 1.

**Independent Test**: Can be fully tested by opening Clean Up with pull request items, clicking the "Pull Requests" header, and verifying all pull request items toggle together.

**Acceptance Scenarios**:

1. **Given** the Clean Up view shows a "Pull Requests" group with 3 items and none are selected, **When** I click the "Pull Requests" header checkbox, **Then** all 3 items are selected.
2. **Given** all 3 pull request items are selected, **When** I click the header checkbox, **Then** all 3 are deselected.

---

### User Story 5 — Keyboard Accessibility for Header Toggles (Priority: P3)

As a keyboard-only user, I want to navigate to a type header row and press Space or Enter to toggle all items in that group, so I can use the bulk-select feature without a mouse.

**Why this priority**: Accessibility is important but extends the delivery timeline. The mouse-based toggle provides the primary value; keyboard support ensures compliance with accessibility standards and benefits power users.

**Independent Test**: Can be fully tested by tabbing to a type header checkbox and pressing Space/Enter to verify the toggle fires and focus management is correct.

**Acceptance Scenarios**:

1. **Given** the "Branches" header checkbox is focused via keyboard Tab navigation, **When** I press Space, **Then** all eligible branch items toggle their selected state.
2. **Given** the "Pull Requests" header checkbox is focused, **When** I press Enter, **Then** all pull request items toggle their selected state.
3. **Given** a screen reader is active, **When** the header checkbox is in indeterminate state, **Then** the screen reader announces the mixed selection state.

---

### Edge Cases

- What happens when a type group contains only the 'main' branch and no other branches? The header checkbox should render as disabled since there are zero eligible items to select.
- What happens when a type group has zero items (e.g., no pull requests to clean up)? The group header should not render at all, or render in a disabled/empty state with no toggle interaction.
- How does the system handle rapid repeated clicks on the header toggle? The selection state must remain consistent — the toggle should reflect the final intended state without race conditions or visual flicker.
- What happens if an item is deleted by another user while the Clean Up view is open? The system should gracefully handle stale items — either refresh the list before executing deletion or skip items that no longer exist and inform the user.
- What happens when all eligible items under a header are individually selected one by one? The header checkbox must update to the fully-checked state reactively as the last eligible item is checked.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST render each item type group (e.g., "Branches", "Pull Requests") in the Chores Clean Up UI with a clickable header row containing a checkbox control.
- **FR-002**: System MUST toggle the selected state of all eligible child items within a group when the user activates the corresponding type header checkbox.
- **FR-003**: System MUST display the type header checkbox in an indeterminate state when only a subset of its eligible child items are selected.
- **FR-004**: System MUST display the type header checkbox as fully checked when all eligible child items are selected, and unchecked when none are selected.
- **FR-005**: System MUST permanently disable the deletion checkbox for the 'main' branch — it must be rendered in a disabled, non-interactive state at all times and cannot be selected individually or via any header toggle action.
- **FR-006**: System MUST exclude the 'main' branch from any bulk-select or toggle-all operation triggered by the "Branches" type header, ensuring it is never queued for deletion.
- **FR-007**: System MUST display a visual indicator (e.g., tooltip, muted label, or lock icon) on the 'main' branch row explaining that it cannot be deleted.
- **FR-008**: System MUST ensure the Clean Up confirmation and execution action only processes items that are explicitly checked and eligible (i.e., the deletion payload must never include the 'main' branch).
- **FR-009**: System MUST derive the header checkbox state (checked, unchecked, indeterminate) from the selection state of its child items rather than storing it as an independent value.
- **FR-010**: System MUST support keyboard interaction (Space and Enter keys) on type header rows for toggling selection.
- **FR-011**: System MUST apply appropriate accessibility attributes to type header checkboxes, including support for the indeterminate state announcement and disabled state indication for protected items.
- **FR-012**: System MUST disable the type header checkbox when a group contains zero eligible items (e.g., a "Branches" group where only 'main' exists).
- **FR-013**: System MUST not render a type group header when the group contains zero total items.

### Key Entities

- **Item Type Group**: A logical grouping of deletable items by category (e.g., "Branches", "Pull Requests"). Contains a header row and zero or more child item rows. The header reflects aggregate selection state.
- **Deletable Item**: An individual item (branch, pull request, etc.) that can be selected for deletion during the Clean Up flow. Each has a name, type, and eligibility status.
- **Protected Item**: A deletable item that is permanently excluded from selection and deletion. The 'main' branch is the only currently defined protected item. Protected items are always rendered as disabled and skipped by all toggle operations.

### Assumptions

- The Clean Up view already groups items by type. This feature adds the interactive header toggle to the existing grouping.
- "Eligible" items are all items in a group except those that are protected (currently only 'main' branch).
- The toggle behaviour follows the standard select-all pattern: clicking the header when in unchecked or indeterminate state selects all eligible items; clicking when fully checked deselects all eligible items.
- The 'main' branch is identified by its exact name "main" — no other branch naming variations (e.g., "master", "develop") require protection unless explicitly configured in the future.
- Server-side validation already exists or will be added to reject deletion requests that include the 'main' branch, as a defence-in-depth measure beyond the UI protection.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can select all eligible items in a type group with a single click on the header checkbox, reducing the number of clicks from N (one per item) to 1.
- **SC-002**: The 'main' branch is never included in any deletion request, verified by 100% of Clean Up executions excluding it from the payload.
- **SC-003**: Users can distinguish between no-selection, partial-selection, and full-selection states of a type group at a glance via the header checkbox visual state.
- **SC-004**: 95% of users can successfully bulk-select and delete items on their first attempt without confusion or errors.
- **SC-005**: Keyboard-only users can toggle type group selection using Space or Enter without requiring mouse interaction.
- **SC-006**: Screen reader users can identify the current selection state of each type header (checked, unchecked, or mixed) through announced accessibility attributes.
