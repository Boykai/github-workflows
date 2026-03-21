# Quickstart: Breadcrumb Deep Route Support

**Feature**: 054-breadcrumb-deep-routes  
**Date**: 2026-03-20

## Overview

This guide walks through implementing the breadcrumb deep route support feature. The implementation is frontend-only and touches 3 files (1 new, 2 modified).

## Prerequisites

- Node.js 18+ and npm
- Repository cloned and dependencies installed: `cd solune/frontend && npm ci`
- Familiarity with React Context, React Router DOM v6, and the existing `Breadcrumb.tsx`

## Implementation Order

### Step 1: Create `useBreadcrumb.ts` Hook

**File**: `solune/frontend/src/hooks/useBreadcrumb.ts` (NEW)

Create the `BreadcrumbContext`, `BreadcrumbProvider`, and `useBreadcrumb` hook:

1. Define `BreadcrumbContextValue` interface with `labels`, `setLabel`, `removeLabel`.
2. Create context with `createContext<BreadcrumbContextValue | null>(null)`.
3. Implement `BreadcrumbProvider` component:
   - Hold `Map<string, string>` in `useState` (use a new `Map` instance on each update for React immutability).
   - Wrap `setLabel` and `removeLabel` in `useCallback` for stable references.
   - Provide context value via `<BreadcrumbContext.Provider>`.
4. Export `useBreadcrumb()` hook that reads context and throws if outside provider.

### Step 2: Wrap Layout with BreadcrumbProvider

**File**: `solune/frontend/src/layout/AppLayout.tsx` (MODIFY)

1. Import `BreadcrumbProvider` from `@/hooks/useBreadcrumb`.
2. Wrap the `<Outlet />` and its surrounding content container with `<BreadcrumbProvider>`.
3. The `TopBar` (which contains `Breadcrumb`) must also be inside the provider scope.

### Step 3: Rewrite `Breadcrumb.tsx`

**File**: `solune/frontend/src/layout/Breadcrumb.tsx` (MODIFY)

1. Build a static `routeLabels` map from `NAV_ROUTES` (path → label) at module level.
2. Add `toTitleCase(segment)` helper: replace hyphens with spaces, capitalize each word.
3. Add `buildSegments(pathname, routeLabels, dynamicLabels)` function:
   - Strip trailing slash, split on `/`, filter empties.
   - For each segment, build cumulative path and resolve label (dynamic → route → title-case).
   - Prepend Home segment, mark last as current.
4. In the component:
   - Read `labels` from `useBreadcrumb()` (with fallback for when provider is absent).
   - Call `buildSegments()` with current pathname.
   - Render `<nav>` → `<ol>` → `<li>` items with proper accessibility attributes.

### Step 4: Integrate Dynamic Labels in Pages (Example)

**File**: `solune/frontend/src/pages/AppsPage.tsx` (MODIFY)

1. Import `useBreadcrumb` hook.
2. In the component, when app data is available, call `setLabel` with the app's path and display name.
3. Return `removeLabel` in `useEffect` cleanup.

## Verification

```bash
# Type-check
cd solune/frontend && npx tsc --noEmit

# Run tests
cd solune/frontend && npx vitest run

# Manual testing
# 1. Navigate to /apps — expect "Home > Apps"
# 2. Navigate to /apps/my-cool-app — expect "Home > Apps > My Cool App"
# 3. Navigate to /agents — expect "Home > Agents"
# 4. Inspect with screen reader: verify nav landmark, ordered list, aria-current
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| React Context (not Zustand) | No new dependency; Map state is simple enough for context |
| Path-based key in labels Map | Full paths are unique; avoids collisions between `/apps/foo` and `/agents/foo` |
| `useEffect` cleanup for label removal | Idiomatic React; automatic on unmount or dependency change |
| Internal `buildSegments()` as pure function | Easy to unit test; separates logic from rendering |
| `<ol>` instead of `<span>` wrapper | Semantic HTML for breadcrumb per WAI-ARIA best practices |

## Files Changed Summary

| File | Action | Description |
|------|--------|-------------|
| `solune/frontend/src/hooks/useBreadcrumb.ts` | NEW | Context provider + hook for dynamic breadcrumb labels |
| `solune/frontend/src/layout/Breadcrumb.tsx` | MODIFY | Full-depth parsing, route metadata, accessibility |
| `solune/frontend/src/layout/AppLayout.tsx` | MODIFY | Wrap with `BreadcrumbProvider` |
| `solune/frontend/src/pages/AppsPage.tsx` | MODIFY | Example integration of dynamic label |
