# Implementation Plan: Apply Brown Background Color to App Interface

**Branch**: `copilot/update-background-color-brown` | **Date**: 2026-02-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-brown-background/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Update the application's primary background color from the current light gray (#f6f8fa) / dark gray (#161b22) to a warm brown shade (#8B5E3C) by modifying CSS custom properties in the existing theming system. The change involves updating two CSS variable declarations (light and dark mode) in `frontend/src/index.css` while ensuring sufficient contrast for all text and UI elements and maintaining modal/popup styling independence.

## Technical Context

**Language/Version**: TypeScript 5.4, HTML5, CSS3  
**Primary Dependencies**: React 18.3, Vite 5.4  
**Storage**: N/A (CSS-only styling changes, persisted theme mode via localStorage)  
**Testing**: Vitest (unit), Playwright (E2E)  
**Target Platform**: Modern web browsers (Chrome, Firefox, Safari, Edge)  
**Project Type**: Web (frontend React SPA + backend Python API)  
**Performance Goals**: N/A (no performance impact from CSS variable changes)  
**Constraints**: Must maintain WCAG AA accessibility (4.5:1 contrast for normal text, 3:1 for large text)  
**Scale/Scope**: 1 file change (frontend/src/index.css); 2 CSS variable updates (light + dark mode)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Evaluation (Before Phase 0)

| Principle | Status | Justification |
|-----------|--------|---------------|
| **I. Specification-First** | ✅ PASS | Complete spec.md with 3 prioritized user stories (P1: Primary color, P2: Readability, P3: Modal scoping), Given-When-Then scenarios, and clear scope (CSS theming only, no component logic changes) |
| **II. Template-Driven** | ✅ PASS | Following plan-template.md structure. All sections populated per template requirements. No custom sections added. |
| **III. Agent-Orchestrated** | ✅ PASS | Single speckit.plan agent execution. Clear input (spec.md) and outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md). Handoff to speckit.tasks next. |
| **IV. Test Optionality** | ✅ PASS | No new tests required. Feature is CSS variable change with visual verification. Manual accessibility contrast validation sufficient per spec requirements. |
| **V. Simplicity & DRY** | ✅ PASS | Minimal complexity: 2 color value changes in existing CSS variables. No abstractions, no new patterns. Direct implementation matches YAGNI principle. |

**Pre-Design Gate Status**: ✅ **PASSED** - All principles satisfied. No violations requiring justification.

### Post-Design Evaluation (After Phase 1)

| Principle | Status | Justification |
|-----------|--------|---------------|
| **I. Specification-First** | ✅ PASS | Design artifacts (research.md, data-model.md, contracts/) align with spec requirements. No scope expansion. All 7 functional requirements addressed. |
| **II. Template-Driven** | ✅ PASS | All Phase 0-1 artifacts follow prescribed templates. No deviations introduced. |
| **III. Agent-Orchestrated** | ✅ PASS | Phase 0-1 completed by single agent. Clean handoff state achieved. Ready for speckit.tasks. |
| **IV. Test Optionality** | ✅ PASS | Design confirms no new test infrastructure needed. Manual visual verification sufficient per spec assumptions. |
| **V. Simplicity & DRY** | ✅ PASS | Final design maintains simplicity: 2 CSS variable value changes only. No complexity introduced. |

**Post-Design Gate Status**: ✅ **PASSED** - Design maintains constitutional compliance. No complexity tracking required.

## Project Structure

### Documentation (this feature)

```text
specs/003-brown-background/
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
│   ├── index.css        # CSS custom properties (--color-bg-secondary updates)
│   ├── App.css          # Uses --color-bg-secondary (no changes needed)
│   ├── components/
│   │   └── chat/
│   │       └── ChatInterface.css  # Uses --color-bg-secondary (no changes needed)
│   └── [other files unchanged]
└── package.json         # No changes required

backend/
└── [No changes - background color is frontend-only concern]
```

**Structure Decision**: Web application with React frontend. Changes isolated to CSS theming layer (custom properties in index.css). The existing CSS variable `--color-bg-secondary` is used throughout the app for page backgrounds, so updating its definition in light/dark mode will automatically apply the brown color everywhere it's referenced. No component logic, state management, or backend involvement.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations detected. This section intentionally left minimal per constitution principle V (Simplicity).
