# Component Contracts: Add Tools Page with MCP Configuration Upload and Agent Tool Selection

**Feature**: 027-mcp-tools-page | **Date**: 2026-03-07

## New Components

### ToolsPage

**Location**: `frontend/src/pages/ToolsPage.tsx`
**Purpose**: Top-level page component for MCP tool management. Mirrors the `AgentsPage.tsx` layout.

```typescript
// No props — route component
// Uses hooks: useToolsList, useProjectContext
```

**Behavior**:
- Renders `CelestialCatalogHero` header with Tools-specific copy (title: "MCP Tools", description about managing MCP configurations)
- Shows "Select a project" prompt when no project is selected (mirrors `AgentsPage` behavior)
- Main content area renders `ToolsPanel` component
- Follows same two-column layout pattern as `AgentsPage`

---

### ToolsPanel

**Location**: `frontend/src/components/tools/ToolsPanel.tsx`
**Purpose**: Main panel containing the tool catalog with search, filter, and upload action. Mirrors `AgentsPanel.tsx` structure.

```typescript
interface ToolsPanelProps {
  projectId: string;
}
```

**Behavior**:
- Header with "MCP Tools" title and "Upload MCP Config" button (FR-004)
- Search input to filter tools by name/description
- Renders `ToolCard` for each MCP tool configuration (FR-007)
- Empty state with icon, message, and "Upload your first MCP config" CTA when no tools exist (FR-003)
- Loading skeleton while data is fetching
- Error state with retry option
- Card grid: `grid gap-4 md:grid-cols-2 2xl:grid-cols-3` (matches AgentsPanel pattern)
- "Upload MCP Config" click opens `UploadMcpModal`

---

### ToolCard

**Location**: `frontend/src/components/tools/ToolCard.tsx`
**Purpose**: Displays a single MCP tool configuration with sync status and actions.

```typescript
interface ToolCardProps {
  tool: McpToolConfig;
  onSync: (toolId: string) => void;
  onDelete: (toolId: string) => void;
}
```

**Behavior**:
- Displays tool name as card title
- Displays tool description as subtitle/body text
- Shows sync status badge with color coding (FR-007):
  - "Synced": green badge
  - "Pending": yellow/amber badge with spinner
  - "Error": red badge
- When sync_status is "error", shows `sync_error` message and "Retry" button (FR-008, FR-014)
- Action buttons: Re-sync (refresh icon) and Delete (trash icon) (FR-009, FR-015)
- Delete opens confirmation prompt; if tool is assigned to agents, shows affected agent names (FR-016)
- Uses `Card` component from `components/ui/card.tsx`
- Uses status badge colors consistent with existing codebase patterns

---

### UploadMcpModal

**Location**: `frontend/src/components/tools/UploadMcpModal.tsx`
**Purpose**: Modal dialog for uploading/pasting MCP configuration JSON.

```typescript
interface UploadMcpModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpload: (data: McpToolConfigCreate) => void;
  isUploading: boolean;
  uploadError: string | null;
}
```

**Behavior**:
- Dialog overlay with title "Upload MCP Configuration"
- Name input field (required, 1–100 chars)
- Description textarea (optional, 0–500 chars)
- Config content area with two modes:
  - **Paste mode** (default): Large textarea for pasting JSON
  - **File mode**: File input accepting `.json` files
- Toggle button to switch between paste and file modes
- Client-side validation before submission (FR-005):
  - Validates JSON syntax
  - Checks for `mcpServers` key
  - Validates server entries have required fields
  - Shows inline error messages per field
- File size validation: max 256 KB (FR-018)
- Duplicate name warning if name matches existing tool (FR-017)
- GitHub repo target input (optional, auto-populated from project context)
- Cancel and Upload buttons
- Upload button disabled while `isUploading` or validation fails
- Displays `uploadError` from server if upload fails
- On successful upload, closes modal and shows success feedback

---

### ToolSelectorModal

**Location**: `frontend/src/components/tools/ToolSelectorModal.tsx`
**Purpose**: Full overlay modal for selecting MCP tools to assign to an agent. Appears in Agent creation/edit form.

```typescript
interface ToolSelectorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (selectedToolIds: string[]) => void;
  initialSelectedIds: string[];
  projectId: string;
}
```

**Behavior**:
- Full overlay modal with title "Select MCP Tools" (FR-011)
- Search/filter input at top for filtering tools by name/description
- Responsive tile grid layout (FR-011):
  - 1 column on viewports < 640px
  - 2 columns on viewports 640px–1023px
  - 3 columns on viewports ≥ 1024px
- Each tile (`ToolTile` sub-component) shows:
  - Tool icon/logo placeholder (wrench icon default)
  - Tool name (bold)
  - Short description (truncated to 2 lines)
  - Selected state: checkmark overlay in corner + highlighted border (`border-primary`) (FR-011)
- Multi-select via click toggle — managed by local `Set<string>` state
- `initialSelectedIds` pre-selects tiles on open (FR-013, scenario 6)
- Footer with tool count ("N tools selected"), Cancel button, and Confirm button
- Confirm commits selection to parent via `onConfirm(Array.from(selectedIds))`
- Cancel closes modal without changing selections
- Empty state when no tools exist: shows message with link to Tools page (FR-019)
- Responsive: tile grid adjusts per SC-011 (768px to 1920px)

---

### ToolChips

**Location**: `frontend/src/components/tools/ToolChips.tsx`
**Purpose**: Renders selected MCP tools as removable chips/tags on the agent form.

```typescript
interface ToolChipsProps {
  tools: ToolChip[];
  onRemove: (toolId: string) => void;
  onAddClick: () => void;
}
```

**Behavior**:
- Renders a horizontal wrap of chip elements (FR-012)
- Each chip shows tool name and a remove (×) button (FR-013)
- Clicking × calls `onRemove(toolId)` to deselect the tool
- "Add Tools" button/chip at the end opens the `ToolSelectorModal`
- When no tools selected, shows only "Add Tools" button
- Chips use existing `Badge` component or custom styled elements
- Consistent with form field styling used in `AddAgentModal`

---

## New Hooks

### useToolsList

**Location**: `frontend/src/hooks/useTools.ts`
**Purpose**: Manages MCP tool CRUD operations and state.

```typescript
interface UseToolsListReturn {
  // Read state
  tools: McpToolConfig[];
  isLoading: boolean;
  error: string | null;

  // Mutations
  uploadTool: (data: McpToolConfigCreate) => Promise<McpToolConfig>;
  isUploading: boolean;
  uploadError: string | null;

  syncTool: (toolId: string) => Promise<McpToolSyncResult>;
  syncingId: string | null;
  syncError: string | null;

  deleteTool: (toolId: string, confirm?: boolean) => Promise<DeleteToolResult>;
  deletingId: string | null;
  deleteError: string | null;

  // Auth
  authError: boolean;
}

function useToolsList(projectId: string): UseToolsListReturn;
```

**Implementation Notes**:
- Uses TanStack Query `useQuery` for tool list with key `['tools', 'list', projectId]`
- `staleTime: 30_000` (30 seconds)
- `uploadTool` uses `useMutation` → invalidates `['tools', 'list', projectId]` on success
- `syncTool` uses `useMutation` → updates specific tool in cache via `queryClient.setQueryData`
- `deleteTool` uses `useMutation` → invalidates tool list on success
- Tracks `syncingId` and `deletingId` for per-item loading states (mirrors `useMcpSettings` pattern)
- Detects 401 errors for `authError` state

### useAgentTools

**Location**: `frontend/src/hooks/useAgentTools.ts`
**Purpose**: Manages MCP tool assignments for a specific agent.

```typescript
interface UseAgentToolsReturn {
  tools: ToolChip[];
  isLoading: boolean;
  updateTools: (toolIds: string[]) => Promise<void>;
  isUpdating: boolean;
}

function useAgentTools(projectId: string, agentId: string): UseAgentToolsReturn;
```

**Implementation Notes**:
- Uses TanStack Query `useQuery` for agent tools with key `['agents', agentId, 'tools']`
- `updateTools` uses `useMutation` → invalidates agent tools and pending agents queries on success
- Used by `AddAgentModal` for persisting tool selections

---

## Modified Components

### AddAgentModal

**Location**: `frontend/src/components/agents/AddAgentModal.tsx`
**Purpose**: Existing agent creation modal — modified to include MCP tool selection.

**Changes**:
- Add "Add Tools" section below the system prompt field
- Render `ToolChips` component showing selected tools
- Clicking "Add Tools" opens `ToolSelectorModal`
- On modal confirm, update local form state with selected tool IDs
- Include `tool_ids` in the agent create/update payload
- When editing an existing agent, pre-populate selected tools from agent record

### Sidebar Navigation

**Location**: `frontend/src/constants.ts`
**Purpose**: Add Tools navigation item.

**Changes**:
- Import `Wrench` from `lucide-react`
- Add `{ path: '/tools', label: 'Tools', icon: Wrench }` after the Agents entry in `NAV_ROUTES`

### Router Configuration

**Location**: `frontend/src/App.tsx` (or equivalent router file)
**Purpose**: Add route for Tools page.

**Changes**:
- Import `ToolsPage`
- Add `<Route path="/tools" element={<ToolsPage />} />`

### API Client

**Location**: `frontend/src/services/api.ts`
**Purpose**: Add tools API methods.

**Changes**:
- Add `toolsApi` namespace with `list`, `get`, `create`, `sync`, `delete` methods
- Extend `agentsApi` with `getTools` and `updateTools` methods

### Types

**Location**: `frontend/src/types/index.ts`
**Purpose**: Add MCP tool types.

**Changes**:
- Add `McpToolConfig`, `McpToolConfigCreate`, `McpToolConfigListResponse`, `McpToolSyncResult` interfaces
- Add `ToolChip`, `ToolSelectorState` interfaces

### Backend Route Registration

**Location**: `backend/src/api/__init__.py`
**Purpose**: Register new tools router.

**Changes**:
- Import `tools_router` from `src.api.tools`
- Add `router.include_router(tools_router, prefix="/tools", tags=["tools"])`
