# Implementation Plan: Add Purple Background Color to App

**Branch**: `019-purple-background` | **Date**: 2026-03-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/019-purple-background/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Update the app's global background from white/neutral to a purple color scheme (#6B21A8). The change is implemented entirely through CSS custom property (design token) updates in `frontend/src/index.css`. The existing theming architecture (CSS variables → Tailwind config → component classes) means updating the variable values automatically propagates the purple theme across all components. Both light mode and dark mode variants are defined. No new components, hooks, dependencies, or architectural changes are needed — this is a pure CSS token update.

## Technical Context

**Language/Version**: TypeScript 5.x, CSS3
**Primary Dependencies**: Tailwind CSS 3.4, PostCSS, tailwindcss-animate
**Storage**: N/A (no data persistence changes)
**Testing**: Vitest 4.x + React Testing Library (existing tests); visual cross-browser verification
**Target Platform**: Web browser (desktop + mobile; Chrome, Firefox, Safari, Edge)
**Project Type**: Web application (frontend-only change)
**Performance Goals**: N/A (CSS variable update has zero runtime performance impact)
**Constraints**: WCAG AA contrast ratio ≥ 4.5:1 for all text against purple background
**Scale/Scope**: Single file change (`frontend/src/index.css`) + audit for hardcoded color overrides

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| **I. Specification-First** | ✅ PASS | `spec.md` exists with 5 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, independent test criteria, edge cases, and explicit scope boundaries |
| **II. Template-Driven Workflow** | ✅ PASS | All artifacts follow canonical templates; plan.md follows plan-template.md structure |
| **III. Agent-Orchestrated Execution** | ✅ PASS | Single-responsibility: speckit.plan generates plan artifacts only; tasks.md deferred to speckit.tasks |
| **IV. Test Optionality** | ✅ PASS | Tests not explicitly mandated in spec. This is a CSS-only change — visual verification and contrast auditing are the appropriate validation methods. No unit tests required. |
| **V. Simplicity and DRY** | ✅ PASS | Uses the existing CSS variable design token system. No new abstractions, no new files, no new dependencies. Color defined in a single source of truth (`index.css`). Follows YAGNI. |

**Gate Result**: ✅ ALL PASS — Proceeding to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/019-purple-background/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── css-variables-contract.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── index.css                  # Modified: update CSS custom property values
│   ├── App.tsx                    # Audit: verify bg-background usage (already correct)
│   ├── components/
│   │   └── ThemeProvider.tsx       # No changes: manages light/dark class toggle
│   └── ...
└── tailwind.config.js             # No changes: already references CSS variables
```

**Structure Decision**: Web application structure (Option 2). This feature is frontend-only, modifying the existing CSS design token values in `frontend/src/index.css`. No backend changes required. No new files created in `src/`. The Tailwind config and ThemeProvider already support the token-based architecture — only the token values change.

## Complexity Tracking

> No constitution violations detected. No complexity justifications needed.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |

## Constitution Re-Check (Post Phase 1 Design)

*Re-evaluated after completing research.md, data-model.md, contracts/, and quickstart.md.*

| Principle | Status | Post-Design Evidence |
|-----------|--------|----------------------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace directly to spec.md user stories (US1–US5) and functional requirements (FR-001 through FR-007) |
| **II. Template-Driven Workflow** | ✅ PASS | plan.md follows plan-template.md; all Phase 0/1 artifacts generated per template |
| **III. Agent-Orchestrated Execution** | ✅ PASS | speckit.plan produced plan.md, research.md, data-model.md, contracts/, quickstart.md; tasks.md deferred to speckit.tasks |
| **IV. Test Optionality** | ✅ PASS | No unit tests required for CSS-only change. Validation via visual inspection and WCAG contrast audit. |
| **V. Simplicity and DRY** | ✅ PASS | Single file modification (index.css). No new abstractions, dependencies, or patterns. Uses existing design token architecture. Color values centralized in one location. |

**Gate Result**: ✅ ALL PASS — Design phase complete. Ready for Phase 2 (tasks generation via speckit.tasks).

## Generated Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| Implementation Plan | `specs/019-purple-background/plan.md` | ✅ Complete |
| Research | `specs/019-purple-background/research.md` | ✅ Complete |
| Data Model | `specs/019-purple-background/data-model.md` | ✅ Complete |
| CSS Variables Contract | `specs/019-purple-background/contracts/css-variables-contract.md` | ✅ Complete |
| Quickstart Guide | `specs/019-purple-background/quickstart.md` | ✅ Complete |
| Agent Context | `.github/agents/copilot-instructions.md` | ✅ Updated |
