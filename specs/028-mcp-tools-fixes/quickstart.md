# Quickstart: Tools Page — Fix MCP Bugs, Broken Link, Repo Name Display, Discover Button & Auto-populate MCP Name

**Feature**: 028-mcp-tools-fixes | **Date**: 2026-03-07

## Prerequisites

- Node.js 20.19+ (or Node.js 22+) and npm
- Python 3.12+
- The repository cloned and on the feature branch

```bash
git checkout 028-mcp-tools-fixes
```

## Setup

### Backend

```bash
cd backend
pip install -e ".[dev]"
uvicorn src.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# App available at http://localhost:5173
```

## Files to Modify

### Frontend

| File | Changes |
|------|---------|
| `frontend/src/pages/ToolsPage.tsx` | Fix MCP docs link URL, change repo display to `repo.name`, add Discover button |
| `frontend/src/components/tools/UploadMcpModal.tsx` | Fix `validateMcpJson()` type inference, add auto-populate name `useEffect` |

### Backend

| File | Changes |
|------|---------|
| `backend/src/services/tools/service.py` | Fix `validate_mcp_config()` type inference, update `_extract_endpoint_url()` |

## Implementation Order

### Step 1: Backend Validation Fix (Critical — Bug Fix)

**File**: `backend/src/services/tools/service.py`

1. In `validate_mcp_config()`, find the existing strict type check on `server_config.get("type")` and replace it:

```python
# Before:
server_type = server_config.get("type")
if server_type not in ("http", "stdio"):
    return False, f"Server '{server_name}' must have 'type' of 'http' or 'stdio'"

# After:
server_type = server_config.get("type")
if server_type is not None:
    if server_type not in ("http", "stdio"):
        return False, f"Server '{server_name}' has invalid type '{server_type}'; must be 'http' or 'stdio'"
elif isinstance(server_config.get("command"), str) and server_config["command"]:
    server_type = "stdio"
elif isinstance(server_config.get("url"), str) and server_config["url"]:
    server_type = "http"
else:
    return False, f"Server '{server_name}' must have 'type', 'command', or 'url'"
```

2. In `_extract_endpoint_url()`, update the type-based endpoint extraction logic to handle configs without explicit type:

```python
# Before:
if cfg.get("type") == "http":
    return cfg.get("url", "")
if cfg.get("type") == "stdio":
    return cfg.get("command", "")

# After:
cfg_type = cfg.get("type")
if cfg_type == "http" or (cfg_type is None and cfg.get("url")):
    return cfg.get("url", "")
if cfg_type == "stdio" or (cfg_type is None and cfg.get("command")):
    return cfg.get("command", "")
```

### Step 2: Frontend Validation Fix (UX — Mirrors Backend)

**File**: `frontend/src/components/tools/UploadMcpModal.tsx`

1. In `validateMcpJson()`, find the strict type check on `serverCfg.type` and replace it:

```typescript
// Before:
const serverType = serverCfg.type;
if (serverType !== 'http' && serverType !== 'stdio') {
  return `Server '${name}' must have 'type' of 'http' or 'stdio'`;
}

// After:
let resolvedType = serverCfg.type as string | undefined;
if (resolvedType !== undefined) {
  if (resolvedType !== 'http' && resolvedType !== 'stdio') {
    return `Server '${name}' has invalid type '${resolvedType}'; must be 'http' or 'stdio'`;
  }
} else if (typeof serverCfg.command === 'string' && serverCfg.command.length > 0) {
  resolvedType = 'stdio';
} else if (typeof serverCfg.url === 'string' && serverCfg.url.length > 0) {
  resolvedType = 'http';
} else {
  return `Server '${name}' must have 'type', 'command', or 'url'`;
}
```

2. Update subsequent checks to use `resolvedType`:
```typescript
if (resolvedType === 'http' && !serverCfg.url) { ... }
if (resolvedType === 'stdio' && !serverCfg.command) { ... }
```

### Step 3: Auto-Populate MCP Name

**File**: `frontend/src/components/tools/UploadMcpModal.tsx`

Add state and `useEffect` after the existing `duplicateWarning` effect:

```typescript
const [multiServerWarning, setMultiServerWarning] = useState<string | null>(null);

useEffect(() => {
  if (!configContent.trim()) {
    setMultiServerWarning(null);
    return;
  }
  try {
    const parsed = JSON.parse(configContent);
    const servers = parsed?.mcpServers;
    if (typeof servers === 'object' && servers !== null && !Array.isArray(servers)) {
      const keys = Object.keys(servers);
      if (keys.length > 0 && name.trim() === '') {
        setName(keys[0]);
      }
      if (keys.length > 1) {
        setMultiServerWarning(`Multiple servers detected; using '${keys[0]}'`);
      } else {
        setMultiServerWarning(null);
      }
    } else {
      setMultiServerWarning(null);
    }
  } catch {
    setMultiServerWarning(null);
  }
}, [configContent]);
```

Display the `multiServerWarning` below the name field's `duplicateWarning`.

### Step 4: Fix ToolsPage — Docs Link, Repo Display, Discover Button

**File**: `frontend/src/pages/ToolsPage.tsx`

1. **Docs link**: Replace the URL string:
   - Old: `https://docs.github.com/en/copilot/customizing-copilot/extending-the-functionality-of-github-copilot-in-your-organization`
   - New: `https://docs.github.com/copilot/customizing-copilot/using-model-context-protocol`

2. **Repo display**: Change two occurrences of `` `${repo.owner}/${repo.name}` `` to `repo.name`.

3. **Discover button**: Add after the "MCP docs" button:
```tsx
<Button variant="outline" size="lg" asChild>
  <a href="https://github.com/mcp" target="_blank" rel="noopener noreferrer" aria-label="Discover MCP integrations on GitHub">
    Discover
  </a>
</Button>
```

## Verification

After applying all changes, verify:

1. **Type Inference (Bug Fix)**:
   - Upload a config with `command`/`args` but no `type` → accepted without error
   - Upload a config with `url` but no `type` → accepted without error
   - Upload a config with explicit `type: "http"` + `url` → accepted (existing behavior)
   - Upload a config with explicit `type: "stdio"` + `command` → accepted (existing behavior)
   - Upload a config with no `type`, no `command`, no `url` → clear error message

2. **Auto-Populate Name**:
   - Leave name empty → paste MCP JSON → name auto-fills with first server key
   - Enter a name → paste MCP JSON → name remains unchanged
   - Paste JSON with multiple servers → warning shown, first key used

3. **Docs Link**: Click "MCP docs" → navigates to GitHub Copilot MCP docs (valid page)

4. **Repository Display**: Repository bubble shows repo name (e.g., `github-workflows`), not owner or `owner/repo`

5. **Discover Button**: Click "Discover" → opens `https://github.com/mcp` in new tab

## Running Tests

### Frontend

```bash
cd frontend
npx vitest run                    # All unit tests
npx tsc --noEmit                  # Type check
npx eslint src/                   # Lint check
```

### Backend

```bash
cd backend
pip install -e ".[dev]"
pytest                            # All tests
ruff check src/                   # Lint check
pyright src/                      # Type check
```
