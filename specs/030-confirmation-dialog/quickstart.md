# Quickstart: Confirmation Dialog for Critical User Actions

**Feature**: 030-confirmation-dialog | **Date**: 2026-03-08

## Prerequisites

- Node.js 20+ and npm
- The repository cloned and on the feature branch

```bash
git checkout 030-confirmation-dialog
```

## Setup

### Frontend

```bash
cd frontend
npm install
npm run dev
# App available at http://localhost:5173
```

No backend changes are required for this feature.

## New Files to Create

### Frontend Files

| File | Purpose |
|------|---------|
| `frontend/src/components/ui/confirmation-dialog.tsx` | NEW: Reusable ConfirmationDialog presentational component |
| `frontend/src/hooks/useConfirmation.ts` | NEW: ConfirmationProvider context + useConfirmation hook |

### Files to Modify

| File | Changes |
|------|---------|
| `frontend/src/App.tsx` | Wrap app tree with `<ConfirmationProvider>` |
| `frontend/src/components/agents/AgentCard.tsx` | Replace `window.confirm()` with `useConfirmation()` |
| `frontend/src/components/agents/AgentsPanel.tsx` | Replace `window.confirm()` with `useConfirmation()` |
| `frontend/src/components/chores/ChoreCard.tsx` | Replace `window.confirm()` with `useConfirmation()` |
| `frontend/src/pages/AgentsPipelinePage.tsx` | Replace `window.confirm()` with `useConfirmation()` |

## Implementation Order

### Phase 1: Core Component (FR-002, FR-003, FR-005, FR-008, FR-010)

1. **confirmation-dialog.tsx** (new)
   - Create `ConfirmationDialog` component with three variant styles (danger, warning, info)
   - Implement portal-based rendering via `createPortal()`
   - Add variant-specific icons (AlertTriangle, Info from lucide-react)
   - Add variant-specific confirm button styling (destructive for danger, default for others)
   - Add backdrop overlay with click-to-cancel
   - Add Escape key handler

2. **useConfirmation.ts** (new) — Context + Hook
   - Create `ConfirmationContext` with `confirm()` function
   - Create `ConfirmationProvider` that renders a single `ConfirmationDialog`
   - Implement Promise-based `confirm()` API: returns `Promise<boolean>`
   - Implement request queue for preventing overlapping dialogs (FR-009)
   - Store `document.activeElement` for focus restoration
   - Create `useConfirmation()` hook that consumes the context

**Verify**: Import `ConfirmationProvider` in a test page → call `confirm()` → dialog appears → confirm returns true → cancel returns false.

### Phase 2: Accessibility (FR-007)

1. **confirmation-dialog.tsx** — Accessibility enhancements
   - Add `role="alertdialog"`, `aria-modal="true"`
   - Add `aria-labelledby` pointing to title element
   - Add `aria-describedby` pointing to description element
   - Implement focus trap (Tab cycles between Cancel and Confirm buttons)
   - Move focus to Cancel button on open
   - Restore focus to trigger element on close

**Verify**: Open dialog → Tab cycles within dialog only. Escape closes. Screen reader announces title and description.

### Phase 3: App Integration (FR-001)

1. **App.tsx** — Provider integration
   - Import `ConfirmationProvider`
   - Wrap the app tree (inside `QueryClientProvider`, wrapping all routes)

2. **AgentCard.tsx** — Migration
   - Import `useConfirmation`
   - Replace `window.confirm()` in `handleDelete()` with `await confirm({ ... })`
   - Use `variant: 'danger'` and `confirmLabel: 'Remove'`

3. **AgentsPanel.tsx** — Migration
   - Import `useConfirmation`
   - Replace `window.confirm()` in `handleClearPending()` with `await confirm({ ... })`
   - Use `variant: 'warning'` and `confirmLabel: 'Clear Records'`

4. **ChoreCard.tsx** — Migration
   - Import `useConfirmation`
   - Replace `window.confirm()` in `handleDelete()` with `await confirm({ ... })`
   - Use `variant: 'danger'` and `confirmLabel: 'Remove'`

5. **AgentsPipelinePage.tsx** — Migration
   - Import `useConfirmation`
   - Replace `window.confirm()` in `handleDelete()` with `await confirm({ ... })`
   - Use `variant: 'danger'` and `confirmLabel: 'Delete'`

**Verify**: Each replaced call site now shows the styled confirmation dialog instead of the browser's native confirm box.

## Key Patterns to Follow

### Imperative Confirmation Pattern

```typescript
import { useConfirmation } from '@/hooks/useConfirmation';

function MyComponent() {
  const { confirm } = useConfirmation();

  const handleDestructiveAction = async () => {
    const ok = await confirm({
      title: 'Delete Item',
      description: 'This will permanently delete the item. This action cannot be undone.',
      confirmLabel: 'Delete',
      cancelLabel: 'Cancel',
      variant: 'danger',
    });
    if (ok) {
      deleteMutation.mutate(itemId);
    }
  };

  return <Button variant="destructive" onClick={handleDestructiveAction}>Delete</Button>;
}
```

### Focus Trap Pattern

```typescript
useEffect(() => {
  if (!isOpen || !dialogRef.current) return;

  const focusableElements = dialogRef.current.querySelectorAll<HTMLElement>(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  const firstFocusable = focusableElements[0];
  const lastFocusable = focusableElements[focusableElements.length - 1];

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Tab') {
      if (e.shiftKey) {
        if (document.activeElement === firstFocusable) {
          e.preventDefault();
          lastFocusable.focus();
        }
      } else {
        if (document.activeElement === lastFocusable) {
          e.preventDefault();
          firstFocusable.focus();
        }
      }
    }
    if (e.key === 'Escape') {
      onCancel();
    }
  };

  document.addEventListener('keydown', handleKeyDown);
  firstFocusable?.focus();

  return () => document.removeEventListener('keydown', handleKeyDown);
}, [isOpen, onCancel]);
```

### Provider Wrapping Pattern

```tsx
// App.tsx
import { ConfirmationProvider } from './hooks/useConfirmation';

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfirmationProvider>
        <RouterProvider router={router} />
      </ConfirmationProvider>
    </QueryClientProvider>
  );
}
```

## Verification

After implementation, verify:

1. **Dialog appears**: Click any delete/remove button → styled dialog appears (not browser native)
2. **Cancel aborts**: Click "Cancel" → dialog closes → no action taken → no side effects
3. **Confirm executes**: Click confirm button → dialog closes → action executes
4. **Escape cancels**: Press Escape while dialog is open → dialog closes → action aborted
5. **Backdrop cancels**: Click outside the dialog → dialog closes → action aborted
6. **Severity variants**: Delete actions show red danger styling; clear pending shows amber warning
7. **Focus trap**: Tab key cycles within dialog buttons only — cannot reach background content
8. **Focus restoration**: After dialog closes, focus returns to the button that triggered it
9. **Screen reader**: `role="alertdialog"` announced; title and description read aloud
10. **Single dialog**: Rapidly trigger two destructive actions → only one dialog appears at a time
11. **No regression**: Existing custom dialogs (BulkModelUpdateDialog, CleanUpConfirmModal, ConfirmChoreModal) continue to work unchanged
