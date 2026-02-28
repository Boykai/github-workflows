# Data Model: MCP Configuration Support

**Feature**: 012-mcp-settings-config  
**Date**: 2026-02-28  
**Depends on**: research.md (R1, R6)

## Entities

### MCP Configuration

Represents a single Model Context Protocol server configuration owned by an authenticated GitHub user.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | TEXT (UUID) | PRIMARY KEY | Unique identifier for this MCP configuration |
| `github_user_id` | TEXT | NOT NULL, FK → user_sessions.github_user_id | Owning user's GitHub account ID |
| `name` | TEXT | NOT NULL, max 100 chars | Human-readable display name for the MCP |
| `endpoint_url` | TEXT | NOT NULL, max 2048 chars, valid HTTP(S) URL | MCP server endpoint URL |
| `is_active` | INTEGER | NOT NULL, DEFAULT 1 | Whether the MCP is active (1) or inactive (0) |
| `created_at` | TEXT | NOT NULL | ISO 8601 timestamp of creation |
| `updated_at` | TEXT | NOT NULL | ISO 8601 timestamp of last modification |

### Relationships

```
User Account (user_sessions)
  └── 1:N ── MCP Configuration (mcp_configurations)
              Constraint: max 25 per user
```

### Indexes

| Index | Columns | Purpose |
|-------|---------|---------|
| `idx_mcp_configs_user` | `github_user_id` | Fast lookup of all MCPs for a user |
| `idx_mcp_configs_user_name` | `github_user_id, name` | Support queries filtering by user + name |

### Validation Rules

| Rule | Field(s) | Enforcement |
|------|----------|-------------|
| Non-empty name | `name` | Pydantic validator + client-side |
| Max name length 100 | `name` | Pydantic `max_length=100` + client-side |
| Valid HTTP(S) URL | `endpoint_url` | Pydantic validator + SSRF check |
| Max URL length 2048 | `endpoint_url` | Pydantic `max_length=2048` + client-side |
| Max 25 MCPs per user | `github_user_id` | Pre-insert COUNT check in service layer |
| No private/reserved IPs | `endpoint_url` | Server-side SSRF validation at write time |

### State Transitions

The `is_active` field is read-only in this feature scope (set to `1` on creation). Toggling active/inactive is out of scope per assumptions in spec.md.

MCP lifecycle:
```
[Not Exists] → POST /settings/mcps → [Active (is_active=1)]
[Active]     → DELETE /settings/mcps/:id → [Deleted/Not Exists]
```

## Migration SQL

File: `backend/src/migrations/006_add_mcp_configurations.sql`

```sql
-- Migration 006: Add MCP configurations table for GitHub agent settings

CREATE TABLE IF NOT EXISTS mcp_configurations (
    id TEXT PRIMARY KEY,
    github_user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    endpoint_url TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_mcp_configs_user ON mcp_configurations(github_user_id);
CREATE INDEX IF NOT EXISTS idx_mcp_configs_user_name ON mcp_configurations(github_user_id, name);
```

## Backend Models (Pydantic)

### Response Models

```python
class McpConfigurationResponse(BaseModel):
    """Single MCP configuration in API responses."""
    id: str
    name: str
    endpoint_url: str
    is_active: bool
    created_at: str
    updated_at: str

class McpConfigurationListResponse(BaseModel):
    """List of MCP configurations for a user."""
    mcps: list[McpConfigurationResponse]
    count: int
```

### Request Models

```python
class McpConfigurationCreate(BaseModel):
    """Request body for creating a new MCP configuration."""
    name: str = Field(min_length=1, max_length=100)
    endpoint_url: str = Field(min_length=1, max_length=2048)

    @field_validator("endpoint_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        # Validate URL format and scheme (http/https only)
        # SSRF check: reject private/reserved IPs
        ...
```

### Database Row Model

```python
class McpConfigurationRow(BaseModel):
    """Represents an mcp_configurations database row."""
    id: str
    github_user_id: str
    name: str
    endpoint_url: str
    is_active: int  # 0/1 in SQLite
    created_at: str
    updated_at: str
```

## Frontend Types

```typescript
export interface McpConfiguration {
  id: string;
  name: string;
  endpoint_url: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface McpConfigurationListResponse {
  mcps: McpConfiguration[];
  count: number;
}

export interface McpConfigurationCreate {
  name: string;
  endpoint_url: string;
}
```
