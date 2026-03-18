# Quickstart: UI Audit — Page-Level Quality & Consistency

**Feature**: 052-ui-audit | **Date**: 2026-03-18

## Overview

This guide explains how to execute a page audit — the repeatable process applied to each top-level route page in the Solune frontend. Each audit evaluates 60 checklist items across 10 quality dimensions and produces a findings report with actionable fixes.

## Prerequisites

- Node.js and npm installed
- Repository cloned with frontend dependencies installed:
  ```bash
  cd solune/frontend
  npm install
  ```
- Familiarity with the audit checklist: [`contracts/audit-checklist.md`](./contracts/audit-checklist.md)
- Familiarity with the findings report template: [`contracts/findings-report.md`](./contracts/findings-report.md)

## Audit a Page (Step-by-Step)

### Step 1: Select the Page

Choose the next page to audit from the priority list in [`research.md`](./research.md#rt-007-page-audit-execution-order).

### Step 2: Discovery

Read the page and its related files to understand its current state.

```bash
# 1. Check page line count
wc -l solune/frontend/src/pages/[PageName].tsx

# 2. List feature components
ls solune/frontend/src/components/[feature]/

# 3. List related hooks
ls solune/frontend/src/hooks/use[Feature]*.ts

# 4. Run linter on the page
cd solune/frontend && npx eslint src/pages/[PageName].tsx src/components/[feature]/

# 5. Run type checker
cd solune/frontend && npx tsc --noEmit

# 6. Run existing tests for this feature
cd solune/frontend && npx vitest run src/**/*[feature]*

# 7. Check for common issues
grep -rn ': any' src/pages/[PageName].tsx src/components/[feature]/
grep -rn 'console.log' src/pages/[PageName].tsx src/components/[feature]/
grep -rn 'style=' src/pages/[PageName].tsx src/components/[feature]/
grep -rn "from '\.\." src/pages/[PageName].tsx src/components/[feature]/
```

### Step 3: Score the Checklist

Evaluate each of the 60 checklist items as **Pass**, **Fail**, or **N/A**.

Use the evaluation methods defined in [`contracts/audit-checklist.md`](./contracts/audit-checklist.md) for each item. Document results in a findings report following [`contracts/findings-report.md`](./contracts/findings-report.md).

### Step 4: Remediation (Phased)

Fix findings in priority order:

1. **Structural Fixes** — Extract oversized pages into sub-components, extract complex state into hooks, replace raw fetches with React Query
2. **States & Error Handling** — Add/fix loading states (CelestialLoader), error states (user-friendly message + retry), empty states (meaningful guidance)
3. **Accessibility & UX** — Add ARIA attributes, fix keyboard navigation, fix focus management, fix copy/terminology, add confirmation dialogs for destructive actions
4. **Testing** — Write/update hook tests, component tests, edge-case tests
5. **Code Hygiene** — Remove dead code, console.logs, fix imports, eliminate `any` types

### Step 5: Validation

Verify all fixes pass quality gates:

```bash
cd solune/frontend

# Lint (must be 0 warnings)
npx eslint src/pages/[PageName].tsx src/components/[feature]/

# Type check (must be 0 errors)
npx tsc --noEmit

# Tests (must all pass)
npx vitest run

# Theme validation (optional)
npm run audit:theme-*
```

Visual verification:
- Light mode: all elements visible and properly styled
- Dark mode: no invisible text, broken contrast, or missing borders
- Responsive: 768px, 1024px, 1440px, 1920px — no clipping, scrolling, or overlapping
- Keyboard: Tab through all interactive elements, Enter/Space to activate

## Key Files Reference

| Category | Path |
|----------|------|
| Pages (audit targets) | `solune/frontend/src/pages/` |
| Feature components | `solune/frontend/src/components/[feature]/` |
| Custom hooks | `solune/frontend/src/hooks/` |
| API service | `solune/frontend/src/services/api.ts` |
| Types | `solune/frontend/src/types/` |
| Shared components | `solune/frontend/src/components/common/`, `src/components/ui/` |
| Test utilities | `solune/frontend/src/test/test-utils.tsx` |
| Test factories | `solune/frontend/src/test/factories/` |
| Utility helpers | `solune/frontend/src/lib/utils.ts` |

## Common Patterns

### Adding a Loading State

```tsx
import { CelestialLoader } from '@/components/common/CelestialLoader';

if (isLoading) {
  return <CelestialLoader size="md" />;
}
```

### Adding an Error State

```tsx
if (isError) {
  return (
    <div className="flex flex-col items-center gap-4 p-8">
      <p className="text-destructive">
        Could not load [resource]. {error?.message || 'Please try again.'}
      </p>
      <Button onClick={() => refetch()} variant="outline">
        Retry
      </Button>
    </div>
  );
}
```

### Adding an Empty State

```tsx
if (data && data.length === 0) {
  return (
    <div className="flex flex-col items-center gap-4 p-8 text-muted-foreground">
      <p>No [items] found.</p>
      <p>Get started by creating your first [item].</p>
    </div>
  );
}
```

### Confirmation on Destructive Action

```tsx
import { useConfirmation } from '@/hooks/useConfirmation';

const { confirm } = useConfirmation();

const handleDelete = async () => {
  const confirmed = await confirm({
    title: 'Delete [Item]',
    description: 'This action cannot be undone. Are you sure?',
    confirmLabel: 'Delete',
    variant: 'destructive',
  });
  if (confirmed) {
    deleteMutation.mutate(itemId);
  }
};
```

### Truncation with Tooltip

```tsx
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';

<Tooltip>
  <TooltipTrigger asChild>
    <span className="truncate max-w-[200px] block">{longText}</span>
  </TooltipTrigger>
  <TooltipContent>{longText}</TooltipContent>
</Tooltip>
```
