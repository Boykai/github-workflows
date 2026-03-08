# Component Contracts: Blocking Queue — Serial Issue Activation & Branch Ancestry Control

**Feature**: 030-blocking-queue | **Date**: 2026-03-08

## Overview

This document defines the frontend component interfaces for the blocking queue feature. All changes are modifications to existing components — no new component files are created for the blocking queue. The feature adds toggle switches, visual indicators, and real-time notifications to the existing UI.

---

## Modified Components

### ChoreCard (`frontend/src/components/chores/ChoreCard.tsx`)

**Change**: Add a "Blocking" toggle switch following the existing `ai_enhance_enabled` toggle pattern.

```typescript
// New prop additions — none; ChoreCard already receives the full Chore object
// The Chore type is extended with `blocking: boolean`

// Toggle behavior:
// - Renders a toggle switch labeled "Blocking" in the card's settings section
// - Uses the same visual pattern as the existing ai_enhance_enabled toggle
// - On toggle: calls useUpdateChore mutation with { blocking: !chore.blocking }
// - Persists immediately (optimistic update via TanStack Query)
// - Tooltip: "When enabled, triggered issues will be blocking and serialize activation"
```

**Visual Pattern Reference** (existing `ai_enhance_enabled` toggle):

```tsx
// Follow this existing pattern in ChoreCard.tsx:
<div className="flex items-center justify-between">
  <label className="text-sm text-muted-foreground">Blocking</label>
  <Switch
    checked={chore.blocking}
    onCheckedChange={(checked) => updateChore({ blocking: checked })}
  />
</div>
```

**State Management**: Uses existing `useUpdateChore` mutation hook, which will be updated to include `blocking` in the mutation payload.

---

### SavedWorkflowsList / PipelineBoard (`frontend/src/components/pipeline/SavedWorkflowsList.tsx`)

**Change**: Add a "Blocking" toggle switch to the pipeline configuration form.

```typescript
// Toggle behavior:
// - Renders a toggle switch labeled "Blocking" in the pipeline config section
// - Tooltip: "When enabled, ALL issues created by this pipeline are blocking"
// - On toggle: calls usePipelineConfig mutation with { blocking: !pipeline.blocking }
// - Persists immediately (optimistic update via TanStack Query)
```

**Visual Pattern**:

```tsx
<div className="flex items-center justify-between">
  <label className="text-sm text-muted-foreground">
    Blocking
    <Tooltip content="When enabled, every issue this pipeline creates will be blocking and serialize activation">
      <InfoIcon className="ml-1 h-3 w-3 inline" />
    </Tooltip>
  </label>
  <Switch
    checked={pipeline.blocking}
    onCheckedChange={(checked) => updatePipeline({ blocking: checked })}
  />
</div>
```

**State Management**: Uses existing `usePipelineConfig` hook's mutation, which will be updated to include `blocking` in the update payload.

---

### ChatInterface (`frontend/src/components/chat/ChatInterface.tsx`)

**Change**: Add `#block` to command autocomplete suggestions and visual indicator.

```typescript
// Autocomplete additions:
// - Add "#block" to the existing command suggestion list
// - Description: "Mark the resulting issue as blocking"

// Visual indicator:
// - When the user types #block in the message input, display a small badge
//   near the send button or in the composer toolbar
// - Badge text: "🔒 Blocking" or similar
// - Badge appears/disappears reactively as #block is typed/removed

// Detection logic (frontend-only, for UI indicator):
const hasBlockFlag = /\b#block\b/i.test(messageContent);
```

**Autocomplete Entry**:

```typescript
{
  command: '#block',
  description: 'Mark the resulting issue as blocking',
  icon: 'Lock'  // From lucide-react
}
```

**State Management**: No new hooks needed. The `#block` detection is purely local state for the visual indicator. The actual `is_blocking` flag is determined server-side when the message is processed.

---

### Board Issue Cards (`frontend/src/components/board/`)

**Change**: Add visual indicators for blocking and pending-blocked issues.

```typescript
// Blocking indicator:
// - If an issue card's labels include a "blocking" indicator (from queue data):
//   Display a 🔒 icon or "Blocking" badge on the card
// - Position: Top-right corner of the card, or inline with status labels

// Pending (blocked) indicator:
// - If an issue is in the blocking queue with status "pending":
//   Display a "Pending (blocked)" status label
// - Position: Below the issue title, styled as a muted status badge

// Blocking chain visualization:
// - Tooltip or collapsible section showing:
//   - Current queue position
//   - Current base branch
//   - Next issue in line
```

**Visual Patterns**:

```tsx
// Blocking badge on issue card
{isBlocking && (
  <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800 dark:bg-amber-900/30 dark:text-amber-400">
    <Lock className="h-3 w-3" />
    Blocking
  </span>
)}

// Pending (blocked) status label
{queueStatus === 'pending' && (
  <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-400">
    <Clock className="h-3 w-3" />
    Pending (blocked)
  </span>
)}
```

---

## WebSocket Event Handling

### Blocking Queue Toast Notifications

**Location**: Handled in the existing WebSocket message handler (wherever `connection_manager` events are consumed on the frontend).

```typescript
// When a 'blocking_queue_updated' event is received:
// For each issue in activatedIssues:
//   Display a toast notification: "Issue #X is now active — agents starting"
// Toast type: "info" or "success"
// Duration: 5 seconds (auto-dismiss)

// Example using sonner (if available) or existing toast system:
import { toast } from 'sonner';

function handleBlockingQueueUpdate(event: BlockingQueueUpdatedEvent) {
  for (const issueNumber of event.activatedIssues) {
    toast.info(`Issue #${issueNumber} is now active — agents starting`);
  }
}
```

---

## Modified Hooks

### useChores / useUpdateChore (`frontend/src/hooks/useChores.ts`)

**Change**: Include `blocking` field in types and mutations.

```typescript
// The useUpdateChore mutation already handles partial updates via ChoreUpdate
// The ChoreUpdate type is extended with `blocking?: boolean`
// No new hook logic needed — the existing mutation pattern handles it:

const updateChore = useMutation({
  mutationFn: ({ choreId, updates }: { choreId: string; updates: ChoreUpdate }) =>
    choresApi.update(projectId, choreId, updates),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['chores', projectId] });
  },
});
```

### usePipelineConfig (`frontend/src/hooks/usePipelineConfig.ts`)

**Change**: Include `blocking` field in types and mutations.

```typescript
// The existing update mutation is extended to accept `blocking` in the update payload
// The PipelineConfigUpdate type is extended with `blocking?: boolean`
// No new hook logic needed — the existing mutation pattern handles it
```

---

## Data Flow Summary

### Toggle Persistence Flow

```
User toggles "Blocking" on ChoreCard
  → ChoreCard calls updateChore({ blocking: true })
  → useUpdateChore fires PATCH /api/v1/chores/{project_id}/{chore_id}
  → Backend updates chores.blocking column
  → TanStack Query invalidates chores cache
  → ChoreCard re-renders with updated blocking state
```

### Chat #block Flow

```
User types "Fix login page #block" in ChatInterface
  → Frontend shows 🔒 badge (local detection)
  → User sends message
  → Backend chat.py detects #block, strips it → "Fix login page"
  → is_blocking=True passed through confirm_proposal()
  → execute_full_workflow() creates issue with is_blocking=True
  → blocking_queue.enqueue_issue(repo_key, issue_number, project_id, True)
  → Issue activates or enters pending based on queue state
```

### Activation Cascade Flow

```
Active issue #41 transitions to "in review"
  → copilot_polling/pipeline.py detects status change
  → blocking_queue.mark_in_review(repo_key, 41)
  → try_activate_next(repo_key) returns [42, 43]
  → For each activated issue: assign_agent_for_status()
  → WebSocket broadcast: { type: "blocking_queue_updated", activated_issues: [42, 43], ... }
  → Frontend receives event → toast: "Issue #42 is now active — agents starting"
  → Board refreshes → issue #42 and #43 cards update
```
