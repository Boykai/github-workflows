# Component Contracts: Agents Page — Sun/Moon Avatars, Featured Agents, Inline Editing with PR Flow, Bulk Model Update, Repo Name Display & Tools Editor

**Feature**: 029-agents-page-ux | **Date**: 2026-03-07

## New Components

### AgentAvatar

**Location**: `frontend/src/components/agents/AgentAvatar.tsx`
**Purpose**: Renders a deterministic sun/moon themed SVG avatar based on the agent's slug. Used on agent cards and in the Featured Agents spotlight section.

```typescript
interface AgentAvatarProps {
  slug: string;               // Agent slug used for deterministic icon selection
  size?: 'sm' | 'md' | 'lg'; // Icon size: sm=24px, md=32px, lg=48px (default: md)
  className?: string;         // Additional CSS classes for the wrapper
}
```

**Behavior**:
- Computes a hash of the `slug` string using djb2 algorithm → maps to index in 12-icon array
- Renders the selected SVG icon inline (no network requests)
- Sun variants (indices 0–5): warm colors (amber-400, yellow-500, orange-400)
- Moon variants (indices 6–11): cool colors (slate-400, indigo-400, blue-300)
- SVG wrapped in a circular container with subtle background: `rounded-full bg-muted/50 p-1`
- Size mapping: `sm` → 24×24 viewBox, `md` → 32×32, `lg` → 48×48
- Accessible: `role="img"` and `aria-label="Avatar for {slug}"`

---

### BulkModelUpdateDialog

**Location**: `frontend/src/components/agents/BulkModelUpdateDialog.tsx`
**Purpose**: Two-step confirmation dialog for updating all agent models at once. Step 1: Select target model. Step 2: Review affected agents and confirm.

```typescript
interface BulkModelUpdateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  agents: AgentConfig[];               // All agents to be affected
  projectId: string;
  onSuccess: () => void;               // Callback after successful bulk update
}
```

**Behavior**:
- **Step 1**: Model selection
  - Reuses the existing `ModelSelector` component (or a simplified model list)
  - Shows available models grouped by provider
  - "Next" button enabled only when a model is selected
- **Step 2**: Confirmation
  - Header: "Update all agents to {Model Name}?"
  - Lists all affected agents with their current model (if any) and the target model
  - Agent count badge: "X agents will be updated"
  - "Cancel" returns to Step 1 or closes dialog
  - "Confirm" triggers the bulk update mutation
- **Loading state**: Shows spinner and "Updating agents..." during API call
- **Success state**: Closes dialog, calls `onSuccess()`, shows success toast
- **Error state**: Shows error message inline, allows retry
- Uses existing dialog/modal pattern from the codebase (Portal-based overlay)
- Icons: `RefreshCw` (lucide-react) for the update action

---

### ToolsEditor

**Location**: `frontend/src/components/agents/ToolsEditor.tsx`
**Purpose**: Interactive ordered list of tools within the agent editor modal. Allows adding, removing, and reordering tools via arrow buttons.

```typescript
interface ToolsEditorProps {
  tools: string[];                     // Current ordered list of tool IDs
  onToolsChange: (tools: string[]) => void;  // Callback when tools list changes
  availableTools?: ToolChip[];         // Available tools for the add dialog
  error?: string;                      // Validation error message (e.g., "At least one tool required")
}
```

**Behavior**:
- Renders an ordered list (`<ul>`) of tool items
- Each item displays:
  - Tool name/identifier as a styled chip
  - Up arrow button (↑) — disabled for first item
  - Down arrow button (↓) — disabled for last item
  - Remove button (×) — removes tool from list
- "Add Tools" button at bottom opens the existing `ToolSelectorModal`
- When a tool is added via the selector, it's appended to the end of the list
- Reorder: clicking ↑ swaps tool with previous; clicking ↓ swaps with next
- Every change calls `onToolsChange(newTools)` with the updated array
- Validation error displayed below the list when `error` prop is provided
- Empty state: "No tools assigned. Click 'Add Tools' to get started."
- Icons: `ChevronUp`, `ChevronDown`, `X`, `Plus` from lucide-react
- Styling: consistent with existing form elements in the codebase

---

## Modified Components

### AgentCard

**Location**: `frontend/src/components/agents/AgentCard.tsx`
**Purpose**: Individual agent card display — modified to add avatar, repo name bubble, and enhanced edit button.

**Changes**:
1. **Avatar**: Add `<AgentAvatar slug={agent.slug} size="md" />` in the card header, before the agent name
2. **Repository name bubble**: Add a chip/bubble below the source badge showing only the repo name (not owner/repo):
   ```tsx
   <span className="inline-flex max-w-[12rem] items-center truncate rounded-full bg-muted px-3 py-0.5 text-xs" title={fullRepoName}>
     {repoName}
   </span>
   ```
   - `repoName` derived by splitting the project's repository on `/` and taking the last segment
   - Full name shown on hover via `title` attribute
3. **Edit button**: Already exists — no structural change. Ensure it opens `AddAgentModal` in edit mode with the enhanced dirty-state tracking.

### AgentsPanel

**Location**: `frontend/src/components/agents/AgentsPanel.tsx`
**Purpose**: Agent catalog with search, sort, featured section, and actions toolbar.

**Changes**:
1. **Featured Agents logic**: Replace the existing `spotlightAgents` computation (lines 67–73) with the two-pass algorithm:
   - Pass 1: Agents with usage count > 0, sorted descending, take up to 3
   - Pass 2: Supplement with agents created within 3 days, excluding duplicates
   - Hide section if 0 agents qualify (FR-005)
2. **Bulk Update button**: Add "Update All Models" button in the catalog controls toolbar (next to search and sort):
   ```tsx
   <Button variant="outline" size="sm" onClick={() => setBulkUpdateOpen(true)}>
     <RefreshCw className="mr-2 h-4 w-4" />
     Update All Models
   </Button>
   ```
3. **BulkModelUpdateDialog**: Render the dialog component, controlled by `bulkUpdateOpen` state

### AddAgentModal

**Location**: `frontend/src/components/agents/AddAgentModal.tsx`
**Purpose**: Agent creation/editing modal — enhanced with unsaved-changes tracking and tools editor.

**Changes**:
1. **Dirty state tracking**: 
   - On modal open in edit mode, snapshot the original agent values
   - Compare current form state against snapshot on every field change
   - Set `isDirty` flag when any field differs from the snapshot
2. **Unsaved changes banner**:
   - When `isDirty`, show a persistent warning banner at the top of the modal:
     ```tsx
     <div className="rounded-md bg-yellow-50 border border-yellow-200 p-3 text-sm text-yellow-800">
       ⚠️ You have unsaved changes
     </div>
     ```
3. **Close guard**:
   - Intercept modal close (onOpenChange, Escape key) when `isDirty`
   - Show confirmation dialog: "You have unsaved changes. Save before leaving?"
   - Options: "Save" (trigger save), "Discard" (close modal), "Cancel" (stay in modal)
4. **beforeunload guard**:
   - Add `window.addEventListener('beforeunload', handler)` when `isDirty`
   - Remove listener when form is clean or modal closes
5. **Tools editor integration**:
   - Replace the existing tools chip display with `<ToolsEditor>` component in edit mode
   - Wire `onToolsChange` to update the local tools state and mark dirty
   - Validate at least one tool before save (FR-019)
6. **PR link display**:
   - On successful save, show the PR URL in the success screen (already partially implemented)
   - Add a toast notification with clickable PR link

### AgentsPage

**Location**: `frontend/src/pages/AgentsPage.tsx`
**Purpose**: Main agents page layout — modified to pass repo name down to components.

**Changes**:
1. **Repo name prop**: Extract the repository name from the project context and pass it to `AgentsPanel` → `AgentCard` as a prop
2. **No structural layout changes** — the page layout remains the same two-column grid

---

## Modified Hooks

### useAgents

**Location**: `frontend/src/hooks/useAgents.ts`
**Purpose**: TanStack Query hooks for agent data — add bulk model update mutation.

**Changes**:
- Add `useBulkUpdateModels(projectId)` mutation:
  ```typescript
  export function useBulkUpdateModels(projectId: string | undefined) {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: ({ targetModelId, targetModelName }: { targetModelId: string; targetModelName: string }) =>
        agentsApi.bulkUpdateModels(projectId!, targetModelId, targetModelName),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['agents', 'list', projectId] });
        queryClient.invalidateQueries({ queryKey: ['agents', 'pending', projectId] });
      },
    });
  }
  ```

---

## UI Layout Changes

### AgentCard (Updated Layout)

```
┌─────────────────────────────────────────────┐
│  ┌────┐                                     │
│  │ 🌙 │  Agent Name                 [Edit]  │
│  │    │  AGENT-SLUG                         │
│  └────┘  [Repository] [Active]  [my-repo]  │
│                                              │
│  Agent description text goes here, clamped   │
│  to 3-4 lines with ellipsis overflow...      │
│                                              │
│  Tools: [read] [edit] [search] [+2 more]    │
│                                              │
│  Created: Mar 7  │ Usage: 5  │ Tools: 4     │
│  PR: #42         │                           │
│                                              │
│  Model: [GPT-4o ▾]                          │
└─────────────────────────────────────────────┘
```

### AgentsPanel Toolbar (Updated)

```
┌─────────────────────────────────────────────┐
│  Agent Catalog                               │
│                                              │
│  [🔍 Search agents...]  [Sort ▾] [Update All Models] │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Agent 1   │  │ Agent 2   │  │ Agent 3   │  │
│  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────┘
```

### AddAgentModal (Edit Mode — Updated)

```
┌─────────────────────────────────────────────┐
│  Edit Agent: Security Reviewer      [×]     │
│                                              │
│  ⚠️ You have unsaved changes                │
│                                              │
│  Name: [Security Reviewer          ]        │
│                                              │
│  System Prompt:                              │
│  ┌─────────────────────────────────┐        │
│  │ You are a security reviewer...   │        │
│  │                                  │        │
│  └─────────────────────────────────┘        │
│  28,432 / 30,000                             │
│                                              │
│  Tools:                                      │
│  ┌─────────────────────────────────┐        │
│  │ 1. read          [↑] [↓] [×]   │        │
│  │ 2. edit          [↑] [↓] [×]   │        │
│  │ 3. search        [↑] [↓] [×]   │        │
│  │ 4. github/*      [↑] [↓] [×]   │        │
│  └─────────────────────────────────┘        │
│  [+ Add Tools]                               │
│                                              │
│                     [Cancel] [Save Changes]  │
└─────────────────────────────────────────────┘
```
