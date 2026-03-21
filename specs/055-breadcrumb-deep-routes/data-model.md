# Data Model: Breadcrumb Deep Route Support

**Feature**: `055-breadcrumb-deep-routes` | **Date**: 2026-03-21

## Entities

### BreadcrumbSegment (new — runtime type)

Represents a single segment in the rendered breadcrumb trail. Produced by the `buildBreadcrumbSegments()` utility function.

| Field | Type | Description |
|-------|------|-------------|
| `label` | `string` | Human-readable display text for this segment |
| `path` | `string` | Cumulative URL path for navigation (e.g., `/apps/my-cool-app`) |

**Source**: To be defined in `solune/frontend/src/lib/breadcrumb-utils.ts`

### BreadcrumbContextValue (new — React context type)

The shape of the value provided by `BreadcrumbContext`. Consumed by the `Breadcrumb` component to read label overrides, and by page components to register/unregister labels.

| Field | Type | Description |
|-------|------|-------------|
| `labels` | `Map<string, string>` | Mapping of cumulative path → human-readable label override. Keys are paths like `/apps/my-cool-app`; values are display names like "My Cool App" |
| `setLabel` | `(path: string, label: string) => void` | Register a label override for a specific path segment |
| `removeLabel` | `(path: string) => void` | Remove a label override (used on component unmount) |

**Source**: To be defined in `solune/frontend/src/hooks/useBreadcrumb.ts`

### NavRoute (existing — no changes)

Existing route configuration used by the sidebar and now also by breadcrumb label resolution.

| Field | Type | Description |
|-------|------|-------------|
| `path` | `string` | Route path (e.g., `/apps`, `/settings`) |
| `label` | `string` | Human-readable label (e.g., "Apps", "Settings") |
| `icon` | `React.ComponentType<{ className?: string }>` | Lucide icon component |

**Source**: `solune/frontend/src/types/index.ts` (line 1042)

### NAV_ROUTES (existing — no changes)

Static array of `NavRoute` entries. Used as the second-tier label source for breadcrumb resolution.

**Entries**:
| Path | Label |
|------|-------|
| `/` | App |
| `/projects` | Projects |
| `/pipeline` | Agents Pipelines |
| `/agents` | Agents |
| `/tools` | Tools |
| `/chores` | Chores |
| `/apps` | Apps |
| `/activity` | Activity |
| `/settings` | Settings |

**Source**: `solune/frontend/src/constants.ts` (lines 76–85)

## Relationships

```text
BreadcrumbProvider (AppLayout)
  ├── provides BreadcrumbContextValue
  │     ├── labels: Map<string, string>
  │     ├── setLabel()
  │     └── removeLabel()
  │
  ├── consumed by Breadcrumb (in TopBar)
  │     └── reads labels Map
  │         └── passes to buildBreadcrumbSegments()
  │               └── produces BreadcrumbSegment[]
  │
  └── consumed by Page components (in Outlet)
        └── calls setLabel() / removeLabel()
```

## Label Resolution Flow

```text
For each path segment:

  1. Check BreadcrumbContextValue.labels.get(cumulativePath)
     ├── Found → use context label
     └── Not found ↓

  2. Check NAV_ROUTES.find(r => r.path === cumulativePath)
     ├── Found → use route.label
     └── Not found ↓

  3. Apply toTitleCase(segment)
     └── "my-cool-app" → "My Cool App"
```

## State Lifecycle

### Label Registration (dynamic page mount)

```text
Page mounts (e.g., AppsPage with :appName param)
  → useEffect calls setLabel('/apps/my-cool-app', 'My Cool App')
  → BreadcrumbContext.labels Map updated
  → Breadcrumb component re-renders with new label
```

### Label Cleanup (dynamic page unmount)

```text
User navigates away (e.g., /apps/my-cool-app → /apps)
  → useEffect cleanup calls removeLabel('/apps/my-cool-app')
  → BreadcrumbContext.labels Map entry deleted
  → Breadcrumb component re-renders without the stale label
```

### Label Update (data arrives after mount)

```text
Page mounts → initial render with title-cased fallback
  → API response arrives with entity name
  → useEffect dependency change triggers setLabel() with real name
  → Breadcrumb re-renders with human-readable label
```

## No Backend Data Model Changes

This feature is entirely frontend. No database schemas, API request/response models, or backend entities are affected. The breadcrumb state is ephemeral (exists only in React context during the session) and is not persisted.
