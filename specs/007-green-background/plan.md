# Implementation Plan: Add Green Background Color to App

**Branch**: `007-green-background` | **Date**: 2026-02-20 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/007-green-background/spec.md`

## Summary

Apply a green background color globally to the application's root element using a CSS custom property (`--color-bg-primary`) defined in `index.css`. The chosen shade (#2D6A4F) meets WCAG AA contrast requirements against the existing text colors. The change is isolated to the global stylesheet with a hardcoded fallback for browsers that do not support CSS custom properties. Existing UI components retain their own backgrounds and layer on top of the green root background.

## Technical Context

**Language/Version**: TypeScript 5.4, CSS3
**Primary Dependencies**: React 18.3, Vite 5.4
**Storage**: N/A (CSS-only change)
**Testing**: Vitest (unit), Playwright (E2E)
**Target Platform**: Modern web browsers (Chrome, Firefox, Safari, Edge)
**Project Type**: Web application (frontend React SPA + backend Python API)
**Performance Goals**: N/A (no performance impact from CSS color change)
**Constraints**: Must maintain WCAG AA contrast (4.5:1) for all text on green background; must not regress existing layout
**Scale/Scope**: 1 file change (`frontend/src/index.css`); no backend, API, or state management changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Evaluation (Before Phase 0)

| Principle | Status | Justification |
|-----------|--------|---------------|
| **I. Specification-First** | ✅ PASS | Complete spec.md with 3 prioritized user stories (P1: Green background visible, P2: Text readability, P3: Overlay consistency), Given-When-Then scenarios, and clear scope boundaries |
| **II. Template-Driven** | ✅ PASS | Following plan-template.md structure. All sections populated per template requirements |
| **III. Agent-Orchestrated** | ✅ PASS | specify → plan phase sequence followed. Clear input (spec.md) and outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md) |
| **IV. Test Optionality** | ✅ PASS | No tests mandated in spec. Feature is a CSS color change verifiable by visual inspection |
| **V. Simplicity & DRY** | ✅ PASS | Minimal complexity: 1 CSS custom property addition and 1 background declaration change in a single file. No abstractions, no new patterns. Follows YAGNI principle |

**Pre-Design Gate Status**: ✅ **PASSED** — All principles satisfied. No violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/007-green-background/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── index.css        # Global CSS — add --color-bg-primary variable and update body background
│   └── [other files unchanged]
└── [other files unchanged]

backend/
└── [No changes — background color is a frontend-only concern]
```

**Structure Decision**: Web application with React frontend. Change isolated to a single global stylesheet file (`frontend/src/index.css`). No backend, component, or state management involvement. This is a View-layer-only CSS update.

## Complexity Tracking

> No constitution violations identified. No complexity justifications needed.

## Constitution Re-Check (Post-Design)

*Re-evaluated after Phase 1 design artifacts were generated.*

| Principle | Status | Justification |
|-----------|--------|---------------|
| **I. Specification-First** | ✅ PASS | Design artifacts align with spec requirements. No scope expansion |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/file-changes.md, quickstart.md all follow canonical templates |
| **III. Agent-Orchestrated** | ✅ PASS | Phase sequence respected: specify → plan (current). Tasks and implementation deferred to later phases |
| **IV. Test Optionality** | ✅ PASS | No tests mandated. Visual verification sufficient for CSS color change |
| **V. Simplicity & DRY** | ✅ PASS | Single CSS custom property in one file. Reusable via `var(--color-bg-primary)`. Hardcoded fallback for graceful degradation. No over-engineering |

**Result**: All gates pass. No complexity justifications needed. Ready for Phase 2 (`/speckit.tasks`).
