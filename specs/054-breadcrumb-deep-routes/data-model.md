# Data Model: Breadcrumb Deep Route Support

**Feature**: 054-breadcrumb-deep-routes  
**Date**: 2026-03-20

## Entities

### BreadcrumbSegment

Represents a single item in the rendered breadcrumb trail.

| Field | Type | Description |
|-------|------|-------------|
| `label` | `string` | Display text for this segment |
| `path` | `string` | The URL path this segment links to (e.g., `/apps`) |
| `isCurrent` | `boolean` | Whether this is the last (current page) segment |

**Notes**: This is a derived/computed type — not stored anywhere. It is built on each render from the pathname, route metadata, and dynamic labels.

### BreadcrumbContextValue

The shape of the React context value exposed by `BreadcrumbProvider`.

| Field | Type | Description |
|-------|------|-------------|
| `labels` | `Map<string, string>` | Maps full path → display label (e.g., `/apps/my-cool-app` → `"My Cool App"`) |
| `setLabel` | `(path: string, label: string) => void` | Registers a dynamic label for a given path |
| `removeLabel` | `(path: string) => void` | Removes a previously registered dynamic label |

### NavRoute (existing — no changes)

| Field | Type | Description |
|-------|------|-------------|
| `path` | `string` | Route path (e.g., `/apps`) |
| `label` | `string` | Display label (e.g., `"Apps"`) |
| `icon` | `React.ComponentType<{ className?: string }>` | Lucide icon component |

## Data Flow

```text
URL pathname ──────────────────┐
                               ▼
                     ┌──────────────────┐
                     │  Split on "/"    │
                     │  Filter empties  │
                     │  Decode URI      │
                     └────────┬─────────┘
                              │ raw segments
                              ▼
              ┌───────────────────────────────┐
              │  For each segment:            │
              │  1. Check dynamic labels Map  │
              │  2. Check NAV_ROUTES lookup   │
              │  3. Fallback: title-case      │
              └───────────────┬───────────────┘
                              │ BreadcrumbSegment[]
                              ▼
                   ┌─────────────────────┐
                   │  Prepend "Home" /   │
                   │  Mark last as       │
                   │  isCurrent          │
                   └─────────────────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │  Render <ol>        │
                   │  with <li> items    │
                   └─────────────────────┘
```

## State Transitions

### Dynamic Label Lifecycle

```text
┌─────────────────┐
│  No label set   │  (fallback: title-cased segment)
└────────┬────────┘
         │ Page mounts, calls setLabel(path, label)
         ▼
┌─────────────────┐
│  Label active   │  (breadcrumb shows dynamic label)
└────────┬────────┘
         │ Page unmounts (useEffect cleanup calls removeLabel)
         ▼
┌─────────────────┐
│  No label set   │  (reverts to fallback)
└─────────────────┘
```

## Validation Rules

- Path segments must be non-empty strings after filtering
- Dynamic labels must be non-empty strings
- Trailing slashes are stripped before processing
- URL-encoded characters are decoded via `decodeURIComponent()`
- The "Home" segment is always present and always links to `/`
- Maximum expected depth: 5 segments (not enforced, just a design assumption)

## Relationships

```text
BreadcrumbProvider (1) ──provides──▶ BreadcrumbContextValue (1)
     │
     └── wraps ──▶ AppLayout.Outlet (component tree)

BreadcrumbContextValue.labels (Map)
     │
     └── consumed by ──▶ Breadcrumb component (reads labels)
     └── modified by ──▶ Page components via useBreadcrumb() hook

NAV_ROUTES (static array)
     │
     └── consumed by ──▶ Breadcrumb component (route label lookup)
     └── consumed by ──▶ Sidebar component (navigation links)
```
