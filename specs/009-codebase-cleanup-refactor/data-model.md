# Data Model: Codebase Cleanup & Refactor

**Feature**: `009-codebase-cleanup-refactor` | **Date**: 2026-02-22

> This feature is a pure refactor — no new database tables, API models, or persistent entities are introduced. This document maps the **module decomposition structure**: which existing modules become packages, what sub-modules they contain, and the dependency relationships between them.

## Module Decomposition Map

### 1. `services/github_projects.py` → `services/github_projects/` package

| Sub-module | Responsibility | Key Exports | Estimated Lines |
|-----------|---------------|-------------|-----------------|
| `__init__.py` | Re-exports all public names for backward compatibility | `GitHubProjectsService`, `github_projects_service`, all GraphQL constants | ~40 |
| `service.py` | Main service class, singleton instance, HTTP client management | `GitHubProjectsService`, `github_projects_service` | ~500 |
| `graphql.py` | GraphQL query/mutation strings and fragments | `PROJECT_FIELDS_FRAGMENT`, `LIST_USER_PROJECTS_QUERY`, etc. | ~400 |
| `issue_ops.py` | Issue CRUD: create, update, get, search, sub-issues | `create_issue()`, `update_issue_body()`, `create_sub_issue()` | ~600 |
| `pr_ops.py` | PR detection, completion checking, timeline events | `check_copilot_pr_completion()`, `get_pr_timeline_events()` | ~500 |
| `board_ops.py` | Board data retrieval and transformation | `get_board_data()`, `_parse_projects()` | ~400 |
| `copilot_assignment.py` | Copilot agent assignment (GraphQL + REST paths) | `assign_copilot_to_issue()` | ~400 |

**Dependency direction**: All sub-modules may import from `service.py` (for the client). `service.py` delegates to sub-modules. No sub-module imports from another sub-module (star topology).

### 2. `services/copilot_polling.py` → `services/copilot_polling/` package

| Sub-module | Responsibility | Key Exports | Estimated Lines |
|-----------|---------------|-------------|-----------------|
| `__init__.py` | Re-exports all public names | `start_polling()`, `stop_polling()`, `get_polling_status()`, etc. | ~50 |
| `state.py` | All module-level mutable state (global dicts/sets) | `_polling_state`, `_polling_task`, `_processed_issue_prs`, `_posted_agent_outputs`, `_claimed_child_prs`, `_pending_agent_assignments`, etc. | ~80 |
| `polling_loop.py` | Polling lifecycle: start/stop/tick, scheduling | `start_polling()`, `stop_polling()`, `_poll_loop()` | ~500 |
| `agent_output.py` | Extract and post agent outputs from PRs | `post_agent_outputs_from_pr()`, file content extraction | ~500 |
| `pipeline.py` | Pipeline advancement and transition logic | `_advance_pipeline()`, `_transition_after_pipeline_complete()` | ~500 |
| `recovery.py` | Stalled issue recovery, cooldown management | `recover_stalled_issues()`, cooldown logic | ~400 |
| `completion.py` | PR completion detection (main + child PRs) | `_check_main_pr_completion()`, `_find_completed_child_pr()`, `_check_child_pr_completion()` | ~500 |

**Dependency direction**: All sub-modules import from `state.py` for shared state. `polling_loop.py` orchestrates calls to other sub-modules. No direct imports between non-loop sub-modules.

### 3. `services/workflow_orchestrator.py` → `services/workflow_orchestrator/` package

| Sub-module | Responsibility | Key Exports | Estimated Lines |
|-----------|---------------|-------------|-----------------|
| `__init__.py` | Re-exports all public names | `WorkflowOrchestrator`, `get_workflow_config()`, etc. | ~40 |
| `models.py` | Shared data classes (breaks circular dependency) | `WorkflowContext`, `PipelineState`, `WorkflowState`, `WorkflowConfig` | ~150 |
| `config.py` | Workflow config load/persist/defaults | `get_workflow_config()`, `_load_workflow_config_from_db()`, `_persist_workflow_config_to_db()` | ~300 |
| `transitions.py` | Status transition logic, review assignment | `handle_in_progress_status()`, `handle_completion()`, `_transition_to_in_review()` | ~500 |
| `orchestrator.py` | Main orchestrator class, agent assignment | `WorkflowOrchestrator`, `assign_agent_for_status()` | ~500 |

**Dependency direction**: `models.py` is a leaf — imported by all other sub-modules and by `copilot_polling`. `config.py` imports from `models.py`. `transitions.py` imports from `models.py` and `config.py`. `orchestrator.py` imports from all.

### 4. `models/chat.py` → split into focused model files

| Target File | Models Moved | Estimated Lines |
|------------|-------------|-----------------|
| `models/chat.py` (trimmed) | `ChatMessage`, `ChatMessageRequest`, `ChatMessagesResponse`, `AVAILABLE_LABELS` (removed — use `constants.py`) | ~80 |
| `models/workflow.py` (new) | `StatusChangeRecommendation`, `IssueRecommendation`, `IssueRecommendationRequest`, `WorkflowConfig*` models | ~120 |
| `models/agent.py` (new) | `AgentConfig`, `AgentMapping`, `AgentAssignment`-related models | ~80 |
| `models/recommendation.py` (new) | `AITaskProposal`, `ProposalConfirmRequest`, `ProposalResponse` | ~80 |

## Shared Utilities (New Extraction Points)

| Utility | Location | Replaces |
|---------|----------|----------|
| `resolve_repository(project, settings)` | `backend/src/services/common.py` or `backend/src/utils.py` | Duplicated in `api/chat.py`, `api/tasks.py`, `api/workflow.py` |
| `start_copilot_polling(...)` | `services/copilot_polling/__init__.py` (public API) | Duplicated startup logic in `api/chat.py`, `api/projects.py`, `api/workflow.py` |
| `_row_to_session(row)` | `services/session_store.py` (private helper) | Duplicated in `get_session()` and `get_sessions_by_user()` |
| `_upsert_row(db, table, ...)` | `services/settings_store.py` (private helper) | Duplicated in `upsert_user_preferences()` and `upsert_project_settings()` |
| `_transition_to_in_review(...)` | `services/workflow_orchestrator/transitions.py` | Duplicated in `handle_in_progress_status()` and `handle_completion()` |
| `utcnow()` | `backend/src/utils.py` | 30+ `datetime.utcnow()` calls |
| `LABELS` | `backend/src/constants.py` | `PREDEFINED_LABELS` in `prompts/` + `AVAILABLE_LABELS` in `models/` |

## Frontend Extraction Points

| Utility | Location | Replaces |
|---------|----------|----------|
| `StatusChangeProposal` type | `frontend/src/types/index.ts` | Duplicate definitions in `useChat.ts` and `ChatInterface.tsx` |
| `generateId()` | `frontend/src/utils/generateId.ts` | Duplicated in `useAgentConfig.ts` and `AgentPresetSelector.tsx` |
| `formatTimeAgo(date)` | `frontend/src/utils/formatTime.ts` | `formatLastUpdated()` in `ProjectBoardPage.tsx` + `formatLastUpdate()` in `ProjectSidebar.tsx` |
| `useSettingsForm<T>(serverState)` | `frontend/src/hooks/useSettingsForm.ts` | Identical form-state pattern in 4 settings components |
| Frontend constants | `frontend/src/constants.ts` | Magic numbers in `useChat.ts`, `useRealTimeSync.ts`, `useProjectBoard.ts`, etc. |
| Workflow/Agent API endpoints | `frontend/src/services/api.ts` | Raw `fetch()` in `useWorkflow.ts` and `useAgentConfig.ts` |

## Dependency Graph (Post-Decomposition)

```
api/ layer
  ├── imports from services/ (via DI or direct import)
  └── imports from models/

services/ layer
  ├── github_projects/
  │     ├── service.py (uses httpx client)
  │     ├── graphql.py (pure data)
  │     ├── issue_ops.py → service.py
  │     ├── pr_ops.py → service.py
  │     ├── board_ops.py → service.py
  │     └── copilot_assignment.py → service.py
  │
  ├── copilot_polling/
  │     ├── state.py (pure data)
  │     ├── polling_loop.py → state.py, agent_output, pipeline, recovery, completion
  │     ├── agent_output.py → state.py
  │     ├── pipeline.py → state.py, workflow_orchestrator/models
  │     ├── recovery.py → state.py
  │     └── completion.py → state.py
  │
  ├── workflow_orchestrator/
  │     ├── models.py (LEAF — no service imports)
  │     ├── config.py → models.py
  │     ├── transitions.py → models.py, config.py
  │     └── orchestrator.py → models.py, config.py, transitions.py
  │
  └── other services (unchanged): ai_agent, cache, database, etc.

models/ layer (pure data, no service imports)
  ├── chat.py (trimmed)
  ├── workflow.py (new)
  ├── agent.py (new)
  ├── recommendation.py (new)
  └── existing: board.py, project.py, settings.py, task.py, user.py

constants.py (LEAF — imported by models, services, prompts)
utils.py (LEAF — imported by services)
```

**No circular dependencies** in this graph. `workflow_orchestrator/models.py` and `copilot_polling/state.py` are leaf nodes that break the current cycle.
