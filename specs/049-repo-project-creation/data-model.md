# Data Model: New Repository & New Project Creation for Solune

**Branch**: `049-repo-project-creation` | **Date**: 2026-03-17

## Overview

This feature extends the existing `apps` data model with new repository and project metadata, adds a new `Owner` entity for the frontend owner selection dropdown, and defines the template file structure used during repository initialization. The core data flow is: user input → GitHub API calls (create repo, create project, link, commit templates) → database record with references to the created resources.

## Entities

### App (Extended)

The existing `App` model is extended with new fields to store references to the GitHub repository and project created during the "new-repo" flow.

| Field | Type | Description | New? |
|---|---|---|---|
| name | TEXT (PK) | Unique app identifier (2-64 chars, kebab-case) | No |
| display_name | TEXT NOT NULL | Human-readable name | No |
| description | TEXT DEFAULT '' | App description | No |
| directory_path | TEXT NOT NULL | Path within the repository (e.g., `apps/my-app`) | No |
| associated_pipeline_id | TEXT (FK, nullable) | Link to workflow_configurations | No |
| status | TEXT NOT NULL | One of: creating, active, stopped, error | No |
| repo_type | TEXT NOT NULL | One of: same-repo, external-repo, **new-repo** | **Modified** |
| external_repo_url | TEXT (nullable) | URL for external-repo type | No |
| github_repo_url | TEXT (nullable) | URL of the created GitHub repository | **New** |
| github_project_url | TEXT (nullable) | URL of the linked GitHub Project V2 | **New** |
| github_project_id | TEXT (nullable) | Node ID of the linked GitHub Project V2 | **New** |
| port | INTEGER (nullable) | Assigned port for running app | No |
| error_message | TEXT (nullable) | Last error message | No |
| created_at | TEXT NOT NULL | ISO 8601 timestamp | No |
| updated_at | TEXT NOT NULL | ISO 8601 timestamp (auto-updated by trigger) | No |

**Validation Rules**:
- `repo_type` CHECK constraint: must be one of `'same-repo'`, `'external-repo'`, `'new-repo'`
- When `repo_type = 'new-repo'`: `github_repo_url` SHOULD be non-null after successful creation
- When `repo_type = 'new-repo'` with project: `github_project_url` and `github_project_id` SHOULD be non-null
- `github_project_url` and `github_project_id` may be null even for `new-repo` type if project creation failed (partial success)

**Location**: `solune/backend/src/models/app.py` (Pydantic) + `solune/backend/src/migrations/028_new_repo_support.sql` (SQLite)

### RepoType (Extended Enum)

```python
class RepoType(StrEnum):
    SAME_REPO = "same-repo"
    EXTERNAL_REPO = "external-repo"
    NEW_REPO = "new-repo"          # NEW
```

**Location**: `solune/backend/src/models/app.py`

### AppCreate (Extended Input Model)

| Field | Type | Description | New? |
|---|---|---|---|
| name | str | App name (validated against APP_NAME_PATTERN) | No |
| display_name | str | Human-readable name | No |
| description | str | App description | No |
| branch | str (optional when new-repo) | Target branch for scaffold commit | **Modified** |
| pipeline_id | str \| None | Optional pipeline association | No |
| repo_type | RepoType | One of: same-repo, external-repo, new-repo | No |
| external_repo_url | str \| None | URL for external-repo type | No |
| ai_enhance | bool | Whether to AI-enhance description | No |
| repo_owner | str \| None | GitHub owner (user/org) for new-repo | **New** |
| repo_visibility | Literal["public", "private"] | Repository visibility (default: private) | **New** |
| create_project | bool | Whether to create a linked Project V2 (default: True) | **New** |

**Validation Rules**:
- When `repo_type = 'new-repo'`: `repo_owner` MUST be provided, `branch` is optional (defaults to repo's default branch)
- When `repo_type = 'same-repo'` or `'external-repo'`: `branch` MUST be provided, `repo_owner`/`repo_visibility`/`create_project` are ignored
- `repo_visibility` defaults to `"private"` if not specified

**Location**: `solune/backend/src/models/app.py`

### Owner (New Entity — Frontend Only)

Represents a GitHub user or organization that can own repositories and projects.

| Field | Type | Description |
|---|---|---|
| login | string | GitHub username or org name |
| avatar_url | string | URL to avatar image |
| type | 'User' \| 'Organization' | Owner type |

**Location**: `solune/frontend/src/types/apps.ts` (TypeScript) + returned by `GET /apps/owners` endpoint

**Note**: This entity is not persisted in the database. It is fetched from GitHub's API on demand and cached on the frontend.

### CreateProjectRequest (New Input Model)

Input for the standalone project creation endpoint.

| Field | Type | Description |
|---|---|---|
| title | string | Project title (required) |
| owner | string | GitHub owner login (user/org) |
| repo_owner | string \| None | Optional: repository owner to link |
| repo_name | string \| None | Optional: repository name to link |

**Location**: `solune/backend/src/api/projects.py` (request body) + `solune/frontend/src/types/apps.ts` (TypeScript)

### CreateProjectResponse (New Output Model)

Output from the standalone project creation endpoint.

| Field | Type | Description |
|---|---|---|
| project_id | string | GitHub Project V2 node ID |
| project_number | int | Project number within the owner |
| project_url | string | URL to the project board |

**Location**: `solune/backend/src/api/projects.py` (response) + `solune/frontend/src/types/apps.ts` (TypeScript)

### TemplateFile (Internal — Not Persisted)

Represents a file to be committed to a new repository.

| Field | Type | Description |
|---|---|---|
| path | string | File path relative to repo root (e.g., `.github/copilot-instructions.md`) |
| content | string | File content (text) |

**Location**: `solune/backend/src/services/template_files.py` (internal dict structure)

## State Transitions

### App Creation (New Repo Flow)

```
INPUT_RECEIVED → REPO_CREATING → REPO_CREATED → TEMPLATES_COMMITTING → TEMPLATES_COMMITTED → PROJECT_CREATING → PROJECT_CREATED → PROJECT_LINKED → DB_RECORD_INSERTED → ACTIVE
```

Error branches:
- `REPO_CREATING → ERROR` (repo creation fails → entire flow fails)
- `PROJECT_CREATING → PARTIAL_SUCCESS` (project fails → app created with null project fields)
- `PROJECT_LINKED → PARTIAL_SUCCESS` (linking fails → app created with project but not linked)

### App Creation (Same Repo Flow — Existing)

```
INPUT_RECEIVED → BRANCH_RESOLVED → SCAFFOLD_COMMITTED → DB_RECORD_INSERTED → ACTIVE
```

No changes to existing flow.

### Standalone Project Creation

```
INPUT_RECEIVED → PROJECT_CREATING → PROJECT_CREATED → (OPTIONAL: LINKING) → PROJECT_LINKED → AUTO_SELECTED
```

Error branches:
- `PROJECT_CREATING → ERROR` (project creation fails → return error)
- `LINKING → PARTIAL_SUCCESS` (linking fails → project created but not linked to repo)

## Relationships

```
App ──── 0..1 ────→ GitHub Repository (via github_repo_url)
App ──── 0..1 ────→ GitHub Project V2 (via github_project_id, github_project_url)
GitHub Project V2 ──── 0..* ────→ GitHub Repository (via linkProjectV2ToRepository)
Owner ──── 1..* ────→ GitHub Repository (ownership)
Owner ──── 1..* ────→ GitHub Project V2 (ownership)
TemplateFile ──── * ────→ GitHub Repository (committed during creation)
```

## Migration: 028_new_repo_support.sql

```sql
-- Migration 028: New repository support for apps
-- Adds fields for tracking GitHub resources created during new-repo app creation.

-- Add new columns (nullable for backward compatibility with existing rows)
ALTER TABLE apps ADD COLUMN github_repo_url TEXT;
ALTER TABLE apps ADD COLUMN github_project_url TEXT;
ALTER TABLE apps ADD COLUMN github_project_id TEXT;

-- SQLite does not support ALTER CHECK CONSTRAINT.
-- Recreate the table to update the repo_type CHECK constraint.
CREATE TABLE apps_new (
    name TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    directory_path TEXT NOT NULL,
    associated_pipeline_id TEXT,
    status TEXT NOT NULL DEFAULT 'creating'
        CHECK (status IN ('creating', 'active', 'stopped', 'error')),
    repo_type TEXT NOT NULL DEFAULT 'same-repo'
        CHECK (repo_type IN ('same-repo', 'external-repo', 'new-repo')),
    external_repo_url TEXT,
    github_repo_url TEXT,
    github_project_url TEXT,
    github_project_id TEXT,
    port INTEGER,
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    FOREIGN KEY (associated_pipeline_id) REFERENCES workflow_configurations(id)
        ON DELETE SET NULL
);

INSERT INTO apps_new SELECT
    name, display_name, description, directory_path, associated_pipeline_id,
    status, repo_type, external_repo_url,
    NULL, NULL, NULL,  -- github_repo_url, github_project_url, github_project_id
    port, error_message, created_at, updated_at
FROM apps;

DROP TABLE apps;
ALTER TABLE apps_new RENAME TO apps;

-- Recreate indexes
CREATE INDEX IF NOT EXISTS idx_apps_status ON apps(status);
CREATE INDEX IF NOT EXISTS idx_apps_created_at ON apps(created_at);

-- Recreate trigger
CREATE TRIGGER IF NOT EXISTS trg_apps_updated_at
    AFTER UPDATE ON apps
    FOR EACH ROW
BEGIN
    UPDATE apps SET updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
    WHERE name = OLD.name;
END;
```
