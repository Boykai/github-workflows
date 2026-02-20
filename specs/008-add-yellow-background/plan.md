# Implementation Plan: Add Yellow Background Color to App

**Branch**: `008-add-yellow-background` | **Date**: 2026-02-20 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/008-add-yellow-background/spec.md`

## Summary

Apply a soft yellow background color (#FFFDE7) globally across the application by updating the CSS custom properties in `frontend/src/index.css`. The yellow background is scoped to light mode only; dark mode retains its existing colors. The change uses the existing CSS variable system (`--color-bg-secondary`) to ensure maintainability and consistency. No new dependencies, components, or backend changes are required.

## Technical Context

**Language/Version**: TypeScript ~5.4 (frontend)
**Primary Dependencies**: React 18.3, Vite 5.4
**Storage**: N/A (CSS-only change)
**Testing**: vitest (unit), Playwright (E2E) — manual verification sufficient for CSS change
**Target Platform**: Web browser (all modern browsers)
**Project Type**: Web application (frontend only for this feature)
**Performance Goals**: N/A (no runtime impact — static CSS change)
**Constraints**: Must maintain WCAG AA contrast ratio (≥4.5:1) against primary text
**Scale/Scope**: Single CSS file change affecting global background color

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | spec.md created with 4 prioritized user stories and acceptance scenarios |
| II. Template-Driven | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated | ✅ PASS | specify → plan → tasks → implement phase sequence followed |
| IV. Test Optionality | ✅ PASS | Tests not mandated in spec; CSS-only change is visually verifiable. No test changes required. |
| V. Simplicity/DRY | ✅ PASS | Reuses existing CSS variable system. Single file change. No new abstractions. |

**Post-Phase 1 Re-check**: ✅ PASS — Design involves modifying 2 CSS variable values in a single file. Maximum simplicity achieved.

## Project Structure

### Documentation (this feature)

```text
specs/008-add-yellow-background/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── file-changes.md  # Exact CSS modifications
└── tasks.md             # Phase 2 output (/speckit.tasks - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   └── index.css        # Global styles with CSS custom properties (MODIFIED)
```

**Structure Decision**: Web application structure. This feature only modifies `frontend/src/index.css` — the global stylesheet that defines CSS custom properties (`:root` and `html.dark-mode-active` selectors). No new files are created.

## Complexity Tracking

> No violations — all constitution checks pass. No complexity justifications needed.
