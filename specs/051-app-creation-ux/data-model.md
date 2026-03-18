# Data Model: Debug & Fix Apps Page — New App Creation UX

**Feature**: 051-app-creation-ux | **Date**: 2026-03-18

## Entities

### App (Modified)

The `App` entity gains two new nullable fields for parent issue tracking.

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| name | TEXT | No | — | Primary key, validated against `APP_NAME_PATTERN` |
| display_name | TEXT | No | — | Human-readable name (1–128 chars) |
| description | TEXT | No | `""` | App description |
| directory_path | TEXT | No | — | Filesystem path for app scaffold |
| associated_pipeline_id | TEXT | Yes | NULL | FK → `pipeline_configs(id)` |
| status | TEXT | No | `"creating"` | CHECK: creating, active, stopped, error |
| repo_type | TEXT | No | `"same-repo"` | CHECK: same-repo, external-repo, new-repo |
| external_repo_url | TEXT | Yes | NULL | URL for external-repo type |
| github_repo_url | TEXT | Yes | NULL | GitHub repository URL (new-repo) |
| github_project_url | TEXT | Yes | NULL | GitHub Project V2 URL |
| github_project_id | TEXT | Yes | NULL | GitHub Project V2 node ID |
| **parent_issue_number** | **INTEGER** | **Yes** | **NULL** | **NEW — GitHub issue number for the parent build issue** |
| **parent_issue_url** | **TEXT** | **Yes** | **NULL** | **NEW — Full URL to the parent issue on GitHub** |
| port | INTEGER | Yes | NULL | Assigned port for running app |
| error_message | TEXT | Yes | NULL | Last error message |
| created_at | TEXT | No | `now()` | ISO 8601 creation timestamp |
| updated_at | TEXT | No | `now()` | ISO 8601 last update (auto-trigger) |

**Transient Fields** (not persisted in DB):

| Field | Type | Description |
|-------|------|-------------|
| warnings | `list[str] \| None` | Populated in memory for non-fatal creation issues |

### Relationships

```
App ──(FK)──> pipeline_configs.id  (associated_pipeline_id, ON DELETE SET NULL)
App ──(ref)──> GitHub Issue         (parent_issue_number / parent_issue_url — external reference)
```

### Validation Rules

- `parent_issue_number` — positive integer when set; NULL when no pipeline selected
- `parent_issue_url` — valid GitHub issue URL format (`https://github.com/{owner}/{repo}/issues/{number}`) when set; NULL when no pipeline selected
- Both fields are always set together (both NULL or both populated) — enforced at application level, not DB constraint

### State Transitions

```
App.status:  creating ──> active ──> stopped ──> active (restart)
                 │            │          │
                 └──> error   └──> error └──> error
                 
                 (delete allowed from: stopped, error, creating)
```

**Parent issue lifecycle tied to app lifecycle**:
- Created during `create_app_with_new_repo()` when `pipeline_id` is provided
- Closed (not deleted) during `delete_app()` when `parent_issue_number` is set

## Migration

### 030_app_parent_issue.sql

```sql
-- Migration 030: Add parent issue tracking to apps table
-- Adds nullable columns for GitHub parent issue number and URL.
-- Used when a pipeline is selected during app creation.

ALTER TABLE apps ADD COLUMN parent_issue_number INTEGER;
ALTER TABLE apps ADD COLUMN parent_issue_url TEXT;
```

**Migration Notes**:
- Simple `ALTER TABLE ADD COLUMN` — no table recreation needed
- Both columns are nullable with no constraints
- No foreign key changes required
- Compatible with all existing rows (default NULL)

## Frontend Type Changes

### TypeScript `App` Interface

```typescript
export interface App {
  // ... existing fields ...
  parent_issue_number: number | null;  // NEW
  parent_issue_url: string | null;     // NEW
  // ... existing fields ...
}
```

### Pydantic Model Changes

```python
class App(BaseModel):
    # ... existing fields ...
    parent_issue_number: int | None = None  # NEW
    parent_issue_url: str | None = None     # NEW
    # ... existing fields ...
```

## External Entities (Reference)

### Parent Issue (GitHub)

Not stored in the Solune database — exists as a GitHub Issue in the target repository.

| Property | Source | Description |
|----------|--------|-------------|
| number | `create_issue()` response | GitHub issue number |
| url | `create_issue()` response | `html_url` field |
| title | Constructed | `"Build {app.display_name}"` |
| body | Constructed | App description + Solune link + tracking table |
| state | GitHub API | `open` → `closed` on app delete |

### Sub-Issues (GitHub)

Created by `create_all_sub_issues()` as child issues of the parent issue.

| Property | Source | Description |
|----------|--------|-------------|
| number | Orchestrator | Per-agent issue number |
| agent_name | Pipeline config | Agent responsible for the sub-issue |
| body | Tailored | Agent-specific instructions |

### Pipeline Configuration (Existing)

Existing `pipeline_configs` table — not modified by this feature.

| Property | Description |
|----------|-------------|
| id | Pipeline config identifier (TEXT PK) |
| config | JSON blob with agent mappings and status order |
