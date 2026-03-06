# Quickstart: Full Codebase Review & Refactoring

**Branch**: `023-codebase-review-refactor` | **Date**: 2026-03-06

## Prerequisites

- Python 3.12+ with the backend venv activated: `source backend/.venv/bin/activate`
- Node.js 20+ with frontend dependencies installed: `cd frontend && npm install`
- All current tests passing (verify before starting any phase)

## Verification Commands

Run these after **every** individual change to ensure nothing is broken:

```bash
# Backend tests (from repo root)
cd backend && source .venv/bin/activate
pytest --cov=src --cov-report=term-missing -x

# Backend lint + type check
ruff check src/ tests/
ruff format --check src/ tests/
pyright

# Frontend tests
cd frontend
npm test -- --run

# Frontend lint + type check
npm run lint
npm run type-check

# Full build verification
npm run build
```

## Phase Execution Order

### Phase 1: Dependency Audit (FR-001 through FR-004)

**Backend**:
1. Remove `python-jose[cryptography]>=3.3.0` from `pyproject.toml` — zero imports exist
2. Update remaining dependency version floors one at a time, running tests after each
3. Verify: `pip install -e .` from clean venv + full test suite

**Frontend**:
1. Remove `jsdom` from `package.json` devDependencies
2. Run `npm install` and `npm test -- --run` to verify
3. Investigate `@dnd-kit` peer dependency alignment: `npm ls @dnd-kit/core`
4. Align versions if warnings exist, test board drag-and-drop manually

### Phase 2: Backend DRY Consolidation (FR-005 through FR-009)

**Order matters** — do these sequentially:

1. **Repository resolution** (FR-005): Replace `workflow.py:_get_repository_info()` and `main.py` inline resolution with calls to `utils.resolve_repository()`. Grep to verify zero duplicates remain.

2. **Validation dependency** (FR-007): Add `require_selected_project()` to `dependencies.py`. Update `chat.py` and any other endpoints with inline `selected_project_id` checks.

3. **Error handling adoption** (FR-006): Systematically update each API route file to use `handle_service_error()`. Do one file at a time, test after each.

4. **Cache wrapper** (FR-008): Add `_cycle_cached()` to the service client. Replace 7 inline cache patterns in `service.py`.

5. **Test mock consolidation** (FR-009): Audit test files for duplicate mock setup. Move any duplicates to `conftest.py`.

### Phase 3: Service Decomposition (FR-010 through FR-012)

**High-risk phase** — smallest possible steps:

1. Create `client.py` with `GitHubClient` class. Move HTTP infrastructure methods.
2. Create sub-service modules one at a time: `projects.py` → `board.py` → `issues.py` → `copilot.py` → `pull_requests.py` → `fields.py` → `repository.py`
3. For each module: move methods, update `service.py` to delegate, run full test suite
4. Update `__init__.py` to re-export all public symbols
5. Verify: `wc -l` on each module confirms <800 LOC. Grep for old import paths confirms none remain.

### Phase 4: Initialization Consolidation (FR-013)

1. Ensure all API routes use `Depends(get_github_service)` — most already do
2. Update `github_commit_workflow.py` to accept service as parameter instead of module-level import
3. Remove `github_projects_service` module-level singleton from `service.py`
4. Remove fallback logic from `dependencies.py:get_github_service()`
5. Run full test suite

### Phase 5: Frontend Quality (FR-014 through FR-016)

1. Split `McpSettings.tsx` (459 LOC) into sub-components
2. Split `ChatInterface.tsx` (412 LOC) into sub-components
3. Split `SignalConnection.tsx` (349 LOC) into sub-components
4. Verify: `find frontend/src/components -name "*.tsx" ! -name "*.test.tsx" -exec wc -l {} + | sort -rn | head -5` — all under 300
5. Run `npm run lint` for accessibility checks
6. Run `npm test -- --run` and `npm run build`

### Phase 6: CI & Best Practices (FR-017 through FR-019)

1. Add coverage artifact upload steps to `.github/workflows/ci.yml`
2. Add dependency vulnerability scanning (e.g., `pip-audit` for backend, `npm audit` for frontend)
3. Validate `python-jose` removal was correct (already done in Phase 1)

## Rollback Strategy

Each phase is independently committable. If any phase causes unexpected failures:
1. `git stash` or `git checkout -- <files>` the current phase's changes
2. The previous phase's state is a valid, working baseline
3. All phases are designed to be behavior-preserving — if tests pass, the refactoring is correct
