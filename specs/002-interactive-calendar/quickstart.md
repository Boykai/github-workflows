# Quickstart Guide: Interactive Calendar Component

**Feature**: Interactive Calendar Component  
**Date**: 2026-02-13  
**For**: Developers implementing the calendar feature

## Overview

This guide helps you set up, develop, and test the interactive calendar component. The calendar supports month/week/day views, event management, and mobile responsiveness.

---

## Prerequisites

### Required Software
- **Node.js**: 18+ (for frontend development)
- **Python**: 3.11+ (for backend API)
- **npm**: 9+ (comes with Node.js)
- **Git**: For version control

### Existing Project Setup
This feature integrates into the existing GitHub Projects Chat Interface application.

**Tech Stack**:
- Frontend: React 18.3.1 + TypeScript 5.4 + Vite
- Backend: FastAPI (Python)
- State Management: Tanstack React Query
- Testing: Vitest (unit), Playwright (E2E)

---

## Installation

### 1. Clone and Install Dependencies

```bash
# If not already done
cd /path/to/github-workflows

# Install frontend dependencies
cd frontend
npm install

# Install backend dependencies
cd ../backend
pip install -e ".[dev]"
```

### 2. Install New Calendar Dependencies

```bash
# Frontend - calendar libraries
cd frontend
npm install react-big-calendar date-fns --save
```

**Dependencies Added**:
- `react-big-calendar` (v1.8+): Calendar UI component library
- `date-fns` (v3.0+): Date manipulation and formatting

---

## Project Structure

### Feature Documentation
```
specs/002-interactive-calendar/
├── spec.md              # Feature specification (user stories, requirements)
├── plan.md              # Implementation plan (this phase's output)
├── research.md          # Technology decisions and alternatives
├── data-model.md        # Entity definitions and data flow
├── quickstart.md        # This guide
└── contracts/
    └── openapi.yaml     # API specification
```

### Source Code Structure

**Frontend** (`frontend/src/`):
```
frontend/src/
├── components/
│   ├── calendar/
│   │   ├── Calendar.tsx              # Main calendar component
│   │   ├── CalendarToolbar.tsx       # View switcher + navigation
│   │   ├── EventDetailPanel.tsx      # Shows events for selected date
│   │   ├── EventFormModal.tsx        # Create/edit event form
│   │   └── styles/
│   │       └── Calendar.module.css   # Calendar-specific styles
│   └── common/
│       └── LoadingSpinner.tsx        # Reuse existing or create new
├── hooks/
│   └── useCalendarEvents.ts          # React Query hook for events API
├── services/
│   └── calendarApi.ts                # API client functions
└── types/
    └── calendar.ts                   # TypeScript interfaces
```

**Backend** (`backend/src/`):
```
backend/src/
├── api/
│   └── calendar.py                   # Calendar event endpoints
├── models/
│   └── calendar.py                   # Pydantic models (CalendarEvent)
├── services/
│   └── calendar_service.py           # Business logic
└── storage/
    └── calendar_storage.py           # In-memory storage (MVP)
```

---

## Development Workflow

### 1. Start Development Servers

**Terminal 1 - Backend**:
```bash
cd backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm run dev
```

Application available at: `http://localhost:5173` (Vite dev server)  
API available at: `http://localhost:8000/api`

### 2. Verify Setup

Open browser to `http://localhost:5173` and check:
- ✅ Application loads without errors
- ✅ Console shows no TypeScript errors
- ✅ API health check: `http://localhost:8000/api/health` returns 200

---

## Implementation Phases

### Phase 1: Core Calendar Display (P1 User Stories)

**Goal**: Display calendar in month/week/day views with navigation

**Files to Create/Modify**:
1. `frontend/src/types/calendar.ts` - TypeScript interfaces
2. `frontend/src/components/calendar/Calendar.tsx` - Main component
3. `frontend/src/components/calendar/CalendarToolbar.tsx` - View controls
4. `frontend/src/App.tsx` - Add calendar link to navigation

**Steps**:
```bash
# 1. Create TypeScript types
# Define CalendarEvent, ViewMode, TimePeriod interfaces
# See data-model.md for reference

# 2. Create Calendar component
# - Import react-big-calendar
# - Set up date-fns localizer
# - Implement view mode state (useState)
# - Add view switching controls
# - Highlight today's date with custom CSS

# 3. Test calendar rendering
npm run dev
# Navigate to calendar page, verify all 3 views display
```

**Acceptance Criteria**:
- [ ] Calendar displays in month view by default
- [ ] View switcher toggles between month/week/day
- [ ] Navigation arrows change time periods
- [ ] Today's date is visually highlighted
- [ ] "Today" button returns to current date

---

### Phase 2: Backend API Implementation

**Goal**: Create REST endpoints for event CRUD operations

**Files to Create**:
1. `backend/src/models/calendar.py` - Pydantic models
2. `backend/src/storage/calendar_storage.py` - In-memory storage
3. `backend/src/api/calendar.py` - FastAPI routes
4. `backend/src/main.py` - Register calendar router

**Steps**:
```bash
# 1. Create Pydantic models (see data-model.md)
# CalendarEventBase, CalendarEventCreate, CalendarEventUpdate, CalendarEvent

# 2. Implement in-memory storage
# Simple dict: events_store = {}

# 3. Create API endpoints
# GET /api/calendar/events?start=...&end=...
# POST /api/calendar/events
# GET /api/calendar/events/{id}
# PUT /api/calendar/events/{id}
# DELETE /api/calendar/events/{id}

# 4. Test API with curl or Postman
curl http://localhost:8000/api/calendar/events?start=2026-02-01&end=2026-02-29
```

**Test with Sample Data**:
```bash
# Create test event
curl -X POST http://localhost:8000/api/calendar/events \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Event",
    "start": "2026-02-14T10:00:00Z",
    "end": "2026-02-14T11:00:00Z",
    "allDay": false
  }'
```

---

### Phase 3: Event Integration (P2 User Stories)

**Goal**: Connect frontend calendar to backend API with React Query

**Files to Create/Modify**:
1. `frontend/src/services/calendarApi.ts` - API client
2. `frontend/src/hooks/useCalendarEvents.ts` - React Query hook
3. `frontend/src/components/calendar/Calendar.tsx` - Integrate events
4. `frontend/src/components/calendar/EventDetailPanel.tsx` - Show events
5. `frontend/src/components/calendar/EventFormModal.tsx` - Create events

**Steps**:
```bash
# 1. Create API client functions
# fetchEvents(start, end)
# createEvent(data)
# updateEvent(id, data)
# deleteEvent(id)

# 2. Create React Query hook
# useCalendarEvents(startDate, endDate)
# Returns: { data, isLoading, isError, refetch }

# 3. Integrate with Calendar component
# Pass events to react-big-calendar
# Handle loading/error states

# 4. Implement event selection
# onSelectSlot: Open event detail panel
# onSelectEvent: Show event details

# 5. Create event form modal
# Form with title, description, start, end, allDay
# Validation: title required, end > start
# Submit → createEvent mutation
```

**Test Event Flow**:
1. Click a date in calendar
2. Event detail panel opens
3. Click "Add Event" button
4. Fill form and submit
5. Event appears on calendar
6. Click event to view details
7. Edit or delete event

---

### Phase 4: Mobile Responsiveness (P2)

**Goal**: Optimize calendar for mobile devices (375px+ width)

**Files to Modify**:
1. `frontend/src/components/calendar/styles/Calendar.module.css`

**Steps**:
```bash
# 1. Add responsive CSS breakpoints
# @media (max-width: 768px) - tablet
# @media (max-width: 375px) - mobile

# 2. Adjust touch target sizes
# Minimum 44x44px for tap areas

# 3. Test on mobile viewport
# Chrome DevTools → Toggle device toolbar
# Test with iPhone SE (375px) and iPad (768px)
```

**Responsive Design Checklist**:
- [ ] Month view: All dates visible at 375px width
- [ ] Week view: Days stack or scroll horizontally
- [ ] Day view: Hourly slots are tap-friendly
- [ ] Navigation controls are large enough for touch
- [ ] Event form modal fits on mobile screen

---

## Testing

### Unit Tests (Optional - Vitest)

```bash
cd frontend
npm run test

# Run specific test file
npm run test src/hooks/useCalendarEvents.test.ts
```

**Test Cases to Consider**:
- Date range calculation (month/week/day)
- Event filtering by selected date
- Form validation logic
- API client error handling

### E2E Tests (Optional - Playwright)

```bash
cd frontend
npm run test:e2e

# Run in UI mode for debugging
npm run test:e2e:ui
```

**E2E Scenarios**:
- User can switch between views
- User can navigate to future/past months
- User can create an event
- User can view events on a date
- Calendar works on mobile viewport

### Manual Testing Checklist

**Desktop (1920x1080)**:
- [ ] All 3 view modes render correctly
- [ ] Navigation arrows work in all views
- [ ] Today button returns to current date
- [ ] Can create event and see it on calendar
- [ ] Can click event to view details
- [ ] Can edit/delete events

**Mobile (375px)**:
- [ ] Calendar adapts to small screen
- [ ] Touch targets are large enough
- [ ] Can scroll/navigate calendar
- [ ] Event form is usable on mobile

**Edge Cases**:
- [ ] Leap year: February 29, 2024
- [ ] Month with 31 days displays correctly
- [ ] All-day events span full day(s)
- [ ] Multi-day events show correctly
- [ ] Overlapping events display properly
- [ ] Empty state (no events) shows message

---

## API Reference

### Base URL
- **Development**: `http://localhost:8000/api`
- **Production**: `https://api.example.com/api`

### Authentication
All endpoints require JWT token in Authorization header:
```
Authorization: Bearer <token>
```

### Endpoints

#### GET /calendar/events
Fetch events in date range

**Query Parameters**:
- `start` (required): ISO 8601 date (YYYY-MM-DD)
- `end` (required): ISO 8601 date (YYYY-MM-DD)

**Response**: `{ events: CalendarEvent[], count: number }`

#### POST /calendar/events
Create new event

**Body**: `{ title, description?, start, end, allDay }`

**Response**: `CalendarEvent` (201 Created)

#### PUT /calendar/events/{id}
Update event (partial update)

**Body**: Any subset of event fields

**Response**: `CalendarEvent` (200 OK)

#### DELETE /calendar/events/{id}
Delete event

**Response**: 204 No Content

See `contracts/openapi.yaml` for complete API documentation.

---

## Configuration

### Environment Variables

**Frontend** (`.env`):
```bash
VITE_API_BASE_URL=http://localhost:8000/api
```

**Backend** (`.env`):
```bash
# No calendar-specific variables needed for MVP
# Uses existing auth configuration
```

### react-big-calendar Setup

In `Calendar.tsx`:
```typescript
import { Calendar, dateFnsLocalizer } from 'react-big-calendar';
import { format, parse, startOfWeek, getDay } from 'date-fns';
import 'react-big-calendar/lib/css/react-big-calendar.css';

const locales = {
  'en-US': require('date-fns/locale/en-US'),
};

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek,
  getDay,
  locales,
});
```

---

## Troubleshooting

### Issue: Calendar doesn't display

**Symptoms**: Blank page or "Calendar is not defined" error

**Solution**:
```bash
# Check imports
import { Calendar } from 'react-big-calendar';
import 'react-big-calendar/lib/css/react-big-calendar.css';

# Verify installation
npm list react-big-calendar
```

### Issue: Dates display incorrectly

**Symptoms**: Events appear on wrong days, timezone issues

**Solution**:
- Ensure all dates stored in UTC on backend
- Convert to user's local timezone only in frontend display
- Use `date-fns-tz` for timezone conversions if needed

### Issue: API returns 401 Unauthorized

**Solution**:
- Check JWT token is included in Authorization header
- Verify token is not expired
- Ensure backend auth middleware is configured correctly

### Issue: Events not appearing after creation

**Solution**:
- Check browser console for errors
- Verify React Query cache invalidation after mutations
- Test API endpoint directly with curl to rule out backend issues

---

## Performance Optimization

### Frontend
1. **Lazy Load Calendar**: Use React.lazy() if calendar is on separate route
2. **Memoize Date Calculations**: Use useMemo for startDate/endDate
3. **Virtualization**: If >100 events, consider virtualized list for event panel

### Backend
1. **Date Range Filtering**: Only fetch events in visible range
2. **Caching**: Add Redis cache for frequently accessed events (future)
3. **Database Indexing**: Index on userId + start_datetime (when migrating to PostgreSQL)

---

## Next Steps

After completing implementation:

1. **Code Review**: Submit PR with changes
2. **Documentation**: Update main README.md with calendar feature
3. **User Testing**: Get feedback from team members
4. **Accessibility Audit**: Test with screen reader
5. **Performance Profiling**: Check bundle size and render times

---

## Resources

### Library Documentation
- [react-big-calendar Examples](https://jquense.github.io/react-big-calendar/examples/index.html)
- [date-fns Documentation](https://date-fns.org/docs/Getting-Started)
- [React Query Guide](https://tanstack.com/query/latest/docs/react/overview)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)

### Design References
- [Material Design - Pickers](https://material.io/components/date-pickers)
- [Apple HIG - Calendar Views](https://developer.apple.com/design/human-interface-guidelines/components/selection-and-input/date-pickers)
- [Google Calendar UI Patterns](https://calendar.google.com)

### Related Specs
- `specs/002-interactive-calendar/spec.md` - Full feature specification
- `specs/002-interactive-calendar/data-model.md` - Data structures
- `specs/002-interactive-calendar/research.md` - Technology decisions

---

## Support

**Questions?** Refer to:
1. Feature specification (`spec.md`) for requirements
2. Data model (`data-model.md`) for entity details
3. API contracts (`contracts/openapi.yaml`) for endpoint specs
4. Research document (`research.md`) for architecture decisions

**Issues?** Check:
- Browser console for frontend errors
- Backend logs for API errors
- React DevTools for component state
- Network tab for API request/response debugging

---

**Last Updated**: 2026-02-13  
**Feature Status**: Planning Phase Complete → Ready for Implementation
