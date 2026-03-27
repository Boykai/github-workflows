# Implementation Plan: UI Audit

**Branch**: `001-ui-audit` | **Date**: 2026-03-27 | **Spec**: [specs/001-ui-audit/spec.md](spec.md)
**Input**: Feature specification from `/specs/001-ui-audit/spec.md`

## Summary

Comprehensive audit of all 12 application pages in the Solune frontend to ensure modern best practices, modular design, accurate text/copy, and zero bugs. The audit covers component architecture and modularity, data fetching patterns, loading/error/empty states, type safety, accessibility (a11y), UX polish, styling consistency, performance, test coverage, and code hygiene. Each page is audited independently against a standardized checklist (45 functional requirements, 12 success criteria) and all "must fix" findings are remediated. The technical approach applies the existing React 19 + TypeScript + TanStack Query + Tailwind CSS stack with no new dependencies.

## Technical Context

**Language/Version**: TypeScript ~5.9, React 19.2.0, Node.js 20+
**Primary Dependencies**: React Router DOM 7.13.1, TanStack React Query 5.91.0, Tailwind CSS 4.2.0, Radix UI (popover, hover-card, tooltip, slot), Lucide React 0.577.0, React Hook Form 7.71.2, Zod 4.3.6, @dnd-kit (core, modifiers, sortable, utilities), Sonner 2.0.7 (toasts), clsx 2.1.1, tailwind-merge 3.5.0, class-variance-authority 0.7.1
**Storage**: N/A (frontend-only audit; API calls go to FastAPI backend via `/api` proxy)
**Testing**: Vitest (unit/integration), Playwright (e2e), Stryker (mutation testing), eslint-plugin-jsx-a11y (accessibility linting)
**Target Platform**: Web browser (viewport 768px–1920px), light and dark themes
**Project Type**: Web application (frontend audit scope only; backend is out of scope)
**Performance Goals**: No blank screens during data fetch (loading indicator within 100ms of navigation); no unnecessary re-renders; heavy computations memoized; lists >50 items virtualized or paginated
**Constraints**: Zero linter warnings, zero type-check errors, zero `any` types, all tests passing, WCAG AA color contrast (4.5:1), keyboard-only navigable
**Scale/Scope**: 12 pages (ProjectsPage, AgentsPipelinePage, AppsPage, ActivityPage, AgentsPage, HelpPage, ChoresPage, AppPage, LoginPage, SettingsPage, ToolsPage, NotFoundPage), ~2,500 lines of page code, 70+ custom hooks, 15+ component directories

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I — Specification-First Development ✅ PASS

The feature spec (`specs/001-ui-audit/spec.md`) is complete with 7 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios for each story, clear scope boundaries, and documented edge cases. The checklist (`checklists/requirements.md`) confirms all mandatory sections are complete with no NEEDS CLARIFICATION markers.

### Principle II — Template-Driven Workflow ✅ PASS

This plan follows the canonical `plan-template.md` from `.specify/templates/`. All artifacts (plan.md, research.md, data-model.md, quickstart.md, contracts/) follow the prescribed structure. No custom sections are added without justification.

### Principle III — Agent-Orchestrated Execution ✅ PASS

This is a `speckit.plan` agent task with a single clear purpose: generate the implementation plan and Phase 0–1 artifacts. It operates on the spec.md input and produces plan.md, research.md, data-model.md, quickstart.md, and contracts/ as outputs. Handoff to `speckit.tasks` is explicit (tasks.md is NOT created by this phase).

### Principle IV — Test Optionality with Clarity ✅ PASS

The feature spec explicitly requires test coverage (User Story 6, FR-040 through FR-042). Tests are mandated by the spec, not added speculatively. The audit will verify existing test coverage and add tests only where the spec identifies gaps (hook tests, component interaction tests, edge-case tests).

### Principle V — Simplicity and DRY ✅ PASS

The audit applies existing patterns and shared components (CelestialLoader, ErrorBoundary, ProjectSelectionEmptyState, ThemedAgentIcon, ConfirmationDialog). No new abstractions are introduced. Remediation reuses existing hooks, UI primitives, and conventions. No complexity tracking violations identified.

### Gate Result: **ALL GATES PASS** — Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-ui-audit/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── audit-checklist-schema.yaml
├── checklists/
│   └── requirements.md  # Pre-existing spec quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/frontend/
├── src/
│   ├── pages/                    # 12 page files — primary audit targets
│   │   ├── ProjectsPage.tsx      # 503 lines — OVER LIMIT, needs decomposition
│   │   ├── AppsPage.tsx          # 325 lines — OVER LIMIT, needs decomposition
│   │   ├── AgentsPipelinePage.tsx # 313 lines — OVER LIMIT, needs decomposition
│   │   ├── ActivityPage.tsx      # 251 lines — BORDERLINE, needs review
│   │   ├── AgentsPage.tsx        # 238 lines — within limit
│   │   ├── HelpPage.tsx          # 221 lines — within limit
│   │   ├── ChoresPage.tsx        # 181 lines — within limit
│   │   ├── AppPage.tsx           # 141 lines — within limit
│   │   ├── LoginPage.tsx         # 119 lines — within limit
│   │   ├── SettingsPage.tsx      # 107 lines — within limit
│   │   ├── ToolsPage.tsx         # 104 lines — within limit
│   │   └── NotFoundPage.tsx      # 29 lines  — within limit
│   ├── components/
│   │   ├── ui/                   # Shared primitives (Button, Card, Input, Tooltip, etc.)
│   │   ├── common/               # Shared components (CelestialLoader, ErrorBoundary, etc.)
│   │   ├── activity/             # ActivityPage feature components
│   │   ├── agents/               # AgentsPage feature components
│   │   ├── apps/                 # AppsPage feature components
│   │   ├── board/                # ProjectsPage board components
│   │   ├── chat/                 # Chat popup components
│   │   ├── chores/               # ChoresPage feature components
│   │   ├── command-palette/      # Command palette components
│   │   ├── help/                 # HelpPage feature components
│   │   ├── onboarding/           # Onboarding flow components
│   │   ├── pipeline/             # Pipeline configuration components
│   │   ├── settings/             # SettingsPage feature components
│   │   └── tools/                # ToolsPage feature components
│   ├── hooks/                    # 70+ custom hooks with colocated tests
│   ├── services/
│   │   ├── api.ts                # API client (React Query wrappers)
│   │   └── schemas/              # Zod validation schemas
│   ├── types/                    # TypeScript type definitions
│   │   ├── index.ts              # Core types
│   │   └── apps.ts               # App-specific types
│   ├── constants/                # Shared constants
│   ├── context/                  # React contexts (RateLimitContext, UndoRedoContext)
│   ├── layout/                   # AppLayout, AuthGate, Sidebar, TopBar
│   ├── lib/                      # Utilities (cn(), icons, commands)
│   ├── utils/                    # Helper functions (formatTime, rateLimit, etc.)
│   └── test/                     # Test setup, factories, utilities
└── package.json                  # Scripts: lint, type-check, test, build
```

**Structure Decision**: Web application structure (Option 2). The audit scope is frontend-only within `solune/frontend/`. The 12 page files in `src/pages/` are the primary audit targets. Feature components live in `src/components/[feature]/`, hooks in `src/hooks/`, and tests are colocated with their implementation files.

## Post-Phase 1 Constitution Re-Check

*Re-evaluation after Phase 1 design artifacts are complete.*

### Principle I — Specification-First Development ✅ PASS (unchanged)

All design artifacts (research.md, data-model.md, contracts/, quickstart.md) trace directly to the 7 user stories and 45 functional requirements in spec.md. No scope expansion occurred during planning.

### Principle II — Template-Driven Workflow ✅ PASS (unchanged)

All artifacts follow canonical template structure. plan.md follows plan-template.md. research.md uses the Decision/Rationale/Alternatives format. data-model.md documents entities, relationships, and validation rules. contracts/ uses OpenAPI 3.0.3 schema format.

### Principle III — Agent-Orchestrated Execution ✅ PASS (unchanged)

This agent (`speckit.plan`) has produced its designated outputs. Handoff to `speckit.tasks` is clear — tasks.md is explicitly excluded from this phase.

### Principle IV — Test Optionality with Clarity ✅ PASS (unchanged)

Test requirements remain spec-mandated. Research identified one test gap (missing ActivityPage.test.tsx). This is documented for the tasks phase.

### Principle V — Simplicity and DRY ✅ PASS (unchanged)

No new abstractions introduced. All remediation patterns use existing codebase components and conventions. No complexity tracking entries needed.

### Post-Design Gate Result: **ALL GATES PASS** — Ready for Phase 2 (tasks generation via `/speckit.tasks`).

## Complexity Tracking

> No Constitution Check violations identified. No complexity justifications needed.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *None* | — | — |
