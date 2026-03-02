# Implementation Plan: Add Green Background Color to App

**Branch**: `016-green-background` | **Date**: 2026-03-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/016-green-background/spec.md`

## Summary

Update the application's global background color to green (#4CAF50) by modifying the `--background` CSS custom property in the existing Tailwind/shadcn theming system. The change is a single-line CSS variable update in `frontend/src/index.css` that propagates automatically to all pages via the existing `bg-background` utility class. Overlay components (modals, popovers, cards, dropdowns) already use their own CSS variables (`--popover`, `--card`) and will not be affected. The `--foreground` color may need adjustment to maintain WCAG AA contrast against the new green background. See [research.md](./research.md) for color choice rationale and contrast analysis.

## Technical Context

**Language/Version**: TypeScript 5.4 / React 18 (frontend)
**Primary Dependencies**: Vite 5, TailwindCSS 3.4, shadcn/ui theming (CSS custom properties with HSL values)
**Storage**: N/A (CSS-only change)
**Testing**: Vitest + React Testing Library (frontend); visual/manual verification for color accuracy
**Target Platform**: Modern browsers (Chrome, Firefox, Safari, Edge)
**Project Type**: Web application (frontend only for this feature)
**Performance Goals**: N/A (no computation or network impact — purely CSS)
**Constraints**: WCAG AA minimum 4.5:1 contrast ratio for normal text, 3:1 for large text against green background
**Scale/Scope**: 1 file modified (`frontend/src/index.css`), 0 new files, 0 new dependencies

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Check (Phase 0 Gate)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | `spec.md` exists with 4 prioritized user stories (P1×2, P2×1, P3×1), Given-When-Then scenarios, 10 FRs, and edge cases |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated Execution | ✅ PASS | `speckit.plan` agent produces plan.md and Phase 0/1 artifacts |
| IV. Test Optionality | ✅ PASS | Tests not mandated in spec; visual verification sufficient for CSS color change |
| V. Simplicity and DRY | ✅ PASS | Single CSS variable change leverages existing theming system; no new abstractions, no new files, no new dependencies |

**Gate Result**: ALL PASS — proceed to Phase 0

### Post-Design Check (Phase 1 Gate)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | All FR items (FR-001 through FR-010) mapped to design decisions in research.md |
| II. Template-Driven Workflow | ✅ PASS | plan.md, research.md, data-model.md, quickstart.md all generated |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan ready for handoff to `speckit.tasks` |
| IV. Test Optionality | ✅ PASS | No test mandate; visual verification sufficient |
| V. Simplicity and DRY | ✅ PASS | Reuses existing CSS custom property theming system (`--background` in `index.css`). No new files, frameworks, or abstractions. Single-line change for core requirement. |

**Gate Result**: ALL PASS — proceed to Phase 2 (tasks)

## Project Structure

### Documentation (this feature)

```text
specs/016-green-background/
├── plan.md              # This file
├── research.md          # Phase 0: Color choice rationale and contrast analysis
├── data-model.md        # Phase 1: Design token definitions
├── quickstart.md        # Phase 1: Development and verification guide
├── contracts/
│   └── no-api.md        # Phase 1: No API contracts (CSS-only change)
├── checklists/
│   └── requirements.md  # Requirements checklist
└── tasks.md             # Phase 2 output (NOT created by speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   └── index.css        # Modify: Update --background CSS custom property to green HSL value
└── index.html           # No change needed (body already styled via Tailwind base layer)
```

**Structure Decision**: Web application structure (frontend only). The repository uses `backend/` and `frontend/` top-level directories, but this feature only touches frontend CSS. The existing shadcn/ui theming system in `frontend/src/index.css` defines all color tokens as CSS custom properties with HSL values. The `--background` variable is consumed by Tailwind's `bg-background` utility class, which is already applied to `body` in the base layer and to the root `<div>` in `App.tsx`. Changing the HSL value of `--background` in `:root` propagates the green color globally with zero additional code changes.

## Complexity Tracking

> No constitution violations detected. No complexity to justify.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
