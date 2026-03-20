# Component Contracts: Breadcrumb Deep Route Support

**Feature**: 054-breadcrumb-deep-routes  
**Date**: 2026-03-20

This feature is frontend-only with no REST/GraphQL API changes. The contracts below define the component interfaces (props, context values, and hook signatures) that form the public API of the breadcrumb system.

---

## 1. BreadcrumbProvider

**File**: `solune/frontend/src/hooks/useBreadcrumb.ts`  
**Type**: React Context Provider component

### Props

```typescript
interface BreadcrumbProviderProps {
  children: React.ReactNode;
}
```

### Context Value

```typescript
interface BreadcrumbContextValue {
  /** Map of full path → custom display label */
  labels: Map<string, string>;
  /** Register a dynamic label for a path */
  setLabel: (path: string, label: string) => void;
  /** Remove a previously registered dynamic label */
  removeLabel: (path: string) => void;
}
```

### Usage Contract

- `BreadcrumbProvider` MUST wrap the component tree that contains both the `Breadcrumb` component and any page components that inject labels.
- Placement: Inside `AppLayout`, wrapping the `<Outlet />`.
- There MUST be exactly one `BreadcrumbProvider` in the component tree.

---

## 2. useBreadcrumb Hook

**File**: `solune/frontend/src/hooks/useBreadcrumb.ts`  
**Type**: Custom React hook

### Signature

```typescript
function useBreadcrumb(): BreadcrumbContextValue;
```

### Contract

- Returns the current `BreadcrumbContextValue` from the nearest `BreadcrumbProvider`.
- Throws if called outside a `BreadcrumbProvider` (standard React context behavior).
- Pages SHOULD call `setLabel` inside a `useEffect` and return `removeLabel` in the cleanup function.

### Usage Example

```typescript
import { useBreadcrumb } from '@/hooks/useBreadcrumb';

function AppDetailPage({ appName }: { appName: string }) {
  const { setLabel, removeLabel } = useBreadcrumb();
  const app = useAppData(appName); // hypothetical data hook

  useEffect(() => {
    if (app?.displayName) {
      const path = `/apps/${appName}`;
      setLabel(path, app.displayName);
      return () => removeLabel(path);
    }
  }, [app?.displayName, appName, setLabel, removeLabel]);

  return <div>...</div>;
}
```

---

## 3. Breadcrumb Component (modified)

**File**: `solune/frontend/src/layout/Breadcrumb.tsx`  
**Type**: React functional component

### Props

```typescript
// No props — reads pathname from useLocation() and labels from useBreadcrumb()
```

### Rendered Output Contract

```html
<nav aria-label="Breadcrumb">
  <ol class="flex items-center gap-1 ...">
    <!-- For each segment except last -->
    <li class="flex items-center gap-1">
      <a href="/path">Label</a>
      <ChevronRight aria-hidden="true" />
    </li>
    <!-- Last segment (current page) -->
    <li class="flex items-center gap-1">
      <span aria-current="page">Current Label</span>
    </li>
  </ol>
</nav>
```

### Behavior Contract

| Input | Behavior |
|-------|----------|
| `pathname = "/"` | Renders single segment: "Home" (current page, no link) |
| `pathname = "/apps"` | Renders: Home (link) → Apps (current) |
| `pathname = "/apps/my-cool-app"` | Renders: Home (link) → Apps (link) → My Cool App (current) |
| `pathname = "/apps/my-cool-app/"` | Same as above (trailing slash stripped) |
| `pathname = "/apps/my%20cool%20app"` | Decodes to "my cool app", title-cases to "My Cool App" |
| Dynamic label set for `/apps/my-cool-app` = "My App" | Renders: Home → Apps → My App |

### Label Resolution Priority

1. Dynamic label from `BreadcrumbContext.labels` (highest priority)
2. Route metadata label from `NAV_ROUTES` (for known route paths)
3. Title-cased raw segment with hyphens replaced by spaces (fallback)

---

## 4. Segment Building Utility

**File**: `solune/frontend/src/layout/Breadcrumb.tsx` (internal)  
**Type**: Pure function (not exported)

### Signature

```typescript
function buildSegments(
  pathname: string,
  routeLabels: Map<string, string>,
  dynamicLabels: Map<string, string>,
): BreadcrumbSegment[];
```

### Contract

- Always returns at least one segment (Home).
- Strips trailing slashes.
- Decodes URI components.
- Filters empty segments.
- Marks the last segment as `isCurrent: true`.

---

## 5. Title-Case Utility

**File**: `solune/frontend/src/layout/Breadcrumb.tsx` (internal)  
**Type**: Pure function (not exported)

### Signature

```typescript
function toTitleCase(segment: string): string;
```

### Contract

- Replaces hyphens with spaces.
- Capitalizes the first letter of each word.
- Example: `"my-cool-app"` → `"My Cool App"`.
- Example: `"settings"` → `"Settings"`.
