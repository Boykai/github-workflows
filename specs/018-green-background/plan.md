# Implementation Plan: Add Green Background Color to App

**Branch**: `018-green-background` | **Date**: 2026-03-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/018-green-background/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Apply a green background color to the application by updating the existing HSL-based CSS custom property `--background` in `frontend/src/index.css`. The change targets the `:root` (light mode) and `.dark` (dark mode) selectors, replacing the current white/dark-blue backgrounds with green equivalents (#4CAF50 for light, #2E7D32 for dark). The foreground text color (`--foreground`) will be updated to white to maintain WCAG AA contrast. No new dependencies, no structural changes, no backend changes.

## Technical Context

**Language/Version**: TypeScript 5.x (frontend), Python 3.11 (backend — not affected)
**Primary Dependencies**: React 18, Tailwind CSS 3, Vite 5, shadcn/ui component library (Radix primitives)
**Storage**: N/A (frontend-only CSS change)
**Testing**: Vitest (unit), Playwright (e2e) — visual verification recommended, automated contrast check optional
**Target Platform**: Web (all modern browsers, responsive — mobile/tablet/desktop)
**Project Type**: Web application (frontend + backend monorepo)
**Performance Goals**: N/A (CSS variable change has zero runtime cost)
**Constraints**: WCAG AA contrast ratio ≥ 4.5:1 for normal text against green background
**Scale/Scope**: Single file change (`frontend/src/index.css`), ~4 lines modified

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | `spec.md` exists with prioritized user stories, acceptance scenarios, and scope |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase runs as dedicated agent with clear input/output |
| IV. Test Optionality | ✅ PASS | Tests not explicitly mandated in spec; visual verification is sufficient for a CSS-only change |
| V. Simplicity and DRY | ✅ PASS | Change modifies existing CSS custom properties in a single file; no new abstractions, no new files |

**Gate Result**: ✅ ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/018-green-background/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (empty — no API contracts for CSS change)
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── index.css            # ← MODIFIED: CSS custom properties for green background
│   ├── main.tsx             # Entry point (ThemeProvider wraps App)
│   ├── components/
│   │   ├── ThemeProvider.tsx # Dark/light/system theme toggling (unchanged)
│   │   └── ui/              # shadcn/ui components (unchanged)
│   ├── pages/               # Application pages (unchanged)
│   └── hooks/               # Custom hooks (unchanged)
├── tailwind.config.js       # Tailwind config consuming CSS vars (unchanged)
└── package.json

backend/                     # Not affected by this change
```

**Structure Decision**: Web application layout. Only `frontend/src/index.css` is modified. The existing design token system (CSS custom properties in `:root` / `.dark`) is used as-is. No new files are created in source code.

## Complexity Tracking

> No violations — no complexity justifications needed.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | — | — |
