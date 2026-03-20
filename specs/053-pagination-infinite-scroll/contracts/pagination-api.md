# Contracts: Pagination API

**Feature Branch**: `053-pagination-infinite-scroll`
**Date**: 2026-03-20

## Overview

This document defines the API contracts for paginated list endpoints. All endpoints follow the
same pattern: accept optional `limit` and `cursor` query parameters, return a `PaginatedResponse`
envelope. When pagination params are omitted, endpoints return the full list (backward-compatible).

## Shared Types

### PaginatedResponse\<T\> (Response Envelope)

```python
# Backend (Pydantic)
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None = None
    has_more: bool = False
    total_count: int | None = None
```

```typescript
// Frontend (TypeScript)
interface PaginatedResponse<T> {
  items: T[];
  next_cursor: string | null;
  has_more: boolean;
  total_count: number | null;
}
```

### Pagination Query Parameters

| Parameter | Type | Default | Constraints | Description |
|-----------|------|---------|-------------|-------------|
| `limit` | `int` | `25` | 1–100 | Maximum items per page |
| `cursor` | `str` | `None` | Valid base64 or `None` | Cursor from previous response's `next_cursor` |

---

## Endpoint Contracts

### 1. List Agents (Paginated)

**Endpoint**: `GET /api/v1/agents/{project_id}`

**Current response**: `list[Agent]`
**New response**: `PaginatedResponse[Agent]`

**Query Parameters**:
| Parameter | Type | Default |
|-----------|------|---------|
| `limit` | `int \| None` | `25` |
| `cursor` | `str \| None` | `None` |

**Response** (200):
```json
{
  "items": [
    {
      "id": "agent-001",
      "project_id": "proj-123",
      "slug": "code-reviewer",
      "display_name": "Code Reviewer",
      "model_name": "gpt-4"
    }
  ],
  "next_cursor": "YWdlbnQtMDI1",
  "has_more": true,
  "total_count": 100
}
```

**Error responses**:
- `400`: Invalid `cursor` format
- `401`: Unauthorized
- `422`: `limit` out of range (< 1 or > 100)

---

### 2. List Tools (Paginated)

**Endpoint**: `GET /api/v1/tools/{project_id}`

**Current response**: `McpToolConfigListResponse` (`{ tools: McpToolConfig[], presets?: McpPreset[] }`)
**New response**: `PaginatedResponse[McpToolConfig]` with `presets` included separately

**Query Parameters**:
| Parameter | Type | Default |
|-----------|------|---------|
| `limit` | `int \| None` | `25` |
| `cursor` | `str \| None` | `None` |

**Response** (200):
```json
{
  "items": [
    {
      "id": "tool-001",
      "name": "code-search",
      "server_url": "https://mcp.example.com"
    }
  ],
  "next_cursor": "dG9vbC0wMjU=",
  "has_more": true,
  "total_count": 60
}
```

**Note**: The `presets` field from `McpToolConfigListResponse` is returned in all pages (it is
not paginated — presets are few and needed for UI rendering on every page).

---

### 3. List Chores (Paginated)

**Endpoint**: `GET /api/v1/chores/{project_id}`

**Current response**: `list[Chore]`
**New response**: `PaginatedResponse[Chore]`

**Query Parameters**:
| Parameter | Type | Default |
|-----------|------|---------|
| `limit` | `int \| None` | `25` |
| `cursor` | `str \| None` | `None` |

**Response** (200):
```json
{
  "items": [
    {
      "id": "chore-001",
      "name": "daily-backup",
      "schedule": "0 0 * * *"
    }
  ],
  "next_cursor": "Y2hvcmUtMDI1",
  "has_more": true,
  "total_count": 50
}
```

---

### 4. List Apps (Paginated)

**Endpoint**: `GET /api/v1/apps`

**Current response**: `list[App]`
**New response**: `PaginatedResponse[App]`

**Query Parameters**:
| Parameter | Type | Default |
|-----------|------|---------|
| `limit` | `int \| None` | `25` |
| `cursor` | `str \| None` | `None` |

**Response** (200):
```json
{
  "items": [
    {
      "name": "slack-integration",
      "status": "installed",
      "version": "2.1.0"
    }
  ],
  "next_cursor": "c2xhY2staW50ZWdyYXRpb24=",
  "has_more": true,
  "total_count": 50
}
```

---

### 5. Board Data (Per-Column Pagination)

**Endpoint**: `GET /api/v1/board/data/{project_id}`

**Current response**: `BoardDataResponse` (all columns, all items)
**New response**: `BoardDataResponse` with per-column pagination fields

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `column_limit` | `int \| None` | `25` | Max items per column |
| `column_cursors` | `str \| None` | `None` | JSON-encoded map of `{ status_option_id: cursor }` |

**Response** (200):
```json
{
  "project": { "id": "proj-123", "name": "My Project" },
  "columns": [
    {
      "status": { "id": "status-backlog", "name": "Backlog" },
      "items": [ /* up to column_limit items */ ],
      "item_count": 150,
      "estimate_total": 300,
      "next_cursor": "aXRlbS0wMjU=",
      "has_more": true
    },
    {
      "status": { "id": "status-done", "name": "Done" },
      "items": [ /* all 10 items — fewer than column_limit */ ],
      "item_count": 10,
      "estimate_total": 20,
      "next_cursor": null,
      "has_more": false
    }
  ],
  "rate_limit": null
}
```

**Note**: `column_cursors` is a JSON string to pass through query params. Example:
`?column_cursors={"status-backlog":"aXRlbS0wMjU="}`

---

### 6. List Pipelines (Paginated)

**Endpoint**: `GET /api/v1/pipelines/{project_id}`

**Current response**: `PipelineConfigListResponse`
**New response**: `PaginatedResponse[PipelineConfig]`

**Query Parameters**:
| Parameter | Type | Default |
|-----------|------|---------|
| `limit` | `int \| None` | `20` |
| `cursor` | `str \| None` | `None` |

**Response** (200):
```json
{
  "items": [
    {
      "id": "pipeline-001",
      "name": "CI/CD Pipeline",
      "status": "active"
    }
  ],
  "next_cursor": "cGlwZWxpbmUtMDIw",
  "has_more": true,
  "total_count": 30
}
```

---

## Error Contract

All paginated endpoints share the same error responses for pagination-specific errors:

| Status | Condition | Response Body |
|--------|-----------|---------------|
| `400` | Invalid cursor (not valid base64 or references non-existent position) | `{ "detail": "Invalid pagination cursor" }` |
| `422` | `limit` out of range | `{ "detail": [{ "loc": ["query", "limit"], "msg": "ensure this value is between 1 and 100" }] }` |

Standard authentication and authorization errors (401, 403) remain unchanged.
