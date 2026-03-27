# Quickstart: UI Audit

**Feature**: `001-ui-audit` | **Date**: 2026-03-27 | **Plan**: [plan.md](plan.md)

## Prerequisites

- Node.js 20+
- npm (comes with Node.js)
- Access to the `solune/frontend/` directory

## Setup

```bash
# Navigate to the frontend directory
cd solune/frontend

# Install dependencies
npm ci

# Verify the current state before making changes
npm run lint          # ESLint — note any existing warnings
npm run type-check    # TypeScript — note any existing errors
npm run test          # Vitest — note any failing tests
npm run build         # Vite build — verify it succeeds
```

## Audit Workflow (per page)

### Step 1: Discovery

```bash
# Check page line count
wc -l src/pages/[PageName].tsx

# Find related components
ls src/components/[feature]/

# Find related hooks
grep -r "use[Feature]" src/hooks/ --include="*.ts" -l

# Find related types
grep -r "[Feature]" src/types/ --include="*.ts" -l
```

### Step 2: Lint & Type Check

```bash
# Lint the page and its feature components
npx eslint src/pages/[PageName].tsx src/components/[feature]/

# Type-check the entire project
npx tsc --noEmit
```

### Step 3: Run Tests

```bash
# Run tests for the specific feature
npx vitest run src/pages/[PageName].test.tsx
npx vitest run src/hooks/use[Feature].test.ts
npx vitest run src/components/[feature]/

# Run all tests to check for regressions
npx vitest run

# Run with coverage
npx vitest run --coverage
```

### Step 4: Apply Fixes

For each audit finding, follow the implementation phases:

1. **Structural fixes** — Extract oversized pages, move logic to hooks
2. **State fixes** — Add loading, error, empty state handling
3. **a11y fixes** — Add ARIA attributes, fix keyboard navigation
4. **UX fixes** — Fix text, add tooltips, add confirmation dialogs
5. **Test fixes** — Add missing tests, update test patterns

### Step 5: Validate

```bash
# After all fixes for a page:
npx eslint src/pages/[PageName].tsx src/components/[feature]/  # 0 warnings
npx tsc --noEmit                                                # 0 errors
npx vitest run                                                  # all tests pass
```

## Page Audit Order

Audit pages in priority order to maximize impact:

### High Priority (complex pages with data fetching)
1. **ProjectsPage** — 503 lines, needs decomposition, most complex page
2. **AgentsPipelinePage** — 313 lines, needs decomposition, pipeline configuration
3. **AppsPage** — 325 lines, needs decomposition, hardcoded colors

### Medium Priority (moderate complexity)
4. **ActivityPage** — 251 lines, borderline, missing test file
5. **AgentsPage** — 238 lines, missing empty state
6. **ChoresPage** — 181 lines, good baseline
7. **ToolsPage** — 104 lines, good baseline
8. **AppPage** — 141 lines, single detail view

### Low Priority (simple pages)
9. **SettingsPage** — 107 lines, form-based
10. **HelpPage** — 221 lines, static content
11. **LoginPage** — 119 lines, auth flow
12. **NotFoundPage** — 29 lines, static error page

## Key Files Reference

| Purpose | Path |
|---------|------|
| Shared UI primitives | `src/components/ui/` (Button, Card, Input, Tooltip, ConfirmationDialog) |
| Common components | `src/components/common/` (CelestialLoader, ErrorBoundary, EmptyState) |
| Class utility | `src/lib/utils.ts` (`cn()` for conditional Tailwind classes) |
| Icons | `src/lib/icons.ts` (centralized Lucide icon re-exports) |
| API client | `src/services/api.ts` (React Query wrappers) |
| Rate limit context | `src/context/RateLimitContext.tsx` |
| Test utilities | `src/test/` (setup, factories, wrappers) |

## Common Patterns

### Loading State
```tsx
import { CelestialLoader } from '@/components/common/CelestialLoader';

if (isLoading) {
  return <CelestialLoader size="md" label="Loading data…" />;
}
```

### Error State
```tsx
import { isRateLimitApiError } from '@/utils/rateLimit';

if (error) {
  const isRateLimit = isRateLimitApiError(error);
  return (
    <div className="text-center p-6">
      <p className="text-destructive">
        {isRateLimit
          ? 'Rate limit reached. Please wait a moment before retrying.'
          : `Could not load data. ${error.message}. Try refreshing the page.`}
      </p>
      <Button onClick={() => refetch()} className="mt-4">
        Retry
      </Button>
    </div>
  );
}
```

### Empty State
```tsx
import { ProjectSelectionEmptyState } from '@/components/common/ProjectSelectionEmptyState';

if (data && data.length === 0) {
  return <ProjectSelectionEmptyState message="No items yet" />;
}
```

### Confirmation Dialog
```tsx
import { ConfirmationDialog } from '@/components/ui/confirmation-dialog';

<ConfirmationDialog
  open={showDeleteConfirm}
  onOpenChange={setShowDeleteConfirm}
  title="Delete Item"
  description="This action cannot be undone."
  confirmLabel="Delete"
  onConfirm={handleDelete}
  variant="destructive"
/>
```

### ErrorBoundary Wrapper
```tsx
import { ErrorBoundary } from '@/components/common/ErrorBoundary';

<ErrorBoundary>
  <ComplexSection />
</ErrorBoundary>
```
