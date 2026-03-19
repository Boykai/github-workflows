# Contract: Toast/Snackbar System (Phase 1)

**Feature**: 050-frontend-ux-improvements  
**Requirements**: FR-001 through FR-005  
**Dependency**: `sonner` (NEW — ~4KB gzipped)

## Component Contracts

### `<Toaster />` Provider (AppLayout.tsx)

**Location**: `solune/frontend/src/layout/AppLayout.tsx`  
**Action**: Add Sonner's `<Toaster />` as a sibling to existing layout children.

```tsx
// Import
import { Toaster } from 'sonner';

// In AppLayout JSX, after SpotlightTour:
<Toaster
  position="bottom-right"
  visibleToasts={3}
  duration={5000}
  toastOptions={{
    classNames: {
      toast: 'celestial-panel border border-border shadow-lg',
      title: 'text-foreground font-sans',
      description: 'text-muted-foreground',
    },
  }}
/>
```

### `toast()` API (used in mutation hooks)

**Pattern**: Import `toast` from `sonner` in each mutation hook.

```tsx
import { toast } from 'sonner';

// In TanStack Query mutation options:
useMutation({
  mutationFn: ...,
  onSuccess: () => {
    toast.success('Pipeline saved');
    // existing onSuccess logic...
  },
  onError: (error) => {
    toast.error(error.message || 'Failed to save pipeline');
    // existing onError logic...
  },
});
```

**Error toast behavior**: Errors use `duration: Infinity` (persistent until dismissed) per FR-002.

```tsx
toast.error('Failed to delete workflow', { duration: Infinity });
```

## Integration Points

| Hook | Success Message | Error Message |
|------|----------------|---------------|
| `usePipelineConfig.savePipeline` | "Pipeline saved" | "Failed to save pipeline" |
| `usePipelineConfig.deletePipeline` | "Pipeline deleted" | "Failed to delete pipeline" |
| `usePipelineConfig.duplicatePipeline` | "Pipeline duplicated" | "Failed to duplicate pipeline" |
| `usePipelineConfig.assignPipeline` | "Pipeline assigned" | "Failed to assign pipeline" |
| `useAgentConfig.save` | "Agent configuration saved" | "Failed to save agent configuration" |
| `useChores.useCreateChore` | "Chore created" | "Failed to create chore" |
| `useChores.useUpdateChore` | "Chore updated" | "Failed to update chore" |
| `useChores.useDeleteChore` | "Chore deleted" | "Failed to delete chore" |
| `useChores.useTriggerChore` | "Chore triggered" | "Failed to trigger chore" |
| `useSettings.save` | "Settings saved" | "Failed to save settings" |
| `useWorkflow.trigger` | "Workflow started" | "Failed to start workflow" |
| `useWorkflow.stop` | "Workflow stopped" | "Failed to stop workflow" |
| `useApps.create` | "App created" | "Failed to create app" |
| `useApps.update` | "App updated" | "Failed to update app" |
| `useApps.delete` | "App deleted" | "Failed to delete app" |
| `useChat.send` (error only) | — | "Failed to send message" |

## Accessibility

- FR-004: Sonner renders toasts in an `<ol role="region" aria-label="Notifications">` with `aria-live="polite"` by default.
- Keyboard dismissal: Sonner supports `Escape` to dismiss focused toast.
- Screen reader: Each toast is announced as it appears.
