# Implementation Plan: Add Black Background Theme to App

**Branch**: `009-black-background` | **Date**: 2026-02-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-black-background/spec.md`

## Summary

Replace the existing light-mode color tokens with a true black (#000000) background theme across the entire Tech Connect frontend. The implementation updates CSS custom properties in `index.css` (`:root` and `html.dark-mode-active`), audits all hardcoded light background values in component CSS files, and adds an inline style on `<html>` in `index.html` to prevent white flash on load. No new dependencies, no architectural changes — this is a design-token-level color swap using the existing CSS custom property infrastructure.

## Technical Context

**Language/Version**: TypeScript ~5.4 (frontend), React 18
**Primary Dependencies**: React 18, Vite 5, @tanstack/react-query v5, socket.io-client
**Storage**: N/A (theme preference stored via existing `useAppTheme` hook → localStorage + user settings API)
**Testing**: Vitest + @testing-library/react (unit); Playwright (e2e)
**Target Platform**: Modern browsers (Chrome, Firefox, Safari, Edge), served via nginx
**Project Type**: Web application (frontend only for this feature)
**Performance Goals**: No visual flash of white/light background on any page load or route transition
**Constraints**: WCAG AA minimum 4.5:1 contrast ratio for all text against black background
**Scale/Scope**: 3 CSS files (`index.css`, `App.css`, `ChatInterface.css`), 1 HTML file (`index.html`), ~50 component screens

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development — ✅ PASS

Spec exists at `specs/009-black-background/spec.md` with 6 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, edge cases, clear scope boundaries, and out-of-scope declarations. Requirements checklist passed all items.

### II. Template-Driven Workflow — ✅ PASS

All artifacts follow canonical templates (`spec-template.md`, `plan-template.md`). No custom sections added.

### III. Agent-Orchestrated Execution — ✅ PASS

Workflow follows specify → plan → tasks → implement phase ordering. Plan phase produces the standard artifact set (plan.md, research.md, data-model.md, contracts/, quickstart.md).

### IV. Test Optionality with Clarity — ✅ PASS

No tests are explicitly requested in the spec. This is a CSS-only visual change with no logic changes. Visual verification (manual inspection + contrast ratio checks) is the appropriate validation method. Existing tests must continue to pass as a regression baseline.

### V. Simplicity and DRY — ✅ PASS

Implementation modifies only existing CSS custom properties and replaces hardcoded color values. No new abstractions, frameworks, or architectural patterns introduced. The approach leverages the existing design token system — the simplest possible path.

**Post-Design Re-Check (Phase 1)**: All five principles remain satisfied. The design introduces:
- 0 new files (modifications only to existing CSS and HTML)
- 0 new dependencies
- 0 new architectural patterns
- Token value changes in 1 file (`index.css`) propagate to all components via `var()` references

No complexity justification needed.

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
├── index.html                          # Add inline background-color to prevent flash
├── src/
│   ├── index.css                       # Update :root and html.dark-mode-active tokens
│   ├── App.css                         # Audit/replace hardcoded light backgrounds
│   ├── components/
│   │   ├── chat/
│   │   │   └── ChatInterface.css       # Audit/replace hardcoded light backgrounds
│   │   ├── board/
│   │   │   └── colorUtils.ts           # Verify badge colors work on dark background
│   │   └── ...                         # (remaining components use var() tokens — auto-updated)
│   └── hooks/
│       └── useAppTheme.ts              # Existing — no changes needed
```

**Structure Decision**: Frontend-only modifications. The app already uses a CSS custom property system where `:root` defines light-mode tokens and `html.dark-mode-active` defines dark-mode overrides. All components reference these tokens via `var()`. Changing the token values in `index.css` propagates the black background globally. The only additional work is auditing and replacing ~15 hardcoded color values in `App.css` and `ChatInterface.css`.

## Complexity Tracking

> No constitution violations to justify. All design decisions follow simplicity principles:
> - Token value changes only — no new abstractions or patterns
> - Hardcoded color replacements use existing `var()` tokens or dark-compatible literal values
> - Flash prevention uses a single inline style attribute — minimal intervention
