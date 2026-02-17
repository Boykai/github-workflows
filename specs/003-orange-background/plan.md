# Implementation Plan: Orange Background Throughout the App

**Branch**: `003-orange-background` | **Date**: 2026-02-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-orange-background/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Update the application's global CSS custom properties to apply an orange background (#FF8C00 for light mode, #CC7000 for dark mode) across all screens. This involves modifying CSS variables in `frontend/src/index.css` (`:root` and `html.dark-mode-active` selectors) and ensuring text/UI contrast meets WCAG 2.1 AA standards. No new dependencies, data model changes, or architectural modifications required.

## Technical Context

**Language/Version**: TypeScript 5.4, CSS3  
**Primary Dependencies**: React 18.3, Vite 5.4  
**Storage**: N/A (CSS-only changes)  
**Testing**: Vitest (unit), Playwright (E2E)  
**Target Platform**: Modern web browsers (Chrome, Firefox, Safari, Edge)  
**Project Type**: Web (frontend React SPA + backend Python API)  
**Performance Goals**: N/A (no performance impact from CSS variable changes)  
**Constraints**: WCAG 2.1 AA contrast compliance (4.5:1 normal text, 3:1 large text/UI)  
**Scale/Scope**: 1 file change (`frontend/src/index.css`); possible minor adjustments in `frontend/src/App.css` for login button contrast

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Evaluation (Before Phase 0)

| Principle | Status | Justification |
|-----------|--------|---------------|
| **I. Specification-First** | ✅ PASS | Complete spec.md with 4 prioritized user stories (P1: Orange background, P2: Accessibility, P3: Dark mode, P4: Responsive), Given-When-Then scenarios, edge cases, and clear scope |
| **II. Template-Driven** | ✅ PASS | Following plan-template.md structure. All sections populated per template requirements. No custom sections added. |
| **III. Agent-Orchestrated** | ✅ PASS | Single speckit.plan agent execution. Clear input (spec.md) and outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md). Handoff to speckit.tasks next. |
| **IV. Test Optionality** | ✅ PASS | No new tests required. Feature is CSS variable change with manual/visual verification. Existing tests should pass without modification. |
| **V. Simplicity & DRY** | ✅ PASS | Minimal complexity: CSS custom property updates in 1-2 files. Leverages existing theming pattern (`:root` + `html.dark-mode-active`). No new abstractions. |

**Pre-Design Gate Status**: ✅ **PASSED** - All principles satisfied. No violations requiring justification.

### Post-Design Evaluation (After Phase 1)

| Principle | Status | Justification |
|-----------|--------|---------------|
| **I. Specification-First** | ✅ PASS | Design artifacts (research.md, data-model.md, contracts/) align with spec requirements. No scope expansion. All FR-001 through FR-008 addressed. |
| **II. Template-Driven** | ✅ PASS | All Phase 0-1 artifacts follow prescribed templates. No deviations introduced. |
| **III. Agent-Orchestrated** | ✅ PASS | Phase 0-1 completed by single agent. Clean handoff state achieved. Ready for speckit.tasks. |
| **IV. Test Optionality** | ✅ PASS | Design confirms no new test infrastructure needed. Visual verification and accessibility audit tools sufficient per spec. |
| **V. Simplicity & DRY** | ✅ PASS | Final design maintains simplicity: CSS custom property updates only. Login button fix uses existing CSS patterns. No complexity introduced. |

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
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── index.css        # Global CSS custom properties (:root and dark-mode-active)
│   ├── App.css          # Component styles (login button may need contrast fix)
│   ├── App.tsx          # Main application component (no changes expected)
│   └── hooks/
│       └── useAppTheme.ts  # Theme toggle hook (no changes needed)
└── [other files unchanged]

backend/
└── [No changes - background is frontend-only concern]
```

**Structure Decision**: Web application with React frontend. Changes isolated to frontend CSS layer (`index.css` for theme variables, potentially `App.css` for login button contrast). No backend, database, or state management involvement. This is a View-layer-only update leveraging the existing CSS custom properties theming system.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations detected. This section intentionally left minimal per constitution principle V (Simplicity).
