# Implementation Plan: Frontend Theme Audit — Light/Dark Mode Contrast & Style Consistency

**Branch**: `037-theme-contrast-audit` | **Date**: 2026-03-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/037-theme-contrast-audit/spec.md`

## Summary

Perform a comprehensive audit of the entire frontend codebase to ensure that the Celestial design system's Light and Dark theme tokens are consistently applied across all components, pages, and UI elements. The audit will eliminate hardcoded color values, verify WCAG 2.1 AA contrast compliance (≥4.5:1 for normal text, ≥3:1 for large text and UI boundaries), correct interactive-state styling in both themes, and ensure seamless theme-switching without visual glitches. The approach combines automated scanning (codebase-wide grep for hardcoded colors, programmatic WCAG contrast ratio verification) with systematic manual review of all component variants, third-party integrations, and edge cases (overlays, SVGs, scrollbars, skeleton loaders).

## Technical Context

**Language/Version**: TypeScript 5.x, React 19.2.0, Node.js  
**Primary Dependencies**: Tailwind CSS v4.2.0 (with `@tailwindcss/vite`), Radix UI (tooltip, slot), Class Variance Authority (CVA), clsx, tailwind-merge, lucide-react icons  
**Storage**: N/A (frontend-only audit; no persistence changes)  
**Testing**: Vitest v4.0.18, @testing-library/react v16.3.2, jest-axe v10.0.0, happy-dom, Playwright v1.58.2 (e2e)  
**Target Platform**: Web browser (Vite dev server, SPA)  
**Project Type**: Web application (frontend + backend monorepo)  
**Performance Goals**: Theme toggle completes within one animation frame (600ms configured transition); no layout shifts or FOUC  
**Constraints**: All color values must reference Celestial design-system tokens (CSS custom properties); no hardcoded hex/rgb/rgba/hsl values in component files; WCAG 2.1 AA minimum compliance  
**Scale/Scope**: ~146 component files, 11 page files, 9 layout files, 28 solar-* utility classes, ~50 CSS custom property tokens (Light + Dark)

### Theming Architecture

- **ThemeProvider** (`frontend/src/components/ThemeProvider.tsx`): React Context provider supporting `'light'`, `'dark'`, `'system'` modes. Toggles `.light`/`.dark` class on `<html>` element. Persists to `localStorage` key `'vite-ui-theme'`. Smooth 600ms transition via `theme-transitioning` class.
- **CSS Custom Properties**: Defined in `frontend/src/index.css` `:root` (Light) and `.dark` (Dark) selectors using HSL format (e.g., `--background: 41 82% 95%`).
- **Tailwind @theme Block**: Maps CSS custom properties to Tailwind color utilities (e.g., `--color-background: hsl(var(--background))`).
- **Celestial Utility Classes**: 28 `solar-*` classes (chips, actions, halos, text) with explicit `.dark` overrides for semantic colors (success, warning, danger, violet).
- **Theme Toggle**: Located in `frontend/src/layout/Sidebar.tsx`, renders Sun/Moon icon button.

### Known Patterns Requiring Audit

- Solar-* utility classes use hardcoded `rgb()` values (e.g., `rgb(16 185 129)` for success) with `.dark` overrides — need verification that all have proper dark-mode counterparts.
- `@theme` block shadow definitions use `rgba()` (e.g., `rgba(41, 29, 12, 0.08)`) — need to verify these adapt appropriately in dark mode.
- SVG/icon components in `frontend/src/components/common/agentIcons.tsx` use `hsl(var(...))` and `rgb()` values — need theme context verification.
- Third-party Radix UI components — need verification they inherit Celestial theme tokens.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First Development** | ✅ PASS | `spec.md` complete with 6 prioritized user stories (P1–P3), Given-When-Then scenarios, edge cases, and success criteria. Requirements checklist fully validated. |
| **II. Template-Driven Workflow** | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/`. Plan generated from `plan-template.md`. |
| **III. Agent-Orchestrated Execution** | ✅ PASS | `speckit.plan` agent has single purpose (generate plan + research + design artifacts). Inputs: `spec.md`. Outputs: `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`. |
| **IV. Test Optionality with Clarity** | ✅ PASS | Tests are not explicitly mandated in the spec for this audit feature. Existing `jest-axe` accessibility testing infrastructure will be leveraged but no new test framework required. Automated contrast-checking scripts are audit tooling, not product tests. |
| **V. Simplicity and DRY** | ✅ PASS | Audit modifies existing token/style definitions rather than adding new abstractions. No new patterns, libraries, or architectural layers introduced. Changes are corrections to existing CSS and component files. |

**Gate Result**: ✅ All principles pass. Proceed to Phase 0.

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | Design artifacts (data-model, contracts) derived directly from spec requirements FR-001 through FR-012. |
| **II. Template-Driven** | ✅ PASS | All Phase 1 artifacts follow template structure. |
| **III. Agent-Orchestrated** | ✅ PASS | Phase 1 outputs hand off cleanly to `speckit.tasks` for Phase 2. |
| **IV. Test Optionality** | ✅ PASS | Contrast-checking tooling defined as audit scripts, not product test suites. Existing `jest-axe` infrastructure noted for optional regression testing. |
| **V. Simplicity and DRY** | ✅ PASS | Data model captures existing entities (tokens, contrast pairs) — no new abstractions. Contracts define audit procedures, not new APIs. |

**Gate Result**: ✅ All principles pass. Design phase complete.

## Project Structure

### Documentation (this feature)

```text
specs/037-theme-contrast-audit/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── audit-checklist.md
│   └── token-registry.md
├── checklists/
│   └── requirements.md  # Specification quality checklist (pre-existing)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── index.css                    # Theme tokens (:root + .dark), @theme block, solar-* utilities
│   ├── components/
│   │   ├── ThemeProvider.tsx         # Theme context provider (light/dark/system)
│   │   ├── AnimatedBackground.tsx    # Background effects (theme-dependent)
│   │   ├── ui/                      # Base UI components (button, card, input, tooltip, dialog)
│   │   ├── agents/                  # Agent panel, modals, form components
│   │   ├── board/                   # Kanban board, agent tiles, issue cards
│   │   ├── chat/                    # Chat interface, messages, command autocomplete
│   │   ├── common/                  # Shared components (icons, loaders, hero sections)
│   │   ├── pipeline/               # Pipeline visualization components
│   │   ├── settings/               # Settings page components
│   │   ├── tools/                  # Tools management components
│   │   ├── chores/                 # Chores components
│   │   └── auth/                   # Authentication components
│   ├── layout/                      # AppLayout, Sidebar (theme toggle), TopBar, Breadcrumb
│   ├── pages/                       # Page-level components (11 pages)
│   ├── hooks/                       # Custom hooks (useTheme via ThemeProvider)
│   ├── lib/                         # Utilities (cn() for className merging)
│   └── test/                        # Test setup, a11y-helpers.ts
└── package.json
```

**Structure Decision**: This is a frontend-only audit within the existing web application monorepo. All changes target `frontend/src/` — primarily `index.css` (token definitions), component files (hardcoded color removal), and layout files (theme toggle behavior). No backend changes required.

## Complexity Tracking

> No constitution violations detected. No complexity justifications needed.
