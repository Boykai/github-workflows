# Component Contracts: Chores Page — Counter Fixes, Featured Rituals Panel, Inline Editing, AI Enhance Toggle, Agent Pipeline Config & Auto-Merge PR Flow

**Feature**: 029-chores-page-enhancements | **Date**: 2026-03-07

## New Components

### FeaturedRitualsPanel

**Location**: `frontend/src/components/chores/FeaturedRitualsPanel.tsx`
**Purpose**: Displays three highlight cards above the Chore grid: Next Run (soonest to trigger), Most Recently Run (latest execution), and Most Run (highest all-time count). Computed entirely client-side from the Chore list.

```typescript
interface FeaturedRitualsPanelProps {
  chores: Chore[];
  parentIssueCount: number;              // Current parent issue count for counter computation
  onChoreClick: (choreId: string) => void; // Navigate to or highlight a specific Chore
}
```

**Behavior**:
- Computes three rankings from `chores` array:
  - **Next Run**: For count-based, sort by `(schedule_value - (parentIssueCount - last_triggered_count))` ascending. For time-based, sort by `(schedule_value - daysSince(last_triggered_at))` ascending. Pick the lowest remaining.
  - **Most Recently Run**: Sort by `last_triggered_at` descending, pick first non-null.
  - **Most Run**: Sort by `execution_count` descending, pick highest.
- Each card displays: Chore name, the relevant statistic (e.g., "2 issues remaining", "Run 3h ago", "15 runs"), and a clickable link.
- Handles empty states:
  - No Chores at all: shows an onboarding message ("Create your first Chore to see Featured Rituals")
  - Some categories empty (e.g., no Chore has run yet): the card shows "—" or a subtle empty state
- Uses three horizontally arranged cards in a grid layout (`grid grid-cols-3 gap-4`)
- Each card uses `lucide-react` icons: `Clock` (Next Run), `PlayCircle` (Most Recently Run), `Trophy` (Most Run)
- Memoized with `React.memo` to prevent re-renders when unrelated state changes

---

### ChoreInlineEditor

**Location**: `frontend/src/components/chores/ChoreInlineEditor.tsx`
**Purpose**: Renders Chore definition fields as editable inputs/textareas within the ChoreCard. Reports field changes to the parent for dirty-state tracking.

```typescript
interface ChoreInlineEditorProps {
  chore: Chore;
  onChange: (updates: Partial<ChoreInlineUpdate>) => void;
  disabled?: boolean;                    // Disable editing (e.g., during save)
}
```

**Behavior**:
- Renders:
  - **Name**: `<input type="text">` with current `chore.name` as value
  - **Template Content**: `<textarea>` with `chore.template_content` as value (auto-resize)
  - **Schedule**: Reuses existing `ChoreScheduleConfig` component inline
- On every field change, calls `onChange()` with only the changed fields
- Does NOT manage its own state — controlled component pattern. Parent passes `chore` (with current edits applied) and receives `onChange` updates.
- When `disabled=true`, all inputs become read-only (used during save operation)
- Uses consistent styling with existing `ChoreScheduleConfig` (Tailwind utility classes)

---

### ConfirmChoreModal

**Location**: `frontend/src/components/chores/ConfirmChoreModal.tsx`
**Purpose**: Two-step confirmation modal for new Chore creation. Step 1 warns about automatic repository commits; Step 2 is a final "Yes, Create Chore" confirmation.

```typescript
interface ConfirmChoreModalProps {
  isOpen: boolean;
  onConfirm: () => void;                // Called when user accepts both steps
  onCancel: () => void;                  // Called when user cancels at any step
  choreName: string;                     // Displayed in confirmation text
  isLoading?: boolean;                   // Show loading state during creation
}
```

**Behavior**:
- Internal `step` state: `1 | 2`
- **Step 1** (Information):
  - Icon: `AlertTriangle` from `lucide-react` (warning color)
  - Heading: "Add Chore to Repository"
  - Body: "This will automatically add a Chore file to your repository's `.github/ISSUE_TEMPLATE/` directory. A Pull Request will be created and auto-merged into main."
  - Buttons: "Cancel" (calls `onCancel`) | "I Understand, Continue" (advances to Step 2)
- **Step 2** (Final Confirmation):
  - Icon: `CheckCircle` from `lucide-react` (success color)
  - Heading: `Create "${choreName}"?`
  - Body: "This action will: 1) Create a GitHub Issue, 2) Open a Pull Request, 3) Auto-merge the PR into main."
  - Buttons: "Back" (returns to Step 1) | "Yes, Create Chore" (calls `onConfirm`)
- When `isLoading=true`: "Yes, Create Chore" button shows a spinner and is disabled
- Resets to Step 1 when `isOpen` transitions from `false` to `true` (fresh state each time)
- Uses the existing modal/dialog component from the app's UI library (if one exists) or a custom overlay

---

### PipelineSelector

**Location**: `frontend/src/components/chores/PipelineSelector.tsx`
**Purpose**: Dropdown for selecting a saved Agent Pipeline configuration or "Auto" for a Chore.

```typescript
interface PipelineSelectorProps {
  projectId: string;
  selectedPipelineId: string;            // "" = Auto
  onPipelineChange: (pipelineId: string) => void;
  className?: string;
}
```

**Behavior**:
- Fetches pipeline list via `usePipelinesList(projectId)` hook (existing from spec 026/028)
- Renders a `<select>` dropdown (or custom `Popover`/`Select` from `components/ui/`) with:
  - First option: "Auto" (value = `""`) — label shows "Auto (Project Default)"
  - Remaining options: each saved pipeline by name (value = pipeline.id)
  - Preset pipelines (if any) shown with a subtle indicator (e.g., "Spec Kit 🔒")
- If `selectedPipelineId` is non-empty but not found in the pipeline list:
  - Shows a warning indicator: "⚠ Pipeline no longer available"
  - Dropdown defaults to "Auto" but preserves the stale ID until the user explicitly changes it
- On selection change: calls `onPipelineChange(newId)`
- When pipeline list is loading: shows a spinner or "Loading pipelines..."
- When pipeline list fails to load: shows "Auto" as the only option with an error note

---

### useUnsavedChanges

**Location**: `frontend/src/hooks/useUnsavedChanges.ts`
**Purpose**: Generic hook for blocking navigation when there are unsaved changes. Covers both browser close/refresh and SPA route transitions.

```typescript
interface UseUnsavedChangesReturn {
  blocker: Blocker;                      // react-router-dom blocker state
  isBlocked: boolean;                    // Whether navigation is currently blocked
}

function useUnsavedChanges(isDirty: boolean): UseUnsavedChangesReturn;
```

**Behavior**:
- When `isDirty=true`:
  - Registers `beforeunload` event listener (browser close/refresh/external navigation)
  - Activates `useBlocker` from `react-router-dom` (SPA route transitions)
- When `isDirty=false`: no listeners, no blocking
- Returns `blocker` object for custom modal rendering (the calling component decides the UI)
- The `blocker` provides `proceed()` and `reset()` methods for programmatic control
- Clean up: removes `beforeunload` listener on unmount or when `isDirty` changes to `false`

---

## Modified Components

### ChoreCard (MODIFIED)

**Location**: `frontend/src/components/chores/ChoreCard.tsx`
**Changes**: Fix counter display, add inline editing, AI Enhance toggle, pipeline selector.

```typescript
interface ChoreCardProps {
  chore: Chore;
  parentIssueCount: number;              // NEW: For counter computation
  editState?: Partial<ChoreInlineUpdate>; // NEW: Current edit state (if editing)
  onEditChange?: (updates: Partial<ChoreInlineUpdate>) => void; // NEW: Edit change handler
  onSave?: () => void;                   // NEW: Save inline edits
  onDiscard?: () => void;                // NEW: Discard inline edits
  isDirty?: boolean;                     // NEW: Whether this card has unsaved changes
  onUpdateChore: (data: ChoreUpdate) => void; // Existing: schedule/status updates
  onDeleteChore: () => void;             // Existing
  onTriggerChore: () => void;            // Existing
}
```

**New Behavior**:
- **Counter Fix**: For count-based Chores, displays `remaining = schedule_value - (parentIssueCount - last_triggered_count)`. Clamps to 0 minimum. Shows "X remaining" badge on the tile. Uses the same computation for both display and trigger evaluation consistency.
- **Inline Editing**: Renders `ChoreInlineEditor` for editable fields. Fields are always editable (FR-005).
- **Dirty Indicator**: When `isDirty=true`, shows an asterisk or highlight on the card border/header.
- **AI Enhance Toggle**: Renders the `Sparkles` toggle button (same style as `ChatToolbar.tsx`). Toggle state stored in `editState.ai_enhance_enabled`. Visible on the card when in edit mode.
- **Pipeline Selector**: Renders `PipelineSelector` dropdown. Value stored in `editState.agent_pipeline_id`. Visible on the card configuration section.
- **Save/Discard**: When `isDirty`, shows "Save" and "Discard" action buttons on the card.

---

### ChoresPanel (MODIFIED)

**Location**: `frontend/src/components/chores/ChoresPanel.tsx`
**Changes**: Add inline edit state management and dirty tracking.

```typescript
interface ChoresPanelProps {
  projectId: string;
  chores: Chore[];
  parentIssueCount: number;              // NEW: Passed through to ChoreCards
  isLoading: boolean;
  // ... existing props for templates, filters, etc.
}
```

**New Behavior**:
- Maintains `editState: Record<string, ChoreEditState>` — one entry per Chore being edited
- Initializes each Chore's `editState.original` on first edit interaction
- Computes `isDirty` per Chore: `JSON.stringify(editState[id].current) !== '{}'`
- Computes global `isAnyDirty`: any Chore has unsaved changes
- Shows a persistent "You have unsaved changes" banner when `isAnyDirty=true`
- Shows a global "Save All" button when `isAnyDirty=true` (saves all dirty Chores sequentially)
- Passes `editState[choreId]` and `onEditChange` to each `ChoreCard`
- Passes `parentIssueCount` to each `ChoreCard` for counter display

---

### AddChoreModal (MODIFIED)

**Location**: `frontend/src/components/chores/AddChoreModal.tsx`
**Changes**: Add AI Enhance toggle, pipeline selector, and two-step confirmation flow.

```typescript
interface AddChoreModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
  onChoreCreated: (chore: Chore) => void;
  // ... existing props
}
```

**New Behavior**:
- Adds AI Enhance toggle (default ON) at the top of the modal, styled like `ChatToolbar`
- Adds `PipelineSelector` dropdown below the main form fields
- When sparse input is detected → `ChoreChatFlow` receives `aiEnhance` prop
- When template is ready and user clicks "Create Chore":
  - Opens `ConfirmChoreModal` (two-step confirmation)
  - On final confirmation: calls `createWithAutoMerge` mutation
  - On success: shows toast with merge status, calls `onChoreCreated`, closes modal
  - On auto-merge failure: shows warning toast with PR link
- On cancel at any confirmation step: returns to the modal with input preserved

---

### ChoreChatFlow (MODIFIED)

**Location**: `frontend/src/components/chores/ChoreChatFlow.tsx`
**Changes**: Support AI Enhance OFF path for metadata-only generation.

```typescript
interface ChoreChatFlowProps {
  projectId: string;
  onTemplateReady: (templateContent: string, templateName: string) => void;
  onCancel: () => void;
  aiEnhance?: boolean;                   // NEW: Controls generation mode (default true)
}
```

**New Behavior**:
- Passes `ai_enhance` parameter in `choresApi.chat()` calls
- When `aiEnhance=false`:
  - Shows a subtle indicator in the chat UI: "Your input will be used as the template body"
  - First user message is treated as the body content
  - Chat Agent responds with metadata suggestions only
  - Template is assembled as: AI front matter + user's raw body
- When `aiEnhance=true`: existing behavior unchanged

---

## Modified Page

### ChoresPage (MODIFIED)

**Location**: `frontend/src/pages/ChoresPage.tsx`
**Changes**: Add Featured Rituals panel, compute parent issue count, wire unsaved changes guard.

**New Behavior**:
- Computes `parentIssueCount` from `useProjectBoard()` data:
  ```typescript
  const parentIssueCount = useMemo(() => {
    if (!boardData?.items) return 0;
    const parentIds = new Set<string>();
    for (const item of boardData.items) {
      if (item.content_type === 'issue') parentIds.add(item.id);
    }
    // Subtract sub-issues (items that have a parent reference)
    for (const item of boardData.items) {
      if (item.parent_id) parentIds.delete(item.parent_id);
    }
    return parentIds.size;
  }, [boardData?.items]);
  ```
  Note: Exact logic depends on existing board data structure; may reuse `useRecentParentIssues` filter.
- Renders `FeaturedRitualsPanel` above `ChoresPanel`, passing `chores` and `parentIssueCount`
- Wires `useUnsavedChanges(isAnyDirty)` for navigation guard
- When `blocker.state === 'blocked'`, renders a custom confirmation modal:
  ```
  "You have unsaved changes — are you sure you want to leave?"
  [Stay] [Discard and Leave]
  ```

---

## Hook Extensions

### useChores (MODIFIED)

**New Return Fields / Hooks**:

```typescript
// New mutation hook for inline updates
export function useInlineUpdateChore(
  projectId: string | null | undefined
): UseMutationResult<ChoreInlineUpdateResponse, ApiError, { choreId: string; data: ChoreInlineUpdate }> {
  // Calls choresApi.inlineUpdate()
  // On success: invalidates choreKeys.list(projectId)
  // On error: preserves edit state for retry
}

// New mutation hook for creation with auto-merge
export function useCreateChoreWithAutoMerge(
  projectId: string | null | undefined
): UseMutationResult<ChoreCreateResponse, ApiError, ChoreCreateWithConfirmation> {
  // Calls choresApi.createWithAutoMerge()
  // On success: invalidates choreKeys.list(projectId)
  // Returns ChoreCreateResponse with merge status
}

// Extended chat mutation — now accepts ai_enhance parameter
export function useChoreChat(
  projectId: string | null | undefined
): UseMutationResult<ChoreChatResponse, ApiError, ChoreChatMessage> {
  // Existing implementation, but ChoreChatMessage now includes ai_enhance?: boolean
}
```

**New Behavior**:
- `useInlineUpdateChore`: Calls `PUT /chores/{projectId}/{choreId}/inline-update`. On 409 Conflict, returns the error with `current_sha` and `current_content` for conflict resolution.
- `useCreateChoreWithAutoMerge`: Calls `POST /chores/{projectId}` with the extended request body. Returns `ChoreCreateResponse` including `pr_merged` and `merge_error` for toast notification.
- `useChoreChat`: Now passes `ai_enhance` field from `ChoreChatMessage` to the API.
