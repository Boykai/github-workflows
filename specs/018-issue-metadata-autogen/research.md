# Research: Chat Agent Auto-Generate Full GitHub Issue Metadata

**Feature**: 018-issue-metadata-autogen | **Date**: 2026-03-05

## R1: GitHub REST API — Labels, Branches, Milestones, Collaborators

### Decision

Use the GitHub REST API v3 for fetching repository metadata. All four endpoints are well-supported, paginated, and available with a standard OAuth token.

### Rationale

- The app already uses `httpx` with `_request_with_retry` for REST calls in `GitHubProjectsService`.
- REST endpoints return all needed fields without requiring GraphQL schema knowledge.
- Pagination is straightforward via `Link` headers and `per_page=100`.
- GraphQL would be overkill for simple list fetches and would add query complexity.

### Endpoints

| Resource | Endpoint | Key Fields |
|----------|----------|------------|
| Labels | `GET /repos/{owner}/{repo}/labels` | `name`, `color`, `description` |
| Branches | `GET /repos/{owner}/{repo}/branches` | `name`, `protected` |
| Milestones | `GET /repos/{owner}/{repo}/milestones` | `number`, `title`, `due_on`, `state` |
| Collaborators | `GET /repos/{owner}/{repo}/collaborators` | `login`, `avatar_url`, `permissions` |

### Alternatives Considered

- **GraphQL API**: More flexible but unnecessary for flat list fetches. Would add query maintenance burden.
- **Octokit.js / PyGithub**: Third-party wrapper libraries. Rejected to avoid new dependencies — `httpx` is already in use and sufficient.

---

## R2: Metadata Cache — SQLite vs. In-Memory

### Decision

Use **SQLite** for persistent metadata cache with an **in-memory L1 cache** layer for hot-path lookups.

### Rationale

- FR-007 requires cache to survive app restarts → SQLite is the only option.
- The app already has a SQLite database (`/app/data/settings.db`) with a custom migration runner.
- Adding a new table (`github_metadata_cache`) follows the existing pattern (see `migrations/001_initial_schema.sql` through `010_chores.sql`).
- The existing `InMemoryCache` (from `cache.py`) provides TTL-based eviction and can serve as an L1 cache for the current session, reducing SQLite reads.

### Schema Design

```sql
CREATE TABLE IF NOT EXISTS github_metadata_cache (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_key    TEXT NOT NULL,           -- "owner/repo"
    field_type  TEXT NOT NULL,           -- "label", "branch", "milestone", "collaborator"
    value       TEXT NOT NULL,           -- JSON-encoded field data
    fetched_at  TEXT NOT NULL,           -- ISO 8601 timestamp
    UNIQUE(repo_key, field_type, value)
);

CREATE INDEX IF NOT EXISTS idx_metadata_cache_repo_type
    ON github_metadata_cache(repo_key, field_type);
```

### Alternatives Considered

- **Pure in-memory cache**: Violates FR-007 (no restart persistence). Rejected.
- **Separate SQLite file**: Adds configuration complexity. Rejected — reusing the existing database is simpler.
- **Redis/Valkey**: Overkill for a single-user desktop app. Rejected.

---

## R3: TTL and Cache Invalidation Strategy

### Decision

Use a configurable TTL (default 1 hour) with per-field-type staleness checks. Stale entries are refreshed lazily on next access, not eagerly via background task.

### Rationale

- The existing `cache_ttl_seconds` config (currently 300s for in-memory) provides a precedent. The metadata TTL should be longer (3600s default) because repo labels/branches change infrequently.
- Lazy refresh avoids background task complexity and aligns with the YAGNI principle (Constitution V).
- Users can force refresh via a "Refresh metadata" button, which clears the cache and re-fetches.

### Configuration

Add `metadata_cache_ttl_seconds: int = 3600` to `Settings` in `config.py`.

### Alternatives Considered

- **Background periodic refresh**: Adds a background task / scheduler. Rejected for simplicity.
- **Event-driven invalidation (webhooks)**: Requires webhook infrastructure. Out of scope.
- **No TTL (manual-only refresh)**: Poor UX — stale data would accumulate. Rejected.

---

## R4: AI Prompt Injection — Dynamic vs. Static Labels

### Decision

Replace the hardcoded `PREDEFINED_LABELS` list in the AI prompt with dynamically fetched labels, branches, milestones, and collaborators from the metadata cache. Fall back to hardcoded `LABELS` from `constants.py` if the cache is empty.

### Rationale

- FR-002 requires the AI to select from real repository values only.
- FR-005 requires priority/size values to map to actual repo labels.
- Current prompt (`issue_generation.py`) has `PREDEFINED_LABELS` baked in — this must become dynamic.
- Fallback to `constants.py` `LABELS` ensures the system works even when no cache is available (first launch, API failure).

### Prompt Structure

```text
AVAILABLE LABELS (from repository — select from this list ONLY):
{json_list_of_cached_labels}

AVAILABLE BRANCHES (for development/parent branch selection):
{json_list_of_cached_branches}

AVAILABLE MILESTONES:
{json_list_of_cached_milestones}

ASSIGNEE CANDIDATES:
{json_list_of_cached_collaborators}
```

### Alternatives Considered

- **Post-generation mapping**: Let AI generate free-text, then map afterwards. Rejected because it leads to poor matches and doesn't leverage the AI's contextual understanding.
- **Structured output with enum constraints**: Use OpenAI function-calling / JSON schema. Rejected because the Copilot SDK doesn't support structured outputs yet.

---

## R5: Issue Creation Payload — Milestone, Assignees, Branch

### Decision

Expand the `create_issue` REST call to include `milestone` (number) and `assignees` (list of logins). The development branch is recorded as a metadata reference in the issue body and/or as a project custom field — GitHub REST API does not natively link branches to issues.

### Rationale

- The GitHub REST API `POST /repos/{owner}/{repo}/issues` accepts `milestone` (number) and `assignees` (array of strings) directly.
- Currently `create_issue` in `service.py` only sends `title`, `body`, `labels`. Adding two more fields is trivial.
- Branch association is not a native GitHub Issues field. Options: (a) mention in body, (b) store in project custom field, (c) create a linked PR. Option (a) is simplest and sufficient for the MVP; option (b) can be added via `set_issue_metadata` which already sets project fields.

### Alternatives Considered

- **GraphQL `createIssue` mutation**: Supports the same fields as REST but with more complexity. No advantage for this use case.
- **Auto-create linked PR for branch**: Creates unnecessary PRs before work begins. Rejected.

---

## R6: Frontend Editable Metadata — Inline Edit vs. Modal

### Decision

Add inline-editable fields directly within the existing `IssueRecommendationPreview` component. Each metadata field becomes a controlled input (dropdown for enums, date picker for dates, multi-select for labels).

### Rationale

- FR-008 and FR-009 require preview and override capability.
- The current preview already displays metadata fields as read-only badges. Extending to editable fields is the minimal change.
- A modal would break the chat flow and add navigation complexity. Inline editing keeps the user in context.

### UI Approach

- **Priority**: Dropdown (P0–P3) with color-coded options
- **Size**: Dropdown (XS–XL)
- **Estimate**: Number input with step=0.5
- **Start/Target Date**: Date picker inputs
- **Labels**: Multi-select chips with typeahead from cached labels
- **Assignees**: Multi-select dropdown from cached collaborators
- **Branch**: Single-select dropdown from cached branches
- **Milestone**: Single-select dropdown from cached milestones

### Alternatives Considered

- **Separate edit modal**: Adds click-through overhead. Rejected for inline editing simplicity.
- **No editing (accept/reject only)**: Violates FR-009. Rejected.

---

## R7: Error Handling and Fallback Strategy

### Decision

Implement a three-tier fallback: (1) L1 in-memory cache → (2) SQLite persistent cache → (3) hardcoded `constants.py` labels. API errors are caught, logged, and surfaced to the user as a non-blocking notification.

### Rationale

- FR-010 requires graceful degradation with cached fallback.
- The three-tier approach ensures the system always has _some_ data to work with.
- The existing `_request_with_retry` in `GitHubProjectsService` handles transient 429/503 errors with exponential backoff. Permanent failures (404, 403) fall through to cached data.

### Error Flow

```
API fetch attempt
  ├── Success → Update SQLite + L1 cache → Return fresh data
  ├── Transient error (429/503) → Retry with backoff (existing logic)
  └── Permanent error (404/403/network) → Log warning
       ├── SQLite cache available → Return stale data + "Using cached data" indicator
       └── No SQLite cache → Return hardcoded LABELS + "Limited metadata" indicator
```

### Alternatives Considered

- **Block issue creation on API failure**: Violates the "always functional" principle. Rejected.
- **Silent fallback with no user notification**: Poor UX. Rejected.
