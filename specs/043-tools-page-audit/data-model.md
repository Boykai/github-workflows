# Data Model: Tools Page Audit

**Feature**: `043-tools-page-audit` | **Date**: 2026-03-16 | **Plan**: [plan.md](plan.md)

## Overview

This audit does not introduce new data models. The existing entity definitions are stable and well-typed. This document catalogs the current data model as it relates to the Tools page, identifies any type safety gaps, and documents the relationships between entities for implementation reference.

## Entities

### McpToolConfig

The primary entity representing a user-managed MCP server configuration.

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `id` | `string` | No | Unique identifier |
| `name` | `string` | No | Display name for the tool |
| `description` | `string` | No | Tool description |
| `endpoint_url` | `string` | No | MCP server endpoint URL |
| `config_content` | `string` | No | JSON configuration content |
| `sync_status` | `McpToolSyncStatus` | No | One of: `'synced'`, `'pending'`, `'error'` |
| `sync_error` | `string` | No | Error message when sync_status is 'error' (empty string otherwise) |
| `synced_at` | `string \| null` | Yes | ISO 8601 timestamp of last successful sync |
| `github_repo_target` | `string` | No | Target repository path for syncing |
| `is_active` | `boolean` | No | Whether the tool is active |
| `created_at` | `string` | No | ISO 8601 creation timestamp |
| `updated_at` | `string` | No | ISO 8601 last update timestamp |

**Validation Rules**:
- `name` must be unique per project (enforced by backend; frontend shows duplicate warning)
- `config_content` must be valid JSON with an `mcpServers` key containing at least one server entry
- `github_repo_target` should match an existing repository path

**State Transitions**:
```
[created] → pending
pending → synced (on successful sync)
pending → error (on failed sync)
synced → pending (on re-sync trigger or config update)
error → pending (on re-sync trigger)
```

### McpToolConfigCreate

Input entity for creating a new tool.

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `name` | `string` | No | Display name |
| `description` | `string` | No | Description |
| `config_content` | `string` | No | JSON configuration |
| `github_repo_target` | `string` | No | Target repository path |

### McpToolConfigUpdate

Input entity for updating an existing tool.

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `name` | `string` | Yes (optional) | Updated display name |
| `description` | `string` | Yes (optional) | Updated description |
| `config_content` | `string` | Yes (optional) | Updated JSON configuration |
| `github_repo_target` | `string` | Yes (optional) | Updated target repository path |

### McpToolConfigListResponse

API response wrapper for tool listings.

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `tools` | `McpToolConfig[]` | No | Array of tool configurations |
| `count` | `number` | No | Total count of tools |

### RepoMcpServerConfig

A server configuration read from repository files.

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `name` | `string` | No | Server name |
| `config` | `Record<string, unknown>` | No | Server configuration object |
| `source_paths` | `string[]` | No | File paths where this config was found |

### RepoMcpServerUpdate

Input entity for updating a repo MCP server.

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `name` | `string` | No | Server name |
| `config_content` | `string` | No | Updated JSON configuration |

### RepoMcpConfigResponse

API response for repository-level MCP configuration.

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `paths_checked` | `string[]` | No | Repository paths that were scanned |
| `available_paths` | `string[]` | No | Paths where MCP config files exist |
| `primary_path` | `string \| null` | Yes | Primary config file path |
| `servers` | `RepoMcpServerConfig[]` | No | Array of discovered server configs |

### McpPreset

A pre-configured MCP tool template from the gallery.

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `id` | `string` | No | Unique identifier |
| `name` | `string` | No | Preset name |
| `description` | `string` | No | Preset description |
| `category` | `string` | No | Preset category (e.g., "Development", "Testing") |
| `icon` | `string` | No | Icon identifier |
| `config_content` | `string` | No | Pre-configured JSON content |

### McpPresetListResponse

API response wrapper for preset listings.

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `presets` | `McpPreset[]` | No | Array of presets |
| `count` | `number` | No | Total count of presets |

### ToolChip

Lightweight tool reference used in agent assignments and delete results.

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `id` | `string` | No | Tool identifier |
| `name` | `string` | No | Tool display name |
| `description` | `string` | No | Tool description |

### ToolDeleteResult

API response for tool deletion.

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `success` | `boolean` | No | Whether deletion succeeded |
| `deleted_id` | `string \| null` | Yes | ID of deleted tool (null on dry run) |
| `affected_agents` | `ToolChip[]` | No | Agents that had this tool assigned |

### McpToolSyncResult

API response for tool sync operation.

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `id` | `string` | No | Tool identifier |
| `sync_status` | `McpToolSyncStatus` | No | Updated sync status |
| `sync_error` | `string` | No | Error message if sync failed |
| `synced_at` | `string \| null` | Yes | Timestamp of sync |
| `synced_paths` | `string[]` | No | Repository paths that were synced |

## Entity Relationships

```text
Project (1) ──── has many ──── (N) McpToolConfig
Project (1) ──── has one  ──── (1) RepoMcpConfigResponse
McpToolConfig (N) ── assigned to ── (N) Agent (via ToolChip)
McpPreset (1) ──── templates ──── (1) McpToolConfigCreate (via selection)
RepoMcpConfigResponse (1) ── contains ── (N) RepoMcpServerConfig
```

## Type Safety Audit

| Issue | Location | Status |
|-------|----------|--------|
| Non-null assertion on `projectId!` | `useTools.ts` mutation functions | ⚠️ Safe at runtime (guarded by `enabled: !!projectId`) but violates strict type safety. Consider early return guard. |
| Non-null assertion on `projectId!`, `agentId!` | `useAgentTools.ts` query/mutation functions | ⚠️ Same pattern as above. |
| `Record<string, unknown>` for config | `RepoMcpServerConfig.config` | ✅ Acceptable — config shape varies per server type |
| `error as Error` type assertion | `useTools.ts` error handling | ⚠️ Should use type guard instead of assertion |
| All other types | `src/types/index.ts` | ✅ Properly typed; aligned with backend Pydantic models |

## No New Entities Required

This audit focuses on improving the existing Tools page implementation. All entities listed above are already defined in `src/types/index.ts` and are correct. The audit work involves:

1. **Better use of existing types** — eliminate `any` and type assertions
2. **Proper null handling** — replace non-null assertions with runtime guards
3. **Consistent error typing** — use `ApiError` type consistently across hooks
4. **No schema changes** — backend API contracts remain unchanged
