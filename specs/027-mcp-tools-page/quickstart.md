# Quickstart: Add Tools Page with MCP Configuration Upload and Agent Tool Selection

**Feature**: 027-mcp-tools-page | **Date**: 2026-03-07

## Prerequisites

- Node.js 20+ and npm
- Python 3.12+
- The repository cloned and on the feature branch

```bash
git checkout 027-mcp-tools-page
```

## Setup

### Backend

```bash
cd backend
pip install -e ".[dev]"
# Database migrations run automatically on startup
uvicorn src.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# App available at http://localhost:5173
```

## New Files to Create

### Backend

| File | Purpose |
|------|---------|
| `backend/src/migrations/014_extend_mcp_tools.sql` | Extend MCP table + agent-tool junction table |
| `backend/src/models/tools.py` | Pydantic models: McpToolConfig, McpToolConfigCreate, sync models |
| `backend/src/services/tools/__init__.py` | Service re-exports |
| `backend/src/services/tools/service.py` | ToolsService: CRUD + MCP validation + GitHub sync |
| `backend/src/api/tools.py` | FastAPI router: tool CRUD + sync endpoints |

### Frontend

| File | Purpose |
|------|---------|
| `frontend/src/pages/ToolsPage.tsx` | Top-level Tools page mirroring AgentsPage layout |
| `frontend/src/components/tools/ToolsPanel.tsx` | Tool catalog panel with search, filter, upload CTA |
| `frontend/src/components/tools/ToolCard.tsx` | Individual tool card with sync status and actions |
| `frontend/src/components/tools/UploadMcpModal.tsx` | Upload/paste MCP configuration modal |
| `frontend/src/components/tools/ToolSelectorModal.tsx` | Tile-grid modal for selecting tools on agent form |
| `frontend/src/components/tools/ToolChips.tsx` | Removable chip/tag display for selected tools |
| `frontend/src/hooks/useTools.ts` | Tool CRUD hook (list, upload, sync, delete) |
| `frontend/src/hooks/useAgentTools.ts` | Agent-tool assignment hook |

### Files to Modify

| File | Changes |
|------|---------|
| `frontend/src/constants.ts` | Add Tools nav route with Wrench icon |
| `frontend/src/App.tsx` (or router file) | Add `/tools` route |
| `frontend/src/services/api.ts` | Add `toolsApi` and extend `agentsApi` with tool methods |
| `frontend/src/types/index.ts` | Add McpToolConfig and related TypeScript interfaces |
| `frontend/src/components/agents/AddAgentModal.tsx` | Add "Add Tools" section with ToolChips + ToolSelectorModal |
| `backend/src/api/__init__.py` | Register tools router |

## Implementation Order

### Phase 1: Backend Foundation

1. **Migration** (`014_extend_mcp_tools.sql`)
   - ALTER TABLE to add columns to `mcp_configurations`
   - Create `agent_tool_associations` junction table
   - Add indexes for project, sync status, and association lookups

2. **Models** (`models/tools.py`)
   - Define Pydantic models: `McpToolConfigCreate`, `McpToolConfigResponse`, `McpToolConfigListResponse`
   - Define `McpToolConfigSyncResult`, `AgentToolAssociation`
   - MCP JSON schema validation function

3. **Service** (`services/tools/service.py`)
   - Implement CRUD: `list_tools`, `get_tool`, `create_tool`, `delete_tool`
   - Implement `sync_tool_to_github` (Contents API integration)
   - Implement `validate_mcp_config` (JSON schema validation)
   - Implement `get_agents_using_tool` (for delete warnings)
   - Implement `update_agent_tools` (set tool assignments)
   - Follow pattern from `services/mcp_store.py` and `services/agents/service.py`

4. **API Router** (`api/tools.py`)
   - Wire endpoints to service methods
   - Follow pattern from `api/agents.py` for session dependency injection and project access verification

### Phase 2: Frontend Types and API

5. **Types** (`types/index.ts`)
   - Add all MCP tool and agent-tool TypeScript interfaces

6. **API Client** (`services/api.ts`)
   - Add `toolsApi` object with `list`, `get`, `create`, `sync`, `delete`
   - Extend `agentsApi` with `getTools`, `updateTools`

### Phase 3: Frontend Navigation and Routing

7. **Navigation** (`constants.ts`)
   - Add `{ path: '/tools', label: 'Tools', icon: Wrench }` to `NAV_ROUTES`

8. **Router** (App.tsx or router config)
   - Add `/tools` route pointing to `ToolsPage`

### Phase 4: Frontend Hooks

9. **useTools** hook
   - Tool list query, upload/sync/delete mutations
   - Per-item loading states (syncingId, deletingId)
   - Auth error detection

10. **useAgentTools** hook
    - Agent-tool assignment query and update mutation
    - Cache invalidation on update

### Phase 5: Frontend Components — Tools Page

11. **ToolCard** component (standalone card)
12. **UploadMcpModal** component (upload form with validation)
13. **ToolsPanel** component (depends on ToolCard, UploadMcpModal)
14. **ToolsPage** component (depends on ToolsPanel)

### Phase 6: Frontend Components — Agent Tool Selection

15. **ToolChips** component (removable tag display)
16. **ToolSelectorModal** component (tile grid with multi-select)
17. **AddAgentModal** modifications (integrate ToolChips + ToolSelectorModal)

## Key Patterns to Follow

### API Client Pattern (from existing `api.ts`)

```typescript
export const toolsApi = {
  list: async (projectId: string): Promise<McpToolConfigListResponse> => {
    const response = await fetchWithAuth(`${API_BASE}/tools/${projectId}`);
    return response.json();
  },
  create: async (projectId: string, data: McpToolConfigCreate): Promise<McpToolConfig> => {
    const response = await fetchWithAuth(`${API_BASE}/tools/${projectId}`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return response.json();
  },
  // ... other methods
};
```

### Hook Pattern (from existing `useMcpSettings.ts`)

```typescript
function useToolsList(projectId: string) {
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['tools', 'list', projectId],
    queryFn: () => toolsApi.list(projectId),
    staleTime: 30_000,
    enabled: !!projectId,
  });

  const uploadMutation = useMutation({
    mutationFn: (data: McpToolConfigCreate) => toolsApi.create(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tools', 'list', projectId] });
    },
  });

  // ... sync and delete mutations
}
```

### Service Pattern (from existing `services/mcp_store.py`)

```python
async def create_tool(
    db: aiosqlite.Connection,
    github_user_id: str,
    project_id: str,
    data: McpToolConfigCreate,
) -> McpToolConfigResponse:
    # 1. Validate MCP config content
    validate_mcp_config(data.config_content)
    # 2. Extract endpoint URL from config
    endpoint_url = extract_endpoint_url(data.config_content)
    # 3. Insert into database
    # 4. Return response
```

### Panel/Card Pattern (from existing `AgentsPanel.tsx`)

```typescript
// Header with title and action button
<div className="flex items-center justify-between">
  <h3 className="text-[11px] uppercase tracking-[0.24em]">MCP Tools</h3>
  <Button onClick={openUploadModal}>Upload MCP Config</Button>
</div>

// Search input
<Input placeholder="Search tools..." className="moonwell h-12 rounded-full" />

// Card grid
<div className="constellation-grid mt-6 grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
  {tools.map(tool => <ToolCard key={tool.id} tool={tool} />)}
</div>

// Empty state
{tools.length === 0 && (
  <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
    <Wrench className="h-12 w-12 mb-4 opacity-50" />
    <p>No MCP tools configured yet</p>
    <Button variant="ghost" onClick={openUploadModal}>Upload your first config</Button>
  </div>
)}
```

## Verification

After implementation, verify:

1. **Navigation**: "Tools" appears in the sidebar directly below "Agents" with a wrench icon
2. **Empty State**: Visit Tools page with no tools — shows empty state with upload CTA
3. **Upload**: Click "Upload MCP Config" → paste valid JSON → submit → tool card appears with "Pending" status
4. **Validation**: Try uploading invalid JSON → see specific error message
5. **Sync**: Tool card shows sync status updating from "Pending" to "Synced" (or "Error")
6. **Re-sync**: Click refresh icon on a tool card → sync status updates
7. **Delete**: Click delete on tool card → confirmation prompt → tool removed
8. **Delete with agents**: Delete a tool used by agents → see warning listing affected agents
9. **Agent Tool Selection**: Open Agent creation form → click "Add Tools" → tile grid modal appears
10. **Multi-select**: Select multiple tools in the modal → click Confirm → chips appear on agent form
11. **Chip removal**: Click × on a chip → tool removed from selection
12. **Persist**: Save agent → reload → selected tools visible on agent detail
13. **Responsive**: Resize viewport from 768px to 1920px → tile grid adjusts columns
14. **Layout parity**: Compare Tools page side-by-side with Agents page → same structure and spacing
