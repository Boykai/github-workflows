# Quickstart: Housekeeping Issue Templates with Configurable Triggers

**Feature**: 014-housekeeping-triggers | **Date**: 2026-02-28

## Prerequisites

- Python 3.12+
- Node.js 20+
- npm (ships with Node.js)
- A configured GitHub Project board with an agent pipeline

## Setup

### Backend

```bash
cd backend
pip install -e ".[dev]"
```

### Frontend

```bash
cd frontend
npm ci
```

## Running the Application

### Backend Server

```bash
cd backend
uvicorn src.main:app --reload --port 8000
```

### Frontend Dev Server

```bash
cd frontend
npm run dev
```

## Key Directories

| Path | Description |
|------|-------------|
| `backend/src/models/housekeeping.py` | Pydantic models for housekeeping tasks, templates, trigger events |
| `backend/src/services/housekeeping/` | Housekeeping service package (CRUD, trigger evaluation, execution) |
| `backend/src/services/housekeeping/service.py` | Main service class (HousekeepingService) |
| `backend/src/services/housekeeping/scheduler.py` | Time-based trigger scheduler logic |
| `backend/src/services/housekeeping/counter.py` | Count-based trigger evaluator |
| `backend/src/services/housekeeping/seed.py` | Built-in seed templates data |
| `backend/src/api/housekeeping.py` | FastAPI router with housekeeping endpoints |
| `backend/src/migrations/006_housekeeping.sql` | Database migration for new tables |
| `frontend/src/components/housekeeping/` | React components for housekeeping UI |
| `frontend/src/hooks/useHousekeeping.ts` | Custom hook for housekeeping API calls |
| `.github/workflows/housekeeping-cron.yml` | GitHub Actions scheduled workflow for time-based triggers |

## API Endpoints

All endpoints are prefixed with `/api/v1/housekeeping`. See [contracts/housekeeping-api.md](./contracts/housekeeping-api.md) for full API documentation.

### Templates

```bash
# List all templates
curl http://localhost:8000/api/v1/housekeeping/templates

# Create a custom template
curl -X POST http://localhost:8000/api/v1/housekeeping/templates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Custom Review",
    "title_pattern": "📋 {task_name} – {date}",
    "body_content": "## Custom Review\n\nPerform these checks..."
  }'
```

### Tasks

```bash
# List tasks for a project
curl "http://localhost:8000/api/v1/housekeeping/tasks?project_id=PVT_abc123"

# Create a time-based task (weekly on Monday at 9 AM)
curl -X POST http://localhost:8000/api/v1/housekeeping/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Weekly Security Review",
    "description": "Automated weekly security review",
    "template_id": "<template-uuid>",
    "trigger_type": "time",
    "trigger_value": "0 9 * * 1",
    "project_id": "PVT_abc123"
  }'

# Create a count-based task (every 10 issues)
curl -X POST http://localhost:8000/api/v1/housekeeping/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bug Bash Every 10 Issues",
    "template_id": "<template-uuid>",
    "trigger_type": "count",
    "trigger_value": "10",
    "project_id": "PVT_abc123"
  }'

# Manually trigger a task
curl -X POST http://localhost:8000/api/v1/housekeeping/tasks/<task-uuid>/run

# Manually trigger (force, skip cooldown)
curl -X POST "http://localhost:8000/api/v1/housekeeping/tasks/<task-uuid>/run?force=true"

# View task history
curl http://localhost:8000/api/v1/housekeeping/tasks/<task-uuid>/history
```

## Running Tests

### Backend

```bash
cd backend

# Run all tests
pytest

# Run housekeeping-specific tests
pytest tests/unit/test_housekeeping.py -v

# Run with coverage
pytest --cov=src --cov-report=term-missing
```

### Frontend

```bash
cd frontend

# Run all unit tests
npm test

# Run in watch mode
npm run test:watch
```

## Linting and Type Checking

### Backend

```bash
cd backend

# Lint
ruff check src tests

# Format check
ruff format --check src tests

# Type check
pyright src
```

### Frontend

```bash
cd frontend

# Lint
npm run lint

# Type check
npm run type-check

# Build
npm run build
```

## Development Workflow

### 1. Database Migration
The `006_housekeeping.sql` migration automatically runs on application startup (handled by `database.py`'s migration runner). Built-in seed templates are inserted during migration.

### 2. Backend Development
1. Add/modify Pydantic models in `backend/src/models/housekeeping.py`
2. Implement service logic in `backend/src/services/housekeeping/service.py`
3. Add API endpoints in `backend/src/api/housekeeping.py`
4. Register the router in `backend/src/main.py`

### 3. Frontend Development
1. Add API methods in `frontend/src/services/api.ts`
2. Create the `useHousekeeping` hook in `frontend/src/hooks/`
3. Build UI components in `frontend/src/components/housekeeping/`
4. Add routing/navigation to the housekeeping page

### 4. GitHub Actions Workflow
1. Create `.github/workflows/housekeeping-cron.yml`
2. Configure the cron schedule (default: every 15 minutes)
3. The workflow calls `POST /api/v1/housekeeping/evaluate-triggers`

## Built-in Templates

The system ships with three pre-configured templates that are seeded on first run:

| Template | Description | Context |
|----------|-------------|---------|
| Security and Privacy Review | Reviews codebase for security, privacy, and best practices | `#codebase` |
| Test Coverage Refresh | Increases quality testing and coverage, resolves bugs | `#codebase` |
| Bug Bash | Reviews codebase to find and resolve bugs and issues | `#codebase` |

These templates reference the `#codebase` context for the agent pipeline to process. They cannot be deleted but can be duplicated and customized.
