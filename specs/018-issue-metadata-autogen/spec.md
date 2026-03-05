# Feature Specification: Chat Agent Auto-Generate Full GitHub Issue Metadata

**Feature Branch**: `018-issue-metadata-autogen`  
**Created**: 2026-03-05  
**Status**: Draft  
**Input**: User description: "Update to ensure app chat agent generates all metadata for a GitHub Issue that would be interesting. For example, tags, priority, size, estimate, start date, target date, labels, development (parent branch). The possible values for these fields should be queried and stored in cache or sqlite for the AI chat agent to then select from when creating the description for the ticket. These fields should be sent when creating the GitHub Issue."

## Assumptions

- Priority values follow the convention P0 (critical) through P3 (low).
- Size values follow T-shirt sizing (XS, S, M, L, XL) mapped to corresponding repository labels.
- Estimates are expressed in hours (e.g., 1h, 2h, 4h, 8h, 16h).
- Dates (start date, target date) are expressed in ISO 8601 format (YYYY-MM-DD).
- The chat agent already has the ability to create basic GitHub Issues (title + body); this feature extends that existing capability.
- The metadata cache uses a configurable time-to-live (TTL) of 1 hour as the default staleness threshold.
- "Tags" as referenced in the original request is synonymous with "labels" in GitHub; the system treats these as a single concept using the GitHub labels API.
- The "development/parent branch" field refers to the branch the issue's future pull request should target or branch from.
- When the user does not override AI-generated values, the system uses the AI's selections as-is.
- Standard session-based authentication is already in place for GitHub API access.
- Assignees are auto-suggested based on available repository collaborators and can be overridden by the user before submission.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fully Populated Issue Creation (Priority: P1)

As a developer using the chat agent, I want the agent to automatically generate and populate all relevant metadata fields (priority, size, estimate, start date, target date, labels, and development branch) when creating a GitHub Issue, so that every issue I create is immediately actionable without manual post-creation edits.

**Why this priority**: This is the core value proposition of the feature. Without auto-populated metadata, issues remain incomplete and require manual follow-up, which defeats the purpose of using a chat agent for issue creation.

**Independent Test**: Can be fully tested by asking the chat agent to create a GitHub Issue and verifying that all metadata fields are present and valid in the resulting issue on GitHub.

**Acceptance Scenarios**:

1. **Given** a developer requests the chat agent to create an issue with a title and description, **When** the agent processes the request, **Then** the agent generates values for all metadata fields: priority, size, estimate, start date, target date, labels (from the repository's actual label list), assignee(s) (from the repository's collaborators), and development branch (from the repository's actual branch list).
2. **Given** the agent has generated metadata for a new issue, **When** the issue is submitted to GitHub, **Then** the GitHub API payload includes all generated metadata fields and the resulting issue on GitHub displays the correct labels, assignee(s), milestone association, and any applicable project fields.
3. **Given** the agent selects a priority of "P1" and a size of "M", **When** the issue is submitted, **Then** the labels array in the API payload contains the exact matching repository labels (e.g., "P1", "size:M") rather than free-text values.

---

### User Story 2 - Metadata Caching and Availability (Priority: P2)

As a developer, I want the system to fetch all available repository metadata (labels, branches, milestones) from GitHub and cache it locally, so that the chat agent always selects from valid, real values and I do not experience delays waiting for API calls every time I create an issue.

**Why this priority**: Caching ensures the agent can only select from valid values and provides a fast, reliable experience. Without caching, the agent could suggest non-existent labels or branches, leading to API errors and a broken workflow.

**Independent Test**: Can be tested by verifying that after an initial metadata fetch, subsequent issue creations use cached values without making additional GitHub API calls, and that cached values match what exists in the repository.

**Acceptance Scenarios**:

1. **Given** the system has never fetched metadata for a repository, **When** the chat agent is asked to create an issue for that repository, **Then** the system fetches all labels, branches, milestones, project fields, and collaborators from the GitHub API and stores them locally before proceeding with issue creation.
2. **Given** the metadata cache was populated less than the configured TTL ago, **When** the chat agent creates another issue, **Then** the system uses cached values without making new API calls.
3. **Given** the metadata cache is older than the configured TTL, **When** the chat agent is asked to create an issue, **Then** the system re-fetches metadata from GitHub, updates the cache, and indicates to the user that metadata is being refreshed.
4. **Given** the app is restarted, **When** the chat agent is asked to create an issue, **Then** the previously cached metadata is available immediately without requiring a fresh fetch from GitHub.

---

### User Story 3 - Preview and Override Before Submission (Priority: P3)

As a developer, I want to see a structured preview of all auto-generated metadata before the issue is submitted, and I want the ability to change any value I disagree with, so that I maintain control over the final issue content.

**Why this priority**: While auto-generation is the core value, allowing the user to review and override values adds a layer of confidence and correctness. This is lower priority because the AI selections should be good enough for most cases.

**Independent Test**: Can be tested by initiating an issue creation, observing the preview card with all metadata fields displayed, modifying one or more fields, and confirming the submitted issue reflects the user's overrides.

**Acceptance Scenarios**:

1. **Given** the agent has generated all metadata for a new issue, **When** the preview is displayed to the user, **Then** each metadata field (priority, size, estimate, start date, target date, labels, assignee(s), branch) is shown with its auto-generated value in a visually distinct format (e.g., badge or chip style).
2. **Given** the preview is displayed, **When** the user modifies the priority from "P2" to "P1" and removes one label, **Then** the final submission uses the user's overridden values.
3. **Given** the preview is displayed, **When** the user accepts all auto-generated values without changes, **Then** the issue is submitted with the original AI-generated metadata.

---

### User Story 4 - Graceful Degradation on API Errors (Priority: P4)

As a developer, I want the system to handle GitHub API failures gracefully by falling back to cached data and notifying me of any issues, so that I can still create issues even when the API is temporarily unavailable.

**Why this priority**: This is an important resilience concern but is secondary to core functionality. Most of the time the API will be available; this story covers the exceptional case.

**Independent Test**: Can be tested by simulating a network failure or API rate limit during metadata fetch and verifying the system falls back to cached data with appropriate user notification.

**Acceptance Scenarios**:

1. **Given** the metadata cache has expired and the GitHub API is unreachable, **When** the chat agent attempts to create an issue, **Then** the system falls back to the last successfully cached metadata values and notifies the user that cached (possibly stale) data is being used.
2. **Given** the GitHub API returns a rate-limit error during metadata refresh, **When** the system detects the error, **Then** it continues using existing cached values, displays a notification about the degraded state, and retries the refresh on the next issue creation attempt.

---

### Edge Cases

- What happens when a repository has no labels defined? The system proceeds with issue creation without labels and informs the user that no labels are available for selection.
- What happens when the AI suggests a priority or size value that has no matching label in the repository? The system maps to the closest available label, or omits the field and notifies the user if no reasonable match exists.
- What happens when the metadata cache is empty (first launch) and the GitHub API is unreachable? The system notifies the user that metadata could not be loaded and allows issue creation with only title and body (no metadata fields).
- How does the system handle repositories with hundreds of labels or branches? The system paginates through all results during the fetch and presents a searchable or filterable selection to the user during override.
- What happens when a cached branch or label is deleted from the repository between cache refreshes? The GitHub API rejects the invalid value; the system catches the error, removes the stale entry from cache, and prompts the user to select a valid alternative.
- What happens if the user creates issues across multiple repositories in the same session? The cache is keyed by repository (owner/repo) so each repository has its own independent set of cached metadata.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST fetch all available repository labels, milestones, project fields, branches, and collaborators (potential assignees) from GitHub when initializing metadata context for a repository, and store the results in a persistent local cache keyed by repository identifier.
- **FR-002**: System MUST use only cached metadata values (labels, branches, milestones, project fields, collaborators) as the selection pool when the AI chat agent generates issue metadata, ensuring no invalid or non-existent values are submitted to the GitHub API.
- **FR-003**: System MUST auto-generate values for all of the following fields for every GitHub Issue created via the chat agent: priority, size, estimate (in hours), start date, target date, labels (mapped to actual repository labels), assignee(s), and development/parent branch.
- **FR-004**: System MUST include all generated metadata fields in the GitHub Issues API creation payload, including the labels array, milestone reference, assignee(s), and any applicable project field values.
- **FR-005**: System MUST map AI-determined priority and size values to the closest matching repository label from the cached label list before submission, rather than submitting arbitrary free-text values.
- **FR-006**: System MUST invalidate and re-fetch cached metadata when the cache age exceeds a configurable TTL (default: 1 hour) or when the user explicitly requests a refresh.
- **FR-007**: System MUST persist the metadata cache so that it survives application restarts and is available immediately on the next session without requiring a fresh API fetch.
- **FR-008**: System SHOULD display a structured preview of all auto-generated metadata fields to the user before submitting the issue to GitHub.
- **FR-009**: System SHOULD allow the user to review and override any AI-generated metadata field in the chat interface before submission.
- **FR-010**: System SHOULD gracefully handle GitHub API errors (rate limits, network failures, authentication errors) during metadata fetching by falling back to previously cached values and notifying the user of the degraded state.
- **FR-011**: System SHOULD display a visual indicator (e.g., "Refreshing metadata…") when re-fetching stale cached data.
- **FR-012**: System SHOULD log each issue creation event with the full metadata payload for debugging and audit purposes.

### Key Entities

- **Metadata Cache Entry**: Represents a single cached value from GitHub (e.g., a label, branch, milestone, project field, or collaborator). Key attributes: repository identifier, field type (label, branch, milestone, project, collaborator), value, display name, and timestamp of last fetch.
- **Issue Metadata**: The complete set of auto-generated fields for a single issue. Key attributes: priority, size, estimate, start date, target date, selected labels, assignee(s), selected branch, and selected milestone.
- **Repository Context**: The association between a specific GitHub repository and its cached metadata. Key attributes: owner, repository name, last refresh timestamp, and TTL configuration.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of issues created via the chat agent include all required metadata fields (priority, size, estimate, start date, target date, at least one label, assignee(s), and a development branch) in the submitted GitHub API payload.
- **SC-002**: Users can create a fully metadata-populated issue in under 60 seconds from initial request to submission, including any preview review time.
- **SC-003**: After the initial metadata fetch, subsequent issue creations within the TTL window complete without additional GitHub API calls for metadata, reducing perceived latency by at least 50%.
- **SC-004**: When the GitHub API is unavailable, the system falls back to cached data and the user is notified within 5 seconds, allowing issue creation to proceed with previously cached values.
- **SC-005**: 100% of label and branch values submitted in the API payload correspond to values that actually exist in the target repository at the time of submission.
- **SC-006**: Users who review the metadata preview accept the auto-generated values without changes at least 80% of the time, indicating high-quality AI selections.
