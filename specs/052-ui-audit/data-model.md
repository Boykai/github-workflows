# Data Model: UI Audit — Page-Level Quality & Consistency

**Feature**: 052-ui-audit | **Date**: 2026-03-18

## Overview

The UI Audit is a process-driven feature — it does not introduce new database tables, API endpoints, or persistent data structures. The "data model" for this feature describes the conceptual entities used during the audit process: the pages being audited, the quality dimensions evaluated, and the findings produced.

## Entities

### Page (Audit Target)

The unit of work for each audit iteration. A page is a top-level route view together with its directly related artifacts.

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Page component name (e.g., "AppsPage") |
| `path` | string | Route path (e.g., "/apps") |
| `filePath` | string | Source file path relative to `solune/frontend/` |
| `lineCount` | number | Current line count of the page file |
| `exceedsLimit` | boolean | Whether `lineCount > 250` |
| `featureDir` | string | Related feature component directory (e.g., "src/components/apps/") |
| `hooks` | string[] | Related custom hooks (e.g., ["useApps", "useAppTheme"]) |
| `apiNamespace` | string | Related API namespace from `src/services/api.ts` |
| `typeFiles` | string[] | Related type definition files |
| `testFiles` | string[] | Existing test files for the page and its components |

**Relationships**:
- Page → has many → Quality Dimension evaluations (1:10)
- Page → has one → Findings Report
- Page → belongs to → Feature Component Directory
- Page → uses → Custom Hooks (many-to-many)

### Page Inventory

Complete inventory of all audit targets with current metrics:

| Page | Route | File | Lines | Feature Dir | Key Hooks |
|------|-------|------|-------|-------------|-----------|
| AppsPage | `/apps`, `/apps/:appName` | `src/pages/AppsPage.tsx` | 707 | `src/components/apps/` | useApps |
| ProjectsPage | `/projects` | `src/pages/ProjectsPage.tsx` | 629 | `src/components/board/` | useProjects, useProjectBoard |
| AgentsPipelinePage | `/pipeline` | `src/pages/AgentsPipelinePage.tsx` | 417 | `src/components/pipeline/` | usePipelineConfig, useSelectedPipeline, usePipelineReducer |
| AgentsPage | `/agents` | `src/pages/AgentsPage.tsx` | 230 | `src/components/agents/` | useAgents, useAgentConfig |
| HelpPage | `/help` | `src/pages/HelpPage.tsx` | 195 | `src/components/help/` | — |
| ChoresPage | `/chores` | `src/pages/ChoresPage.tsx` | 166 | `src/components/chores/` | useChores |
| AppPage | `/` | `src/pages/AppPage.tsx` | 141 | `src/components/chat/` | useChat, useChatHistory |
| LoginPage | `/login` | `src/pages/LoginPage.tsx` | 119 | `src/components/auth/` | useAuth |
| SettingsPage | `/settings` | `src/pages/SettingsPage.tsx` | 107 | `src/components/settings/` | useSettings, useSettingsForm |
| ToolsPage | `/tools` | `src/pages/ToolsPage.tsx` | 87 | `src/components/tools/` | useTools |
| NotFoundPage | `*` | `src/pages/NotFoundPage.tsx` | 29 | — | — |

### Quality Dimension

One of the ten audit categories evaluated for each page.

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Dimension identifier (e.g., "component-architecture") |
| `name` | string | Display name (e.g., "Component Architecture & Modularity") |
| `checklistItems` | ChecklistItem[] | Individual pass/fail criteria within this dimension |

**Enumeration** (10 dimensions):

1. `component-architecture` — Component Architecture & Modularity (7 items)
2. `data-fetching` — Data Fetching & State Management (6 items)
3. `loading-error-empty` — Loading, Error & Empty States (5 items)
4. `type-safety` — Type Safety (5 items)
5. `accessibility` — Accessibility (7 items)
6. `copy-ux` — Text, Copy & UX Polish (8 items)
7. `styling-layout` — Styling & Layout (6 items)
8. `performance` — Performance (5 items)
9. `test-coverage` — Test Coverage (5 items)
10. `code-hygiene` — Code Hygiene (6 items)

**Total**: 60 checklist items across 10 dimensions.

### Checklist Item

An individual pass/fail criterion within a quality dimension.

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Item identifier (e.g., "arch-single-responsibility") |
| `dimension` | string | Parent dimension ID |
| `description` | string | What is being checked |
| `requirement` | string | The specific standard to meet |
| `evaluationResult` | enum | `Pass` \| `Fail` \| `N/A` |
| `issues` | string[] | Specific issues found (only when `Fail`) |
| `fixDescription` | string \| null | How to fix (only when `Fail`) |

### Findings Report

The output of a single page audit — a scored evaluation of all checklist items with actionable findings.

| Field | Type | Description |
|-------|------|-------------|
| `pageName` | string | Page being audited |
| `auditDate` | string (ISO 8601) | When the audit was performed |
| `overallScore` | string | Summary: `{passCount}/{totalItems}` items passing |
| `dimensionScores` | DimensionScore[] | Per-dimension pass/fail counts |
| `findings` | Finding[] | All failing items with remediation guidance |
| `validationCommands` | string[] | Commands to verify fixes |

### Dimension Score

Per-dimension summary within a findings report.

| Field | Type | Description |
|-------|------|-------------|
| `dimension` | string | Dimension ID |
| `passed` | number | Count of passing items |
| `failed` | number | Count of failing items |
| `notApplicable` | number | Count of N/A items |
| `total` | number | Total items in this dimension |

### Finding

A single failing checklist item with remediation details.

| Field | Type | Description |
|-------|------|-------------|
| `checklistItemId` | string | Reference to the failing checklist item |
| `severity` | enum | `Critical` \| `Major` \| `Minor` |
| `description` | string | What was found |
| `location` | string | File path and line range |
| `remediation` | string | Specific fix instructions |
| `relatedFR` | string | Related functional requirement (e.g., "FR-004") |

**Severity definitions**:
- **Critical**: User-facing bug or accessibility blocker (blank screen, broken keyboard nav, unguarded destructive action)
- **Major**: Quality gap that degrades UX or maintainability (missing error state, exceeds line limit, any type violations)
- **Minor**: Polish item that improves consistency (spacing, copy inconsistency, missing tooltip)

## State Transitions

### Page Audit Lifecycle

```
Not Audited → Discovery → Scored → Remediation → Validated → Complete
```

| State | Description | Exit Criteria |
|-------|-------------|---------------|
| Not Audited | Page has not been evaluated | Audit begins |
| Discovery | Reading page, components, hooks, running lint/tests | All 60 checklist items scored |
| Scored | Findings report generated with pass/fail/N/A | Findings reviewed and remediation planned |
| Remediation | Fixes applied per phased order (structural → states → a11y → tests) | All critical/major findings addressed |
| Validated | Lint, type-check, and tests pass; visual verification complete | All validation commands succeed |
| Complete | Page meets quality bar | N/A — terminal state |

## Validation Rules

- A page audit is complete when all checklist items score `Pass` or `N/A` (zero `Fail`)
- Critical findings must be fixed before major findings
- Major findings must be fixed before minor findings
- Fixes must not change business logic or introduce new features
- All fixes must pass validation: `eslint` (0 warnings), `tsc --noEmit` (0 errors), `vitest run` (all tests pass)
