# Quickstart: Codebase Cleanup & Refactor

**Feature**: `009-codebase-cleanup-refactor` | **Date**: 2026-02-22

## Prerequisites

- Python 3.11+ (`python3 --version`)
- Node.js 18+ (`node --version`)
- Docker & Docker Compose (`docker compose version`)

## Environment Setup

```bash
# Clone and switch to feature branch
git checkout 009-codebase-cleanup-refactor

# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Frontend
cd ../frontend
npm install
```

## Build & Verify

### Backend

```bash
cd backend

# Run all tests (primary regression gate)
python -m pytest tests/ -v

# Type checking
pyright src/

# Verify no circular imports (should exit 0 with no output)
python -c "
import importlib, sys
modules = [
    'src.services.copilot_polling',
    'src.services.workflow_orchestrator',
    'src.services.github_projects',
]
for m in modules:
    importlib.import_module(m)
print('No circular import errors')
"

# Verify no deprecated datetime.utcnow() calls (SC-002)
grep -rn 'datetime\.utcnow()' src/ && echo 'FAIL: deprecated calls found' || echo 'PASS: no deprecated calls'

# Verify no dead code artifacts remain (spot check)
grep -rn 'class RateLimiter' src/ && echo 'FAIL: dead code found' || echo 'PASS: RateLimiter removed'
```

### Frontend

```bash
cd frontend

# Build (catches TypeScript and import errors)
npm run build

# Unit tests
npm run test -- --run

# Verify no unused components (spot check)
grep -rn 'ErrorToast\|ErrorBanner\|RateLimitIndicator' src/ && echo 'FAIL: dead components found' || echo 'PASS: dead components removed'
```

### Full Stack (Docker)

```bash
# From repo root
docker compose build
docker compose up -d

# Health check — backend responds
curl -sf http://localhost:8000/health && echo ' OK' || echo ' FAIL'

# Tear down
docker compose down
```

## Verification Checklist

After each user story merge, verify:

| Check | Command | Expected |
|-------|---------|----------|
| Backend tests pass | `cd backend && python -m pytest tests/ -v` | All green |
| Frontend tests pass | `cd frontend && npm run test -- --run` | All green |
| Frontend builds | `cd frontend && npm run build` | Exit 0, no errors |
| No circular imports | Python import check above | No `ImportError` |
| Docker starts | `docker compose up -d && curl localhost:8000/health` | 200 OK |
| No deprecated `utcnow()` | `grep -rn 'datetime\.utcnow()' backend/src/` | No matches (after Story 5) |
| LOC reduced ≥10% (SC-008) | `find backend/src frontend/src -name '*.py' -o -name '*.ts' -o -name '*.tsx' \| xargs wc -l` | ≤22,846 lines (from 25,385) |

## Story-by-Story Verification

### Story 1 — Dead Code Removal (P1)
```bash
# Confirm removed symbols have zero references
grep -rn 'RateLimiter\|ErrorToast\|ErrorBanner\|RateLimitIndicator\|identify_target_status' backend/src/ frontend/src/
# Expected: no output
```

### Story 2 — Module Decomposition (P1)
```bash
# Confirm packages exist
ls backend/src/services/github_projects/__init__.py
ls backend/src/services/copilot_polling/__init__.py
ls backend/src/services/workflow_orchestrator/__init__.py

# Confirm old monolithic files are gone
test ! -f backend/src/services/github_projects.py && echo 'PASS' || echo 'FAIL: old file still exists'
test ! -f backend/src/services/copilot_polling.py && echo 'PASS' || echo 'FAIL: old file still exists'
test ! -f backend/src/services/workflow_orchestrator.py && echo 'PASS' || echo 'FAIL: old file still exists'

# Run tests to confirm backward-compatible imports
python -m pytest tests/ -v
```

### Story 3 — Backend DRY (P2)
```bash
# Verify shared utilities exist
grep -l 'def resolve_repository' backend/src/services/common.py backend/src/utils.py 2>/dev/null
grep -l 'def utcnow' backend/src/utils.py 2>/dev/null

# Run tests
python -m pytest tests/ -v
```

### Story 4 — Frontend DRY (P2)
```bash
# Verify shared utilities exist
ls frontend/src/utils/generateId.ts
ls frontend/src/utils/formatTime.ts
ls frontend/src/hooks/useSettingsForm.ts

# Build + test
cd frontend && npm run build && npm run test -- --run
```

### Story 5 — Deprecation Fixes (P2)
```bash
# Zero deprecated calls
grep -rn 'datetime\.utcnow()\|get_event_loop()\.time()' backend/src/
# Expected: no output

# Verify aware datetimes serialize correctly
python -c "from datetime import datetime, UTC; print(datetime.now(UTC).isoformat())"
# Expected: output ends with +00:00
```

### Story 6 — Structural Organization (P3)
```bash
# Verify model split
ls backend/src/models/workflow.py backend/src/models/agent.py backend/src/models/recommendation.py

# Verify error boundary exists
grep -l 'ErrorBoundary' frontend/src/components/common/ErrorBoundary.tsx

# Full test suite
cd backend && python -m pytest tests/ -v
cd ../frontend && npm run build && npm run test -- --run
```

## Performance Baseline (SC-011)

Capture before refactoring to compare after:

```bash
# Backend startup time
time python -c "from src.main import app; print('started')"

# API response latency (requires running server)
# Run 100 requests, check p95
for i in $(seq 1 100); do
  curl -s -o /dev/null -w '%{time_total}\n' http://localhost:8000/health
done | sort -n | awk 'NR==95{print "p95:", $1, "seconds"}'
```
