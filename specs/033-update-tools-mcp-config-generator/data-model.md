# Data Model: Update Tools Page — GitHub.com MCP Configuration Generator

**Feature**: 033-update-tools-mcp-config-generator | **Date**: 2026-03-10

## Overview

This feature introduces no new database entities or backend models. All data transformations occur on the frontend using existing types and API responses. The data model below documents the entities consumed and produced by the configuration generator.

## Existing Entities (No Changes)

### McpToolConfig

**Source**: `frontend/src/types/index.ts`, `backend/src/models/tools.py`
**Role**: Primary input — represents a user's MCP tool configuration stored in the project.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique tool identifier |
| `name` | `string` | Display name for the tool |
| `description` | `string` | Tool description |
| `endpoint_url` | `string` | MCP endpoint URL |
| `config_content` | `string` | Full JSON MCP configuration (contains `mcpServers` object) |
| `sync_status` | `'synced' \| 'pending' \| 'error'` | GitHub sync status |
| `sync_error` | `string` | Last sync error message |
| `synced_at` | `string \| null` | ISO 8601 timestamp of last successful sync |
| `github_repo_target` | `string` | Target repository (owner/repo format) |
| `is_active` | `boolean` | Whether the tool is currently active |
| `created_at` | `string` | ISO 8601 creation timestamp |
| `updated_at` | `string` | ISO 8601 last update timestamp |

**Validation rules**: `config_content` must be valid JSON with a top-level `mcpServers` object. Max size: 256 KB. Max tools per project: 25.

### McpPreset

**Source**: `frontend/src/types/index.ts`, `backend/src/services/tools/presets.py`
**Role**: Read-only preset definitions for quick tool creation.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Preset identifier |
| `name` | `string` | Display name |
| `description` | `string` | Preset description |
| `category` | `string` | Category grouping |
| `icon` | `string` | Lucide icon name |
| `config_content` | `string` | Pre-built MCP JSON configuration |

## New Frontend-Only Types

### BuiltInMcp

**Source**: `frontend/src/lib/buildGitHubMcpConfig.ts`
**Role**: Defines a built-in MCP that is always included in the generated configuration.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `string` | Display name (e.g., "Context7") |
| `serverKey` | `string` | Key used in the `mcpServers` object (e.g., "context7") |
| `config` | `Record<string, unknown>` | MCP server configuration object |

**Instances** (hardcoded constant `BUILTIN_MCPS`):

| Name | Server Key | Type | Connection |
|------|-----------|------|------------|
| Context7 | `context7` | `http` | `https://mcp.context7.com/mcp` |
| Code Graph Context | `CodeGraphContext` | `local` | `uvx --from codegraphcontext cgc mcp start` |

### McpServerEntry

**Source**: `frontend/src/lib/buildGitHubMcpConfig.ts`
**Role**: Intermediate representation of a resolved MCP server entry in the merged configuration.

| Field | Type | Description |
|-------|------|-------------|
| `key` | `string` | Server key in the `mcpServers` object |
| `config` | `Record<string, unknown>` | Server configuration object |
| `builtin` | `boolean` | `true` if this is a Built-In MCP, `false` if from user tools |
| `sourceName` | `string` | Display name of the source (tool name or built-in name) |

## Data Flow

```text
┌─────────────────────────────────────────────────────────┐
│                    ToolsPanel                            │
│                                                         │
│  useToolsList(projectId) ──> tools: McpToolConfig[]     │
│           │                                             │
│           ▼                                             │
│  ┌─────────────────────────────────┐                    │
│  │ GitHubMcpConfigGenerator        │                    │
│  │                                 │                    │
│  │  props.tools ──filter(active)──┐│                    │
│  │                                ││                    │
│  │  buildGitHubMcpConfig(active)  ││                    │
│  │       │                        ││                    │
│  │       ▼                        ││                    │
│  │  ┌──────────────────────┐      ││                    │
│  │  │ 1. Extract servers   │      ││                    │
│  │  │    from each tool    │      ││                    │
│  │  │                      │      ││                    │
│  │  │ 2. Deduplicate keys  │      ││                    │
│  │  │    (first wins)      │      ││                    │
│  │  │                      │      ││                    │
│  │  │ 3. Merge built-in    │      ││                    │
│  │  │    MCPs (if no key   │      ││                    │
│  │  │    conflict)         │      ││                    │
│  │  │                      │      ││                    │
│  │  │ 4. Serialize to JSON │      ││                    │
│  │  └──────────────────────┘      ││                    │
│  │       │                        ││                    │
│  │       ▼                        ││                    │
│  │  { configJson, entries }       ││                    │
│  │       │          │             ││                    │
│  │       ▼          ▼             ││                    │
│  │  Code Block   Entry List       ││                    │
│  │  (readonly)   (with badges)    ││                    │
│  └─────────────────────────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

## State Transitions

The config generator component is stateless with respect to the MCP data. The only local state is the `copied` boolean for clipboard feedback.

### Tool Activation State Machine

```text
[Tool Created] ──> is_active: true ──> Included in config
                                            │
                                    user toggles off
                                            │
                                            ▼
                                   is_active: false ──> Excluded from config
                                            │
                                    user toggles on
                                            │
                                            ▼
                                   is_active: true ──> Included in config
```

### Config Generation Pipeline

```text
Input: McpToolConfig[] (all project tools)
  │
  ├─ Filter: is_active === true
  │
  ├─ For each active tool:
  │   └─ Parse config_content JSON
  │   └─ Extract mcpServers entries
  │   └─ Skip if malformed JSON or missing mcpServers
  │
  ├─ Deduplicate: First occurrence of each server key wins
  │
  ├─ Append Built-In MCPs (only if key not already present)
  │
  └─ Output: { configJson: string, entries: McpServerEntry[] }
```

## Relationships

```text
McpToolConfig (1) ──contains──> (N) MCP Server Entries (via config_content JSON)
BuiltInMcp (N) ──always merged──> Generated Config
McpServerEntry (N) ──aggregated into──> Final mcpServers JSON
```

No new database tables, columns, or migrations are required for this feature.
