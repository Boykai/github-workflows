# Research: Update App Title to "Happy Place"

**Feature**: 007-app-title-happy-place  
**Date**: 2026-02-20  
**Purpose**: Resolve all Technical Context unknowns and document design decisions

## Research Tasks

### R1: What is the current application title and where does it appear?

**Decision**: The current application title is `"Agent Projects"`. It appears in 15 files with approximately 25 occurrences across the codebase. All occurrences are direct string literals — no centralized constant or configuration variable is used.

**Rationale**: A codebase-wide search for `"Agent Projects"` confirmed all locations. The title is hardcoded in each location independently, which means each occurrence must be individually updated.

**Complete inventory of occurrences**:

| # | File | Line(s) | Context |
|---|------|---------|---------|
| 1 | `frontend/index.html` | 7 | `<title>Agent Projects</title>` |
| 2 | `frontend/src/App.tsx` | 72 | `<h1>Agent Projects</h1>` (login view) |
| 3 | `frontend/src/App.tsx` | 89 | `<h1>Agent Projects</h1>` (main header) |
| 4 | `frontend/src/services/api.ts` | 2 | Docstring: `API client service for Agent Projects.` |
| 5 | `frontend/src/types/index.ts` | 2 | Docstring: `TypeScript types for Agent Projects API.` |
| 6 | `frontend/e2e/auth.spec.ts` | 12, 24, 38, 99 | `toContainText('Agent Projects')` |
| 7 | `frontend/e2e/auth.spec.ts` | 62 | `toHaveTitle(/Agent Projects/i)` |
| 8 | `frontend/e2e/ui.spec.ts` | 43, 67 | `toContainText('Agent Projects')` |
| 9 | `frontend/e2e/integration.spec.ts` | 69 | `toContainText('Agent Projects')` |
| 10 | `backend/src/main.py` | 75 | `logger.info("Starting Agent Projects API")` |
| 11 | `backend/src/main.py` | 77 | `logger.info("Shutting down Agent Projects API")` |
| 12 | `backend/src/main.py` | 85 | `title="Agent Projects API"` |
| 13 | `backend/src/main.py` | 86 | `description="REST API for Agent Projects"` |
| 14 | `backend/pyproject.toml` | 4 | `description = "FastAPI backend for Agent Projects"` |
| 15 | `backend/tests/test_api_e2e.py` | 2 | Docstring: `End-to-end API tests for the Agent Projects Backend.` |
| 16 | `backend/README.md` | 1 | `# Agent Projects — Backend` |
| 17 | `backend/README.md` | 3 | `FastAPI backend that powers Agent Projects...` |
| 18 | `README.md` | 1 | `# Agent Projects` |
| 19 | `.devcontainer/devcontainer.json` | 2 | `"name": "Agent Projects"` |
| 20 | `.devcontainer/post-create.sh` | 7 | `echo "🚀 Setting up Agent Projects development environment..."` |
| 21 | `.env.example` | 2 | `# Agent Projects - Environment Configuration` |

**Alternatives considered**:
- Centralizing the title in a single constant/config file — rejected per YAGNI (Principle V). The title is a stable branding string that changes infrequently. A single constant would add indirection without meaningful benefit for ~25 occurrences that are easily searchable.

---

### R2: Are there any dynamic or computed title references?

**Decision**: No. All title references are static string literals. There is no `APP_TITLE` constant, no environment variable for the title, and no computed title logic. The title is not derived from any configuration at runtime.

**Rationale**: Search for patterns like `APP_TITLE`, `app.title`, `appName`, `APP_NAME`, and environment variable patterns (`process.env.*TITLE*`, `os.environ.*TITLE*`) returned zero results outside of the known static occurrences.

**Alternatives considered**: N/A — this was a factual research question.

---

### R3: Are there any PWA manifest or meta tags that reference the title?

**Decision**: No. The application does not have a PWA manifest (`manifest.json` / `manifest.webmanifest`). The `index.html` has only a basic `<title>` tag — no `<meta property="og:title">`, `<meta name="application-name">`, or other title-related meta tags exist.

**Rationale**: File searches for `manifest.json`, `manifest.webmanifest`, `og:title`, and `application-name` returned zero results. The `index.html` is minimal (13 lines) with only charset, viewport, and title tags.

**Alternatives considered**: N/A — this was a factual research question. The spec mentions PWA manifest and meta tags as "if applicable" — they are not applicable here.

---

### R4: What is the best practice for this type of branding change?

**Decision**: Perform a systematic file-by-file replacement with human review of each occurrence to ensure context-appropriate substitution. Do not use blind find-and-replace due to risk of changing unintended strings (e.g., if "Agent Projects" appeared in user data or API responses).

**Rationale**: While "Agent Projects" is unique enough that a global replace would be safe in this codebase, context-aware replacement is the standard best practice for branding changes. Each occurrence should be verified to ensure the replacement reads naturally in context (e.g., "FastAPI backend for Happy Place" vs "FastAPI backend for Agent Projects").

**Alternatives considered**:
- Global `sed` replacement — considered but rejected because it wouldn't allow per-occurrence review for contextual correctness.
- Introducing an `APP_TITLE` constant and replacing all occurrences with references to it — rejected per YAGNI; the title is stable and the indirection adds complexity without proportional benefit.

---

### R5: Do existing tests need updating and what is the testing strategy?

**Decision**: Yes. Eight E2E test assertions across 3 Playwright test files reference "Agent Projects" and must be updated to "Happy Place". No new tests are needed. The backend pytest test file has only a docstring reference (not an assertion).

**Rationale**: The E2E tests use `toContainText('Agent Projects')` and `toHaveTitle(/Agent Projects/i)` to verify the page title and header content. These are functional assertions that will fail if the title is changed without updating the tests. Updating these assertions is part of the change, not additional test work.

**Test files requiring updates**:
- `frontend/e2e/auth.spec.ts`: 5 assertions (lines 12, 24, 38, 62, 99)
- `frontend/e2e/ui.spec.ts`: 2 assertions (lines 43, 67)
- `frontend/e2e/integration.spec.ts`: 1 assertion (line 69)

**Alternatives considered**:
- Adding new tests specifically for the title change — rejected because existing E2E tests already cover all title-display scenarios.
- Parameterizing the title in tests — rejected per YAGNI; the title is a stable string.
