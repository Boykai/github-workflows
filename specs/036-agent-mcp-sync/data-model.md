# Data Model: Agent MCP Sync

**Feature**: 036-agent-mcp-sync | **Date**: 2026-03-11

## Entities

### AgentFile

Represents a single `.github/agents/*.agent.md` file in the repository.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `path` | `str` | Relative path from repo root (e.g., `.github/agents/archivist.agent.md`) | Must match `*.agent.md` pattern |
| `sha` | `str` | GitHub file SHA for conditional updates | Required for PUT operations |
| `frontmatter` | `dict` | Parsed YAML frontmatter | Must parse via `yaml.safe_load()` |
| `body` | `str` | Markdown content after frontmatter | Preserved verbatim during sync |
| `name` | `str` | Agent display name (from frontmatter `name` key) | Optional (some files omit it) |
| `description` | `str` | Agent description (from frontmatter `description` key) | Optional |
| `tools` | `list[str]` | Tool access list (from frontmatter `tools` key) | Enforced as `["*"]` after sync |
| `mcp_servers` | `dict[str, dict]` | MCP server configurations (from frontmatter `mcp-servers` key) | Dict keyed by server name |
| `metadata` | `dict` | Metadata fields (from frontmatter `metadata` key) | Optional, preserved during sync |

**State transitions**:
- `unsynced` → `synced`: After sync process updates `tools` and `mcp-servers` fields
- `synced` → `dirty`: When user manually edits `tools` or `mcp-servers` after sync
- `dirty` → `synced`: On next sync trigger (re-enforces correct values)

### McpServerConfig

Represents a single MCP server entry within an agent file's `mcp-servers` field or the `mcp_configurations` database table.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `server_key` | `str` | Unique server identifier (e.g., `context7`, `CodeGraphContext`) | Unique within agent file |
| `type` | `str` | Server connection type | One of: `http`, `stdio`, `local`, `sse` |
| `url` | `str \| None` | Server endpoint URL | Required when `type` is `http` or `sse` |
| `command` | `str \| None` | Local command to execute | Required when `type` is `stdio` or `local` |
| `args` | `list[str] \| None` | Command arguments | Optional, for `stdio`/`local` types |
| `tools` | `list[str] \| str` | Tool filter for this server | `["*"]` or list of specific tool names |
| `headers` | `dict[str, str] \| None` | HTTP headers / env vars | Optional, for `http`/`sse` types |
| `builtin` | `bool` | Whether this is a built-in MCP | `True` for system-provided MCPs |

### SyncOperation

Represents a single execution of the agent MCP sync process.

| Field | Type | Description |
|-------|------|-------------|
| `trigger` | `str` | What initiated the sync: `startup`, `tool_toggle`, `agent_create`, `agent_update` |
| `active_mcps` | `dict[str, McpServerConfig]` | All MCPs to be synced (built-in + user-activated) |
| `agent_files` | `list[AgentFile]` | All agent files discovered in the repository |
| `files_updated` | `int` | Count of files that were modified |
| `files_skipped` | `int` | Count of files skipped (unparseable, etc.) |
| `warnings` | `list[str]` | Warnings generated during sync (e.g., tools overrides) |
| `errors` | `list[str]` | Errors encountered during sync |

### BuiltinMcpEntry

Represents a built-in MCP that is always included in every agent file.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Display name (e.g., `Context7`) |
| `server_key` | `str` | Unique server key (e.g., `context7`) |
| `config` | `McpServerConfig` | Full server configuration |

## Relationships

```text
SyncOperation ──reads──▶ mcp_configurations (DB table)
SyncOperation ──reads──▶ BUILTIN_MCPS (constant)
SyncOperation ──discovers──▶ AgentFile (via GitHub API)
SyncOperation ──updates──▶ AgentFile.mcp_servers
SyncOperation ──enforces──▶ AgentFile.tools = ["*"]
AgentFile.mcp_servers ──contains──▶ McpServerConfig (1:N)
BuiltinMcpEntry ──provides──▶ McpServerConfig
```

## Merge Logic

The sync operation merges MCP servers into each agent file using the following precedence:

1. **Built-in MCPs** (highest priority) — always present, cannot be overridden
2. **User-activated MCPs** (from `mcp_configurations` where `is_active = 1`) — added on activation, removed on deactivation
3. **Existing per-agent MCPs** (from agent file frontmatter) — preserved if not conflicting with built-in or activated MCPs

**Deduplication**: By `server_key`. If a server key appears in multiple sources, the highest-priority source wins.

**Removal**: When an MCP is deactivated, its server key is removed from all agent files. Built-in MCPs are never removed.
