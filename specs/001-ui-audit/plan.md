# Implementation Plan: UI Audit

**Branch**: `001-ui-audit` | **Date**: 2026-03-27 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-ui-audit/spec.md`

## Summary

Comprehensive audit of all 12 application pages to ensure modern best practices, modular design, accurate text/copy, and zero bugs. The audit covers component architecture, data-fetching patterns, loading/error/empty states, type safety, accessibility, UX polish, styling, performance, test coverage, and code hygiene. Each page is audited independently against a 10-category checklist, findings are remediated, and the page is validated via lint, type-check, tests, and manual review.

## Technical Context

**Language/Version**: TypeScript ~5.9, React ^19.2.0
**Primary Dependencies**: @tanstack/react-query ^5.91.0, Tailwind CSS ^4.2.0, Radix UI primitives, clsx, tailwind-merge
**Storage**: N/A (frontend-only audit; backend API consumed via React Query)
**Testing**: Vitest ^4.0.18, @testing-library/react, @testing-library/user-event
**Target Platform**: Web (viewport 768px–1920px, light and dark themes)
**Project Type**: Web application (frontend only — `solune/frontend/`)
**Performance Goals**: No unnecessary re-renders, memoized expensive computations, virtualized lists >50 items
**Constraints**: Zero linter warnings, zero type errors, WCAG AA compliance (4.5:1 contrast)
**Scale/Scope**: 12 pages, ~54 custom hooks, ~16 feature component directories

## Project Structure

### Documentation (this feature)

```text
specs/001-ui-audit/
├── spec.md              # Feature specification (7 user stories, 45 FRs)
├── plan.md              # This file
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Implementation tasks (/speckit.tasks output)
```

### Source Code (repository root)

```text
solune/frontend/
├── src/
│   ├── pages/                    # 12 page files (audit targets)
│   │   ├── ProjectsPage.tsx      # 503 lines — OVER LIMIT
│   │   ├── AppsPage.tsx          # 325 lines — OVER LIMIT
│   │   ├── AgentsPipelinePage.tsx # 313 lines — OVER LIMIT
│   │   ├── ActivityPage.tsx      # 251 lines — OVER LIMIT (borderline)
│   │   ├── AgentsPage.tsx        # 238 lines
│   │   ├── HelpPage.tsx          # 221 lines
│   │   ├── ChoresPage.tsx        # 181 lines
│   │   ├── AppPage.tsx           # 141 lines
│   │   ├── LoginPage.tsx         # 119 lines
│   │   ├── SettingsPage.tsx      # 107 lines
│   │   ├── ToolsPage.tsx         # 104 lines
│   │   └── NotFoundPage.tsx      # 29 lines
│   ├── components/
│   │   ├── ui/                   # Shared UI primitives (Button, Card, Input, Tooltip, etc.)
│   │   ├── common/               # Shared common (CelestialLoader, ErrorBoundary, EmptyState, etc.)
│   │   ├── activity/             # Activity feature components
│   │   ├── agents/               # Agents feature components
│   │   ├── apps/                 # Apps feature components
│   │   ├── auth/                 # Auth feature components
│   │   ├── board/                # Board feature components
│   │   ├── chat/                 # Chat feature components
│   │   ├── chores/               # Chores feature components
│   │   ├── command-palette/      # Command palette components
│   │   ├── help/                 # Help feature components
│   │   ├── onboarding/           # Onboarding components
│   │   ├── pipeline/             # Pipeline feature components
│   │   ├── settings/             # Settings feature components
│   │   └── tools/                # Tools feature components
│   ├── hooks/                    # 54 custom hooks (each with .test.ts)
│   ├── services/
│   │   ├── api.ts                # Main API service
│   │   └── schemas/              # Zod validation schemas
│   ├── types/
│   │   ├── index.ts              # Main type exports
│   │   └── apps.ts               # App-specific types
│   └── lib/
│       └── utils.ts              # cn() helper (clsx + tailwind-merge)
```

**Structure Decision**: Frontend-only audit. All work happens within `solune/frontend/src/`. Pages are the primary audit targets; components, hooks, services, and types are audited in the context of the page that uses them.

### Pages to Audit (Inventory)

| # | Page | File | Lines | Data Fetching | Feature Components |
|---|------|------|-------|---------------|--------------------|
| 1 | ProjectsPage | `src/pages/ProjectsPage.tsx` | 503 | Yes | `src/components/board/` |
| 2 | AppsPage | `src/pages/AppsPage.tsx` | 325 | Yes | `src/components/apps/` |
| 3 | AgentsPipelinePage | `src/pages/AgentsPipelinePage.tsx` | 313 | Yes | `src/components/pipeline/` |
| 4 | ActivityPage | `src/pages/ActivityPage.tsx` | 251 | Yes | `src/components/activity/` |
| 5 | AgentsPage | `src/pages/AgentsPage.tsx` | 238 | Yes | `src/components/agents/` |
| 6 | HelpPage | `src/pages/HelpPage.tsx` | 221 | No | `src/components/help/` |
| 7 | ChoresPage | `src/pages/ChoresPage.tsx` | 181 | Yes | `src/components/chores/` |
| 8 | AppPage | `src/pages/AppPage.tsx` | 141 | Yes | `src/components/apps/` |
| 9 | LoginPage | `src/pages/LoginPage.tsx` | 119 | Minimal | `src/components/auth/` |
| 10 | SettingsPage | `src/pages/SettingsPage.tsx` | 107 | Yes | `src/components/settings/` |
| 11 | ToolsPage | `src/pages/ToolsPage.tsx` | 104 | Yes | `src/components/tools/` |
| 12 | NotFoundPage | `src/pages/NotFoundPage.tsx` | 29 | No | None |

### Audit Categories (from parent issue checklist)

1. Component Architecture & Modularity (FR-001–FR-006)
2. Data Fetching & State Management (FR-007–FR-009)
3. Loading, Error & Empty States (FR-010–FR-015)
4. Type Safety (FR-016–FR-017)
5. Accessibility (FR-018–FR-024)
6. Text, Copy & UX Polish (FR-025–FR-032)
7. Styling & Layout (FR-033–FR-036)
8. Performance (FR-037–FR-039)
9. Test Coverage (FR-040–FR-042)
10. Code Hygiene (FR-043–FR-045)
