# Implementation Plan: Add Black Background Theme to App

**Branch**: `009-black-background` | **Date**: 2026-02-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-black-background/spec.md`

## Summary

Apply a true black (#000000) background globally across the Tech Connect app by updating the existing CSS custom property (design token) system. The change centers on modifying `:root` and `html.dark-mode-active` token values in `frontend/src/index.css` to use black/near-black colors, updating text and border tokens for WCAG AA contrast compliance (≥4.5:1), and auditing `App.css` for any hardcoded light background values that bypass the token system. The dark mode toggle (`useAppTheme` hook) and `localStorage`/API-based persistence already exist and require no structural changes — only token value updates.

## Technical Context

**Language/Version**: TypeScript ~5.4 (frontend)
**Primary Dependencies**: React 18, @tanstack/react-query v5, Vite 5
**Storage**: N/A (theme persistence already handled via `localStorage` + user settings API)
**Testing**: Vitest + @testing-library/react (unit); Playwright (e2e)
**Target Platform**: Modern browsers (served via nginx in Docker)
**Project Type**: Web application (frontend-only change)
**Performance Goals**: No regression — zero flash of white/light background on page load or route transitions
**Constraints**: WCAG AA contrast ratio ≥4.5:1 for all text against black background; must not break existing dark mode toggle mechanism
**Scale/Scope**: ~7K frontend LOC; 6 component directories, 2 pages, 1 global CSS file (`index.css`), 1 component CSS file (`App.css`)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development — ✅ PASS

Spec exists at `specs/009-black-background/spec.md` with 6 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, clear scope boundaries, edge cases, and an Out of Scope section.

### II. Template-Driven Workflow — ✅ PASS

All artifacts follow canonical templates (`spec-template.md`, `plan-template.md`). No custom sections added.

### III. Agent-Orchestrated Execution — ✅ PASS

Workflow follows specify → plan → tasks → implement phase ordering. Each agent has a single purpose with well-defined inputs/outputs.

### IV. Test Optionality with Clarity — ✅ PASS

No new tests are explicitly required by the spec. The feature is a CSS token value change — existing visual regression or e2e tests (if any) serve as the baseline. Tests may be added at the implementer's discretion for contrast ratio validation but are not mandated.

### V. Simplicity and DRY — ✅ PASS

The implementation modifies existing CSS custom property values in a single file (`index.css`) and audits one additional file (`App.css`) for hardcoded overrides. No new abstractions, frameworks, or architectural patterns are introduced. The existing `useAppTheme` hook and `dark-mode-active` class mechanism are reused as-is.

**Post-Design Re-Check (Phase 1)**: All five principles remain satisfied. The design introduces:
- Zero new files or components
- Token value changes in 1 file (`index.css`)
- Hardcoded color replacements in 1 file (`App.css`)
- Optional inline `background-color` on `<html>` in `index.html` to prevent flash of white

No new frameworks, patterns, or architectural layers. All changes simplify the color palette to a black-first theme.

## Project Structure

### Documentation (this feature)

```text
specs/009-black-background/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── index.html                  # Root HTML — add inline bg to prevent FOUC
├── src/
│   ├── index.css               # CSS custom property tokens (PRIMARY change target)
│   ├── App.css                 # Component styles (audit for hardcoded light colors)
│   ├── App.tsx                 # Main app component (no changes expected)
│   ├── hooks/
│   │   └── useAppTheme.ts     # Theme toggle hook (no changes expected)
│   ├── components/
│   │   ├── auth/
│   │   ├── board/
│   │   ├── chat/
│   │   ├── common/
│   │   ├── settings/
│   │   └── sidebar/
│   └── pages/
│       ├── ProjectBoardPage.tsx
│       └── SettingsPage.tsx
└── ...
```

**Structure Decision**: Frontend-only change within the existing web application structure. The CSS custom property system in `index.css` is the single source of truth for theme colors. All components already reference these tokens via `var()`. The change is purely a value update — no structural modifications needed.

## Complexity Tracking

> No constitution violations to justify. All design decisions follow simplicity principles:
> - Token value changes only — no new abstractions or patterns
> - Existing dark mode infrastructure (`useAppTheme`, `dark-mode-active` class) reused without modification
> - Hardcoded color audit in `App.css` replaces light values with token references or dark-compatible alternatives
