# Data Model: Agents Section on Project Board

**Feature**: `017-agents-section` | **Date**: 2026-03-03

## Entities

### AgentConfig (existing — `agent_configs` SQLite table)

The `agent_configs` table already exists (migration `007_agent_configs.sql`). No schema changes needed for core CRUD. The new Agents section reuses this table directly.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | TEXT | PRIMARY KEY | UUID v4 |
| `name` | TEXT | NOT NULL | Display name (e.g., "Security Reviewer") |
| `slug` | TEXT | NOT NULL | Kebab-case identifier (e.g., "security-reviewer") |
| `description` | TEXT | NOT NULL | One-line purpose summary |
| `system_prompt` | TEXT | NOT NULL | Full system prompt (≤30,000 chars) |
| `status_column` | TEXT | NOT NULL | Assigned pipeline status column |
| `tools` | TEXT | NOT NULL, DEFAULT '[]' | JSON array of tool identifiers |
| `project_id` | TEXT | NOT NULL | Associated GitHub project node ID |
| `owner` | TEXT | NOT NULL | GitHub repo owner |
| `repo` | TEXT | NOT NULL | GitHub repo name |
| `created_by` | TEXT | NOT NULL | GitHub user ID of creator |
| `github_issue_number` | INTEGER | nullable | Tracking issue number |
| `github_pr_number` | INTEGER | nullable | Creation PR number |
| `branch_name` | TEXT | nullable | Feature branch name (e.g., `agent/security-reviewer`) |
| `created_at` | TEXT | NOT NULL, DEFAULT now | ISO 8601 timestamp |

**Indexes**:
- `idx_agent_configs_project` on `(project_id)`
- `idx_agent_configs_slug` on `(slug, project_id)`

**Unique constraint**: `(name, project_id)`

### AgentPreview (existing — Pydantic model)

Used during the creation flow to represent the agent before committing. Already defined in `models/agent_creator.py`.

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Display name |
| `slug` | str | Derived via `name_to_slug()` |
| `description` | str | One-line summary |
| `system_prompt` | str | Full prompt text |
| `status_column` | str | Target pipeline column |
| `tools` | list[str] | Tool identifiers (default `[]`) |

### Agent (new — Pydantic response model)

API response model for agent listing. Merges data from SQLite and GitHub repo.

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | UUID (from SQLite) or derived ID (from repo) |
| `name` | str | Display name |
| `slug` | str | Kebab-case identifier |
| `description` | str | One-line summary |
| `system_prompt` | str | Full prompt content |
| `status` | AgentStatus | Lifecycle state: `active`, `pending_pr`, `pending_deletion` |
| `tools` | list[str] | Tool identifiers |
| `status_column` | str \| None | Assigned pipeline column (None if not assigned) |
| `github_issue_number` | int \| None | Tracking issue number |
| `github_pr_number` | int \| None | Creation/edit PR number |
| `branch_name` | str \| None | Feature branch |
| `source` | AgentSource | Where this agent was loaded from: `local`, `repo`, `both` |
| `created_at` | str \| None | ISO 8601 (None for repo-only agents) |

### AgentStatus (new — Enum)

| Value | Description |
|-------|-------------|
| `active` | Agent files exist in repository's default branch |
| `pending_pr` | Agent created locally, PR not yet merged |
| `pending_deletion` | Deletion PR opened, awaiting merge |

### AgentSource (new — Enum)

| Value | Description |
|-------|-------------|
| `local` | Exists only in SQLite (PR not merged) |
| `repo` | Exists only in GitHub repo (created outside this app) |
| `both` | Exists in both SQLite and GitHub repo |

### AgentCreate (new — Pydantic request model)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `name` | str | required, 1-100 chars | Agent display name |
| `description` | str | required, 1-500 chars | One-line summary |
| `system_prompt` | str | required, 1-30000 chars | Full system prompt |
| `tools` | list[str] | optional, default `[]` | Tool identifiers |
| `status_column` | str | optional, default `""` | Pipeline column assignment |

### AgentUpdate (new — Pydantic request model, P3)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `name` | str \| None | optional, 1-100 chars | Updated display name |
| `description` | str \| None | optional, 1-500 chars | Updated summary |
| `system_prompt` | str \| None | optional, 1-30000 chars | Updated prompt |
| `tools` | list[str] \| None | optional | Updated tool list |

### AgentChatMessage (new — Pydantic request model)

| Field | Type | Description |
|-------|------|-------------|
| `message` | str | User's input in the chat refinement flow |
| `session_id` | str \| None | Chat session ID for multi-turn continuity |

### AgentChatResponse (new — Pydantic response model)

| Field | Type | Description |
|-------|------|-------------|
| `reply` | str | AI's response (questions, preview, or confirmation) |
| `session_id` | str | Session ID for next turn |
| `is_complete` | bool | True when a final agent config is ready |
| `preview` | AgentPreview \| None | Generated agent preview when `is_complete=True` |

### CommitWorkflowResult (new — shared dataclass)

Result of the shared branch → commit → PR → issue workflow.

| Field | Type | Description |
|-------|------|-------------|
| `success` | bool | Overall success |
| `branch_name` | str \| None | Created branch name |
| `commit_oid` | str \| None | Commit SHA |
| `pr_number` | int \| None | PR number |
| `pr_url` | str \| None | PR URL |
| `issue_number` | int \| None | Tracking issue number |
| `issue_node_id` | str \| None | Issue node ID for project board |
| `errors` | list[str] | Per-step error messages |

## Relationships

```text
AgentConfig (SQLite) ──── 1:1 ──── Agent File Pair (.agent.md + .prompt.md)
      │                                      │
      │ project_id                           │ slug (filename)
      ▼                                      ▼
  GitHub Project                    GitHub Repository
      │                                      │
      │ status_column                        │ default branch
      ▼                                      ▼
  Pipeline Mapping              Source of Truth (post-merge)
```

## State Transitions

```text
                    ┌─────────────┐
     User creates   │  pending_pr │──── PR merged ──── ┐
     agent via UI   │  (SQLite)   │                    │
                    └──────┬──────┘                    ▼
                           │                    ┌─────────────┐
                           │ PR closed          │   active    │
                           │ without merge      │  (repo)     │
                           ▼                    └──────┬──────┘
                    ┌─────────────┐                    │
                    │  (removed)  │                    │ User deletes
                    └─────────────┘                    │ agent via UI
                                                       ▼
                                                ┌─────────────────┐
                                                │ pending_deletion│
                                                │  (SQLite flag)  │
                                                └────────┬────────┘
                                                         │ Deletion PR merged
                                                         ▼
                                                  ┌─────────────┐
                                                  │  (removed)  │
                                                  └─────────────┘
```

## Validation Rules

- **Name**: 1-100 characters, must be unique per `project_id` (checked against both SQLite and repo)
- **Slug**: Derived from name via `name_to_slug()` — lowercase, hyphens for spaces, strip invalid chars. Must match pattern `[a-z0-9][a-z0-9._-]*`
- **Description**: 1-500 characters
- **System Prompt**: 1-30,000 characters (GitHub Custom Agent limit)
- **Tools**: Array of strings; unrecognized tool names are ignored by GitHub (per spec)
- **Filename**: Must contain only `.`, `-`, `_`, `a-z`, `A-Z`, `0-9` (enforced via slug)
