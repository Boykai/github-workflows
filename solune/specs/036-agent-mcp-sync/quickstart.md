# Quickstart: Agent MCP Sync

**Feature**: 036-agent-mcp-sync | **Date**: 2026-03-11

## Overview

This feature adds automatic synchronization of MCP (Model Context Protocol) server configurations across all agent definition files (`.github/agents/*.agent.md`). When MCPs are activated/deactivated on the Tools page or built-in MCPs are defined, all agent files are updated to reflect the current set of available MCPs. Additionally, `tools: ["*"]` is enforced on every agent file to ensure unrestricted tool access.

## Key Components

### 1. Backend: `agent_mcp_sync.py` (New Module)

The centralized sync utility that:
- Discovers all `.agent.md` files in `.github/agents/` via GitHub Contents API
- Reads each file's YAML frontmatter
- Merges active MCPs (built-in + user-activated) into the `mcp-servers` field
- Enforces `tools: ["*"]` on every file
- Writes back only files that changed (idempotent)

```python
# Usage in backend code:
from backend.src.services.agents.agent_mcp_sync import sync_agent_mcps

result = await sync_agent_mcps(
    owner="org",
    repo="repo",
    project_id="proj_123",
    access_token="ghp_...",
    trigger="tool_toggle",
)
# result.files_updated == 15
# result.warnings == ["archivist.agent.md: tools overridden from ['search'] to ['*']"]
```

### 2. Trigger Points

| Trigger | Location | When |
|---------|----------|------|
| Tool activation/deactivation | `tools/service.py` → `sync_tool_to_github()` | After MCP config is synced to `mcp.json` |
| Agent creation | `agents/service.py` → `create_agent()` | After agent files are committed |
| Agent update | `agents/service.py` → `update_agent()` | After agent files are committed |
| App startup | `startup.py` | On application initialization |

### 3. Frontend: Cache Invalidation

After a sync completes, the frontend invalidates agent-related query caches so the UI reflects the updated `mcp-servers` and `tools` fields:

```typescript
// In useTools.ts, after sync mutation:
queryClient.invalidateQueries({ queryKey: agentKeys.list(projectId) });
```

## Architecture

```text
┌──────────────────────────────────────────────────────────┐
│                    Sync Triggers                          │
│  ┌─────────┐  ┌───────────┐  ┌──────────┐  ┌─────────┐ │
│  │ Startup │  │Tool Toggle│  │Agent CRUD│  │ Manual  │  │
│  └────┬────┘  └─────┬─────┘  └────┬─────┘  └────┬────┘ │
│       │             │              │              │       │
│       └─────────────┴──────┬───────┴──────────────┘      │
│                            ▼                              │
│                ┌───────────────────────┐                  │
│                │  sync_agent_mcps()    │                  │
│                │  (agent_mcp_sync.py)  │                  │
│                └───────────┬───────────┘                  │
│                            │                              │
│              ┌─────────────┼─────────────┐                │
│              ▼             ▼             ▼                │
│     ┌──────────────┐ ┌──────────┐ ┌──────────────┐      │
│     │  BUILTIN_MCPS│ │ DB Query │ │ GitHub API   │      │
│     │  (constant)  │ │ (active  │ │ (agent files)│      │
│     │              │ │  MCPs)   │ │              │      │
│     └──────┬───────┘ └────┬─────┘ └──────┬───────┘      │
│            │              │              │                │
│            └──────────────┼──────────────┘                │
│                           ▼                               │
│              ┌─────────────────────────┐                  │
│              │  Merge & Deduplicate    │                  │
│              │  • Built-in MCPs first  │                  │
│              │  • User MCPs second     │                  │
│              │  • Enforce tools: ["*"] │                  │
│              └────────────┬────────────┘                  │
│                           ▼                               │
│              ┌─────────────────────────┐                  │
│              │  Write Changed Files    │                  │
│              │  via GitHub Contents API│                  │
│              └─────────────────────────┘                  │
└──────────────────────────────────────────────────────────┘
```

## Development Steps

1. **Create `agent_mcp_sync.py`** — Define `BUILTIN_MCPS`, implement `sync_agent_mcps()` function
2. **Add sync API endpoint** — `POST /agents/{project_id}/sync-mcps`
3. **Wire trigger in `tools/service.py`** — Call sync after `sync_tool_to_github()` completes
4. **Wire trigger in `agents/service.py`** — Call sync after `create_agent()` and `update_agent()`
5. **Wire startup trigger** — Call sync on app initialization
6. **Frontend cache invalidation** — Invalidate agent queries after tool sync
7. **Add unit tests** — Test sync logic with mock agent files and MCP configurations

## Validation

```bash
# Run backend tests
cd backend && python -m pytest tests/unit/test_agent_mcp_sync.py -v

# Run frontend tests
cd frontend && npx vitest run --reporter=verbose
```
