# Contract: Audit Findings Schema

**Feature**: `043-projects-page-audit` | **Date**: 2026-03-16 | **Data Model**: [data-model.md](../data-model.md)

## Overview

This contract defines the schema for documenting audit findings during Phase 1 (Discovery & Assessment). Each checklist category is scored, and individual items receive Pass/Fail/N/A ratings with evidence and remediation notes.

## Findings Table Schema

### Category Summary

Each audit category produces a summary row:

| Field | Type | Description |
|-------|------|-------------|
| `category` | `string` | Category name (e.g., "Component Architecture & Modularity") |
| `category_number` | `number` | Category number (1–10) |
| `pass_count` | `number` | Number of items that passed |
| `fail_count` | `number` | Number of items that failed |
| `na_count` | `number` | Number of items not applicable |
| `total_count` | `number` | Total items in category |
| `score_pct` | `number` | Pass percentage excluding N/A: `pass / (pass + fail) * 100` |

### Item Finding

Each individual checklist item produces a finding:

| Field | Type | Description |
|-------|------|-------------|
| `category_number` | `number` | Parent category (1–10) |
| `item_name` | `string` | Item name (e.g., "Single Responsibility") |
| `status` | `'PASS' \| 'FAIL' \| 'N/A'` | Assessment result |
| `evidence` | `string` | Factual observation supporting the status |
| `remediation` | `string \| null` | Required fix description (null if PASS or N/A) |
| `priority` | `'P1' \| 'P2' \| 'P3' \| null` | Implementation priority (null if PASS or N/A) |
| `phase` | `number \| null` | Implementation phase where this is addressed (null if PASS or N/A) |

## Expected Findings Format

The findings should be documented as a markdown table in the implementation task output:

```markdown
## Audit Findings: Projects Page

### Summary

| # | Category | Pass | Fail | N/A | Score |
|---|----------|------|------|-----|-------|
| 1 | Component Architecture | X/7 | Y/7 | Z/7 | NN% |
| 2 | Data Fetching | X/6 | Y/6 | Z/6 | NN% |
| ... | ... | ... | ... | ... | ... |
| 10 | Code Hygiene | X/6 | Y/6 | Z/6 | NN% |
| | **Total** | **XX** | **YY** | **ZZ** | **NN%** |

### Detailed Findings

| # | Item | Status | Evidence | Remediation | Priority | Phase |
|---|------|--------|----------|-------------|----------|-------|
| 1.1 | Single Responsibility | FAIL | Page is 630 lines (limit: 250) | Extract sub-components | P1 | 2 |
| 1.2 | Feature folder structure | PASS | Components in src/components/board/ | — | — | — |
| ... | ... | ... | ... | ... | ... | ... |
```

## Scoring Rules

1. **PASS**: The item fully meets the checklist requirement as stated. Evidence must cite specific file/line or observation.
2. **FAIL**: The item does not meet the requirement. Evidence must describe the gap. Remediation must describe the fix.
3. **N/A**: The item is not applicable to this page (e.g., "Large lists virtualized" when no list exceeds 50 items).
4. **Score calculation**: `(PASS count) / (PASS count + FAIL count) × 100`. N/A items are excluded from the denominator.

## Pre-Audit Known Findings

Based on research phase analysis, these findings are expected:

| Item | Expected Status | Evidence |
|------|----------------|----------|
| 1.1 Single Responsibility | FAIL | `ProjectsPage.tsx` is 630 lines (limit: 250) |
| 1.6 Hook extraction | PASS | 4 dedicated hooks already exist |
| 2.1 React Query for API calls | PASS | All hooks use `useQuery`/`useMutation` |
| 2.4 staleTime configured | PASS | Uses `STALE_TIME_PROJECTS` and `STALE_TIME_SHORT` constants |
| 3.1 Loading state | PASS | Uses `<CelestialLoader size="md" />` |
| 3.5 Error boundary | PASS | `App.tsx` wraps all routes in `<ErrorBoundary>` |
| 4.1 No any types | PASS | No `any` types found in page or hooks |
| 7.1 Tailwind only | FAIL | 2 inline `style={}` attributes found (lines 536, 552) |
| 10.2 No console.log | PASS | No `console.log` found in page or hooks |
| 10.3 Imports use @/ alias | PASS | All imports use `@/` alias |

## Remediation Priority Mapping

| Priority | Description | Implementation Phase |
|----------|-------------|---------------------|
| P1 | Core functionality — must fix | Phase 2 (Structural) or Phase 3 (States) |
| P2 | Accessibility/UX — should fix | Phase 4 (a11y & UX) |
| P3 | Polish/hygiene — nice to fix | Phase 5 (Styling/Performance) or Phase 6 (Testing) |
