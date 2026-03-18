# Quickstart: Debug & Fix Apps Page — New App Creation UX

**Feature**: 051-app-creation-ux | **Date**: 2026-03-18

## Prerequisites

- Python ≥ 3.12 installed
- Node.js ≥ 20 installed
- Docker Compose available
- GitHub personal access token with `repo`, `project`, and `admin:org` scopes
- Repository cloned: `git clone https://github.com/Boykai/github-workflows`

## Environment Setup

```bash
# 1. Copy environment file
cp solune/.env.example solune/.env
# Edit solune/.env with your GitHub token and other secrets

# 2. Start all services
docker compose up -d

# Or run backend/frontend individually for development:
```

## Backend Development

```bash
cd solune/backend

# Install dependencies
pip install -e ".[dev]"

# Run database migrations (auto-applied on startup)
python -m src.services.database

# Start backend server
uvicorn src.main:app --reload --port 8000
```

### Key Files to Modify

| File | Change |
|------|--------|
| `src/models/app.py` | Add `parent_issue_number`, `parent_issue_url` fields |
| `src/services/template_files.py` | Harden `build_template_files()` — return `(files, warnings)` |
| `src/services/app_service.py` | Fix poll timeout, add `_create_app_parent_issue()`, update `delete_app()` |
| `src/migrations/030_app_parent_issue.sql` | New migration — `ALTER TABLE apps ADD COLUMN ...` |

### Running Backend Tests

```bash
cd solune/backend

# Run all app-related unit tests
python -m pytest tests/unit/test_app_service_new_repo.py tests/unit/test_api_apps.py -v

# Run specific test
python -m pytest tests/unit/test_app_service_new_repo.py -v -k "test_parent_issue"

# Run with coverage
python -m pytest tests/unit/ --cov=src --cov-report=term-missing
```

## Frontend Development

```bash
cd solune/frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

### Key Files to Modify

| File | Change |
|------|--------|
| `src/types/apps.ts` | Add `parent_issue_number`, `parent_issue_url` to `App` interface |
| `src/pages/AppsPage.tsx` | Pipeline selector, all-warnings display, success toast |
| `src/components/apps/AppDetailView.tsx` | Parent issue link, pipeline name |
| `src/components/apps/AppCard.tsx` | Pipeline status badge |

### Running Frontend Tests

```bash
cd solune/frontend

# Run all app-related tests
npx vitest run src/pages/AppsPage.test.tsx src/components/apps/

# Run in watch mode
npx vitest src/pages/AppsPage.test.tsx
```

## Verification Checklist

After implementation, verify:

1. **Template Files**: Create new-repo app → check GitHub repo → `.github/agents/`, `.github/prompts/`, `.github/workflows/`, `.specify/`, `.gitignore` all present
2. **Parent Issue**: After creation with pipeline → repo Issues tab → parent issue with tracking table + sub-issues exists
3. **Polling**: Polling service active → first agent assigned within 60s
4. **Pipeline Selector**: Open create dialog → pipeline dropdown visible → `pipeline_id` sent in payload on submit
5. **All Warnings**: Create app with Azure secret failure → ALL warnings shown (not just first)
6. **Detail View**: App detail view → parent issue link and pipeline name displayed
7. **Backend Tests**: `cd solune/backend && python -m pytest tests/unit/test_app_service*.py tests/unit/test_api_apps.py -v`
8. **Frontend Tests**: `cd solune/frontend && npx vitest run src/pages/AppsPage.test.tsx src/components/apps/`

## Implementation Order

The recommended implementation order follows the dependency chain:

1. **Phase 1**: Backend — Template file hardening (no dependencies)
2. **Phase 2**: Backend — Data model + migration (no dependencies)
3. **Phase 3**: Backend — Parent issue creation + pipeline wiring (depends on Phase 2)
4. **Phase 4**: Frontend — Pipeline selector + warnings + detail view (depends on Phases 2–3)
5. **Phase 5**: Tests — Backend + Frontend (depends on Phases 3–4)
