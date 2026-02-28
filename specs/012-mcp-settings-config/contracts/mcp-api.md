# API Contracts: MCP Configuration Management

**Feature**: 012-mcp-settings-config  
**Date**: 2026-02-28  
**Base Path**: `/api/v1/settings/mcps`

All endpoints require a valid session cookie (GitHub OAuth). Responses use standard JSON. Authentication failures return 401.

---

## GET /settings/mcps

**Description**: List all MCP configurations for the authenticated user.

**Auth**: Required (session cookie via `get_session_dep`)

### Response 200 OK

```json
{
  "mcps": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "My MCP Server",
      "endpoint_url": "https://mcp.example.com/api",
      "is_active": true,
      "created_at": "2026-02-28T01:00:00Z",
      "updated_at": "2026-02-28T01:00:00Z"
    }
  ],
  "count": 1
}
```

### Response 401 Unauthorized

```json
{
  "detail": "No session cookie"
}
```

---

## POST /settings/mcps

**Description**: Add a new MCP configuration for the authenticated user.

**Auth**: Required (session cookie via `get_session_dep`)

### Request Body

```json
{
  "name": "My MCP Server",
  "endpoint_url": "https://mcp.example.com/api"
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `name` | string | Yes | 1–100 characters |
| `endpoint_url` | string | Yes | Valid HTTP(S) URL, 1–2048 characters, no private IPs |

### Response 201 Created

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "My MCP Server",
  "endpoint_url": "https://mcp.example.com/api",
  "is_active": true,
  "created_at": "2026-02-28T01:00:00Z",
  "updated_at": "2026-02-28T01:00:00Z"
}
```

### Response 400 Bad Request — Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "String should have at least 1 character",
      "type": "string_too_short"
    }
  ]
}
```

### Response 400 Bad Request — SSRF Blocked

```json
{
  "detail": "URL points to a private or reserved IP address"
}
```

### Response 409 Conflict — Limit Exceeded

```json
{
  "detail": "Maximum of 25 MCP configurations per user reached"
}
```

### Response 401 Unauthorized

```json
{
  "detail": "No session cookie"
}
```

---

## DELETE /settings/mcps/{mcp_id}

**Description**: Remove an MCP configuration. Only the owning user can delete their own MCPs.

**Auth**: Required (session cookie via `get_session_dep`)

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `mcp_id` | string (UUID) | The unique identifier of the MCP to delete |

### Response 200 OK

```json
{
  "message": "MCP configuration deleted"
}
```

### Response 404 Not Found

```json
{
  "detail": "MCP configuration not found"
}
```

### Response 401 Unauthorized

```json
{
  "detail": "No session cookie"
}
```

---

## Error Handling

All endpoints follow the existing error response patterns:

| Status | Meaning | When |
|--------|---------|------|
| 400 | Bad Request | Validation failure, SSRF blocked URL |
| 401 | Unauthorized | No session cookie, expired session |
| 404 | Not Found | MCP ID doesn't exist or doesn't belong to user |
| 409 | Conflict | Per-user MCP limit exceeded (25) |
| 500 | Internal Server Error | Unexpected server failure |

### Authentication Error Flow

When a 401 is returned during any MCP operation, the frontend should:
1. Display an inline message: "Your session has expired. Please sign in again."
2. Provide a re-authentication link/button that triggers `authApi.login()`.
