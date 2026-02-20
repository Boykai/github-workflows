# File Changes Contract: Update App Title to "Ready Set Go"

**Feature**: 007-app-title-ready-set-go | **Date**: 2026-02-20

---

## Change Type

**Category**: Text replacement (branding)
**API Changes**: None — the FastAPI `title` and `description` fields change but these are metadata only (visible in `/docs` Swagger UI), not API contract changes.
**Breaking Changes**: None

## Affected Endpoints (metadata only)

The FastAPI app metadata displayed at `/docs` will change:

| Field | Old Value | New Value |
|-------|-----------|-----------|
| `title` | Agent Projects API | Ready Set Go API |
| `description` | REST API for Agent Projects | REST API for Ready Set Go |

No request/response schemas, paths, or authentication requirements change.

## File Change Summary

### Priority 1 — User-Facing (Browser Tab + Header)

| File | Change Description |
|------|-------------------|
| `frontend/index.html` | Update `<title>` tag |
| `frontend/src/App.tsx` | Update both `<h1>` headers |

### Priority 1 — E2E Test Updates (must match user-facing changes)

| File | Change Description |
|------|-------------------|
| `frontend/e2e/auth.spec.ts` | Update 5 title assertions |
| `frontend/e2e/ui.spec.ts` | Update 2 title assertions |
| `frontend/e2e/integration.spec.ts` | Update 1 title assertion |

### Priority 2 — Backend & Configuration

| File | Change Description |
|------|-------------------|
| `backend/src/main.py` | Update FastAPI title/description + log messages |
| `backend/pyproject.toml` | Update project description |
| `backend/tests/test_api_e2e.py` | Update module docstring |
| `backend/README.md` | Update heading + description |
| `.devcontainer/devcontainer.json` | Update container name |
| `.devcontainer/post-create.sh` | Update setup echo message |
| `.env.example` | Update header comment |
| `README.md` | Update project heading |

### Priority 2 — Frontend Docstrings

| File | Change Description |
|------|-------------------|
| `frontend/src/services/api.ts` | Update module docstring |
| `frontend/src/types/index.ts` | Update module docstring |

## Verification

```bash
# After all changes, this command should return zero results:
grep -rn "Agent Projects" --include="*.ts" --include="*.tsx" --include="*.html" \
  --include="*.py" --include="*.json" --include="*.md" --include="*.toml" \
  --include="*.sh" --include="*.yaml" --include="*.yml" . \
  | grep -v node_modules | grep -v ".git/" | grep -v "specs/"
```
