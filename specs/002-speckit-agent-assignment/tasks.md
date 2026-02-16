# Tasks: Spec Kit Custom Agent Assignment by Status

**Input**: Design documents from `/specs/002-speckit-agent-assignment/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Tests are NOT included (not explicitly requested in spec). Existing tests may need updates.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Model & Configuration Changes)

**Purpose**: Update data models and constants for agent mapping support

- [X] T001 Add DEFAULT_AGENT_MAPPINGS constant and replace `custom_agent` field with `agent_mappings: dict[str, list[str]]` on WorkflowConfiguration in backend/src/models/chat.py
- [X] T002 [P] Add PipelineState dataclass with current_agent, is_complete, next_agent properties to backend/src/services/workflow_orchestrator.py
- [X] T003 [P] Add `agent_mappings` field to WorkflowConfiguration TypeScript interface and add AgentNotification interface in frontend/src/types/index.ts

---

## Phase 2: Core Service Changes (US1 - Backlog Agent Assignment)

**Purpose**: Modify workflow to stop at Backlog and assign speckit.specify

- [X] T004 [US1] Add check_agent_completion_comment() method to GitHubProjectsService in backend/src/services/github_projects.py that scans issue comments for `<agent-name>: Done!` marker
- [X] T005 [US1] Add assign_agent_for_status() helper method to WorkflowOrchestrator in backend/src/services/workflow_orchestrator.py that looks up agent_mappings, fetches issue context, and calls assign_copilot_to_issue
- [X] T006 [US1] Refactor execute_full_workflow() in backend/src/services/workflow_orchestrator.py to stop at Backlog status and assign first Backlog agent instead of transitioning to Ready

---

## Phase 3: Polling Extension (US1 + US2 - Completion Detection)

**Purpose**: Extend polling service to detect comment-based agent completion

- [X] T007 [US1] Add check_backlog_issues() function to backend/src/services/copilot_polling.py that polls Backlog issues for speckit.specify completion and transitions to Ready
- [X] T008 [US2] Add check_ready_issues() function to backend/src/services/copilot_polling.py that manages the plan→tasks pipeline and transitions to In Progress on completion
- [X] T009 [US1+US2] Extend poll_for_copilot_completion() loop in backend/src/services/copilot_polling.py to call check_backlog_issues and check_ready_issues before existing checks

---

## Phase 4: In Progress Agent Assignment (US3)

**Purpose**: Assign speckit.implement when issue enters In Progress

- [X] T010 [US3] Refactor handle_ready_status() in backend/src/services/workflow_orchestrator.py to use agent_mappings for In Progress status instead of single custom_agent field

---

## Phase 5: API & Configuration Endpoints (US4)

**Purpose**: Update API endpoints for agent mapping configuration and pipeline state

- [X] T011 [US4] Update GET/PUT /workflow/config endpoints in backend/src/api/workflow.py to include agent_mappings field
- [X] T012 [US4] Add GET /workflow/pipeline-states and GET /workflow/pipeline-states/{issue_number} endpoints to backend/src/api/workflow.py
- [X] T013 [US4] Update confirm_recommendation endpoint in backend/src/api/workflow.py to send agent_assigned WebSocket notification and report Backlog status in result

---

## Phase 6: Polish & Integration

**Purpose**: WebSocket notifications, error handling, test updates

- [X] T014 [P] Add WebSocket notifications for agent_assigned and agent_completed events in backend/src/services/copilot_polling.py using connection_manager.broadcast_to_project
- [X] T015 [P] Update existing tests in backend/tests/unit/test_workflow_orchestrator.py to use agent_mappings instead of custom_agent
- [X] T016 [P] Update existing tests in backend/tests/integration/test_custom_agent_assignment.py to use agent_mappings

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup (T001-T003, parallel)
    ↓
Phase 2: Core Service (T004-T006, sequential)
    ↓
Phase 3: Polling (T007-T009, sequential)
    ↓
Phase 4: In Progress (T010)
    ↓
Phase 5: API (T011-T013, parallel)
    ↓
Phase 6: Polish (T014-T016, parallel)
```

## Summary

| Phase | Tasks | Files Modified |
|-------|-------|---------------|
| Setup | T001-T003 | chat.py, workflow_orchestrator.py, index.ts |
| Core | T004-T006 | github_projects.py, workflow_orchestrator.py |
| Polling | T007-T009 | copilot_polling.py |
| In Progress | T010 | workflow_orchestrator.py |
| API | T011-T013 | workflow.py |
| Polish | T014-T016 | copilot_polling.py, tests |

**Total Tasks**: 16
