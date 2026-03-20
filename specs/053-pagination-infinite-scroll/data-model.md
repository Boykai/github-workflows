# Data Model: Pagination & Infinite Scroll for All List Views

**Feature Branch**: `053-pagination-infinite-scroll`
**Date**: 2026-03-20
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Overview

This feature introduces a generic paginated response envelope used across all list endpoints.
No new database tables are created — pagination operates on existing data by slicing query
results. The entities below represent the API response shapes and the conceptual objects that
manage pagination state on both backend and frontend.

## Entities

### 1. PaginatedResponse\<T\> (Backend — Pydantic Generic Model)

The universal response envelope for all paginated list endpoints. Wraps any item type `T`.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `items` | `list[T]` | The current page of results | Length ≤ `limit` (page size) |
| `next_cursor` | `str \| None` | Opaque cursor for the next page | Base64-encoded sort key; `None` when no more pages |
| `has_more` | `bool` | Whether additional pages exist beyond this response | `True` if `next_cursor` is not `None` |
| `total_count` | `int \| None` | Total number of items matching the query (optional) | ≥ 0; may be `None` if count is expensive |

**Relationships**:
- A `PaginatedResponse` *wraps* a page of items of any entity type (`Agent`, `McpToolConfig`, `Chore`, `App`, `BoardItem`, `PipelineConfig`).
- A `PaginatedResponse` *links to* the next page via `next_cursor`.

**Validation rules**:
- `items` length must be ≤ the requested `limit`.
- When `has_more` is `False`, `next_cursor` must be `None`.
- When `has_more` is `True`, `next_cursor` must be a non-empty string.
- `total_count`, if provided, must be ≥ the count of items across all pages.

**Example (JSON)**:
```json
{
  "items": [
    { "id": "agent-001", "slug": "code-reviewer", "display_name": "Code Reviewer" },
    { "id": "agent-002", "slug": "test-writer", "display_name": "Test Writer" }
  ],
  "next_cursor": "YWdlbnQtMDAy",
  "has_more": true,
  "total_count": 100
}
```

---

### 2. PaginationParams (Backend — Query Parameter Model)

The input parameters accepted by paginated endpoints.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `limit` | `int \| None` | Maximum number of items to return per page | 1–100; defaults to 25 when `None` |
| `cursor` | `str \| None` | Opaque cursor from a previous `PaginatedResponse.next_cursor` | Valid base64 string or `None` for first page |

**Validation rules**:
- `limit` must be between 1 and 100 (inclusive) when provided.
- `cursor` must be a valid base64-encoded string when provided; invalid cursors return a 400 error.
- When both are `None`, the endpoint returns the first page with default page size.

---

### 3. PaginatedResponse\<T\> (Frontend — TypeScript Generic Type)

The TypeScript equivalent of the backend model, used for type-safe API responses.

```typescript
interface PaginatedResponse<T> {
  items: T[];
  next_cursor: string | null;
  has_more: boolean;
  total_count: number | null;
}
```

**Usage**: All paginated API fetch functions return `PaginatedResponse<T>` where `T` is the
specific item type (`AgentConfig`, `McpToolConfig`, `Chore`, `App`, `BoardItem`, etc.).

---

### 4. BoardColumn (Modified — adds pagination fields)

The existing `BoardColumn` type is extended with pagination metadata per column.

| Field | Type | Description | Change |
|-------|------|-------------|--------|
| `status` | `BoardStatusOption` | Column status identifier | Existing — no change |
| `items` | `BoardItem[]` | Items in this column (current page) | Existing — now represents current loaded page(s) |
| `item_count` | `number` | Total items in this column | Existing — no change |
| `estimate_total` | `number` | Sum of estimates | Existing — no change |
| `next_cursor` | `string \| null` | Cursor for next page of items in this column | **NEW** |
| `has_more` | `boolean` | Whether more items exist in this column | **NEW** |

**Relationships**:
- A `BoardColumn` *belongs to* one `BoardDataResponse`.
- A `BoardColumn` *contains* zero or more `BoardItem` entries (paginated).
- A `BoardColumn` *links to* its next page via `next_cursor`.

---

### 5. InfiniteQueryState (Frontend — Conceptual)

The state managed by TanStack Query's `useInfiniteQuery` for each paginated list. This is not a
custom type — it's the built-in state shape provided by the library, documented here for clarity.

| Field | Type | Description |
|-------|------|-------------|
| `pages` | `PaginatedResponse<T>[]` | Array of all loaded pages |
| `pageParams` | `(string \| undefined)[]` | Array of cursors used to fetch each page |
| `hasNextPage` | `boolean` | Whether more pages can be fetched |
| `isFetchingNextPage` | `boolean` | Whether the next page is currently being fetched |
| `isError` | `boolean` | Whether the last fetch failed |
| `error` | `Error \| null` | Error details if fetch failed |

**Derived data**:
- `allItems`: Flattened array of all items across all loaded pages (`pages.flatMap(p => p.items)`).
- `totalCount`: From the first page's `total_count` field (consistent across pages).

## State Transitions

### Pagination Lifecycle (per list view)

```text
[Initial Load] → [First Page Loaded] → [User Scrolls] → [Next Page Loading]
                                                              ↓
                                                    [Next Page Loaded] → [User Scrolls] → ...
                                                              ↓
                                                    [All Pages Loaded] (has_more = false)
```

- **Initial Load**: `useInfiniteQuery` fires with no cursor → backend returns first page.
- **First Page Loaded**: Items render; `InfiniteScrollContainer` sentinel is placed after last item.
- **User Scrolls**: `IntersectionObserver` detects sentinel → calls `fetchNextPage()`.
- **Next Page Loading**: Loading indicator shown; existing items remain visible.
- **Next Page Loaded**: New items appended below existing; sentinel moves to new bottom.
- **All Pages Loaded**: `has_more=false` → sentinel removed, no loading indicator.

### Error Recovery

```text
[Next Page Loading] → [Fetch Failed] → [Error Displayed + Retry Button]
                                              ↓ (user clicks retry)
                                        [Next Page Loading] → [Next Page Loaded]
```

- Failed page fetches display an error with retry button.
- Already-loaded pages remain visible and interactive.
- Retry re-attempts the same cursor, not a fresh query.

### Filter/Sort Reset

```text
[Multiple Pages Loaded] → [User Changes Filter/Sort] → [Query Reset]
                                                              ↓
                                                    [Initial Load] (back to first page)
```

- Filter or sort changes trigger `queryClient.resetQueries()` for the affected query key.
- All loaded pages are discarded; the list resets to the first page with new params.

## Relationship Diagram

```text
┌─────────────────────┐
│   PaginationParams  │
│ (limit, cursor)     │
└────────┬────────────┘
         │ request
         ▼
┌─────────────────────┐     wraps      ┌──────────────────┐
│  Backend Service     │──────────────▶│ PaginatedResponse │
│  apply_pagination()  │               │ (items, cursor,   │
└─────────────────────┘               │  has_more, total) │
                                       └────────┬─────────┘
                                                │ response
                                                ▼
                                       ┌──────────────────┐
                                       │ useInfiniteList   │
                                       │ (useInfiniteQuery │
                                       │  wrapper)         │
                                       └────────┬─────────┘
                                                │ provides
                                                ▼
                                       ┌──────────────────────────┐
                                       │ InfiniteScrollContainer  │
                                       │ (IntersectionObserver    │
                                       │  + loading/error states) │
                                       └──────────────────────────┘
```
