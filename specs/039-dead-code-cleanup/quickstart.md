# Quickstart: Dead Code & Technical Debt Cleanup Implementation

**Feature**: 039-dead-code-cleanup
**Date**: 2026-03-13

## Prerequisites

- Python 3.12+ (backend)
- Node.js 22+ (frontend)
- Git

## Repository Setup

```bash
cd /path/to/github-workflows

# Backend
cd backend
pip install -e ".[dev]"

# Frontend
cd ../frontend
npm install
```

## Key Files to Modify

### Phase 1: Build Artifacts & Obvious Waste (Steps 1–5)

| File | Purpose | What to Change |
|------|---------|---------------|
| `backend/htmlcov/` | Coverage reports (gitignored) | Delete directory |
| `frontend/coverage/` | Coverage reports (gitignored) | Delete directory |
| `frontend/e2e-report/` | E2E reports (gitignored) | Delete if exists |
| `frontend/test-results/` | Test results (gitignored) | Delete if exists |
| `frontend/src/components/settings/DynamicDropdown.tsx` | Duplicate formatTimeAgo | Replace local function with import from `@/utils/formatTime` |
| `frontend/src/utils/formatTime.ts` | Canonical formatTimeAgo | Import target (no changes needed) |
| `frontend/src/hooks/useChatHistory.ts` | Legacy storage cleanup | Audit and annotate or remove `clearLegacyStorage` |
| `backend/src/models/recommendation.py` | "Temporary" docstring | Update `AITaskProposal` docstring to permanent |
| `docs/configuration.md` | Stale migration count | Update "001 through 020" → "001 through 022", annotate historical migrations |

### Phase 2: Legacy Pipeline Migration Code (Steps 6–10)

| File | Purpose | What to Change |
|------|---------|---------------|
| `backend/src/services/agent_tracking.py` | Legacy regex | Add `DEPRECATED(v2.0)` to `_ROW_RE_OLD` |
| `backend/src/services/copilot_polling/pipeline.py` | Legacy pipeline path | Add `DEPRECATED(v2.0)` to all legacy references |
| `backend/src/models/pipeline.py` | Deprecated fields | Add deprecation timeline to `agents`, `execution_mode` |
| `backend/src/services/pipelines/service.py` | Legacy normalization | Add encounter logging |
| `frontend/src/types/index.ts` | Deprecated TS fields | Add `@deprecated` JSDoc to `old_status`, `agents`, `execution_mode` |
| `frontend/src/lib/pipelineMigration.ts` | Runtime migration | Reference for adoption monitoring |
| `frontend/src/hooks/useScrollLock.ts` | Test utility | Add `@internal` to `_resetForTesting` |

### Phase 3: DRY Consolidation (Steps 11–15)

| File | Purpose | What to Change |
|------|---------|---------------|
| `backend/src/logging_utils.py` | Error handler | Reference — `handle_service_error` already exists |
| `backend/src/api/projects.py` | 5 inline catches | Migrate to `handle_service_error` |
| `backend/src/api/webhooks.py` | 4 inline catches | Migrate to `handle_service_error` |
| `backend/src/api/signal.py` | 2 inline catches | Migrate to `handle_service_error` |
| `backend/src/api/auth.py` | 1 inline catch | Migrate to `handle_service_error` |
| `backend/src/api/chores.py` | 1 inline catch | Migrate to `handle_service_error` |
| `backend/src/api/chat.py` | 1 direct candidate + 4 skips | Migrate L952; skip L167/249/389/437 |
| `backend/src/services/cache.py` | Cache utility | Add `cached_fetch` async wrapper |
| `backend/src/api/board.py` | Cache pattern | Adopt `cached_fetch` |
| `backend/src/dependencies.py` | Validation helper | `require_selected_project` already exists |

### Phase 4: Complexity Reduction (Steps 16–20)

| File | Purpose | What to Change |
|------|---------|---------------|
| `backend/src/services/copilot_polling/agent_output.py` | CC=123 | Decompose `post_agent_outputs_from_pr` |
| `backend/src/services/workflow_orchestrator/orchestrator.py` | CC=91 | Decompose `assign_agent_for_status` |
| `backend/src/services/copilot_polling/recovery.py` | CC=72 | Decompose `recover_stalled_issues` |
| `frontend/src/components/settings/GlobalSettings.tsx` | CC=96 | Verify decomposition; extract hook if needed |
| `frontend/src/pages/LoginPage.tsx` | CC=90 | Extract `HeroSection`, `ThemeToggle`, `AuthPanel` |

### Phase 5: Singleton & State Migration Planning (Steps 21–25)

| File | Purpose | What to Change |
|------|---------|---------------|
| `backend/src/services/github_projects/service.py` | Singleton | Document migration plan (17+ import sites) |
| `backend/src/services/github_projects/agents.py` | Singleton | Document migration plan |
| `backend/src/api/chat.py` | In-memory stores | Document SQLite migration plan (15+ code paths) |
| `backend/src/models/chat.py` | Backward-compat aliases | Audit and remove if no consumers |
| `backend/src/prompts/issue_generation.py` | Backward-compat alias | Audit and remove if no consumers |
| `backend/src/api/auth.py` | Backward-compat alias | Audit and remove if no consumers |
| `backend/src/models/settings.py` | Legacy field | Audit `agent_pipeline_mappings` |
| `frontend/src/components/settings/ProjectSettings.tsx` | Legacy UI | Audit agent_pipeline_mappings editing |

## Running Tests

```bash
# Backend tests (targeted by phase)
cd backend
python -m pytest tests/ -v --tb=short

# Backend lint + type check
python -m ruff check src/
python -m pyright src/

# Frontend tests
cd frontend
npx vitest run

# Frontend type check + lint
npm run type-check
npm run lint

# Full test suites (after each phase)
cd backend && python -m pytest tests/ -v
cd frontend && npx vitest run

# E2E smoke test (after Phase 5)
cd frontend && npx playwright test
```

## CGC Checkpoints

Run after every 5 steps:

```bash
# Check for dead code
# (via CGC tools: find_dead_code)

# Compare repository stats against baseline
# Baseline: 465 files, 4653 functions, 803 classes
# (via CGC tools: get_repository_stats)

# Check complexity targets
# (via CGC tools: find_most_complex_functions, calculate_cyclomatic_complexity)
```

## Implementation Order

1. **Phase 1 — Build Artifacts & Obvious Waste** (Steps 1–5)
   - Delete gitignored directories
   - Remove duplicate `formatTimeAgo`
   - Audit `clearLegacyStorage`
   - Fix docstring, update docs
   - CGC Checkpoint 1

2. **Phase 2 — Legacy Pipeline Migration Code** (Steps 6–10)
   - Add deprecation annotations
   - Add migration tracking logging
   - Mark deprecated TS fields
   - Add @internal annotations
   - CGC Checkpoint 2

3. **Phase 3 — DRY Consolidation** (Steps 11–15)
   - Migrate inline error handlers (Step 11)
   - Create `cached_fetch` utility (Step 12, parallel with 11)
   - Adopt `require_selected_project` (Step 13)
   - Verify `pipeline_source` usage (Step 14)
   - Address temp file storage (Step 15)
   - CGC Checkpoint 3

4. **Phase 4 — Complexity Reduction** (Steps 16–20)
   - Decompose 3 backend functions (Steps 16–18)
   - Simplify 2 frontend components (Steps 19–20, parallel with 18)
   - CGC Checkpoint 4

5. **Phase 5 — Singleton & State Migration Planning** (Steps 21–25)
   - Document singleton migration plan (Step 21)
   - Document SQLite migration plan (Step 22)
   - Audit backward-compat aliases (Step 23)
   - Verify agent_pipeline_mappings deprecation (Step 24)
   - Final cleanup sweep (Step 25)
   - CGC Checkpoint 5

## Contracts Reference

- [Error Handling](contracts/error-handling.md) — Consolidated error handling pattern
- [Deprecation Policy](contracts/deprecation-policy.md) — Annotation format and lifecycle
- [Complexity Budget](contracts/complexity-budget.md) — Function decomposition targets and rules

## Success Criteria Quick Reference

| Metric | Target |
|--------|--------|
| Build artifact directories | 0 remaining |
| Duplicate utility functions | 0 remaining |
| Legacy paths with deprecation annotations | 100% (all 8) |
| Inline error handlers | 0 remaining (14 migrated, 4 intentional exceptions) |
| Functions with CC > 40 | 0 remaining |
| Test regressions | 0 |
| Type-check errors | 0 |
| Migration plans documented | 2 (singleton, SQLite) |
