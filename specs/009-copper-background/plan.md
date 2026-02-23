# Implementation Plan: Add Copper Background Theme to App

**Branch**: `009-copper-background` | **Date**: 2026-02-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-copper-background/spec.md`

## Summary

Apply a copper background color (#B87333) to the app by updating the existing CSS custom property theming system. The change requires updating 4 design tokens in `frontend/src/index.css` (2 for light mode, 2 for dark mode), adjusting text/foreground colors to meet WCAG 2.1 AA contrast ratios (≥4.5:1), and ensuring overlay components (modals, drawers, sidebars) harmonize with the copper tone. The copper color is defined as a single-source-of-truth design token so future palette changes require editing only one file.

## Technical Context

**Language/Version**: TypeScript ~5.4 (frontend), CSS3 (styling)
**Primary Dependencies**: React 18, Vite 5, CSS custom properties (no additional libraries needed)
**Storage**: N/A
**Testing**: Vitest + @testing-library/react (frontend unit); Playwright (frontend e2e); manual accessibility audit
**Target Platform**: Modern browsers (Chrome, Firefox, Safari, Edge) via nginx
**Project Type**: Web application (frontend-only change)
**Performance Goals**: N/A — CSS-only change, no runtime performance impact
**Constraints**: WCAG 2.1 AA compliance (≥4.5:1 contrast ratio for normal text, ≥3:1 for large text); all existing UI components must remain fully visible and usable
**Scale/Scope**: ~4 CSS token updates in 1 file (`index.css`); visual audit of all pages/components

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development — ✅ PASS

Spec exists at `specs/009-copper-background/spec.md` with 4 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, edge cases, and a requirements checklist that passes all validations.

### II. Template-Driven Workflow — ✅ PASS

All artifacts follow canonical templates (`spec-template.md`, `plan-template.md`). No custom sections added.

### III. Agent-Orchestrated Execution — ✅ PASS

Workflow follows specify → plan → tasks → implement phase ordering. Each agent has a single purpose with well-defined inputs/outputs.

### IV. Test Optionality with Clarity — ✅ PASS

Tests are not explicitly mandated in the spec for this CSS-only change. Manual visual and accessibility audits are the primary verification method (SC-002, SC-005). No TDD approach is needed. Existing tests serve as the regression baseline.

### V. Simplicity and DRY — ✅ PASS

The change modifies CSS custom properties in exactly one file (`index.css`). No new abstractions, frameworks, or architectural layers are introduced. The existing design token system is reused as-is. The copper color is defined once and cascades globally through the existing `var()` references — maximum DRY.

**Post-Design Re-Check (Phase 1)**: All five principles remain satisfied. The design:
- Modifies 1 file (`index.css`) for token definitions
- Adds 0 new files, libraries, or abstractions
- Reuses the existing CSS custom property theming system unchanged
- Meets all functional requirements with the smallest possible change surface

## Project Structure

### Documentation (this feature)

```text
specs/009-copper-background/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── index.css         # ← PRIMARY CHANGE: Update CSS custom property tokens
│   ├── App.css           # Existing component styles (use var() tokens — no changes expected)
│   ├── App.tsx           # Root component (no changes expected)
│   ├── hooks/
│   │   └── useAppTheme.ts  # Dark mode toggle (no changes — already toggles dark-mode-active class)
│   ├── components/       # All components (visual audit for contrast compliance)
│   └── pages/            # All pages (visual audit for copper background consistency)
└── ...
```

**Structure Decision**: Web application structure (frontend-only). The copper background is implemented entirely through CSS custom property token updates in `index.css`. The existing theming architecture (`var()` references throughout `App.css` and components, `useAppTheme` hook for dark mode toggle) requires no structural changes.

## Complexity Tracking

> No constitution violations to justify. The change is a minimal CSS token update with zero new abstractions, files, or dependencies.
