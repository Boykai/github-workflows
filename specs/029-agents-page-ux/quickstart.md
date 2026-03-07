# Quickstart: Agents Page — Sun/Moon Avatars, Featured Agents, Inline Editing with PR Flow, Bulk Model Update, Repo Name Display & Tools Editor

**Feature**: 029-agents-page-ux | **Date**: 2026-03-07

## Prerequisites

- Node.js 20+ and npm
- Python 3.12+
- The repository cloned and on the feature branch

```bash
git checkout 029-agents-page-ux
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

### Frontend

| File | Purpose |
|------|---------|
| `frontend/src/components/agents/AgentAvatar.tsx` | NEW: Sun/moon themed SVG avatar component with 12 variants |
| `frontend/src/components/agents/BulkModelUpdateDialog.tsx` | NEW: Two-step confirmation dialog for bulk model update |
| `frontend/src/components/agents/ToolsEditor.tsx` | NEW: Interactive tools list with add/remove/reorder controls |

### Files to Modify

| File | Changes |
|------|---------|
| `frontend/src/components/agents/AgentCard.tsx` | Add AgentAvatar, repo name bubble, edit button enhancements |
| `frontend/src/components/agents/AgentsPanel.tsx` | Enhanced Featured Agents logic (date supplement), "Update All Models" button |
| `frontend/src/components/agents/AddAgentModal.tsx` | Unsaved-changes tracking, close guard, beforeunload, ToolsEditor integration, PR link toast |
| `frontend/src/hooks/useAgents.ts` | Add `useBulkUpdateModels` mutation |
| `frontend/src/hooks/useAgentTools.ts` | Enhanced for reorder support — tools editor uses this hook to manage tool list state |
| `frontend/src/pages/AgentsPage.tsx` | Pass repo name to child components |
| `frontend/src/services/api.ts` | Add `agentsApi.bulkUpdateModels()` method |
| `backend/src/api/agents.py` | Add `PATCH /{project_id}/bulk-model` endpoint |
| `backend/src/models/agents.py` | Add `BulkModelUpdateRequest` and `BulkModelUpdateResult` models |
| `backend/src/services/agents/service.py` | Add `bulk_update_models()` method |

## Implementation Order

### Phase 1: Sun/Moon Avatars (FR-001, FR-002)

1. **AgentAvatar.tsx** (new)
   - Create 12 inline SVG icon variants (6 sun, 6 moon)
   - Implement djb2 hash function: `slug → hash → index % 12`
   - Support three sizes: sm (24px), md (32px), lg (48px)
   - Add accessibility attributes (`role="img"`, `aria-label`)

2. **AgentCard.tsx** — Integration
   - Import `AgentAvatar`
   - Render avatar in card header before agent name
   - Apply circular container styling: `rounded-full bg-muted/50 p-1`

**Verify**: Load Agents page → each agent card shows a distinct sun/moon icon. Refresh → same icons persist.

### Phase 2: Repository Name Display (FR-015, FR-016)

3. **AgentsPage.tsx** — Extract repo name
   - Parse repository from project context: `fullRepo.split('/').pop()`
   - Pass `repoName` prop to `AgentsPanel` → `AgentCard`

4. **AgentCard.tsx** — Repo name bubble
   - Add chip element with truncation:
     ```tsx
     <span className="inline-flex max-w-[12rem] items-center truncate rounded-full bg-muted px-3 py-0.5 text-xs" title={fullRepo}>
       {repoName}
     </span>
     ```

**Verify**: View agent cards → repo name shows without owner prefix. Long names truncate with ellipsis. Hover shows full name.

### Phase 3: Enhanced Featured Agents (FR-003, FR-004, FR-005)

5. **AgentsPanel.tsx** — Updated spotlight logic
   - Replace `spotlightAgents` computation with two-pass algorithm:
     - Pass 1: Agents with usage > 0, sorted descending, up to 3
     - Pass 2: Supplement with agents created within 3 days
   - Hide Featured section when 0 agents qualify
   - Deduplicate agents across passes

**Verify**: With agents having usage data → top 3 by usage shown. With new agents (< 3 days) → they supplement. With no qualifiers → section hidden.

### Phase 4: Tools Editor (FR-017, FR-018, FR-019)

6. **ToolsEditor.tsx** (new)
   - Ordered list with tool chips
   - Up/down arrow buttons for reorder (swap adjacent items)
   - Remove button (×) per tool
   - "Add Tools" button opens existing `ToolSelectorModal`
   - Validation: show error when tools list is empty

7. **AddAgentModal.tsx** — Tools editor integration
   - Replace static tool chips with `<ToolsEditor>` in edit mode
   - Wire `onToolsChange` callback to local state
   - Add validation check before save: `tools.length >= 1`
   - Show inline error: "At least one tool must be assigned"

**Verify**: Open agent editor → tools list shows with reorder/remove controls. Add a tool → appears at end. Reorder → order changes. Remove all → validation error appears.

### Phase 5: Inline Editing with Unsaved Changes (FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-020)

8. **AddAgentModal.tsx** — Dirty state tracking
   - Snapshot original agent values on modal open (edit mode)
   - Compare current form state against snapshot on each change
   - Set `isDirty` flag when any field differs

9. **AddAgentModal.tsx** — Unsaved changes banner
   - Show persistent yellow banner when `isDirty`:
     ```tsx
     {isDirty && (
       <div className="rounded-md bg-yellow-50 border border-yellow-200 p-3 text-sm text-yellow-800">
         ⚠️ You have unsaved changes
       </div>
     )}
     ```

10. **AddAgentModal.tsx** — Close guard
    - Intercept `onOpenChange(false)` when `isDirty`
    - Show confirmation dialog: "Save / Discard / Cancel"
    - Wire Save to trigger the update mutation
    - Wire Discard to close the modal
    - Wire Cancel to keep the modal open

11. **AddAgentModal.tsx** — beforeunload guard
    - Add `useEffect` that adds/removes `beforeunload` listener based on `isDirty`

12. **AddAgentModal.tsx** — PR link notification
    - On successful save (update mutation returns `AgentCreateResult`)
    - Show success toast with clickable PR link:
      ```
      ✅ Changes saved! PR created: #42 (View PR →)
      ```

**Verify**: Edit agent → banner appears. Try to close modal → confirmation dialog. Click Save → PR created, link shown. Refresh page during edit → browser warning.

### Phase 6: Bulk Model Update (FR-012, FR-013, FR-014)

13. **Backend models** (`agents.py`)
    - Add `BulkModelUpdateRequest` and `BulkModelUpdateResult` Pydantic models

14. **Backend service** (`agents/service.py`)
    - Add `bulk_update_models(project_id, target_model_id, target_model_name)` method
    - Iterate over all active agents, update each agent's model preference
    - Return summary with updated/failed counts

15. **Backend API** (`agents.py`)
    - Add `PATCH /{project_id}/bulk-model` endpoint
    - Parse request body, call service, return result

16. **Frontend API** (`api.ts`)
    - Add `agentsApi.bulkUpdateModels()` method

17. **useAgents.ts** — Mutation
    - Add `useBulkUpdateModels(projectId)` hook
    - Invalidate agents list on success

18. **BulkModelUpdateDialog.tsx** (new)
    - Step 1: Model selector (reuse ModelSelector or simplified list)
    - Step 2: Confirmation with agent list and "Confirm" / "Cancel" buttons
    - Loading/success/error states

19. **AgentsPanel.tsx** — Integration
    - Add "Update All Models" button in toolbar
    - Render `BulkModelUpdateDialog` controlled by local state

**Verify**: Click "Update All Models" → dialog opens. Select model → confirmation shows all agents. Confirm → agents updated, toast shown. Cancel → no changes.

## Key Patterns to Follow

### Deterministic Avatar Hash Pattern

```typescript
const AVATAR_COUNT = 12;

function getAvatarIndex(slug: string): number {
  let hash = 0;
  for (let i = 0; i < slug.length; i++) {
    hash = ((hash << 5) - hash + slug.charCodeAt(i)) | 0;
  }
  return Math.abs(hash) % AVATAR_COUNT;
}
```

### Dirty State Tracking Pattern

```typescript
// Snapshot on modal open
const [snapshot] = useState<AgentEditorSnapshot>(() => ({
  name: agent.name,
  description: agent.description,
  system_prompt: agent.system_prompt,
  tools: [...agent.tools],
  default_model_id: agent.default_model_id,
  default_model_name: agent.default_model_name,
}));

// Check dirty on every render
const isDirty = useMemo(() => {
  if (name !== snapshot.name) return true;
  if (description !== snapshot.description) return true;
  if (systemPrompt !== snapshot.system_prompt) return true;
  if (JSON.stringify(tools) !== JSON.stringify(snapshot.tools)) return true;
  return false;
}, [name, description, systemPrompt, tools, snapshot]);
```

### beforeunload Guard Pattern

```typescript
useEffect(() => {
  if (!isDirty) return;

  const handler = (e: BeforeUnloadEvent) => {
    e.preventDefault();
    // Modern browsers ignore custom messages, but the event must be prevented
  };

  window.addEventListener('beforeunload', handler);
  return () => window.removeEventListener('beforeunload', handler);
}, [isDirty]);
```

### Tools Reorder Pattern

```typescript
function moveUp(index: number) {
  if (index <= 0) return;
  const newTools = [...tools];
  [newTools[index - 1], newTools[index]] = [newTools[index], newTools[index - 1]];
  onToolsChange(newTools);
}

function moveDown(index: number) {
  if (index >= tools.length - 1) return;
  const newTools = [...tools];
  [newTools[index], newTools[index + 1]] = [newTools[index + 1], newTools[index]];
  onToolsChange(newTools);
}
```

### Bulk Model Update Backend Pattern

```python
async def bulk_update_models(
    self,
    project_id: str,
    target_model_id: str,
    target_model_name: str,
    access_token: str,
) -> BulkModelUpdateResult:
    agents = await self.list_agents(project_id, access_token)
    updated = []
    failed = []

    for agent in agents:
        try:
            await self._update_model_preference(
                agent.slug, target_model_id, target_model_name, project_id
            )
            updated.append(agent.slug)
        except Exception as e:
            logger.error(f"Failed to update model for {agent.slug}: {e}")
            failed.append(agent.slug)

    return BulkModelUpdateResult(
        success=len(failed) == 0,
        updated_count=len(updated),
        failed_count=len(failed),
        updated_agents=updated,
        failed_agents=failed,
        target_model_id=target_model_id,
        target_model_name=target_model_name,
    )
```

## Verification

After implementation, verify:

1. **Avatars**: Load Agents page with multiple agents → each card shows a distinct sun/moon icon. Refresh → same icons. Same agent on different pages → same icon.
2. **Featured Agents (usage)**: Assign agents to board columns → top 3 by column count appear in Featured section.
3. **Featured Agents (recency)**: Create a new agent → if fewer than 3 high-usage agents, new agent appears in Featured within 3 days.
4. **Featured Agents (empty)**: No agents assigned to columns and none created recently → Featured section hidden.
5. **Inline Edit — Open**: Click "Edit" on agent card → modal opens with pre-populated fields.
6. **Inline Edit — Dirty State**: Change agent name → "Unsaved changes" banner appears.
7. **Inline Edit — Close Guard**: Click modal close with unsaved changes → confirmation dialog appears.
8. **Inline Edit — Save**: Click Save → PR created → success toast with PR link shown.
9. **Inline Edit — Discard**: Click Discard in confirmation → modal closes, no changes saved.
10. **Inline Edit — beforeunload**: With unsaved changes, try to close browser tab → browser warning appears.
11. **Tools Editor — Add**: Open editor → click "Add Tools" → select tool → tool appears in list.
12. **Tools Editor — Remove**: Click × on tool → tool removed → "Unsaved changes" banner appears.
13. **Tools Editor — Reorder**: Click ↑/↓ arrows → tool order changes.
14. **Tools Editor — Validation**: Remove all tools → "At least one tool required" error shown → Save disabled.
15. **Bulk Update — Dialog**: Click "Update All Models" → dialog shows model selector.
16. **Bulk Update — Confirm**: Select model → confirmation lists all agents → click Confirm → agents updated.
17. **Bulk Update — Cancel**: Click Cancel → no changes made.
18. **Repo Name — Display**: Agent card shows "my-repo" (not "owner/my-repo") in a styled bubble.
19. **Repo Name — Truncation**: Long repo names truncate with ellipsis. Hover shows full name.
20. **Edge Case**: Two editors open simultaneously (if possible) → each tracks its own dirty state independently.
21. **Edge Case**: Save fails (network error) → changes preserved, user can retry.
22. **Edge Case**: Bulk update with 0 agents → button still works, dialog shows "No agents to update."
