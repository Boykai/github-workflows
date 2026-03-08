# Research: Confirmation Flow for Critical Actions

**Feature**: 001-confirmation-flow | **Date**: 2026-03-08

## R1: Modal Implementation Pattern — Custom vs. Library

**Task**: Determine the best approach for implementing the confirmation dialog given the existing codebase patterns and dependencies.

**Decision**: Build a custom confirmation dialog component using the same patterns as the 10+ existing modals in the codebase: fixed positioning with `inset-0`, backdrop overlay with `bg-black/50`, relative inner container with Tailwind styling, and lucide-react icons for visual feedback. No external dialog library will be added.

**Rationale**: The codebase has a well-established custom modal pattern used consistently across `UnsavedChangesDialog`, `ConfirmChoreModal`, `CleanUpConfirmModal`, `AddAgentModal`, `BulkModelUpdateDialog`, and others. All modals use:
- Fixed `inset-0 z-50` (or higher) container
- Absolute backdrop with `bg-black/50` and click-to-dismiss handler
- Relative inner modal with `rounded-2xl border shadow-xl` styling
- `lucide-react` icons (`AlertTriangle`, `CheckCircle`, `Trash2`, etc.)
- `Button` component from `components/ui/button.tsx` with `variant` props
- Manual keyboard event listeners for Escape key handling

The only Radix UI dependency is `@radix-ui/react-slot` (v1.2.4) for the `Slot` component in `button.tsx` — no Radix Dialog or AlertDialog is installed. Adding a dialog library would create an inconsistent pattern where one modal uses a library while 10+ others are custom-built.

**Alternatives Considered**:
- **@radix-ui/react-alert-dialog**: Rejected — adds a new dependency (~8 KB). While it provides excellent accessibility primitives (focus trapping, ARIA attributes), the codebase has no precedent for Radix dialog usage. Implementing focus trapping and ARIA manually is straightforward and keeps the codebase consistent. Also rejected per Constitution Principle V (simplicity — YAGNI).
- **@headlessui/react**: Rejected — adds a larger dependency (~30 KB). Designed for use with Tailwind CSS, but the project already has a working custom modal system. Introducing a second pattern would increase cognitive load for developers.
- **shadcn/ui AlertDialog**: Rejected — shadcn/ui is not installed in the project. While it generates local components (no runtime dependency), it requires `@radix-ui/react-alert-dialog` as a peer dependency, which brings us back to the first alternative.

---

## R2: Imperative vs. Declarative Confirmation API

**Task**: Determine the best developer API for triggering confirmation dialogs — should callers render a component or call a function?

**Decision**: Provide an imperative `useConfirmation()` hook that returns a `confirm(options)` function. This function returns a `Promise<boolean>` and renders the dialog via React Context at the app root. The API mirrors the native `window.confirm()` pattern for easy migration:

```typescript
// Before (native)
if (window.confirm('Delete agent?')) { deleteMutation.mutate(id); }

// After (useConfirmation)
const { confirm } = useConfirmation();
const confirmed = await confirm({
  title: 'Delete Agent',
  description: `Remove agent "${agent.name}"? This opens a PR to delete the repo files.`,
  variant: 'danger',
  confirmLabel: 'Delete',
});
if (confirmed) { deleteMutation.mutate(id); }
```

The Context Provider (`ConfirmationDialogProvider`) is added once at the app root (in `App.tsx`) and manages dialog state, queue, and rendering.

**Rationale**: The existing codebase uses the `if(confirm(msg)){action()}` imperative pattern at all 4 call sites. An imperative hook preserves this pattern, making migration a minimal diff — the call structure stays the same, only the `confirm()` function changes. A declarative approach (rendering `<ConfirmationDialog>` at each call site) would require restructuring each handler to manage `open`/`onConfirm`/`onCancel` state, which is more invasive. The Context-based approach also naturally enforces the single-dialog constraint (FR-016) — only one dialog state exists in the provider.

**Alternatives Considered**:
- **Declarative component at each call site**: Rejected — requires each consumer to manage `isOpen` state, `onConfirm` callback, and `onCancel` callback. This creates 3 additional state variables per call site (vs. 0 with the hook). Also harder to enforce the single-dialog constraint across independent components.
- **Global event emitter (non-React)**: Rejected — bypasses React's rendering model, making it harder to test and debug. The React Context approach integrates naturally with the component tree and supports Testing Library's `render()` pattern.
- **Render prop pattern**: Rejected — requires wrapping each trigger in a render prop component, which is more verbose than the hook approach. React hooks are the standard API pattern in this codebase.

---

## R3: Focus Management and Accessibility Implementation

**Task**: Determine how to implement WCAG 2.1 AA compliant focus management (trapping, restoration) without a UI library.

**Decision**: Implement focus management manually using three techniques:

1. **Focus trapping**: On dialog open, query all focusable elements within the dialog container (`button`, `[tabindex]`, `a[href]`, `input`, `select`, `textarea`). Intercept `Tab` and `Shift+Tab` keydown events to cycle focus within the dialog. When Tab would move past the last element, wrap to the first; when Shift+Tab would move before the first, wrap to the last.

2. **Initial focus**: On dialog open, focus the cancel button (not the destructive action button) to prevent accidental confirmation. This follows the WAI-ARIA dialog pattern recommendation: "When a dialog opens, focus is typically set to the first focusable element or the element that provides a non-destructive action."

3. **Focus restoration**: Before opening the dialog, capture `document.activeElement` as a ref. On dialog close (confirm, cancel, or Escape), restore focus to the captured element via `previousFocusRef.current?.focus()`.

4. **ARIA attributes**: The dialog container gets `role="dialog"`, `aria-modal="true"`, `aria-labelledby` pointing to the title element's `id`, and `aria-describedby` pointing to the description element's `id`.

**Rationale**: The existing modals in the codebase have inconsistent accessibility support — some have `aria-modal="true"` (CleanUpConfirmModal), most do not. None implement focus trapping. The confirmation dialog is a high-priority target for accessibility because it guards destructive actions — a user who cannot navigate the dialog may accidentally trigger or miss a critical confirmation. Manual focus trapping is well-documented in the WAI-ARIA Authoring Practices (Dialog pattern) and requires ~20 lines of code. The initial-focus-on-cancel pattern is specifically recommended for destructive confirmation dialogs to prevent accidental data loss.

**Alternatives Considered**:
- **`focus-trap-react` library**: Rejected — adds a dependency (~4 KB + `tabbable` peer dep). The focus trapping logic is straightforward to implement manually. The library is most valuable when trapping focus in complex forms with many focusable elements; a confirmation dialog has only 2 buttons.
- **`inert` attribute on background content**: Considered as a complement — the `inert` HTML attribute hides background content from assistive technologies and prevents focus. Browser support is good (Chrome 102+, Firefox 112+, Safari 15.5+). However, this requires adding `inert` to the app root on dialog open and removing it on close, which is fragile in a React SPA. The focus-trap approach is more reliable and self-contained.
- **Focus on confirm button initially**: Rejected — violates accessibility best practice. Focusing the destructive action button means a user pressing Enter immediately after dialog open would trigger the action without reading the prompt.

---

## R4: Async Confirmation and Error Handling Strategy

**Task**: Determine how the confirmation dialog should handle async operations (loading states, errors, retries) after the user clicks "Confirm."

**Decision**: The `onConfirm` handler in the dialog supports both sync and async patterns:

1. **Promise-based `confirm()` API (primary pattern)**: The `confirm()` function from `useConfirmation` returns a `Promise<boolean>`. The dialog resolves the promise with `true` (confirmed) or `false` (cancelled). The caller is responsible for executing the action and handling errors. This is the simple migration path from `window.confirm()`.

2. **Async `onConfirm` callback (enhanced pattern)**: For use cases that need loading states and error display within the dialog (FR-013, FR-014), the confirmation options accept an optional `onConfirm` async callback. When provided:
   - The dialog shows a loading spinner on the confirm button after click
   - The confirm button is disabled during the async operation
   - If the callback throws, the error message is displayed inline in the dialog
   - A "Retry" option re-enables the confirm button
   - The dialog only closes on successful completion

**Rationale**: The two-tier approach covers both simple and complex use cases. The simple `Promise<boolean>` pattern handles 3 of the 4 existing `window.confirm()` call sites where the action is a TanStack Query mutation (error handling is already managed by the mutation's `onError` callback and toast notifications). The async `onConfirm` pattern is available for cases where in-dialog error display is desired (e.g., bulk operations where partial failure feedback is important).

**Alternatives Considered**:
- **Always-async with in-dialog error handling**: Rejected — over-engineered for simple delete confirmations where the action is a single mutation. The existing toast notification system already handles mutation errors. Forcing all confirmations through an async pattern adds unnecessary complexity to simple use cases.
- **Sync-only (no loading state)**: Rejected — violates FR-013 (loading indicator) and FR-014 (error display). Some confirmations (like bulk operations) benefit from showing progress within the dialog.
- **Separate `ConfirmationDialog` and `AsyncConfirmationDialog` components**: Rejected — duplicates rendering logic. A single component with optional async support is simpler.

---

## R5: Z-Index Stacking and Single-Dialog Constraint

**Task**: Determine how to ensure only one confirmation dialog is displayed at a time and how it coexists with existing modals.

**Decision**: 
1. **Single dialog constraint**: The `ConfirmationDialogProvider` maintains a single `dialogState` ref. When `confirm()` is called while a dialog is already open, the new request is queued. Once the current dialog is resolved, the next queued request is displayed. This prevents overlapping dialogs (FR-016).

2. **Z-index stacking**: The confirmation dialog uses `z-[60]`, which is above the standard modal layer (`z-50`) used by most modals but below `z-[2000]` used by `CleanUpConfirmModal`. This ensures the confirmation dialog can overlay other modals (e.g., confirming a destructive action triggered from within an agent editor modal) while not interfering with the board cleanup modal's critical stacking.

3. **Backdrop interaction**: The backdrop uses `bg-black/50` consistent with existing modals. Clicking the backdrop dismisses the dialog (treated as cancel, per FR-006). During an async loading state, backdrop clicks are disabled to prevent dismissal mid-operation.

**Rationale**: The existing z-index layers are: `z-50` (standard modals), `z-[60]` (ConfirmChoreModal), `z-[2000]` (CleanUpConfirmModal). The confirmation dialog at `z-[60]` matches the precedent set by the chore confirmation modal. The queue-based approach for the single-dialog constraint is simple (a basic array queue) and deterministic — requests are processed in order with no race conditions.

**Alternatives Considered**:
- **Reject duplicate requests (throw error)**: Rejected — poor UX. If a user rapidly clicks two delete buttons, the second click should queue rather than error. Queuing is more forgiving and handles edge cases gracefully.
- **Stack multiple dialogs (z-index + offset)**: Rejected — confusing UX. Multiple overlapping confirmation dialogs would overwhelm the user. The queue approach ensures the user deals with one decision at a time.
- **Portal-based rendering**: Considered — some existing modals use `createPortal()` (e.g., CleanUpConfirmModal). However, since the confirmation dialog is rendered via Context at the app root, it's already at the top level of the component tree. A portal is unnecessary and adds complexity without benefit.

---

## R6: Content Overflow and Long Description Handling

**Task**: Determine how to handle confirmation dialogs with very long content (e.g., bulk actions affecting hundreds of items).

**Decision**: The dialog description area uses a scrollable container with `max-h-[60vh] overflow-y-auto` styling. The action buttons (Confirm/Cancel) are rendered outside the scrollable area in a fixed footer, ensuring they are always visible regardless of content length (FR-015). The dialog itself has a `max-w-md` width constraint (matching existing modal patterns) and a `max-h-[85vh]` overall height limit.

**Rationale**: The edge case of "bulk action affecting hundreds of items" (from spec) requires the description to be scrollable. Placing the buttons in a fixed footer guarantees they are accessible without scrolling. The `60vh` max height for the scrollable area leaves room for the title, footer buttons, and some viewport padding. The `md` width constraint (448px) is consistent with the existing `UnsavedChangesDialog` and `ConfirmChoreModal` modals.

**Alternatives Considered**:
- **Truncate content with "Show more"**: Rejected — users should see the full context before confirming a destructive action. Hiding information behind a "Show more" toggle could lead to uninformed confirmations.
- **Full-width dialog for long content**: Rejected — a wider dialog would break visual consistency with existing modals. The scrollable content area handles the overflow within the standard width.
- **Collapsible sections**: Rejected — adds interaction complexity to a dialog that should be quick to read and act on. A simple scroll is more straightforward.

---

## R7: Double-Click Prevention Strategy

**Task**: Determine how to prevent duplicate execution when the user rapidly clicks the confirm button.

**Decision**: Implement a two-layer prevention strategy:

1. **Immediate UI disable**: On confirm button click, set `isLoading: true` in the dialog state. This disables the button via the `disabled` attribute and shows a spinner icon replacing the button text. The disable happens synchronously before any async work begins.

2. **Promise guard**: The `confirm()` function in the hook resolves only once. If the promise has already been resolved (either by confirm or cancel), subsequent calls to the resolve function are no-ops. This prevents the edge case where a click event fires twice before the state update disables the button.

**Rationale**: The UI disable handles 99.9% of double-click scenarios — the button becomes non-interactive immediately on the first click. The promise guard is a defense-in-depth measure for the theoretical race condition where two click events are queued in the same microtask. Together, they satisfy FR-013 ("confirm button MUST be disabled immediately after activation") and the edge case requirement ("prevent duplicate execution by disabling the confirm button immediately").

**Alternatives Considered**:
- **Debounce the click handler**: Rejected — introduces a delay before the action executes, which feels sluggish. Immediate disable is both faster and more reliable.
- **Mutation `isPending` check from TanStack Query**: Rejected — this is a concern of the confirmation dialog, not the mutation. The dialog should prevent re-submission regardless of what the caller does with the confirmed result.
- **`pointer-events: none` CSS**: Rejected — less reliable than the `disabled` attribute. Disabled buttons also communicate their state to screen readers.
