# Implementation Plan: Ruby-Colored Background Theme

**Branch**: `018-ruby-background-theme` | **Date**: 2026-03-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/018-ruby-background-theme/spec.md`

## Summary

Apply a ruby-colored background (deep red, #9B111E) to the application by updating the existing CSS custom property theming system in `frontend/src/index.css`. The change targets the `--background` token (and related foreground tokens) in both `:root` (light) and `.dark` scopes, leveraging the existing Tailwind CSS + HSL custom property architecture. Foreground colors will be adjusted to ensure WCAG AA 4.5:1 contrast compliance. No new dependencies or structural changes are required—this is a pure CSS token update.

## Technical Context

**Language/Version**: TypeScript 5.x (React 18 frontend), CSS3 with Tailwind CSS  
**Primary Dependencies**: React 18, Tailwind CSS 3.x, shadcn/ui component library, `tailwindcss-animate`  
**Storage**: N/A (frontend-only styling change)  
**Testing**: Vitest (frontend unit tests exist in `frontend/src/test/`)  
**Target Platform**: Web browsers (desktop, tablet, mobile)  
**Project Type**: Web application (frontend + backend monorepo)  
**Performance Goals**: N/A (no runtime performance impact—static CSS change)  
**Constraints**: WCAG AA minimum 4.5:1 contrast ratio for all foreground text against ruby background  
**Scale/Scope**: Single CSS file change (`index.css`) affecting global theme tokens; potential adjustments to component-level foreground colors if contrast fails

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | `spec.md` exists with prioritized user stories (P1–P3), acceptance scenarios, and edge cases |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates; plan.md uses plan-template.md structure |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase produces plan.md, research.md, data-model.md, contracts/, quickstart.md per workflow |
| IV. Test Optionality with Clarity | ✅ PASS | Tests not explicitly requested in spec; contrast verification is a manual/tool check, not automated test |
| V. Simplicity and DRY | ✅ PASS | Change is minimal—updating existing CSS tokens in a single file; no new abstractions introduced |

**Gate Result**: ✅ ALL PASS — Proceed to Phase 0.

### Post-Design Re-Check (after Phase 1)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | Design artifacts trace directly to spec requirements (FR-001 through FR-008) |
| II. Template-Driven Workflow | ✅ PASS | All Phase 0/1 artifacts generated: research.md, data-model.md, contracts/README.md, quickstart.md |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase complete; agent context updated via `update-agent-context.sh copilot` |
| IV. Test Optionality with Clarity | ✅ PASS | No tests mandated; contrast verification documented as manual check in quickstart.md |
| V. Simplicity and DRY | ✅ PASS | Solution modifies only 4 CSS token values in 1 file; no new abstractions, dependencies, or patterns |

**Post-Design Gate Result**: ✅ ALL PASS — Ready for Phase 2 (tasks generation).

## Project Structure

### Documentation (this feature)

```text
specs/018-ruby-background-theme/
├── plan.md              # This file
├── research.md          # Phase 0: Color research & contrast analysis
├── data-model.md        # Phase 1: Design token definitions
├── quickstart.md        # Phase 1: Quick implementation guide
├── contracts/           # Phase 1: N/A (no API contracts for CSS-only change)
│   └── README.md        # Explanation of why contracts are not applicable
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── index.css              # PRIMARY: Theme tokens (:root, .dark) — update --background, --foreground
│   ├── App.tsx                # Uses bg-background text-foreground — inherits token changes
│   ├── components/
│   │   └── ThemeProvider.tsx   # Toggles .dark class — no changes needed
│   └── ...
└── tailwind.config.js         # Maps hsl(var(--background)) — no changes needed
```

**Structure Decision**: Web application structure (frontend + backend). This feature only touches the frontend, specifically `frontend/src/index.css` where theme tokens are defined. The Tailwind config and ThemeProvider are consumed as-is with no modifications needed—they already reference `hsl(var(--background))` and toggle `.dark` class respectively.

## Complexity Tracking

> No constitution violations detected. No complexity justifications needed.
