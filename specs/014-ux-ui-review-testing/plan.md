# Implementation Plan: Deep UX/UI Review, Polish & Meaningful Frontend Test Coverage

**Branch**: `014-ux-ui-review-testing` | **Date**: 2026-02-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/014-ux-ui-review-testing/spec.md`

## Summary

Perform a comprehensive UX/UI audit of the customer-facing React frontend — covering visual consistency, accessibility (WCAG AA), interactive states, form validation, UI state handling, and responsive layouts — then add meaningful automated test coverage for critical user flows using Vitest (integration) and Playwright (E2E) with a behavior-driven approach. Integrate automated accessibility auditing into the CI pipeline via axe-core, centralize any remaining hardcoded design tokens, and document all discovered issues in a structured findings log with severity ratings.

## Technical Context

**Language/Version**: TypeScript 5.4 / Node 20 (frontend), Python 3.12 (backend — unchanged)
**Primary Dependencies**: React 18, Vite 5, Tailwind CSS 3.4, Radix UI, TanStack Query v5, dnd-kit, Socket.io-client, class-variance-authority, Lucide React
**Storage**: N/A (frontend-only changes; backend SQLite unchanged)
**Testing**: Vitest 4.0+ / @testing-library/react 16.3+ / happy-dom 20.6+ (unit/integration), Playwright 1.58+ (E2E), axe-core (accessibility auditing — new)
**Target Platform**: Modern browsers (Chrome, Firefox, Safari, Edge)
**Project Type**: web (frontend focus within backend + frontend monorepo)
**Performance Goals**: LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1 (Core Web Vitals "good" thresholds)
**Constraints**: No new UI frameworks; reuse existing Tailwind + Radix + CVA stack; behavior-driven tests using getByRole/getByLabelText over test IDs; snapshot tests used sparingly
**Scale/Scope**: 3 customer-facing views (Home, Project Board, Settings), 33+ components across 6 categories (ui, board, chat, settings, auth, common), 18 hooks, 9 API service namespaces, 9 existing unit tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | spec.md exists with 6 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, and clear scope boundaries |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase follows single-responsibility agent model; outputs are well-defined markdown documents |
| IV. Test Optionality with Clarity | ✅ PASS | Tests are *explicitly requested* in the feature specification (FR-003, FR-010); behavior-driven testing approach defined |
| V. Simplicity and DRY | ✅ PASS | Reuses existing test infrastructure (createMockApi, renderWithProviders, factories); no new frameworks; extends rather than replaces |

**Gate Result**: ✅ ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/014-ux-ui-review-testing/
├── plan.md              # This file
├── research.md          # Phase 0: Research findings
├── data-model.md        # Phase 1: Audit entity model
├── quickstart.md        # Phase 1: Developer quickstart for UX audit workflow
├── contracts/           # Phase 1: Audit conventions and standards
│   └── audit-standards.md
└── tasks.md             # Phase 2 output (created by /speckit.tasks, NOT this phase)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── components/
│   │   ├── ui/              # 3 primitives: button, card, input (CVA + Radix patterns)
│   │   ├── board/           # 11 board components (columns, cards, modals, agent config)
│   │   ├── chat/            # 6 chat components (interface, messages, previews)
│   │   ├── settings/        # 12 settings components (sections, forms, dropdowns)
│   │   ├── auth/            # 2 auth components (LoginButton + test)
│   │   ├── common/          # 2 common components (ErrorBoundary + test)
│   │   └── ThemeProvider.tsx # Theme context (light/dark/system)
│   ├── hooks/               # 18 custom hooks (auth, projects, chat, settings, real-time)
│   ├── pages/               # 2 pages: ProjectBoardPage, SettingsPage
│   ├── services/            # API client (api.ts) with 9 namespaces
│   ├── test/                # Test infrastructure
│   │   ├── setup.ts         # Global mocks + createMockApi()
│   │   ├── test-utils.tsx   # renderWithProviders, createTestQueryClient
│   │   └── factories/       # Test data factories (user, project, task, etc.)
│   ├── lib/                 # Utilities (cn() class merging)
│   ├── App.tsx              # Root component with hash-based routing
│   ├── index.css            # Design tokens (CSS variables for colors, radius)
│   └── constants.ts         # Timing/polling constants (no design tokens)
├── e2e/                     # Playwright E2E tests (to be populated)
├── tailwind.config.js       # Tailwind configuration referencing CSS variables
├── vitest.config.ts         # Vitest configuration (happy-dom)
├── playwright.config.ts     # Playwright configuration (Chromium)
└── eslint.config.js         # ESLint (React Hooks plugin — jsx-a11y to be added)

.github/
└── workflows/
    └── ci.yml               # CI pipeline (frontend lint, type-check, test, build)
```

**Structure Decision**: Web application — the repository uses a `backend/` + `frontend/` split. This feature focuses exclusively on the `frontend/` directory. All UX/UI changes, tests, and audit artifacts target the existing component/hook/page structure. No new directories are created beyond standard test file co-location.

## Complexity Tracking

> No constitution violations to justify. All principles are satisfied.

## Constitution Re-Check (Post Phase 1 Design)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | All design artifacts trace back to spec.md requirements (FR-001 through FR-013) |
| II. Template-Driven Workflow | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow canonical structure |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase produced well-defined outputs for handoff to tasks phase |
| IV. Test Optionality with Clarity | ✅ PASS | Tests are the explicit subject of this feature; behavior-driven approach defined in research.md and contracts |
| V. Simplicity and DRY | ✅ PASS | Design extends existing test infrastructure (factories, mock API, render helpers); axe-core is lightweight and standard; no unnecessary abstractions introduced |

**Post-Design Gate Result**: ✅ ALL PASS — ready for Phase 2 (tasks generation via `/speckit.tasks`).
