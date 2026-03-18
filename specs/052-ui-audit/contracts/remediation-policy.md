# Contract: Remediation Policy

**Feature**: `052-ui-audit`
**Date**: 2026-03-18

---

## Overview

This contract defines the standards and process for fixing audit findings. It ensures remediation is consistent, safe, and verifiable across all audited pages.

## Remediation Priority

Findings are remediated in severity order, then by audit category priority:

### Severity Order

1. **Critical** — Must fix immediately. Blocks audit completion.
   - Broken functionality (blank screens, crashes)
   - Accessibility barriers (keyboard-inaccessible controls, missing ARIA)
   - Security issues (exposed data, XSS vectors)

2. **Major** — Must fix before audit sign-off.
   - Missing loading/error/empty states
   - Type safety violations (`any` types, unsafe assertions)
   - UX inconsistencies (missing confirmations, raw error messages)
   - Data fetching anti-patterns (raw fetch, duplicate calls)

3. **Minor** — Should fix, may defer with justification.
   - Code style issues (console.log, dead code, relative imports)
   - Performance optimizations (missing memoization, index keys)
   - Missing test coverage

### Category Priority for Remediation

1. Loading, Error & Empty States (most user-visible)
2. Accessibility (legal/ethical requirement)
3. Component Architecture (enables other fixes)
4. Type Safety (prevents regressions)
5. Data Fetching (correctness)
6. Text, Copy & UX Polish (user trust)
7. Styling & Layout (visual consistency)
8. Performance (user experience)
9. Code Hygiene (developer experience)
10. Test Coverage (regression prevention)

## Remediation Standards

### Component Extraction (ARCH-01)

When a page exceeds 250 lines:

```
GIVEN a page file exceeds 250 lines
WHEN extracting sub-components
THEN each extracted component:
  - Lives in src/components/[feature]/[ComponentName].tsx
  - Has a single responsibility (one section of the page)
  - Receives data via props (no more than 2 levels of prop drilling)
  - Uses TypeScript interfaces for its props
  - Has no inline business logic
AND the page file is ≤250 lines after extraction
AND all existing tests still pass
```

### Hook Extraction (ARCH-06)

When complex state logic exceeds 15 lines:

```
GIVEN a page or component has >15 lines of useState/useEffect/useCallback
WHEN extracting into a custom hook
THEN the hook:
  - Lives in src/hooks/use[Feature].ts
  - Has a descriptive name matching its responsibility
  - Returns a typed object (not a tuple for >2 values)
  - Encapsulates related state and effects together
AND the component's render logic contains only JSX and simple conditionals
```

### Loading State Addition (STATE-01)

```
GIVEN a page fetches data
WHEN data has not yet arrived
THEN the page displays:
  - <CelestialLoader size="md" /> for full-page loading
  - <CelestialLoader size="sm" /> for section-level loading
  - OR a skeleton placeholder matching the content shape
AND the loading indicator is centered in the content area
AND the loading indicator has an aria-label="Loading"
```

### Error State Addition (STATE-02)

```
GIVEN an API call fails
WHEN rendering the error state
THEN the page displays:
  - A user-friendly message: "Could not load [resource]. [Reason]. Please try again."
  - A "Retry" button that re-triggers the failed query
  - Rate limit detection using isRateLimitApiError()
  - Rate limit-specific message: "Rate limit reached. Please wait a moment and try again."
AND the error message does not expose raw error codes or stack traces
AND the error state is accessible (aria-live="polite")
```

### Empty State Addition (STATE-03)

```
GIVEN data has loaded but the collection is empty
WHEN rendering the empty state
THEN the page displays:
  - A descriptive message explaining what the empty collection represents
  - A call-to-action guiding the user to create/add the first item
  - OR uses ProjectSelectionEmptyState for project-dependent pages
AND the empty state is visually distinct from the loading state
```

### Destructive Action Confirmation (UX-04)

```
GIVEN a destructive action (delete, remove, stop) exists
WHEN the user triggers it
THEN a <ConfirmationDialog> appears with:
  - A clear title describing the action ("Delete [resource name]?")
  - A description of consequences
  - A "Cancel" button (secondary style)
  - A "Delete" / "Remove" / "Stop" button (destructive style)
AND the action is NOT executed until the user confirms
AND the dialog traps focus and returns focus to the trigger on close
```

### Mutation Feedback (UX-05, DATA-06)

```
GIVEN a mutation (create, update, delete) completes
WHEN the mutation succeeds
THEN the user sees success feedback:
  - Toast notification for background operations
  - Inline status change for visible items
  - OR navigation to the created/updated resource
AND when the mutation fails
THEN the user sees error feedback:
  - User-friendly error message (FR-037 format)
  - The form/action state is preserved (not cleared)
  - Rate limit errors are detected and messaged specifically
```

## Verification Checklist

After remediation of each page, verify:

```bash
# 1. ESLint clean (0 warnings)
npx eslint src/pages/[PageName].tsx src/components/[feature]/

# 2. Type check clean (0 errors)
npx tsc --noEmit

# 3. All tests pass
npx vitest run src/pages/[PageName].test.tsx src/hooks/use[Feature].test.ts src/components/[feature]/

# 4. Build succeeds
npm run build
```

Plus manual verification:
- Light mode and dark mode render correctly
- Viewport 768px → 1920px — no layout breakage
- Tab through all interactive elements
- Enter/Space to activate buttons, links, toggles
- Screen reader labels read correctly (or axe DevTools audit reports no violations)
