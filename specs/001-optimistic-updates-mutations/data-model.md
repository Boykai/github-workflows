# Data Model: Optimistic Updates for Mutations

**Feature**: 001-optimistic-updates-mutations  
**Date**: 2026-03-21

## Entities

### AgentConfig

**Source**: `solune/frontend/src/services/api.ts`  
**Cache key**: `['agents', 'list', projectId]` (flat) / `['agents', 'list', projectId, 'paginated']` (InfiniteData)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | string | Yes | Server-assigned; use `temp-${Date.now()}` for optimistic |
| name | string | Yes | User-provided |
| description | string | No | User-provided |
| icon_name | string \| null | No | User-provided or null |
| system_prompt | string | Yes | User-provided |
| tools | string[] | No | User-provided or [] |
| status | AgentStatus | Yes | Default `'pending_pr'` for optimistic creates |
| source | AgentSource | Yes | Default `'local'` for optimistic creates |
| status_column | string | No | User-provided or empty |
| default_model_id | string | No | User-provided |
| default_model_name | string | No | User-provided |
| created_at | string (ISO) | Yes | `new Date().toISOString()` for optimistic |
| updated_at | string (ISO) | Yes | `new Date().toISOString()` for optimistic |

**Optimistic placeholder construction** (create):
```typescript
{
  id: `temp-${Date.now()}`,
  name: data.name,
  description: data.description ?? '',
  icon_name: data.icon_name ?? null,
  system_prompt: data.system_prompt,
  tools: data.tools ?? [],
  status: 'pending_pr',
  source: 'local',
  status_column: data.status_column ?? '',
  default_model_id: data.default_model_id ?? '',
  default_model_name: data.default_model_name ?? '',
  created_at: now,
  updated_at: now,
  _optimistic: true,
}
```

### McpToolConfig

**Source**: `solune/frontend/src/types/index.ts`  
**Cache key**: `['tools', 'list', projectId]` (wrapper: `{ tools: McpToolConfig[] }`) / `['tools', 'list', projectId, 'paginated']` (InfiniteData)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | string | Yes | Server-assigned; use `temp-${Date.now()}` for optimistic |
| name | string | Yes | User-provided |
| description | string | No | From create data |
| command | string | Yes | User-provided |
| args | string[] | No | User-provided or [] |
| env | Record<string, string> | No | User-provided or {} |
| enabled | boolean | Yes | Default `true` |
| created_at | string (ISO) | Yes | Generated client-side |
| updated_at | string (ISO) | Yes | Generated client-side |

**Optimistic placeholder construction** (upload):
```typescript
{
  id: `temp-${Date.now()}`,
  name: data.name,
  description: data.description ?? '',
  command: data.command ?? '',
  args: data.args ?? [],
  env: data.env ?? {},
  enabled: true,
  created_at: now,
  updated_at: now,
  _optimistic: true,
}
```

### Project

**Source**: `solune/frontend/src/types/index.ts`  
**Cache key**: `['projects']` (wrapper: `{ projects: Project[] }`)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| project_id | string | Yes | Server-assigned; use `temp-${Date.now()}` for optimistic |
| owner_id | string | Yes | Unknown at create time; use empty string |
| owner_login | string | Yes | From `data.owner` |
| name | string | Yes | From `data.title` |
| type | ProjectType | Yes | Default `'ProjectV2'` |
| url | string | Yes | Placeholder empty string |
| description | string | No | Empty for create |
| status_columns | StatusColumn[] | Yes | Empty array for create |
| item_count | number | No | `0` for create |
| cached_at | string (ISO) | Yes | Generated client-side |

**Optimistic placeholder construction** (create):
```typescript
{
  project_id: `temp-${Date.now()}`,
  owner_id: '',
  owner_login: data.owner,
  name: data.title,
  type: 'ProjectV2',
  url: '',
  description: '',
  status_columns: [],
  item_count: 0,
  cached_at: now,
  _optimistic: true,
}
```

## Cache Structures

### Flat Array Cache

Used by: Agents list, Chores list, Apps list

```typescript
type FlatCache<T> = T[];
```

### Wrapper Object Cache

Used by: Tools list (`{ tools: McpToolConfig[] }`), Projects list (`{ projects: Project[] }`)

```typescript
type ToolsCache = { tools: McpToolConfig[] };
type ProjectsCache = { projects: Project[] };
```

### InfiniteData Cache (Paginated)

Used by: All paginated variants (agents, tools, chores, apps)

```typescript
import type { InfiniteData } from '@tanstack/react-query';
import type { PaginatedResponse } from '@/types';

type PaginatedCache<T> = InfiniteData<PaginatedResponse<T>>;
// Equivalent to:
// {
//   pages: Array<{
//     items: T[];
//     next_cursor: string | null;
//     has_more: boolean;
//     total_count: number | null;
//   }>;
//   pageParams: (string | undefined)[];
// }
```

## State Transitions

### Optimistic Mutation Lifecycle

```
IDLE → OPTIMISTIC → CONFIRMED | ROLLED_BACK
```

1. **IDLE**: No mutation in progress. Cache reflects server state.
2. **OPTIMISTIC**: `onMutate` fires. Cache updated with placeholder/removal. Snapshot stored in mutation context.
3. **CONFIRMED**: `onSuccess` fires. Toast shown. `onSettled` invalidates queries to reconcile.
4. **ROLLED_BACK**: `onError` fires. Cache restored from snapshot. Error toast shown. `onSettled` invalidates.

### Rollback Behavior

- Each mutation stores its own `{ snapshot, queryKey }` context (and `paginatedSnapshot`/`paginatedQueryKey` for paginated)
- Rollback restores both flat and paginated caches independently
- Rapid sequential mutations each have independent snapshots — rolling back mutation N only restores the cache state from just before mutation N fired
