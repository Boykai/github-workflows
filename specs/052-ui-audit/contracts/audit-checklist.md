# Contract: Audit Checklist

**Feature**: `052-ui-audit`
**Date**: 2026-03-18

---

## Overview

This contract defines the standardized per-page audit evaluation process. Every page in `src/pages/` is evaluated against the same 10-category checklist with consistent scoring rules.

## Evaluation Process

### Step 1: Discovery

For each page, gather:

```
Page file:           src/pages/[PageName].tsx
Feature components:  src/components/[feature]/
Custom hooks:        src/hooks/use[Feature].ts (and related)
API module:          src/services/api.ts (relevant API group)
Type definitions:    src/types/index.ts or src/types/[feature].ts
Existing tests:      src/pages/[PageName].test.tsx, src/hooks/use[Feature].test.ts
```

### Step 2: Automated Checks

```bash
# Line count check (FR-004: must be ≤250)
wc -l src/pages/[PageName].tsx

# ESLint check (FR-056: must report 0 warnings)
npx eslint src/pages/[PageName].tsx src/components/[feature]/

# Type check (no any types, no type assertions)
npx tsc --noEmit

# Run existing tests
npx vitest run src/pages/[PageName].test.tsx src/hooks/use[Feature].test.ts
```

### Step 3: Manual Evaluation

For each of the 10 categories, evaluate every item as:
- **Pass**: Item fully satisfied
- **Fail**: Item not satisfied — document finding with file, location, and recommended fix
- **N/A**: Item does not apply to this page (e.g., "Data Fetching" items on a static page)

## Scoring Rules

### Category 1: Component Architecture & Modularity

| Item ID | Check | Pass Criteria |
|---------|-------|---------------|
| ARCH-01 | Single Responsibility | Page file ≤250 lines |
| ARCH-02 | Feature folder structure | Sub-components in `src/components/[feature]/` |
| ARCH-03 | No prop drilling >2 levels | No props passed through >2 component layers |
| ARCH-04 | Reusable primitives | Uses `src/components/ui/` components, no reimplementations |
| ARCH-05 | Shared components | Uses `CelestialLoader`, `ErrorBoundary`, etc. where applicable |
| ARCH-06 | Hook extraction | Complex state (>15 lines useState/useEffect/useCallback) in `src/hooks/` |
| ARCH-07 | No business logic in JSX | Computation/transformation in hooks or helpers, not inline |

### Category 2: Data Fetching & State Management

| Item ID | Check | Pass Criteria |
|---------|-------|---------------|
| DATA-01 | React Query for API calls | Uses `useQuery`/`useMutation`, no raw `useEffect` + `fetch` |
| DATA-02 | Query key conventions | Keys follow `[feature].all / .list(id) / .detail(id)` pattern |
| DATA-03 | Optimistic updates | Mutations `invalidateQueries` on success |
| DATA-04 | staleTime configured | Appropriate staleTime for data type (30s lists, 60s settings) |
| DATA-05 | No duplicate API calls | Same data not fetched independently by page and child |
| DATA-06 | Mutation error handling | All `useMutation` have `onError` with user-visible feedback |

### Category 3: Loading, Error & Empty States

| Item ID | Check | Pass Criteria |
|---------|-------|---------------|
| STATE-01 | Loading state | Shows `<CelestialLoader>` or skeleton during load |
| STATE-02 | Error state | User-friendly error message with retry action |
| STATE-03 | Empty state | Meaningful empty state when collection is empty |
| STATE-04 | Partial loading | Independent sections have own loading/error states |
| STATE-05 | Error boundary | Page wrapped in `<ErrorBoundary>` |

### Category 4: Type Safety

| Item ID | Check | Pass Criteria |
|---------|-------|---------------|
| TYPE-01 | No `any` types | All props, state, API responses fully typed |
| TYPE-02 | No type assertions (`as`) | Prefers type guards or discriminated unions |
| TYPE-03 | API types match backend | Types aligned with Pydantic models |
| TYPE-04 | Event handler types explicit | Form events use specific React event types |
| TYPE-05 | Hook return types | Explicit or unambiguously inferrable |

### Category 5: Accessibility (a11y)

| Item ID | Check | Pass Criteria |
|---------|-------|---------------|
| A11Y-01 | Keyboard accessible | All interactive elements reachable via Tab, activated via Enter/Space |
| A11Y-02 | Focus management | Dialogs trap focus, return focus on close |
| A11Y-03 | ARIA attributes | Custom controls have `role`, `aria-label`, `aria-expanded`, `aria-selected` |
| A11Y-04 | Form field labels | Every input has visible or `aria-label` label |
| A11Y-05 | Color contrast | Text meets WCAG AA (4.5:1). Status not color-only |
| A11Y-06 | Focus-visible styles | Interactive elements use `celestial-focus` or `focus-visible:` ring |
| A11Y-07 | Screen reader text | Decorative icons `aria-hidden="true"`, meaningful icons have `aria-label` |

### Category 6: Text, Copy & UX Polish

| Item ID | Check | Pass Criteria |
|---------|-------|---------------|
| UX-01 | No placeholder text | No "TODO", "Lorem ipsum", "Test" in user-visible strings |
| UX-02 | Consistent terminology | Same terms as rest of app (e.g., "pipeline" not "workflow") |
| UX-03 | Verb-based button labels | "Create Agent" not "New Agent" |
| UX-04 | Confirmation on destructive actions | Delete/remove/stop uses `<ConfirmationDialog>` |
| UX-05 | Success feedback | Mutations show success state (toast, status change, inline) |
| UX-06 | User-friendly errors | Format: "Could not [action]. [Reason]. [Next step]." |
| UX-07 | Consistent timestamps | Relative for recent, absolute for older |
| UX-08 | Truncation with tooltip | Long text uses `text-ellipsis` + `<Tooltip>` |

### Category 7: Styling & Layout

| Item ID | Check | Pass Criteria |
|---------|-------|---------------|
| STYLE-01 | Tailwind only | No inline `style={}` attributes. Uses `cn()` |
| STYLE-02 | Responsive design | Not broken at 768px–1920px |
| STYLE-03 | Dark mode support | Uses `dark:` variants or CSS variables. No hardcoded colors |
| STYLE-04 | Consistent spacing | Tailwind spacing scale only, no arbitrary values |
| STYLE-05 | Card consistency | Content sections use `<Card>` with consistent padding |
| STYLE-06 | Loading shimmer | Consider skeleton states for content areas |

### Category 8: Performance

| Item ID | Check | Pass Criteria |
|---------|-------|---------------|
| PERF-01 | No unnecessary re-renders | `React.memo` where props stable, `useCallback` for memoized children |
| PERF-02 | Stable list keys | `key={item.id}`, never `key={index}` |
| PERF-03 | Large list virtualization | >50 items uses `react-window` or pagination |
| PERF-04 | Memoized transforms | Heavy sorts/filters/groups in `useMemo` |
| PERF-05 | Lazy loaded images | Non-critical images use `loading="lazy"` |

### Category 9: Test Coverage

| Item ID | Check | Pass Criteria |
|---------|-------|---------------|
| TEST-01 | Hook tests exist | Custom hooks tested via `renderHook()` with mocked API |
| TEST-02 | Component tests exist | Key interactive components have `.test.tsx` files |
| TEST-03 | Test conventions | Uses `vi.mock`, `renderHook`, `waitFor`, `createWrapper()` |
| TEST-04 | Edge cases covered | Empty, error, loading, rate limit, long strings, null data |
| TEST-05 | No snapshot tests | Assertion-based tests only |

### Category 10: Code Hygiene

| Item ID | Check | Pass Criteria |
|---------|-------|---------------|
| HYGIENE-01 | No dead code | No unused imports, commented-out blocks, unreachable branches |
| HYGIENE-02 | No console.log | All removed or replaced with structured logging |
| HYGIENE-03 | `@/` alias imports | All project imports use `@/...`, not relative `../../` |
| HYGIENE-04 | File naming | Components PascalCase `.tsx`, hooks `use*.ts`, types in `types/` |
| HYGIENE-05 | No magic strings | Repeated strings defined as constants |
| HYGIENE-06 | ESLint clean | 0 warnings for all audited files |

## Output Format

Each page audit produces a markdown file at `specs/052-ui-audit/checklists/[page-name]-audit.md` with:

```markdown
# Audit: [PageName]

**Page**: `src/pages/[PageName].tsx`
**Date**: [ISO date]
**Status**: [Audit Passed | Needs Remediation]

## Summary

| Category | Pass | Fail | N/A |
|----------|------|------|-----|
| 1. Component Architecture | X | Y | Z |
| ... | ... | ... | ... |
| **Total** | XX | YY | ZZ |

## Findings

### [ITEM-ID]: [Brief Description]
- **Status**: Fail
- **Severity**: [Critical | Major | Minor]
- **File**: `src/path/to/file.tsx`
- **Location**: Lines XX-YY / function `functionName`
- **Issue**: [Description of the problem]
- **Recommendation**: [Specific fix]
- **Related Requirement**: FR-XXX
```
