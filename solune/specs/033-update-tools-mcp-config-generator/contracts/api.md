# API Contracts: Update Tools Page — GitHub.com MCP Configuration Generator

**Feature**: 033-update-tools-mcp-config-generator | **Date**: 2026-03-10

## Overview

This feature requires **no new API endpoints** and **no backend changes**. The configuration generator operates entirely on the frontend by consuming existing API responses.

## Existing Endpoints Used (No Changes)

### GET /tools/{project_id}

**Purpose**: Retrieve all MCP tool configurations for a project.
**Consumer**: `useToolsList` hook → `ToolsPanel` → `GitHubMcpConfigGenerator`

**Response**:

```json
{
  "tools": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "endpoint_url": "string",
      "config_content": "string (JSON)",
      "sync_status": "synced | pending | error",
      "sync_error": "string",
      "synced_at": "string | null",
      "github_repo_target": "string",
      "is_active": true,
      "created_at": "string",
      "updated_at": "string"
    }
  ],
  "count": 1
}
```

**Relevance**: The `tools` array is passed directly to `GitHubMcpConfigGenerator`. The component filters for `is_active === true` and extracts `config_content` JSON to build the merged MCP configuration.

### GET /tools/presets

**Purpose**: List available MCP presets for quick tool creation.
**Consumer**: `useMcpPresets` hook → `McpPresetsGallery`

**Relevance**: Presets are used to create new MCP tools, which then appear in the tools list and get included in the generated configuration.

## Client-Side Data Contract

### buildGitHubMcpConfig Function

**Input**:

```typescript
function buildGitHubMcpConfig(tools: McpToolConfig[]): {
  configJson: string;
  entries: McpServerEntry[];
}
```

**Output `configJson`** conforms to GitHub.com MCP schema:

```json
{
  "mcpServers": {
    "<server-key>": {
      "type": "http | sse | local | stdio",
      "url": "string (for http/sse)",
      "command": "string (for local/stdio)",
      "args": ["string[]"],
      "tools": ["string[] | '*'"],
      "headers": { "string": "string" },
      "env": { "string": "string" }
    }
  }
}
```

**Output `entries`** provides metadata for UI rendering:

```typescript
interface McpServerEntry {
  key: string;           // Server key in mcpServers
  config: Record<string, unknown>;  // Server config object
  builtin: boolean;      // true for Built-In MCPs
  sourceName: string;    // Display name of the source
}
```

### Merge Rules

1. User tool servers are added first (iteration order)
2. Duplicate server keys are resolved by first-occurrence-wins
3. Built-In MCPs are appended only if their `serverKey` is not already present
4. User tools can override Built-In MCPs by using the same server key

## Validation Constraints

| Constraint | Value | Source |
|-----------|-------|--------|
| Max tools per project | 25 | `backend/src/services/tools/service.py` |
| Max config_content size | 256 KB | `backend/src/services/tools/service.py` |
| Allowed server types | `http`, `stdio`, `local`, `sse` | `backend/src/services/tools/service.py` |
| config_content format | Valid JSON with `mcpServers` object | `backend/src/services/tools/service.py` |
