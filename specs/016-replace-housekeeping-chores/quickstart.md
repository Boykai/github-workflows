# Quickstart: Replace Housekeeping with Chores

**Feature**: 016-replace-housekeeping-chores  
**Branch**: `016-replace-housekeeping-chores`

## Prerequisites

- Docker + docker-compose running (existing setup)
- GitHub Personal Access Token configured in app settings
- A GitHub Project configured in the app with an agent pipeline

## Implementation Order

### Phase 0: Remove Housekeeping (Foundation)

1. **Create migration** `backend/src/migrations/010_chores.sql` — drops housekeeping tables, creates `chores` table
2. **Delete housekeeping files**:
   - `backend/src/models/housekeeping.py`
   - `backend/src/services/housekeeping/` (entire directory)
   - `backend/src/api/housekeeping.py`
   - `frontend/src/components/housekeeping/` (entire directory)
   - `frontend/src/hooks/useHousekeeping.ts`
3. **Update imports** in `backend/src/api/__init__.py` — remove housekeeping router, add chores router
4. **Update main.py** — remove `HousekeepingService.initialize()` from lifespan
5. **Remove housekeeping test files** and update any references

### Phase 1: Backend Data Layer (Models + Service CRUD)

1. Create `backend/src/models/chores.py` — Pydantic models per data-model.md
2. Create `backend/src/services/chores/__init__.py`
3. Create `backend/src/services/chores/service.py` — `ChoresService` with CRUD: create, list, get, update, delete
4. Create `backend/src/services/chores/counter.py` — count-based trigger logic
5. Create `backend/src/services/chores/scheduler.py` — time-based trigger logic

### Phase 2: Backend Template Builder + GitHub Integration

1. Create `backend/src/services/chores/template_builder.py`:
   - `build_template(name, content)` — generates `.md` with YAML front matter
   - `commit_template_to_repo(...)` — branch + commit + PR workflow using `github_service`
   - Sparse input detection heuristic

### Phase 3: Backend API Endpoints

1. Create `backend/src/api/chores.py` — REST endpoints per contracts/chores-api.yaml
2. Register router in `backend/src/api/__init__.py`

### Phase 4: Backend Trigger Evaluation + Agent Pipeline

1. Add trigger evaluation logic to `ChoresService`:
   - `evaluate_time_triggers(project_id)` — CAS-based time trigger evaluation
   - `evaluate_count_triggers(project_id, current_count)` — count-based evaluation
   - `trigger_chore(chore, ctx)` — create issue + execute agent pipeline via `WorkflowOrchestrator`
2. Add `POST /chores/evaluate-triggers` endpoint
3. Wire trigger execution to `WorkflowOrchestrator.create_all_sub_issues()`

### Phase 5: Backend Chat Flow

1. Add chat conversation state management in `ChoresService` or dedicated module
2. Add `POST /chores/{project_id}/chat` endpoint using `AIAgentService`

### Phase 6: Frontend — Chores Panel

1. Create `frontend/src/hooks/useChores.ts` — React Query hooks for CRUD
2. Create `frontend/src/components/chores/ChoresPanel.tsx` — panel container
3. Create `frontend/src/components/chores/ChoreCard.tsx` — per-chore display
4. Create `frontend/src/components/chores/ChoreScheduleConfig.tsx` — schedule editor
5. Modify `frontend/src/pages/ProjectBoardPage.tsx` — integrate ChoresPanel

### Phase 7: Frontend — Add Chore Modal + Chat Flow

1. Create `frontend/src/components/chores/AddChoreModal.tsx` — creation modal
2. Create `frontend/src/components/chores/ChoreChatFlow.tsx` — embedded chat for sparse input

### Phase 8: Tests

1. Backend unit tests: `test_chores_service.py`, `test_chores_api.py`, `test_chores_scheduler.py`, `test_chores_counter.py`
2. Frontend tests: `ChoresPanel.test.tsx`, `AddChoreModal.test.tsx`, `ChoreScheduleConfig.test.tsx`

## Verification

```bash
# Backend tests
cd backend && python -m pytest tests/ -v

# Frontend tests
cd frontend && npx vitest run

# Full app
docker-compose up --build
# Navigate to project board → verify Chores panel on right side
# Click "Add Chore" → verify modal
# Create a chore → verify it appears in panel
# Configure schedule → verify "Until next trigger" display
```

## Key Files Reference

| Purpose | File |
|---------|------|
| Data model spec | [data-model.md](data-model.md) |
| API contract | [contracts/chores-api.yaml](contracts/chores-api.yaml) |
| Research decisions | [research.md](research.md) |
| Feature spec | [spec.md](spec.md) |
| Migration template | `backend/src/migrations/010_chores.sql` |
| Router registration | `backend/src/api/__init__.py` |
| App startup | `backend/src/main.py` (lifespan) |
| Project board page | `frontend/src/pages/ProjectBoardPage.tsx` |
