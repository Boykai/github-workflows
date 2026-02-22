# Implementation Plan: Add Brown Background Color to App

**Branch**: `copilot/add-brown-background-color` | **Date**: 2026-02-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from parent issue #679

## Summary

Apply a brown background color globally across the application by updating the existing CSS custom properties (`--color-bg`, `--color-bg-secondary`) in `frontend/src/index.css`. The brown color value `#4E342E` (Material Design Brown 800) will be used for light mode, with a darker variant `#3E2723` (Material Design Brown 900) for dark mode. The change is confined to CSS variable definitions in the `:root` and `html.dark-mode-active` selectors — no component code changes are required. The brown color will be defined via the existing CSS custom property system, ensuring reusability and easy future adjustments.

## Technical Context

**Language/Version**: TypeScript ~5.4 (frontend), React 18
**Primary Dependencies**: React 18, @tanstack/react-query v5, Vite 5
**Storage**: N/A (CSS-only change)
**Testing**: Vitest + @testing-library/react (frontend unit); visual inspection for CSS changes
**Target Platform**: Modern browsers (Chrome, Firefox, Safari, Edge); all viewports (mobile, tablet, desktop)
**Project Type**: Web application (frontend-only change)
**Performance Goals**: N/A (no performance impact from CSS variable change)
**Constraints**: WCAG AA contrast ratio (4.5:1 minimum for normal text); existing component visual coherence
**Scale/Scope**: 2 CSS variable definitions changed in 1 file (`index.css`), affecting 2 selectors (`:root` and `html.dark-mode-active`)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development — ✅ PASS

Feature specification provided via parent issue #679 with user story, functional requirements (8 items with MUST/SHOULD prioritization), UI/UX description, and technical notes. Scope is clearly bounded to background color change only.

### II. Template-Driven Workflow — ✅ PASS

All artifacts follow canonical templates (`plan-template.md`). Plan includes required sections: Summary, Technical Context, Constitution Check, Project Structure, and Complexity Tracking.

### III. Agent-Orchestrated Execution — ✅ PASS

Workflow follows specify → plan → tasks → implement phase ordering. Plan phase produces plan.md, research.md, data-model.md, contracts/, and quickstart.md as defined by the workflow.

### IV. Test Optionality with Clarity — ✅ PASS

No tests explicitly requested in the specification. This is a CSS-only change with no logic to unit test. Visual verification is the appropriate validation method. No TDD required.

### V. Simplicity and DRY — ✅ PASS

Change modifies exactly 2 existing CSS variable values per theme (light and dark). No new abstractions, files, or patterns introduced. Uses the existing CSS custom property system already in place. Maximally simple approach.

**Post-Design Re-Check (Phase 1)**: All five principles remain satisfied. The design:
- Modifies only CSS variable values in the existing theming system
- Introduces no new files, components, or abstractions
- Reuses the existing `--color-bg` / `--color-bg-secondary` custom properties
- No tests needed (CSS visual change only)
- Maximum simplicity — smallest possible change footprint

## Project Structure

### Documentation (this feature)

```text
specs/010-brown-background/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (no API changes)
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── index.css          # MODIFIED: Update --color-bg and --color-bg-secondary values
│   ├── App.css            # UNCHANGED: Already uses var(--color-bg) and var(--color-bg-secondary)
│   ├── App.tsx            # UNCHANGED: No component changes needed
│   ├── hooks/
│   │   └── useAppTheme.ts # UNCHANGED: Dark mode toggle works with CSS variables
│   └── ...                # UNCHANGED: All other frontend files
└── ...
```

**Structure Decision**: Web application structure. The change is isolated to CSS custom property values in `frontend/src/index.css`. The existing theming architecture (CSS custom properties in `:root` and `html.dark-mode-active`, toggled by `useAppTheme` hook) fully supports this change with zero structural modifications. All components already reference `var(--color-bg)` and `var(--color-bg-secondary)`, so updating the variable values propagates the brown background automatically.

## Complexity Tracking

> No constitution violations to justify. This is a minimal CSS variable value change with no complexity:
> - No new files, components, or abstractions
> - No new dependencies
> - Uses existing CSS custom property theming system as-is
> - Change footprint: 4 CSS variable values in 1 file
