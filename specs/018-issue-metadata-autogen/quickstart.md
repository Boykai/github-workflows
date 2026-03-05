# Quickstart: Chat Agent Auto-Generate Full GitHub Issue Metadata

**Feature**: 018-issue-metadata-autogen | **Date**: 2026-03-05

## Overview

This guide describes how to implement and test the metadata auto-generation feature for the chat agent's issue creation pipeline. After completing this feature, every issue created via the chat agent will include AI-selected values for priority, size, estimate, dates, labels, assignees, milestone, and development branch — all validated against real repository data.

## Prerequisites

- Docker and Docker Compose installed
- GitHub OAuth app configured (existing setup)
- Access to a GitHub repository with labels, branches, milestones, and collaborators

## Implementation Order

Follow this sequence to minimize integration risk:

### Step 1: Database Migration (backend)

Create `backend/src/migrations/011_metadata_cache.sql`:

```sql
CREATE TABLE IF NOT EXISTS github_metadata_cache (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_key    TEXT NOT NULL,
    field_type  TEXT NOT NULL,
    value       TEXT NOT NULL,
    fetched_at  TEXT NOT NULL,
    UNIQUE(repo_key, field_type, value)
);

CREATE INDEX IF NOT EXISTS idx_metadata_cache_repo_type
    ON github_metadata_cache(repo_key, field_type);
```

The existing migration runner in `database.py` will pick this up automatically on next startup.

### Step 2: MetadataService (backend)

Create `backend/src/services/metadata_service.py` with:

1. **`fetch_metadata(access_token, owner, repo)`** — Calls GitHub REST API for labels, branches, milestones, collaborators. Paginates through all results. Stores in SQLite.
2. **`get_metadata(owner, repo)`** — Returns cached metadata. Checks TTL. Returns `RepositoryMetadataContext` with `is_stale` and `source` indicators.
3. **`invalidate(owner, repo)`** — Clears cache for a specific repo.
4. **`get_or_fetch(access_token, owner, repo)`** — Combined: returns cached if fresh, fetches if stale or missing.

Key design decisions:
- Use existing `InMemoryCache` as L1 (session-duration) and SQLite as L2 (persistent)
- TTL from `Settings.metadata_cache_ttl_seconds` (default: 3600)
- Fallback to `constants.LABELS` if both caches are empty

### Step 3: Expand IssueMetadata Model (backend)

Add three fields to `IssueMetadata` in `backend/src/models/recommendation.py`:

```python
assignees: list[str] = Field(default_factory=list, description="Assigned GitHub usernames")
milestone: str | None = Field(default=None, description="Milestone title")
branch: str | None = Field(default=None, description="Development/parent branch name")
```

### Step 4: Update AI Prompt (backend)

Modify `backend/src/prompts/issue_generation.py`:

- `create_issue_generation_prompt()` accepts an optional `metadata_context: dict` parameter
- When provided, injects real labels/branches/milestones/collaborators into the system prompt
- When not provided, falls back to existing hardcoded `PREDEFINED_LABELS`
- Add instructions for the AI to select assignees, milestone, and branch from the provided lists

### Step 5: Update AI Agent Service (backend)

Modify `backend/src/services/ai_agent.py`:

- `generate_issue_recommendation()` accepts optional `metadata_context` parameter
- Passes it to `create_issue_generation_prompt()`
- `_parse_issue_metadata()` extracts new fields: `assignees`, `milestone`, `branch`

### Step 6: Expand create_issue (backend)

Modify `backend/src/services/github_projects/service.py`:

- `create_issue()` accepts optional `milestone: int | None` and `assignees: list[str] | None`
- Includes them in the REST API payload

### Step 7: Update Workflow Orchestrator (backend)

Modify `backend/src/services/workflow_orchestrator/orchestrator.py`:

- `create_issue_from_recommendation()` passes full metadata (labels from recommendation, milestone number, assignees) to `create_issue()`
- Validate metadata against cached values before submission
- Map priority/size to repo labels if matching labels exist

### Step 8: Metadata API Endpoint (backend)

Create `backend/src/api/metadata.py`:

- `GET /api/v1/metadata/{owner}/{repo}` — Returns cached metadata
- `POST /api/v1/metadata/{owner}/{repo}/refresh` — Force refresh

### Step 9: Frontend Types (frontend)

Update `frontend/src/types/index.ts`:

- Add `assignees`, `milestone`, `branch` to `IssueMetadata`
- Add `RepositoryMetadata` interface

### Step 10: useMetadata Hook (frontend)

Create `frontend/src/hooks/useMetadata.ts`:

- Fetches metadata from backend when a repository is selected
- Caches in React state
- Exposes `refresh()` function

### Step 11: Update IssueRecommendationPreview (frontend)

Modify `frontend/src/components/chat/IssueRecommendationPreview.tsx`:

- Add editable dropdowns for assignees, milestone, branch
- Add editable multi-select for labels (typeahead from metadata)
- Make priority and size fields editable (dropdowns)
- Add date pickers for start/target dates
- Show "cached" vs "fresh" indicator
- Pass overrides back to confirmation endpoint

## Testing

### Manual Testing

1. Start the app: `docker-compose up --build`
2. Authenticate with GitHub OAuth
3. Open the chat agent
4. Type a feature request (e.g., "Add dark mode support")
5. Verify the preview shows all metadata fields populated from real repo data
6. Modify a field (e.g., change priority from P2 to P1)
7. Confirm the issue
8. Check the created issue on GitHub — verify labels, assignees, milestone are set

### Cache Testing

1. Create an issue (triggers initial metadata fetch)
2. Create another issue immediately — should use cached data (no API calls in network tab)
3. Wait > TTL (or use refresh button) — should re-fetch

### Fallback Testing

1. Disconnect from network
2. Attempt to create an issue — should use cached data with "Using cached data" indicator
3. If no cache exists, should fall back to hardcoded labels

## Configuration

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| `metadata_cache_ttl_seconds` | `METADATA_CACHE_TTL_SECONDS` | `3600` | TTL for metadata cache in seconds |

## API Quick Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/metadata/{owner}/{repo}` | Get cached repo metadata |
| POST | `/api/v1/metadata/{owner}/{repo}/refresh` | Force refresh metadata |
| POST | `/api/v1/workflow/recommendations/{id}/confirm` | Confirm with optional overrides |
