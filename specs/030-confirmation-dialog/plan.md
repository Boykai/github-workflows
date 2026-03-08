# Implementation Plan: Confirmation Dialog for Critical User Actions

**Branch**: `030-confirmation-dialog` | **Date**: 2026-03-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/030-confirmation-dialog/spec.md`

## Summary

Implement a reusable confirmation dialog component that intercepts all critical and destructive user actions before execution. The solution replaces the existing `window.confirm()` calls (4 instances) and provides a shared `useConfirmation` hook + `ConfirmationDialog` component that any part of the application can invoke with customizable title, description, severity level, and button labels. The dialog meets WCAG 2.1 AA accessibility standards with focus trapping, keyboard navigation, ARIA attributes, and focus restoration. An async-aware loading state prevents duplicate submissions during in-flight operations. The component integrates with the existing portal-based modal pattern and Tailwind CSS design system already established in the codebase.

## Technical Context

**Language/Version**: TypeScript ~5.9 (frontend)
**Primary Dependencies**: React 19.2, Tailwind CSS v4, lucide-react 0.577, class-variance-authority 0.7
**Storage**: N/A — purely frontend component; no database changes
**Testing**: Vitest 4 + Testing Library + jest-axe (for accessibility assertions)
**Target Platform**: Desktop browsers (Chrome, Firefox, Safari, Edge)
**Project Type**: Web application (frontend-only change)
**Performance Goals**: Dialog render < 16ms (single frame); focus trap setup < 5ms
**Constraints**: No new UI library additions; must follow existing portal-based modal pattern; must not break any existing dialog behavior
**Scale/Scope**: 1 new component, 1 new hook, 1 new context provider, ~6 modified files replacing `window.confirm()` calls, optional tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 4 prioritized user stories (P1–P2), Given-When-Then acceptance scenarios, 10 functional requirements, 6 success criteria, edge cases documented |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (specify → plan → tasks → implement) |
| **IV. Test Optionality** | ✅ PASS | Tests not explicitly mandated in spec; jest-axe available for optional a11y tests |
| **V. Simplicity/DRY** | ✅ PASS | Single reusable component replaces 4 `window.confirm()` calls and consolidates multiple ad-hoc confirmation patterns; no new libraries required; extends existing Tailwind + lucide-react design system |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace back to spec FRs (FR-001–FR-010) |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow template structure |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 |
| **IV. Test Optionality** | ✅ PASS | No additional tests mandated; optional a11y tests documented in quickstart |
| **V. Simplicity/DRY** | ✅ PASS | One component + one hook + one context provider. Replaces `window.confirm()` and consolidates patterns from UnsavedChangesDialog, ConfirmChoreModal, and CleanUpConfirmModal into a generic contract. No premature abstraction — the component API is driven by the 4 existing `window.confirm()` call sites plus 3 existing custom modal patterns. |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/030-confirmation-dialog/
├── plan.md              # This file
├── research.md          # Phase 0: Research decisions (R1–R5)
├── data-model.md        # Phase 1: Entity definitions, types, state machines
├── quickstart.md        # Phase 1: Developer onboarding guide
├── contracts/
│   └── components.md    # Phase 1: Component interface contracts
├── checklists/
│   └── requirements.md  # Specification quality checklist (complete)
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── components/
│   │   └── ui/
│   │       └── confirmation-dialog.tsx  # NEW: Reusable ConfirmationDialog component
│   ├── hooks/
│   │   └── useConfirmation.ts           # NEW: Context + hook for imperative confirmation API
│   ├── components/
│   │   └── agents/
│   │       ├── AgentCard.tsx            # MODIFIED: Replace window.confirm with useConfirmation
│   │       └── AgentsPanel.tsx          # MODIFIED: Replace window.confirm with useConfirmation
│   │   └── chores/
│   │       └── ChoreCard.tsx            # MODIFIED: Replace window.confirm with useConfirmation
│   ├── pages/
│   │   └── AgentsPipelinePage.tsx       # MODIFIED: Replace window.confirm with useConfirmation
│   └── App.tsx                          # MODIFIED: Wrap with ConfirmationProvider
```

**Structure Decision**: Web application (frontend-only). The confirmation dialog is a purely presentational component with no backend changes. New files are placed in `frontend/src/components/ui/` (following the existing primitives pattern for `button.tsx`, `card.tsx`, `input.tsx`) and `frontend/src/hooks/` (following the existing custom hooks pattern). The `ConfirmationProvider` wraps the app at the root level in `App.tsx` to enable the imperative `useConfirmation()` hook from any component.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| Context + hook pattern (not prop-drilling) | The `useConfirmation()` hook enables any component to trigger a dialog without passing callbacks through the tree. This matches the spec requirement "can be applied across different parts of the application" (FR-005). The context provider renders a single dialog instance at the app root, preventing multiple dialogs (FR-009). | Prop-drilling (rejected: requires threading callbacks through unrelated components; doesn't scale as more actions need confirmation). Render-prop pattern (rejected: verbose; each call site would need its own dialog render). |
| Portal-based rendering (consistent with codebase) | All existing modals in the codebase use `createPortal()` or fixed overlays. Keeping the same pattern ensures visual consistency and z-index behavior. | `<dialog>` HTML element (rejected: browser support for `<dialog>` styling varies; existing codebase doesn't use native dialogs; would introduce an inconsistent pattern). |
| Single severity-based visual variant (not separate components) | One component with a `variant` prop (`"danger"` \| `"warning"` \| `"info"`) controls the visual treatment (icon, color scheme). This avoids creating separate `DangerDialog`, `WarningDialog`, etc. | Separate components per severity (rejected: DRY violation; the dialogs are structurally identical, only colors/icons differ). |
