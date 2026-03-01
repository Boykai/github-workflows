# Data Model: Custom Agent Creation via Chat (#agent)

**Feature**: 001-custom-agent-creation  
**Date**: 2026-02-28  
**Status**: Complete

## Entities

### AgentConfig (persisted)

Stores a custom agent's full definition. Created during the pipeline execution step.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | TEXT (UUID) | PRIMARY KEY | Unique identifier |
| `name` | TEXT | NOT NULL, UNIQUE per project | Agent display name (e.g., "SecurityReviewer") |
| `slug` | TEXT | NOT NULL | Kebab-case identifier derived from name (e.g., "security-reviewer") |
| `description` | TEXT | NOT NULL | One-line summary of agent purpose |
| `system_prompt` | TEXT | NOT NULL | Full system prompt defining agent behavior |
| `status_column` | TEXT | NOT NULL | Assigned project board column name |
| `tools` | TEXT (JSON) | NOT NULL | JSON array of tool identifiers |
| `project_id` | TEXT | NOT NULL | GitHub Project node ID (e.g., "PVT_...") |
| `owner` | TEXT | NOT NULL | Repository owner |
| `repo` | TEXT | NOT NULL | Repository name |
| `created_by` | TEXT | NOT NULL | GitHub user ID of the admin who created it |
| `github_issue_number` | INTEGER | NULL | Issue number (if creation succeeded) |
| `github_pr_number` | INTEGER | NULL | PR number (if creation succeeded) |
| `branch_name` | TEXT | NULL | Branch name (if creation succeeded) |
| `created_at` | TEXT | NOT NULL | ISO 8601 timestamp |

**Relationships**: 
- Belongs to a project (`project_id`) and repository (`owner/repo`)
- Created by a user (`created_by`)
- Links to GitHub artifacts (issue, PR, branch) — nullable because pipeline steps may fail

**Validation rules**:
- `name` must be unique within a `project_id` (enforced by UNIQUE constraint on `name, project_id`)
- `slug` derived from `name`: lowercase, replace spaces/special chars with hyphens, strip leading/trailing hyphens
- `tools` must be a valid JSON array
- `status_column` must be a non-empty string

---

### AgentCreationState (in-memory, transient)

Tracks the multi-step guided conversation for a single agent creation session.

| Field | Type | Description |
|-------|------|-------------|
| `step` | Enum | Current step: `PARSE`, `RESOLVE_PROJECT`, `RESOLVE_STATUS`, `PREVIEW`, `EDIT_LOOP`, `EXECUTING`, `DONE` |
| `session_id` | str | Web chat session ID or Signal user ID (used as BoundedDict key) |
| `project_id` | str | Target GitHub Project node ID |
| `owner` | str | Repository owner |
| `repo` | str | Repository name |
| `raw_description` | str | Original description text from the `#agent` command |
| `raw_status` | str \| None | Optional status name from `#<status-name>` in command |
| `resolved_status` | str \| None | Matched or new column name after resolution |
| `is_new_column` | bool | Whether the resolved status requires creating a new column |
| `preview` | AgentPreview \| None | AI-generated agent configuration preview |
| `pipeline_results` | list[PipelineStepResult] | Results from each pipeline step |
| `created_at` | datetime | When the conversation started |

**Lifecycle**: Created when `#agent` is first detected → updated as steps progress → evicted from `BoundedDict` on completion or FIFO eviction.

**State transitions**:
```
PARSE → RESOLVE_PROJECT (if project unknown/ambiguous)
PARSE → RESOLVE_STATUS (if project known)
RESOLVE_PROJECT → RESOLVE_STATUS
RESOLVE_STATUS → PREVIEW
PREVIEW → EDIT_LOOP (if user requests changes)
EDIT_LOOP → PREVIEW (after applying edits)
PREVIEW → EXECUTING (on user confirmation)
EXECUTING → DONE
```

---

### AgentPreview (in-memory, transient)

The AI-generated agent configuration shown to the user for review.

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Agent display name |
| `slug` | str | Kebab-case derived identifier |
| `description` | str | One-line summary |
| `system_prompt` | str | Full system prompt text |
| `status_column` | str | Assigned status column |
| `tools` | list[str] | All available tool identifiers |

---

### PipelineStepResult (in-memory, transient)

Result of a single step in the creation pipeline.

| Field | Type | Description |
|-------|------|-------------|
| `step_name` | str | Human-readable step name (e.g., "Save agent configuration") |
| `success` | bool | Whether the step completed successfully |
| `error` | str \| None | Error message if failed |
| `detail` | str \| None | Extra info (e.g., issue URL, PR URL) |

---

## Database Migration: 007_agent_configs.sql

```sql
CREATE TABLE IF NOT EXISTS agent_configs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    description TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    status_column TEXT NOT NULL,
    tools TEXT NOT NULL DEFAULT '[]',
    project_id TEXT NOT NULL,
    owner TEXT NOT NULL,
    repo TEXT NOT NULL,
    created_by TEXT NOT NULL,
    github_issue_number INTEGER,
    github_pr_number INTEGER,
    branch_name TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(name, project_id)
);

CREATE INDEX IF NOT EXISTS idx_agent_configs_project ON agent_configs(project_id);
CREATE INDEX IF NOT EXISTS idx_agent_configs_slug ON agent_configs(slug, project_id);
```

## Entity Relationship Summary

```
AgentCreationState (in-memory)
  ├── has one → AgentPreview (in-memory, during PREVIEW/EDIT_LOOP steps)
  ├── has many → PipelineStepResult (in-memory, during EXECUTING step)
  └── produces → AgentConfig (persisted to DB on pipeline execution)

AgentConfig (DB)
  ├── belongs to → Project (via project_id)
  ├── belongs to → Repository (via owner/repo)
  ├── created by → User (via created_by)
  └── links to → GitHub Issue, PR, Branch (nullable)
```
