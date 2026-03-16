# Component Contracts: Tools Page Audit

**Feature**: `043-tools-page-audit` | **Date**: 2026-03-16 | **Plan**: [plan.md](../plan.md)

## Overview

This document defines the component API contracts for all changes in the Tools page audit. Since this is an audit of existing code (not new feature development), contracts focus on the **changed behavior** of existing components and the **expected props/callbacks** for shared components being adopted.

## Shared Component Usage Contracts

### CelestialLoader

**Source**: `src/components/common/CelestialLoader.tsx`  
**Used in**: RepoConfigPanel, McpPresetsGallery, ToolsPanel (tools list loading)

```typescript
interface CelestialLoaderProps {
  size?: 'sm' | 'md' | 'lg';  // Default: 'md'
  label?: string;               // Screen-reader label (default: 'Loading…')
  className?: string;            // Additional CSS classes
}

// Usage pattern for section-level loading:
<CelestialLoader size="md" label="Loading MCP tools" />
```

**Contract**: When a data-dependent section is loading (`isLoading === true`), render `<CelestialLoader size="md" />` instead of the section content. Never show a blank area while data is loading.

---

### ConfirmationDialog

**Source**: `src/components/ui/confirmation-dialog.tsx`  
**Used in**: ToolsPanel (tool delete, repo server delete)

```typescript
interface ConfirmationDialogProps {
  isOpen: boolean;
  title: string;
  description: string;
  variant: 'danger' | 'warning' | 'info';  // Default: 'danger'
  confirmLabel: string;
  cancelLabel: string;
  isLoading: boolean;
  error: string | null;
  onConfirm: () => void;
  onCancel: () => void;
}

// Usage pattern for destructive tool delete (via useConfirmation hook):
const { confirm } = useConfirmation();
const confirmed = await confirm({
  title: 'Delete Tool',
  description: `Are you sure you want to delete "${toolName}"? ${affectedAgents.length > 0 ? `This will affect ${affectedAgents.length} agent(s): ${agentNames}.` : ''}`,
  confirmLabel: 'Delete Tool',
  variant: 'danger',
  onConfirm: async () => { await deleteTool({ toolId, confirm: true }); },
});
```

**Contract**: All destructive actions (delete tool, delete repo server) MUST use ConfirmationDialog. The dialog MUST display:
1. The name of the item being deleted
2. A list of affected agents (if any) obtained from the first delete API call
3. A "Delete" confirm button with destructive variant
4. Loading state on the confirm button while the delete is in progress

---

### Tooltip (for truncated text)

**Source**: `src/components/ui/tooltip.tsx`  
**Used in**: ToolCard (name, description, URL), RepoConfigPanel (server names)

```typescript
interface TooltipProps {
  contentKey?: string;          // Registry key (primary — use centralized registry)
  content?: string;             // Direct tooltip text (escape-hatch for dynamic content)
  title?: string;               // Direct title (used with `content`)
  learnMoreUrl?: string;        // Direct learn-more link (used with `content`)
  side?: 'top' | 'right' | 'bottom' | 'left';
  align?: 'start' | 'center' | 'end';
  delayDuration?: number;       // Override default hover delay (ms)
  children: ReactNode;
}

// Usage pattern for truncated text:
<Tooltip content={tool.name}>
  <span className="truncate max-w-[200px]">{tool.name}</span>
</Tooltip>

// Usage pattern for registry-based tooltip:
<Tooltip contentKey="tools.card.editButton">
  <Button>Edit</Button>
</Tooltip>
```

**Contract**: Any text that is visually truncated (via `truncate` or `text-ellipsis`) MUST be wrapped in a Tooltip that shows the full text on hover/focus.

---

## Modified Component Contracts

### ToolsPanel (modified)

**Changes**:
1. Replace inline delete confirmation with `<ConfirmationDialog>`
2. Add repo server delete confirmation
3. Add success feedback for mutations
4. Format error messages to standard pattern
5. Add rate-limit error detection

**New state shape** (additions):

```typescript
// Delete confirmation state
const [deleteTarget, setDeleteTarget] = useState<{
  type: 'tool' | 'repoServer';
  id: string;
  name: string;
  affectedAgents?: ToolChip[];
} | null>(null);
```

**Error message format contract**:

```typescript
// All user-facing errors follow this pattern:
`Could not ${action}. ${reason}. ${nextStep}`

// Examples:
"Could not upload tool. The server name already exists. Try using a different name."
"Could not sync tool. Rate limit reached. Please wait a moment before trying again."
"Could not delete tool. An unexpected error occurred. Please try again."
```

---

### RepoConfigPanel (modified) ✅ Implemented

**Changes** (applied):
1. Replace "Loading…" text with `<CelestialLoader size="md" />`
2. Add retry button to error state
3. Pass `onRefresh` callback for retry action
4. Add `rawError` prop for rate-limit detection via `isRateLimitApiError()`

**New prop**: `rawError?: unknown` — Raw error object passed from the hook to enable rate-limit detection.

**Implemented error state**:

```typescript
<div className="flex flex-col items-center gap-3 rounded-2xl border border-destructive/30 bg-destructive/5 p-6 text-center">
  <AlertCircle className="h-5 w-5 text-destructive" aria-hidden="true" />
  <p className="text-sm text-destructive">
    {isRateLimit
      ? 'Rate limit reached. Please wait a few minutes before retrying.'
      : `Could not load repository config. ${error} Please try again.`}
  </p>
  <Button variant="outline" size="sm" onClick={onRefresh}>
    <RefreshCw className="mr-1.5 h-3.5 w-3.5" aria-hidden="true" />
    Retry
  </Button>
</div>
```

---

### McpPresetsGallery (modified) ✅ Implemented

**Changes** (applied):
1. Replace "Loading…" text with `<CelestialLoader size="md" />`
2. Add retry callback for error state
3. Add empty state when presets list is empty
4. Add `aria-label` to preset buttons
5. Add `rawError` prop for rate-limit detection via `isRateLimitApiError()`
6. Add `focus-visible` ring to preset buttons

**New props** (additions):

```typescript
interface McpPresetsGalleryProps {
  presets: McpPreset[];
  isLoading: boolean;
  error: string | null;
  rawError?: unknown;  // Raw error object for rate-limit detection via isRateLimitApiError()
  onSelectPreset: (preset: McpPreset) => void;
  onRetry?: () => void;  // NEW: retry callback for error state
}
```

---

### ToolCard (modified)

**Changes**:
1. Wrap truncated name/description in Tooltip
2. Format synced_at/created_at timestamps
3. Ensure SyncStatusBadge conveys status via text + color (not color alone)

**Timestamp format contract**:

```typescript
// < 24 hours old: relative time
"5 minutes ago"
"2 hours ago"

// ≥ 24 hours old: absolute date
"Mar 15, 2026"
"Jan 1, 2026"

// null synced_at:
"Never synced"
```

---

## API Contracts (unchanged)

The backend API contracts are **not modified** by this audit. All endpoints, request shapes, and response shapes remain as documented in `src/services/api.ts`. The audit only changes how the frontend consumes and displays this data.

| Endpoint | Method | Request | Response | Status |
|----------|--------|---------|----------|--------|
| `/tools/{projectId}` | GET | — | `McpToolConfigListResponse` | Unchanged |
| `/tools/{projectId}` | POST | `McpToolConfigCreate` | `McpToolConfig` | Unchanged |
| `/tools/{projectId}/{toolId}` | PUT | `McpToolConfigUpdate` | `McpToolConfig` | Unchanged |
| `/tools/{projectId}/{toolId}` | DELETE | `?confirm=true/false` | `ToolDeleteResult` | Unchanged |
| `/tools/{projectId}/{toolId}/sync` | POST | — | `McpToolSyncResult` | Unchanged |
| `/tools/{projectId}/repo-config` | GET | — | `RepoMcpConfigResponse` | Unchanged |
| `/tools/{projectId}/repo-config/{name}` | PUT | `RepoMcpServerUpdate` | `RepoMcpServerConfig` | Unchanged |
| `/tools/{projectId}/repo-config/{name}` | DELETE | — | `RepoMcpServerConfig` | Unchanged |
| `/tools/presets` | GET | — | `McpPresetListResponse` | Unchanged |

## Test Contracts

### Hook Tests (useToolsList)

```typescript
describe('useToolsList', () => {
  it('returns tools on successful fetch');
  it('returns empty array when project has no tools');
  it('reports loading state while fetching');
  it('reports error message on fetch failure');
  it('detects rate-limit errors');
  it('uploads tool and invalidates cache');
  it('syncs tool and invalidates cache');
  it('updates tool and invalidates cache');
  it('deletes tool with confirmation flow');
  it('handles delete with affected agents');
});
```

### Component Tests (ToolCard)

```typescript
describe('ToolCard', () => {
  it('renders tool name and description');
  it('shows sync status badge with text label');
  it('truncates long names with tooltip');
  it('calls onEdit when edit button clicked');
  it('calls onSync when sync button clicked');
  it('calls onDelete when delete button clicked');
  it('disables actions during sync/delete');
  it('shows relative timestamp for recent syncs');
  it('shows absolute timestamp for old syncs');
});
```

### Component Tests (ToolsPanel interactions)

```typescript
describe('ToolsPanel', () => {
  it('shows ConfirmationDialog on tool delete');
  it('shows affected agents in delete confirmation');
  it('shows ConfirmationDialog on repo server delete');
  it('shows success feedback after upload');
  it('shows formatted error on mutation failure');
  it('shows rate-limit message on 429 error');
  it('filters tools by search query');
});
```
