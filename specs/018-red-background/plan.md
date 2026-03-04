# Implementation Plan: Add Red Background Color to App

**Branch**: `018-red-background` | **Date**: 2026-03-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/018-red-background/spec.md`

## Summary

Apply a red background color globally to the application by updating the existing CSS custom properties (design tokens) in `frontend/src/index.css`. The `--background` variable will be changed to a material-design red shade (`#D32F2F` / HSL `0 70% 50%`) for light mode and a deep red (`#B71C1C` / HSL `0 73% 41%`) for dark mode. The `--foreground` text color will be updated to white to maintain WCAG 2.1 AA contrast compliance. This approach uses the existing Tailwind CSS + CSS variable theme system with zero structural changes.

## Technical Context

**Language/Version**: TypeScript 5.x, React 18.3.1  
**Primary Dependencies**: Tailwind CSS 3.4.19, Vite 5.4.0, shadcn/ui components  
**Storage**: N/A (CSS-only change)  
**Testing**: Vitest 4.0.18 + React Testing Library 16.3.2, jest-axe for accessibility  
**Target Platform**: Web browser (all modern browsers)  
**Project Type**: Web application (frontend + backend)  
**Performance Goals**: N/A (no runtime performance impact — CSS variable change only)  
**Constraints**: WCAG 2.1 AA minimum contrast ratio 4.5:1 for all text  
**Scale/Scope**: Single file change (`frontend/src/index.css`), affects all views globally via existing CSS variable cascade

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | `spec.md` exists with prioritized user stories (P1, P2, P3), acceptance scenarios, and scope boundaries |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase produces well-defined outputs for subsequent task/implement phases |
| IV. Test Optionality | ✅ PASS | Tests not explicitly mandated in spec; accessibility audit recommended but not required as automated tests |
| V. Simplicity and DRY | ✅ PASS | Single-file CSS variable change; no new abstractions, no new dependencies; uses existing theme system as-is |

**Gate Result**: ✅ ALL PASS — No violations. Proceeding to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/018-red-background/
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
│   ├── index.css              # ← PRIMARY CHANGE: Update --background and --foreground CSS variables
│   ├── components/
│   │   └── ThemeProvider.tsx   # Existing theme system (no changes needed)
│   ├── pages/                 # All pages inherit background via Tailwind's bg-background
│   └── App.tsx                # Root component (no changes needed)
├── tailwind.config.js         # Maps CSS vars to Tailwind classes (no changes needed)
└── tests/                     # Existing test infrastructure
```

**Structure Decision**: Web application structure (Option 2). This feature modifies only `frontend/src/index.css` — the CSS variable definitions that cascade to all components via Tailwind's `bg-background` and `text-foreground` utility classes applied to `<body>` in the same file.

## Complexity Tracking

> No violations — section intentionally left empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
