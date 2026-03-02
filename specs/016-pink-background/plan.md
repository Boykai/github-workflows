# Implementation Plan: Add Pink Background Color to App

**Branch**: `016-pink-background` | **Date**: 2026-03-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/016-pink-background/spec.md`

## Summary

Update the application's global background color to pink by modifying CSS custom properties in the existing theming system. The frontend uses a shadcn/ui-based design system with HSL CSS custom properties defined in `frontend/src/index.css` and consumed via Tailwind's `bg-background` utility. The change involves updating the `--background` CSS variable in both `:root` (light mode: `#FFC0CB` / HSL `350 100% 88%`) and `.dark` (dark mode: `#8B475D` / HSL `340 33% 41%`) scopes. No new files, dependencies, or backend changes are required. See [research.md](./research.md) for decision rationale.

## Technical Context

**Language/Version**: TypeScript 5.x (frontend), CSS3 with CSS Custom Properties
**Primary Dependencies**: React 18, Vite 5.4, TailwindCSS 3.x, shadcn/ui component library
**Storage**: N/A (pure CSS change, no data persistence)
**Testing**: Vitest + React Testing Library (frontend)
**Target Platform**: Modern browsers (Chrome, Firefox, Safari, Edge), responsive (mobile, tablet, desktop)
**Project Type**: Web application (frontend only — no backend changes needed)
**Performance Goals**: No performance impact; CSS variable change is instantaneous
**Constraints**: WCAG AA contrast ratio ≥ 4.5:1 for normal text, ≥ 3:1 for large text against both light and dark pink variants
**Scale/Scope**: 1 file modified (`frontend/src/index.css`), 2 CSS variable values changed (light mode `--background`, dark mode `--background`)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Check (Phase 0 Gate)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | `spec.md` exists with 4 prioritized user stories (P1×3, P2×1), Given-When-Then scenarios, 10 FRs, and 5 edge cases |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated Execution | ✅ PASS | `speckit.plan` agent produces plan.md and Phase 0/1 artifacts |
| IV. Test Optionality | ✅ PASS | Tests not mandated in spec; visual change verifiable by inspection |
| V. Simplicity and DRY | ✅ PASS | Modifies only existing CSS variables in a single file; no new abstractions, components, or dependencies |

**Gate Result**: ALL PASS — proceed to Phase 0

### Post-Design Check (Phase 1 Gate)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | All FR items (FR-001 through FR-010) are addressed by the CSS variable change in data-model.md |
| II. Template-Driven Workflow | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all generated |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan ready for handoff to `speckit.tasks` |
| IV. Test Optionality | ✅ PASS | No test mandate; visual verification sufficient per constitution |
| V. Simplicity and DRY | ✅ PASS | Single-file change modifying 2 existing CSS variable values. Reuses existing `bg-background` Tailwind utility class already applied to `body` in index.css. No new files, components, or abstractions. |

**Gate Result**: ALL PASS — proceed to Phase 2 (tasks)

## Project Structure

### Documentation (this feature)

```text
specs/016-pink-background/
├── plan.md              # This file
├── research.md          # Phase 0: Color decisions and contrast analysis
├── data-model.md        # Phase 1: CSS variable definitions (design tokens)
├── quickstart.md        # Phase 1: Development setup and verification guide
├── contracts/
│   └── no-api.md        # Phase 1: Documents why no API contracts needed
├── checklists/
│   └── requirements.md  # Requirements checklist
└── tasks.md             # Phase 2 output (NOT created by speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   └── index.css                # Modify: Update --background CSS variable in :root and .dark
├── tailwind.config.js           # No change: Already maps `background` to hsl(var(--background))
└── index.html                   # No change: Already renders body with Tailwind classes
```

**Structure Decision**: Frontend-only change within the existing web application structure (backend + frontend). Only `frontend/src/index.css` requires modification. The existing Tailwind configuration already maps the `background` color token to `hsl(var(--background))`, and the `body` element already uses `@apply bg-background` — so changing the CSS variable value is the only required action.

## Complexity Tracking

> No constitution violations detected. This is the simplest possible implementation — a 2-line CSS variable value change.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
