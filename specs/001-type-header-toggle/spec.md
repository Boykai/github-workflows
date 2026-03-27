# Feature Specification: Chores Page Type Header Toggle for Clean Up Deletion

**Feature Branch**: `001-type-header-toggle`  
**Created**: 2026-03-27  
**Status**: Draft  
**Input**: User description: "On Chores page, the Clean Up button UX - the user should be able to select item type headers like 'branch' and 'pull request' to toggle all the branches or pull requests for deletion. 'main' branch can NEVER be deleted by the user. Disable the option."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bulk-Select All Items by Type Header (Priority: P1)

As a user on the Chores page Clean Up flow, I want to click a type header checkbox (e.g., "Branches" or "Pull Requests") to select or deselect all items under that type at once, so that I can quickly bulk-manage deletions without checking each item individually.

**Why this priority**: This is the core feature request. Without the header toggle, users must manually select each item, which is tedious for large lists. This delivers the primary value of faster bulk-selection.

**Independent Test**: Can be fully tested by opening the Chores page, triggering the Clean Up flow, and clicking a type header checkbox to verify all eligible child items toggle their selection state. Delivers value by reducing selection effort from N clicks to 1.

**Acceptance Scenarios**:

1. **Given** the Chores page Clean Up UI displays a "Branches" group with 5 eligible branches (none selected), **When** the user clicks the "Branches" type header checkbox, **Then** all 5 eligible branches become selected.
2. **Given** the "Branches" type header checkbox is fully checked (all eligible items selected), **When** the user clicks the header checkbox again, **Then** all eligible branches become deselected.
3. **Given** a "Pull Requests" group with 3 pull requests (none selected), **When** the user clicks the "Pull Requests" type header checkbox, **Then** all 3 pull requests become selected.

---

### User Story 2 - 'main' Branch Protection During Bulk Toggle (Priority: P1)

As a user on the Chores page, I need the 'main' branch to be permanently protected from deletion, so that even when I use the type header toggle to select all branches, the 'main' branch is never selected or queued for deletion.

**Why this priority**: This is a critical safety requirement. Accidentally deleting the 'main' branch would be catastrophic. This protection must be enforced unconditionally, making it equally important as the core toggle feature.

**Independent Test**: Can be tested by verifying that the 'main' branch checkbox is always disabled, clicking the "Branches" header toggle, and confirming 'main' remains unselected. Delivers value by preventing accidental deletion of the primary branch.

**Acceptance Scenarios**:

1. **Given** the Clean Up UI displays a "Branches" group containing the 'main' branch, **When** the UI renders, **Then** the 'main' branch row displays a disabled, non-interactive checkbox that cannot be clicked.
2. **Given** the "Branches" group contains 'main' and 4 other branches (none selected), **When** the user clicks the "Branches" type header checkbox, **Then** only the 4 non-protected branches become selected and the 'main' branch remains unselected.
3. **Given** all eligible branches are selected via the header toggle, **When** the user confirms the Clean Up deletion action, **Then** the deletion request includes only the eligible branches and never includes 'main'.
4. **Given** the 'main' branch row is visible, **When** the user hovers over or focuses on the disabled 'main' checkbox, **Then** a visual indicator (tooltip or label) explains that this branch cannot be deleted.

---

### User Story 3 - Indeterminate Header State for Partial Selections (Priority: P2)

As a user on the Chores page, I want the type header checkbox to visually reflect whether all, some, or no items under it are selected, so that I can quickly understand the current selection state at a glance.

**Why this priority**: While not essential for functionality, the indeterminate state is important for UX clarity. Without it, users cannot distinguish between "all selected" and "some selected" states, which could lead to confusion during the deletion flow.

**Independent Test**: Can be tested by manually selecting a subset of items within a type group and verifying the header checkbox shows an indeterminate (dash/minus) state. Delivers value by providing clear visual feedback about partial selections.

**Acceptance Scenarios**:

1. **Given** a "Branches" group with 5 eligible branches and none are selected, **When** the user views the header checkbox, **Then** it displays an unchecked state.
2. **Given** a "Branches" group with 5 eligible branches and the user manually selects 2, **When** the user views the header checkbox, **Then** it displays an indeterminate state (partially checked).
3. **Given** a "Branches" group with 5 eligible branches and all 5 are selected, **When** the user views the header checkbox, **Then** it displays a fully checked state.
4. **Given** the header checkbox is in an indeterminate state, **When** the user clicks it, **Then** all eligible items become selected (resolving the partial state to fully selected).

---

### User Story 4 - Keyboard Accessibility for Header Toggles (Priority: P3)

As a keyboard-only user, I want to be able to navigate to type header checkboxes and toggle them using Space or Enter keys, so that the bulk-selection feature is accessible without a mouse.

**Why this priority**: Accessibility is important for inclusivity and compliance but is lower priority than core functionality and safety. It enhances the feature for users who rely on keyboard navigation or assistive technology.

**Independent Test**: Can be tested by tabbing to a type header checkbox and pressing Space or Enter to verify it toggles all eligible items. Delivers value by ensuring the feature meets accessibility standards.

**Acceptance Scenarios**:

1. **Given** the Clean Up UI is displayed, **When** the user navigates using the Tab key, **Then** type header checkboxes are focusable and reachable in the tab order.
2. **Given** a type header checkbox has focus, **When** the user presses Space or Enter, **Then** all eligible child items under that type toggle their selected state.
3. **Given** a type header checkbox has focus and is in an indeterminate state, **When** a screen reader reads it, **Then** the screen reader announces the mixed/indeterminate state appropriately.

---

### Edge Cases

- What happens when a type group contains only the 'main' branch and no other branches? The header checkbox should remain in a permanently unchecked and effectively disabled state since there are no eligible items to toggle.
- What happens when a type group has zero items? The type header should not be rendered, or should be rendered in a disabled state with no toggle functionality.
- What happens when the user selects items individually, then clicks the header toggle? The header toggle should select all remaining unselected eligible items (or deselect all if already fully selected).
- How does the system handle the case where 'main' is the only unselected item? The header checkbox should display a fully checked state since all eligible items are selected, even though 'main' remains unselected.
- What happens if the user tries to submit a deletion with no items selected? The confirmation/execution action should be disabled or display a prompt indicating no items are selected.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST render each item type group (e.g., "Branches", "Pull Requests") on the Chores page Clean Up UI with a clickable header row containing a checkbox control.
- **FR-002**: System MUST toggle the selected state of ALL eligible child items within a group when the user clicks the corresponding type header checkbox.
- **FR-003**: System MUST display the type header checkbox in an indeterminate state when only a subset of its eligible child items are selected.
- **FR-004**: System MUST display the type header checkbox in a fully checked state when all eligible child items are selected, and unchecked when none are selected.
- **FR-005**: System MUST permanently disable the deletion checkbox for the 'main' branch — it MUST be rendered in a disabled, non-interactive state at all times and cannot be selected individually or via header toggle.
- **FR-006**: System MUST exclude the 'main' branch from any bulk-select or toggle-all operation triggered by the "Branches" type header, ensuring it is never queued for deletion.
- **FR-007**: System MUST display a visual indicator (e.g., tooltip, muted label, or lock icon) on the 'main' branch row explaining why it cannot be selected for deletion.
- **FR-008**: System MUST ensure the Clean Up confirmation and execution action only processes items that are explicitly checked and eligible (never includes 'main' branch).
- **FR-009**: System MUST derive the header checkbox state (checked, indeterminate, unchecked) purely from the child items' selection state rather than storing it independently, to prevent synchronization bugs.
- **FR-010**: System MUST support keyboard interaction (Space and Enter) on type header rows for toggling selection.
- **FR-011**: System MUST apply appropriate ARIA attributes including `aria-checked` with `mixed` value for indeterminate state and `aria-disabled` for the 'main' branch row to support screen reader users.
- **FR-012**: When the header checkbox is clicked while in an indeterminate state, the system MUST select all eligible (unselected) items in the group, resolving the partial state to fully selected.
- **FR-013**: When a type group contains only protected items (e.g., only the 'main' branch), the header checkbox MUST be rendered in a disabled state with no toggle functionality.
- **FR-014**: System MUST validate on the server side that the 'main' branch is never included in a deletion request, regardless of what the client sends.

### Key Entities

- **Type Group**: A logical grouping of deletable items by their category (e.g., "Branches", "Pull Requests"). Contains a header row and zero or more child items.
- **Type Header**: The clickable header row for a type group. Displays the group name, item count, and a checkbox that controls bulk selection of all eligible child items.
- **Deletable Item**: An individual item within a type group that can be selected for deletion (e.g., a specific branch or pull request). Has a name, selection state, and eligibility status.
- **Protected Item**: A special deletable item that is permanently excluded from selection and deletion. The 'main' branch is the primary protected item. Protected items are visually distinct and functionally disabled.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can select or deselect all eligible items within a type group in a single click, reducing bulk-selection time by at least 80% compared to selecting items individually.
- **SC-002**: The 'main' branch is never included in any deletion operation — verified across all user interaction paths (individual click, header toggle, keyboard toggle, and direct submission).
- **SC-003**: Users can visually distinguish between unchecked, partially checked (indeterminate), and fully checked states on every type header checkbox without ambiguity.
- **SC-004**: Keyboard-only users can navigate to and operate all type header checkboxes using Tab, Space, and Enter keys with screen reader announcements for all three checkbox states.
- **SC-005**: The Clean Up confirmation action correctly reflects only eligible, explicitly selected items — zero false inclusions of protected items across all test scenarios.
- **SC-006**: Users viewing the 'main' branch row can immediately understand why it cannot be deleted, without needing to consult external documentation.

## Assumptions

- The Chores page Clean Up UI already renders items grouped by type (e.g., branches, pull requests). This feature adds the header toggle control to existing groups.
- The 'main' branch is the only protected branch. If additional protected branches are needed in the future, the protection mechanism should be extensible but for now only 'main' is protected.
- The existing deletion API processes a list of items for deletion. Server-side validation will add a check to reject 'main' from that list.
- Item type groups with no items (empty groups) are either not rendered or rendered in a non-interactive state, consistent with existing Chores page behavior.
- The indeterminate checkbox state follows the standard HTML checkbox `indeterminate` property pattern, which is widely supported across browsers.
- Standard web accessibility patterns (WAI-ARIA checkbox specification) are sufficient for screen reader support — no custom screen reader integration is required.
