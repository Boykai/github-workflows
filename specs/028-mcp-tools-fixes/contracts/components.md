# Component Contracts: Tools Page — Fix MCP Bugs, Broken Link, Repo Name Display, Discover Button & Auto-populate MCP Name

**Feature**: 028-mcp-tools-fixes | **Date**: 2026-03-07

## Overview

No new components are created. All changes modify existing component behavior. This document describes the behavioral changes for each affected component.

---

## Modified Components

### ToolsPage

**Location**: `frontend/src/pages/ToolsPage.tsx`
**Purpose**: Top-level page component for MCP tool management.

**Changes**:

#### 1. Fix MCP Documentation Link (FR-007)

**Before**:
```typescript
<a href="https://docs.github.com/en/copilot/customizing-copilot/extending-the-functionality-of-github-copilot-in-your-organization" target="_blank" rel="noopener noreferrer">
  MCP docs
</a>
```

**After**:
```typescript
<a href="https://docs.github.com/copilot/customizing-copilot/using-model-context-protocol" target="_blank" rel="noopener noreferrer">
  MCP docs
</a>
```

#### 2. Fix Repository Display (FR-008, FR-009)

**Before**:
```typescript
badge={repo ? `${repo.owner}/${repo.name}` : 'Awaiting repository'}
stats={[
  { label: 'Repository', value: repo ? `${repo.owner}/${repo.name}` : 'Unlinked' },
  // ...
]}
```

**After**:
```typescript
badge={repo ? repo.name : 'Awaiting repository'}
stats={[
  { label: 'Repository', value: repo ? repo.name : 'Unlinked' },
  // ...
]}
```

**Dynamic sizing**: The `CelestialCatalogHero` stat display already applies `truncate` CSS class for text overflow handling. The badge uses `rounded-full` container with `px-3 py-1` padding that adapts to content width. No additional sizing logic needed.

#### 3. Add Discover Button (FR-010, FR-011, FR-012)

**New element** added to the `actions` slot:

```typescript
<Button variant="outline" size="lg" asChild>
  <a
    href="https://github.com/mcp"
    target="_blank"
    rel="noopener noreferrer"
    aria-label="Discover MCP integrations on GitHub"
  >
    Discover
  </a>
</Button>
```

**Placement**: Third button in the actions row, after "Browse tools" (primary) and "MCP docs" (outline).

**Accessibility**:
- `aria-label`: "Discover MCP integrations on GitHub" — announces purpose to screen readers
- Keyboard-navigable: `<a>` inside `<Button>` inherits focus styles from the Button component
- `rel="noopener noreferrer"`: Security best practice for `target="_blank"` external links

---

### UploadMcpModal

**Location**: `frontend/src/components/tools/UploadMcpModal.tsx`
**Purpose**: Modal dialog for uploading/pasting MCP configuration JSON.

**Interface** (unchanged):
```typescript
interface UploadMcpModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpload: (data: McpToolConfigCreate) => Promise<unknown>;
  isUploading: boolean;
  uploadError: string | null;
  existingNames?: string[];
}
```

**Changes**:

#### 1. Fix Validation — Type Inference (FR-001, FR-002, FR-003, FR-013)

The `validateMcpJson()` function's server type check is updated to support implicit type inference.

**Before**:
```typescript
const serverType = serverCfg.type;
if (serverType !== 'http' && serverType !== 'stdio') {
  return `Server '${name}' must have 'type' of 'http' or 'stdio'`;
}
```

**After**:
```typescript
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

**Subsequent checks** use `resolvedType` instead of `serverType`:
```typescript
if (resolvedType === 'http' && !serverCfg.url) {
  return `HTTP server '${name}' must have a 'url' field`;
}
if (resolvedType === 'stdio' && !serverCfg.command) {
  return `Stdio server '${name}' must have a 'command' field`;
}
```

#### 2. Auto-Populate MCP Name (FR-004, FR-005, FR-006)

**New state**: `multiServerWarning` (informational message when multiple servers detected).

**New `useEffect`** added after the existing `duplicateWarning` effect:

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
}, [configContent]); // Only triggers on configContent changes, not on name changes
```

**Display**: The `multiServerWarning` is rendered as an informational note (amber styling, similar to `duplicateWarning`) below the Name field or above the config content section.

**Key behavior**:
- Only fires when `configContent` changes (not when `name` changes)
- Only sets name when `name.trim() === ''` — never overwrites user input
- Handles invalid JSON gracefully (no error, no auto-populate)
- Handles empty `mcpServers` gracefully (no auto-populate)

---

## Unchanged Components

The following components are referenced but **not modified**:

- **CelestialCatalogHero** (`frontend/src/components/common/CelestialCatalogHero.tsx`): No changes. Its existing `badge`, `stats`, and `actions` props already support the modified data.
- **ToolsPanel** (`frontend/src/components/tools/ToolsPanel.tsx`): No changes.
- **ToolCard** (`frontend/src/components/tools/ToolCard.tsx`): No changes.
- **ToolSelectorModal** (`frontend/src/components/tools/ToolSelectorModal.tsx`): No changes.
- **ToolChips** (`frontend/src/components/tools/ToolChips.tsx`): No changes.
