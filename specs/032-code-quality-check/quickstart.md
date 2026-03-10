# Quickstart: Code Quality Check

**Feature**: 032-code-quality-check
**Date**: 2026-03-10

## Prerequisites

- Python 3.12+ with `uv` package manager
- Node.js 22+ with npm
- Git
- Access to the repository

## Setup

```bash
# Clone and checkout the feature branch
git checkout 032-code-quality-check

# Backend setup
cd backend
uv sync --all-extras
cd ..

# Frontend setup
cd frontend
npm install
cd ..
```

## Verification Commands

### Phase 1: Silent Failures & Security

```bash
# Verify zero except:pass blocks remain
cd backend
grep -rn "except.*:" src/ | grep -c "pass$"
# Expected: 0

# Verify no internal details in Signal responses
grep -rn "TODO(bug-bash)" src/services/signal_chat.py
# Expected: 0 matches (all resolved)

# Verify CORS methods are explicit
grep -A1 "allow_methods" src/main.py
# Expected: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]

# Run backend tests
uv run pytest tests/ -x -q
```

### Phase 2: DRY Consolidation

```bash
# Verify _get_repository_info removed
grep -rn "_get_repository_info" backend/src/
# Expected: 0 matches

# Verify handle_service_error is used
grep -rn "handle_service_error" backend/src/api/
# Expected: Multiple matches across route files

# Verify require_selected_project is used
grep -rn "require_selected_project" backend/src/api/
# Expected: Matches in chat.py, workflow.py, tasks.py, chores.py

# Verify cn() usage in frontend
cd frontend
grep -rn 'className={`' src/components/ | wc -l
# Expected: 0 (all replaced with cn())
```

### Phase 3: Module Decomposition

```bash
# Verify backend service file sizes
wc -l backend/src/services/github_projects/*.py
# Expected: No file exceeds 500 lines

# Verify frontend API module structure
ls frontend/src/services/api/
# Expected: client.ts, projects.ts, chat.ts, agents.ts, tools.ts, board.ts, index.ts

# Verify hook sizes
wc -l frontend/src/hooks/usePipelineConfig.ts
# Expected: ≤100 lines (composition hook)

# Verify all tests pass
cd backend && uv run pytest tests/ -x -q
cd ../frontend && npm test
```

### Phase 4: Type Safety

```bash
# Verify backend type checking passes
cd backend
uv run pyright src/

# Verify frontend strict mode compiles
cd frontend
npm run type-check
# Expected: 0 errors with noUnusedLocals and noUnusedParameters enabled
```

### Phase 5: Technical Debt

```bash
# Verify __import__ removed
grep -rn "__import__" backend/src/
# Expected: 0 matches

# Verify jsdom removed
cd frontend
grep "jsdom" package.json
# Expected: 0 matches

# Verify single test directory
ls -d frontend/src/test* 
# Expected: Only src/test/ (no src/tests/)

# Verify TODO comments resolved
grep -rn "TODO(bug-bash)" backend/src/
# Expected: 0 matches
```

### Phase 6: Performance & Observability

```bash
# Verify bundle analysis available
cd frontend
npm run build
# Expected: Bundle analysis output generated

# Verify AbortSignal in API client
grep -n "signal" frontend/src/services/api/client.ts
# Expected: AbortSignal parameter in request function
```

### Phase 7: Testing & Linting

```bash
# Run backend tests with coverage
cd backend
uv run pytest tests/ --cov=src --cov-report=term-missing

# Run frontend tests with coverage
cd frontend
npm run test -- --coverage

# Run frontend linter
npm run lint
# Expected: 0 errors with import ordering and React rules

# Run type checker
npm run type-check
# Expected: 0 errors
```

## Implementation Order

Execute phases in dependency order:

1. **Phase 1** (P0): Fix exceptions and security — no dependencies
2. **Phase 2** (P1): DRY consolidation — depends on Phase 1 (error handling patterns)
3. **Phase 3** (P2): Module decomposition — depends on Phase 2 (consolidated patterns)
4. **Phase 4** (P2): Type safety — depends on Phase 3 (stable module boundaries)
5. **Phase 5** (P3): Technical debt — depends on Phase 3 (module structure)
6. **Phase 6** (P3): Performance — depends on Phase 3 (API client refactored)
7. **Phase 7** (P4): Testing & linting — depends on all prior phases

## Key Files Quick Reference

| Purpose | File Path |
|---------|-----------|
| Error handling utilities | `backend/src/logging_utils.py` |
| Repository resolution | `backend/src/utils.py` |
| DI dependencies | `backend/src/dependencies.py` |
| CORS configuration | `backend/src/main.py` |
| Signal chat (security) | `backend/src/services/signal_chat.py` |
| GitHub service (split) | `backend/src/services/github_projects/service.py` |
| Frontend API (split) | `frontend/src/services/api.ts` |
| Pipeline hook (split) | `frontend/src/hooks/usePipelineConfig.ts` |
| TypeScript config | `frontend/tsconfig.json` |
| ESLint config | `frontend/eslint.config.js` |
| Vite config | `frontend/vite.config.ts` |
| Dialog base | `frontend/src/components/ui/confirmation-dialog.tsx` |
| Class utility | `frontend/src/lib/utils.ts` |
