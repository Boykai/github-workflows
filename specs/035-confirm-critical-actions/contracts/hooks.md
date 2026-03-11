# Hook & Behavior Contracts: Add Confirmation Step to Critical Actions

**Feature**: 035-confirm-critical-actions | **Date**: 2026-03-11

## Overview

This document defines the behavioral contracts for hooks that manage confirmation state. All hooks are existing — changes are behavioral enhancements, not new APIs.

---

## Modified Hook: `useConfirmation`

**Location**: `frontend/src/hooks/useConfirmation.tsx`

### Public API (Unchanged)

```typescript
interface UseConfirmationReturn {
  confirm: (options: ConfirmationOptions) => Promise<boolean>;
}

function useConfirmation(): UseConfirmationReturn;
```

### Provider: `ConfirmationDialogProvider`

```typescript
function ConfirmationDialogProvider({ children }: { children: ReactNode }): JSX.Element;
```

Must wrap the application tree (currently in `App.tsx`). Renders the `ConfirmationDialog` component.

### Behavioral Contract

| Behavior | Contract | Status |
|----------|----------|--------|
| **Single dialog at a time** | Only one dialog is visible. Additional `confirm()` calls are queued. | ✅ Existing |
| **Queue processing** | When a dialog is resolved, the next queued request is immediately shown. | ✅ Existing |
| **Promise resolution** | `confirm()` returns `true` if user confirmed, `false` if canceled. | ✅ Existing |
| **Focus capture** | On open, `document.activeElement` is saved to `previousFocusRef`. | ✅ Existing |
| **Focus restoration** | On close, focus is returned to `previousFocusRef.current`. | ✅ Existing |
| **Async onConfirm** | If `onConfirm` is provided, it runs on confirm click with loading state. | ✅ Existing |
| **Error handling** | If `onConfirm` throws, the error message is displayed in-dialog. | ✅ Existing |
| **Loading guard** | Cancel and Escape are blocked while `isLoading` is true. | ✅ Existing |
| **Dismiss during loading** | Escape key and backdrop click must not dismiss while loading. | ⚠️ Verify |

### Enhancement: Queuing Robustness

The queue currently processes the next item in `processQueue()` after dialog close. Ensure:
1. Queue items preserve their `resolve` reference correctly across React re-renders.
2. If the provider unmounts while items are queued, all pending promises resolve with `false`.
3. Queue processing does not race with state updates (use `queueRef` not state for the queue).

These are defensive checks — the current implementation likely handles them, but they should be verified during implementation.

---

## Modified Hook: `useUnsavedChanges`

**Location**: `frontend/src/hooks/useUnsavedChanges.ts`

### Public API (Unchanged)

```typescript
interface UseUnsavedChangesOptions {
  isDirty: boolean;
  message?: string;
}

interface UseUnsavedChangesReturn {
  blocker: ReturnType<typeof useBlocker>;
  isBlocked: boolean;
}

function useUnsavedChanges(options: UseUnsavedChangesOptions): UseUnsavedChangesReturn;
```

### Behavioral Contract

| Behavior | Contract | Status |
|----------|----------|--------|
| **Browser guard** | `beforeunload` event fires when `isDirty` is true and user closes/refreshes tab. | ✅ Existing |
| **SPA guard** | `useBlocker` from react-router-dom blocks client-side navigation when `isDirty` is true. | ✅ Existing |
| **Blocker state** | `isBlocked` is `true` when a navigation attempt is blocked. | ✅ Existing |
| **Proceed** | Calling `blocker.proceed()` allows blocked navigation to continue. | ✅ Existing |
| **Reset** | Calling `blocker.reset()` cancels the navigation and stays on the page. | ✅ Existing |

No changes needed. This hook is already complete and correct.

---

## Existing Hook: `useCleanup`

**Location**: `frontend/src/hooks/useCleanup.ts`

### Public API (Unchanged)

```typescript
type CleanupState = 'idle' | 'loading' | 'confirming' | 'executing' | 'summary' | 'auditHistory';

interface UseCleanupReturn {
  state: CleanupState;
  preflightData: CleanupPreflightResponse | null;
  executeResult: CleanupExecuteResponse | null;
  error: string | null;
  permissionError: string | null;
  auditHistory: CleanupHistoryEntry[] | null;
  startPreflight: () => Promise<void>;
  confirmExecute: () => Promise<void>;
  cancel: () => void;
  dismiss: () => void;
  loadHistory: () => Promise<void>;
  showAuditHistory: () => void;
  closeAuditHistory: () => void;
}
```

### Behavioral Contract

The cleanup flow is a specialized multi-step confirmation that uses `CleanUpConfirmModal` rather than the generic `ConfirmationDialog`. This is acceptable because the cleanup modal displays a complex categorized impact summary (branches, PRs, orphaned issues) that exceeds what the generic dialog's description field can convey.

No changes to the hook. Accessibility improvements are applied to `CleanUpConfirmModal` component.

---

## Cross-Cutting Behavior Contracts

### Dialog Queuing

When a critical action triggers `confirm()` while another dialog is already open:

```
Time →
t1: confirm(A) called → Dialog A shown
t2: confirm(B) called → B queued (Promise pending)
t3: User resolves A   → Dialog A closes → Dialog B shown immediately
t4: User resolves B   → Dialog B closes → B's Promise resolved
```

**Contract**: Queued dialogs are shown in FIFO order. Each receives its own focus capture/restore cycle. No dialog is ever skipped.

### Focus Restoration Chain

When dialogs are queued, focus restoration follows this chain:

```
Element X triggers Dialog A → previousFocusRef = Element X
  Dialog A resolves → Dialog B shown immediately
    Dialog B's previousFocusRef = cancel button of Dialog A (or the last focused element)
      Dialog B resolves → Focus returns to Dialog B's previousFocusRef
```

**Note**: In practice, the previous focus ref for queued dialogs will be the dialog's own buttons. This is acceptable because the queue processes immediately — there's no moment where focus needs to return to the background.

### Error Recovery in Dialogs

When `onConfirm` throws an error:

```
1. Error message extracted from thrown Error object
2. error state set in DialogState
3. ConfirmationDialog displays error inline
4. Confirm button re-enabled (no longer loading)
5. Cancel button re-enabled
6. User can retry (click confirm again) or cancel
```

**Contract**: Errors never cause the dialog to close automatically. The user must explicitly choose to retry or cancel.

### Keyboard Interaction Matrix

| Key | Dialog State | Action |
|-----|-------------|--------|
| `Escape` | Idle (not loading) | Cancel and close |
| `Escape` | Loading | Blocked (no action) |
| `Tab` | Any | Cycle focus forward between interactive elements |
| `Shift+Tab` | Any | Cycle focus backward between interactive elements |
| `Enter` | Focus on button | Activate focused button |
| `Space` | Focus on button | Activate focused button |

### Screen Reader Expectations

| Event | Announcement |
|-------|-------------|
| Dialog opens | Title and description announced (via `aria-labelledby` + `aria-describedby`) |
| Error appears | Error text announced immediately (via `aria-live="assertive"`) |
| Loading starts | "Processing…" announced (via `aria-live="polite"`) |
| Dialog closes | Focus returns to trigger element (screen reader context restored) |
