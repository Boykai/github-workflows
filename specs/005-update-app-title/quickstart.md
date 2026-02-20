# Quickstart: Update App Title to "Happy Place"

**Feature**: 005-update-app-title | **Branch**: `005-update-app-title` | **Date**: 2026-02-20

---

## Prerequisites

- Docker & Docker Compose installed (for full-stack verification)
- Node.js ≥ 18 (for frontend development and E2E tests)
- Python 3.11+ (for backend development)
- GitHub OAuth App credentials configured (see main README)

## Setup

### 1. Switch to feature branch

```bash
cd /home/runner/work/github-workflows/github-workflows
git checkout 005-update-app-title
```

### 2. No new dependencies

This feature requires no new packages — it is a pure string replacement.

### 3. Start the application

```bash
docker compose up --build -d
```

- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- API docs: http://localhost:8000/api/docs

### 4. Verify services

```bash
docker compose ps
curl http://localhost:8000/api/v1/health
```

## Implementation Workflow

### Step 1: Replace title strings

Perform find-and-replace of "Agent Projects" → "Happy Place" across all files listed in [data-model.md](data-model.md). Use the exact diffs from [contracts/file-changes.md](contracts/file-changes.md).

Key files to modify:
- [frontend/index.html](../../frontend/index.html) — `<title>` tag
- [frontend/src/App.tsx](../../frontend/src/App.tsx) — `<h1>` elements (2 locations)
- [backend/src/main.py](../../backend/src/main.py) — FastAPI metadata + log messages (4 locations)
- [frontend/e2e/auth.spec.ts](../../frontend/e2e/auth.spec.ts) — Test assertions (5 locations)
- [frontend/e2e/ui.spec.ts](../../frontend/e2e/ui.spec.ts) — Test assertions (2 locations)
- [frontend/e2e/integration.spec.ts](../../frontend/e2e/integration.spec.ts) — Test assertion (1 location)

### Step 2: Update configuration and documentation

- [.devcontainer/devcontainer.json](../../.devcontainer/devcontainer.json) — Container name
- [.devcontainer/post-create.sh](../../.devcontainer/post-create.sh) — Setup message
- [.env.example](../../.env.example) — Header comment
- [backend/pyproject.toml](../../backend/pyproject.toml) — Package description
- [README.md](../../README.md) — Project header
- [backend/README.md](../../backend/README.md) — Backend header and description

### Step 3: Update code comments

- [frontend/src/types/index.ts](../../frontend/src/types/index.ts) — Module docstring
- [frontend/src/services/api.ts](../../frontend/src/services/api.ts) — Module docstring
- [backend/tests/test_api_e2e.py](../../backend/tests/test_api_e2e.py) — Module docstring

### Step 4: Verify no residual references

```bash
grep -rn "Agent Projects" . \
  --include="*.html" --include="*.tsx" --include="*.ts" \
  --include="*.py" --include="*.json" --include="*.md" \
  --include="*.toml" --include="*.sh" \
  | grep -v "specs/" | grep -v "node_modules/"
```

Expected: zero results.

## Verification Checklist

- [ ] Browser tab shows "Happy Place" when app is loaded
- [ ] Login page header (`<h1>`) displays "Happy Place"
- [ ] Authenticated page header (`<h1>`) displays "Happy Place"
- [ ] API docs page (`/api/docs`) shows "Happy Place API" as the title
- [ ] `grep` verification returns zero matches for "Agent Projects" outside `specs/`
- [ ] All existing E2E tests pass with updated assertions
