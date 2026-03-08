# Research: Confirmation Dialog for Critical User Actions

**Feature**: 030-confirmation-dialog | **Date**: 2026-03-08

## R1: Dialog Architecture — Context + Hook vs. Component-Only

**Task**: Determine the best architecture for a reusable confirmation dialog that can be invoked from any part of the application without prop-drilling.

**Decision**: Implement a `ConfirmationProvider` (React Context) at the app root that renders a single `ConfirmationDialog` instance. Expose a `useConfirmation()` hook that returns a `confirm()` function. Calling `confirm({ title, description, ... })` returns a `Promise<boolean>` that resolves when the user confirms (`true`) or cancels (`false`). This imperative API allows any component to trigger a confirmation dialog without rendering it locally or passing callbacks through the tree.

**Rationale**: The existing codebase has 4 `window.confirm()` calls (AgentCard.tsx:63, AgentsPanel.tsx:57, ChoreCard.tsx:120, AgentsPipelinePage.tsx:126) that all follow the same imperative pattern: `if (window.confirm(message)) { doAction(); }`. The context + hook approach preserves this imperative flow — developers replace `window.confirm(msg)` with `const ok = await confirm({ title, description }); if (ok) { doAction(); }`. The migration path is minimal. The single dialog instance at the root prevents multiple overlapping dialogs (FR-009). The Promise-based API naturally supports async confirmation flows (FR-006) — after the user confirms, the calling code can show loading state, execute the async operation, and handle errors.

**Alternatives Considered**:
- **Component-only (render at each call site)**: Rejected — requires each component to manage dialog open/close state, render the dialog JSX, and handle callbacks. This duplicates dialog management logic across 7+ call sites. It also makes preventing overlapping dialogs (FR-009) difficult since each component controls its own instance.
- **Global event emitter**: Rejected — breaks React's unidirectional data flow. Event-based systems are harder to debug and test. The Context API is the idiomatic React solution for cross-component communication.
- **Redux/Zustand global store**: Rejected — the codebase does not use Redux or Zustand. Adding a state management library for a single dialog is over-engineered and violates Constitution Principle V (simplicity).

---

## R2: Focus Management and Accessibility (WCAG 2.1 AA)

**Task**: Determine the accessibility implementation approach for the confirmation dialog, including focus trapping, ARIA attributes, and keyboard navigation.

**Decision**: Implement a custom focus trap within the dialog using a `useEffect` that captures focusable elements on mount and cycles Tab focus between them. Use native ARIA attributes: `role="alertdialog"`, `aria-modal="true"`, `aria-labelledby` (pointing to the title element), and `aria-describedby` (pointing to the description element). On open, move focus to the cancel button (safest default — doesn't accidentally trigger the destructive action). On close, restore focus to the element that triggered the dialog using `document.activeElement` captured before opening. Support Escape key to cancel.

**Rationale**: The existing modals in the codebase (CleanUpConfirmModal, ConfirmChoreModal, UnsavedChangesDialog) implement partial keyboard support (Escape to close) but lack focus trapping, ARIA roles, and focus restoration. The spec explicitly requires WCAG 2.1 AA compliance (FR-007), which mandates all three. Using `role="alertdialog"` (instead of `role="dialog"`) is correct for confirmation dialogs because the dialog demands an immediate response and interrupts the user's workflow — this is the WAI-ARIA recommended role for confirmation prompts. Moving focus to the cancel button on open follows the principle of least surprise — it prevents accidental confirmation via Enter key. The custom focus trap implementation is lightweight (~30 lines) and avoids adding a dependency like `focus-trap-react`.

**Alternatives Considered**:
- **`focus-trap-react` library**: Rejected — adds a dependency for ~30 lines of custom code. The codebase has no existing focus trap library, and adding one for a single component violates Constitution Principle V (simplicity/YAGNI). The custom implementation is straightforward and well-tested in the web accessibility community.
- **HTML `<dialog>` element**: Rejected — while `<dialog>` provides built-in focus trapping and `showModal()`, its styling support varies across browsers (particularly backdrop styling). The existing codebase uses div-based overlays exclusively. Mixing patterns would create inconsistency. Additionally, `<dialog>` Escape key behavior would need to be intercepted to prevent default close and route through our cancel logic.
- **`@radix-ui/react-alert-dialog`**: Rejected — the project only uses `@radix-ui/react-slot` (for the Button component). Adding a full Radix dialog primitive adds bundle size and a dependency. The custom implementation is tailored to our exact requirements and consistent with existing modal patterns.

---

## R3: Visual Severity Variants

**Task**: Determine how to visually distinguish between different severity levels (destructive, warning, informational) in the confirmation dialog.

**Decision**: Support three visual variants via a `variant` prop: `"danger"` (destructive actions like deletion), `"warning"` (irreversible but non-destructive actions like bulk updates), and `"info"` (standard confirmations). Each variant controls: (1) the icon displayed (AlertTriangle for danger/warning, Info for info), (2) the icon background color (red-100/red-500 for danger, amber-100/amber-500 for warning, blue-100/blue-500 for info), and (3) the confirm button variant (Button `variant="destructive"` for danger, Button `variant="default"` for warning/info). The cancel button always uses `variant="outline"`.

**Rationale**: The spec requires visual severity indication (FR-008). The existing codebase already uses this color pattern: `UnsavedChangesDialog` uses amber (warning), `ConfirmChoreModal` uses yellow/green (info → success), and `CleanUpConfirmModal` uses red (danger). Mapping to three variants keeps the API simple while covering all use cases. Using `lucide-react` icons (already in the project) maintains visual consistency. The `Button` component already has a `destructive` variant (red styling) that's purpose-built for this use case.

**Alternatives Considered**:
- **Free-form color props**: Rejected — gives too much flexibility, leading to inconsistent usage across the app. Constrained variants enforce a design system.
- **Five severity levels (critical, high, medium, low, info)**: Rejected — over-granular for a confirmation dialog. Users can't meaningfully distinguish between 5 severity levels in a modal prompt. Three levels (danger, warning, info) cover all practical use cases.
- **No visual distinction**: Rejected — spec explicitly requires it (FR-008). A generic dialog for all actions would fail to communicate severity.

---

## R4: Async Confirmation and Loading State

**Task**: Determine how to handle the loading state when the confirmed action involves an asynchronous operation (e.g., API call).

**Decision**: The `confirm()` function from `useConfirmation()` returns a `Promise<boolean>`. After the promise resolves with `true`, the calling code is responsible for executing the async operation and managing its loading state. The dialog itself does NOT manage the async operation — it closes immediately after the user confirms. This keeps the dialog's responsibility focused (prompt → collect decision → return result) and avoids coupling the dialog to specific API call patterns.

**Rationale**: The existing `window.confirm()` pattern already works this way: `if (window.confirm(msg)) { mutation.mutate(id); }`. The mutation's loading state (`mutation.isPending`) is already managed by TanStack Query in each component. Trying to pass the async operation into the dialog would require complex callback threading and duplicate the mutation state management. The spec mentions async loading state (FR-006), which is satisfied by the calling component disabling its trigger button while the mutation is in flight — this is the existing pattern used throughout the codebase (e.g., `isLoading` props on buttons in `ChoreCard.tsx`, `ToolsPanel.tsx`).

**Alternatives Considered**:
- **Dialog manages async operation**: Rejected — would require passing the mutation function into the dialog, rendering loading/success/error states within the dialog, and managing dialog lifecycle around the operation. This couples the dialog to specific operations and violates single-responsibility. Each calling component already has TanStack Query mutations that handle loading/error state.
- **Two-phase dialog (confirm → loading → result)**: Rejected — the `BulkModelUpdateDialog` and `ConfirmChoreModal` already implement this pattern for complex multi-step operations. The generic confirmation dialog should be simpler. Components that need the two-phase pattern can continue using their custom dialogs.

---

## R5: Preventing Overlapping Dialogs

**Task**: Determine how to ensure only one confirmation dialog is active at a time (FR-009).

**Decision**: The `ConfirmationProvider` maintains a single dialog state. When `confirm()` is called while a dialog is already open, the new request is queued. The queued request's promise remains pending until the current dialog is resolved, at which point the next queued dialog opens automatically. In practice, overlapping confirmations are rare (they require simultaneous user actions), so the queue will almost always be empty.

**Rationale**: The single-instance pattern is enforced architecturally by having one `ConfirmationDialog` rendered at the app root. This is simpler than attempting to prevent individual components from rendering their own dialogs. The queue approach handles the edge case gracefully without dropping requests or throwing errors.

**Alternatives Considered**:
- **Reject concurrent requests (throw error)**: Rejected — would cause silent failures if a component doesn't handle the error. The queue approach is more resilient.
- **Replace current dialog with new one**: Rejected — would resolve the current dialog's promise as cancelled without user input, potentially causing confusing behavior in the component that triggered the first dialog.
- **Multiple dialog instances (z-index stacking)**: Rejected — spec explicitly prohibits it (FR-009). Stacked dialogs create confusing UX.
