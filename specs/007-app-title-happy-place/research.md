# Research: Update App Title to "Happy Place"

**Feature**: 007-app-title-happy-place
**Date**: 2026-02-20
**Purpose**: Resolve all Technical Context unknowns and document design decisions

## Research Tasks

### R1: What is the current application title and where does it appear?

**Decision**: The current application title is **"Agent Projects"** and it appears in approximately 25 occurrences across 15 files. A complete inventory was gathered by searching the codebase for the string "Agent Projects".

**Rationale**: A codebase-wide search confirms a single, consistent title string is used everywhere. No variations (e.g., "agent projects", "AGENT PROJECTS", "Agent-Projects") were found, which simplifies the replacement to a straightforward find-and-replace operation.

**Locations identified**:

| Category | File | Line(s) | Context |
|----------|------|---------|---------|
| Browser tab | `frontend/index.html` | 7 | `<title>Agent Projects</title>` |
| UI headers | `frontend/src/App.tsx` | 72, 89 | `<h1>Agent Projects</h1>` (login + authenticated) |
| API metadata | `backend/src/main.py` | 85, 86 | FastAPI `title` and `description` fields |
| Log messages | `backend/src/main.py` | 75, 77 | Startup/shutdown log strings |
| DevContainer | `.devcontainer/devcontainer.json` | 2 | Container `name` field |
| DevContainer | `.devcontainer/post-create.sh` | 7 | Setup echo message |
| Environment | `.env.example` | 2 | Header comment |
| Documentation | `README.md` | 1 | Project heading |
| Documentation | `backend/README.md` | 1, 3 | Heading and description |
| Build config | `backend/pyproject.toml` | 4 | `description` field |
| Code comments | `frontend/src/services/api.ts` | 2 | JSDoc comment |
| Code comments | `frontend/src/types/index.ts` | 2 | JSDoc comment |
| E2E tests | `frontend/e2e/auth.spec.ts` | 12, 24, 38, 62, 99 | Title and heading assertions |
| E2E tests | `frontend/e2e/ui.spec.ts` | 43, 67 | Heading assertions |
| E2E tests | `frontend/e2e/integration.spec.ts` | 69 | Heading assertion |

**Alternatives considered**:
- Partial replacement (user-visible only) — rejected because the spec requires FR-006: no residual references to the old app title in the codebase.
- Centralized title constant — rejected because this is a simple branding update, not an architectural change. Introducing a shared constant would add unnecessary complexity for a one-time rename.

---

### R2: Are there any title-related configuration files beyond source code?

**Decision**: No additional configuration files (e.g., PWA manifest.json, meta og:title tags, favicon-related configs) were found. The application does not include a PWA manifest or Open Graph meta tags.

**Rationale**: A search for `manifest.json`, `og:title`, and `meta.*title` in the frontend found no results beyond the `<title>` tag in `index.html`. The application is a standard SPA without PWA capabilities.

**Alternatives considered**: N/A — no additional files exist to update.

---

### R3: What is the best approach for updating E2E test assertions?

**Decision**: Direct string replacement within each test file. Each assertion referencing "Agent Projects" will be updated to "Happy Place". The assertions use two patterns:
1. `await expect(page).toHaveTitle(/Agent Projects/i)` — regex pattern in title check
2. `await expect(page.locator('h1')).toContainText('Agent Projects')` — string match in heading check

Both patterns will be updated to reference "Happy Place" using the same assertion style.

**Rationale**: The tests use standard Playwright assertion patterns. The replacement is mechanical and preserves the test structure. No test logic changes are needed — only the expected string value.

**Alternatives considered**:
- Using a test fixture or constant for the title — rejected because the existing tests use inline strings, and introducing a shared constant would be inconsistent with the current test style.
- Regex-based assertions for flexibility — rejected because "Happy Place" is the exact expected value and exact matching is more precise.

---

### R4: Are there any backend API responses that include the app title?

**Decision**: The FastAPI metadata fields (`title` and `description` in `create_app()`) are exposed in the auto-generated OpenAPI schema at `/api/docs` (when debug mode is enabled). The `description` field contains "REST API for Agent Projects" which should become "REST API for Happy Place". No API endpoint returns the app title as response data.

**Rationale**: The FastAPI `title` and `description` appear in the OpenAPI/Swagger UI but are not part of any API response payload. The change is cosmetic to the API documentation only.

**Alternatives considered**: N/A — straightforward metadata update.

---

### R5: Impact on backend test suite

**Decision**: The backend test file `backend/tests/test_api_e2e.py` contains a reference to "Agent Projects" in a comment (line 2). This is a documentation comment, not a functional assertion. It should be updated for consistency per FR-006.

**Rationale**: While updating a comment does not affect test execution, the spec explicitly requires zero residual references to the old title (FR-006). Leaving it would fail the codebase-wide search criterion (SC-002).

**Alternatives considered**: N/A — must update per spec requirements.
