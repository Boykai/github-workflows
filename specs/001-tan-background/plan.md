# Implementation Plan: Apply Tan Background Color to App

**Branch**: `001-tan-background` | **Date**: 2026-02-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-tan-background/spec.md`

## Summary

Apply a tan background color (#D2B48C) globally to the application by updating CSS custom properties in `frontend/src/index.css`. The change replaces the current `--color-bg-secondary` value (used as the body background) with the tan color in light mode and maps to a dark-tan equivalent (#2C1E12) in dark mode. Secondary text color requires darkening to maintain WCAG AA contrast on the new tan background.

## Technical Context

**Language/Version**: TypeScript ~5.4, React 18.3  
**Primary Dependencies**: React, Vite 5.4, @tanstack/react-query  
**Storage**: N/A  
**Testing**: vitest, @testing-library/react  
**Target Platform**: Web (all modern browsers, all viewports)  
**Project Type**: web (frontend + backend monorepo)  
**Performance Goals**: N/A (visual-only change, no performance impact)  
**Constraints**: WCAG AA contrast ratio (4.5:1 normal text, 3:1 large text)  
**Scale/Scope**: Single CSS file change (`frontend/src/index.css`), ~5 lines modified

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ Pass | `spec.md` exists with prioritized user stories, acceptance scenarios, and scope boundaries |
| II. Template-Driven | ✅ Pass | All artifacts follow canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated | ✅ Pass | Plan phase follows specify → plan → tasks → implement pipeline |
| IV. Test Optionality | ✅ Pass | No tests mandated in spec for CSS-only change; visual verification via accessibility audit suffices |
| V. Simplicity & DRY | ✅ Pass | Change is minimal — CSS custom property updates only, no new abstractions |

**Gate result**: PASS — No violations. Proceeding to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-tan-background/
├── plan.md              # This file
├── research.md          # Phase 0: color research and contrast analysis
├── data-model.md        # Phase 1: CSS token definitions
├── quickstart.md        # Phase 1: implementation guide
├── contracts/           # Phase 1: N/A (no API changes)
└── tasks.md             # Phase 2 output (NOT created by plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── index.css          # ← Primary change target (CSS custom properties)
│   ├── App.css            # Review for component-specific overrides
│   ├── App.tsx            # No changes expected
│   ├── components/        # Review for hard-coded backgrounds
│   ├── pages/             # Review for hard-coded backgrounds
│   └── hooks/
│       └── useAppTheme.ts # Dark mode toggle (no changes expected)
└── package.json
```

**Structure Decision**: Web application structure (frontend + backend). All changes are scoped to `frontend/src/index.css` for CSS custom property updates. No backend changes needed. Component CSS files may need review for hard-coded background overrides that conflict with the new tan color.

## Complexity Tracking

> No violations — section intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
