# Feature Specification: Add 'Clean Up' Button to Delete Stale Branches and PRs

**Feature Branch**: `015-stale-cleanup-button`  
**Created**: 2026-03-01  
**Status**: Draft  
**Input**: User description: "Add 'Clean Up' Button to Delete Stale Branches and PRs (Preserving Open Issue-Linked Items)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review and Confirm Deletion Candidates (Priority: P1)

A project maintainer clicks the 'Clean Up' button and the system fetches all branches and pull requests, cross-references them against open issues on the project board, and presents a confirmation modal. The modal clearly lists which branches and PRs will be deleted and which will be preserved (including the reason for preservation). The maintainer reviews the lists and either confirms or cancels the operation.

**Why this priority**: This is the critical safety gate for the entire feature. Without an accurate preflight check and clear confirmation step, the maintainer risks losing work-in-progress branches. The confirmation modal is the foundation that all other functionality depends on.

**Independent Test**: Can be fully tested by clicking the 'Clean Up' button on a repository with a mix of stale branches, active branches linked to open issues, and the main branch, then verifying the modal correctly categorizes every item.

**Acceptance Scenarios**:

1. **Given** a repository with branches linked to open issues and branches not linked to any open issue, **When** the maintainer clicks 'Clean Up', **Then** the confirmation modal displays two lists: items scheduled for deletion and items that will be preserved, each with a reason.
2. **Given** the main branch exists, **When** the confirmation modal is displayed, **Then** the main branch always appears in the preserved list and never in the deletion list.
3. **Given** a branch is linked to an open issue on the project board, **When** the confirmation modal is displayed, **Then** that branch appears in the preserved list with its linked issue reference shown.
4. **Given** a pull request references an open issue on the project board, **When** the confirmation modal is displayed, **Then** that pull request appears in the preserved list.
5. **Given** the maintainer reviews the confirmation modal, **When** the maintainer clicks 'Cancel', **Then** no deletions occur and the modal closes.

---

### User Story 2 - Execute Clean-Up Operation (Priority: P1)

After reviewing and confirming the deletion list, the maintainer proceeds with the clean-up. The system deletes all confirmed branches and closes all confirmed pull requests sequentially, displays a progress indicator during the operation, and presents a summary report upon completion showing how many items were deleted versus preserved.

**Why this priority**: This is the core destructive operation. It must be reliable, sequential to respect rate limits, and must provide clear feedback so the maintainer knows exactly what happened.

**Independent Test**: Can be tested by confirming the deletion on a repository with known stale branches and PRs, then verifying each targeted item is deleted/closed and the summary report matches expectations.

**Acceptance Scenarios**:

1. **Given** the maintainer confirms deletion in the modal, **When** the clean-up executes, **Then** a progress indicator is visible showing the current operation status.
2. **Given** 5 branches and 3 PRs are scheduled for deletion, **When** the clean-up completes, **Then** a summary report shows "5 branches deleted, 3 PRs closed, N items preserved".
3. **Given** the clean-up completes successfully, **When** the summary report is displayed, **Then** the maintainer can see the detailed list of every deleted and preserved item.
4. **Given** the main branch, **When** the clean-up executes, **Then** the main branch is never deleted regardless of any error or unexpected state.

---

### User Story 3 - Discover the Clean-Up Feature (Priority: P2)

A project maintainer sees a 'Clean Up' button in the interface with a descriptive tooltip. Before clicking, they hover over the button and read a tooltip explaining what the operation does — that it removes stale branches and PRs while preserving main and items linked to open issues. This helps the maintainer understand the impact before initiating the process.

**Why this priority**: Discoverability and informed consent are important for a destructive operation. The tooltip prevents accidental clicks and ensures maintainers understand the scope before starting.

**Independent Test**: Can be tested by hovering over the 'Clean Up' button and verifying the tooltip text accurately describes the operation.

**Acceptance Scenarios**:

1. **Given** the maintainer views the interface, **When** the 'Clean Up' button is rendered, **Then** the button has a descriptive tooltip explaining the operation.
2. **Given** the maintainer hovers over the button, **When** the tooltip appears, **Then** it explains that the operation removes stale branches and PRs while preserving main and items linked to open issues on the project board.

---

### User Story 4 - Handle Errors Gracefully During Clean-Up (Priority: P2)

During the clean-up operation, one or more deletions fail due to permission errors, rate limits, or network issues. The system surfaces actionable error messages for each failure, continues processing remaining items where possible, and includes the errors in the final summary report. No failures are silently ignored.

**Why this priority**: Errors during batch destructive operations must be transparent. Silent failures lead to confusion about the repository state. Graceful error handling builds trust in the tool.

**Independent Test**: Can be tested by simulating a permission error on one branch deletion and verifying the system reports the error, continues with remaining deletions, and includes the failure in the summary.

**Acceptance Scenarios**:

1. **Given** a deletion fails due to insufficient permissions, **When** the error occurs, **Then** the system displays an actionable error message identifying the failed item and the reason.
2. **Given** a rate limit is hit during clean-up, **When** the system encounters the limit, **Then** it surfaces a message about the rate limit and either retries or reports the remaining items as not processed.
3. **Given** some deletions succeed and some fail, **When** the summary report is shown, **Then** it clearly distinguishes successful deletions, failed deletions (with reasons), and preserved items.

---

### User Story 5 - Permission Verification Before Clean-Up (Priority: P2)

A maintainer clicks the 'Clean Up' button but does not have the necessary permissions to delete branches or close PRs. The system detects the missing permissions before attempting any deletions and displays a clear error explaining which permissions are required.

**Why this priority**: Failing fast with a clear permission error is better than attempting operations that will all fail individually. This saves time and avoids confusing partial-failure states.

**Independent Test**: Can be tested by authenticating as a user without delete permissions, clicking 'Clean Up', and verifying a permission error is shown before any deletions are attempted.

**Acceptance Scenarios**:

1. **Given** the authenticated user lacks delete permissions, **When** they click 'Clean Up', **Then** a clear error message is shown explaining which permissions are required.
2. **Given** the authenticated user has the required permissions, **When** they click 'Clean Up', **Then** the system proceeds to the preflight fetch and confirmation modal without permission errors.

---

### User Story 6 - Audit Trail of Clean-Up Operations (Priority: P3)

After a clean-up operation completes, the maintainer can review a detailed audit trail listing every item that was deleted or preserved, including timestamps and reasons. This trail is available for review after the operation summary is dismissed.

**Why this priority**: Audit trails are valuable for accountability and troubleshooting but are not blocking for the core clean-up functionality. They enhance the feature's usability for teams that need traceability.

**Independent Test**: Can be tested by performing a clean-up, dismissing the summary, and then accessing the audit trail to verify all actions are logged with correct details.

**Acceptance Scenarios**:

1. **Given** a clean-up operation has completed, **When** the maintainer reviews the audit trail, **Then** each deleted item shows what was deleted and when.
2. **Given** a clean-up operation preserved items, **When** the maintainer reviews the audit trail, **Then** each preserved item shows the reason for preservation (e.g., linked to issue #42, is main branch).

---

### Edge Cases

- What happens when the repository has no branches other than main? The confirmation modal should indicate there are no items to clean up and the 'Confirm' action should be disabled or hidden.
- What happens when there are no open issues on the project board? All branches (except main) and all PRs should appear in the deletion list since no issue-linking criteria exist to preserve them.
- What happens when a branch is linked to a closed issue? The branch should be treated as a deletion candidate since only open issues on the project board qualify for preservation.
- What happens when a PR references an issue that is open but not on the project board? The PR should be treated as a deletion candidate, since the preservation criteria require the issue to be on the associated project board.
- What happens when a branch name follows the naming convention (e.g., `issue-42`) but the referenced issue does not exist? The branch should be treated as a deletion candidate.
- What happens when a network error occurs during the preflight fetch? The system should display an error message and not open the confirmation modal, leaving the repository unchanged.
- What happens when the repository has hundreds of branches? The system should paginate through all branches during the preflight fetch and handle the volume without timeout or truncation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST render a 'Clean Up' button with a descriptive tooltip that explains the operation removes stale branches and PRs while preserving main and items linked to open issues on the project board.
- **FR-002**: System MUST perform a preflight fetch when the 'Clean Up' button is clicked, querying all branches, all open PRs, and all open issues on the linked project board before displaying the confirmation modal.
- **FR-003**: System MUST display a confirmation modal listing all branches and PRs scheduled for deletion alongside all items that will be preserved, with preservation reasons shown for each preserved item.
- **FR-004**: System MUST preserve the main branch unconditionally and never include it in the deletion candidates under any circumstance.
- **FR-005**: System MUST preserve any branch that is linked to an open issue on the associated project board, using cross-referencing via branch naming conventions, PR body references, and issue timeline events.
- **FR-006**: System MUST preserve any pull request whose associated branch or referenced issue is an open issue on the associated project board.
- **FR-007**: System MUST delete all branches not meeting preservation criteria when the maintainer confirms the clean-up operation.
- **FR-008**: System MUST close all pull requests not meeting preservation criteria when the maintainer confirms the clean-up operation.
- **FR-009**: System MUST display a progress indicator during the clean-up operation showing the current status of deletions.
- **FR-010**: System MUST display a post-operation summary report showing the count and list of deleted items versus preserved items.
- **FR-011**: System MUST verify the authenticated user has sufficient permissions to delete branches and close PRs before attempting any deletions, and display a clear error if permissions are lacking.
- **FR-012**: System SHOULD handle errors gracefully during the clean-up operation, surfacing actionable error messages for each failure without silently ignoring any error.
- **FR-013**: System SHOULD provide a detailed audit trail of deleted and preserved items available for review after the operation completes.
- **FR-014**: System MUST execute deletions sequentially or in controlled batches to respect rate limits and avoid bursting operations.

### Key Entities

- **Branch**: A git branch in the repository. Key attributes: name, linked issue (if any), deletion eligibility status. The main branch is always protected.
- **Pull Request**: An open pull request in the repository. Key attributes: number, title, associated branch, referenced issues, deletion eligibility status.
- **Open Issue**: An issue with open status on the associated project board. Key attributes: number, title, linked branches, linked PRs. Used as the criteria for preservation.
- **Project Board**: The GitHub project board associated with the repository. Used to determine which issues are considered "active" for preservation purposes.
- **Clean-Up Operation**: A single execution of the clean-up process. Key attributes: timestamp, initiating user, list of deleted items, list of preserved items, list of errors.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Maintainers can initiate a clean-up and receive the confirmation modal within 10 seconds for repositories with up to 200 branches.
- **SC-002**: The confirmation modal accurately categorizes 100% of branches and PRs into deletion or preservation lists with correct preservation reasons.
- **SC-003**: The main branch is preserved in 100% of clean-up operations, regardless of repository state or error conditions.
- **SC-004**: Maintainers can complete the full clean-up workflow (click button → review modal → confirm → view summary) in under 5 minutes for repositories with up to 200 branches.
- **SC-005**: The post-operation summary report correctly reflects the outcome of every attempted deletion, with zero silent failures.
- **SC-006**: When the authenticated user lacks permissions, the system displays a permission error within 3 seconds of clicking the button, before any deletion is attempted.
- **SC-007**: 95% of maintainers can understand the tooltip and confirmation modal content on first read without needing external documentation.
- **SC-008**: The audit trail captures every deletion and preservation event with sufficient detail for a reviewer to understand what happened and why.

## Assumptions

- The repository has a single primary branch named "main" that serves as the protected default branch. Repositories using alternative default branch names (e.g., "master") are out of scope for the initial release.
- The associated project board is a GitHub Projects v2 board linked to the repository. Classic project boards are out of scope.
- Branch-to-issue linking is determined by a combination of: branch naming conventions (e.g., `issue-{number}`, `{number}-feature-name`), PR body references (e.g., "Closes #42"), and GitHub timeline events linking branches/PRs to issues.
- The clean-up operation is initiated by a single user and does not support concurrent clean-up operations on the same repository.
- The feature is available only to users with write access to the repository. The specific permission scopes needed are verified at runtime.
- Rate limiting is handled by sequential or batched execution of deletion requests, with standard backoff behavior for transient failures.
