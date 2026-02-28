# Issue Creation Contract: Description Preservation

**Feature**: 014-preserve-issue-description
**Date**: 2026-02-28

## Contract Summary

All issue creation paths MUST pass the user-provided description to the GitHub API `body` field without any truncation, summarization, or modification. The assembled body MUST be validated against the GitHub API limit (65,536 characters) before the API call, with explicit user notification on exceeding the limit.

## Endpoints Affected

### 1. POST `/api/v1/workflow/recommendations/{recommendation_id}/confirm`

**Current behavior**: Creates a GitHub Issue from an AI-generated recommendation. The body is assembled by `format_issue_body()` from structured fields.

**Required behavior**:
- Assembled body MUST preserve all user-provided content from `IssueRecommendation.original_input`/`original_context`
- Assembled body length MUST be validated ≤ 65,536 characters before API call
- If body exceeds limit: return HTTP 422 with clear error message including the current length and the limit
- If body is within limit: pass to GitHub API unchanged

**Request**: `POST /api/v1/workflow/recommendations/{recommendation_id}/confirm`
```json
{}
```

**Success Response** (200): Existing `WorkflowResult` schema — no changes.

**Error Response** (422 — body too long):
```json
{
  "error": "Issue body exceeds GitHub API limit",
  "details": "The assembled issue body is {n} characters, which exceeds the GitHub API limit of 65,536 characters. Please shorten the description and try again."
}
```

### 2. POST `/api/v1/chat/proposals/{proposal_id}/confirm`

**Current behavior**: Creates a GitHub Issue from an AI task proposal. The body is `proposal.final_description`.

**Required behavior**:
- `proposal.final_description` MUST be passed to GitHub API `body` field unchanged
- Body length MUST be validated ≤ 65,536 characters before API call
- If body exceeds limit: return HTTP 422 with clear error message
- `AITaskProposal.proposed_description` max_length updated from 65,535 to 65,536
- `ProposalConfirmRequest.edited_description` max_length updated from 65,535 to 65,536

**Request**: Existing `ProposalConfirmRequest` schema — no changes except max_length.

**Success Response** (200): Existing `AITaskProposal` schema — no changes.

**Error Response** (422 — body too long):
```json
{
  "error": "Issue body exceeds GitHub API limit",
  "details": "The issue description is {n} characters, which exceeds the GitHub API limit of 65,536 characters. Please shorten the description and try again."
}
```

## Invariants

1. **No silent truncation**: At no point in the request pipeline may any code reduce the length of a user-provided description without explicit user consent.
2. **Character-for-character fidelity**: The `body` field in the GitHub API POST request MUST be byte-identical to the assembled body string, preserving all markdown, Unicode, emoji, and whitespace.
3. **Limit validation**: All issue creation paths MUST validate the body length before calling the GitHub API.
4. **Explicit error**: If the body exceeds 65,536 characters, the API MUST return a 422 error with a human-readable message — never a silent truncation.

## Test Boundaries

Tests MUST verify description preservation at these character counts:
- 1 character (minimum)
- 256 characters
- 1,024 characters
- 4,096 characters
- 32,768 characters
- 65,536 characters (GitHub API limit — must succeed)
- 65,537 characters (1 over limit — must return 422 error)
