# Implementation Plan: Add Pink Background Color to App

**Branch**: `011-pink-background` | **Date**: 2026-02-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/011-pink-background/spec.md`

## Summary

Apply a pink background color globally across the app using the existing CSS custom property theming system. Define the pink color as a design token (`--color-bg`, `--color-bg-secondary`) in both light and dark mode blocks in `frontend/src/index.css`, ensuring WCAG AA contrast compliance and no visual regressions.

## Technical Context

**Language/Version**: TypeScript ~5.4 (frontend), CSS3
**Primary Dependencies**: React 18.3, Vite, CSS custom properties
**Storage**: N/A
**Testing**: Vitest + React Testing Library (frontend)
**Target Platform**: Web (Chrome, Firefox, Safari, Edge), responsive (mobile/tablet/desktop)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: No layout shifts, no visual regressions
**Constraints**: WCAG AA contrast ratio for all text/UI elements on pink background
**Scale/Scope**: 2 CSS blocks (~6 token values total) in a single file

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | PASS | Feature spec provided in parent issue with user story, functional requirements, and acceptance criteria |
| II. Template-Driven Workflow | PASS | All artifacts use canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | PASS | Plan produced by `/speckit.plan` agent; tasks will be produced by `/speckit.tasks` |
| IV. Test Optionality with Clarity | PASS | Spec requires at least one visual regression or UI snapshot test. Test task will be included in tasks.md. |
| V. Simplicity and DRY | PASS | Change is minimal — update existing CSS custom properties. No new abstractions, no new files, no new dependencies. |

**Gate result**: ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/011-pink-background/
├── plan.md              # This file
├── research.md          # Phase 0: Color choice, contrast, dark mode research
├── data-model.md        # Phase 1: Design token definitions
├── quickstart.md        # Phase 1: Implementation guide
├── contracts/           # Phase 1: CSS token contract
│   └── design-tokens.md
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── index.css        # PRIMARY CHANGE: Update :root and html.dark-mode-active tokens
│   ├── App.css          # VERIFY: No hardcoded colors that conflict with pink background
│   ├── App.tsx          # NO CHANGE: Already uses CSS custom properties via className
│   ├── hooks/
│   │   └── useAppTheme.ts  # NO CHANGE: Theme toggle logic unchanged
│   └── components/      # VERIFY: No inline background overrides that mask the pink
└── e2e/                 # OPTIONAL: Add visual regression test if Playwright is configured
```

**Structure Decision**: Web application (Option 2). The change is CSS-only — update existing design tokens in `frontend/src/index.css`. No structural changes needed.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
