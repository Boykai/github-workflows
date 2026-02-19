# Data Model: Replace App Title with 'agentic'

**Feature**: 001-agentic-app-title | **Date**: 2026-02-19
**Purpose**: Define entities and their relationships for feature implementation

## Model Overview

This feature involves no data model in the traditional sense (no database entities, API models, or state management). The "data" being changed consists of static string literals in presentation layer files, backend metadata, and developer configuration. This document exists to satisfy Phase 1 requirements but is intentionally minimal due to the feature's lack of programmatic data structures.

## Entities

### Entity: ApplicationTitle

**Type**: Static String Literal (View Layer + Metadata)
**Purpose**: User-facing and developer-facing text identifying the application name
**Lifecycle**: Compile-time constant embedded in HTML/JSX/Python/JSON/Markdown

**Attributes**:

| Attribute | Type | Constraints | Current Value | New Value |
|-----------|------|-------------|---------------|-----------|
| `htmlTitle` | `string` | Non-empty, < 100 chars | `"Agent Projects"` | `"agentic"` |
| `loginHeaderTitle` | `string` | Non-empty, < 100 chars | `"Agent Projects"` | `"agentic"` |
| `appHeaderTitle` | `string` | Non-empty, < 100 chars | `"Agent Projects"` | `"agentic"` |
| `fastapiTitle` | `string` | Non-empty | `"Agent Projects API"` | `"agentic API"` |
| `fastapiDescription` | `string` | Non-empty | `"REST API for Agent Projects"` | `"REST API for agentic"` |
| `logStartMessage` | `string` | Non-empty | `"Starting Agent Projects API"` | `"Starting agentic API"` |
| `logStopMessage` | `string` | Non-empty | `"Shutting down Agent Projects API"` | `"Shutting down agentic API"` |
| `devcontainerName` | `string` | Non-empty | `"Agent Projects"` | `"agentic"` |
| `setupMessage` | `string` | Non-empty | `"Setting up Agent Projects development environment..."` | `"Setting up agentic development environment..."` |
| `pyprojectName` | `string` | kebab-case | `"agent-projects-backend"` | `"agentic-backend"` |
| `pyprojectDescription` | `string` | Non-empty | `"FastAPI backend for Agent Projects"` | `"FastAPI backend for agentic"` |
| `rootReadmeTitle` | `string` | Non-empty | `"# Agent Projects"` | `"# agentic"` |
| `backendReadmeTitle` | `string` | Non-empty | `"# Agent Projects — Backend"` | `"# agentic — Backend"` |

**Locations**:
- `htmlTitle`: `frontend/index.html` line 7 (`<title>` element)
- `loginHeaderTitle`: `frontend/src/App.tsx` line 72 (`<h1>` in login view)
- `appHeaderTitle`: `frontend/src/App.tsx` line 89 (`<h1>` in authenticated view)
- `fastapiTitle`: `backend/src/main.py` line 85 (FastAPI constructor)
- `fastapiDescription`: `backend/src/main.py` line 86 (FastAPI constructor)
- `logStartMessage`: `backend/src/main.py` line 75 (lifespan startup)
- `logStopMessage`: `backend/src/main.py` line 77 (lifespan shutdown)
- `devcontainerName`: `.devcontainer/devcontainer.json` line 2
- `setupMessage`: `.devcontainer/post-create.sh` line 7
- `pyprojectName`: `backend/pyproject.toml` line 2
- `pyprojectDescription`: `backend/pyproject.toml` line 4
- `rootReadmeTitle`: `README.md` line 1
- `backendReadmeTitle`: `backend/README.md` line 1

**Validation Rules**:
1. **Non-empty**: Title must not be empty string
2. **Exact casing**: Must be exactly "agentic" (all lowercase) for brand name references
3. **Consistency**: All instances should use the same brand name for consistency (not programmatically enforced)

**State Transitions**: None — static values with no runtime changes

**Relationships**: None — no dependencies on other entities

---

## Entity Relationships

**Diagram**: N/A — single entity with no relationships

This feature modifies isolated string literals with no connections to:
- User data or session state
- Backend API models or database records
- Configuration objects or component props
- Authentication or authorization logic

---

## Data Validation

### Compile-Time Validation

- **TypeScript**: JSX string literals are type-checked as `string` (satisfied)
- **HTML**: `<title>` tag requires text content (satisfied)
- **Python**: String literals in FastAPI constructor are typed (satisfied)
- **Linter**: ESLint/Prettier/Ruff format strings but don't enforce content rules

### Runtime Validation

None required. Titles are static strings with no user input or dynamic generation.

### Human Validation (Acceptance Criteria)

From spec.md acceptance scenarios:
1. Browser tab displays "agentic" (visual inspection)
2. Login page header displays "agentic" (visual inspection)
3. Authenticated header displays "agentic" (visual inspection)
4. Backend metadata shows "agentic API" (Swagger UI inspection)
5. No old title references remain (codebase search)

---

## Data Storage

**Storage Mechanism**: Git repository source code
**Format**: Plain text (HTML, TypeScript/TSX, Python, JSON, Shell, Markdown, TOML)
**Persistence**: Version controlled via git
**Backup**: GitHub remote repository
**Encryption**: Not applicable (public source code)

---

## Data Flow

```
Developer edits source files
       ↓
Git commit with new title strings
       ↓
Frontend: Vite build → Static HTML + compiled React bundle
Backend: Python source → FastAPI application metadata
       ↓
Web server serves frontend to browser / Backend starts with metadata
       ↓
Browser displays title in tab/header; Backend logs/Swagger show new name
```

**Flow Characteristics**:
- **Unidirectional**: Source → Build → Deploy → Display
- **No user input**: Users cannot change title (read-only display)
- **No persistence layer**: No database, localStorage, or cookies involved
- **No synchronization**: Title is not shared across users or sessions

---

## Security Considerations

**Threat Model**: None — static public strings with no user input or dynamic generation

**Security Properties**:
- **No XSS risk**: Hardcoded strings, not user-generated content
- **No injection risk**: No dynamic SQL, shell commands, or template rendering
- **No authentication impact**: Title display is public information
- **No authorization impact**: No access control decisions based on title

---

## Performance Characteristics

**Size Impact**:
- Old title: 14 chars (`"Agent Projects"`)
- New title: 7 chars (`"agentic"`)
- **Savings**: ~7 bytes per instance (negligible)

**Runtime Impact**:
- Title rendering: O(1) — single DOM text node update
- No performance degradation expected

**Memory Impact**: Negligible — string literal storage in compiled JavaScript/Python

---

## Phase 1 Data Model Completion Checklist

- [x] All entities identified (1 static entity: ApplicationTitle)
- [x] Entity attributes documented with current/new values
- [x] Validation rules defined (non-empty, exact casing)
- [x] Relationships documented (none — isolated strings)
- [x] Data flow described (source → build → display)
- [x] Storage mechanism identified (git source code)
- [x] Security considerations addressed (no risks)
- [x] Performance impact assessed (negligible)

**Status**: ✅ **DATA MODEL COMPLETE** — Ready for contracts and quickstart generation
