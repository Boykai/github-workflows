# Quickstart: Breadcrumb Deep Route Support

**Feature**: `055-breadcrumb-deep-routes` | **Date**: 2026-03-21

## Overview

This feature replaces the current two-segment breadcrumb with a full-depth breadcrumb that parses all URL path segments and supports dynamic labels via React Context. Three new files are created and two existing files are modified. No backend changes or new dependencies are needed.

## Prerequisites

- Node.js and npm installed
- Repository cloned with `solune/` directory structure

## Setup

```bash
cd solune/frontend
npm install
```

## Key Implementation Patterns

### 1. Breadcrumb Utilities (Phase 1, Step 1.1 + Phase 2, Step 2.1)

**File**: `solune/frontend/src/lib/breadcrumb-utils.ts`

Create pure utility functions for breadcrumb segment building:

```typescript
export interface BreadcrumbSegment {
  label: string;
  path: string;
}

/**
 * Convert a URL slug to title case.
 * 'my-cool-app' → 'My Cool App'
 * 'user_profile' → 'User Profile'
 */
export function toTitleCase(slug: string): string {
  if (!slug) return '';
  return slug
    .split(/[-_]/)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Build breadcrumb segments from a pathname.
 * Resolution order: labelOverrides → navRoutes → toTitleCase fallback.
 */
export function buildBreadcrumbSegments(
  pathname: string,
  navRoutes: Array<{ path: string; label: string }>,
  labelOverrides: Map<string, string>,
): BreadcrumbSegment[] {
  // Always start with Home
  const segments: BreadcrumbSegment[] = [{ label: 'Home', path: '/' }];

  // Normalize: strip trailing slashes, split on /
  const normalized = pathname.replace(/\/+$/, '') || '/';
  if (normalized === '/') return segments;

  const parts = normalized.split('/').filter(Boolean);

  for (let i = 0; i < parts.length; i++) {
    const cumulativePath = '/' + parts.slice(0, i + 1).join('/');

    // 1. Check context overrides
    const override = labelOverrides.get(cumulativePath);
    if (override) {
      segments.push({ label: override, path: cumulativePath });
      continue;
    }

    // 2. Check NAV_ROUTES
    const route = navRoutes.find((r) => r.path === cumulativePath);
    if (route) {
      segments.push({ label: route.label, path: cumulativePath });
      continue;
    }

    // 3. Title-case fallback
    segments.push({ label: toTitleCase(parts[i]), path: cumulativePath });
  }

  return segments;
}
```

### 2. Breadcrumb Context & Hook (Phase 1, Step 1.2)

**File**: `solune/frontend/src/hooks/useBreadcrumb.ts`

Create the context, provider, and hooks:

```typescript
import { createContext, useContext, useCallback, useState, type ReactNode } from 'react';

interface BreadcrumbContextValue {
  labels: Map<string, string>;
  setLabel: (path: string, label: string) => void;
  removeLabel: (path: string) => void;
}

const BreadcrumbContext = createContext<BreadcrumbContextValue | null>(null);

export function BreadcrumbProvider({ children }: { children: ReactNode }) {
  const [labels, setLabels] = useState<Map<string, string>>(() => new Map());

  const setLabel = useCallback((path: string, label: string) => {
    setLabels((prev) => {
      const next = new Map(prev);
      next.set(path, label);
      return next;
    });
  }, []);

  const removeLabel = useCallback((path: string) => {
    setLabels((prev) => {
      const next = new Map(prev);
      next.delete(path);
      return next;
    });
  }, []);

  return (
    <BreadcrumbContext.Provider value={{ labels, setLabel, removeLabel }}>
      {children}
    </BreadcrumbContext.Provider>
  );
}

/** Hook for page components to register/unregister breadcrumb labels. */
export function useBreadcrumb() {
  const ctx = useContext(BreadcrumbContext);
  if (!ctx) throw new Error('useBreadcrumb must be used within BreadcrumbProvider');
  return { setLabel: ctx.setLabel, removeLabel: ctx.removeLabel };
}

/** Hook for the Breadcrumb component to read label overrides. */
export function useBreadcrumbLabels(): Map<string, string> {
  const ctx = useContext(BreadcrumbContext);
  if (!ctx) throw new Error('useBreadcrumbLabels must be used within BreadcrumbProvider');
  return ctx.labels;
}
```

### 3. Wire BreadcrumbProvider into AppLayout (Phase 1, Step 1.3)

**File**: `solune/frontend/src/layout/AppLayout.tsx`

Add the provider around TopBar and Outlet:

```typescript
import { BreadcrumbProvider } from '@/hooks/useBreadcrumb';

// In the AppLayout JSX, wrap TopBar and the main content area:
<BreadcrumbProvider>
  <TopBar ... />
  <main>
    <Outlet />
  </main>
</BreadcrumbProvider>
```

### 4. Rewrite Breadcrumb Component (Phase 2, Step 2.2)

**File**: `solune/frontend/src/layout/Breadcrumb.tsx`

Replace the current implementation:

```typescript
import { useLocation, Link } from 'react-router-dom';
import { NAV_ROUTES } from '@/constants';
import { ChevronRight } from 'lucide-react';
import { useBreadcrumbLabels } from '@/hooks/useBreadcrumb';
import { buildBreadcrumbSegments } from '@/lib/breadcrumb-utils';

export function Breadcrumb() {
  const { pathname } = useLocation();
  const labelOverrides = useBreadcrumbLabels();
  const segments = buildBreadcrumbSegments(pathname, NAV_ROUTES, labelOverrides);

  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-sm text-muted-foreground">
      {segments.map((segment, i) => (
        <span key={segment.path} className="flex items-center gap-1">
          {i > 0 && <ChevronRight className="w-3.5 h-3.5 text-primary/60" />}
          {i < segments.length - 1 ? (
            <Link to={segment.path} className="transition-colors hover:text-primary">
              {segment.label}
            </Link>
          ) : (
            <span className="font-medium tracking-wide text-foreground">{segment.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}
```

### 5. Page Integration Example (Phase 3, Step 3.1)

**File**: `solune/frontend/src/pages/AppsPage.tsx`

Add dynamic label registration when viewing an app detail:

```typescript
import { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useBreadcrumb } from '@/hooks/useBreadcrumb';

// Inside the AppsPage component, when appName param is present:
const { appName } = useParams<{ appName: string }>();
const { setLabel, removeLabel } = useBreadcrumb();
const { data: app } = useAppDetail(appName); // existing hook

useEffect(() => {
  if (!appName) return;
  const path = `/apps/${appName}`;
  const label = app?.display_name ?? toTitleCase(appName);
  setLabel(path, label);
  return () => removeLabel(path);
}, [appName, app?.display_name, setLabel, removeLabel]);
```

## Validation

```bash
# Frontend lint + type check + test
cd solune/frontend
npm run lint
npm run type-check
npm run test -- --run

# Full test suite (Vitest)
cd solune/frontend
npx vitest run
```

## File Change Summary

| File | Change Type | Description |
|------|------------|-------------|
| `frontend/src/lib/breadcrumb-utils.ts` | NEW | `toTitleCase()` and `buildBreadcrumbSegments()` pure utility functions |
| `frontend/src/hooks/useBreadcrumb.ts` | NEW | `BreadcrumbContext`, `BreadcrumbProvider`, `useBreadcrumb()`, `useBreadcrumbLabels()` |
| `frontend/src/layout/Breadcrumb.tsx` | MODIFY | Rewrite to use `buildBreadcrumbSegments()` with context labels |
| `frontend/src/layout/AppLayout.tsx` | MODIFY | Wrap TopBar + Outlet with `BreadcrumbProvider` |
| `frontend/src/pages/AppsPage.tsx` | MODIFY | Add `useBreadcrumb().setLabel()` for dynamic app name display |

## Architecture Notes

- **No new dependencies** — uses built-in React Context, existing React Router hooks, existing NAV_ROUTES constant
- **2 new files** — `breadcrumb-utils.ts` (pure functions) and `useBreadcrumb.ts` (context + hooks)
- **3 modified files** — `Breadcrumb.tsx` (rewrite), `AppLayout.tsx` (add provider), `AppsPage.tsx` (add label registration)
- **Frontend-only** — no backend changes, no API endpoints, no database changes
- **Backward compatible** — existing two-segment breadcrumbs (e.g., "Home > Apps") continue to work identically; the change only adds depth and dynamic labels
- **Cleanup is automatic** — `useEffect` return function removes labels on unmount, preventing cross-route leakage
