# Quickstart: Codebase Cleanup Implementation

**Date**: 2026-03-02  
**Feature**: 002-codebase-cleanup  
**Branch**: `002-codebase-cleanup`

## Prerequisites

- Python 3.12 with backend venv activated: `source backend/.venv/bin/activate`
- Node.js with frontend dependencies: `cd frontend && npm install`
- All CI checks currently passing on main branch

## Execution Order

The cleanup tasks should be executed in this order to avoid cascading failures:

### Phase 1: Backend Dead Code Removal (P1)

```bash
# 1. Delete MagicMock artifact files
cd backend && ls | grep "MagicMock" | xargs rm -f

# 2. Remove dead functions and models from source files
# Edit: webhooks.py, agent_tracking.py, counter.py, ai_agent.py, cache.py, settings.py

# 3. Remove backward-compat re-exports from chat.py

# 4. Validate
cd backend && ruff check src/ && pyright src/ && pytest
```

### Phase 2: Backend Stale Test Removal (P2)

```bash
# 1. Remove test classes/methods for dead functions
# Edit: test_agent_tracking.py (TestDetermineNextAction), test_webhooks.py (TestHandleCopilotPrReady)

# 2. Update test imports from chat.py shim to canonical modules
# Edit: test_models.py, test_workflow_orchestrator.py, test_ai_agent.py, etc.

# 3. Remove unused test helpers directory
rm -rf backend/tests/helpers/

# 4. Remove PREDEFINED_LABELS alias and update test
# Edit: issue_generation.py, test_prompts.py

# 5. Validate
cd backend && pytest
```

### Phase 3: Frontend Dead Code Removal (P1)

```bash
# 1. Remove unused components
rm -rf frontend/src/components/housekeeping/
rm frontend/src/components/settings/AIPreferences.tsx

# 2. Remove unused types from types/index.ts
# 3. Remove unused API methods, utils, constants
# 4. Remove unused dependency
cd frontend && npm uninstall socket.io-client

# 5. Validate
cd frontend && npm run lint && npm run type-check && npm run test && npm run build
```

### Phase 4: Frontend Consolidation (P3)

```bash
# 1. Consolidate duplicate formatTimeAgo
# 2. Fix or consolidate STALE_TIME constants

# 3. Validate
cd frontend && npm run lint && npm run type-check && npm run test && npm run build
```

### Phase 5: Dependency Cleanup (P5)

```bash
# Backend: remove unused deps
# Edit: pyproject.toml (remove python-jose, agent-framework-core)
cd backend && pip install -e . && pytest

# Frontend: already done in Phase 3
```

### Phase 6: Commit and PR

```bash
# Use conventional commits:
# chore: remove dead backend functions and MagicMock artifacts
# chore: remove stale tests and unused test helpers
# chore: remove unused frontend components and types
# refactor: consolidate duplicate formatTimeAgo utility
# chore: remove unused dependencies

# Push and open PR with categorized summary
git push origin 002-codebase-cleanup
```

## Validation Checklist

After all changes:

- [ ] `cd backend && ruff check src/` — no errors
- [ ] `cd backend && pyright src/` — no errors
- [ ] `cd backend && pytest` — all tests pass
- [ ] `cd frontend && npm run lint` — no errors
- [ ] `cd frontend && npm run type-check` — no errors
- [ ] `cd frontend && npm run test` — all tests pass
- [ ] `cd frontend && npm run build` — builds successfully
- [ ] No MagicMock files in `backend/` root
- [ ] API routes unchanged (same set of endpoints)
- [ ] PR opened with categorized change summary

## Key Constraints

- **Do not** remove `get_session_dep` alias in `auth.py` — still actively used
- **Do not** remove workflow_orchestrator `__init__.py` re-exports — used by copilot_polling
- **Do not** remove legacy `process_in_progress_issue` path — cannot be statically verified as safe
- **Do not** remove `python-multipart` dep — implicit FastAPI requirement
- **Do not** remove `github-copilot-sdk` dep — dynamically loaded
- **Do not** change any `@router.*` decorator paths or response model types
