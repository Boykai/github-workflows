# Implementation Plan: Confirmation Flow for Critical Actions

**Branch**: `001-confirmation-flow` | **Date**: 2026-03-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-confirmation-flow/spec.md`

## Summary

Replace all native `window.confirm()` calls across Project Solune with a reusable, accessible `ConfirmationDialog` component that provides consistent confirmation flows for destructive and state-changing actions. The component supports customizable title, description, severity levels (danger/warning/info), async confirm handlers with loading states, error display with retry capability, and full WCAG 2.1 AA compliance (focus trapping, ARIA attributes, Escape dismissal, focus restoration). Four existing `window.confirm()` call sites (agent deletion, pipeline deletion, chore deletion, clear pending agents) will be retrofitted, and the component will be available for all future critical actions. The implementation is frontend-only — no backend changes required — using the project's existing custom modal patterns with Tailwind CSS and lucide-react icons.

## Technical Context

**Language/Version**: TypeScript ~5.9 (frontend), Python 3.13 (backend — no changes needed)
**Primary Dependencies**: React 19.2, TanStack Query v5.90, Tailwind CSS v4.2, lucide-react 0.577, class-variance-authority 0.7 (frontend)
**Storage**: N/A — no storage changes; confirmation is a pure UI concern
**Testing**: Vitest 4 + Testing Library (frontend unit tests)
**Target Platform**: Desktop browsers (Chrome, Firefox, Safari, Edge); responsive design
**Project Type**: Web application (frontend/ + backend/)
**Performance Goals**: Dialog render < 16ms (single frame); dialog open/close animation < 200ms; zero layout shift on dialog open
**Constraints**: No new UI library additions (use existing custom modal patterns); must coexist with existing modals (z-index stacking); must not break existing confirmation behavior during incremental adoption
**Scale/Scope**: 1 new reusable component, 1 new React hook, 4 retrofitted call sites, 0 backend changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 4 prioritized user stories (P1–P2), Given-When-Then acceptance scenarios per story, 16 functional requirements (FR-001–FR-016), 8 success criteria (SC-001–SC-008), 6 edge cases, clear scope boundaries |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (specify → plan → tasks → implement) |
| **IV. Test Optionality** | ✅ PASS | Tests mentioned in acceptance criteria ("Unit and/or integration tests cover the confirmation logic") — will include test tasks for the reusable component |
| **V. Simplicity/DRY** | ✅ PASS | Single reusable component replaces 4 duplicated `window.confirm()` patterns; follows existing custom modal conventions (no new libraries); extends established Tailwind + lucide-react patterns |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace back to spec FRs (FR-001–FR-016) and user stories (US-1–US-4) |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow template structure |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 task generation |
| **IV. Test Optionality** | ✅ PASS | Tests included per spec acceptance criteria; component tests for ConfirmationDialog, hook tests for useConfirmation |
| **V. Simplicity/DRY** | ✅ PASS | One component (`ConfirmationDialog`) + one hook (`useConfirmation`) replaces all `window.confirm()` usage. No new libraries. Follows existing modal patterns (fixed positioning, backdrop, Tailwind styling, lucide-react icons). The hook provides an imperative API that matches the `if(confirm(msg)){action()}` pattern for easy migration. |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/001-confirmation-flow/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── api.md           # No backend API changes — documents existing endpoints used
│   └── components.md    # Component interface contracts
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── components/
│   │   └── ui/
│   │       └── confirmation-dialog.tsx   # NEW: Reusable confirmation dialog component
│   ├── hooks/
│   │   └── useConfirmation.ts            # NEW: Imperative confirmation hook with queue management
│   ├── components/
│   │   ├── agents/
│   │   │   ├── AgentCard.tsx             # MODIFIED: Replace window.confirm() with useConfirmation
│   │   │   └── AgentsPanel.tsx           # MODIFIED: Replace window.confirm() with useConfirmation
│   │   ├── chores/
│   │   │   └── ChoreCard.tsx             # MODIFIED: Replace window.confirm() with useConfirmation
│   │   └── pipeline/                     # (No changes — pipeline delete is in page component)
│   ├── pages/
│   │   └── AgentsPipelinePage.tsx        # MODIFIED: Replace window.confirm() with useConfirmation
│   └── App.tsx                           # MODIFIED: Add ConfirmationDialogProvider at app root
```

**Structure Decision**: Web application (frontend/ + backend/). All changes are in the `frontend/` directory. The confirmation dialog is placed in `components/ui/` following the existing pattern for reusable UI primitives (`button.tsx`, `card.tsx`, `input.tsx`). The hook is placed in `hooks/` following the existing pattern (`useAgents.ts`, `useBoardControls.ts`). No backend changes are needed — confirmation is a pure frontend UI concern.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| Context-based hook (`useConfirmation`) | Provides an imperative `confirm()` API via React Context that mirrors the native `window.confirm()` pattern, making migration trivial. The context renders a single dialog instance at the app root, ensuring only one dialog is open at a time (FR-016). | Direct component usage at each call site (rejected: duplicates dialog rendering logic, harder to enforce single-dialog constraint, more code per call site) |
| Custom modal (no library) | Follows the existing codebase pattern of custom modals with Tailwind CSS. All 10+ existing modals use fixed positioning + backdrop + Tailwind styling. Adding Radix Dialog or Headless UI for one component would introduce an inconsistent pattern. | Radix AlertDialog (rejected: adds dependency, inconsistent with 10+ existing custom modals; YAGNI — Principle V) |
| Single severity-based component | One `ConfirmationDialog` component with a `variant` prop (danger/warning/info) covers all confirmation use cases. The variant controls button color and icon. | Separate components per severity (rejected: violates DRY; a single component with variants is simpler and more maintainable) |
| Async confirm handler with loading state | The `onConfirm` callback returns a Promise, enabling the dialog to show a loading spinner and disable the confirm button during async operations (FR-013). Errors are caught and displayed inline (FR-014). | Fire-and-forget confirm (rejected: cannot show loading state or handle errors within the dialog; user sees no feedback) |
