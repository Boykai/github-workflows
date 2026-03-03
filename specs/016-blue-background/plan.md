# Implementation Plan: Add Blue Background Color to App

**Branch**: `016-blue-background` | **Date**: 2026-03-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/016-blue-background/spec.md`

## Summary

Apply a blue background color to the root application container by updating the existing CSS custom properties (`--background`) in `frontend/src/index.css`. The change uses the project's existing Tailwind CSS + HSL CSS variable theming system — no new frameworks, components, or backend changes are needed. Light mode gets a medium blue (`#1E90FF` / Dodger Blue) and dark mode gets a deeper blue (`#1A3A5C`), both maintaining WCAG AA contrast (≥4.5:1) with their respective foreground colors. See [research.md](./research.md) for color selection rationale and contrast verification.

## Technical Context

**Language/Version**: TypeScript 5.4 / React 18 (frontend only)
**Primary Dependencies**: React 18, Vite 5.4, TailwindCSS 3.4 (tailwindcss-animate plugin)
**Storage**: N/A (no backend or database changes)
**Testing**: Vitest + React Testing Library (frontend); visual manual testing for color verification
**Target Platform**: Modern browsers (last 2 versions of Chrome, Firefox, Safari, Edge)
**Project Type**: Web application (frontend-only change)
**Performance Goals**: Blue background visible within 1 second of page load (SC-006); no flash of white/other color before blue renders
**Constraints**: WCAG AA contrast ratio ≥4.5:1 between blue background and all foreground text; consistent rendering from 320px to 2560px viewport width
**Scale/Scope**: 1 CSS file modification (`frontend/src/index.css`), 0 new files, 0 new components, 0 backend changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Check (Phase 0 Gate)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | `spec.md` exists with 4 prioritized user stories (P1×2, P2×1, P3×1), Given-When-Then scenarios, 8 FRs, 5 edge cases |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated Execution | ✅ PASS | `speckit.plan` agent produces plan.md and Phase 0/1 artifacts |
| IV. Test Optionality | ✅ PASS | Tests not mandated in spec; visual verification sufficient for CSS-only change |
| V. Simplicity and DRY | ✅ PASS | Modifies existing CSS variables in one file; no new abstractions, no new dependencies |

**Gate Result**: ALL PASS — proceed to Phase 0

### Post-Design Check (Phase 1 Gate)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | All FR items (FR-001 through FR-008) addressed by CSS variable change in research.md |
| II. Template-Driven Workflow | ✅ PASS | plan.md, research.md, data-model.md, quickstart.md all generated; contracts/ contains no-op note (no API changes) |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan ready for handoff to `speckit.tasks` |
| IV. Test Optionality | ✅ PASS | No test mandate; visual verification per quickstart.md |
| V. Simplicity and DRY | ✅ PASS | Single-file CSS variable change; reuses existing `--background`/`--foreground` theming system; no new tokens, no new Tailwind classes, no component modifications |

**Gate Result**: ALL PASS — proceed to Phase 2 (tasks)

## Project Structure

### Documentation (this feature)

```text
specs/016-blue-background/
├── plan.md              # This file
├── research.md          # Phase 0: Color selection rationale and contrast verification
├── data-model.md        # Phase 1: No new entities (CSS-only change)
├── quickstart.md        # Phase 1: Development setup and visual testing guide
├── contracts/
│   └── no-api-changes.md  # Phase 1: No API contract changes needed
├── checklists/
│   └── requirements.md  # Requirements checklist
└── tasks.md             # Phase 2 output (NOT created by speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   └── index.css                    # Modify: Update --background CSS variable for light and dark modes
└── tailwind.config.js               # No changes needed (already maps bg-background to hsl(var(--background)))
```

**Structure Decision**: Web application structure. Only the frontend is affected. The change is confined to `frontend/src/index.css` where the existing CSS custom properties `--background` (light) and `.dark --background` (dark) are updated from their current white/dark-navy values to blue values. The Tailwind config (`tailwind.config.js`) already maps `bg-background` to `hsl(var(--background))`, so all components using `bg-background` automatically inherit the new color. No component-level changes are required.

## Complexity Tracking

> No constitution violations detected. This is the simplest possible implementation — a CSS variable value change in one file.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
