# Implementation Plan: UI Audit — Page-Level Quality & Consistency

**Branch**: `052-ui-audit` | **Date**: 2026-03-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/052-ui-audit/spec.md`

## Summary

Systematic, page-by-page audit of the Solune frontend application to raise every page to a consistent quality bar across ten dimensions: component architecture, data management, loading/error/empty states, type safety, accessibility, copy & UX polish, styling & layout, performance, test coverage, and code hygiene. The audit is non-destructive — it improves quality and consistency of existing behavior without introducing new features or changing business logic. Each page audit is independently scoped, producing a findings report that drives targeted fixes.

The technical approach applies the audit checklist to each of the 11 top-level route pages (AppsPage, ProjectsPage, AgentsPipelinePage, AgentsPage, AppPage, HelpPage, ChoresPage, SettingsPage, ToolsPage, LoginPage, NotFoundPage) and their related feature components, hooks, and types. Fixes follow a phased order: structural refactoring → state/error handling → accessibility/UX → testing → validation.

## Technical Context

**Language/Version**: TypeScript ~5.9.0, React 19.2.0
**Primary Dependencies**: TanStack Query v5.90.0 (data fetching), React Router v7.13.1 (routing), React Hook Form v7.71.2 (forms), Zod v4.3.6 (validation), Radix UI (accessible primitives), Tailwind CSS v4.2.0 (styling), Lucide React v0.577.0 (icons), clsx + tailwind-merge via `cn()` helper
**Storage**: N/A (frontend only — consumes backend REST API via `src/services/api.ts`)
**Testing**: Vitest v4.0.18 + happy-dom (unit/component), @testing-library/react v16.3.2, Playwright v1.58.2 (E2E), Stryker v9.6.0 (mutation testing)
**Target Platform**: Web (modern browsers), viewport 768px–1920px
**Project Type**: Web application (frontend-only audit — backend changes are out of scope)
**Performance Goals**: Sub-second interactions, smooth scrolling, loading indicator within 200ms of navigation
**Constraints**: No new features or business logic changes, shared primitives used as-is, no mobile viewport below 768px
**Scale/Scope**: 11 pages, ~134 existing test files, ~44 custom hooks, ~18 API namespaces, ~172 exported types

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First Development** | ✅ PASS | `spec.md` complete with 7 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, clear scope boundaries, and out-of-scope declarations. Checklist validates all mandatory sections. |
| **II. Template-Driven Workflow** | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/`. Plan uses `plan-template.md`, spec uses `spec-template.md`. No custom sections added without justification. |
| **III. Agent-Orchestrated Execution** | ✅ PASS | This plan is produced by the `speckit.plan` agent with a single clear purpose. Handoff to `speckit.tasks` is explicit. |
| **IV. Test Optionality with Clarity** | ✅ PASS | Tests are explicitly requested in the spec (User Stories 6 and 7, FR-031 through FR-033). Test tasks will follow implementation tasks per story, consistent with the audit's phased approach (fix first, then lock in with tests). |
| **V. Simplicity and DRY** | ✅ PASS | The audit improves existing code — no new abstractions, no premature generalization. Extractions (hooks, sub-components) follow existing codebase patterns and the YAGNI principle. |
| **Phase-Based Execution** | ✅ PASS | Spec → Plan → Tasks → Implement → Analyze. This plan (Phase 2) builds on the completed spec (Phase 1). |
| **Independent User Stories** | ✅ PASS | Each of the 7 user stories is independently implementable and testable. Page audits are also independent — each page can be audited without dependencies on other page audits. |

**Gate result: ALL PASS — proceed to Phase 0 research.**

## Project Structure

### Documentation (this feature)

```text
specs/052-ui-audit/
├── plan.md              # This file
├── research.md          # Phase 0: Audit methodology research and decisions
├── data-model.md        # Phase 1: Audit entities, page inventory, quality dimensions
├── quickstart.md        # Phase 1: How to execute a page audit
├── checklists/
│   └── requirements.md  # Specification quality checklist (already exists)
├── contracts/
│   ├── audit-checklist.md       # Standardized 10-dimension checklist contract
│   └── findings-report.md       # Per-page findings report template/schema
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/frontend/
├── src/
│   ├── pages/                    # 11 top-level route pages (audit targets)
│   │   ├── AgentsPipelinePage.tsx # 417 lines — EXCEEDS 250-line limit
│   │   ├── AppsPage.tsx          # 707 lines — EXCEEDS 250-line limit
│   │   ├── ProjectsPage.tsx      # 629 lines — EXCEEDS 250-line limit
│   │   ├── AgentsPage.tsx        # 230 lines
│   │   ├── AppPage.tsx           # 141 lines
│   │   ├── HelpPage.tsx          # 195 lines
│   │   ├── ChoresPage.tsx        # 166 lines
│   │   ├── SettingsPage.tsx      # 107 lines
│   │   ├── ToolsPage.tsx         # 87 lines
│   │   ├── LoginPage.tsx         # 119 lines
│   │   └── NotFoundPage.tsx      # 29 lines
│   ├── components/
│   │   ├── agents/               # Agent feature components
│   │   ├── apps/                 # Apps feature components
│   │   ├── auth/                 # Auth components
│   │   ├── board/                # Board components
│   │   ├── chat/                 # Chat components
│   │   ├── chores/               # Chore components
│   │   ├── common/               # Shared: CelestialLoader, ErrorBoundary, etc.
│   │   ├── help/                 # Help components
│   │   ├── onboarding/           # Onboarding components
│   │   ├── pipeline/             # Pipeline builder components
│   │   ├── settings/             # Settings components
│   │   ├── tools/                # Tools components
│   │   └── ui/                   # Design system: Button, Card, Input, Tooltip, etc.
│   ├── hooks/                    # 44 custom hooks (co-located tests)
│   ├── services/
│   │   └── api.ts                # 1199 lines — 18 API namespaces
│   ├── types/
│   │   ├── index.ts              # 1295 lines — ~172 exported types
│   │   └── apps.ts               # 74 lines — App-specific types
│   ├── lib/
│   │   └── utils.ts              # cn() helper
│   └── test/
│       ├── setup.ts              # Vitest global setup
│       ├── test-utils.tsx         # renderWithProviders, createTestQueryClient
│       └── factories/            # Test data factories
├── e2e/                          # Playwright E2E tests
├── eslint.config.js              # ESLint 9 flat config (react-hooks, jsx-a11y, security)
├── vitest.config.ts              # Vitest config (happy-dom, coverage thresholds)
└── playwright.config.ts          # Playwright config
```

**Structure Decision**: This feature targets the existing `solune/frontend/` web application. No new directories are created in the source tree — the audit modifies existing files (pages, components, hooks) and adds test files alongside them. The only new files are in `specs/052-ui-audit/` (planning artifacts). The project follows the established web application structure with `src/pages/` for route views, `src/components/[feature]/` for feature components, `src/hooks/` for custom hooks, and `src/services/` for API calls.

## Complexity Tracking

> No constitution violations detected. No complexity justifications required.
