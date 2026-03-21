# Component Contract: Breadcrumb Context API

**Feature**: `055-breadcrumb-deep-routes` | **Date**: 2026-03-21

## Overview

This document defines the public API contract for the breadcrumb context system. Since this feature is frontend-only with no backend endpoints, the contract covers React component interfaces and hook APIs instead of HTTP endpoints.

## useBreadcrumb Hook

**File**: `solune/frontend/src/hooks/useBreadcrumb.ts`
**Export**: `useBreadcrumb(): BreadcrumbHookReturn`

### Return Type

```typescript
interface BreadcrumbHookReturn {
  /**
   * Register a human-readable label for a specific path.
   * The label will be used by the Breadcrumb component instead of
   * the URL segment or NAV_ROUTES label.
   *
   * @param path - Cumulative path (e.g., '/apps/my-cool-app')
   * @param label - Human-readable display text (e.g., 'My Cool App')
   */
  setLabel: (path: string, label: string) => void;

  /**
   * Remove a previously registered label override.
   * Should be called on component unmount to prevent label leakage.
   *
   * @param path - The cumulative path to remove the label for
   */
  removeLabel: (path: string) => void;
}
```

### Usage Contract

```typescript
// In a page component:
import { useBreadcrumb } from '@/hooks/useBreadcrumb';

function AppDetailPage({ appName }: { appName: string }) {
  const { setLabel, removeLabel } = useBreadcrumb();
  const { data: app } = useAppDetail(appName);

  useEffect(() => {
    const path = `/apps/${appName}`;
    const label = app?.display_name ?? appName;
    setLabel(path, label);
    return () => removeLabel(path);
  }, [appName, app?.display_name, setLabel, removeLabel]);

  return <div>...</div>;
}
```

### Constraints

- `useBreadcrumb()` MUST be called within a component tree wrapped by `BreadcrumbProvider`
- Calling `useBreadcrumb()` outside a provider MUST throw a descriptive error
- `setLabel` and `removeLabel` function references MUST be stable (wrapped in `useCallback`) to avoid unnecessary re-renders in consumer useEffect dependencies

## useBreadcrumbLabels Hook

**File**: `solune/frontend/src/hooks/useBreadcrumb.ts`
**Export**: `useBreadcrumbLabels(): Map<string, string>`

### Description

Read-only hook for the Breadcrumb component to access the current label overrides map. Separated from `useBreadcrumb` to allow the Breadcrumb component to subscribe to label changes without exposing mutation functions.

### Usage Contract

```typescript
// In the Breadcrumb component:
import { useBreadcrumbLabels } from '@/hooks/useBreadcrumb';

function Breadcrumb() {
  const labels = useBreadcrumbLabels();
  // labels is Map<string, string>
  // e.g., Map { '/apps/my-cool-app' => 'My Cool App' }
}
```

## BreadcrumbProvider Component

**File**: `solune/frontend/src/hooks/useBreadcrumb.ts`
**Export**: `BreadcrumbProvider({ children }: { children: React.ReactNode })`

### Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `children` | `React.ReactNode` | Yes | Child components that will have access to the breadcrumb context |

### Placement Contract

```tsx
// In AppLayout.tsx:
import { BreadcrumbProvider } from '@/hooks/useBreadcrumb';

function AppLayout() {
  return (
    <BreadcrumbProvider>
      <TopBar />     {/* Contains Breadcrumb (consumer) */}
      <Outlet />     {/* Contains page components (producers) */}
    </BreadcrumbProvider>
  );
}
```

## buildBreadcrumbSegments Function

**File**: `solune/frontend/src/lib/breadcrumb-utils.ts`
**Export**: `buildBreadcrumbSegments(pathname, navRoutes, labelOverrides): BreadcrumbSegment[]`

### Signature

```typescript
interface BreadcrumbSegment {
  label: string;
  path: string;
}

function buildBreadcrumbSegments(
  pathname: string,
  navRoutes: Array<{ path: string; label: string }>,
  labelOverrides: Map<string, string>,
): BreadcrumbSegment[]
```

### Behavior Contract

| Input | Output |
|-------|--------|
| `pathname: '/'` | `[{ label: 'Home', path: '/' }]` |
| `pathname: '/apps'` | `[{ label: 'Home', path: '/' }, { label: 'Apps', path: '/apps' }]` |
| `pathname: '/apps/my-cool-app'` with override `Map { '/apps/my-cool-app' => 'My Cool App' }` | `[{ label: 'Home', path: '/' }, { label: 'Apps', path: '/apps' }, { label: 'My Cool App', path: '/apps/my-cool-app' }]` |
| `pathname: '/apps/my-cool-app'` with no override | `[{ label: 'Home', path: '/' }, { label: 'Apps', path: '/apps' }, { label: 'My Cool App', path: '/apps/my-cool-app' }]` (title-case fallback) |
| `pathname: '/apps/my-cool-app/settings'` | `[{ label: 'Home', path: '/' }, { label: 'Apps', path: '/apps' }, { label: 'My Cool App', path: '/apps/my-cool-app' }, { label: 'Settings', path: '/apps/my-cool-app/settings' }]` |
| `pathname: '/apps/'` (trailing slash) | Same as `pathname: '/apps'` |

### Edge Cases

- Empty pathname (`''`) → returns `[{ label: 'Home', path: '/' }]`
- Multiple trailing slashes → normalized to no trailing slash
- Segments with only hyphens/underscores → title-cased normally

## toTitleCase Function

**File**: `solune/frontend/src/lib/breadcrumb-utils.ts`
**Export**: `toTitleCase(slug: string): string`

### Behavior Contract

| Input | Output |
|-------|--------|
| `'my-cool-app'` | `'My Cool App'` |
| `'settings'` | `'Settings'` |
| `'user_profile'` | `'User Profile'` |
| `'already-Capitalized'` | `'Already Capitalized'` |
| `''` | `''` |
