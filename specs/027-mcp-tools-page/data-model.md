# Data Model: Add Tools Page with MCP Configuration Upload and Agent Tool Selection

**Feature**: 027-mcp-tools-page | **Date**: 2026-03-07

## Backend Entities (Pydantic Models)

### McpToolConfig

The primary entity representing an uploaded MCP tool configuration with sync status tracking.

```python
class McpToolConfig(BaseModel):
    id: str                              # UUID, primary key
    github_user_id: str                  # Owner (authenticated user)
    project_id: str                      # Scoping to project
    name: str                            # MCP server display name (1–100 chars)
    description: str = ""                # Auto-generated or user-provided (0–500 chars)
    endpoint_url: str                    # MCP server URL or command
    config_content: str = "{}"           # Raw JSON config content
    sync_status: str = "pending"         # "synced" | "pending" | "error"
    sync_error: str = ""                 # Human-readable error message (empty if no error)
    synced_at: str | None = None         # ISO 8601 datetime of last successful sync
    github_repo_target: str = ""         # "owner/repo" target for sync
    is_active: bool = True               # Active/inactive toggle
    created_at: str                      # ISO 8601 datetime
    updated_at: str                      # ISO 8601 datetime
```

**Relationships**: Owned by a user (`github_user_id`). Scoped to a project (`project_id`). Referenced by 0..N `AgentToolAssociation` records.

### McpToolConfigCreate

Request body for creating/uploading a new MCP tool configuration.

```python
class McpToolConfigCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    config_content: str = Field(min_length=2, max_length=262144)  # 256 KB limit
    github_repo_target: str = Field(default="", max_length=200)   # "owner/repo"
```

**Validation Rules**:
- `name` must be non-empty (1–100 characters)
- `description` max 500 characters
- `config_content` must be valid JSON conforming to MCP schema (validated server-side)
- `config_content` max 256 KB
- `github_repo_target` optional; if provided, must match `owner/repo` format

### McpToolConfigUpdate

Request body for updating an existing MCP tool configuration.

```python
class McpToolConfigUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    config_content: str | None = None
    github_repo_target: str | None = None
```

**Validation Rules**: Same as `McpToolConfigCreate` for any provided field.

### McpToolConfigResponse

Single MCP tool configuration in API responses.

```python
class McpToolConfigResponse(BaseModel):
    id: str
    name: str
    description: str
    endpoint_url: str
    config_content: str
    sync_status: str                     # "synced" | "pending" | "error"
    sync_error: str
    synced_at: str | None
    github_repo_target: str
    is_active: bool
    created_at: str
    updated_at: str
```

### McpToolConfigListResponse

Response for the list endpoint.

```python
class McpToolConfigListResponse(BaseModel):
    tools: list[McpToolConfigResponse]
    count: int
```

### McpToolConfigSyncResult

Response for sync operations.

```python
class McpToolConfigSyncResult(BaseModel):
    id: str
    sync_status: str
    sync_error: str
    synced_at: str | None
```

### AgentToolAssociation

Represents the many-to-many relationship between agents and MCP tools.

```python
class AgentToolAssociation(BaseModel):
    agent_id: str                        # References agent_configs.id
    tool_id: str                         # References mcp_configurations.id
    assigned_at: str                     # ISO 8601 datetime
```

**Relationships**: References one `agent_configs` record and one `mcp_configurations` record.

---

## Frontend Types (TypeScript)

### MCP Tool Types

```typescript
interface McpToolConfig {
  id: string;
  name: string;
  description: string;
  endpointUrl: string;
  configContent: string;
  syncStatus: 'synced' | 'pending' | 'error';
  syncError: string;
  syncedAt: string | null;
  githubRepoTarget: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

interface McpToolConfigCreate {
  name: string;
  description: string;
  configContent: string;
  githubRepoTarget: string;
}

interface McpToolConfigListResponse {
  tools: McpToolConfig[];
  count: number;
}

interface McpToolSyncResult {
  id: string;
  syncStatus: 'synced' | 'pending' | 'error';
  syncError: string;
  syncedAt: string | null;
}
```

### Agent-Tool Selection Types

```typescript
interface ToolSelectorState {
  isOpen: boolean;
  selectedToolIds: Set<string>;
  searchQuery: string;
}

interface ToolChip {
  id: string;
  name: string;
  description: string;
}
```

---

## Database Schema

### Extended mcp_configurations Table (Migration 014)

```sql
-- Migration 014: Extend MCP configurations for Tools page
-- Adds description, config content, sync status tracking, project scoping

ALTER TABLE mcp_configurations ADD COLUMN description TEXT NOT NULL DEFAULT '';
ALTER TABLE mcp_configurations ADD COLUMN config_content TEXT NOT NULL DEFAULT '{}';
ALTER TABLE mcp_configurations ADD COLUMN sync_status TEXT NOT NULL DEFAULT 'pending';
ALTER TABLE mcp_configurations ADD COLUMN sync_error TEXT NOT NULL DEFAULT '';
ALTER TABLE mcp_configurations ADD COLUMN synced_at TEXT;
ALTER TABLE mcp_configurations ADD COLUMN github_repo_target TEXT NOT NULL DEFAULT '';
ALTER TABLE mcp_configurations ADD COLUMN project_id TEXT NOT NULL DEFAULT '';

CREATE INDEX IF NOT EXISTS idx_mcp_configs_project
    ON mcp_configurations(project_id);

CREATE INDEX IF NOT EXISTS idx_mcp_configs_sync_status
    ON mcp_configurations(sync_status);
```

### Agent-Tool Associations Table (Migration 014, same file)

```sql
-- Junction table for many-to-many agent ↔ MCP tool relationship
CREATE TABLE IF NOT EXISTS agent_tool_associations (
    agent_id TEXT NOT NULL,
    tool_id TEXT NOT NULL,
    assigned_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (agent_id, tool_id)
);

CREATE INDEX IF NOT EXISTS idx_agent_tools_agent
    ON agent_tool_associations(agent_id);

CREATE INDEX IF NOT EXISTS idx_agent_tools_tool
    ON agent_tool_associations(tool_id);
```

**Storage Notes**:
- Extending the existing `mcp_configurations` table preserves backward compatibility with the Settings page MCP management.
- `config_content` stores the raw uploaded JSON for re-syncing and display.
- `sync_status` tracks the state machine for GitHub sync operations.
- `project_id` defaults to empty string for backward compatibility with existing user-scoped MCP entries.
- The composite primary key on `agent_tool_associations` prevents duplicate assignments.
- Indexes on both foreign keys support efficient queries in both directions.

---

## State Machines

### MCP Tool Sync Status

```
                    ┌──────────────┐
                    │   PENDING    │  (Upload accepted, sync not started or in progress)
                    │              │
                    └──────┬───────┘
                           │ Sync to GitHub
                    ┌──────┴───────┐
                    │              │
              Success          Failure
                    │              │
                    ▼              ▼
             ┌──────────┐   ┌──────────┐
             │  SYNCED   │   │  ERROR   │
             │           │   │          │
             └──────┬────┘   └────┬─────┘
                    │              │
               Re-sync         Re-sync (retry)
                    │              │
                    ▼              ▼
             ┌──────────────┐
             │   PENDING    │  (Re-sync in progress)
             └──────────────┘
```

### Tool Selector Modal Flow

```
Agent Form (Add Tools section)
    │
    │ Click "Add Tools"
    ▼
┌───────────────────────────┐
│    TOOL SELECTOR MODAL    │
│                           │
│  ┌─ Search ────────────┐  │
│  │                     │  │
│  └─────────────────────┘  │
│                           │
│  ┌─ Tile Grid ─────────┐  │
│  │ [Tool A ✓] [Tool B] │  │
│  │ [Tool C]   [Tool D ✓]│  │
│  └─────────────────────┘  │
│                           │
│  [ Cancel ]  [ Confirm ]  │
└───────────────────────────┘
    │
    │ Confirm
    ▼
Agent Form
    ┌─ Selected Tools ───────┐
    │ [Tool A ×] [Tool D ×]  │
    └────────────────────────┘
```

---

## Existing Entities (Unchanged)

The following existing entities are referenced but not structurally modified:

- **McpConfiguration** (`backend/src/models/mcp.py`): `id`, `name`, `endpoint_url`, `is_active`, timestamps — the base table being extended.
- **AgentConfig** (`backend/src/migrations/007_agent_configs.sql`): `tools` JSON column already exists, will be utilized to store selected tool IDs.
- **McpConfigurationCreate** (`backend/src/models/mcp.py`): Existing create model — the new `McpToolConfigCreate` extends this for the Tools page upload workflow.
