# Data Model: Debug & Fix Apps Page — New App Creation UX

**Feature**: `051-fix-app-creation-ux` | **Date**: 2026-03-17

## Entity Changes

### App (Modified)

**Table**: `apps`
**Migration**: `029_app_parent_issue.sql`

#### New Fields

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `parent_issue_number` | INTEGER | Yes | NULL | GitHub issue number for the Parent Issue created to kickstart the Agent Pipeline |
| `parent_issue_url` | TEXT | Yes | NULL | Full URL to the Parent Issue on GitHub (e.g., `https://github.com/owner/repo/issues/1`) |

#### Existing Fields (no changes)

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `name` | TEXT | No | Primary key; kebab-case, 2–64 chars |
| `display_name` | TEXT | No | Human-readable name, 1–128 chars |
| `description` | TEXT | No | App description, default empty string |
| `directory_path` | TEXT | No | Relative path to app directory |
| `associated_pipeline_id` | TEXT | Yes | FK → `pipeline_configs(id)` — already exists but unused in creation flow |
| `status` | TEXT | No | CHECK: `'creating' \| 'active' \| 'stopped' \| 'error'` |
| `repo_type` | TEXT | No | CHECK: `'same-repo' \| 'external-repo' \| 'new-repo'` |
| `external_repo_url` | TEXT | Yes | URL for external-repo type apps |
| `github_repo_url` | TEXT | Yes | URL for the GitHub repository (new-repo) |
| `github_project_url` | TEXT | Yes | URL for the GitHub Project V2 |
| `github_project_id` | TEXT | Yes | Node ID for the GitHub Project V2 |
| `port` | INTEGER | Yes | Port for running app |
| `error_message` | TEXT | Yes | Error details if status = 'error' |
| `created_at` | TEXT | No | ISO 8601 timestamp |
| `updated_at` | TEXT | No | ISO 8601 timestamp, auto-updated by trigger |

#### Transient Fields (in-memory only, not persisted)

| Field | Type | Description |
|-------|------|-------------|
| `warnings` | `list[str] \| None` | Warnings from partial-success creation (Azure secrets, template files, pipeline setup) |

### Migration SQL

```sql
-- 029_app_parent_issue.sql
-- Add parent issue tracking columns to the apps table

ALTER TABLE apps ADD COLUMN parent_issue_number INTEGER;
ALTER TABLE apps ADD COLUMN parent_issue_url TEXT;
```

**Notes**:
- Both columns are nullable with no default — existing rows automatically get NULL values
- No table recreation needed (unlike 028 which changed a CHECK constraint)
- No foreign key constraints — these reference external GitHub resources, not local tables
- The `associated_pipeline_id` FK references `pipeline_configs(id)` per migration 025

---

## Pydantic Model Changes

### App (Backend Model)

**File**: `apps/solune/backend/src/models/app.py`

```python
# New fields to add after existing github_project_id field:
parent_issue_number: int | None = None
parent_issue_url: str | None = None
```

### AppCreate (No changes needed)

The `AppCreate` model already has `pipeline_id: str | None = None` — this is the field that triggers Parent Issue creation when provided.

---

## TypeScript Type Changes

### App (Frontend Type)

**File**: `apps/solune/frontend/src/types/apps.ts`

```typescript
// New fields to add to the App interface:
parent_issue_number: number | null;
parent_issue_url: string | null;
```

---

## Relationships

```
App (1) ──── associated_pipeline_id ───→ (0..1) PipelineConfig
  │
  ├── parent_issue_number ───→ (0..1) GitHub Issue (external)
  ├── parent_issue_url ────→ (0..1) GitHub Issue URL (external)
  │
  └── github_project_id ───→ (0..1) GitHub Project V2 (external)
         │
         └── contains ───→ (0..N) Sub-Issues (external, managed by orchestrator)
```

---

## State Transitions

### App Creation Flow (with pipeline)

```
1. AppCreate payload received (with pipeline_id)
   ↓
2. GitHub repo created → status = 'creating'
   ↓
3. Branch readiness polled (exponential backoff, ~18.5s max)
   ↓
4. Template files committed → warnings[] if partial failure
   ↓
5. Azure secrets stored → warnings[] if failure (best-effort)
   ↓
6. GitHub Project V2 created → warnings[] if failure (best-effort)
   ↓
7. Pipeline loaded from pipeline_id
   ↓
8. Parent Issue created in target repo → parent_issue_number, parent_issue_url stored
   ↓  (best-effort: failure → warning, no parent issue fields set)
   ↓
9. Sub-issues created, PipelineState initialized, polling started
   ↓  (best-effort: failure → warning)
   ↓
10. App record inserted → status = 'active'
    ↓
11. App returned with warnings[] populated
```

### App Creation Flow (without pipeline)

Steps 1–6 and 10–11 only. Steps 7–9 skipped entirely. `parent_issue_number` and `parent_issue_url` remain NULL.

### App Deletion Flow (with parent issue)

```
1. DELETE /apps/{name} received
   ↓
2. If app.parent_issue_number is set:
   ↓
3. Close parent issue via GitHub API (best-effort)
   ↓  (failure → log warning, continue deletion)
   ↓
4. Delete app record from database
   ↓
5. Return success
```

---

## Validation Rules

| Field | Rule | Source |
|-------|------|--------|
| `parent_issue_number` | Positive integer when set | FR-005 |
| `parent_issue_url` | Valid HTTPS URL matching `https://github.com/{owner}/{repo}/issues/{number}` pattern when set | FR-005 |
| `associated_pipeline_id` | Must reference a valid `pipeline_configs` record when set (existing constraint) | FR-006 |
| `warnings` | Each string ≤ 500 chars; array ≤ 20 items (defensive limits) | FR-004, FR-014 |
