# API Contracts: Tools Page — Fix MCP Bugs, Broken Link, Repo Name Display, Discover Button & Auto-populate MCP Name

**Feature**: 028-mcp-tools-fixes | **Date**: 2026-03-07

## Overview

This feature modifies **no API endpoints**. All REST API contracts remain unchanged. The only backend change is in the validation logic within the `ToolsService.validate_mcp_config()` static method, which is called by the existing `POST /api/v1/tools/{project_id}` endpoint.

---

## Modified Validation Contract

### Upload MCP Tool Configuration

```
POST /api/v1/tools/{project_id}
```

**Endpoint contract unchanged** — same URL, same request/response schema, same error codes. The only change is in the **validation behavior** of the `config_content` field.

#### Previous Validation Behavior

The `config_content` JSON was validated with a strict requirement that each server entry must include an explicit `type` field:

```json
// ❌ REJECTED (no explicit type) — This is the reported bug
{
  "mcpServers": {
    "markitdown": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "markitdown-mcp:latest"]
    }
  }
}
// Error: "Server 'markitdown' must have 'type' of 'http' or 'stdio'"
```

#### Updated Validation Behavior

The `config_content` JSON now supports implicit type inference:

```json
// ✅ ACCEPTED (type inferred as stdio from command field)
{
  "mcpServers": {
    "markitdown": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "markitdown-mcp:latest"]
    }
  }
}

// ✅ ACCEPTED (type inferred as http from url field)
{
  "mcpServers": {
    "context7": {
      "url": "https://mcp.context7.com/mcp",
      "headers": {
        "CONTEXT7_API_KEY": "YOUR_API_KEY"
      }
    }
  }
}

// ✅ ACCEPTED (explicit type — existing behavior, unchanged)
{
  "mcpServers": {
    "sentry": {
      "type": "http",
      "url": "https://sentry.example.com/mcp"
    }
  }
}

// ❌ REJECTED (no type, command, or url — genuinely ambiguous)
{
  "mcpServers": {
    "broken": {
      "headers": {"key": "value"}
    }
  }
}
// Error: "Server 'broken' must have 'type', 'command', or 'url'"

// ❌ REJECTED (invalid explicit type)
{
  "mcpServers": {
    "bad": {
      "type": "websocket"
    }
  }
}
// Error: "Server 'bad' has invalid type 'websocket'; must be 'http' or 'stdio'"
```

#### Error Message Changes

| Scenario | Previous Error | Updated Error |
|----------|---------------|---------------|
| No `type`, has `command` | `"Server '{name}' must have 'type' of 'http' or 'stdio'"` | ✅ No error (inferred as stdio) |
| No `type`, has `url` | `"Server '{name}' must have 'type' of 'http' or 'stdio'"` | ✅ No error (inferred as http) |
| No `type`, no `command`, no `url` | `"Server '{name}' must have 'type' of 'http' or 'stdio'"` | `"Server '{name}' must have 'type', 'command', or 'url'"` |
| Invalid explicit `type` | `"Server '{name}' must have 'type' of 'http' or 'stdio'"` | `"Server '{name}' has invalid type '{type}'; must be 'http' or 'stdio'"` |

---

## Unchanged Endpoints

All other endpoints remain unchanged:

- `GET /api/v1/tools/{project_id}` — List tools
- `GET /api/v1/tools/{project_id}/{tool_id}` — Get tool
- `POST /api/v1/tools/{project_id}/{tool_id}/sync` — Sync tool
- `DELETE /api/v1/tools/{project_id}/{tool_id}` — Delete tool
- `GET /api/v1/agents/{project_id}/{agent_id}/tools` — Get agent tools
- `PUT /api/v1/agents/{project_id}/{agent_id}/tools` — Update agent tools
