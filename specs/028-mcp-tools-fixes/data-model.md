# Data Model: Tools Page — Fix MCP Bugs, Broken Link, Repo Name Display, Discover Button & Auto-populate MCP Name

**Feature**: 028-mcp-tools-fixes | **Date**: 2026-03-07

## Overview

This feature involves **no new entities, no database changes, and no new TypeScript interfaces**. All changes are behavioral modifications to existing validation logic, display logic, and UI elements. This document describes the validation logic changes as the "data model" for this fix-oriented feature.

---

## Validation Logic Changes

### MCP Server Type Inference (Frontend + Backend)

The core data model change is in how the MCP server type is resolved during validation. The existing logic requires an explicit `type` field; the updated logic infers it from context.

#### Current Validation (Before Fix)

```
Input: server_config object
  ↓
  Is server_config.type === "http" OR "stdio"?
    YES → proceed to field-specific validation
    NO  → ERROR: "Server '{name}' must have 'type' of 'http' or 'stdio'"
```

#### Updated Validation (After Fix)

```
Input: server_config object
  ↓
  Does server_config have explicit "type"?
    YES → Is type === "http" OR "stdio"?
      YES → resolved_type = type
      NO  → ERROR: "Server '{name}' has invalid type '{type}'; must be 'http' or 'stdio'"
    NO → Does server_config have "command" (non-empty string)?
      YES → resolved_type = "stdio"
      NO  → Does server_config have "url" (non-empty string)?
        YES → resolved_type = "http"
        NO  → ERROR: "Server '{name}' must have 'type', 'command', or 'url'"
  ↓
  resolved_type === "http"?
    → Require "url" field (non-empty)
  resolved_type === "stdio"?
    → Require "command" field (non-empty)
```

#### Type Inference Truth Table

| `type` field | `command` field | `url` field | Resolved Type | Result |
|-------------|----------------|-------------|---------------|--------|
| `"http"` | any | any | `http` | ✅ Valid (requires `url`) |
| `"stdio"` | any | any | `stdio` | ✅ Valid (requires `command`) |
| `"invalid"` | any | any | — | ❌ Invalid type error |
| absent | `"docker"` | any | `stdio` | ✅ Inferred stdio |
| absent | `""` (empty) | any | — | ❌ Ambiguous error |
| absent | absent | `"https://..."` | `http` | ✅ Inferred http |
| absent | absent | `""` (empty) | — | ❌ Ambiguous error |
| absent | absent | absent | — | ❌ Ambiguous error |

---

## Affected Validation Functions

### Frontend: `validateMcpJson()` 

**Location**: `frontend/src/components/tools/UploadMcpModal.tsx`

**Current signature** (unchanged):
```typescript
function validateMcpJson(content: string): string | null
```

**Changed behavior**: The server type check is replaced with type inference logic matching the truth table above. The subsequent field-specific validation remains the same but uses the resolved type.

### Backend: `validate_mcp_config()`

**Location**: `backend/src/services/tools/service.py`

**Current signature** (unchanged):
```python
@staticmethod
def validate_mcp_config(config_content: str) -> tuple[bool, str]
```

**Changed behavior**: The `server_type` check is replaced with type inference logic matching the truth table above. The subsequent field-specific validation remains the same but uses the resolved type.

### Backend: `_extract_endpoint_url()`

**Location**: `backend/src/services/tools/service.py`

**Current signature** (unchanged):
```python
@staticmethod
def _extract_endpoint_url(config_content: str) -> str
```

**Changed behavior**: Currently checks `cfg.get("type") == "http"` and `cfg.get("type") == "stdio"` explicitly. Updated to also check for `url`/`command` fields when `type` is absent, matching the inference logic. This ensures the endpoint URL is correctly extracted from configs that use implicit types.

---

## Existing Entities (Unchanged)

The following entities are referenced but **not modified**:

- **McpToolConfig** (`frontend/src/types/index.ts`): No field changes. The `config_content` field continues to store raw JSON — the inference happens at validation time, not in the stored data.
- **McpToolConfigCreate** (`frontend/src/types/index.ts`): No field changes.
- **mcp_configurations table** (`backend/src/migrations/014_extend_mcp_tools.sql`): No schema changes. The `config_content` column stores the original JSON as-is — type inference is a validation-time concern.

---

## UI Data Flow Changes

### Auto-Populate Name Field

```
configContent state changes (paste or file upload)
  ↓
useEffect fires
  ↓
Parse configContent as JSON
  ↓
Extract Object.keys(parsed.mcpServers)[0] → serverName
  ↓
Is name field empty (name.trim() === "")?
  YES → setName(serverName)
  NO  → do nothing (preserve user input)
  ↓
Are there multiple keys in mcpServers?
  YES → show informational message: "Multiple servers detected; using '{serverName}'"
  NO  → no message
```

### Repository Display

```
Current: badge = `${repo.owner}/${repo.name}` → shows "Boykai/github-workflows"
Updated: badge = repo.name                    → shows "github-workflows"

Current: stats.Repository = `${repo.owner}/${repo.name}`
Updated: stats.Repository = repo.name
```

No changes to the `repo` data object itself — only the display template.
