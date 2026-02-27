# Implementation Plan: Add Pink Background Color to App

**Branch**: `012-pink-background` | **Date**: 2026-02-27 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/012-pink-background/spec.md`

## Summary

Update the app's root-level background color to pink (#FFC0CB) by changing the `--background` CSS custom property in `frontend/src/index.css`. The color is already defined as a centralized design token (HSL value) consumed via Tailwind's `bg-background` utility. Light mode gets the standard pink (`350 100% 88%`), dark mode gets a dark-appropriate pink variant (`350 30% 12%`). No new files, no new dependencies, no backend changes — a single CSS file edit.

## Technical Context

**Language/Version**: TypeScript ~5.4, CSS3
**Primary Dependencies**: React 18.3, Tailwind CSS 3, shadcn/ui (CSS custom properties in HSL format)
**Storage**: N/A (no backend/storage changes)
**Testing**: vitest (frontend unit), Playwright (E2E)
**Target Platform**: Browser SPA (desktop + mobile)
**Project Type**: Web application (frontend-only CSS change)
**Performance Goals**: N/A (zero runtime cost — CSS custom property value change only)
**Constraints**: WCAG AA contrast ratio ≥ 4.5:1 for normal text against pink background
**Scale/Scope**: 1 CSS file modified (`frontend/src/index.css`), 2 lines changed

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | `spec.md` created with 4 prioritized user stories (P1, P2), GWT acceptance scenarios, edge cases, and success criteria |
| II. Template-Driven | ✅ PASS | Using canonical `plan.md` template, all artifacts follow `.specify/templates/` |
| III. Agent-Orchestrated | ✅ PASS | Plan phase produces plan.md, research.md, data-model.md, contracts/, quickstart.md |
| IV. Test Optionality | ✅ PASS | Tests not explicitly mandated in spec. Existing tests should continue to pass. No new test infrastructure needed for a CSS value change. |
| V. Simplicity and DRY | ✅ PASS | Single CSS custom property value change — the simplest possible approach. No new abstractions, no new tokens, no new files. Reuses the existing `--background` design token. |

**Gate result: PASS** — no violations, no complexity justification needed.

### Post-Design Re-Evaluation

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | All design artifacts trace back to spec.md FRs (FR-001 through FR-008). No scope creep. |
| II. Template-Driven | ✅ PASS | All artifacts (plan.md, research.md, data-model.md, contracts/, quickstart.md) follow canonical templates. |
| III. Agent-Orchestrated | ✅ PASS | Phase 0 and Phase 1 complete with clear handoff to Phase 2 (tasks). |
| IV. Test Optionality | ✅ PASS | No tests mandated. Existing vitest and Playwright suites cover regression. A CSS custom property value change requires no new tests. |
| V. Simplicity and DRY | ✅ PASS | Changing 2 HSL values in 1 file. Zero new abstractions, zero new dependencies, zero new files. This is the simplest possible implementation. |

**Post-design gate result: PASS**

## Project Structure

### Documentation (this feature)

```text
specs/012-pink-background/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   └── index.css        # FR-001, FR-002, FR-004, FR-006, FR-008: Update --background HSL values for light and dark mode
```

**Structure Decision**: Web application (existing `frontend/` structure). No new files. Single modification to `frontend/src/index.css` — updating the `--background` CSS custom property values in both `:root` (light mode) and `.dark` (dark mode) selectors.

## Complexity Tracking

> No constitution violations detected. No complexity justification needed.
