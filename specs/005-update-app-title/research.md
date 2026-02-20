# Research: Update App Title to "Happy Place"

**Feature**: 005-update-app-title | **Date**: 2026-02-20

---

## R1: Current Title Locations and Values

### Decision
The current app title is **"Agent Projects"** and appears in exactly 15 files across ~25 occurrences. All instances use the exact string "Agent Projects" with no emoji, no dynamic construction, and no environment-variable-based resolution.

### Rationale
- A full-repository search (`grep -rn "Agent Projects"`) confirmed all locations
- No `.env` variable controls the title — it is hardcoded in every location
- No PWA `manifest.json` exists — the app does not have a service worker or web app manifest
- No OpenGraph `<meta>` tags exist in `index.html` — the page has minimal `<head>` content
- The title is never dynamically constructed from fragments — each occurrence is a complete literal string

### Locations Inventory

| Category | File | Line(s) | Context |
|----------|------|---------|---------|
| **Frontend — User-Facing** | `frontend/index.html` | 7 | `<title>Agent Projects</title>` |
| | `frontend/src/App.tsx` | 72 | `<h1>Agent Projects</h1>` (logged-out view) |
| | `frontend/src/App.tsx` | 89 | `<h1>Agent Projects</h1>` (authenticated header) |
| **Frontend — Code Comments** | `frontend/src/types/index.ts` | 2 | Module docstring: `TypeScript types for Agent Projects API.` |
| | `frontend/src/services/api.ts` | 2 | Module docstring: `API client service for Agent Projects.` |
| **Frontend — E2E Tests** | `frontend/e2e/auth.spec.ts` | 12, 24, 38, 62, 99 | `toContainText('Agent Projects')` and `toHaveTitle(/Agent Projects/i)` |
| | `frontend/e2e/ui.spec.ts` | 43, 67 | `toContainText('Agent Projects')` |
| | `frontend/e2e/integration.spec.ts` | 69 | `toContainText('Agent Projects')` |
| **Backend — Application Config** | `backend/src/main.py` | 85 | `title="Agent Projects API"` (FastAPI metadata) |
| | `backend/src/main.py` | 86 | `description="REST API for Agent Projects"` |
| | `backend/src/main.py` | 75 | `logger.info("Starting Agent Projects API")` |
| | `backend/src/main.py` | 77 | `logger.info("Shutting down Agent Projects API")` |
| **Backend — Package Metadata** | `backend/pyproject.toml` | 4 | `description = "FastAPI backend for Agent Projects"` |
| **Backend — Documentation** | `backend/README.md` | 1, 3 | Header + description paragraph |
| **Backend — Tests** | `backend/tests/test_api_e2e.py` | 2 | Module docstring |
| **DevContainer** | `.devcontainer/devcontainer.json` | 2 | `"name": "Agent Projects"` |
| | `.devcontainer/post-create.sh` | 7 | Echo message |
| **Config** | `.env.example` | 2 | Header comment |
| **Project Root** | `README.md` | 1 | `# Agent Projects` |

### Alternatives Considered
| Alternative | Why Rejected |
|---|---|
| Introduce an environment variable for the title | Over-engineering for a one-time rename; adds indirection for no benefit |
| Use a shared constants file for the title | Violates Simplicity/DRY principle — the title appears in different contexts (HTML, Python, TypeScript, shell, TOML) with no runtime sharing possible |
| Only update user-facing files, skip comments and docs | Spec FR-007 requires no residual references; partial update creates inconsistency |

---

## R2: Replacement Strategy

### Decision
Use direct find-and-replace of the exact string "Agent Projects" → "Happy Place" in all 15 files. For backend API metadata, use "Happy Place API" (matching the existing pattern "Agent Projects API"). For documentation and comments, use "Happy Place" as the project name.

### Rationale
- The replacement is deterministic — no ambiguity in any location
- "Agent Projects API" → "Happy Place API" preserves the existing naming pattern for the FastAPI app
- No code logic changes required — all occurrences are string literals or comments
- E2E test assertions must change to prevent false failures (spec edge case)

### Replacement Rules

| Pattern | Replacement | Applies To |
|---------|-------------|------------|
| `Agent Projects API` | `Happy Place API` | `backend/src/main.py` (title, description, log messages) |
| `Agent Projects` (standalone) | `Happy Place` | All other files |
| `/Agent Projects/i` (regex in test) | `/Happy Place/i` | `frontend/e2e/auth.spec.ts` line 62 |

### Verification Approach
1. After replacement: `grep -rn "Agent Projects" . --include="*.html" --include="*.tsx" --include="*.ts" --include="*.py" --include="*.json" --include="*.md" --include="*.toml" --include="*.sh"` → must return zero results (excluding `specs/` directory)
2. Load app in browser → verify browser tab shows "Happy Place"
3. Load app in browser → verify `<h1>` shows "Happy Place"
4. Run E2E test suite → all tests pass with updated assertions

---

## R3: Risk Assessment

### Decision
This change is low-risk with no functional impact beyond branding.

### Rationale
- No API contract changes (title metadata is informational, not consumed by clients)
- No database changes
- No authentication flow changes
- No dependency changes
- The only risk is missing an occurrence, which is mitigated by the grep verification step

### Alternatives Considered
| Alternative | Why Rejected |
|---|---|
| Staged rollout (frontend first, then backend) | Unnecessary for a string replacement — atomicity preferred |
| Feature flag for title | Over-engineering for a permanent rename |
