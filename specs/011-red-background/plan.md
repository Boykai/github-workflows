# Implementation Plan: Add Red Background Color to App

**Branch**: `011-red-background` | **Date**: 2026-02-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/011-red-background/spec.md`

## Summary

Update the application's primary background color to red (#E53E3E) by modifying the existing CSS custom property `--color-bg-secondary` in the root stylesheet (`frontend/src/index.css`). The body element already uses `var(--color-bg-secondary)` for its background, so changing the token value propagates globally. The `--color-bg` token is intentionally **not** changed — it remains white/dark for component backgrounds (cards, modals, sidebars) to preserve visual hierarchy and legibility. Foreground text color (`--color-text`) will be adjusted to white (#FFFFFF) to meet WCAG AA contrast requirements (4.5:1 for normal text, 3:1 for interactive elements) against the red surface visible between components. Dark mode will use a darker red (#9B2C2C) for `--color-bg-secondary`. A CSS fallback value is added inline for robustness.

## Technical Context

**Language/Version**: TypeScript ~5.4 (frontend), Python ≥3.11 (backend — no changes)
**Primary Dependencies**: React 18.3, Vite 5, CSS custom properties (no Tailwind/CSS modules)
**Storage**: N/A — no data model changes
**Testing**: Vitest ≥4.0 (frontend unit), Playwright ≥1.58 (E2E)
**Target Platform**: Browser SPA (Chrome, Firefox, Safari, Edge), responsive (mobile/tablet/desktop)
**Project Type**: Web application (backend + frontend) — only frontend changes required
**Performance Goals**: N/A — CSS-only change, no runtime impact
**Constraints**: Must maintain WCAG AA contrast (4.5:1 normal text, 3:1 large text/interactive elements)
**Scale/Scope**: Single CSS file change (`frontend/src/index.css`), potential minor adjustments to component styles for contrast

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | `spec.md` created with 4 prioritized user stories, GWT acceptance scenarios, edge cases |
| II. Template-Driven | ✅ PASS | Using canonical `plan.md` template, all artifacts follow `.specify/templates/` |
| III. Agent-Orchestrated | ✅ PASS | Plan phase produces plan.md, research.md, data-model.md, contracts/, quickstart.md |
| IV. Test Optionality | ✅ PASS | Spec says tests SHOULD be updated if visual regression tests exist; no mandatory new test infrastructure |
| V. Simplicity and DRY | ✅ PASS | Single centralized token change — no abstraction layers, no new files, no new dependencies |

**Gate result: PASS** — no violations, no complexity justification needed.

### Post-Design Re-Evaluation

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | All design artifacts trace to spec.md FRs (FR-001 through FR-008). No scope creep. |
| II. Template-Driven | ✅ PASS | All artifacts (plan.md, research.md, data-model.md, contracts/, quickstart.md) follow canonical templates. |
| III. Agent-Orchestrated | ✅ PASS | Phase 0 and Phase 1 complete with clear handoff to Phase 2 (tasks). |
| IV. Test Optionality | ✅ PASS | No mandatory tests. Existing visual regression tests (if any) should be updated to reflect new color. |
| V. Simplicity and DRY | ✅ PASS | Design modifies exactly one CSS file for the color token. No new abstractions, no new dependencies, no new files. Maximum simplicity for an XS change. |

**Post-design gate result: PASS**

## Project Structure

### Documentation (this feature)

```text
specs/011-red-background/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── index.css          # FR-001, FR-002, FR-003, FR-004, FR-008: update --color-bg-secondary to red,
│   │                      #   adjust --color-text for contrast, add fallback value
│   │                      #   (--color-bg intentionally unchanged — used by component backgrounds)
│   └── (components/)      # FR-007: review overlaid components for legibility — may need minor
│                          #   color overrides if contrast fails on specific elements
```

**Structure Decision**: Web application (existing backend/ + frontend/ structure). Only frontend CSS changes. No new files or directories. The red background is applied via the existing `--color-bg-secondary` custom property used on the `body` element in `frontend/src/index.css`.

## Complexity Tracking

> No constitution violations detected. No complexity justification needed.
