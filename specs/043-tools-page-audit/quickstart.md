# Quickstart: Tools Page Audit

**Feature**: `043-tools-page-audit` | **Date**: 2026-03-16 | **Plan**: [plan.md](plan.md)

## Prerequisites

- Node.js 22+ (see `solune/frontend/package.json` engines)
- npm 10+
- Access to the Solune frontend development environment

## Setup

```bash
# Navigate to the frontend directory
cd solune/frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend runs at `http://localhost:5173` by default.

## Key Files to Edit

### Primary targets (audit changes happen here)

| File | Path | Priority |
|------|------|----------|
| ToolsPanel | `src/components/tools/ToolsPanel.tsx` | Phase 1–3 |
| ToolCard | `src/components/tools/ToolCard.tsx` | Phase 2–3 |
| RepoConfigPanel | `src/components/tools/RepoConfigPanel.tsx` | Phase 1 |
| McpPresetsGallery | `src/components/tools/McpPresetsGallery.tsx` | Phase 1–2 |
| UploadMcpModal | `src/components/tools/UploadMcpModal.tsx` | Phase 2 |
| GitHubMcpConfigGenerator | `src/components/tools/GitHubMcpConfigGenerator.tsx` | Phase 4 |
| useTools hook | `src/hooks/useTools.ts` | Phase 1 |

### Reference files (read but don't modify)

| File | Path | Purpose |
|------|------|---------|
| CelestialLoader | `src/components/common/CelestialLoader.tsx` | Loading state component |
| ConfirmationDialog | `src/components/ui/confirmation-dialog.tsx` | Confirmation dialog API |
| Tooltip | `src/components/ui/tooltip.tsx` | Tooltip component API |
| ErrorBoundary | `src/components/common/ErrorBoundary.tsx` | Error boundary pattern |
| API service | `src/services/api.ts` | Tool API endpoints |
| Rate limit utility | `src/utils/rateLimit.ts` | `isRateLimitApiError()` helper |
| Types | `src/types/index.ts` | Tool type definitions |

### Test files (extend existing)

| File | Path | Purpose |
|------|------|---------|
| Existing tests | `src/components/tools/ToolsEnhancements.test.tsx` | Extend with new test cases |
| New hook tests | `src/hooks/useTools.test.ts` | Create new — hook tests |

## Verification Commands

```bash
# Navigate to the frontend directory
cd solune/frontend

# Run linter on tools-related files
npx eslint src/pages/ToolsPage.tsx src/components/tools/ src/hooks/useTools.ts src/hooks/useAgentTools.ts src/hooks/useRepoMcpConfig.ts src/hooks/useMcpPresets.ts

# Run type checker
npm run type-check

# Run all tests
npx vitest run

# Run only tools-related tests
npx vitest run src/components/tools/ src/hooks/useTools

# Build to verify no compilation errors
npm run build
```

## Development Workflow

### Phase 1: Reliability fixes

1. Open `RepoConfigPanel.tsx` — replace loading text with `<CelestialLoader>`; add retry button to error state
2. Open `McpPresetsGallery.tsx` — same loading/error fixes; add empty state
3. Open `ToolsPanel.tsx` — replace inline delete with `<ConfirmationDialog>`; add success toasts; format errors
4. Open `useTools.ts` — add rate-limit detection; format error messages

### Phase 2: Accessibility

1. Check all interactive elements with Tab key
2. Verify modals trap focus and return focus on close
3. Add `aria-label` to unlabeled buttons and inputs
4. Verify SyncStatusBadge text+color (not color alone)

### Phase 3: UX polish

1. Review all button labels for verb-based naming
2. Add Tooltip wrapping for truncated text in ToolCard
3. Format timestamps (relative vs. absolute)
4. Test dark mode for all components

### Phase 4: Performance

1. Fix array-index keys in GitHubMcpConfigGenerator
2. Verify responsive layout at 768px, 1024px, 1440px, 1920px
3. Check for unnecessary re-renders

### Phase 5: Quality + Testing

1. Run linter — fix all warnings
2. Run type checker — fix all errors
3. Write hook tests for useToolsList
4. Write component tests for ToolCard and ToolsPanel interactions
5. Write edge case tests

### Phase 6: Final validation

1. All verification commands pass (lint, types, tests, build)
2. Manual browser testing (light/dark mode, responsive, keyboard-only)

## Common Patterns

### Importing shared components

```typescript
import { CelestialLoader } from '@/components/common/CelestialLoader';
import { ConfirmationDialog } from '@/components/ui/confirmation-dialog';
import { Tooltip } from '@/components/ui/tooltip';
import { isRateLimitApiError } from '@/utils/rateLimit';
```

### Loading state pattern

```tsx
if (isLoading) {
  return <CelestialLoader size="md" />;
}
```

### Error state with retry

```tsx
if (error) {
  return (
    <div className="flex flex-col items-center gap-2 py-4">
      <p className="text-sm text-destructive">{error}</p>
      <Button variant="ghost" size="sm" onClick={onRetry}>
        Retry
      </Button>
    </div>
  );
}
```

### Confirmation dialog pattern

```tsx
<ConfirmationDialog
  open={showDeleteDialog}
  onOpenChange={setShowDeleteDialog}
  title="Delete Tool"
  description={deleteDescription}
  confirmLabel="Delete Tool"
  variant="destructive"
  onConfirm={handleConfirmDelete}
  isLoading={isDeleting}
/>
```

### Truncated text with tooltip

```tsx
<Tooltip content={tool.name}>
  <span className="truncate max-w-[200px] block">{tool.name}</span>
</Tooltip>
```

### Relative timestamp formatting

```typescript
function formatTimestamp(isoString: string | null): string {
  if (!isoString) return 'Never synced';
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffHours = diffMs / (1000 * 60 * 60);

  if (diffHours < 1) {
    const mins = Math.floor(diffMs / (1000 * 60));
    return mins <= 1 ? 'Just now' : `${mins} minutes ago`;
  }
  if (diffHours < 24) {
    return `${Math.floor(diffHours)} hours ago`;
  }
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}
```
