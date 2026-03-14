# Data Model: Solune Rebrand & App Builder Architecture

**Feature**: `041-solune-rebrand-app-builder` | **Date**: 2026-03-14
**Input**: Research findings from [`research.md`](research.md), feature spec from [`spec.md`](spec.md)

## Entities

### 1. Application (App)

The primary entity representing a user-created project managed by the Solune platform.

**Source**: FR-012, FR-013, FR-014, FR-015, FR-017

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `name` | TEXT | PRIMARY KEY, UNIQUE, regex `^[a-z0-9][a-z0-9-]*[a-z0-9]$` (2-64 chars) | Unique identifier, used as directory name under `apps/` |
| `display_name` | TEXT | NOT NULL, max 128 chars | Human-readable name shown in the UI |
| `description` | TEXT | DEFAULT '' | Optional app description |
| `directory_path` | TEXT | NOT NULL | Relative path from repo root (e.g., `apps/my-app`) |
| `associated_pipeline_id` | TEXT | NULLABLE, FK → `workflow_configurations.id` | Optional link to an agent pipeline |
| `status` | TEXT | NOT NULL, CHECK IN ('creating', 'active', 'stopped', 'error'), DEFAULT 'creating' | Current lifecycle state |
| `repo_type` | TEXT | NOT NULL, CHECK IN ('same-repo', 'external-repo'), DEFAULT 'same-repo' | Where the app code lives |
| `external_repo_url` | TEXT | NULLABLE | GitHub URL if repo_type = 'external-repo' |
| `port` | INTEGER | NULLABLE | Dynamically assigned local port when running |
| `error_message` | TEXT | NULLABLE | Last error message if status = 'error' |
| `created_at` | TEXT | NOT NULL, DEFAULT RFC3339 with 'Z' | Creation timestamp |
| `updated_at` | TEXT | NOT NULL, DEFAULT RFC3339 with 'Z' | Last modification timestamp |

**Validation Rules** (FR-014):
- `name`: Alphanumeric and hyphens only. Must start and end with alphanumeric. Length 2-64. No path traversal (`..`, `/`, `\`). No reserved names (`api`, `admin`, `solune`, `apps`, `github`).
- `display_name`: Non-empty, trimmed, max 128 characters.
- `directory_path`: Always computed as `apps/{name}` — never user-supplied.

**State Machine** (FR-017):

```text
                 ┌──────────┐
   create ──────►│ creating │
                 └────┬─────┘
                      │ scaffold complete
                      ▼
                 ┌──────────┐
          ┌─────►│  active  │◄─────┐
          │      └────┬─────┘      │
          │           │ stop       │ start
          │           ▼            │
          │      ┌──────────┐      │
          │      │ stopped  │──────┘
          │      └────┬─────┘
          │           │ delete
          │           ▼
          │      [DELETED]
          │
     any──┤
          │      ┌──────────┐
          └─────►│  error   │
                 └────┬─────┘
                      │ delete / retry
                      ▼
                 [DELETED] or back to creating
```

**Valid Transitions**:
| From | To | Trigger |
|------|----|---------|
| (new) | creating | `create_app()` |
| creating | active | Scaffold completes successfully |
| creating | error | Scaffold fails |
| active | stopped | `stop_app()` |
| stopped | active | `start_app()` |
| active | error | Runtime failure detected |
| stopped | (deleted) | `delete_app()` |
| error | (deleted) | `delete_app()` |
| error | creating | `retry_app()` (re-scaffold) |
| creating | (deleted) | `delete_app()` (cancel creation) |

**Invalid Transitions** (must be rejected):
- `active` → (deleted): Must stop first (FR-018)

---

### 2. App Context (Session-level)

Tracks which application is the active working scope in the chat interface. Not a database table — stored as session metadata.

**Source**: FR-023, FR-024, FR-025, FR-026

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `active_app_name` | TEXT | NULLABLE, FK → `apps.name` | Currently selected app, or NULL for platform context |
| `session_id` | TEXT | FK → `user_sessions.session_id` | The user session this context belongs to |

**Behavior**:
- Default: `NULL` (no app selected, operations target the platform)
- Set via `/<app-name>` slash command
- Cleared via `/platform` or similar command to return to platform context
- Persisted per-session so context survives page refreshes
- Does NOT affect conversation history visibility (FR-026)

---

### 3. Guard Rule (Configuration-level)

Defines protection levels for file paths. Stored in a configuration file, not in the database.

**Source**: FR-027, FR-028, FR-029, FR-030

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `path_pattern` | TEXT | Required, glob pattern | File path pattern to protect (e.g., `solune/**`) |
| `guard_level` | TEXT | Required, ENUM('admin', 'adminlock') | Protection level |
| `description` | TEXT | Optional | Human-readable explanation of why this path is protected |

**Default Configuration**:
```yaml
guard_rules:
  - path_pattern: "solune/**"
    guard_level: admin
    description: "Platform core — requires elevated permission"
  - path_pattern: ".github/**"
    guard_level: adminlock
    description: "Workflow and agent configs — fully locked"
  - path_pattern: "apps/**"
    guard_level: none
    description: "App directories — unrestricted for agents"
```

**Evaluation Rules** (FR-030):
- Rules are evaluated per-file when an operation targets multiple paths
- Most specific match wins (longest path prefix)
- `adminlock` always blocks, no override possible
- `admin` blocks by default, can be overridden with elevated permission
- Paths not matching any rule default to `admin` (fail-closed)

---

### 4. App Scaffold Template

Defines the directory structure created when a new app is scaffolded. Not a database entity — filesystem structure.

**Source**: FR-015

```text
apps/<app-name>/
├── README.md              # Auto-generated with app name and description
├── config.json            # Configuration placeholder
│   {
│     "name": "<app-name>",
│     "display_name": "<display_name>",
│     "version": "0.1.0",
│     "created_at": "<timestamp>"
│   }
├── src/                   # Source code directory
│   └── .gitkeep
├── CHANGELOG.md           # Empty changelog
└── docker-compose.yml     # Template for app services (optional)
```

---

## Relationships

```text
┌─────────────────────┐         ┌──────────────────────────┐
│       apps          │         │  workflow_configurations  │
│─────────────────────│         │──────────────────────────│
│ name (PK)           │────────►│  id (PK)                 │
│ display_name        │  0..1   │  name                    │
│ description         │         │  ...                     │
│ directory_path      │         └──────────────────────────┘
│ associated_pipeline │
│ status              │         ┌──────────────────────────┐
│ repo_type           │         │    user_sessions         │
│ external_repo_url   │         │──────────────────────────│
│ port                │         │  session_id (PK)         │
│ error_message       │         │  active_app_name ────────┤──► apps.name
│ created_at          │         │  ...                     │    (session attr)
│ updated_at          │         └──────────────────────────┘
└─────────────────────┘

┌─────────────────────┐
│  guard_rules.yml    │  (config file, not DB)
│─────────────────────│
│ path_pattern        │
│ guard_level         │
│ description         │
└─────────────────────┘
```

## SQLite Migration (024_apps.sql)

```sql
-- Migration 024: Application management
CREATE TABLE IF NOT EXISTS apps (
    name TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    directory_path TEXT NOT NULL,
    associated_pipeline_id TEXT,
    status TEXT NOT NULL DEFAULT 'creating'
        CHECK (status IN ('creating', 'active', 'stopped', 'error')),
    repo_type TEXT NOT NULL DEFAULT 'same-repo'
        CHECK (repo_type IN ('same-repo', 'external-repo')),
    external_repo_url TEXT,
    port INTEGER,
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    FOREIGN KEY (associated_pipeline_id) REFERENCES workflow_configurations(id)
        ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_apps_status ON apps(status);
CREATE INDEX IF NOT EXISTS idx_apps_created_at ON apps(created_at);
```

## Pydantic Models (Backend)

```python
# backend/src/models/app.py
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class AppStatus(str, Enum):
    CREATING = "creating"
    ACTIVE = "active"
    STOPPED = "stopped"
    ERROR = "error"


class RepoType(str, Enum):
    SAME_REPO = "same-repo"
    EXTERNAL_REPO = "external-repo"


class App(BaseModel):
    name: str = Field(..., pattern=r"^[a-z0-9][a-z0-9-]*[a-z0-9]$", min_length=2, max_length=64)
    display_name: str = Field(..., min_length=1, max_length=128)
    description: str = Field(default="")
    directory_path: str
    associated_pipeline_id: Optional[str] = None
    status: AppStatus = AppStatus.CREATING
    repo_type: RepoType = RepoType.SAME_REPO
    external_repo_url: Optional[str] = None
    port: Optional[int] = None
    error_message: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""


class AppCreate(BaseModel):
    name: str = Field(..., pattern=r"^[a-z0-9][a-z0-9-]*[a-z0-9]$", min_length=2, max_length=64)
    display_name: str = Field(..., min_length=1, max_length=128)
    description: str = Field(default="")
    pipeline_id: Optional[str] = None
    repo_type: RepoType = RepoType.SAME_REPO
    external_repo_url: Optional[str] = None


class AppUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = None
    pipeline_id: Optional[str] = None


class AppStatusResponse(BaseModel):
    name: str
    status: AppStatus
    port: Optional[int] = None
    error_message: Optional[str] = None
```

## TypeScript Types (Frontend)

```typescript
// frontend/src/types/apps.ts
export type AppStatus = 'creating' | 'active' | 'stopped' | 'error';
export type RepoType = 'same-repo' | 'external-repo';

export interface App {
  name: string;
  display_name: string;
  description: string;
  directory_path: string;
  associated_pipeline_id: string | null;
  status: AppStatus;
  repo_type: RepoType;
  external_repo_url: string | null;
  port: number | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface AppCreate {
  name: string;
  display_name: string;
  description?: string;
  pipeline_id?: string;
  repo_type?: RepoType;
  external_repo_url?: string;
}

export interface AppUpdate {
  display_name?: string;
  description?: string;
  pipeline_id?: string;
}

export interface AppStatusResponse {
  name: string;
  status: AppStatus;
  port: number | null;
  error_message: string | null;
}
```
