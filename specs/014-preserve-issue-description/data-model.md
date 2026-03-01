# Data Model: Preserve Full User-Provided GitHub Issue Description Without Truncation

**Feature**: 014-preserve-issue-description
**Date**: 2026-02-28

## Entities

### Issue Description (Conceptual — no new model required)

The user-provided issue description is not a standalone entity in the data model. After initial request sanitization and validation, it flows through existing entities as an **immutable string** from input to API delivery.

| Stage | Entity | Field(s) | Max Length | Mutable? |
|-------|--------|----------|------------|----------|
| Input | `ChatMessageRequest` | `content` | 100,000 chars (post-sanitization cap) | No |
| AI Processing | `IssueRecommendation` | `original_input`, `original_context` | Unbounded (limited only by upstream input) | No |
| AI-Generated Fields | `IssueRecommendation` | `user_story`, `ui_ux_description`, `functional_requirements`, `technical_notes` | Unbounded (limited only by upstream input) | No |
| Task Proposal | `AITaskProposal` | `proposed_description` | 65,536 chars | No (until edited) |
| User Edit | `ProposalConfirmRequest` | `edited_description` | 65,536 chars | One-time |
| Assembled Body | `format_issue_body()` return value | N/A (local string) | 65,536 chars (validated) | No |
| GitHub API | REST POST payload | `body` | 65,536 chars (GitHub limit) | No |

**Note:** `ChatMessageRequest.content` is normalized by `sanitize_content()` at the API boundary (e.g., `.strip()`, removal of null bytes, and collapsing runs of 4+ consecutive newlines) and constrained by `max_length=100000`. The guarantees in this spec about "verbatim" preservation and immutability apply to this sanitized value; no additional truncation or mutation is allowed afterward.

### Validation Rules

1. **`AITaskProposal.proposed_description`**: `max_length=65536` (Pydantic field constraint). Currently 65535 — must be corrected to 65536.
2. **`ProposalConfirmRequest.edited_description`**: `max_length=65536` (Pydantic field constraint). Currently 65535 — must be corrected to 65536.
3. **Assembled body**: Must be validated before API call. If `len(body) > 65536`, return an explicit error (HTTP 422) to the user with a descriptive message.
4. **No truncation**: At no point in the pipeline may any code silently reduce the length of a user-provided description field.

### State Transitions

The description does not have state transitions — it is immutable. The *recommendation* containing the description has the following states:

```
PENDING → CONFIRMED (on user confirmation)
PENDING → REJECTED  (on user rejection)
```

The *proposal* containing the description has:

```
PENDING → CONFIRMED (on user confirmation without edits)
PENDING → EDITED    (on user confirmation with edits)
PENDING → CANCELLED (on expiration)
```

### Relationships

```
ChatMessageRequest.content
    ↓ (preserved as)
IssueRecommendation.original_input / .original_context
    ↓ (assembled by)
format_issue_body() → combined markdown string
    ↓ (validated ≤ 65,536 chars)
github_projects_service.create_issue(body=...)
    ↓ (sent to)
GitHub REST API POST /repos/{owner}/{repo}/issues { "body": ... }
```

## Key Changes from Current Model

| Change | Current | Proposed | Rationale |
|--------|---------|----------|-----------|
| `AITaskProposal.proposed_description` max_length | 65535 | 65536 | Match GitHub API limit exactly (off-by-one fix) |
| `ProposalConfirmRequest.edited_description` max_length | 65535 | 65536 | Match GitHub API limit exactly (off-by-one fix) |
| Body length validation | None | Pre-API check with user notification | FR-006: explicit notification if limit exceeded |
| Body length constant | Not defined | `GITHUB_ISSUE_BODY_MAX_LENGTH = 65_536` | DRY: single source of truth for the limit |
