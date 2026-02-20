# Data Model: Update App Title to "Happy Place"

**Feature**: 007-app-title-happy-place | **Date**: 2026-02-20  
**Purpose**: Define entities and their relationships for feature implementation

## Model Overview

This feature involves no data model in the traditional sense (no database entities, API models, or state management). The "data" being changed consists of static string literals across frontend, backend, configuration, documentation, and test files. This document exists to satisfy Phase 1 requirements but is intentionally minimal due to the feature's lack of programmatic data structures.

## Entities

### Entity: ApplicationTitle

**Type**: Static String Literal (Presentation + Configuration Layer)  
**Purpose**: User-facing and developer-facing text identifying the application name  
**Lifecycle**: Compile-time constant embedded in HTML/JSX/Python/config files

**Attributes**:

| Attribute | Type | Constraints | Current Value | New Value |
|-----------|------|-------------|---------------|-----------|
| `htmlTitle` | `string` | Non-empty, < 100 chars | `"Agent Projects"` | `"Happy Place"` |
| `loginHeaderTitle` | `string` | Non-empty, < 100 chars | `"Agent Projects"` | `"Happy Place"` |
| `appHeaderTitle` | `string` | Non-empty, < 100 chars | `"Agent Projects"` | `"Happy Place"` |
| `apiTitle` | `string` | Non-empty | `"Agent Projects API"` | `"Happy Place API"` |
| `apiDescription` | `string` | Non-empty | `"REST API for Agent Projects"` | `"REST API for Happy Place"` |

**Locations**:
- `htmlTitle`: `frontend/index.html` line 7 (`<title>` element)
- `loginHeaderTitle`: `frontend/src/App.tsx` line 72 (`<h1>` in login view)
- `appHeaderTitle`: `frontend/src/App.tsx` line 89 (`<h1>` in authenticated view)
- `apiTitle`: `backend/src/main.py` line 85 (FastAPI `title` parameter)
- `apiDescription`: `backend/src/main.py` line 86 (FastAPI `description` parameter)

**Validation Rules**:
1. **Non-empty**: Title must not be empty string
2. **Character constraints**: Valid Unicode text ("Happy Place" is ASCII-only)
3. **Length**: Reasonable for browser tabs (< 100 chars; new value is 11 chars)
4. **Consistency**: All user-facing instances must display "Happy Place" exactly (FR-005)
5. **Casing**: Title case with space — "Happy Place" (not "happy place", "HAPPY PLACE", or "HappyPlace")

**State Transitions**: None — static values with no runtime changes

**Relationships**: None — no dependencies on other entities

---

## Entity Relationships

**Diagram**: N/A — single entity with no relationships

This feature modifies isolated string literals with no connections to:
- User data or session state
- Database records
- Configuration objects
- Component props or state (titles are hardcoded, not passed as props)

---

## Data Validation

### Compile-Time Validation

- **TypeScript**: JSX string literals are type-checked as `string` (satisfied)
- **HTML**: `<title>` tag requires text content (satisfied)
- **Python**: FastAPI string parameters are validated at startup (satisfied)

### Runtime Validation

None required. Titles are static strings with no user input or dynamic generation.

### Human Validation (Acceptance Criteria)

From spec.md acceptance scenarios:
1. Browser tab displays "Happy Place" (visual inspection)
2. Login page header displays "Happy Place" (visual inspection)
3. Authenticated header displays "Happy Place" (visual inspection)
4. Backend API metadata displays "Happy Place API" (API docs inspection)
5. No old title references remain (codebase search)

---

## Data Flow

```
Developer edits source files
       ↓
Git commit with new title strings
       ↓
Frontend: Vite build → Static HTML + compiled React bundle → Browser displays title
Backend: FastAPI startup → API metadata served at /docs → Swagger UI displays title
```

**Flow Characteristics**:
- **Unidirectional**: Source → Build → Deploy → Display
- **No user input**: Users cannot change title (read-only display)
- **No persistence layer**: No database, localStorage, or cookies involved

---

## Security Considerations

**Threat Model**: None — static public strings with no user input or dynamic generation

- **No XSS risk**: Hardcoded strings, not user-generated content
- **No injection risk**: No dynamic SQL, shell commands, or template rendering
- **No authentication impact**: Title display is public information

---

## Alternative Data Models Considered

### Alternative 1: Centralized Configuration

```typescript
// config/app.ts
export const APP_CONFIG = { title: "Happy Place" };
```

**Rejected Rationale**: YAGNI violation. Adds unnecessary abstraction for single-use string.

### Alternative 2: Environment Variables

```bash
VITE_APP_TITLE="Happy Place"
```

**Rejected Rationale**: Title is not environment-dependent (same in dev/staging/prod). Adds build-time complexity for no benefit.

---

## Phase 1 Data Model Completion Checklist

- [x] All entities identified (1 static entity: ApplicationTitle)
- [x] Entity attributes documented with current/new values
- [x] Validation rules defined (non-empty, casing, length)
- [x] Relationships documented (none — isolated strings)
- [x] Data flow described (source → build → display)
- [x] Security considerations addressed (no risks)
- [x] Alternative models evaluated and rejected

**Status**: ✅ **DATA MODEL COMPLETE** - Ready for contracts and quickstart generation
