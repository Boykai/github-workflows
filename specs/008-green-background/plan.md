# Implementation Plan: Add Green Background Color to App

**Branch**: `008-green-background` | **Date**: 2026-02-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-green-background/spec.md`

## Summary

Apply a green background color (#4CAF50) to the application's root container by updating the existing CSS custom property `--color-bg` in `frontend/src/index.css`. The app already uses a centralized CSS custom property theming system with light/dark mode support. The change requires updating the `--color-bg` value in the `:root` selector and the `html.dark-mode-active` selector to use green shades, and ensuring foreground text colors maintain WCAG 2.1 AA contrast ratios against the new background.

## Technical Context

**Language/Version**: TypeScript ~5.4, React 18.3, ES2022 target
**Primary Dependencies**: React 18, Vite 5, @tanstack/react-query 5, CSS custom properties (no CSS framework)
**Storage**: N/A (frontend-only change)
**Testing**: Vitest (unit), Playwright (e2e)
**Target Platform**: Web (Chrome, Firefox, Safari, Edge — latest stable)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Zero CLS from background color application; no FOUC
**Constraints**: WCAG 2.1 AA contrast ratios (4.5:1 normal text, 3:1 large text)
**Scale/Scope**: Single CSS file change; affects all pages via CSS custom property

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ Pass | spec.md complete with prioritized user stories, acceptance scenarios, and scope boundaries |
| II. Template-Driven Workflow | ✅ Pass | All artifacts follow canonical templates |
| III. Agent-Orchestrated Execution | ✅ Pass | Plan phase follows specify → plan → tasks → implement pipeline |
| IV. Test Optionality with Clarity | ✅ Pass | Tests not explicitly mandated in spec; visual verification sufficient for CSS change. Existing tests should not break. |
| V. Simplicity and DRY | ✅ Pass | Single CSS custom property update; no new abstractions; leverages existing theming system |

## Project Structure

### Documentation (this feature)

```text
specs/008-green-background/
├── plan.md              # This file
├── research.md          # Phase 0 output — theming approach research
├── data-model.md        # Phase 1 output — CSS token model
├── quickstart.md        # Phase 1 output — implementation guide
├── contracts/           # Phase 1 output — style contract
│   └── theme-tokens.md  # CSS custom property contract
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── index.css          # Global CSS — contains :root custom properties (PRIMARY CHANGE TARGET)
│   ├── App.css            # App component styles — uses var(--color-bg)
│   ├── App.tsx            # Root component
│   ├── main.tsx           # Entry point
│   ├── hooks/
│   │   └── useAppTheme.ts # Dark/light mode toggle hook
│   └── components/
│       ├── chat/
│       │   └── ChatInterface.css  # Uses var(--color-bg), var(--color-bg-secondary)
│       ├── sidebar/
│       ├── board/
│       ├── settings/
│       └── auth/
└── package.json
```

**Structure Decision**: Web application with frontend/backend separation. This feature only modifies the frontend. The existing CSS custom property system in `frontend/src/index.css` is the centralized theming location. All component CSS files reference `var(--color-bg)` and `var(--color-bg-secondary)`, so changing the root definition propagates automatically.

## Complexity Tracking

> No violations detected. No complexity justifications needed.
