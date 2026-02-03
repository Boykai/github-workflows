# Tasks: AI-Assisted GitHub Issue Creation and Workflow Management

**Input**: Design documents from `/specs/001-github-project-workflow/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Tests are NOT included (not explicitly requested in spec). Test examples available in quickstart.md.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Extend existing project structure for workflow feature

- [X] T001 Add RecommendationStatus enum to backend/src/models/chat.py
- [X] T002 [P] Add ActionType.ISSUE_CREATE enum value to backend/src/models/chat.py
- [X] T003 [P] Create issue generation prompt file at backend/src/prompts/issue_generation.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create IssueRecommendation model in backend/src/models/chat.py with fields: recommendation_id, session_id, original_input, title, user_story, ui_ux_description, functional_requirements, status, created_at, confirmed_at
- [X] T005 Create WorkflowConfiguration model in backend/src/models/chat.py with fields: project_id, repository_owner, repository_name, copilot_assignee, review_assignee, status_backlog, status_ready, status_in_progress, status_in_review, enabled
- [X] T006 Create WorkflowTransition model in backend/src/models/chat.py with fields: transition_id, issue_id, project_id, from_status, to_status, assigned_user, triggered_by, success, error_message, timestamp
- [X] T007 [P] Add in-memory storage for recommendations (_recommendations dict) in backend/src/api/chat.py
- [X] T008 Create workflow_orchestrator.py skeleton with WorkflowState enum and WorkflowContext dataclass in backend/src/services/workflow_orchestrator.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - AI-Generated Issue Recommendation (Priority: P1) 🎯 MVP

**Goal**: User sends feature request → AI generates structured recommendation with title, user story, UI/UX description, and functional requirements

**Independent Test**: Submit a feature request in chat and verify AI returns structured recommendation with all required sections

### Implementation for User Story 1

- [X] T009 [US1] Define ISSUE_GENERATION_SYSTEM_PROMPT constant in backend/src/prompts/issue_generation.py with instructions for generating title, user_story, ui_ux_description, functional_requirements as JSON
- [X] T010 [US1] Define create_issue_generation_prompt(user_input, project_name) function in backend/src/prompts/issue_generation.py
- [X] T011 [US1] Add generate_issue_recommendation(user_input, project_name) async method to AIAgentService in backend/src/services/ai_agent.py
- [X] T012 [US1] Add _parse_issue_recommendation_response(response) helper method to AIAgentService in backend/src/services/ai_agent.py to parse JSON response into IssueRecommendation
- [X] T013 [US1] Add detect_feature_request_intent(user_input) method to AIAgentService in backend/src/services/ai_agent.py to distinguish feature requests from status changes
- [X] T014 [US1] Extend send_message endpoint in backend/src/api/chat.py to detect feature request intent and call generate_issue_recommendation
- [X] T015 [US1] Create ChatMessage response with action_type=ISSUE_CREATE and action_data containing recommendation details in backend/src/api/chat.py
- [X] T016 [US1] Store generated recommendation in _recommendations dict with recommendation_id key in backend/src/api/chat.py
- [X] T017 [US1] Add error handling for AI generation failures with user-friendly error messages in backend/src/api/chat.py

**Checkpoint**: User Story 1 complete - feature requests generate AI recommendations displayed in chat

---

## Phase 4: User Story 2 - GitHub Issue Creation and Project Attachment (Priority: P2)

**Goal**: Confirmed recommendation → GitHub Issue created (not draft) → Attached to Project with "Backlog" status

**Independent Test**: Confirm a recommendation and verify GitHub Issue is created with correct content, appears in GitHub Project with "Backlog" status

### Implementation for User Story 2

- [X] T018 [US2] Add create_issue(access_token, owner, repo, title, body, labels) async method to GitHubProjectsService in backend/src/services/github_projects.py using REST API POST /repos/{owner}/{repo}/issues
- [X] T019 [US2] Add ADD_ISSUE_TO_PROJECT_MUTATION GraphQL mutation string to backend/src/services/github_projects.py
- [X] T020 [US2] Add add_issue_to_project(access_token, project_id, issue_node_id) async method to GitHubProjectsService in backend/src/services/github_projects.py
- [X] T021 [US2] Add format_issue_body(recommendation) helper function in backend/src/services/workflow_orchestrator.py to create markdown body with User Story, UI/UX, Requirements sections
- [X] T022 [US2] Implement create_issue_from_recommendation(ctx, recommendation) method in WorkflowOrchestrator in backend/src/services/workflow_orchestrator.py
- [X] T023 [US2] Implement add_to_project_with_backlog(ctx) method in WorkflowOrchestrator in backend/src/services/workflow_orchestrator.py
- [X] T024 [US2] Create workflow.py API router file at backend/src/api/workflow.py with router = APIRouter(prefix="/workflow")
- [X] T025 [US2] Add POST /workflow/recommendations/{recommendation_id}/confirm endpoint in backend/src/api/workflow.py
- [X] T026 [US2] Add POST /workflow/recommendations/{recommendation_id}/reject endpoint in backend/src/api/workflow.py
- [X] T027 [US2] Register workflow router in backend/src/main.py with app.include_router(workflow_router)
- [X] T028 [US2] Add WorkflowResult response model in backend/src/models/chat.py with fields: success, issue_id, issue_number, issue_url, project_item_id, current_status, message
- [X] T029 [US2] Add duplicate detection using hash of original_input with 5-minute window in backend/src/api/workflow.py
- [X] T030 [US2] Add error handling for GitHub API failures with retry suggestion in chat in backend/src/api/workflow.py

**Checkpoint**: User Story 2 complete - confirmed recommendations create real GitHub Issues attached to project

---

## Phase 5: User Story 3 - Automatic Status Transition to Ready (Priority: P3)

**Goal**: After issue created with "Backlog" status → Automatically transition to "Ready" status

**Independent Test**: Create an issue and verify status automatically changes from "Backlog" to "Ready"

### Implementation for User Story 3

- [X] T031 [US3] Add transition_to_ready(ctx) method in WorkflowOrchestrator in backend/src/services/workflow_orchestrator.py that updates status from Backlog to Ready
- [X] T032 [US3] Add log_transition(transition) method in WorkflowOrchestrator to record WorkflowTransition for audit in backend/src/services/workflow_orchestrator.py
- [X] T033 [US3] Modify confirm endpoint to call transition_to_ready after add_to_project in backend/src/api/workflow.py
- [X] T034 [US3] Add GET /workflow/transitions endpoint with optional issue_id filter and limit parameter in backend/src/api/workflow.py
- [X] T035 [US3] Send WebSocket notification to user session when status transitions to Ready in backend/src/api/workflow.py

**Checkpoint**: User Story 3 complete - issues automatically transition to Ready after creation

---

## Phase 6: User Story 4 - Ready to In Progress with Copilot Assignment (Priority: P4)

**Goal**: When status changes to "Ready" → Detect change → Update to "In Progress" → Assign GitHub Copilot

**Independent Test**: Change issue to "Ready" status and verify automatic transition to "In Progress" with Copilot assigned

### Implementation for User Story 4

- [X] T036 [US4] Add assign_issue(access_token, owner, repo, issue_number, assignees) async method to GitHubProjectsService in backend/src/services/github_projects.py using REST API PATCH
- [X] T037 [US4] Add validate_assignee(access_token, owner, repo, username) async method to GitHubProjectsService in backend/src/services/github_projects.py to check if user can be assigned
- [X] T038 [US4] Add handle_ready_status(ctx) method in WorkflowOrchestrator that transitions to In Progress and assigns Copilot in backend/src/services/workflow_orchestrator.py
- [X] T039 [US4] Add GET /workflow/config endpoint returning current WorkflowConfiguration in backend/src/api/workflow.py
- [X] T040 [US4] Add PUT /workflow/config endpoint to update copilot_assignee and status column names in backend/src/api/workflow.py
- [X] T041 [US4] Extend poll_project_changes in GitHubProjectsService to detect Ready status and trigger handle_ready_status in backend/src/services/github_projects.py
- [X] T042 [US4] Add error handling for invalid assignee (copilot user not found) with clear error message in backend/src/services/workflow_orchestrator.py

**Checkpoint**: User Story 4 complete - Ready issues auto-transition to In Progress with Copilot assigned

---

## Phase 7: User Story 5 - In Progress to In Review with Owner Assignment (Priority: P5)

**Goal**: When completion detected → Update to "In Review" → Assign Project Owner

**Independent Test**: Simulate completion signal and verify transition to "In Review" with owner assigned

### Implementation for User Story 5

- [X] T043 [US5] Add get_repository_owner(access_token, owner, repo) async method to GitHubProjectsService in backend/src/services/github_projects.py using REST API
- [X] T044 [US5] Add detect_completion_signal(task) method in WorkflowOrchestrator to check for completion indicators (label, closed status) in backend/src/services/workflow_orchestrator.py
- [X] T045 [US5] Add handle_completion(ctx) method in WorkflowOrchestrator that transitions to In Review and assigns owner in backend/src/services/workflow_orchestrator.py
- [X] T046 [US5] Extend poll_project_changes to detect completion signals and trigger handle_completion in backend/src/services/github_projects.py
- [X] T047 [US5] Add notification to chat when issue moves to In Review in backend/src/api/workflow.py

**Checkpoint**: User Story 5 complete - completed issues auto-transition to In Review with owner assigned

---

## Phase 8: Frontend Integration

**Goal**: Display AI recommendations in chat with confirm/reject buttons and real-time status updates

### Implementation for Frontend

- [X] T048 [P] Create IssueRecommendationPreview.tsx component in frontend/src/components/chat/IssueRecommendationPreview.tsx displaying title, user_story, ui_ux_description, functional_requirements
- [X] T049 [P] Add Confirm and Reject buttons to IssueRecommendationPreview component with onClick handlers
- [X] T050 [P] Create useWorkflow.ts hook in frontend/src/hooks/useWorkflow.ts with confirmRecommendation(id) and rejectRecommendation(id) functions
- [X] T051 Add IssueRecommendation type to frontend/src/types/index.ts with all fields from IssueRecommendation model
- [X] T052 Add WorkflowResult type to frontend/src/types/index.ts
- [X] T053 Update ChatInterface.tsx to render IssueRecommendationPreview when action_type is issue_create in frontend/src/components/chat/ChatInterface.tsx
- [X] T054 Add loading state to IssueRecommendationPreview during confirm/reject API calls
- [X] T055 Display WorkflowResult success message after confirmation in ChatInterface

**Checkpoint**: Frontend complete - users can view recommendations and confirm/reject them

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T056 Add comprehensive logging for all workflow transitions in backend/src/services/workflow_orchestrator.py
- [X] T057 [P] Add rate limit handling with exponential backoff for GitHub API calls in backend/src/services/github_projects.py
- [X] T058 [P] Add input validation for maximum content length on feature requests in backend/src/api/chat.py
- [X] T059 Update API documentation strings in backend/src/api/workflow.py
- [X] T060 Run quickstart.md validation to verify all success criteria

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup
    ↓
Phase 2: Foundational (BLOCKS all user stories)
    ↓
┌───────────────────────────────────────────────────────────┐
│ User Stories can proceed in priority order OR in parallel │
└───────────────────────────────────────────────────────────┘
    ↓
Phase 3: US1 (P1) - AI Recommendation 🎯 MVP
    ↓
Phase 4: US2 (P2) - Issue Creation (depends on US1 for recommendation)
    ↓
Phase 5: US3 (P3) - Auto Ready (depends on US2 for issue)
    ↓
Phase 6: US4 (P4) - In Progress + Copilot (depends on US3 for Ready status)
    ↓
Phase 7: US5 (P5) - In Review + Owner (depends on US4 for In Progress)
    ↓
Phase 8: Frontend (can start after US1, integrates with all)
    ↓
Phase 9: Polish
```

### User Story Dependencies

- **User Story 1 (P1)**: Depends only on Foundational - Can be MVP standalone
- **User Story 2 (P2)**: Depends on US1 (needs recommendation to confirm)
- **User Story 3 (P3)**: Depends on US2 (needs issue in Backlog)
- **User Story 4 (P4)**: Depends on US3 (needs issue in Ready)
- **User Story 5 (P5)**: Depends on US4 (needs issue In Progress)
- **Frontend**: Can start after US1, progressively integrates

### Parallel Opportunities Per Phase

**Phase 1 (Setup)**:
```
T001 ──┐
T002 ──┼── All parallel (different enum/file additions)
T003 ──┘
```

**Phase 2 (Foundational)**:
```
T004 ──┐
T005 ──┼── All parallel (different models in same file but independent)
T006 ──┤
T007 ──┤
T008 ──┘
```

**Phase 8 (Frontend)**:
```
T048 ──┐
T049 ──┼── Component tasks parallel
T050 ──┘
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (AI Recommendation)
4. Complete Phase 4: User Story 2 (Issue Creation)
5. **STOP and VALIDATE**: Test issue creation flow end-to-end
6. Deploy/demo if ready - users can create structured GitHub Issues from chat

### Incremental Delivery

| Increment | User Stories | Value Delivered |
|-----------|--------------|-----------------|
| MVP | US1 + US2 | AI generates recommendations → Creates GitHub Issues |
| +1 | US3 | Auto-transition to Ready |
| +2 | US4 | Auto-assign Copilot on Ready |
| +3 | US5 | Auto-assign owner on completion |
| Full | Frontend | Complete chat UI experience |

### Single Developer Strategy

Execute phases sequentially in priority order:
1. Setup → Foundational → US1 → US2 → Test MVP
2. US3 → US4 → US5 → Test automation
3. Frontend → Test full flow
4. Polish

---

## Summary

| Phase | Tasks | Files Modified/Created |
|-------|-------|----------------------|
| Setup | T001-T003 | chat.py, issue_generation.py |
| Foundational | T004-T008 | chat.py, workflow_orchestrator.py |
| US1 (P1) | T009-T017 | issue_generation.py, ai_agent.py, chat.py |
| US2 (P2) | T018-T030 | github_projects.py, workflow_orchestrator.py, workflow.py, main.py |
| US3 (P3) | T031-T035 | workflow_orchestrator.py, workflow.py |
| US4 (P4) | T036-T042 | github_projects.py, workflow_orchestrator.py, workflow.py |
| US5 (P5) | T043-T047 | github_projects.py, workflow_orchestrator.py, workflow.py |
| Frontend | T048-T055 | IssueRecommendationPreview.tsx, useWorkflow.ts, types, ChatInterface.tsx |
| Polish | T056-T060 | Various |

**Total Tasks**: 60
**MVP Tasks**: T001-T030 (30 tasks through US2)
**Parallel Opportunities**: 15 tasks marked [P]

---

## Notes

- All workflow logic contained in single file `workflow_orchestrator.py` per user requirement
- Uses existing `AIAgentService` and `GitHubProjectsService` (DRY principle)
- No new dependencies required
- REST API for issue creation/assignment, GraphQL for project operations
- Polling-based status detection (no webhook complexity)
