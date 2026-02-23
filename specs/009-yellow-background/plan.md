# Implementation Plan: Add Yellow Background to App

**Branch**: `009-yellow-background` | **Date**: 2026-02-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-yellow-background/spec.md`

## Summary

Apply a soft yellow background (#FFF9C4) globally to the app in light mode by updating two CSS custom properties (`--color-bg` and `--color-bg-secondary`) in the `:root` block of `frontend/src/index.css`. Dark mode values remain unchanged. Verify foreground text contrast meets WCAG 2.1 AA (≥4.5:1).

## Technical Context

**Language/Version**: TypeScript ~5.4 (frontend), CSS3
**Primary Dependencies**: React 18.3, Vite, CSS custom properties (no additional libraries needed)
**Storage**: N/A
**Testing**: Visual inspection + contrast audit (no automated test infrastructure changes needed)
**Target Platform**: Web — Chrome, Firefox, Safari, Edge (desktop + mobile)
**Project Type**: Web application (frontend-only change)
**Performance Goals**: N/A (CSS-only change, zero runtime cost)
**Constraints**: WCAG 2.1 AA contrast ratio ≥4.5:1 for all text against #FFF9C4
**Scale/Scope**: 2 lines changed in `frontend/src/index.css` (light-mode `:root` block only)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | PASS | `spec.md` written with 4 prioritized user stories, acceptance scenarios, edge cases, and success criteria |
| II. Template-Driven Workflow | PASS | All artifacts use canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | PASS | Plan produced by `/speckit.plan` agent; tasks will be produced by `/speckit.tasks` |
| IV. Test Optionality with Clarity | PASS | No automated tests required — this is a CSS-only visual change. Verification is via visual inspection and contrast audit tools (Lighthouse, axe DevTools). Spec does not mandate automated tests. |
| V. Simplicity and DRY | PASS | Change is 2 CSS custom property values in one file. Color is defined once as a design token (`:root` variable), not duplicated. No new abstractions introduced. |

**Gate result**: ALL PASS — proceed to Phase 0.

### Post-Design Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | PASS | All research decisions trace back to spec requirements (FR-001 through FR-007) |
| II. Template-Driven Workflow | PASS | All 5 plan artifacts generated per template |
| III. Agent-Orchestrated Execution | PASS | Artifacts ready for `/speckit.tasks` handoff |
| IV. Test Optionality with Clarity | PASS | No tests needed — CSS value change verified by contrast audit |
| V. Simplicity and DRY | PASS | Minimal change (2 lines). No new files, no new dependencies, no new abstractions. |

**Post-design gate result**: ALL PASS.

## Project Structure

### Documentation (this feature)

```text
specs/009-yellow-background/
├── plan.md              # This file
├── research.md          # Phase 0: Color choice, contrast, dark mode decisions
├── data-model.md        # Phase 1: Design token and theme mode entities
├── quickstart.md        # Phase 1: Step-by-step implementation guide
├── contracts/           # Phase 1: CSS custom property contract
│   └── theme-tokens.css # Light-mode token values
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── index.css        # ← ONLY file modified (2 lines in :root block)
│   ├── App.css          # No changes needed
│   ├── App.tsx          # No changes needed
│   ├── hooks/
│   │   └── useAppTheme.ts  # No changes needed (toggles dark-mode-active class)
│   └── components/      # No changes needed
└── ...

backend/                 # No changes needed
```

**Structure Decision**: Web application (frontend-only). The change is isolated to CSS custom properties in `frontend/src/index.css`. The existing theme system (`:root` for light mode, `html.dark-mode-active` for dark mode) already supports this — only the light-mode token values need updating.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
