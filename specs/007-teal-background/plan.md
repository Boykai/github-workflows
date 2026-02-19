# Implementation Plan: Add Teal Background Color to App

**Branch**: `007-teal-background` | **Date**: 2026-02-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/007-teal-background/spec.md`

## Summary

Apply a teal background color (#0D9488) globally to the app by updating CSS custom properties in the existing design token system (`index.css`). Define the teal as a new `--color-bg-app` token used on the `body` element, with a darker variant (#0F766E) for dark mode. Ensure all text on the teal background meets WCAG AA contrast (white text: #FFFFFF achieves ~4.53:1 on #0D9488). No new dependencies, no structural changes — purely a CSS token update in one file.

## Technical Context

**Language/Version**: TypeScript ~5.4 (frontend), Python 3.12 (backend — no changes)
**Primary Dependencies**: React 18.3, Vite 5.4 (no new dependencies)
**Storage**: N/A (CSS-only change)
**Testing**: Playwright (E2E visual verification), vitest (no new unit tests needed)
**Target Platform**: Web browser (Chrome, Firefox, Safari, Edge)
**Project Type**: Web application (frontend only)
**Performance Goals**: N/A (negligible impact — single CSS property change)
**Constraints**: WCAG AA contrast compliance (4.5:1 minimum for normal text on teal)
**Scale/Scope**: Single CSS file change affecting all views globally

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | spec.md complete with 3 prioritized user stories, acceptance scenarios, and edge cases |
| II. Template-Driven | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated | ✅ PASS | specify → plan → tasks → implement phase sequence followed |
| IV. Test Optionality | ✅ PASS | Tests not mandated in spec; visual changes can be verified via E2E screenshots. No new test files required. |
| V. Simplicity/DRY | ✅ PASS | Extends existing CSS custom property system; single token defined once in `:root`; no new abstractions or dependencies |

## Project Structure

### Documentation (this feature)

```text
specs/007-teal-background/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── file-changes.md  # CSS change contract
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── index.css        # ← MODIFY: Add --color-bg-app token to :root and dark mode, apply to body
│   ├── App.css          # No changes needed (components already use var() tokens)
│   ├── App.tsx          # No changes needed
│   └── main.tsx         # No changes needed
└── index.html           # No changes needed
```

**Structure Decision**: Web application structure — only `frontend/src/index.css` requires modification. The existing CSS custom property system in `:root` / `html.dark-mode-active` is the single source of truth for all design tokens. The body already references `var(--color-bg-secondary)` for background; this will be updated to a new dedicated `--color-bg-app` token.

## Complexity Tracking

> No constitution violations identified. No complexity justifications needed.

## Constitution Re-Check (Post-Design)

*Re-evaluated after Phase 1 design artifacts were generated.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | spec.md was completed before any design work |
| II. Template-Driven | ✅ PASS | plan.md, research.md, data-model.md, contracts/file-changes.md, quickstart.md all follow canonical templates |
| III. Agent-Orchestrated | ✅ PASS | Phase sequence respected: specify → plan (current). Tasks and implementation deferred to later phases |
| IV. Test Optionality | ✅ PASS | No tests mandated; visual change verified via existing E2E infrastructure |
| V. Simplicity/DRY | ✅ PASS | One new CSS custom property in one file. Minimal change, maximum coverage. No new abstractions. |
