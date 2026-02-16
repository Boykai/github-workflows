# Data Model: Standalone Project Board Page

**Feature**: 003-project-board | **Date**: 2026-02-16  
**Purpose**: Define entities and their relationships for feature implementation

## Model Overview

This feature introduces five key entities that represent the GitHub Projects V2 board structure: Board Project, Board Status Column, Board Issue Card, Linked Pull Request, and Board Assignee. All data is sourced from the GitHub Projects V2 GraphQL API and proxied through the FastAPI backend. No persistent storage is introduced — data is cached in-memory with the existing cache service.

## Entities

### Entity: BoardProject

**Type**: API Response Model (Pydantic backend, TypeScript frontend)  
**Purpose**: Represents a GitHub Project V2 available to the authenticated user  
**Lifecycle**: Fetched from GitHub API, cached in-memory (TTL: 300s default)

**Attributes**:

| Attribute | Type | Constraints | Source | Description |
|-----------|------|-------------|--------|-------------|
| `project_id` | `string` | Required, GitHub node ID | `ProjectV2.id` | Unique GitHub Project V2 identifier |
| `title` | `string` | Required, non-empty | `ProjectV2.title` | Project display name |
| `description` | `string \| null` | Optional | `ProjectV2.shortDescription` | Brief project description |
| `url` | `string` | Required, valid URL | `ProjectV2.url` | GitHub project URL |
| `item_count` | `number` | >= 0 | `ProjectV2.items.totalCount` | Total number of items in the project |
| `status_columns` | `BoardStatusColumn[]` | Array, can be empty | `ProjectV2.field("Status").options` | Available status options |

**Validation Rules**:
1. `project_id` must be a valid GitHub node ID (non-empty string)
2. `title` must be non-empty
3. `url` must be a valid HTTPS URL
4. `item_count` must be non-negative

**Relationships**:
- Has many `BoardStatusColumn` (one per status option)
- Contains many `BoardIssueCard` (grouped by status)

---

### Entity: BoardStatusColumn

**Type**: Nested model within BoardProject / board response  
**Purpose**: Represents a status column in the Kanban board  
**Lifecycle**: Derived from project status field options + aggregated from items

**Attributes**:

| Attribute | Type | Constraints | Source | Description |
|-----------|------|-------------|--------|-------------|
| `name` | `string` | Required, non-empty | `ProjectV2SingleSelectFieldOption.name` | Column display name (e.g., "Todo", "In Progress") |
| `color` | `string` | Required | `ProjectV2SingleSelectFieldOption.color` | Color identifier (e.g., "GREEN", "YELLOW") |
| `option_id` | `string` | Required | `ProjectV2SingleSelectFieldOption.id` | GitHub option ID |
| `description` | `string \| null` | Optional | Derived or static | Column description text |
| `item_count` | `number` | >= 0 | Computed | Count of items in this status |
| `total_estimate` | `number \| null` | >= 0 or null | Computed | Sum of estimate values for items in this column |
| `items` | `BoardIssueCard[]` | Array | Filtered from project items | Issue cards belonging to this column |

**Validation Rules**:
1. `name` must be non-empty
2. `color` must be one of GitHub's valid color names (GREEN, YELLOW, RED, BLUE, PURPLE, PINK, ORANGE, GRAY)
3. `item_count` must match `items.length`
4. `total_estimate` is null if no items have estimate values

**Relationships**:
- Belongs to one `BoardProject`
- Has many `BoardIssueCard`

---

### Entity: BoardIssueCard

**Type**: API Response Model  
**Purpose**: Represents an issue or draft issue within a project board column  
**Lifecycle**: Fetched from GitHub API as project item content

**Attributes**:

| Attribute | Type | Constraints | Source | Description |
|-----------|------|-------------|--------|-------------|
| `item_id` | `string` | Required | `ProjectV2Item.id` | GitHub project item ID |
| `content_id` | `string \| null` | Optional (null for draft issues) | `Issue.id` | GitHub issue node ID |
| `issue_number` | `number \| null` | Optional (null for drafts) | `Issue.number` | Issue number in repository |
| `title` | `string` | Required, non-empty | `Issue.title` or `DraftIssue.title` | Issue title |
| `body` | `string \| null` | Optional | `Issue.body` or `DraftIssue.body` | Issue description/body text |
| `state` | `string \| null` | "OPEN", "CLOSED", or null | `Issue.state` | Issue state on GitHub |
| `url` | `string \| null` | Optional (null for drafts) | `Issue.url` | GitHub issue URL |
| `repo_name` | `string \| null` | Optional (null for drafts) | `Issue.repository.name` | Repository short name |
| `repo_full_name` | `string \| null` | Optional (null for drafts) | `Issue.repository.nameWithOwner` | Repository full name (owner/repo) |
| `status` | `string \| null` | Optional | Field value "Status" | Current status field value |
| `priority` | `string \| null` | Optional | Field value "Priority" | Priority field value (e.g., "P0", "P1", "P2", "P3") |
| `size` | `string \| null` | Optional | Field value "Size" | Size field value (e.g., "XS", "S", "M", "L", "XL") |
| `estimate` | `number \| null` | Optional, >= 0 | Field value "Estimate" | Estimate in story points or hours |
| `assignees` | `BoardAssignee[]` | Array, can be empty | `Issue.assignees.nodes` | Users assigned to this issue |
| `linked_prs` | `LinkedPullRequest[]` | Array, can be empty | Secondary query | Pull requests linked to this issue |

**Validation Rules**:
1. `item_id` must be a valid GitHub node ID
2. `title` must be non-empty
3. If `content_id` is null, the card is a draft issue (no `issue_number`, `url`, `repo_name`)
4. `priority` should match known values if present
5. `estimate` must be non-negative if present

**State Transitions**: None — read-only view. Status changes happen on GitHub.

**Relationships**:
- Belongs to one `BoardStatusColumn` (via status field value)
- Has many `BoardAssignee` (zero or more)
- Has many `LinkedPullRequest` (zero or more)

---

### Entity: LinkedPullRequest

**Type**: Nested model within BoardIssueCard  
**Purpose**: Represents a pull request linked to an issue  
**Lifecycle**: Fetched via secondary GraphQL query on issue timeline items

**Attributes**:

| Attribute | Type | Constraints | Source | Description |
|-----------|------|-------------|--------|-------------|
| `pr_number` | `number` | Required, > 0 | `PullRequest.number` | PR number |
| `title` | `string` | Required | `PullRequest.title` | PR title |
| `state` | `string` | "OPEN", "CLOSED", "MERGED" | `PullRequest.state` | PR state |
| `url` | `string` | Required, valid URL | `PullRequest.url` | GitHub PR URL |

**Validation Rules**:
1. `pr_number` must be positive integer
2. `state` must be one of "OPEN", "CLOSED", "MERGED"
3. `url` must be a valid HTTPS URL

**Relationships**:
- Belongs to one `BoardIssueCard` (many-to-one)

---

### Entity: BoardAssignee

**Type**: Nested model within BoardIssueCard  
**Purpose**: Represents a user assigned to an issue  
**Lifecycle**: Fetched as part of issue content in board data query

**Attributes**:

| Attribute | Type | Constraints | Source | Description |
|-----------|------|-------------|--------|-------------|
| `login` | `string` | Required, non-empty | `User.login` | GitHub username |
| `avatar_url` | `string` | Required, valid URL | `User.avatarUrl` | GitHub avatar image URL |

**Validation Rules**:
1. `login` must be non-empty
2. `avatar_url` must be a valid URL (HTTPS)

**Relationships**:
- Belongs to one `BoardIssueCard` (many-to-one)

---

## Entity Relationships

```
BoardProject (1)
  └── BoardStatusColumn (many)
        └── BoardIssueCard (many)
              ├── BoardAssignee (many)
              └── LinkedPullRequest (many)
```

- A `BoardProject` contains multiple `BoardStatusColumn` entries (one per status option)
- Each `BoardStatusColumn` contains multiple `BoardIssueCard` entries (filtered by status)
- Each `BoardIssueCard` has zero or more `BoardAssignee` entries
- Each `BoardIssueCard` has zero or more `LinkedPullRequest` entries

---

## Data Flow

```
User selects project in dropdown
       ↓
Frontend calls GET /api/v1/project-board/{project_id}/board
       ↓
Backend authenticates via session cookie
       ↓
Backend checks in-memory cache for board data
       ↓ (cache miss)
Backend sends GraphQL query to GitHub API
       ↓
GitHub returns ProjectV2 items with field values
       ↓
Backend parses and groups items by status column
       ↓
Backend sends secondary GraphQL query for linked PRs (batched)
       ↓
Backend merges linked PR data into issue cards
       ↓
Backend caches response and returns to frontend
       ↓
Frontend renders Kanban board with columns and cards
       ↓
Auto-refresh: repeat every 15 seconds
```

**Flow Characteristics**:
- **Request-Response**: All data flows through REST API calls
- **Proxied**: Frontend never directly calls GitHub API
- **Cached**: Backend caches responses to reduce GitHub API load
- **Paginated**: Large projects use cursor-based pagination on GraphQL query
- **Lazy**: Linked PRs fetched in secondary query, not blocking initial render

---

## Data Storage

**Storage Mechanism**: In-memory cache (existing `cache` service)  
**Format**: Serialized Python objects (Pydantic models)  
**Persistence**: Non-persistent; cache cleared on backend restart  
**TTL**: 300 seconds (configurable via `CACHE_TTL_SECONDS` setting)  
**Eviction**: Time-based expiry

---

## Security Considerations

**Threat Model**: Moderate — proxies authenticated GitHub API calls

**Security Properties**:
- **Token Security**: GitHub access token stored server-side in session; never exposed to browser
- **Authentication**: All board endpoints require valid session cookie (existing auth middleware)
- **Authorization**: Users can only see projects their GitHub token has access to (enforced by GitHub API)
- **No XSS Risk**: All data rendered as text content, not raw HTML. React auto-escapes JSX
- **No Injection Risk**: GraphQL queries use parameterized variables, not string concatenation
- **Rate Limiting**: Existing rate limiter protects against excessive GitHub API calls
- **Data Exposure**: No sensitive data beyond what user can already see on GitHub

---

## Performance Characteristics

**API Response Size**:
- Project list: ~2KB for 20 projects
- Board data (50 items): ~15-25KB
- Board data (100 items): ~30-50KB
- Linked PRs (50 issues): ~5-10KB

**Latency Estimates**:
- Cached response: < 50ms
- GitHub GraphQL query (board data): 500-1500ms
- GitHub GraphQL query (linked PRs): 300-800ms
- Total cold load: 1-3 seconds

**Memory Impact**: Minimal — cached board data is ephemeral, ~50KB per project

---

## Phase 1 Data Model Completion Checklist

- [x] All entities identified (5: BoardProject, BoardStatusColumn, BoardIssueCard, LinkedPullRequest, BoardAssignee)
- [x] Entity attributes documented with types and constraints
- [x] Validation rules defined for all entities
- [x] Relationships documented (hierarchical: Project → Columns → Cards → Assignees/PRs)
- [x] Data flow described (frontend → backend → GitHub API → cache → frontend)
- [x] Storage mechanism identified (in-memory cache, existing service)
- [x] Security considerations addressed (token proxy, auth, rate limiting)
- [x] Performance impact assessed (response sizes, latency estimates)
- [x] No migration required (no persistent storage)
- [x] Alternative models not applicable (data shape dictated by GitHub API)

**Status**: ✅ **DATA MODEL COMPLETE** - Ready for contracts and quickstart generation
