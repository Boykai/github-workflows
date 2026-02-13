# Data Model: Interactive Calendar Component

**Feature**: Interactive Calendar Component  
**Date**: 2026-02-13  
**Status**: Phase 1 - Data Model Complete

## Overview

This document defines the data structures, entities, relationships, and validation rules for the interactive calendar component. The model supports month/week/day views, event management, and state tracking.

---

## Core Entities

### 1. CalendarEvent

**Description**: Represents a scheduled activity on the calendar with date/time, title, and description.

**Attributes**:

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| `id` | string (UUID) | Yes | Unique identifier for the event | Auto-generated on backend |
| `title` | string | Yes | Event title/summary | 1-200 characters, non-empty |
| `description` | string | No | Detailed event description | 0-1000 characters |
| `start` | string (ISO 8601) | Yes | Event start date/time | Valid datetime, must be before `end` |
| `end` | string (ISO 8601) | Yes | Event end date/time | Valid datetime, must be after `start` |
| `allDay` | boolean | Yes | Whether event spans entire day(s) | Default: false |
| `userId` | string | Yes | User who created the event | References authenticated user |
| `createdAt` | string (ISO 8601) | Yes | Timestamp of creation | Auto-generated, immutable |
| `updatedAt` | string (ISO 8601) | Yes | Timestamp of last update | Auto-updated on modification |

**TypeScript Interface**:
```typescript
interface CalendarEvent {
  id: string;
  title: string;
  description?: string;
  start: string;  // ISO 8601: "2026-02-14T10:00:00Z"
  end: string;    // ISO 8601: "2026-02-14T11:00:00Z"
  allDay: boolean;
  userId: string;
  createdAt: string;
  updatedAt: string;
}
```

**Python Model** (Pydantic):
```python
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional

class CalendarEventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    start: datetime
    end: datetime
    allDay: bool = False
    
    @validator('end')
    def end_after_start(cls, v, values):
        if 'start' in values and v <= values['start']:
            raise ValueError('end must be after start')
        return v

class CalendarEventCreate(CalendarEventBase):
    pass

class CalendarEventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    allDay: Optional[bool] = None

class CalendarEvent(CalendarEventBase):
    id: str
    userId: str
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        from_attributes = True
```

**Validation Rules**:
1. `start` must be before `end` (enforced by backend validator)
2. `title` cannot be empty string or whitespace only
3. For all-day events, `start` and `end` should represent full days (time portion ignored in display)
4. Multi-day all-day events: `end` date is exclusive (end = day after last day)
5. Time zone: All datetimes stored in UTC, converted to user's local timezone in frontend

**Business Rules**:
- Events can overlap (no conflict detection in MVP)
- Users can only modify/delete their own events (enforced by `userId` filter)
- Deleted events are hard-deleted (no soft delete/archiving in MVP)
- Event duration: Minimum 15 minutes, Maximum 7 days (validation on backend)

**Relationships**:
- **User → Events**: One-to-many (user can have multiple events)
- No event recurrence in MVP (each occurrence is a separate event)

---

### 2. ViewMode

**Description**: Enumeration representing the current calendar display mode.

**Values**:
- `month`: Display full month grid (default view)
- `week`: Display 7-day week with time slots
- `day`: Display single day with hourly slots

**TypeScript Type**:
```typescript
type ViewMode = 'month' | 'week' | 'day';
```

**State Management**:
- Stored in React component state (`useState<ViewMode>('month')`)
- Persisted to localStorage for user preference (optional enhancement)

**View-Specific Behavior**:

| View Mode | Date Range Displayed | Time Granularity | Navigation Unit |
|-----------|---------------------|------------------|-----------------|
| Month | 1st to last day of month | Full days | ±1 month |
| Week | Sunday-Saturday (or Monday-Sunday based on locale) | 30-minute slots | ±1 week |
| Day | Single 24-hour period | 1-hour slots | ±1 day |

---

### 3. TimePeriod

**Description**: Represents the currently visible date range in the calendar.

**Attributes**:

| Field | Type | Description |
|-------|------|-------------|
| `currentDate` | Date | The "anchor" date determining visible range |
| `viewMode` | ViewMode | Current display mode affecting range calculation |
| `startDate` | Date | Start of visible range (computed) |
| `endDate` | Date | End of visible range (computed) |

**TypeScript Interface**:
```typescript
interface TimePeriod {
  currentDate: Date;    // e.g., Feb 14, 2026
  viewMode: ViewMode;
  startDate: Date;      // Computed based on currentDate + viewMode
  endDate: Date;        // Computed based on currentDate + viewMode
}
```

**Computation Logic**:

```typescript
import { startOfMonth, endOfMonth, startOfWeek, endOfWeek, 
         startOfDay, endOfDay } from 'date-fns';

function calculateDateRange(currentDate: Date, viewMode: ViewMode): {
  startDate: Date;
  endDate: Date;
} {
  switch (viewMode) {
    case 'month':
      return {
        startDate: startOfMonth(currentDate),
        endDate: endOfMonth(currentDate)
      };
    case 'week':
      return {
        startDate: startOfWeek(currentDate, { weekStartsOn: 0 }), // Sunday
        endDate: endOfWeek(currentDate, { weekStartsOn: 0 })
      };
    case 'day':
      return {
        startDate: startOfDay(currentDate),
        endDate: endOfDay(currentDate)
      };
  }
}
```

**State Management**:
- `currentDate`: React state, initialized to `new Date()`
- Updated by navigation controls (prev/next/today buttons)
- `startDate` and `endDate` derived via useMemo to avoid recalculation

---

### 4. DateSelection

**Description**: Tracks the user's currently selected date (for viewing/adding events).

**Attributes**:

| Field | Type | Description |
|-------|------|-------------|
| `selectedDate` | Date \| null | The date user clicked, null if none selected |
| `selectedEvents` | CalendarEvent[] | Events on the selected date (filtered) |

**TypeScript Interface**:
```typescript
interface DateSelection {
  selectedDate: Date | null;
  selectedEvents: CalendarEvent[];
}
```

**State Management**:
- React state, initialized to `null`
- Set when user clicks a date in the calendar
- Cleared when user closes event detail panel or clicks elsewhere
- `selectedEvents` computed by filtering all events by selected date

**Event Filtering Logic**:
```typescript
function getEventsForDate(date: Date, allEvents: CalendarEvent[]): CalendarEvent[] {
  const startOfDay = new Date(date.setHours(0, 0, 0, 0));
  const endOfDay = new Date(date.setHours(23, 59, 59, 999));
  
  return allEvents.filter(event => {
    const eventStart = new Date(event.start);
    const eventEnd = new Date(event.end);
    
    // Event overlaps with selected date
    return eventStart <= endOfDay && eventEnd >= startOfDay;
  });
}
```

---

## Data Flow Diagrams

### 1. Calendar View Rendering

```
┌─────────────────────────────────────────────────────────────────┐
│                     Calendar Component                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [currentDate, viewMode] ──────────────────────────────┐       │
│                                                         ▼       │
│                                            calculateDateRange()  │
│                                                         │       │
│                                          [startDate, endDate]   │
│                                                         │       │
│                                                         ▼       │
│                                  React Query: useCalendarEvents │
│                                   (fetch events in range)       │
│                                                         │       │
│                                              [CalendarEvent[]]  │
│                                                         │       │
│                                                         ▼       │
│                                         react-big-calendar      │
│                                          (render calendar)      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Event Selection Flow

```
User clicks date
       │
       ▼
onSelectSlot(slotInfo) callback
       │
       ├─── Set selectedDate state
       │
       ├─── Filter events for date ──▶ selectedEvents state
       │
       └─── Show EventDetailPanel component
                    │
                    ├─── Display event list
                    │
                    └─── [Add Event] button ──▶ Open EventFormModal
```

### 3. Event Creation Flow

```
User clicks [Add Event] on date
       │
       ▼
Open EventFormModal
       │
       ├─── Pre-fill date field with selectedDate
       │
       └─── User fills: title, description, start time, end time, allDay
              │
              ▼
       [Submit Form]
              │
              ├─── Validate: title non-empty, end > start
              │
              ▼
       POST /api/calendar/events
              │
              ├─── Backend: Create event, return CalendarEvent
              │
              ▼
       React Query: Invalidate ['calendar', 'events'] cache
              │
              ▼
       Refetch events ──▶ Calendar updates with new event
              │
              ▼
       Close modal, show success toast
```

---

## API Contract Data Structures

### Request/Response Formats

#### GET /api/calendar/events

**Query Parameters**:
```typescript
interface GetEventsQuery {
  start: string;  // ISO 8601 date: "2026-02-01"
  end: string;    // ISO 8601 date: "2026-02-29"
}
```

**Response**:
```typescript
interface GetEventsResponse {
  events: CalendarEvent[];
  count: number;
}
```

**Example**:
```json
{
  "events": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Team Standup",
      "description": "Daily sync meeting",
      "start": "2026-02-14T10:00:00Z",
      "end": "2026-02-14T10:30:00Z",
      "allDay": false,
      "userId": "user123",
      "createdAt": "2026-02-13T15:00:00Z",
      "updatedAt": "2026-02-13T15:00:00Z"
    }
  ],
  "count": 1
}
```

#### POST /api/calendar/events

**Request Body**:
```typescript
type CreateEventRequest = Omit<CalendarEvent, 'id' | 'userId' | 'createdAt' | 'updatedAt'>;
```

**Response**: `CalendarEvent` (201 Created)

**Example**:
```json
{
  "title": "Doctor Appointment",
  "description": "Annual checkup",
  "start": "2026-02-15T14:00:00Z",
  "end": "2026-02-15T15:00:00Z",
  "allDay": false
}
```

#### PUT /api/calendar/events/{id}

**Request Body**: `CalendarEventUpdate` (partial update allowed)

**Response**: `CalendarEvent` (200 OK)

#### DELETE /api/calendar/events/{id}

**Response**: 204 No Content

---

## State Management Architecture

### React Query Cache Structure

```typescript
// Query Keys
['calendar', 'events', startDate, endDate] → CalendarEvent[]

// Mutations
createEvent: POST /api/calendar/events
updateEvent: PUT /api/calendar/events/{id}
deleteEvent: DELETE /api/calendar/events/{id}

// Cache Invalidation
- On create: Invalidate ['calendar', 'events']
- On update: Invalidate ['calendar', 'events']
- On delete: Invalidate ['calendar', 'events']
```

### Component State Structure

```typescript
interface CalendarState {
  // Derived from TimePeriod
  currentDate: Date;
  viewMode: ViewMode;
  
  // Derived from DateSelection
  selectedDate: Date | null;
  
  // UI State
  isEventModalOpen: boolean;
  eventFormMode: 'create' | 'edit';
  editingEvent: CalendarEvent | null;
}
```

---

## Validation Rules Summary

### Client-Side Validation (React)

1. **Event Title**: Required, 1-200 chars, trim whitespace
2. **Start/End Dates**: End must be after start
3. **Description**: Optional, max 1000 chars
4. **All Fields**: XSS prevention via React's automatic escaping

### Server-Side Validation (FastAPI)

1. All client-side rules re-enforced
2. **User Authorization**: Event `userId` must match authenticated user
3. **Date Range**: Start/end must be valid ISO 8601
4. **Business Rules**: 
   - Min duration: 15 minutes
   - Max duration: 7 days
5. **Rate Limiting**: Max 100 events created per user per day (future)

### Error Responses

```typescript
interface ValidationError {
  field: string;
  message: string;
}

interface ErrorResponse {
  detail: string;
  errors?: ValidationError[];
}
```

**Example**:
```json
{
  "detail": "Validation failed",
  "errors": [
    {
      "field": "title",
      "message": "Title must be between 1 and 200 characters"
    },
    {
      "field": "end",
      "message": "End date must be after start date"
    }
  ]
}
```

---

## Edge Case Handling

### Multi-Day Events
- **All-Day**: Display as banner spanning multiple days in month/week view
- **Timed**: Display in first day with indicator "continues →"

### Timezone Handling
- **Storage**: All events stored in UTC on backend
- **Display**: Convert to user's local timezone via `date-fns-tz`
- **Creation**: User selects time in local timezone, converted to UTC before sending

### Overlapping Events
- **Display**: Stack vertically in day/week view
- **Limit**: If >5 events overlap, show "+N more" indicator

### Empty States
- **No Events**: Display "No events scheduled" message in event panel
- **Loading**: Show skeleton calendar with placeholder events
- **Error**: Display error overlay with retry button

### DST Transitions
- **Spring Forward**: Events at 2:00 AM show as 3:00 AM
- **Fall Back**: Events at 2:00 AM disambiguated by UTC timestamp

---

## Performance Considerations

### Data Fetching Strategy

1. **Windowed Loading**: Only fetch events in visible date range + buffer
   - Month view: Current month ± 7 days (for events spanning boundaries)
   - Week view: Current week ± 3 days
   - Day view: Current day only

2. **Caching**: React Query caches for 5 minutes
   - Reduces API calls on view switches
   - Background refetch on window focus

3. **Optimistic Updates**: 
   - Create/update events: Immediately update UI
   - Rollback on server error

### Memory Management

- **Event Limit**: Display max 500 events per view (pagination if exceeded)
- **React Memo**: Memoize event list to prevent re-renders
- **Cleanup**: Clear selectedDate state when unmounting

---

## Migration Path (Future)

### Current MVP: In-Memory Storage
```python
# backend/src/storage/memory.py
events_store: dict[str, CalendarEvent] = {}
```

### Future: PostgreSQL Database

**Schema**:
```sql
CREATE TABLE calendar_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    start_datetime TIMESTAMPTZ NOT NULL,
    end_datetime TIMESTAMPTZ NOT NULL,
    all_day BOOLEAN DEFAULT FALSE,
    user_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CHECK (end_datetime > start_datetime)
);

CREATE INDEX idx_events_user_date ON calendar_events(user_id, start_datetime);
CREATE INDEX idx_events_date_range ON calendar_events(start_datetime, end_datetime);
```

**Migration Steps**:
1. Add SQLModel to dependencies
2. Create CalendarEventDB model inheriting from CalendarEventBase
3. Replace in-memory dict with database queries
4. Add Alembic migration

---

## Summary

This data model provides:
- ✅ Clear entity definitions with validation rules
- ✅ Type-safe contracts (TypeScript + Pydantic)
- ✅ Efficient data fetching strategy
- ✅ Comprehensive edge case handling
- ✅ Migration path for future scaling

**Dependencies**:
- Frontend: TypeScript, React, date-fns
- Backend: Python 3.11+, FastAPI, Pydantic

**Next Step**: Generate API contracts in OpenAPI format (contracts/ directory)
