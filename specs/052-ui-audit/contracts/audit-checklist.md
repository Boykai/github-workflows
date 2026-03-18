# Audit Checklist Contract

**Feature**: 052-ui-audit | **Version**: 1.0 | **Date**: 2026-03-18

## Purpose

Standardized 10-dimension quality checklist applied uniformly to every page audit. Each item maps to a functional requirement from the spec and has a deterministic pass/fail evaluation method.

---

## Dimension 1: Component Architecture & Modularity

| ID | Check | Pass Criteria | Evaluation Method | FR |
|----|-------|---------------|-------------------|-----|
| ARCH-01 | Single Responsibility | Page file ≤ 250 lines | `wc -l src/pages/[Page].tsx` | FR-020 |
| ARCH-02 | Feature folder structure | Sub-components in `src/components/[feature]/` | Directory inspection | FR-021 |
| ARCH-03 | No deep prop drilling | No data passed > 2 component levels | Code review — trace props | FR-022 |
| ARCH-04 | Reusable primitives | Uses `src/components/ui/` — no reimplementation | grep for duplicate Button/Card/Input/Tooltip implementations | — |
| ARCH-05 | Shared components | Uses CelestialLoader, ErrorBoundary, etc. where applicable | Verify loading/error patterns use shared components | — |
| ARCH-06 | Hook extraction | Complex state logic (> 15 lines useState/useEffect/useCallback) in hooks | Measure stateful code blocks in page file | FR-023 |
| ARCH-07 | No business logic in JSX | Computation in hooks/helpers, not inline | Code review — check render tree for transforms/filters/sorts | FR-024 |

## Dimension 2: Data Fetching & State Management

| ID | Check | Pass Criteria | Evaluation Method | FR |
|----|-------|---------------|-------------------|-----|
| DATA-01 | React Query for all API calls | Uses useQuery/useMutation — no raw useEffect + fetch | grep for `useEffect.*fetch` patterns | — |
| DATA-02 | Query key conventions | Hierarchical array keys: `[feature, ...params]` | Code review of query keys in hooks | — |
| DATA-03 | Optimistic updates | Mutations invalidateQueries on success | Check useMutation onSuccess handlers | — |
| DATA-04 | staleTime configured | Reasonable staleTime for non-volatile data | Check useQuery options | — |
| DATA-05 | No duplicate API calls | Same data not fetched independently in page + child | Trace query keys across component tree | — |
| DATA-06 | Mutation error handling | All useMutation have onError with user feedback | Check all useMutation calls for onError | — |

## Dimension 3: Loading, Error & Empty States

| ID | Check | Pass Criteria | Evaluation Method | FR |
|----|-------|---------------|-------------------|-----|
| STATE-01 | Loading state | CelestialLoader or skeleton visible during fetch | Check isLoading/isPending branches | FR-004 |
| STATE-02 | Error state | User-friendly message + retry on API error | Check isError branches, verify no raw error codes | FR-005 |
| STATE-03 | Empty state | Meaningful empty state when data is empty array | Check data.length === 0 branches | FR-006 |
| STATE-04 | Partial loading | Independent sections have independent loading/error | Check multi-query pages for per-section states | FR-007 |
| STATE-05 | Error boundary | Page wrapped in ErrorBoundary | Check App.tsx route wrappers or page-level ErrorBoundary | — |

## Dimension 4: Type Safety

| ID | Check | Pass Criteria | Evaluation Method | FR |
|----|-------|---------------|-------------------|-----|
| TYPE-01 | No `any` types | Zero `any` in page, components, hooks | `grep -rn ': any' src/pages/[Page].tsx src/components/[feature]/` | FR-030 |
| TYPE-02 | No type assertions | No `as` keyword (prefer type guards) | `grep -rn ' as ' src/pages/[Page].tsx` | — |
| TYPE-03 | API types match backend | Types in src/types/ aligned with Pydantic models | Cross-reference type definitions with API responses | — |
| TYPE-04 | Event handler types | Form events typed explicitly (not `any`) | Check event handler parameter types | — |
| TYPE-05 | Hook return types | Custom hooks have explicit or inferrable return types | Check hook signatures | — |

## Dimension 5: Accessibility (a11y)

| ID | Check | Pass Criteria | Evaluation Method | FR |
|----|-------|---------------|-------------------|-----|
| A11Y-01 | Keyboard accessible | All interactive elements reachable via Tab, activated via Enter/Space | Manual keyboard navigation test | FR-008 |
| A11Y-02 | Focus management | Dialogs trap focus; focus returns to trigger on close | Open/close dialogs with keyboard | FR-009 |
| A11Y-03 | ARIA attributes | Custom controls have role, aria-label, aria-expanded, aria-selected | Code review of custom controls | FR-010 |
| A11Y-04 | Form labels | All inputs have visible or aria-label | ESLint jsx-a11y check + code review | FR-011 |
| A11Y-05 | Color contrast | WCAG AA (4.5:1), status not color-only | Visual inspection + icon/text check | FR-012 |
| A11Y-06 | Focus-visible styles | celestial-focus class or focus-visible: ring on interactive elements | Code review of focus styles | FR-013 |
| A11Y-07 | Screen reader text | Decorative icons: aria-hidden="true"; meaningful icons: aria-label | Code review of icon usage | — |

## Dimension 6: Text, Copy & UX Polish

| ID | Check | Pass Criteria | Evaluation Method | FR |
|----|-------|---------------|-------------------|-----|
| COPY-01 | No placeholder text | Zero "TODO", "Lorem ipsum", "Test" strings | `grep -rni 'TODO\|Lorem\|placeholder' src/pages/[Page].tsx` | FR-014 |
| COPY-02 | Consistent terminology | Same terms used across pages | Cross-page terminology review | FR-015 |
| COPY-03 | Verb-based action labels | "Create X" not "New X", "Save X" not "X" | Review all button/action labels | — |
| COPY-04 | Confirmation on destructive actions | ConfirmationDialog for all delete/remove/stop | Trace destructive action handlers | FR-016 |
| COPY-05 | Success feedback | Mutations show toast/status/inline message | Check useMutation onSuccess for user feedback | FR-017 |
| COPY-06 | User-friendly errors | No raw error codes; follows "Could not [action]..." format | Check error message strings | FR-018 |
| COPY-07 | Consistent timestamps | Relative for recent, absolute for older | Check date formatting | — |
| COPY-08 | Truncation with tooltip | Long text truncated with ellipsis + Tooltip for full text | Check text-overflow patterns | FR-019 |

## Dimension 7: Styling & Layout

| ID | Check | Pass Criteria | Evaluation Method | FR |
|----|-------|---------------|-------------------|-----|
| STYLE-01 | Tailwind only | No inline `style={}` attributes; uses `cn()` | `grep -rn 'style=' src/pages/[Page].tsx` | — |
| STYLE-02 | Responsive design | No broken layout at 768px–1920px | Visual inspection at breakpoints | FR-026 |
| STYLE-03 | Dark mode support | Tailwind dark: variants, no hardcoded colors | `grep -rn 'bg-white\|text-black\|#fff\|#000' src/pages/[Page].tsx` | FR-025 |
| STYLE-04 | Consistent spacing | Tailwind spacing scale, no arbitrary values | `grep -rn 'p-\[.*px\]\|m-\[.*px\]' src/pages/[Page].tsx` | — |
| STYLE-05 | Card consistency | Content sections use Card from ui/card.tsx | Check section wrappers | — |
| STYLE-06 | Skeleton loading | Consider skeleton states for content areas | Check loading state rendering | — |

## Dimension 8: Performance

| ID | Check | Pass Criteria | Evaluation Method | FR |
|----|-------|---------------|-------------------|-----|
| PERF-01 | No unnecessary re-renders | React.memo for expensive components, useCallback where needed | Profile component renders | — |
| PERF-02 | Stable list keys | `key={item.id}` never `key={index}` | `grep -rn 'key={.*index}' src/pages/[Page].tsx` | FR-028 |
| PERF-03 | Large lists virtualized | Lists > 50 items use pagination or react-window | Check list rendering patterns | FR-027 |
| PERF-04 | No sync computation in render | Heavy transforms in useMemo | Check for inline sort/filter/map chains | — |
| PERF-05 | Lazy loaded images | Non-critical images use `loading="lazy"` | Check img tags | — |

## Dimension 9: Test Coverage

| ID | Check | Pass Criteria | Evaluation Method | FR |
|----|-------|---------------|-------------------|-----|
| TEST-01 | Hook tests exist | Custom hooks tested via renderHook() | Check for .test.ts files in hooks/ | FR-031 |
| TEST-02 | Component tests exist | Key interactive components have .test.tsx | Check for .test.tsx files in components/[feature]/ | FR-032 |
| TEST-03 | Test patterns correct | Uses vi.mock, renderHook, waitFor, createWrapper | Code review of test files | — |
| TEST-04 | Edge cases covered | Empty, error, loading, rate limit, null, long strings | Check test case descriptions | FR-033 |
| TEST-05 | No snapshot tests | Assertion-based tests only | `grep -rn 'toMatchSnapshot' src/**/*.test.*` | — |

## Dimension 10: Code Hygiene

| ID | Check | Pass Criteria | Evaluation Method | FR |
|----|-------|---------------|-------------------|-----|
| HYGIENE-01 | No dead code | No unused imports, commented blocks, unreachable branches | ESLint no-unused-vars + code review | FR-030 |
| HYGIENE-02 | No console.log | All removed or replaced | `grep -rn 'console.log' src/pages/[Page].tsx` | FR-030 |
| HYGIENE-03 | @/ import alias | All project imports use @/ alias | `grep -rn "from '\.\." src/pages/[Page].tsx` | — |
| HYGIENE-04 | File naming | PascalCase .tsx, use*.ts hooks, types in types/ | Directory inspection | — |
| HYGIENE-05 | No magic strings | Repeated strings defined as constants | Code review for repeated strings | — |
| HYGIENE-06 | ESLint clean | Zero warnings from ESLint | `npx eslint src/pages/[Page].tsx src/components/[feature]/` | FR-029 |

---

## Validation Commands

Per-page validation after remediation:

```bash
# Lint check (0 warnings)
npx eslint src/pages/[PageName].tsx src/components/[feature]/

# Type check (0 errors)
npx tsc --noEmit

# Unit tests (all pass)
npx vitest run src/**/*[feature]*

# Full test suite (all pass)
npx vitest run
```
