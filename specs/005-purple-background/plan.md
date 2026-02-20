# Implementation Plan: Add Purple Background Color to App

**Branch**: `005-purple-background` | **Date**: 2026-02-20 | **Spec**: [spec.md](spec.md)
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
**Scale/Scope**: 2 file changes (frontend/src/index.css, frontend/src/App.css); no backend, database, or state management changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Evaluation (Before Phase 0)

| Principle | Status | Justification |
|-----------|--------|---------------|
| **I. Specification-First** | ✅ PASS | Complete spec.md with 3 prioritized user stories |
| **II. Template-Driven Workflow** | ✅ PASS | Using standard plan template |
| **III. Agent-Orchestrated Execution** | ✅ PASS | Following speckit workflow |
| **IV. Test Optionality** | ✅ PASS | No tests required for CSS-only change |
| **V. Simplicity and DRY** | ✅ PASS | Minimal 2-file change, reuses existing CSS variable system |

## Project Structure

### Documentation (this feature)

```text
specs/005-purple-background/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Technical research and decisions
├── data-model.md        # Entity definitions (CSS variables)
├── quickstart.md        # Step-by-step implementation guide
├── contracts/
│   └── file-changes.md  # Exact file modification contract
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Implementation tasks
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── index.css        # Global CSS variables and base styles (MODIFIED)
│   └── App.css          # App component styles (MODIFIED)
└── index.html           # HTML entry point (unchanged)
```

**Structure Decision**: Web application structure. Only frontend CSS files are modified; no backend changes needed.

## Complexity Tracking

No violations — this is a minimal CSS-only change.
