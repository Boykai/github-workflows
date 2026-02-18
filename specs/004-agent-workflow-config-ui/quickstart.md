# Quickstart: Custom Agent Workflow Configuration UI

**Feature**: 004-agent-workflow-config-ui | **Branch**: `004-agent-workflow-config-ui`

---

## Prerequisites

- Docker & Docker Compose installed
- Node.js ≥ 18 (for frontend development outside Docker)
- Python 3.11+ (for backend development outside Docker)
- GitHub OAuth App credentials configured (see main README)
- A GitHub Project with status columns configured

## Setup

### 1. Switch to feature branch

```bash
cd /root/repos/github-workflows
git checkout 004-agent-workflow-config-ui
```

### 2. Install new frontend dependency

```bash
cd frontend
npm install @dnd-kit/core@6.3.1 @dnd-kit/sortable@10.0.0 @dnd-kit/modifiers@9.0.0 @dnd-kit/utilities@3.2.2
cd ..
```

### 3. Start the application

```bash
docker compose up --build -d
```

- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs

### 4. Verify services

```bash
docker compose ps
curl http://localhost:8000/api/v1/health
```

## Development Workflow

### Backend (FastAPI)

```bash
# Run backend outside Docker for faster iteration
cd backend
pip install -e ".[dev]"
uvicorn src.main:app --reload --port 8000
```

Key files to modify:
- [backend/src/models/chat.py](../backend/src/models/chat.py) — `AgentAssignment` model, `WorkflowConfiguration` update
- [backend/src/api/workflow.py](../backend/src/api/workflow.py) — `GET /agents` endpoint
- [backend/src/services/github_projects.py](../backend/src/services/github_projects.py) — `list_available_agents()` method
- [backend/src/services/workflow_orchestrator.py](../backend/src/services/workflow_orchestrator.py) — `get_agent_slugs()` helper

### Frontend (React + TypeScript)

```bash
# Run frontend outside Docker for HMR
cd frontend
npm install
npm run dev
```

Key files to create/modify:
- `frontend/src/components/board/AgentConfigRow.tsx` — Main row container
- `frontend/src/components/board/AgentColumnCell.tsx` — Per-column dnd-kit sortable area
- `frontend/src/components/board/AgentTile.tsx` — Draggable agent card
- `frontend/src/components/board/AddAgentPopover.tsx` — Add agent dropdown
- `frontend/src/components/board/AgentPresetSelector.tsx` — Preset buttons
- `frontend/src/components/board/AgentSaveBar.tsx` — Floating save/discard bar
- `frontend/src/hooks/useAgentConfig.ts` — Agent state management hook
- `frontend/src/types/index.ts` — Updated types

### Running Tests

```bash
# Backend unit tests
cd backend
python -m pytest tests/unit/ -v

# Frontend unit tests
cd frontend
npm run test

# E2E tests
cd frontend
npx playwright test
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/workflow/agents` | List available agents for assignment |
| `GET` | `/api/v1/workflow/config` | Get workflow config (now returns `AgentAssignment[]`) |
| `PUT` | `/api/v1/workflow/config` | Update workflow config (accepts both formats) |

## Verification Checklist

- [ ] Agent configuration row appears above board columns (expanded by default)
- [ ] Row can be collapsed/expanded via toggle button
- [ ] Each status column shows its assigned agents as card tiles
- [ ] "+" button in each column opens agent popover with available agents
- [ ] Agent tiles can be reordered via drag-and-drop within a column
- [ ] Agent tiles can be removed via "X" button
- [ ] Modified columns show visual diff indicators
- [ ] Floating save bar appears when changes are unsaved
- [ ] Save persists config; Discard reverts to server state
- [ ] Preset selector offers Custom, GitHub Copilot, Spec Kit options
- [ ] Selecting a preset shows confirmation dialog before replacing
- [ ] Keyboard navigation works for drag-and-drop (Space to grab, arrows to move)
- [ ] Empty columns show only the "+" button (pass-through in pipeline)
- [ ] Agent count per column respects soft limit of 10 with warning
