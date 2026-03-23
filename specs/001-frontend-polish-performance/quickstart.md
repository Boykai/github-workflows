# Quickstart: Frontend Polish & Performance

**Feature**: 001-frontend-polish-performance
**Date**: 2026-03-22

## Overview

This guide covers three independent workstreams. Each can be implemented and tested in isolation.

## Prerequisites

- Node.js 18+ and npm (frontend)
- Python 3.11+ with pip (backend)
- Repository cloned with `solune/frontend` and `solune/backend` accessible

## Phase A — Centralized Icon Imports

### Step 1: Create the barrel file

Create `solune/frontend/src/lib/icons.ts` with named re-exports of all Lucide icons currently used in the codebase.

```bash
# Scan for all unique Lucide icons currently imported
grep -rn "from 'lucide-react'" solune/frontend/src/ \
  | grep -oP 'import \{[^}]+\}' \
  | tr ',' '\n' \
  | grep -oP '\w+' \
  | grep -v 'import' \
  | sort -u
```

### Step 2: Migrate all imports

Update all ~68 files importing from `lucide-react` to import from `@/lib/icons` instead.

### Step 3: Add lint rule

Add `no-restricted-imports` to `eslint.config.js`:

```javascript
'no-restricted-imports': ['error', {
  paths: [{
    name: 'lucide-react',
    message: 'Import icons from @/lib/icons instead of lucide-react directly.',
  }],
}]
```

### Step 4: Verify

```bash
cd solune/frontend
# Must return zero results
grep -rn "from 'lucide-react'" src/
# Must pass without errors
npm run lint
# Build and check icons-vendor chunk size
npm run build
```

## Phase B — ChoresPanel Bug Fix

### Step 1: Add backend endpoint

Add `GET /{project_id}/chore-names` to `solune/backend/src/api/chores.py`:

```python
@router.get("/{project_id}/chore-names", response_model=list[str])
async def list_chore_names(project_id: str):
    """Return all chore names for template membership checks."""
    # SELECT name FROM chores WHERE project_id = ?
```

### Step 2: Add frontend hook

Add `useAllChoreNames` to `solune/frontend/src/hooks/useChores.ts`:

```typescript
export function useAllChoreNames(projectId: string | undefined) {
  return useQuery({
    queryKey: ['chore-names', projectId],
    queryFn: () => choresApi.listNames(projectId!),
    enabled: !!projectId,
    staleTime: 60_000,
  });
}
```

### Step 3: Update ChoresPanel

Replace the paginated membership check in `ChoresPanel.tsx`:

```typescript
const { data: allChoreNames = [] } = useAllChoreNames(projectId);
const choreNamesSet = useMemo(() => new Set(allChoreNames), [allChoreNames]);
const uncreatedTemplates = useMemo(
  () => repoTemplates?.filter((tpl) => !choreNamesSet.has(tpl.name)) ?? [],
  [repoTemplates, choreNamesSet]
);
```

### Step 4: Verify

```bash
cd solune/backend && python -m pytest tests/ -k chore
cd solune/frontend && npm run test -- --run
```

## Phase C — Error Recovery Hints

### Step 1: Create error hints utility

Create `solune/frontend/src/utils/errorHints.ts` with `getErrorHint(error: unknown)`.

### Step 2: Integrate into error components

- `ErrorBoundary.tsx`: Show hint below error message
- `ProjectBoardErrorBanners.tsx`: Enhance banners with hints and action links

### Step 3: Extend EmptyState

Add optional `hint?: string` prop to `EmptyState.tsx`.

### Step 4: Verify

```bash
cd solune/frontend
npm run test -- --run
npm run lint
npm run test:coverage
```

## Full Verification Checklist

1. ✅ `grep -rn "from 'lucide-react'" solune/frontend/src/` returns zero results
2. ✅ ESLint blocks direct `lucide-react` imports
3. ✅ Icons-vendor chunk size unchanged or smaller after build
4. ✅ Filtered chores no longer cause templates to appear uncreated
5. ✅ 401 and network errors surface hint text in UI
6. ✅ `npm run lint` passes
7. ✅ `npm run test:coverage` passes
