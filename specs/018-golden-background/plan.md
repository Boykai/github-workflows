# Implementation Plan: Add Golden Background to App

**Branch**: `018-golden-background` | **Date**: 2026-03-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/018-golden-background/spec.md`

## Summary

Apply a golden background color globally across the application by updating the CSS custom properties (design tokens) in the existing theming system. The `--background` variable in `:root` is changed to a gold tone (#FFD700 equivalent in HSL), with a deepened dark-gold variant for `.dark` mode. The `--foreground` and related text tokens are verified to already meet WCAG AA 4.5:1 contrast compliance against the updated background. No new dependencies, API changes, or structural changes are needed — this is a pure CSS token update scoped to `frontend/src/index.css`.

## Technical Context

**Language/Version**: TypeScript ~5.4 (frontend), CSS3 with Tailwind CSS 3.4
**Primary Dependencies**: React 18.3, Tailwind CSS 3.4, tailwindcss-animate, Vite
**Storage**: N/A (no data persistence changes)
**Testing**: Vitest 4 + Testing Library (frontend); visual regression review (manual)
**Target Platform**: Docker (Linux) — web application, all modern browsers (Chrome, Firefox, Safari, Edge)
**Project Type**: Web application (frontend + backend); changes scoped to frontend only
**Performance Goals**: N/A — solid color background, negligible render cost
**Constraints**: WCAG AA minimum 4.5:1 contrast ratio for all foreground text against golden background
**Scale/Scope**: Single global CSS variable change; affects all pages via `body { @apply bg-background }` rule

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development — ✅ PASS
Spec exists at `specs/018-golden-background/spec.md` with 4 prioritized user stories (P1-P2), Given-When-Then acceptance scenarios, edge cases, and functional requirements (FR-001 through FR-008).

### II. Template-Driven Workflow — ✅ PASS
All artifacts follow canonical templates. Plan uses `plan-template.md`. Spec uses `spec-template.md`.

### III. Agent-Orchestrated Execution — ✅ PASS
Plan produced by `/speckit.plan` agent. Tasks will be produced by `/speckit.tasks`. Clear handoffs defined.

### IV. Test Optionality with Clarity — ✅ PASS
Tests not mandated in spec. No TDD approach specified. Visual regression review is manual per spec assumptions. No automated test infrastructure changes needed for a CSS token update.

### V. Simplicity and DRY — ✅ PASS
Implementation modifies exactly one file (`frontend/src/index.css`) to update existing CSS custom properties. No new abstractions, no new files, no new dependencies. The golden color is defined in a single location (the `--background` CSS variable) and consumed everywhere via the existing `hsl(var(--background))` pattern in Tailwind config. This is the simplest possible approach.

## Project Structure

### Documentation (this feature)

```text
specs/018-golden-background/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   └── index.css          # MODIFY — update :root and .dark CSS custom properties
└── tailwind.config.js     # NO CHANGE — already consumes hsl(var(--background))
```

**Structure Decision**: Web application (frontend + backend). Changes are scoped entirely to the frontend styling layer. Only `frontend/src/index.css` requires modification — the existing Tailwind configuration already maps `background` to `hsl(var(--background))`, and the body element already applies `@apply bg-background`. No backend changes needed.

## Complexity Tracking

> No violations detected. No complexity justifications needed.
