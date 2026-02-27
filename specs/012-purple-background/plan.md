# Implementation Plan: Add Purple Background Color to Application

**Branch**: `012-purple-background` | **Date**: 2026-02-27 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/012-purple-background/spec.md`

## Summary

Update the application's primary background color to purple by modifying the centralized CSS custom property `--background` in `frontend/src/index.css`. The change applies to both light and dark mode variants using WCAG AA compliant HSL values. The `--background` token is consumed by Tailwind's `bg-background` utility class, which is already applied to `body` and multiple components — so changing the token value propagates the purple background automatically across all pages and routes with zero component-level changes. Secondary surfaces (`--card`, `--popover`, etc.) and foreground colors (`--foreground`) will be audited to ensure sufficient contrast.

## Technical Context

**Language/Version**: TypeScript ~5.4, CSS3 (HSL custom properties)
**Primary Dependencies**: React 18.3, Tailwind CSS 3.x, shadcn/ui (CSS variable system)
**Storage**: N/A (no backend/storage changes)
**Testing**: vitest (frontend unit), manual visual inspection for color/contrast
**Target Platform**: Browser SPA (Chrome, Firefox, Safari, Edge)
**Project Type**: Web application (frontend-only CSS change)
**Performance Goals**: N/A (no performance-sensitive changes — CSS variable update is instant)
**Constraints**: WCAG AA contrast ratio ≥ 4.5:1 for all text against new purple background
**Scale/Scope**: 1 file modified (`frontend/src/index.css`), ~4 CSS variable lines changed

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | `spec.md` created with 5 prioritized user stories (P1–P3), GWT acceptance scenarios, edge cases, and measurable success criteria |
| II. Template-Driven | ✅ PASS | Using canonical `plan.md` template; all artifacts follow `.specify/templates/` |
| III. Agent-Orchestrated | ✅ PASS | Plan phase produces plan.md, research.md, data-model.md, contracts/, quickstart.md |
| IV. Test Optionality | ✅ PASS | Tests not explicitly mandated in spec. Existing tests should continue to pass. Manual visual inspection and contrast audit are the primary verification methods. |
| V. Simplicity and DRY | ✅ PASS | Change is limited to CSS custom property values in a single file (`index.css`). No new abstractions, no new components, no new dependencies. The existing `--background` token and `bg-background` Tailwind utility propagate the change automatically. |

**Gate result: PASS** — no violations, no complexity justification needed.

### Post-Design Re-Evaluation

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | All design artifacts trace back to spec.md FRs (FR-001 through FR-008). No scope creep. |
| II. Template-Driven | ✅ PASS | All artifacts (plan.md, research.md, data-model.md, contracts/, quickstart.md) follow canonical templates. |
| III. Agent-Orchestrated | ✅ PASS | Phase 0 and Phase 1 complete with clear handoff to Phase 2 (tasks). |
| IV. Test Optionality | ✅ PASS | No tests mandated. Existing vitest suite covers regression. Contrast verification is manual (WCAG audit tool). |
| V. Simplicity and DRY | ✅ PASS | Entire change is 4 CSS variable value updates in one file. No new files, components, or dependencies. Maximum simplicity. |

**Post-design gate result: PASS**

## Project Structure

### Documentation (this feature)

```text
specs/012-purple-background/
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
│   ├── index.css                              # FR-001, FR-002, FR-003, FR-004, FR-007: Update --background HSL values in :root and .dark
│   ├── App.tsx                                # No changes — already uses bg-background via Tailwind
│   ├── components/
│   │   ├── ThemeProvider.tsx                   # No changes — light/dark class toggling already works
│   │   └── ui/
│   │       ├── button.tsx                     # No changes — uses bg-background, bg-primary, etc. via tokens
│   │       └── input.tsx                      # No changes — uses bg-background via tokens
│   └── tailwind.config.js                     # No changes — background already maps to hsl(var(--background))
```

**Structure Decision**: Web application (existing `frontend/` structure). Only `frontend/src/index.css` requires modification. All other files consume the `--background` CSS custom property indirectly through Tailwind's `bg-background` utility and are unaffected at the code level.

## Complexity Tracking

> No constitution violations detected. No complexity justification needed.
