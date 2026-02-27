# Implementation Plan: Modern UI Refresh

**Branch**: `001-modern-ui-refresh` | **Date**: 2026-02-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-modern-ui-refresh/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Refresh the application's UI to look and feel modern, fresh, and bespoke (developer-focused & sleek), avoiding a generic "AI vibe coded" appearance. This will be achieved by implementing a custom design system using Tailwind CSS and Shadcn UI (Radix UI primitives), supporting both light and dark modes, and rolling out the changes gradually starting with core components.

## Technical Context

**Language/Version**: TypeScript, React 18  
**Primary Dependencies**: React, Vite, Tailwind CSS, Shadcn UI (Radix UI), Lucide React  
**Storage**: N/A (UI only)  
**Testing**: Playwright (E2E), Vitest (Unit/Component)  
**Target Platform**: Web (Modern Browsers)  
**Project Type**: Web application (Frontend)  
**Performance Goals**: Fast CSS transitions, no layout shift, 60fps animations  
**Constraints**: WCAG AA accessibility, gradual rollout without breaking legacy pages  
**Scale/Scope**: Core UI components and primary pages

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Specification-First**: `spec.md` exists with prioritized user stories and acceptance criteria.
- [x] **Template-Driven**: Using standard `plan.md` template.
- [x] **Test Optionality**: Tests are not explicitly mandated for UI styling changes, but existing E2E tests must pass.
- [x] **Simplicity and DRY**: Using Tailwind and Shadcn UI avoids complex custom CSS architectures and runtime CSS-in-JS overhead.

## Project Structure

### Documentation (this feature)

```text
specs/001-modern-ui-refresh/
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
│   ├── components/
│   │   └── ui/          # New Shadcn UI components
│   ├── pages/           # Pages to be incrementally updated
│   ├── index.css        # Global styles and CSS variables
│   └── App.tsx
├── tailwind.config.js   # New Tailwind configuration
└── package.json
```

**Structure Decision**: Web application (frontend only). We will introduce a `src/components/ui/` directory for the new design system components, keeping them separate from legacy components during the gradual rollout.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
