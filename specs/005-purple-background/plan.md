# Implementation Plan: Add Purple Background Color to App

**Branch**: `005-purple-background` | **Date**: 2026-02-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-purple-background/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Apply a purple background color (#7C3AED) to the app's root container by introducing a dedicated CSS custom property (`--color-bg-app`) in the global stylesheet and applying it to the `body` element. Foreground text and icon colors on exposed surfaces (login page, loading screen) must be adjusted to white/light tones to maintain WCAG AA contrast compliance (minimum 4.5:1). Authenticated views are unaffected as all major components (header, sidebar, chat section, board page) already define their own opaque backgrounds.

## Technical Context

**Language/Version**: TypeScript 5.4, CSS3, HTML5  
**Primary Dependencies**: React 18.3, Vite 5.4  
**Storage**: N/A (CSS variable changes only)  
**Testing**: Vitest (unit), Playwright (E2E) — no new tests required  
**Target Platform**: Modern web browsers (Chrome, Firefox, Safari, Edge)  
**Project Type**: Web (frontend React SPA + backend Python API)  
**Performance Goals**: N/A (no performance impact from CSS variable change)  
**Constraints**: WCAG AA contrast ratio ≥ 4.5:1 for all text on purple background  
**Scale/Scope**: 1 file change (frontend/src/index.css); no backend, database, or state management changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Evaluation (Before Phase 0)

| Principle | Status | Justification |
|-----------|--------|---------------|
| **I. Specification-First** | ✅ PASS | Complete spec.md with 3 prioritized user stories (P1: Purple background visible, P2: Accessible text/icons, P3: Cross-browser consistency), Given-When-Then scenarios, and clear scope boundaries |
| **II. Template-Driven** | ✅ PASS | Following plan-template.md structure. All sections populated per template requirements. No custom sections added. |
| **III. Agent-Orchestrated** | ✅ PASS | Single speckit.plan agent execution. Clear input (spec.md) and outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md). Handoff to speckit.tasks next. |
| **IV. Test Optionality** | ✅ PASS | No new tests required. Feature is a CSS variable change with manual verification. Spec does not mandate automated tests. |
| **V. Simplicity & DRY** | ✅ PASS | Minimal complexity: 1 new CSS variable + body background update + text color adjustments on 2 selectors. No abstractions, no new patterns. Direct implementation matches YAGNI principle. |

**Pre-Design Gate Status**: ✅ **PASSED** — All principles satisfied. No violations requiring justification.

### Post-Design Evaluation (After Phase 1)

| Principle | Status | Justification |
|-----------|--------|---------------|
| **I. Specification-First** | ✅ PASS | Design artifacts (research.md, data-model.md, contracts/) align with spec requirements. No scope expansion. |
| **II. Template-Driven** | ✅ PASS | All Phase 0–1 artifacts follow prescribed templates. No deviations introduced. |
| **III. Agent-Orchestrated** | ✅ PASS | Phase 0–1 completed by single agent. Clean handoff state achieved. Ready for speckit.tasks. |
| **IV. Test Optionality** | ✅ PASS | Design confirms no new test infrastructure needed. Manual verification sufficient per spec assumptions. |
| **V. Simplicity & DRY** | ✅ PASS | Final design maintains simplicity: CSS variable addition and value updates only. No complexity introduced. |

**Post-Design Gate Status**: ✅ **PASSED** — Design maintains constitutional compliance. No complexity tracking required.

## Project Structure

### Documentation (this feature)

```text
specs/005-purple-background/
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
│   ├── index.css        # Global CSS variables and body styling (MODIFIED)
│   ├── App.css          # Component-level styles (NO CHANGES - components have own backgrounds)
│   ├── App.tsx          # Main application component (NO CHANGES)
│   └── [other files unchanged]
├── index.html           # HTML entry point (NO CHANGES)
└── package.json         # No changes required

backend/
└── [No changes - purple background is frontend-only concern]
```

**Structure Decision**: Web application with React frontend. Changes isolated to the global CSS file (`frontend/src/index.css`). No backend, database, or state management involvement. This is a theming/style-layer-only update.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations detected. This section intentionally left minimal per constitution principle V (Simplicity).
