# Data Model: SQLite-Backed Settings Storage

**Feature**: 006-sqlite-settings-storage
**Date**: 2026-02-19

## Entity Relationship Overview

```
schema_version (singleton)
    │
    ├── user_sessions (1 per session; N per user)
    │       └── FK: github_user_id
    │
    ├── user_preferences (1 per user)
    │       └── PK: github_user_id
    │
    ├── project_settings (1 per user-project pair)
    │       └── PK: (github_user_id, project_id)
    │       └── FK: github_user_id → user_preferences
    │
    └── global_settings (singleton)
```

## Tables

### 1. schema_version

Tracks the current database schema version. Created unconditionally at startup with `CREATE TABLE IF NOT EXISTS`. Single row.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| version | INTEGER | NOT NULL | Current schema version number |
| applied_at | TEXT | NOT NULL | ISO 8601 timestamp of last migration |

**Indexes**: None (single row).
**Notes**: Initialized to `0` if no row exists. After running migration `001_*.sql`, updated to `1`.

---

### 2. user_sessions

Persists the existing `UserSession` Pydantic model. One row per active session. A user may have multiple concurrent sessions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| session_id | TEXT | PRIMARY KEY | UUID string (matches `UserSession.session_id`) |
| github_user_id | TEXT | NOT NULL, INDEX | GitHub user ID from OAuth |
| github_username | TEXT | NOT NULL | GitHub username for display |
| github_avatar_url | TEXT | NULL | User's avatar URL |
| access_token | TEXT | NOT NULL | GitHub OAuth access token |
| refresh_token | TEXT | NULL | OAuth refresh token |
| token_expires_at | TEXT | NULL | ISO 8601 token expiration timestamp |
| selected_project_id | TEXT | NULL | Currently selected GitHub Project ID |
| created_at | TEXT | NOT NULL | ISO 8601 session creation time |
| updated_at | TEXT | NOT NULL | ISO 8601 last activity time |

**Indexes**:
- `idx_sessions_github_user_id` on `github_user_id` (lookup sessions by user)
- `idx_sessions_updated_at` on `updated_at` (expired session cleanup query)

**Validation Rules**:
- `session_id` must be a valid UUID string
- `github_user_id` must be non-empty
- `github_username` must be non-empty
- `access_token` must be non-empty
- Timestamps stored as ISO 8601 strings (SQLite has no native datetime type)

**State Transitions**:
- Created on OAuth login (INSERT)
- Updated when user selects a project or token is refreshed (UPDATE `selected_project_id`, `access_token`, `updated_at`)
- Deleted on explicit logout (DELETE by `session_id`)
- Deleted by background cleanup when `updated_at` + session expiry window < now (DELETE batch)

---

### 3. user_preferences

Per-user settings. One row per user. All preference fields are nullable — NULL means "use global default."

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| github_user_id | TEXT | PRIMARY KEY | GitHub user ID (unique per user) |
| ai_provider | TEXT | NULL | "copilot" or "azure_openai" |
| ai_model | TEXT | NULL | Model identifier (e.g., "gpt-4o") |
| ai_temperature | REAL | NULL | Generation temperature (0.0–2.0) |
| theme | TEXT | NULL | "dark" or "light" |
| default_view | TEXT | NULL | "chat" or "board" or "settings" |
| sidebar_collapsed | INTEGER | NULL | Boolean as 0/1 |
| default_repository | TEXT | NULL | "owner/repo" format |
| default_assignee | TEXT | NULL | GitHub username |
| copilot_polling_interval | INTEGER | NULL | Seconds (0 to disable) |
| notify_task_status_change | INTEGER | NULL | Boolean as 0/1 |
| notify_agent_completion | INTEGER | NULL | Boolean as 0/1 |
| notify_new_recommendation | INTEGER | NULL | Boolean as 0/1 |
| notify_chat_mention | INTEGER | NULL | Boolean as 0/1 |
| updated_at | TEXT | NOT NULL | ISO 8601 last update time |

**Indexes**: None beyond PK (lookup is always by PK).

**Validation Rules**:
- `ai_provider` must be one of: "copilot", "azure_openai", or NULL
- `ai_temperature` must be between 0.0 and 2.0, or NULL
- `theme` must be one of: "dark", "light", or NULL
- `default_view` must be one of: "chat", "board", "settings", or NULL
- `copilot_polling_interval` must be ≥ 0, or NULL
- Notification booleans: 0, 1, or NULL (NULL = use global default)

**State Transitions**:
- Created on first preference save (INSERT or INSERT OR REPLACE)
- Updated on subsequent preference changes (UPDATE)
- Never deleted (preferences persist even if user has no active sessions)

---

### 4. project_settings

Per-user-per-project settings. One row per (user, project) pair. All fields nullable — NULL means "use user preference or global default."

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| github_user_id | TEXT | NOT NULL | GitHub user ID |
| project_id | TEXT | NOT NULL | GitHub Project ID (e.g., "PVT_kwDOABCD1234") |
| board_display_config | TEXT | NULL | JSON string of board display preferences |
| agent_pipeline_mappings | TEXT | NULL | JSON string of status→agent mappings |
| updated_at | TEXT | NOT NULL | ISO 8601 last update time |

**Primary Key**: Composite `(github_user_id, project_id)`

**Indexes**:
- `idx_project_settings_user` on `github_user_id` (list all project settings for a user)

**Validation Rules**:
- `github_user_id` must be non-empty
- `project_id` must be non-empty
- `board_display_config` must be valid JSON or NULL
- `agent_pipeline_mappings` must be valid JSON or NULL

**JSON Column Schemas**:

`board_display_config` example:
```json
{
  "column_order": ["Backlog", "Ready", "In Progress", "Done"],
  "collapsed_columns": ["Done"],
  "show_estimates": true
}
```

`agent_pipeline_mappings` example:
```json
{
  "Backlog": [{"slug": "speckit.specify", "display_name": "Spec Kit - Specify"}],
  "Ready": [{"slug": "speckit.plan", "display_name": "Spec Kit - Plan"}]
}
```

**State Transitions**:
- Created on first project-specific setting save (INSERT OR REPLACE)
- Updated on subsequent changes (UPDATE)
- Never auto-deleted (stale project references are harmless and may be cleaned up manually)

---

### 5. global_settings

Instance-wide default configuration. Single row (singleton). Seeded from environment variables on first startup.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, DEFAULT 1, CHECK(id = 1) | Singleton constraint |
| ai_provider | TEXT | NOT NULL | Default: from env `AI_PROVIDER` |
| ai_model | TEXT | NOT NULL | Default: from env `COPILOT_MODEL` |
| ai_temperature | REAL | NOT NULL, DEFAULT 0.7 | Default generation temperature |
| theme | TEXT | NOT NULL, DEFAULT 'light' | Default theme |
| default_view | TEXT | NOT NULL, DEFAULT 'chat' | Default landing view |
| sidebar_collapsed | INTEGER | NOT NULL, DEFAULT 0 | Default sidebar state |
| default_repository | TEXT | NULL | From env `DEFAULT_REPOSITORY` |
| default_assignee | TEXT | NOT NULL, DEFAULT '' | From env `DEFAULT_ASSIGNEE` |
| copilot_polling_interval | INTEGER | NOT NULL, DEFAULT 60 | From env `COPILOT_POLLING_INTERVAL` |
| notify_task_status_change | INTEGER | NOT NULL, DEFAULT 1 | All notifications on by default |
| notify_agent_completion | INTEGER | NOT NULL, DEFAULT 1 | All notifications on by default |
| notify_new_recommendation | INTEGER | NOT NULL, DEFAULT 1 | All notifications on by default |
| notify_chat_mention | INTEGER | NOT NULL, DEFAULT 1 | All notifications on by default |
| allowed_models | TEXT | NOT NULL, DEFAULT '[]' | JSON array of allowed model identifiers |
| updated_at | TEXT | NOT NULL | ISO 8601 last update time |

**Indexes**: None (singleton, always accessed by `id = 1`).
**Constraint**: `CHECK(id = 1)` enforces singleton pattern.

**Validation Rules**:
- `ai_provider` must be one of: "copilot", "azure_openai"
- `ai_temperature` must be between 0.0 and 2.0
- `theme` must be one of: "dark", "light"
- `default_view` must be one of: "chat", "board", "settings"
- `copilot_polling_interval` must be ≥ 0
- `allowed_models` must be valid JSON array
- Notification booleans: 0 or 1

**State Transitions**:
- Created (seeded from environment variables) on first startup if no row exists
- Updated when any authenticated user modifies global settings
- Never deleted

**Seeding Logic** (first startup only):
```
IF global_settings has 0 rows:
  INSERT with values from environment variables (Settings model)
  ai_provider ← env.AI_PROVIDER (default: "copilot")
  ai_model ← env.COPILOT_MODEL (default: "gpt-4o")
  default_repository ← env.DEFAULT_REPOSITORY
  default_assignee ← env.DEFAULT_ASSIGNEE (default: "")
  copilot_polling_interval ← env.COPILOT_POLLING_INTERVAL (default: 60)
```

---

## Settings Merge Logic

The API returns **effective settings** by merging layers. Merge precedence (highest wins):

```
project_settings > user_preferences > global_settings
```

**Algorithm** (for user settings endpoint):
1. Load `global_settings` row (all fields NOT NULL — always a complete record)
2. Load `user_preferences` row (fields may be NULL)
3. For each field: if user value is NOT NULL, use it; otherwise use global value
4. Return merged result

**Algorithm** (for project settings endpoint):
1. Load merged user settings (above)
2. Load `project_settings` row for (user_id, project_id)
3. For project-specific fields: if project value is NOT NULL, use it; otherwise use merged user value
4. Return merged result

The merge is performed server-side. The API response always contains a fully-resolved settings object with no NULL values.

---

## Migration: 001_initial_schema.sql

This is the first migration script applied at startup:

```sql
-- Migration 001: Initial schema for settings storage

CREATE TABLE IF NOT EXISTS user_sessions (
    session_id TEXT PRIMARY KEY,
    github_user_id TEXT NOT NULL,
    github_username TEXT NOT NULL,
    github_avatar_url TEXT,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_expires_at TEXT,
    selected_project_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_github_user_id ON user_sessions(github_user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_updated_at ON user_sessions(updated_at);

CREATE TABLE IF NOT EXISTS user_preferences (
    github_user_id TEXT PRIMARY KEY,
    ai_provider TEXT,
    ai_model TEXT,
    ai_temperature REAL,
    theme TEXT,
    default_view TEXT,
    sidebar_collapsed INTEGER,
    default_repository TEXT,
    default_assignee TEXT,
    copilot_polling_interval INTEGER,
    notify_task_status_change INTEGER,
    notify_agent_completion INTEGER,
    notify_new_recommendation INTEGER,
    notify_chat_mention INTEGER,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS project_settings (
    github_user_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    board_display_config TEXT,
    agent_pipeline_mappings TEXT,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (github_user_id, project_id)
);

CREATE INDEX IF NOT EXISTS idx_project_settings_user ON project_settings(github_user_id);

CREATE TABLE IF NOT EXISTS global_settings (
    id INTEGER PRIMARY KEY DEFAULT 1 CHECK(id = 1),
    ai_provider TEXT NOT NULL DEFAULT 'copilot',
    ai_model TEXT NOT NULL DEFAULT 'gpt-4o',
    ai_temperature REAL NOT NULL DEFAULT 0.7,
    theme TEXT NOT NULL DEFAULT 'light',
    default_view TEXT NOT NULL DEFAULT 'chat',
    sidebar_collapsed INTEGER NOT NULL DEFAULT 0,
    default_repository TEXT,
    default_assignee TEXT NOT NULL DEFAULT '',
    copilot_polling_interval INTEGER NOT NULL DEFAULT 60,
    notify_task_status_change INTEGER NOT NULL DEFAULT 1,
    notify_agent_completion INTEGER NOT NULL DEFAULT 1,
    notify_new_recommendation INTEGER NOT NULL DEFAULT 1,
    notify_chat_mention INTEGER NOT NULL DEFAULT 1,
    allowed_models TEXT NOT NULL DEFAULT '[]',
    updated_at TEXT NOT NULL
);
```
