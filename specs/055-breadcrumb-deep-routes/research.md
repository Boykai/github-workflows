# Research: Breadcrumb Deep Route Support

**Feature**: `055-breadcrumb-deep-routes` | **Date**: 2026-03-21

## R1: Breadcrumb State Management Approach

**Decision**: Use React Context with a `Map<string, string>` for dynamic label registration.

**Rationale**: The breadcrumb needs a way for page components to inject human-readable labels for dynamic path segments (e.g., replacing the URL slug `my-cool-app` with the display name "My Cool App"). React Context is the standard mechanism for cross-component state sharing in React, and it's already used throughout the codebase (e.g., `useAuth`, `useChat`, `useWorkflow`).

The context stores a `Map<string, string>` mapping path segments (or full sub-paths) to human-readable labels. Components register labels via a `setLabel(path, label)` function and clean up via `removeLabel(path)` on unmount (using `useEffect` cleanup). The Map is simple, efficient for lookups, and naturally handles the "last writer wins" semantic required by the edge case where multiple components set labels for the same segment.

**Alternatives Considered**:
- **Zustand/Jotai store**: Rejected — adds an external dependency for a feature that only needs component-scoped ephemeral state. Constitution Principle V (Simplicity) favors built-in React APIs
- **URL state (search params)**: Rejected — breadcrumb labels are display-only metadata; encoding them in the URL would create ugly, shareable URLs with implementation details
- **React Router `handle` / loader data**: Rejected — React Router v7 supports route `handle` metadata, but the project uses `createRoutesFromElements` with JSX-based route definitions where `handle` is less ergonomic. Dynamic labels (from API responses) cannot be known at route definition time
- **Global event bus**: Rejected — violates React's unidirectional data flow; harder to debug and clean up than Context

## R2: Breadcrumb Segment Resolution Strategy

**Decision**: Three-tier label resolution: Context override → NAV_ROUTES label → title-case fallback.

**Rationale**: The breadcrumb needs to resolve a human-readable label for each path segment. The three tiers handle different scenarios:

1. **Context override** (highest priority): Page components provide entity-specific labels via `useBreadcrumb().setLabel()`. This handles dynamic segments like `:appName` where the label comes from an API response (e.g., the app's `display_name`).

2. **NAV_ROUTES label** (medium priority): The existing `NAV_ROUTES` array in `src/constants.ts` already maps paths like `/apps` to labels like "Apps". For known static routes, this ensures breadcrumb labels match the sidebar navigation labels (FR-006, SC-005).

3. **Title-case fallback** (lowest priority): For unknown segments with no context override and no route match, convert the URL slug to title case: replace hyphens and underscores with spaces, capitalize each word. This handles intermediate path segments and future routes that haven't been added to NAV_ROUTES yet (FR-007).

**Alternatives Considered**:
- **Only NAV_ROUTES + title-case**: Rejected — cannot handle dynamic labels from API data (the core P1 user story)
- **Route metadata (handle/meta)**: Rejected — see R1; cannot provide runtime-dynamic labels
- **Breadcrumb configuration object**: Rejected — would duplicate route definitions; NAV_ROUTES already serves as the static label source

## R3: Pathname Parsing Approach

**Decision**: Split `pathname` on `/`, filter empty segments, build cumulative paths.

**Rationale**: The implementation splits the pathname string by `/` to get individual segments. Empty strings (from leading slash or trailing slash) are filtered out. Each segment's cumulative path is built by joining all segments up to and including that index with `/` and prepending `/`.

For example, `/apps/my-cool-app/settings` produces:
- Segment "apps" → path `/apps`
- Segment "my-cool-app" → path `/apps/my-cool-app`
- Segment "settings" → path `/apps/my-cool-app/settings`

"Home" is always prepended as the first breadcrumb item linking to `/`.

Trailing slashes are stripped before splitting (FR-011). Query strings and hash fragments are ignored by using `useLocation().pathname` which excludes them by default (FR-010).

**Alternatives Considered**:
- **Regex-based path matching**: Rejected — over-engineered for simple path splitting; regex adds cognitive load without benefit
- **React Router's `matchRoutes()`**: Rejected — returns matched route objects but doesn't provide the intermediate segments needed for breadcrumbs. Only matches defined routes, not arbitrary path segments
- **URL constructor**: Rejected — `useLocation().pathname` already provides a clean pathname without query/hash; no need for additional URL parsing

## R4: Title-Case Utility Implementation

**Decision**: Simple string utility: split on hyphens/underscores, capitalize first letter of each word, join with spaces.

**Rationale**: The title-case fallback converts URL slugs like `my-cool-app` to "My Cool App". The implementation:

1. Split the segment string on `-` and `_`
2. Capitalize the first character of each resulting word
3. Join with spaces

This handles the common URL slug conventions used in the application. No external library (e.g., lodash `_.startCase`) is needed — the transformation is a 3-line function.

**Alternatives Considered**:
- **lodash/startCase**: Rejected — adds a dependency import for a trivial function; the codebase does not currently use lodash
- **CSS `text-transform: capitalize`**: Rejected — only capitalizes the first letter of each CSS word, doesn't handle hyphen/underscore replacement. Also, this needs to be a data transformation, not a visual one, since the label is used in accessibility attributes

## R5: Provider Placement in Component Tree

**Decision**: Wrap both `<TopBar />` and `<Outlet />` inside `<BreadcrumbProvider>` in `AppLayout`.

**Rationale**: The `Breadcrumb` component lives inside `TopBar`, and page components that call `useBreadcrumb().setLabel()` render inside `<Outlet />`. Both need access to the same context instance. `AppLayout` is the common ancestor that wraps both:

```text
AppLayout
  └── BreadcrumbProvider      ← provider here
        ├── TopBar
        │     └── Breadcrumb  ← reads labels from context
        └── Outlet
              └── AppsPage    ← sets labels via context
```

This ensures the context is available to both producers (pages) and consumers (Breadcrumb) without being too high in the tree (which would cause unnecessary re-renders of unrelated components).

**Alternatives Considered**:
- **Root-level provider (in App.tsx)**: Rejected — `App.tsx` uses `createBrowserRouter` with JSX route elements; adding a provider there would wrap the login page too, which doesn't need breadcrumbs
- **Inside TopBar**: Rejected — page components (producers) render outside TopBar's subtree and wouldn't have access to the context
- **Inside Breadcrumb component**: Rejected — same issue; producers can't reach a context defined inside the consumer

## R6: Cleanup Strategy for Dynamic Labels

**Decision**: `useBreadcrumb` hook returns `setLabel` and `removeLabel`; page components use `useEffect` cleanup to call `removeLabel` on unmount.

**Rationale**: When a user navigates from `/apps/my-cool-app` to `/apps`, the `AppsPage` component re-renders (or the detail view unmounts). The dynamic label "My Cool App" must be removed from the context so it doesn't appear when navigating to a different app or back to the apps list.

The standard React pattern is `useEffect(() => { setLabel(path, name); return () => removeLabel(path); }, [path, name])`. This ties label lifecycle to component lifecycle, which is exactly the desired behavior (FR-008).

The `removeLabel` function deletes the entry from the Map. If a component unmounts and a new component mounts for a different route, the old label is cleaned up before the new one is set.

**Alternatives Considered**:
- **Automatic cleanup based on pathname changes**: Rejected — would clear ALL labels on every navigation, including labels set by parent components for intermediate segments
- **TTL-based expiration**: Rejected — adds complexity; React's component lifecycle already provides deterministic cleanup
- **Weak references**: Rejected — `WeakMap` requires object keys; path strings are primitive values. Also adds unnecessary complexity

## R7: Existing Breadcrumb Component Compatibility

**Decision**: The existing `Breadcrumb` component will be rewritten in-place (same file, same export name), not replaced with a new component.

**Rationale**: The `Breadcrumb` component is imported in `TopBar.tsx` as `import { Breadcrumb } from './Breadcrumb'`. The rewrite maintains the same export interface (`export function Breadcrumb()`) so no import changes are needed in consuming files.

The internal implementation changes from:
- Old: `NAV_ROUTES.find(r => pathname.startsWith(r.path))` → max 2 segments
- New: `buildBreadcrumbSegments(pathname, NAV_ROUTES, contextLabels)` → arbitrary segments

The JSX rendering structure (nav > spans with ChevronRight separators, Link for non-final segments, plain text for final segment) is preserved to maintain the existing visual design and accessibility attributes.

**Alternatives Considered**:
- **New component alongside old**: Rejected — creates dead code; the old component has no other use
- **Higher-order component wrapper**: Rejected — unnecessary indirection; a direct rewrite is simpler and more readable
