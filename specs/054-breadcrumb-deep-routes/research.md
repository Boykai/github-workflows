# Research: Breadcrumb Deep Route Support

**Feature**: 054-breadcrumb-deep-routes  
**Date**: 2026-03-20  
**Status**: Complete — all unknowns resolved

## Research Tasks

### 1. React Context Pattern for Breadcrumb Labels

**Decision**: Use a single `BreadcrumbContext` with a `Map<string, string>` mapping path segments to display labels, exposed via a `useBreadcrumb()` hook.

**Rationale**: React Context is the idiomatic mechanism for sharing state across the component tree without prop drilling. A `Map<string, string>` keyed by full path (e.g., `/apps/my-cool-app`) is the simplest data structure that supports O(1) lookup, avoids collisions, and auto-cleans via `useEffect` cleanup. This pattern is already used in the codebase for other cross-cutting concerns (e.g., `useAuth`, `useAppTheme`).

**Alternatives considered**:
- **Zustand / external state**: Adds a new dependency for minimal state. Rejected — overkill for a simple Map.
- **Route loader data (React Router)**: Would couple breadcrumb labels to route definitions and require route refactoring. Rejected — the spec requires pages to inject labels dynamically after data loads.
- **URL search params**: Would pollute the URL and require encoding/decoding. Rejected — non-standard and user-visible.

### 2. Path Segment Parsing Strategy

**Decision**: Split `pathname` on `/`, filter empty segments (handles leading/trailing slashes), and build cumulative paths for each segment.

**Rationale**: This is the simplest approach with zero dependencies. `pathname.split('/')` produces `['', 'apps', 'my-cool-app']` — filtering empties gives `['apps', 'my-cool-app']`. Building cumulative paths (`/apps`, `/apps/my-cool-app`) is a single reduce operation.

**Alternatives considered**:
- **React Router's `useMatches()` or `matchRoutes()`**: Would provide structured match data but requires all routes to be defined with nested `<Route>` elements. The current routing setup uses flat routes with a catch-all, so `useMatches()` would not produce intermediate matches for unregistered sub-paths (e.g., `/apps/my-cool-app` has no explicit route definition for the `:appName` segment in a nested sense). Rejected — would require route refactoring beyond scope.
- **Third-party breadcrumb library (e.g., `use-react-router-breadcrumbs`)**: Adds a dependency and may not support the dynamic label injection pattern. Rejected — the logic is simple enough to implement directly.

### 3. Route Metadata Lookup for Known Segments

**Decision**: Build a lookup `Map<string, string>` from `NAV_ROUTES` at module level, mapping `path` → `label` (e.g., `/apps` → `"Apps"`). During breadcrumb construction, check this map first before falling back to title-casing.

**Rationale**: `NAV_ROUTES` already contains all needed path-to-label mappings. A `Map` provides O(1) lookup and is constructed once. No changes to `NAV_ROUTES` or `NavRoute` type are needed.

**Alternatives considered**:
- **Extending `NavRoute` with `breadcrumbLabel`**: Unnecessary indirection — the existing `label` field is the correct display name. Rejected.
- **Linear scan of `NAV_ROUTES` per segment**: Works but is O(n) per segment. Rejected in favor of pre-built Map for clarity, though the array is small enough that performance difference is negligible.

### 4. Title-Casing Fallback for Unknown Segments

**Decision**: Replace hyphens with spaces and capitalize the first letter of each word. Decode URI components before transformation.

**Rationale**: Covers the most common slug formats (kebab-case) used in the application's URL structure. URI decoding handles `%20` and other encoded characters per FR-003.

**Alternatives considered**:
- **No transformation (raw segment)**: Unfriendly for users. Rejected — spec explicitly requires human-readable fallback (FR-008).
- **Sentence case (capitalize first word only)**: Less readable for multi-word segments. Rejected.

### 5. Accessibility Implementation

**Decision**: Wrap breadcrumb in `<nav aria-label="Breadcrumb">` (already present), change inner container from `<span>` to `<ol>` with `<li>` children, add `aria-current="page"` to last segment, and hide separators with `aria-hidden="true"`.

**Rationale**: Follows WAI-ARIA Authoring Practices for breadcrumb navigation. The existing `<nav>` landmark is correct. Adding `<ol>`/`<li>` provides semantic list structure. `aria-current="page"` identifies the current location. `aria-hidden` on separators prevents screen readers from announcing decorative content.

**Alternatives considered**:
- **Using `role="list"` on a `<div>`**: Non-semantic, harder to maintain. Rejected in favor of native `<ol>`.
- **JSON-LD structured data**: Out of scope — this is a SPA, not an SEO-facing page. Rejected.

### 6. Context Cleanup on Navigation

**Decision**: Pages call `setLabel(path, label)` in a `useEffect` and return a cleanup function that calls `removeLabel(path)`. The `BreadcrumbProvider` holds the Map in state and exposes `setLabel`/`removeLabel` via context.

**Rationale**: This follows the standard React `useEffect` cleanup pattern. When a component unmounts (user navigates away), the cleanup fires and removes the dynamic label. This satisfies FR-011 (no stale labels after navigation).

**Alternatives considered**:
- **Automatic cleanup based on pathname**: Would require the provider to track which labels belong to which routes and clear them on navigation. More complex and error-prone. Rejected.
- **TTL-based expiration**: Over-engineered for this use case. Rejected.
