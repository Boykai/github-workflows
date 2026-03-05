# Quickstart: Audit & Refactor FastAPI + React GitHub Projects V2 Codebase

**Feature**: 018-audit-refactor-codebase | **Date**: 2026-03-05

---

## Prerequisites

- Python 3.11+
- Node.js 18+ with npm
- Git

## Setup

```bash
# Clone and checkout the feature branch
git checkout 018-audit-refactor-codebase

# Backend setup
cd backend
pip install -e ".[dev]"

# Frontend setup
cd ../frontend
npm install
```

## Execution Order

This refactor MUST be executed in strict phase order. Each phase builds on the previous.

### Phase 1 — Dependency Modernization

```bash
# 1. Update backend dependencies
cd backend
# Edit pyproject.toml:
#   - Remove "agent-framework-core>=1.0.0a1"
#   - Bump "github-copilot-sdk>=0.1.0" → "github-copilot-sdk>=0.1.30"
#   - Bump "openai>=1.0.0" → "openai>=2.24.0"
#   - Bump "azure-ai-inference>=1.0.0b1" → "azure-ai-inference>=1.0.0b9"
pip install -e ".[dev]"

# 2. Verify backend
pytest                     # All tests must pass
ruff check src/            # No lint errors
ruff format --check src/   # Formatting OK

# 3. Update frontend dependencies
cd ../frontend
# Edit package.json:
#   - Bump "@tanstack/react-query" → "^5.90.7"
#   - Bump "vite" → "^7.3.1" (verify plugin compat)
#   - Bump "@vitejs/plugin-react" accordingly
npm install

# 4. Verify frontend
npm run build              # Build succeeds
npm test                   # All unit tests pass
npm run test:e2e           # E2E tests pass (if CI environment available)
```

### Phase 2 — DRY Consolidation

```bash
cd backend

# 2A. Extract CopilotClientPool
# File: src/services/completion_providers.py
# - Add CopilotClientPool class
# - Refactor CopilotCompletionProvider to use pool
# File: src/services/model_fetcher.py
# - Import and use shared pool from completion_providers

# 2B. Add _with_fallback helper
# File: src/services/github_projects/service.py
# - Add _with_fallback() method to GitHubProjectsService
# - Refactor assign_copilot_to_issue() to use it
# - Refactor review request methods to use it
# - Refactor add_issue_to_project() to use it

# 2C. Unify retry logic
# File: src/services/github_projects/service.py
# - Enhance _request_with_retry() for secondary rate limits
# - Remove inline retry in _graphql() if duplicated

# 2D. Consolidate header builder
# File: src/services/github_projects/service.py
# - Enhance _build_headers() with extra_headers and graphql_features params
# - Update all call sites

# Verify after each sub-phase
pytest
ruff check src/
```

### Phase 3 — Anti-Pattern Remediation

```bash
# 3A. Parameterize model in graphql.py
# File: src/services/github_projects/graphql.py
# - Add $model variable to ASSIGN_COPILOT_MUTATION
# File: src/services/github_projects/service.py
# - Pass model from config at call site

# 3B. Document chat state as MVP
# File: src/api/chat.py
# - Add TODO comments, convert to BoundedDict

# 3C. Implement delete_files
# File: src/services/github_commit_workflow.py
# - Add fileChanges.deletions to GraphQL mutation

# 3D. Document OAuth state bounds
# File: src/services/github_auth.py
# - Add detailed code comments

# 3E. Standardize singleton registration
# File: src/main.py — ensure all services on app.state
# File: src/dependencies.py — remove module-global fallbacks

# 3F. Bound all caches
# Files: Multiple (see data-model.md for full list)
# - Import BoundedDict from utils
# - Replace dict() with BoundedDict(maxlen=N)

# Final verification
pytest                     # All backend tests pass
cd ../frontend
npm test                   # All frontend tests pass
npm run build              # Frontend builds
```

## Verification Checklist

```bash
# Backend
cd backend
pytest -v                           # Zero failures
ruff check src/                     # Zero errors
ruff format --check src/            # Formatted

# Frontend  
cd frontend
npm run build                       # Build succeeds
npm test                            # Zero failures
npm run type-check                  # No type errors

# Smoke test
cd backend
python -c "from src.main import create_app; print('Import OK')"
```

## Key Files to Review

| File | Changes |
|------|---------|
| `backend/pyproject.toml` | Dependency updates |
| `backend/src/services/completion_providers.py` | CopilotClientPool extraction |
| `backend/src/services/model_fetcher.py` | Use shared pool |
| `backend/src/services/github_projects/service.py` | Fallback helper, retry unification, header builder |
| `backend/src/services/github_projects/graphql.py` | Parameterized model |
| `backend/src/api/chat.py` | Bounded caches + MVP documentation |
| `backend/src/services/github_commit_workflow.py` | File deletion implementation |
| `backend/src/services/github_auth.py` | OAuth state documentation |
| `backend/src/main.py` | Singleton registration |
| `backend/src/dependencies.py` | Remove module-global fallbacks |
| `frontend/package.json` | Dependency bumps |

## Rollback

All changes are in-place refactors. If any phase fails:
1. `git stash` or `git checkout -- <file>` to revert individual files
2. Each phase is independently revertible — Phase 3 doesn't depend on Phase 2 changes being present
3. Frontend changes (package.json only) are independent of backend changes
