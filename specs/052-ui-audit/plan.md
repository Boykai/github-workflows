# Implementation Plan: UI Audit

**Branch**: `052-ui-audit` | **Date**: 2026-03-18 | **Spec**: [`specs/052-ui-audit/spec.md`](spec.md)
**Input**: Feature specification from `specs/052-ui-audit/spec.md`

## Summary

Comprehensive audit of every user-facing page in the Solune frontend against ten quality dimensions: component architecture, data fetching, state handling (loading/error/empty), type safety, accessibility, text/UX polish, styling/layout, performance, test coverage, and code hygiene. Each of the 11 pages is evaluated against a standardized checklist, findings are documented, and defects are remediated — resulting in a uniformly high-quality user experience. The audit is frontend-only, modifying existing code rather than introducing new features.

## Technical Context

**Language/Version**: TypeScript ~5.9.0, React 19.2.0
**Primary Dependencies**: TanStack React Query ^5.91.0, React Router DOM ^7.13.1, React Hook Form ^7.71.2, Radix UI (primitives), Tailwind CSS ^4.2.0, Zod ^4.3.6, Vite ^8.0.0
**Storage**: N/A (frontend-only; backend uses SQLite via aiosqlite — not modified by this feature)
**Testing**: Vitest ^4.0.18 + React Testing Library (unit/component), Playwright ^1.58.2 (E2E), @axe-core/playwright (a11y), jest-axe (a11y unit), Stryker (mutation)
**Target Platform**: Modern browsers (Chrome, Firefox, Safari, Edge); viewport 320px–1920px
**Project Type**: Web application (frontend only — `solune/frontend/`)
**Performance Goals**: Interactions feel instant, lists render smoothly (≥30 fps drag), no unnecessary re-renders
**Constraints**: No new features — audit and remediate only; no new external dependencies; maintain all existing test coverage; ESLint 0 warnings, TypeScript 0 errors
**Scale/Scope**: 11 pages, 13 component directories, 42 custom hooks, 7 UI primitives, 6 common components, 139 existing test files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development — ✅ PASS

The feature specification (`specs/052-ui-audit/spec.md`) contains 8 prioritized user stories (P1–P3) with independent testing criteria and Given-When-Then acceptance scenarios. Scope boundaries are explicit: audit and remediate only, no new features. Out-of-scope items are clear.

### II. Template-Driven Workflow — ✅ PASS

All artifacts follow canonical templates from `.specify/templates/`. This plan follows `plan-template.md`. Research, data model, contracts, and quickstart documents are generated per the template structure.

### III. Agent-Orchestrated Execution — ✅ PASS

This plan is produced by the `speckit.plan` agent with clear inputs (spec.md) and outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md). Handoff to `speckit.tasks` for task generation is explicit.

### IV. Test Optionality with Clarity — ✅ PASS

Tests are explicitly requested in the spec (US-8, FR-048 through FR-051). Test tasks are scoped to verifying audit findings: hooks must have tests for happy path, error, loading, and empty states; interactive components must have interaction tests. Snapshot tests are explicitly prohibited (FR-051). Tests follow the project's existing Vitest + React Testing Library conventions.

### V. Simplicity and DRY — ✅ PASS

The plan favors reusing existing shared components (`CelestialLoader`, `ErrorBoundary`, `ProjectSelectionEmptyState`, `ConfirmationDialog`, `Tooltip`) over creating new abstractions. Audit remediation modifies existing files rather than introducing new patterns. Hook extraction follows the existing `src/hooks/use[Feature].ts` convention already established in the codebase.

### Post-Design Re-evaluation — ✅ PASS

After Phase 1 design, all principles remain satisfied. The data model introduces only audit-tracking entities (Audit Checklist, Audit Finding) that formalize the evaluation process. No new runtime abstractions or dependencies are added. All changes modify existing files and patterns.

## Project Structure

### Documentation (this feature)

```text
specs/052-ui-audit/
├── plan.md              # This file (speckit.plan output)
├── research.md          # Phase 0 output (speckit.plan)
├── data-model.md        # Phase 1 output (speckit.plan)
├── quickstart.md        # Phase 1 output (speckit.plan)
├── contracts/           # Phase 1 output (speckit.plan)
│   ├── audit-checklist.md    # Per-page audit evaluation contract
│   └── remediation-policy.md # Standards for fixing audit findings
├── checklists/
│   └── requirements.md # Spec quality checklist (already exists)
└── tasks.md             # Phase 2 output (speckit.tasks — NOT created by speckit.plan)
```

### Source Code (repository root)

```text
solune/frontend/
├── src/
│   ├── pages/                    # 11 page files — primary audit targets
│   │   ├── AgentsPage.tsx        # 230 lines
│   │   ├── AgentsPipelinePage.tsx # 417 lines (exceeds 250-line threshold)
│   │   ├── AppPage.tsx           # 141 lines
│   │   ├── AppsPage.tsx          # 709 lines (exceeds 250-line threshold)
│   │   ├── ChoresPage.tsx        # 166 lines
│   │   ├── HelpPage.tsx          # 195 lines
│   │   ├── LoginPage.tsx         # 119 lines
│   │   ├── NotFoundPage.tsx      # 29 lines
│   │   ├── ProjectsPage.tsx      # 631 lines (exceeds 250-line threshold)
│   │   ├── SettingsPage.tsx      # 107 lines
│   │   └── ToolsPage.tsx         # 87 lines
│   ├── components/
│   │   ├── agents/               # Agent feature components
│   │   ├── apps/                 # App feature components
│   │   ├── auth/                 # Authentication components
│   │   ├── board/                # Board/kanban components
│   │   ├── chat/                 # Chat interface components
│   │   ├── chores/               # Chores feature components
│   │   ├── common/               # Shared: CelestialLoader, ErrorBoundary, etc.
│   │   ├── help/                 # Help feature components
│   │   ├── onboarding/           # Onboarding flow components
│   │   ├── pipeline/             # Pipeline workflow components
│   │   ├── settings/             # Settings feature components
│   │   ├── tools/                # Tools feature components
│   │   └── ui/                   # Primitives: Button, Card, Input, Tooltip, etc.
│   ├── hooks/                    # 42 custom hooks
│   ├── services/
│   │   └── api.ts                # 1,199 lines — 18 API module exports
│   ├── types/
│   │   ├── index.ts              # Main type definitions
│   │   └── apps.ts               # App-specific types
│   └── lib/
│       └── utils.ts              # cn() helper (clsx + tailwind-merge)
└── eslint.config.js              # ESLint flat config with jsx-a11y, security plugins
```

**Structure Decision**: Web application (frontend-only). All audit work targets existing files under `solune/frontend/src/`. No new directories are created. Sub-components extracted during remediation go into the existing `src/components/[feature]/` directories. Hooks extracted go into the existing `src/hooks/` directory.

## Complexity Tracking

> No constitution violations detected. No complexity justifications needed.
