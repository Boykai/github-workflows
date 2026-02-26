# Implementation Plan: Add Red Background Color to App

**Branch**: `011-red-background` | **Date**: 2026-02-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/011-red-background/spec.md`

## Summary

Update the application's primary background color to red (#E53E3E) by modifying the existing CSS custom property system in `frontend/src/index.css`. The change is centralized in the `:root` and `html.dark-mode-active` token definitions, applying to the `body` element via the existing `var(--color-bg-secondary)` usage. Foreground text colors will be adjusted to maintain WCAG AA contrast compliance against the new red background.

## Technical Context

**Language/Version**: TypeScript 5.4, React 18.3.1, Python 3.11 (backend — not affected)
**Primary Dependencies**: Vite 5.4, TanStack React Query 5.17, Socket.io-client 4.7
**Storage**: N/A (frontend-only change)
**Testing**: Vitest (unit), Playwright (e2e)
**Target Platform**: Web — Chrome, Firefox, Safari, Edge; mobile/tablet/desktop viewports
**Project Type**: web (frontend + backend)
**Performance Goals**: N/A (CSS-only change, no runtime cost)
**Constraints**: WCAG AA contrast ratios (4.5:1 normal text, 3:1 large text/interactive elements)
**Scale/Scope**: Single CSS file change (`frontend/src/index.css`) affecting global theme tokens

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | `spec.md` exists with prioritized user stories (P1, P2), acceptance scenarios, and requirements |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase follows spec phase; outputs are well-defined |
| IV. Test Optionality with Clarity | ✅ PASS | Spec mentions visual regression tests as SHOULD (optional). No mandatory test requirement. Existing test infrastructure (Vitest/Playwright) available if needed |
| V. Simplicity and DRY | ✅ PASS | Change modifies 1 file (index.css) using existing CSS custom property infrastructure. No new abstractions. Single source of truth for color tokens |

**Gate Result**: ✅ ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/011-red-background/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (N/A — no API changes)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── index.css        # ← PRIMARY CHANGE: CSS custom property tokens
│   ├── App.css          # Review for contrast/legibility
│   ├── App.tsx          # No changes expected
│   ├── components/      # Review for hardcoded backgrounds
│   ├── hooks/
│   │   └── useAppTheme.ts  # No changes expected (theme toggle logic)
│   ├── pages/
│   └── services/
└── tests/
```

**Structure Decision**: Web application structure (frontend + backend). Only the frontend is affected by this feature. The change is isolated to CSS token definitions in `frontend/src/index.css`, with potential minor adjustments to component CSS files for contrast compliance.

## Complexity Tracking

> No constitution violations. No complexity justification needed.

*Table intentionally left empty — all principles satisfied.*
