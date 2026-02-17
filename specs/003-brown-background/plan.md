# Implementation Plan: Brown Background Color

**Branch**: `003-brown-background` | **Date**: 2026-02-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-brown-background/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Apply a brown background color (#8B5C2B or approved variant) across all screens and components of the Tech Connect app. The implementation updates CSS custom properties in `frontend/src/index.css` to change `--color-bg` and `--color-bg-secondary` to brown shades for both light and dark modes. Text colors are adjusted to maintain WCAG AA contrast ratios. Modals, sidebars, navigation bars, and overlay components inherit the brown theme through existing CSS variable usage. No backend, database, or architectural changes required — this is a purely visual/CSS change.

## Technical Context

**Language/Version**: TypeScript 5.4, CSS3  
**Primary Dependencies**: React 18.3, Vite 5.4  
**Storage**: N/A (visual styling change only)  
**Testing**: Vitest (unit), Playwright (E2E)  
**Target Platform**: Modern web browsers (Chrome, Firefox, Safari, Edge)  
**Project Type**: Web (frontend React SPA + backend Python API)  
**Performance Goals**: N/A (no performance impact from CSS color changes)  
**Constraints**: WCAG AA contrast ratio (4.5:1 normal text, 3:1 large text) must be maintained  
**Scale/Scope**: 1-2 CSS file changes; no database, API, or component logic changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Evaluation (Before Phase 0)

| Principle | Status | Justification |
|-----------|--------|---------------|
| **I. Specification-First** | ✅ PASS | Complete spec.md with 3 prioritized user stories (P1: Consistent brown background, P2: Overlays and navigation, P3: Dark mode variant), Given-When-Then acceptance scenarios, edge cases, and clear scope (CSS theming only). |
| **II. Template-Driven** | ✅ PASS | Following plan-template.md structure. All sections populated per template requirements. No custom sections added. |
| **III. Agent-Orchestrated** | ✅ PASS | Single speckit.plan agent execution. Clear input (spec.md) and outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md). Handoff to speckit.tasks next. |
| **IV. Test Optionality** | ✅ PASS | No new tests required. Feature is CSS variable value changes with manual and automated (Lighthouse/axe) verification. Existing tests should continue to pass as no component logic changes. |
| **V. Simplicity & DRY** | ✅ PASS | Minimal complexity: update CSS custom property values in a single file (`index.css`). The app already uses CSS variables for theming — this feature leverages that existing infrastructure. No new abstractions or patterns. YAGNI principle maintained. |

**Pre-Design Gate Status**: ✅ **PASSED** — All principles satisfied. No violations requiring justification.

### Post-Design Evaluation (After Phase 1)

| Principle | Status | Justification |
|-----------|--------|---------------|
| **I. Specification-First** | ✅ PASS | Design artifacts align with spec requirements. Color palette defined centrally (FR-009). All user stories addressable via CSS variable changes. No scope expansion. |
| **II. Template-Driven** | ✅ PASS | All Phase 0-1 artifacts follow prescribed templates. No deviations introduced. |
| **III. Agent-Orchestrated** | ✅ PASS | Phase 0-1 completed by single agent. Clean handoff state achieved. Ready for speckit.tasks. |
| **IV. Test Optionality** | ✅ PASS | Design confirms no new test infrastructure needed. Manual verification + accessibility audit tools sufficient per spec assumptions. |
| **V. Simplicity & DRY** | ✅ PASS | Final design maintains simplicity: CSS variable value updates in one file. Hardcoded colors in hover/interactive states reviewed and adjusted only where they clash with the brown background. No new complexity introduced. |

**Post-Design Gate Status**: ✅ **PASSED** — Design maintains constitutional compliance. No complexity tracking required.

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
│   ├── index.css             # CSS custom properties (:root and html.dark-mode-active)
│   ├── App.css               # Component styles (may need hardcoded color adjustments)
│   ├── App.tsx                # Dark mode toggle (no changes expected)
│   ├── hooks/
│   │   └── useAppTheme.ts    # Theme toggle hook (no changes expected)
│   └── components/
│       ├── chat/
│       │   └── ChatInterface.css  # Chat component styles (may need hardcoded color adjustments)
│       ├── sidebar/
│       │   └── ProjectSidebar.tsx # Sidebar component (no changes - uses CSS vars)
│       └── common/
│           └── ErrorDisplay.tsx   # Error display component (no changes - uses CSS vars)
└── [other files unchanged]

backend/
└── [No changes - brown background is frontend-only concern]
```

**Structure Decision**: Web application with React frontend. Changes isolated to frontend CSS layer (custom property values). No backend involvement. The existing CSS variable theming system (`--color-bg`, `--color-bg-secondary`, etc.) makes this change centralized and minimal.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations detected. This section intentionally left minimal per constitution principle V (Simplicity).
