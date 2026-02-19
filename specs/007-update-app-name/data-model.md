# Data Model: Update App Name to "Robot"

**Feature**: 007-update-app-name | **Date**: 2026-02-19  
**Purpose**: Define entities and their relationships for feature implementation

## Model Overview

This feature involves no data model in the traditional sense (no database entities, API models, or state management). The "data" being changed consists of static string literals across frontend, backend, configuration, documentation, and test files. This document exists to satisfy Phase 1 requirements but is intentionally minimal due to the feature's lack of programmatic data structures.

## Entities

### Entity: ApplicationDisplayName

**Type**: Static String Literal (Presentation/Configuration Layer)  
**Purpose**: User-facing text identifying the application name  
**Lifecycle**: Compile-time constant embedded in HTML/JSX/Python/JSON/TOML/Markdown

**Attributes**:

| Attribute | Type | Location | Current Value | New Value |
|-----------|------|----------|---------------|-----------|
| `htmlTitle` | `string` | `frontend/index.html:7` | `"Agent Projects"` | `"Robot"` |
| `loginHeader` | `string` | `frontend/src/App.tsx:72` | `"Agent Projects"` | `"Robot"` |
| `appHeader` | `string` | `frontend/src/App.tsx:89` | `"Agent Projects"` | `"Robot"` |
| `apiTitle` | `string` | `backend/src/main.py:85` | `"Agent Projects API"` | `"Robot API"` |
| `apiDescription` | `string` | `backend/src/main.py:86` | `"REST API for Agent Projects"` | `"REST API for Robot"` |
| `startupLog` | `string` | `backend/src/main.py:75` | `"Starting Agent Projects API"` | `"Starting Robot API"` |
| `shutdownLog` | `string` | `backend/src/main.py:77` | `"Shutting down Agent Projects API"` | `"Shutting down Robot API"` |
| `devcontainerName` | `string` | `.devcontainer/devcontainer.json:2` | `"Agent Projects"` | `"Robot"` |
| `postCreateLog` | `string` | `.devcontainer/post-create.sh:7` | `"Setting up Agent Projects development environment..."` | `"Setting up Robot development environment..."` |
| `envHeader` | `string` | `.env.example:2` | `"Agent Projects - Environment Configuration"` | `"Robot - Environment Configuration"` |
| `pyprojectDescription` | `string` | `backend/pyproject.toml:4` | `"FastAPI backend for Agent Projects"` | `"FastAPI backend for Robot"` |
| `readmeTitle` | `string` | `README.md:1` | `"# Agent Projects"` | `"# Robot"` |
| `backendReadmeTitle` | `string` | `backend/README.md:1` | `"# Agent Projects — Backend"` | `"# Robot — Backend"` |
| `backendReadmeBody` | `string` | `backend/README.md:3` | `"...powers Agent Projects..."` | `"...powers Robot..."` |

**E2E Test Assertions** (must match new app name):

| Test File | Line(s) | Current Assertion | New Assertion |
|-----------|---------|-------------------|---------------|
| `frontend/e2e/auth.spec.ts` | 12, 24, 38, 99 | `toContainText('Agent Projects')` | `toContainText('Robot')` |
| `frontend/e2e/auth.spec.ts` | 62 | `toHaveTitle(/Agent Projects/i)` | `toHaveTitle(/Robot/i)` |
| `frontend/e2e/ui.spec.ts` | 43, 67 | `toContainText('Agent Projects')` | `toContainText('Robot')` |
| `frontend/e2e/integration.spec.ts` | 69 | `toContainText('Agent Projects')` | `toContainText('Robot')` |

**Validation Rules**:
1. **Non-empty**: Name must not be empty string
2. **Consistency**: All instances should display "Robot" for brand consistency
3. **No old references**: Zero occurrences of "Agent Projects" in user-facing content and configuration post-implementation (FR-009)

**State Transitions**: None — static values with no runtime changes

**Relationships**: None — no dependencies on other entities

---

## Entity Relationships

**Diagram**: N/A — single conceptual entity with no relationships

This feature modifies isolated string literals with no connections to:
- User data or session state
- Backend API request/response models
- Database records
- Configuration objects (beyond display name)
- Component props or state

---

## Data Flow

```
Developer edits source files (HTML, TSX, Python, JSON, TOML, Markdown, Shell)
       ↓
Git commit with new name strings
       ↓
Frontend: Vite build → static HTML + compiled React bundle
Backend: Python source loaded at startup → FastAPI metadata + log output
       ↓
Web server serves frontend to browser; backend starts with new API title
       ↓
Browser displays "Robot" in tab/header; API docs display "Robot API"
```

---

## Security Considerations

**Threat Model**: None — static public strings with no user input or dynamic generation

- **No XSS risk**: Hardcoded strings, not user-generated content
- **No injection risk**: No dynamic SQL, shell commands, or template rendering
- **No authentication impact**: Name display is public information
- **No authorization impact**: No access control decisions based on app name

---

## Phase 1 Data Model Completion Checklist

- [x] All entities identified (1 conceptual entity: ApplicationDisplayName)
- [x] Entity attributes documented with current/new values and file locations
- [x] Validation rules defined (non-empty, consistency, no old references)
- [x] Relationships documented (none — isolated strings)
- [x] Data flow described (source → build → display)
- [x] Security considerations addressed (no risks)
- [x] E2E test assertion updates documented

**Status**: ✅ **DATA MODEL COMPLETE** — Ready for contracts and quickstart generation
