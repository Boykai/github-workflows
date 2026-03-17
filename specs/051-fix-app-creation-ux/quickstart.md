# Quickstart: Debug & Fix Apps Page — New App Creation UX

**Feature**: `051-fix-app-creation-ux` | **Date**: 2026-03-17

## Prerequisites

- Docker and Docker Compose installed
- GitHub Personal Access Token with `repo`, `project`, `admin:org` scopes
- Node.js 18+ and Python 3.11+
- Clone of the `github-workflows` monorepo

## Setup

### 1. Environment

```bash
# From repo root
cp solune/.env.example solune/.env
# Edit solune/.env — set GITHUB_TOKEN, DATABASE_URL, etc.
```

### 2. Start Services

```bash
docker compose up -d
```

### 3. Run Database Migrations

Migrations run automatically on backend startup. To verify the new migration:

```bash
# Check that migration 029 was applied
cd apps/solune/backend
sqlite3 path/to/db.sqlite ".schema apps" | grep parent_issue
# Expected: parent_issue_number INTEGER, parent_issue_url TEXT
```

### 4. Install Dependencies

```bash
# Backend
cd apps/solune/backend
pip install -e ".[dev]"

# Frontend
cd apps/solune/frontend
npm install
```

## Development Workflow

### Backend Changes

Key files to modify:

```
apps/solune/backend/src/
├── models/app.py                    # Add parent_issue_number, parent_issue_url
├── services/
│   ├── template_files.py            # Harden build_template_files()
│   └── app_service.py               # Fix poll timeout, add pipeline setup
└── migrations/
    └── 029_app_parent_issue.sql     # New migration
```

### Frontend Changes

Key files to modify:

```
apps/solune/frontend/src/
├── types/apps.ts                    # Add parent_issue_number, parent_issue_url
├── pages/AppsPage.tsx               # Pipeline selector, warnings, success toast
└── components/apps/
    ├── AppDetailView.tsx            # Parent issue link, pipeline info
    └── AppCard.tsx                  # Pipeline badge
```

## Running Tests

### Backend

```bash
cd apps/solune/backend
python -m pytest tests/unit/test_app_service_new_repo.py -v
python -m pytest tests/unit/test_api_apps.py -v
```

### Frontend

```bash
cd apps/solune/frontend
npx vitest run src/pages/AppsPage.test.tsx
npx vitest run src/components/apps/
```

### Linting

```bash
# Backend
cd apps/solune/backend
ruff check src tests
ruff format --check src tests
bandit -r src/ -ll -ii --skip B104,B608
pyright src

# Frontend
cd apps/solune/frontend
npx eslint src/
npx tsc --noEmit
```

## Verification Steps

### Manual E2E Test

1. **Create new-repo app with pipeline**:
   - Open Solune dashboard → Apps page
   - Click "Create New App"
   - Fill in name, description
   - Select repo type = "new-repo"
   - Select a pipeline from the dropdown
   - Click Create

2. **Verify repository**:
   - Open the created GitHub repo
   - Confirm `.github/agents/`, `.github/prompts/`, `.github/workflows/`, `.specify/`, `.gitignore` are all present

3. **Verify Parent Issue**:
   - Open the repo's Issues tab
   - Confirm a "Build {app name}" issue exists
   - Confirm it has a tracking table in the body
   - Confirm sub-issues are linked

4. **Verify polling**:
   - Check backend logs for polling start
   - Wait ~60s — first agent should be assigned

5. **Verify frontend**:
   - Check success toast shows structured summary
   - Check all warnings are displayed (if any)
   - Navigate to app detail → parent issue link is clickable
   - Go to apps list → pipeline badge is shown on card

6. **Verify backward compatibility**:
   - View an app created before this feature
   - Confirm no errors, parent issue section is absent

7. **Verify deletion**:
   - Delete an app that has a parent issue
   - Confirm the GitHub issue is closed (not deleted)

## Architecture Notes

### Best-Effort Pattern

All non-critical operations (template file copying, Azure secrets, Parent Issue creation, sub-issue creation, polling start) follow the **best-effort** pattern:

```python
try:
    result = await some_optional_operation()
except Exception as exc:
    warnings.append(f"Operation failed: {exc}")
    logger.warning("Operation failed", exc_info=True)
```

The app is always created successfully; failures are surfaced as warnings to the user.

### Pipeline Setup Flow

```
create_app_with_new_repo()
  ├── create_repo()
  ├── poll_branch_readiness()          # exponential backoff
  ├── commit_template_files()          # warnings collected
  ├── store_azure_secrets()            # best-effort
  ├── create_project_v2()              # best-effort
  ├── [if pipeline_id]:
  │   ├── load_workflow_config()
  │   ├── create_parent_issue()        # best-effort
  │   ├── add_to_project()
  │   ├── create_sub_issues()          # best-effort
  │   ├── init_pipeline_state()
  │   └── ensure_polling_started()     # best-effort
  └── insert_app_record()
```

### Reference Patterns

- **Parent Issue creation**: See `_create_parent_issue_sub_issues()` in `apps/solune/backend/src/api/tasks.py`
- **Full workflow**: See `execute_full_workflow()` in `apps/solune/backend/src/services/workflow_orchestrator/orchestrator.py`
- **Tracking table**: See `append_tracking_to_body()` in `apps/solune/backend/src/services/agent_tracking.py`
- **Polling**: See `ensure_polling_started()` in `apps/solune/backend/src/services/copilot_polling/polling_loop.py`
