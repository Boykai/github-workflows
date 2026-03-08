# Quickstart: Confirmation Flow for Critical Actions

**Feature**: 001-confirmation-flow | **Date**: 2026-03-08

## Prerequisites

- Node.js 20+ and npm
- The repository cloned and on the feature branch

```bash
git checkout 001-confirmation-flow
```

## Setup

### Frontend

```bash
cd frontend
npm install
npm run dev
# App available at http://localhost:5173
```

No backend changes are needed for this feature.

## New Files to Create

### Frontend

| File | Purpose |
|------|---------|
| `frontend/src/components/ui/confirmation-dialog.tsx` | NEW: Reusable confirmation dialog presentational component |
| `frontend/src/hooks/useConfirmation.ts` | NEW: Imperative confirmation hook + ConfirmationDialogProvider context |

### Files to Modify

| File | Changes |
|------|---------|
| `frontend/src/App.tsx` | Wrap app content with `<ConfirmationDialogProvider>` |
| `frontend/src/components/agents/AgentCard.tsx` | Replace `window.confirm()` with `useConfirmation` hook |
| `frontend/src/components/agents/AgentsPanel.tsx` | Replace `window.confirm()` with `useConfirmation` hook |
| `frontend/src/components/chores/ChoreCard.tsx` | Replace `window.confirm()` with `useConfirmation` hook |
| `frontend/src/pages/AgentsPipelinePage.tsx` | Replace `window.confirm()` with `useConfirmation` hook |

## Implementation Order

### Phase 1: Core Component and Hook (FR-003–FR-012, FR-015)

1. **confirmation-dialog.tsx** (new)
   - Presentational component receiving all state as props
   - Fixed positioning with `inset-0 z-[60]` backdrop
   - Variant-based styling (danger: red, warning: amber, info: blue)
   - Icon from lucide-react based on variant (`AlertTriangle`, `Info`)
   - Title with `aria-labelledby` and description with `aria-describedby`
   - Scrollable description area (`max-h-[60vh] overflow-y-auto`)
   - Button footer always visible (outside scroll area)
   - Loading spinner on confirm button when `isLoading`
   - Inline error message when `error` is set
   - `role="dialog"`, `aria-modal="true"` on container
   - Accessible: ARIA attributes per FR-011

2. **useConfirmation.ts** (new)
   - `ConfirmationDialogProvider` component (wraps app root)
   - `useConfirmation()` hook returning `{ confirm }` function
   - `confirm(options)` returns `Promise<boolean>`
   - Internal state management: dialog state, queue, loading, error
   - Focus management: capture previous focus, restore on close
   - Focus trapping: Tab/Shift+Tab cycle within dialog
   - Escape key handling: dismiss as cancel
   - Backdrop click handling: dismiss as cancel (disabled during loading)
   - Queue management: one dialog at a time, queue additional requests
   - Double-click prevention: immediate disable + promise guard

**Verify**: Import `useConfirmation` in any component → call `confirm()` → dialog appears with correct styling. Press Escape → dialog closes. Click backdrop → dialog closes. Click Confirm → returns true. Click Cancel → returns false.

### Phase 2: Provider Integration (FR-016)

3. **App.tsx** — Add provider
   - Import `ConfirmationDialogProvider` from hooks
   - Wrap the app content (inside existing providers, e.g., QueryClientProvider, Router)
   - This is a one-line addition to the JSX tree

**Verify**: App loads without errors. `useConfirmation()` is available in all components.

### Phase 3: Retrofit Existing Call Sites (FR-001, FR-005–FR-007)

4. **AgentCard.tsx** — Delete agent confirmation
   - Import `useConfirmation`
   - Replace `window.confirm(...)` in `handleDelete` with `await confirm({ ... })`
   - Set variant: `'danger'`, confirmLabel: `'Delete'`
   - Make `handleDelete` async

5. **AgentsPanel.tsx** — Clear pending agents confirmation
   - Import `useConfirmation`
   - Replace `window.confirm(...)` in `handleClearPending` with `await confirm({ ... })`
   - Set variant: `'warning'`, confirmLabel: `'Clear Records'`
   - Make `handleClearPending` async

6. **ChoreCard.tsx** — Delete chore confirmation
   - Import `useConfirmation`
   - Replace `window.confirm(...)` in `handleDelete` with `await confirm({ ... })`
   - Set variant: `'danger'`, confirmLabel: `'Delete'`
   - Make `handleDelete` async

7. **AgentsPipelinePage.tsx** — Delete pipeline confirmation
   - Import `useConfirmation`
   - Replace `window.confirm(...)` in `handleDelete` with `await confirm({ ... })`
   - Set variant: `'danger'`, confirmLabel: `'Delete Pipeline'`
   - Make `handleDelete` async

**Verify**: Each action triggers the new styled confirmation dialog. Confirm → action executes. Cancel → no side effects. Escape → no side effects. Visual styling matches the project design system.

### Phase 4: Testing (Spec Acceptance Criteria)

8. **confirmation-dialog.test.tsx** (new)
   - Test rendering with all variants (danger, warning, info)
   - Test confirm button click resolves with true
   - Test cancel button click resolves with false
   - Test Escape key dismissal resolves with false
   - Test backdrop click dismissal resolves with false
   - Test loading state disables buttons
   - Test error state displays error message
   - Test ARIA attributes are present
   - Test focus management (initial focus, restoration)
   - Test queue management (second confirm while dialog open)
   - Test double-click prevention

**Verify**: `cd frontend && npx vitest run` — all tests pass including new tests.

## Key Patterns to Follow

### Imperative Confirmation Pattern

```typescript
// In any component that needs confirmation:
import { useConfirmation } from '@/hooks/useConfirmation';

function MyComponent() {
  const { confirm } = useConfirmation();

  const handleDelete = async () => {
    const confirmed = await confirm({
      title: 'Delete Item',
      description: 'Are you sure you want to delete this item? This action cannot be undone.',
      variant: 'danger',
      confirmLabel: 'Delete',
    });
    if (confirmed) {
      deleteMutation.mutate(itemId);
    }
  };

  return <button onClick={handleDelete}>Delete</button>;
}
```

### Async Confirmation with Loading/Error

```typescript
// For actions that need in-dialog feedback:
const handleBulkDelete = async () => {
  await confirm({
    title: 'Delete All Items',
    description: `This will delete ${items.length} items. This action cannot be undone.`,
    variant: 'danger',
    confirmLabel: 'Delete All',
    onConfirm: async () => {
      // This runs within the dialog — shows loading spinner, catches errors
      await bulkDeleteMutation.mutateAsync(itemIds);
    },
  });
};
```

### Focus Trap Pattern

```typescript
// Focus trapping within the dialog:
function trapFocus(dialogRef: HTMLDivElement, event: KeyboardEvent) {
  const focusable = dialogRef.querySelectorAll<HTMLElement>(
    'button:not([disabled]), [tabindex]:not([tabindex="-1"]), a[href], input, select, textarea'
  );
  const first = focusable[0];
  const last = focusable[focusable.length - 1];

  if (event.key === 'Tab') {
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }
}
```

## Verification

After implementation, verify:

1. **Agent delete**: Click delete on an agent card → styled confirmation dialog with danger styling appears → "Delete" and "Cancel" buttons visible → Confirm deletes, Cancel does nothing.
2. **Clear pending agents**: Click "Clear Pending" → styled confirmation dialog with warning (amber) styling appears → "Clear Records" and "Cancel" buttons visible.
3. **Chore delete**: Click delete on a chore card → styled confirmation dialog with danger styling appears.
4. **Pipeline delete**: Click delete on pipeline page → styled confirmation dialog with danger styling appears.
5. **Escape key**: Any confirmation dialog open → press Escape → dialog closes, action NOT executed.
6. **Backdrop click**: Any confirmation dialog open → click outside dialog → dialog closes, action NOT executed.
7. **Focus trap**: Tab key cycles only within dialog buttons → does not reach background elements.
8. **Focus restore**: After dialog closes → focus returns to the button that triggered it.
9. **ARIA**: Inspect dialog element → `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, `aria-describedby` present.
10. **Keyboard nav**: Navigate entire confirmation flow using only Tab, Enter, Escape → all elements reachable and activatable.
11. **Double-click**: Rapidly click "Confirm" → action executes only once.
12. **Loading state** (async): Trigger async confirmation → spinner visible, buttons disabled during operation.
13. **Error state** (async): Trigger async confirmation that fails → error message displayed inline, retry available.
14. **Queue**: Open a confirmation dialog → trigger another critical action → second dialog appears after first resolves.
15. **Visual consistency**: All 4 confirmation dialogs use the same layout, typography, spacing, and interaction patterns.
