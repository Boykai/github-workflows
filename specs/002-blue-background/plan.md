# Implementation Plan: Blue Background Color

**Branch**: `002-blue-background` | **Date**: 2026-02-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-blue-background/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Apply a blue background color (#2196F3) to the main app layout and all core screens, ensuring WCAG AA contrast compliance (4.5:1 for text, 3:1 for interactive elements) across both light and dark modes. The implementation leverages the existing CSS custom properties theme system with class-based theming on document root element.

## Technical Context

**Language/Version**: TypeScript 5.4 (frontend), Python (backend - not impacted)  
**Primary Dependencies**: React 18.3, Vite 5.4, CSS custom properties for theming  
**Storage**: localStorage for theme persistence (existing useAppTheme hook)  
**Testing**: Vitest for unit tests, Playwright for E2E tests, @testing-library/react for component tests  
**Target Platform**: Web browsers (Chrome, Firefox, Safari, Edge)  
**Project Type**: Web application (frontend React SPA + Python backend)  
**Performance Goals**: Instant CSS theme application (<16ms), no layout shift  
**Constraints**: WCAG AA contrast ratios (4.5:1 text, 3:1 interactive), maintain existing dark mode functionality  
**Scale/Scope**: Single-page app with core screens (login, dashboard, chat, projects), ~3-5 CSS files impacted

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Check

- ✅ **Specification-First Development**: Complete spec.md exists with 3 prioritized user stories (P1-P3), Given-When-Then acceptance scenarios, and clear scope boundaries
- ✅ **Template-Driven Workflow**: Spec follows spec-template.md, plan follows plan-template.md
- ✅ **Agent-Orchestrated Execution**: Using /speckit.plan agent with clear outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md)
- ✅ **Test Optionality**: Tests not explicitly required by spec; existing E2E tests may need updates for visual validation
- ✅ **Simplicity and DRY**: Extends existing CSS custom properties system rather than introducing new theming framework; no new abstractions needed

**Status**: ✅ PASS - All principles satisfied, ready for Phase 0 research

### Post-Design Check

- ✅ **Specification-First Development**: All design artifacts (research.md, data-model.md, contracts/, quickstart.md) reference and fulfill spec.md requirements
- ✅ **Template-Driven Workflow**: Research follows decision/rationale/alternatives format; data-model follows entity/validation structure; contracts organized by type; quickstart follows step-by-step format
- ✅ **Agent-Orchestrated Execution**: Design phase complete; ready for /speckit.tasks to generate implementation tasks
- ✅ **Test Optionality**: Testing strategy defined in research.md (Playwright visual + axe-core accessibility); tests remain optional per constitution; quickstart includes optional test steps
- ✅ **Simplicity and DRY**: Reuses existing CSS custom properties system with zero new abstractions; no new React hooks or state management; pure CSS implementation

**Status**: ✅ PASS - All principles maintained through design phase. No complexity added beyond spec requirements.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── index.css          # Primary: CSS custom properties for blue background
│   ├── App.css            # Secondary: Component-specific styles 
│   ├── App.tsx            # Theme toggle and layout
│   ├── hooks/
│   │   └── useAppTheme.ts # Existing theme state management (no changes needed)
│   ├── components/
│   │   ├── auth/
│   │   ├── chat/
│   │   ├── sidebar/
│   │   └── [others]/      # Text/button contrast validation
│   └── test/
│       └── [unit tests]   # Optional: contrast validation tests
├── e2e/
│   └── ui.spec.ts         # Optional: visual regression for blue background
└── package.json

backend/
└── [not impacted by this feature]
```

**Structure Decision**: Web application with React frontend. The blue background is purely a frontend CSS change. Primary modifications in `frontend/src/index.css` to update CSS custom properties `--color-bg` and `--color-bg-secondary` for both `:root` (light mode) and `html.dark-mode-active` (dark mode) selectors. Component-level styles in `App.css` and other component files may need text/button color adjustments for WCAG AA contrast compliance.

## Complexity Tracking

**No violations to justify** - All constitution principles satisfied without compromises.

Design decisions maintain simplicity:
- Reuses existing `useAppTheme` hook (no modifications)
- Extends existing CSS custom properties pattern (no new patterns)
- No new state management or abstractions
- Purely declarative CSS changes

All complexity is inherent to the requirement (WCAG AA compliance, dark mode support) rather than introduced by the solution.
