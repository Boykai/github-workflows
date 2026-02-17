# Implementation Plan: Orange Background Throughout the App

**Branch**: `003-orange-background` | **Date**: 2026-02-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-orange-background/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Update the application's global CSS custom properties to apply an orange background (#FF8C00 in light mode, #CC7000 in dark mode) across all screens. This involves modifying CSS variables in `frontend/src/index.css` for both `:root` and `html.dark-mode-active` selectors, and ensuring text and interactive elements maintain WCAG 2.1 AA contrast compliance. The login button, which uses `var(--color-text)` as its background, will need adjustment to remain visible against the new text color.

## Technical Context

**Language/Version**: TypeScript 5.4, CSS3  
**Primary Dependencies**: React 18.3, Vite 5.4  
**Storage**: N/A (styling changes only)  
**Testing**: Vitest (unit), Playwright (E2E)  
**Target Platform**: Modern web browsers (Chrome, Firefox, Safari, Edge)  
**Project Type**: Web (frontend React SPA + backend Python API)  
**Performance Goals**: N/A (no performance impact from CSS variable changes)  
**Constraints**: WCAG 2.1 AA contrast compliance (4.5:1 for normal text, 3:1 for large text/UI components)  
**Scale/Scope**: 1-2 file changes in `frontend/src/` (index.css, possibly App.css); no backend, API, or state management changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Evaluation (Before Phase 0)

| Principle | Status | Justification |
|-----------|--------|---------------|
| **I. Specification-First** | ✅ PASS | Complete spec.md with 4 prioritized user stories (P1: Global orange background, P2: Accessible contrast, P3: Dark mode variant, P4: Responsive rendering), Given-When-Then acceptance scenarios, edge cases, and clear scope boundaries |
| **II. Template-Driven** | ✅ PASS | Following plan-template.md structure. All sections populated per template requirements. No custom sections added. |
| **III. Agent-Orchestrated** | ✅ PASS | Single speckit.plan agent execution. Clear input (spec.md) and outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md). Handoff to speckit.tasks next. |
| **IV. Test Optionality** | ✅ PASS | No new tests explicitly required. Feature is CSS variable update with manual visual verification. Existing tests should continue passing. |
| **V. Simplicity & DRY** | ✅ PASS | Minimal complexity: CSS custom property value changes in 1-2 files. Leverages existing theming infrastructure (CSS variables, dark mode class toggle). No new abstractions. |

**Pre-Design Gate Status**: ✅ **PASSED** - All principles satisfied. No violations requiring justification.

### Post-Design Evaluation (After Phase 1)

| Principle | Status | Justification |
|-----------|--------|---------------|
| **I. Specification-First** | ✅ PASS | Design artifacts align with spec requirements. No scope expansion. All FR-001 through FR-008 addressed. |
| **II. Template-Driven** | ✅ PASS | All Phase 0-1 artifacts follow prescribed templates. No deviations introduced. |
| **III. Agent-Orchestrated** | ✅ PASS | Phase 0-1 completed by single agent. Clean handoff state achieved. Ready for speckit.tasks. |
| **IV. Test Optionality** | ✅ PASS | No new test infrastructure needed. Manual visual verification sufficient per spec. |
| **V. Simplicity & DRY** | ✅ PASS | Final design uses existing CSS variable system. Only variable values change. Login button fix is minimal (explicit color override). No new patterns introduced. |

**Post-Design Gate Status**: ✅ **PASSED** - Design maintains constitutional compliance. No complexity tracking required.

## Project Structure

### Documentation (this feature)

```text
specs/003-orange-background/
├── spec.md              # Feature specification (completed)
├── checklists/
│   └── requirements.md  # Spec validation checklist (completed)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (generated below)
├── data-model.md        # Phase 1 output (generated below)
├── quickstart.md        # Phase 1 output (generated below)
├── contracts/           # Phase 1 output (generated below)
│   └── css-changes.md   # CSS modification contract
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── index.css        # Global CSS custom properties (:root and dark mode overrides)
│   ├── App.css          # Component styles (login button, headers, sidebar, cards)
│   ├── App.tsx          # Main application component
│   └── hooks/
│       └── useAppTheme.ts  # Theme toggle hook (dark-mode-active class management)
└── [other files unchanged]

backend/
└── [No changes - background is frontend-only concern]
```

**Structure Decision**: Web application with React frontend. Changes isolated to frontend CSS layer (custom property values). No backend, database, or state management involvement. This is a View-layer-only update leveraging the existing CSS variable theming system.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations detected. This section intentionally left minimal per constitution principle V (Simplicity).
