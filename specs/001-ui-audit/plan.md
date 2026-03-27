# Implementation Plan: UI Audit

**Branch**: `001-ui-audit` | **Date**: 2026-03-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-ui-audit/spec.md`

## Summary

Comprehensive audit of all 12 application pages to ensure modern best practices, modular design, accurate text/copy, and zero bugs. Each page is evaluated against a standardized checklist covering component architecture, data fetching, loading/error/empty states, type safety, accessibility, UX polish, styling, performance, test coverage, and code hygiene. Remediation is applied per page in priority order.

## Technical Context

**Language/Version**: TypeScript ~5.9, React 19.2, Node.js 20+
**Primary Dependencies**: React, TanStack Query ^5.91, Tailwind CSS, Radix UI primitives, Vitest
**Storage**: N/A (frontend audit — backend API assumed stable)
**Testing**: Vitest with React Testing Library, `renderHook`, `vi.mock`, `waitFor`, `createWrapper()`
**Target Platform**: Web browser (768px–1920px viewports, light + dark themes)
**Project Type**: Web application (frontend only for this audit)
**Performance Goals**: No blank screens during data loading; all interactions respond within 100ms perceived; memoization where measurable
**Constraints**: Zero linter warnings, zero type errors, WCAG AA contrast, keyboard-only navigable
**Scale/Scope**: 12 pages, ~15 feature component directories, ~60 custom hooks

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ Pass | spec.md created with 7 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, scope boundaries |
| II. Template-Driven Workflow | ✅ Pass | All artifacts follow canonical templates |
| III. Agent-Orchestrated Execution | ✅ Pass | Work decomposed into single-responsibility agent phases (specify → plan → tasks → implement) |
| IV. Test Optionality with Clarity | ✅ Pass | Tests explicitly requested in spec (FR-040, FR-041, FR-042, US6); included in task plan |
| V. Simplicity and DRY | ✅ Pass | Audit leverages existing shared components (ui/, common/); no new abstractions introduced |

## Project Structure

### Documentation (this feature)

```text
specs/001-ui-audit/
├── spec.md              # Feature specification
├── plan.md              # This file
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Task decomposition (created by /speckit.tasks)
```

### Source Code (repository root)

```text
solune/frontend/
├── src/
│   ├── pages/                  # 12 page files (audit targets)
│   │   ├── ProjectsPage.tsx
│   │   ├── AgentsPipelinePage.tsx
│   │   ├── AppsPage.tsx
│   │   ├── ActivityPage.tsx
│   │   ├── AgentsPage.tsx
│   │   ├── HelpPage.tsx
│   │   ├── ChoresPage.tsx
│   │   ├── SettingsPage.tsx
│   │   ├── ToolsPage.tsx
│   │   ├── AppPage.tsx
│   │   ├── LoginPage.tsx
│   │   └── NotFoundPage.tsx
│   ├── components/
│   │   ├── ui/                 # Shared primitives (Button, Card, Input, Tooltip, etc.)
│   │   ├── common/             # Shared components (CelestialLoader, ErrorBoundary, etc.)
│   │   ├── activity/           # Feature components
│   │   ├── agents/
│   │   ├── apps/
│   │   ├── auth/
│   │   ├── board/
│   │   ├── chat/
│   │   ├── chores/
│   │   ├── command-palette/
│   │   ├── help/
│   │   ├── onboarding/
│   │   ├── pipeline/
│   │   ├── settings/
│   │   └── tools/
│   ├── hooks/                  # ~60 custom hooks
│   ├── services/
│   │   └── api.ts              # API client
│   ├── types/
│   │   ├── index.ts
│   │   └── apps.ts
│   └── lib/
│       ├── utils.ts            # cn() helper
│       ├── time-utils.ts       # Timestamp formatting
│       └── ...
└── vitest.config.ts
```

**Structure Decision**: Existing web application structure with `solune/frontend/` as the frontend root. Audit targets are the 12 page files and their associated feature component directories, hooks, and types. No structural changes to the project layout are needed.

## Architecture Decisions

### Audit-Per-Page Strategy

Each of the 12 pages is treated as an independent audit unit. The audit checklist (10 categories, ~60 individual items) is applied to each page. Findings are categorized as must-fix, should-fix, or not-applicable. Pages are audited in priority order matching their complexity and user impact.

### Page Priority Order

Based on line count and complexity (descending risk):

1. **ProjectsPage** (503 lines) — Highest risk: exceeds 250-line limit, complex state
2. **AppsPage** (325 lines) — Exceeds limit, multiple data sources
3. **AgentsPipelinePage** (313 lines) — Exceeds limit, complex pipeline editor
4. **ActivityPage** (251 lines) — Borderline limit, feed rendering
5. **AgentsPage** (238 lines) — Within limit but complex interactions
6. **HelpPage** (221 lines) — Within limit, mostly static content
7. **ChoresPage** (181 lines) — Within limit, list management
8. **AppPage** (141 lines) — Within limit, detail view
9. **LoginPage** (119 lines) — Within limit, auth flow
10. **SettingsPage** (107 lines) — Within limit, form management
11. **ToolsPage** (104 lines) — Within limit, list view
12. **NotFoundPage** (29 lines) — Minimal, mostly static

### Remediation Approach

For each page:
1. Discovery: score all checklist items (pass/fail/N/A)
2. Structural fixes: extract oversized pages, extract hooks
3. State handling: add missing loading/error/empty states
4. Accessibility: add ARIA attributes, keyboard navigation, focus management
5. Testing: add missing hook and component tests
6. Hygiene: fix linter warnings, remove dead code, fix imports

## Complexity Tracking

> No constitution violations detected. No complexity justifications needed.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |
