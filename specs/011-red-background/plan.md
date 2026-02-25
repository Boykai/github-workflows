# Implementation Plan: Add Red Background Color to Application

**Branch**: `011-red-background` | **Date**: 2026-02-25 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/011-red-background/spec.md`

## Summary

Update the application's global background color to red by modifying the existing CSS custom property tokens (`--color-bg`, `--color-bg-secondary`) in `frontend/src/index.css`. Both light mode (`:root`) and dark mode (`html.dark-mode-active`) variants will be updated with red shades chosen to meet WCAG AA contrast requirements (≥4.5:1 against text). The change is purely CSS — no new dependencies, components, or backend changes required. All existing component-level backgrounds use `var(--color-bg)` or `var(--color-bg-secondary)` tokens, so the change cascades automatically.

## Technical Context

**Language/Version**: TypeScript ~5.4 (frontend)
**Primary Dependencies**: React 18, Vite 5, CSS custom properties (native)
**Storage**: N/A
**Testing**: Vitest + React Testing Library (frontend unit), Playwright (frontend e2e)
**Target Platform**: Browser (SPA served via nginx), all viewports (320px–2560px)
**Project Type**: Web application — separate `backend/` and `frontend/` directories
**Performance Goals**: N/A — CSS-only change, no runtime performance impact
**Constraints**: WCAG AA contrast ratio ≥4.5:1 for all text against red backgrounds
**Scale/Scope**: 1 file change (`frontend/src/index.css`), 2–4 token values updated

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | `spec.md` contains 3 prioritized user stories with acceptance scenarios |
| II. Template-Driven Workflow | ✅ PASS | All artifacts use canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan agent producing well-defined outputs for subsequent phases |
| IV. Test Optionality | ✅ PASS | Spec does not mandate new tests. Visual regression check is SHOULD-level (FR-008). Existing tests must continue passing. |
| V. Simplicity and DRY | ✅ PASS | Change modifies existing CSS tokens — no new abstractions, no new files, no new dependencies. Maximum simplicity. |

**Gate result**: PASS — proceed to Phase 0.

### Post-Design Re-evaluation (after Phase 1)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | All design artifacts trace to spec.md requirements |
| II. Template-Driven Workflow | ✅ PASS | All Phase 0/1 outputs follow canonical structure |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan agent produced defined outputs; clear handoff to `/speckit.tasks` |
| IV. Test Optionality | ✅ PASS | No new tests mandated; existing tests unaffected by CSS token changes |
| V. Simplicity and DRY | ✅ PASS | Single-file CSS change. No complexity added. Complexity Tracking empty. |

**Post-design gate result**: PASS — proceed to Phase 2 (tasks).

## Project Structure

### Documentation (this feature)

```text
specs/011-red-background/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (N/A — CSS-only change, no new APIs)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── index.css            # Global stylesheet — PRIMARY CHANGE TARGET
│   ├── App.tsx              # Root component
│   ├── App.css              # App-level styles (audit for conflicts)
│   ├── components/          # Component styles (audit for hardcoded backgrounds)
│   ├── hooks/
│   │   └── useAppTheme.ts   # Theme toggle hook (no changes needed)
│   └── pages/               # Page components (audit for hardcoded backgrounds)
└── index.html               # HTML entry point (audit for inline styles)
```

**Structure Decision**: Existing web application structure with separate `backend/` and `frontend/` directories. This feature only touches `frontend/src/index.css`. No new directories or files needed.

## Complexity Tracking

> No constitution violations found. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
