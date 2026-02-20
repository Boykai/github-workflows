# Quickstart: Update App Title to "Ready Set Go"

**Feature**: 007-app-title-ready-set-go | **Branch**: `007-app-title-ready-set-go`

---

## Prerequisites

- Docker & Docker Compose installed (for full verification)
- Node.js ≥ 18 (for frontend E2E tests)
- Python 3.11+ (for backend tests)

## Setup

### 1. Switch to feature branch

```bash
cd /root/repos/github-workflows
git checkout 007-app-title-ready-set-go
```

### 2. No new dependencies

This feature requires no new dependencies — it is a pure text replacement.

### 3. Start the application (optional — for visual verification)

```bash
docker compose up --build -d
```

- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs

## Implementation Steps

### Step 1: Replace all occurrences

Replace every instance of "Agent Projects" with "Ready Set Go" in the 15 files listed in [data-model.md](data-model.md). Use exact casing "Ready Set Go" in all locations.

### Step 2: Verify completeness

```bash
# This should return zero results:
grep -rn "Agent Projects" --include="*.ts" --include="*.tsx" --include="*.html" \
  --include="*.py" --include="*.json" --include="*.md" --include="*.toml" \
  --include="*.sh" --include="*.yaml" --include="*.yml" . \
  | grep -v node_modules | grep -v ".git/" | grep -v "specs/"
```

### Step 3: Run tests

```bash
# Backend tests
cd backend
python -m pytest tests/ -v
cd ..

# Frontend unit tests
cd frontend
npm run test
cd ..

# Frontend E2E tests (requires running app)
cd frontend
npx playwright test
cd ..
```

## Verification Checklist

- [ ] Browser tab shows "Ready Set Go" when opening http://localhost:5173
- [ ] Login page header displays "Ready Set Go"
- [ ] Authenticated dashboard header displays "Ready Set Go"
- [ ] API docs at http://localhost:8000/docs show "Ready Set Go API" as title
- [ ] `grep -rn "Agent Projects"` returns zero results (excluding specs/ and .git/)
- [ ] All E2E tests pass with updated assertions
- [ ] All backend tests pass
- [ ] All frontend unit tests pass

## Key Files Modified

| File | What Changes |
|------|-------------|
| `frontend/index.html` | `<title>` tag |
| `frontend/src/App.tsx` | Two `<h1>` headers |
| `frontend/e2e/auth.spec.ts` | 5 test assertions |
| `frontend/e2e/ui.spec.ts` | 2 test assertions |
| `frontend/e2e/integration.spec.ts` | 1 test assertion |
| `frontend/src/services/api.ts` | Module docstring |
| `frontend/src/types/index.ts` | Module docstring |
| `backend/src/main.py` | FastAPI title/description + logs |
| `backend/pyproject.toml` | Project description |
| `backend/tests/test_api_e2e.py` | Module docstring |
| `backend/README.md` | Heading + description |
| `.devcontainer/devcontainer.json` | Container name |
| `.devcontainer/post-create.sh` | Setup echo |
| `.env.example` | Header comment |
| `README.md` | Project heading |
