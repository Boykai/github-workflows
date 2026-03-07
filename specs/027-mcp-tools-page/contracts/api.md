# API Contracts: Add Tools Page with MCP Configuration Upload and Agent Tool Selection

**Feature**: 027-mcp-tools-page | **Date**: 2026-03-07

## Base URL

All endpoints are prefixed with `/api/v1` and require an authenticated session (same auth pattern as existing endpoints in `/api/v1/agents/*` and `/api/v1/settings/mcps`).

---

## MCP Tool CRUD Endpoints

### List MCP Tools

```
GET /api/v1/tools/{project_id}
```

**Description**: List all MCP tool configurations for the given project owned by the authenticated user.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | string | Project identifier |

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sort` | string | `created_at` | Sort field: `created_at`, `name`, `sync_status` |
| `order` | string | `desc` | Sort order: `asc`, `desc` |

**Response** (200 OK):
```json
{
  "tools": [
    {
      "id": "uuid-1234",
      "name": "Sentry MCP",
      "description": "Sentry error tracking integration via MCP",
      "endpoint_url": "https://sentry.example.com/mcp",
      "config_content": "{\"mcpServers\":{\"sentry\":{\"type\":\"http\",\"url\":\"https://sentry.example.com/mcp\"}}}",
      "sync_status": "synced",
      "sync_error": "",
      "synced_at": "2026-03-07T10:30:00Z",
      "github_repo_target": "owner/repo",
      "is_active": true,
      "created_at": "2026-03-07T10:00:00Z",
      "updated_at": "2026-03-07T10:30:00Z"
    }
  ],
  "count": 1
}
```

**Error Responses**:
- `401 Unauthorized` — Missing or invalid session

---

### Upload MCP Tool Configuration

```
POST /api/v1/tools/{project_id}
```

**Description**: Upload and create a new MCP tool configuration. Validates the config content against MCP schema, stores locally, and initiates sync to GitHub.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | string | Project identifier |

**Request Body**:
```json
{
  "name": "Sentry MCP",
  "description": "Sentry error tracking integration via MCP",
  "config_content": "{\"mcpServers\":{\"sentry\":{\"type\":\"http\",\"url\":\"https://sentry.example.com/mcp\",\"headers\":{\"x-api-key\":\"${input:sentry-key}\"}}}}",
  "github_repo_target": "owner/repo"
}
```

**Validation**:
- `name`: Required, 1–100 characters
- `description`: Optional, 0–500 characters
- `config_content`: Required, must be valid JSON conforming to MCP schema:
  - Must contain a `mcpServers` object with at least one server entry
  - Each server must have `type` of `"http"` or `"stdio"`
  - HTTP servers must include `url`
  - Stdio servers must include `command`
- `config_content` max size: 256 KB
- `github_repo_target`: Optional, must match `owner/repo` format if provided
- Duplicate name check: warns if name matches existing config for this project

**Response** (201 Created):
```json
{
  "id": "uuid-new",
  "name": "Sentry MCP",
  "description": "Sentry error tracking integration via MCP",
  "endpoint_url": "https://sentry.example.com/mcp",
  "config_content": "{\"mcpServers\":{\"sentry\":{...}}}",
  "sync_status": "pending",
  "sync_error": "",
  "synced_at": null,
  "github_repo_target": "owner/repo",
  "is_active": true,
  "created_at": "2026-03-07T10:00:00Z",
  "updated_at": "2026-03-07T10:00:00Z"
}
```

**Error Responses**:
- `400 Bad Request` — Validation failure (invalid JSON, missing required MCP fields, name too long, file size exceeded)
- `401 Unauthorized` — Missing or invalid session
- `409 Conflict` — MCP tool with same name already exists in this project

---

### Get MCP Tool

```
GET /api/v1/tools/{project_id}/{tool_id}
```

**Description**: Get a single MCP tool configuration with full details.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | string | Project identifier |
| `tool_id` | string | UUID of the MCP tool |

**Response** (200 OK):
```json
{
  "id": "uuid-1234",
  "name": "Sentry MCP",
  "description": "Sentry error tracking integration via MCP",
  "endpoint_url": "https://sentry.example.com/mcp",
  "config_content": "{\"mcpServers\":{\"sentry\":{...}}}",
  "sync_status": "synced",
  "sync_error": "",
  "synced_at": "2026-03-07T10:30:00Z",
  "github_repo_target": "owner/repo",
  "is_active": true,
  "created_at": "2026-03-07T10:00:00Z",
  "updated_at": "2026-03-07T10:30:00Z"
}
```

**Error Responses**:
- `401 Unauthorized` — Missing or invalid session
- `404 Not Found` — Tool ID does not exist

---

### Sync MCP Tool to GitHub

```
POST /api/v1/tools/{project_id}/{tool_id}/sync
```

**Description**: Trigger a sync (or re-sync) of the MCP tool configuration to the connected GitHub repository. Updates or creates the `.copilot/mcp.json` file in the repo.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | string | Project identifier |
| `tool_id` | string | UUID of the MCP tool |

**Response** (200 OK):
```json
{
  "id": "uuid-1234",
  "sync_status": "synced",
  "sync_error": "",
  "synced_at": "2026-03-07T11:00:00Z"
}
```

**Error Responses**:
- `401 Unauthorized` — Missing or invalid session
- `404 Not Found` — Tool ID does not exist
- `502 Bad Gateway` — GitHub API error during sync (returns error details in sync_error)

---

### Delete MCP Tool

```
DELETE /api/v1/tools/{project_id}/{tool_id}
```

**Description**: Delete an MCP tool configuration. Returns a list of affected agents (if any) for the frontend to display a warning.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | string | Project identifier |
| `tool_id` | string | UUID of the MCP tool |

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `confirm` | boolean | `false` | Must be `true` to proceed when tool is assigned to agents |

**Response** (200 OK, when no agents affected or confirm=true):
```json
{
  "success": true,
  "deleted_id": "uuid-1234",
  "affected_agents": []
}
```

**Response** (200 OK, when agents affected and confirm=false):
```json
{
  "success": false,
  "deleted_id": null,
  "affected_agents": [
    { "id": "agent-uuid-1", "name": "Security Reviewer" },
    { "id": "agent-uuid-2", "name": "Code Auditor" }
  ]
}
```

**Error Responses**:
- `401 Unauthorized` — Missing or invalid session
- `404 Not Found` — Tool ID does not exist

---

## Agent-Tool Association Endpoints

### Get Agent Tools

```
GET /api/v1/agents/{project_id}/{agent_id}/tools
```

**Description**: List MCP tools assigned to a specific agent.

**Response** (200 OK):
```json
{
  "tools": [
    {
      "id": "uuid-1234",
      "name": "Sentry MCP",
      "description": "Sentry error tracking integration"
    }
  ]
}
```

---

### Update Agent Tools

```
PUT /api/v1/agents/{project_id}/{agent_id}/tools
```

**Description**: Set the MCP tools for an agent. Replaces the entire tool assignment list.

**Request Body**:
```json
{
  "tool_ids": ["uuid-1234", "uuid-5678"]
}
```

**Response** (200 OK):
```json
{
  "tools": [
    {
      "id": "uuid-1234",
      "name": "Sentry MCP",
      "description": "Sentry error tracking integration"
    },
    {
      "id": "uuid-5678",
      "name": "GitHub MCP",
      "description": "GitHub API integration"
    }
  ]
}
```

**Error Responses**:
- `400 Bad Request` — Invalid tool IDs (non-existent tools)
- `401 Unauthorized` — Missing or invalid session
- `404 Not Found` — Agent ID does not exist

**Notes**:
- Sending an empty `tool_ids` array removes all tool assignments from the agent.
- Invalid tool IDs in the array are rejected with a 400 error listing which IDs were invalid.

---

## Frontend API Client Methods

Added to `frontend/src/services/api.ts`:

```typescript
// MCP Tools CRUD
toolsApi: {
  list: (projectId: string, sort?: string, order?: string) =>
    GET<McpToolConfigListResponse>(`/tools/${projectId}`, { sort, order }),

  get: (projectId: string, toolId: string) =>
    GET<McpToolConfig>(`/tools/${projectId}/${toolId}`),

  create: (projectId: string, data: McpToolConfigCreate) =>
    POST<McpToolConfig>(`/tools/${projectId}`, data),

  sync: (projectId: string, toolId: string) =>
    POST<McpToolSyncResult>(`/tools/${projectId}/${toolId}/sync`),

  delete: (projectId: string, toolId: string, confirm?: boolean) =>
    DELETE<{ success: boolean; deleted_id: string | null; affected_agents: Array<{ id: string; name: string }> }>(
      `/tools/${projectId}/${toolId}`, { confirm }
    ),
},

// Agent-Tool Associations (extends existing agentsApi)
agentsApi: {
  // ... existing methods ...
  getTools: (projectId: string, agentId: string) =>
    GET<{ tools: ToolChip[] }>(`/agents/${projectId}/${agentId}/tools`),

  updateTools: (projectId: string, agentId: string, toolIds: string[]) =>
    PUT<{ tools: ToolChip[] }>(`/agents/${projectId}/${agentId}/tools`, { tool_ids: toolIds }),
},
```

---

## Query Keys (TanStack Query)

| Key | Endpoint | staleTime |
|-----|----------|-----------|
| `['tools', 'list', projectId]` | `GET /tools/{projectId}` | 30s |
| `['tools', 'detail', projectId, toolId]` | `GET /tools/{projectId}/{toolId}` | 60s |
| `['agents', agentId, 'tools']` | `GET /agents/{projectId}/{agentId}/tools` | 60s |
