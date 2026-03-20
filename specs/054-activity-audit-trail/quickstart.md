# Quickstart: Activity Log / Audit Trail

**Feature**: `054-activity-audit-trail` | **Date**: 2026-03-20

## Overview

This guide provides a rapid implementation path for the Activity Log / Audit Trail feature. It covers the minimum viable implementation for each phase, with references to the detailed plan and data model.

## Prerequisites

- Existing Solune backend running with SQLite database
- Existing Solune frontend with React + TanStack Query
- Familiarity with the codebase patterns (see [plan.md](./plan.md) § Technical Context)

## Phase 1 — Backend Foundation (Stories 1, 2, 3)

### Step 1: Database Migration

Create `solune/backend/src/migrations/032_activity_events.sql`:

```sql
CREATE TABLE IF NOT EXISTS activity_events (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    actor TEXT NOT NULL DEFAULT 'system',
    action TEXT NOT NULL,
    summary TEXT NOT NULL,
    detail TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_activity_project_time
    ON activity_events (project_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_activity_entity
    ON activity_events (entity_type, entity_id);
```

### Step 2: Pydantic Models

Create `solune/backend/src/models/activity.py`:

```python
from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field

class ActivityEvent(BaseModel):
    id: str
    event_type: str
    entity_type: str
    entity_id: str
    project_id: str
    actor: str
    action: str
    summary: str
    detail: dict[str, Any] | None = None
    created_at: str

class ActivityEventCreate(BaseModel):
    event_type: str
    entity_type: str
    entity_id: str
    project_id: str
    actor: str = "system"
    action: str
    summary: str
    detail: dict[str, Any] | None = None
```

### Step 3: Activity Logger Service

Create `solune/backend/src/services/activity_logger.py`:

```python
import json
import logging
import uuid
from typing import Any
import aiosqlite

logger = logging.getLogger(__name__)

async def log_event(
    db: aiosqlite.Connection,
    *,
    event_type: str,
    entity_type: str,
    entity_id: str,
    project_id: str,
    actor: str = "system",
    action: str,
    summary: str,
    detail: dict[str, Any] | None = None,
) -> None:
    """Fire-and-forget activity event logging. Never raises."""
    try:
        event_id = str(uuid.uuid4())
        detail_json = json.dumps(detail) if detail else None
        await db.execute(
            """INSERT INTO activity_events
               (id, event_type, entity_type, entity_id, project_id, actor, action, summary, detail)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (event_id, event_type, entity_type, entity_id, project_id, actor, action, summary, detail_json),
        )
        await db.commit()
    except Exception:
        logger.exception("Activity logging failed (non-fatal)")
```

### Step 4: Activity Feed API

Create `solune/backend/src/api/activity.py`:

```python
from fastapi import APIRouter, Depends, Query
from typing import Annotated
# ... implement GET /activity and GET /activity/{entity_type}/{entity_id}
# See contracts/activity-api.yaml for full endpoint specification
```

Register in `solune/backend/src/api/__init__.py`:

```python
from src.api.activity import router as activity_router
router.include_router(activity_router, prefix="/activity", tags=["activity"])
```

### Step 5: Instrument Existing Flows

Add `log_event()` calls to existing route handlers. Example for pipeline runs:

```python
# In api/pipelines.py, after a pipeline run is created:
await log_event(
    db,
    event_type="pipeline_run",
    entity_type="pipeline",
    entity_id=pipeline_id,
    project_id=project_id,
    actor=session.github_username,
    action="started",
    summary=f"Pipeline '{pipeline_name}' started",
)
```

## Phase 2 — Frontend (Stories 1, 2, 3)

### Step 6: TypeScript Types

Add to `solune/frontend/src/types/index.ts`:

```typescript
export interface ActivityEvent {
  id: string;
  event_type: string;
  entity_type: string;
  entity_id: string;
  project_id: string;
  actor: string;
  action: string;
  summary: string;
  detail?: Record<string, unknown>;
  created_at: string;
}
```

### Step 7: API Client

Add to `solune/frontend/src/services/api.ts`:

```typescript
activity: {
  feed: (projectId: string, params?: { limit?: number; cursor?: string; event_type?: string }) =>
    fetchApi<PaginatedResponse<ActivityEvent>>(
      `/activity?project_id=${projectId}${params?.limit ? `&limit=${params.limit}` : ''}${params?.cursor ? `&cursor=${params.cursor}` : ''}${params?.event_type ? `&event_type=${params.event_type}` : ''}`
    ),
  entityHistory: (entityType: string, entityId: string, params?: { limit?: number; cursor?: string }) =>
    fetchApi<PaginatedResponse<ActivityEvent>>(
      `/activity/${entityType}/${entityId}${params?.limit ? `?limit=${params.limit}` : ''}${params?.cursor ? `${params?.limit ? '&' : '?'}cursor=${params.cursor}` : ''}`
    ),
},
```

### Step 8: Activity Feed Hook

Create `solune/frontend/src/hooks/useActivityFeed.ts`:

```typescript
import { useInfiniteList } from './useInfiniteList';
import { api } from '@/services/api';
import type { ActivityEvent } from '@/types';

export function useActivityFeed(projectId: string, eventTypes?: string[]) {
  const eventTypeParam = eventTypes?.length ? eventTypes.join(',') : undefined;
  return useInfiniteList<ActivityEvent>({
    queryKey: ['activity', projectId, eventTypeParam],
    queryFn: ({ limit, cursor }) =>
      api.activity.feed(projectId, { limit, cursor, event_type: eventTypeParam }),
    limit: 50,
    staleTime: 30_000,
    enabled: !!projectId,
  });
}
```

### Step 9: Activity Page + Route

Create `solune/frontend/src/pages/ActivityPage.tsx` with filter chips and infinite scroll timeline.

Add route in `App.tsx`:

```typescript
<Route path="activity" element={<ActivityPage />} />
```

Add to `NAV_ROUTES` in `constants.ts`:

```typescript
{ path: '/activity', label: 'Activity', icon: Clock },
```

## Phase 3 — Notification Bell + Entity History (Stories 4, 5, 6)

### Step 10: Wire Notification Bell

Modify `solune/frontend/src/hooks/useNotifications.ts` to query `api.activity.feed()` with high-signal event type filters.

### Step 11: Entity History Panels

Add collapsible "History" sections in entity detail views using `api.activity.entityHistory()`.

### Step 12: Pipeline Run History

Add `pipelinesApi.listRuns()` and `pipelinesApi.getRun()` to the API client. Backend endpoints already exist.

## Verification Checklist

- [ ] Run migration → `activity_events` table exists with indexes
- [ ] Trigger a pipeline run → event appears in `GET /activity?project_id=X`
- [ ] Create/delete a chore → CRUD events appear in feed
- [ ] Insert 100+ events → pagination works (cursor returns next page)
- [ ] `GET /activity/pipeline/{id}` → only events for that pipeline
- [ ] Activity page loads with timeline and filter chips
- [ ] Scroll to bottom → next page loads automatically
- [ ] Filter by event type → list narrows correctly
- [ ] Notification bell shows unread badge for high-signal events
- [ ] "View all" in bell dropdown → navigates to /activity
- [ ] Pipeline editor "Run History" tab shows past runs
- [ ] Existing test suites pass (no regressions)
