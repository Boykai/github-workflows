# Implementation Plan: Add Green Background Color to App

**Branch**: `016-green-background` | **Date**: 2026-03-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/016-green-background/spec.md`

## Summary

Apply a green background color (`#22c55e`) globally to the application by updating the existing HSL-based CSS custom property `--background` in `frontend/src/index.css`. The project uses Tailwind CSS with a shadcn/ui design token system where all colors are defined as HSL values in `:root` and `.dark` selectors. The body already applies `bg-background`, so changing the `--background` variable propagates the green to all pages. Foreground text colors (`--foreground`) must be updated to maintain WCAG AA contrast ratios (4.5:1 for body text, 3:1 for large text/UI). A darker green variant (`#166534`) is used for dark mode. See [research.md](./research.md) for decision rationale.

## Technical Context

**Language/Version**: TypeScript 5.4 (frontend), Python 3.12 (backend — no changes needed)
**Primary Dependencies**: React 18.3, Vite 5.4, TailwindCSS 3.4, shadcn/ui (Radix UI primitives)
**Storage**: N/A
**Testing**: Vitest + React Testing Library (frontend)
**Target Platform**: Modern browsers (Chrome, Firefox, Safari, Edge), mobile and desktop viewports
**Project Type**: Web application (frontend + backend)
**Performance Goals**: N/A — CSS-only change, no runtime performance impact
**Constraints**: WCAG AA contrast ratios (4.5:1 body text, 3:1 large text/UI components)
**Scale/Scope**: 1 file change (`frontend/src/index.css`), potentially minor foreground color adjustments in the same file

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Check (Phase 0 Gate)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | `spec.md` exists with 3 prioritized user stories (P1×2, P2×1), Given-When-Then scenarios, 8 FRs, 4 edge cases |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated Execution | ✅ PASS | `speckit.plan` agent produces plan.md and Phase 0/1 artifacts |
| IV. Test Optionality | ✅ PASS | Tests not mandated in spec; visual CSS change best verified manually |
| V. Simplicity and DRY | ✅ PASS | Reuses existing `--background` CSS variable and `bg-background` Tailwind utility; single-file change |

**Gate Result**: ALL PASS — proceed to Phase 0

### Post-Design Check (Phase 1 Gate)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | All FR items (FR-001 through FR-008) addressed by data-model.md CSS variable definitions |
| II. Template-Driven Workflow | ✅ PASS | plan.md, research.md, data-model.md, quickstart.md all generated; contracts/ intentionally empty (CSS-only, no API) |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan ready for handoff to `speckit.tasks` |
| IV. Test Optionality | ✅ PASS | No test mandate; visual change verified via browser inspection |
| V. Simplicity and DRY | ✅ PASS | Changes the existing `--background` variable in `index.css` — the single source of truth already referenced by Tailwind's `bg-background` utility class used on `<body>` and root `<div>`. No new abstractions, no new files, no new dependencies. |

**Gate Result**: ALL PASS — proceed to Phase 2 (tasks)

## Project Structure

### Documentation (this feature)

```text
specs/016-green-background/
├── plan.md              # This file
├── research.md          # Phase 0: Color choice, contrast, and approach rationale
├── data-model.md        # Phase 1: CSS variable definitions (light + dark mode)
├── quickstart.md        # Phase 1: Development setup and manual verification guide
├── contracts/           # Phase 1: Empty — no API changes (CSS-only feature)
│   └── README.md        # Explanation of why no contracts are needed
├── checklists/          # Requirements checklist
└── tasks.md             # Phase 2 output (NOT created by speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   └── index.css                # Modify: Update --background, --foreground HSL values
└── tailwind.config.js           # No changes needed (already maps bg-background to --background)
```

**Structure Decision**: Web application structure. Only the frontend `index.css` file requires modification. The existing Tailwind + shadcn/ui design token system centralizes all color values as HSL CSS custom properties in `index.css`. The `<body>` element already uses `bg-background text-foreground` via Tailwind utilities, so updating the CSS variables is sufficient to propagate the green background globally.

## Complexity Tracking

> No constitution violations detected. All design decisions follow existing patterns.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
