# Implementation Plan: Add Blue Background Color to App

**Branch**: `010-blue-background` | **Date**: 2026-02-24 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/010-blue-background/spec.md`

## Summary

Apply a blue background color to the Tech Connect app at the root level using CSS custom properties. The existing theming system in `frontend/src/index.css` already defines `--color-bg` and `--color-bg-secondary` tokens for light and dark modes. This feature updates those tokens to blue values (#2563EB for light, #1E3A5F for dark) and adjusts foreground colors to maintain WCAG AA contrast ratios. An inline style on `<body>` in `index.html` prevents flash of unstyled content during page load.

## Technical Context

**Language/Version**: TypeScript ~5.4, CSS3
**Primary Dependencies**: React 18.3, Vite
**Storage**: N/A
**Testing**: Vitest 4.x + happy-dom + React Testing Library (frontend)
**Target Platform**: Web (Chrome, Firefox, Safari, Edge)
**Project Type**: Web application (frontend-only change)
**Performance Goals**: No performance impact — CSS variable change only
**Constraints**: WCAG AA contrast ratio ≥4.5:1 for normal text, ≥3:1 for large text
**Scale/Scope**: ~3 files modified (index.css, index.html, potentially App.css)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | PASS | `spec.md` written with 4 prioritized user stories, acceptance scenarios, and edge cases |
| II. Template-Driven Workflow | PASS | All artifacts use canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | PASS | Plan produced by `/speckit.plan` agent; tasks will be produced by `/speckit.tasks` |
| IV. Test Optionality with Clarity | PASS | Tests not explicitly requested in the spec. This is a CSS-only change — visual verification is primary validation method. |
| V. Simplicity and DRY | PASS | Reuses existing CSS custom property system. No new abstractions, no new files. Single-token change at `:root` level. |

**Gate result**: ALL PASS — proceed to Phase 0.

**Post-Phase 1 Re-check**: ALL PASS — design uses existing CSS custom properties, no new patterns or complexity introduced.

## Project Structure

### Documentation (this feature)

```text
specs/010-blue-background/
├── plan.md              # This file
├── research.md          # Phase 0: Color choice, contrast, theming research
├── data-model.md        # Phase 1: CSS token definitions
├── quickstart.md        # Phase 1: How to apply and verify the change
├── contracts/           # Phase 1: CSS variable contract
│   └── css-tokens.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
frontend/
├── index.html           # Inline body background for flash prevention (FR-009)
└── src/
    └── index.css        # CSS custom property definitions (:root and .dark-mode-active)
```

**Structure Decision**: Web application (frontend only). No structural changes needed — this feature modifies existing CSS custom properties in `frontend/src/index.css` and the inline style in `frontend/index.html`. No new files required.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
