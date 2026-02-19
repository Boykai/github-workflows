# Implementation Plan: Add Black Background Theme

**Branch**: `007-black-background` | **Date**: 2026-02-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-black-background/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Update the application's default background from light/white to black (#000000) by modifying the existing CSS custom properties (design tokens) in `:root`. The app already uses a centralized token system (`--color-bg`, `--color-bg-secondary`, `--color-text`, etc.) in `frontend/src/index.css`, so the change is primarily a token value update plus an inline style on `<html>` in `index.html` to prevent white flash before CSS loads. A small number of hardcoded light background values in `App.css` and `ChatInterface.css` must also be audited and updated. No new dependencies, no architectural changes, no backend modifications.

## Technical Context

**Language/Version**: TypeScript 5.4, CSS3, HTML5  
**Primary Dependencies**: React 18.3, Vite 5.4  
**Storage**: N/A (CSS-only changes)  
**Testing**: Vitest (unit), Playwright (E2E)  
**Target Platform**: Modern web browsers (Chrome, Firefox, Safari, Edge)  
**Project Type**: Web (frontend React SPA + backend Python API)  
**Performance Goals**: N/A (no performance impact from color value changes)  
**Constraints**: WCAG AA contrast ratio (4.5:1 minimum for normal text, 3:1 for large text) must be maintained  
**Scale/Scope**: 3 CSS files + 1 HTML file; no database, API, or state management changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Evaluation (Before Phase 0)

| Principle | Status | Justification |
|-----------|--------|---------------|
| **I. Specification-First** | ✅ PASS | Complete spec.md with 4 prioritized user stories (P1: Global background, P2: Contrast/readability, P3: Component theming, P4: Third-party blending), Given-When-Then scenarios, edge cases, and clear scope boundaries |
| **II. Template-Driven** | ✅ PASS | Following plan-template.md structure. All sections populated per template requirements. No custom sections added. |
| **III. Agent-Orchestrated** | ✅ PASS | Single speckit.plan agent execution. Clear input (spec.md) and outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md). Handoff to speckit.tasks next. |
| **IV. Test Optionality** | ✅ PASS | No new tests required. Feature is CSS value changes with manual/visual verification. Existing E2E tests may need color assertion updates if currently hardcoded. |
| **V. Simplicity & DRY** | ✅ PASS | Minimal complexity: update centralized design tokens + audit hardcoded values. Leverages existing token architecture. No new abstractions or patterns introduced. |

**Pre-Design Gate Status**: ✅ **PASSED** - All principles satisfied. No violations requiring justification.

### Post-Design Evaluation (After Phase 1)

| Principle | Status | Justification |
|-----------|--------|---------------|
| **I. Specification-First** | ✅ PASS | Design artifacts (research.md, data-model.md, contracts/) align with spec requirements. No scope expansion. All FR items addressed. |
| **II. Template-Driven** | ✅ PASS | All Phase 0-1 artifacts follow prescribed templates. No deviations introduced. |
| **III. Agent-Orchestrated** | ✅ PASS | Phase 0-1 completed by single agent. Clean handoff state achieved. Ready for speckit.tasks. |
| **IV. Test Optionality** | ✅ PASS | Design confirms no new test infrastructure needed. Visual verification sufficient per spec assumptions. |
| **V. Simplicity & DRY** | ✅ PASS | Final design maintains simplicity: CSS token value updates + hardcoded color replacements + one inline style. No complexity introduced. |

**Post-Design Gate Status**: ✅ **PASSED** - Design maintains constitutional compliance. No complexity tracking required.

## Project Structure

### Documentation (this feature)

```text
specs/007-black-background/
├── spec.md              # Feature specification (completed)
├── checklists/
│   └── requirements.md  # Spec validation checklist (completed)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (generated)
├── data-model.md        # Phase 1 output (generated)
├── quickstart.md        # Phase 1 output (generated)
├── contracts/           # Phase 1 output (generated)
│   └── css-changes.md   # File modification contract
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── index.html                          # Add inline background style to prevent white flash
├── src/
│   ├── index.css                       # Update :root design tokens to black theme values
│   ├── App.css                         # Audit/replace hardcoded light background values
│   └── components/
│       └── chat/
│           └── ChatInterface.css       # Audit/replace hardcoded light background values
└── [other files unchanged]

backend/
└── [No changes - theme is frontend-only concern]
```

**Structure Decision**: Web application with React frontend. Changes isolated to frontend presentation layer (CSS + HTML). No backend, database, or state management involvement. This is a View-layer-only update leveraging the existing CSS custom properties architecture.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations detected. This section intentionally left minimal per constitution principle V (Simplicity).
