# Implementation Plan: Add Blue Background Color to App

**Branch**: `009-blue-background` | **Date**: 2026-02-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-blue-background/spec.md`

## Summary

Apply a blue background color globally to the Tech Connect app by updating the existing CSS custom property theming system in `frontend/src/index.css`. The change updates the `--color-bg` and `--color-bg-secondary` tokens for both light and dark themes to blue shades that meet WCAG AA contrast requirements. No new dependencies, components, or architectural changes are needed — this is a pure CSS token update with foreground color adjustments to maintain accessibility.

## Technical Context

**Language/Version**: TypeScript ~5.4 (target ES2022), CSS3  
**Primary Dependencies**: React 18.3, Vite 5.4  
**Storage**: N/A  
**Testing**: Vitest 4.x + happy-dom (frontend unit tests)  
**Target Platform**: Web/Chromium (all viewport sizes: 320px–1920px+)  
**Project Type**: Web application (backend + frontend)  
**Performance Goals**: No performance impact — CSS variable update only  
**Constraints**: WCAG AA contrast ratio ≥4.5:1 for normal text, ≥3:1 for large text against blue background  
**Scale/Scope**: ~3 files modified (index.css, index.html optional), 0 new files in source

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | PASS | `spec.md` written with 4 prioritized user stories, Given-When-Then acceptance scenarios, and edge cases |
| II. Template-Driven Workflow | PASS | All artifacts follow canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | PASS | Plan produced by `/speckit.plan` agent; tasks to be produced by `/speckit.tasks` |
| IV. Test Optionality with Clarity | PASS | Tests not explicitly required in spec. This is a visual CSS change. Manual verification and contrast checking are the primary validation methods. |
| V. Simplicity and DRY | PASS | Updating existing CSS custom properties — no new abstractions, no new files, no new dependencies. Single-point token change. |

**Gate result**: ALL PASS — proceed to Phase 0.

### Post-Phase 1 Re-check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | PASS | All FR-001 through FR-007 addressed in design |
| II. Template-Driven Workflow | PASS | Artifacts follow canonical format |
| III. Agent-Orchestrated Execution | PASS | Handoff to `/speckit.tasks` ready |
| IV. Test Optionality with Clarity | PASS | No tests required — CSS-only change, verified via contrast ratio tools |
| V. Simplicity and DRY | PASS | Minimal change: update token values in one CSS file |

**Gate result**: ALL PASS — proceed to Phase 2 (tasks).

## Project Structure

### Documentation (this feature)

```text
specs/009-blue-background/
├── plan.md              # This file
├── research.md          # Phase 0: Blue shade selection, contrast analysis, dark mode adaptation
├── data-model.md        # Phase 1: Design token entity definitions
├── quickstart.md        # Phase 1: How to apply and verify the blue background
├── contracts/           # Phase 1: CSS custom property contracts
│   └── design-tokens.css
└── tasks.md             # Phase 2 output (/speckit.tasks - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── index.html           # Root HTML (optional: inline background-color to prevent flash)
└── src/
    ├── index.css        # PRIMARY: CSS custom properties (:root and .dark-mode-active)
    ├── App.css          # Component styles (reference --color-bg, --color-bg-secondary)
    ├── App.tsx          # App shell (no changes expected)
    ├── main.tsx         # Entry point (no changes expected)
    ├── hooks/
    │   └── useAppTheme.ts  # Dark mode toggle (no changes expected)
    └── components/      # All components use CSS variables (no changes expected)
```

**Structure Decision**: Web application (frontend only for this feature). The blue background is implemented entirely via CSS custom property updates in `frontend/src/index.css`. No backend changes. No new files in source tree.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
