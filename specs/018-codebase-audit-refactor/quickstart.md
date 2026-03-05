# Quickstart: Codebase Audit & Refactor

**Feature**: 018-codebase-audit-refactor
**Date**: 2026-03-05

## Overview

This feature refactors the existing codebase in-place. There is no new application to start or new service to deploy. After implementation, the application runs identically to before — same endpoints, same behavior — with cleaner internals, current dependencies, and persistent chat state.

## Prerequisites

- Python 3.11+
- Node.js 18+
- Existing development environment set up per `docs/setup.md`

## Verification Steps

After the refactor is complete, verify with these steps:

### 1. Backend Tests
```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```
All tests must pass. Some test files will have been updated to reflect renamed methods or new parameters.

### 2. Frontend Tests
```bash
cd frontend
npm test
```
All vitest tests must pass.

### 3. Dependency Verification
```bash
# Backend: confirm agent-framework-core is gone
cd backend
pip list | grep agent-framework  # should return nothing

# Frontend: confirm packages are at latest
cd frontend
npm outdated  # should show no outdated packages
```

### 4. Chat Persistence Verification
```bash
# Start the application
cd backend && uvicorn src.main:app --host 0.0.0.0 --port 8000

# In another terminal: send a chat message via the API
curl -X POST http://localhost:8000/api/chat/messages \
  -H "Content-Type: application/json" \
  -d '{"content": "test message", "session_id": "test"}'

# Restart the application (Ctrl+C, then restart)
# Verify the message persists:
curl http://localhost:8000/api/chat/messages?session_id=test
# Should return the previously sent message
```

### 5. Rate Limiting Verification
Watch the application logs during bulk operations. You should see:
- `Throttling: waiting Xms before next GitHub API call` logs when calls are spaced
- Polling interval changes in the copilot polling logs (60s → 120s → 240s → 300s during idle periods)

## Key Changes Summary

| Area | What Changed | Impact |
|------|-------------|--------|
| Dependencies | Removed `agent-framework-core`, bumped all versions | Faster install, smaller footprint |
| Client caching | Single `CopilotClientPool` shared by completion + model fetcher | Fewer connections, proper cleanup |
| Fallback logic | Generic `_with_fallback()` helper | Less boilerplate, consistent error handling |
| Headers | `graphql_features` parameter on `_graphql()` | Cleaner call sites |
| GraphQL model | Parameterized in `ASSIGN_COPILOT_MUTATION` | Any model can be used |
| File deletion | Implemented via `fileChanges.deletions` | Commits can now delete files |
| Chat storage | SQLite-backed (migration 011) | Survives restarts |
| Service init | `app.state` only, no module globals | Clean DI, test-friendly |
| Bounded caches | All in-memory collections bounded | No memory leaks |
| API throttling | 500ms between calls | Rate limits respected |
| Adaptive polling | 60s base, 2x backoff, 5min cap | Less API waste when idle |
