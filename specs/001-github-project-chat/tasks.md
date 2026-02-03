# Tasks: GitHub Projects Chat Interface

**Input**: Design documents from `/specs/001-github-project-chat/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓

**Tests**: OPTIONAL - not explicitly requested in feature specification.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Includes exact file paths based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for backend (FastAPI) + frontend (React/Vite)

- [X] T001 Create backend project structure per plan.md: `backend/src/`, `backend/src/models/`, `backend/src/services/`, `backend/src/api/`, `backend/src/prompts/`, `backend/tests/`
- [X] T002 Create frontend project structure per plan.md: `frontend/src/`, `frontend/src/components/`, `frontend/src/hooks/`, `frontend/src/services/`, `frontend/src/types/`
- [X] T003 [P] Initialize Python backend with pyproject.toml including FastAPI, httpx, python-jose, pydantic, azure-ai-inference dependencies in `backend/`
- [X] T004 [P] Initialize Vite React TypeScript project with TanStack Query, Socket.io-client dependencies in `frontend/`
- [X] T005 [P] Configure backend linting (ruff) and formatting (black) in `backend/pyproject.toml`
- [X] T006 [P] Configure frontend ESLint and Prettier in `frontend/`
- [X] T007 [P] Create environment configuration template `.env.example` for both backend and frontend

**Checkpoint**: Project skeleton ready - proceed to foundational infrastructure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T008 Create base configuration module with environment variables in `backend/src/config.py` (GitHub OAuth secrets, Azure OpenAI key, session settings)
- [X] T009 [P] Create FastAPI application entry point with CORS, middleware setup in `backend/src/main.py`
- [X] T010 [P] Create base Pydantic models `__init__.py` in `backend/src/models/__init__.py`
- [X] T011 [P] Create API router structure `__init__.py` in `backend/src/api/__init__.py`
- [X] T012 [P] Create TypeScript base types for API responses in `frontend/src/types/index.ts` (User, Project, Task, ChatMessage, AITaskProposal)
- [X] T013 [P] Create API client service with base fetch wrapper in `frontend/src/services/api.ts`
- [X] T014 Create error handling middleware and custom exceptions in `backend/src/main.py`
- [X] T015 Create logging configuration in `backend/src/config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - GitHub Authentication and Project Selection (Priority: P1) 🎯 MVP

**Goal**: Users can authenticate via GitHub OAuth, see their projects, and select one to work with

**Independent Test**: 
1. User clicks "Login with GitHub" → redirects to GitHub OAuth
2. After authorization → returns to app with session
3. User sees list of their GitHub Projects
4. User selects a project → sidebar shows project board items

### Implementation for User Story 1

#### Backend Models

- [X] T016 [P] [US1] Create UserSession model with OAuth tokens in `backend/src/models/user.py` (session_id, github_user_id, access_token, refresh_token, token_expires_at, selected_project_id)
- [X] T017 [P] [US1] Create GitHubProject model with status columns in `backend/src/models/project.py` (project_id, owner_login, name, type, url, status_columns, cached_at)

#### Backend Services

- [X] T018 [US1] Implement GitHub OAuth service in `backend/src/services/github_auth.py` (initiate_oauth, handle_callback, exchange_code_for_token, refresh_token, revoke_token)
- [X] T019 [US1] Implement GitHub Projects GraphQL service in `backend/src/services/github_projects.py` (list_user_projects, list_org_projects, get_project_details, get_project_items)
- [X] T020 [US1] Implement project cache service in `backend/src/services/cache.py` (in-memory cache with TTL for project lists)

#### Backend API Endpoints

- [X] T021 [US1] Implement OAuth endpoints in `backend/src/api/auth.py` (GET /auth/github, GET /auth/github/callback, GET /auth/me, POST /auth/logout)
- [X] T022 [US1] Implement projects endpoints in `backend/src/api/projects.py` (GET /projects, GET /projects/{projectId}, POST /projects/{projectId}/select)
- [X] T023 [US1] Add session cookie middleware for authentication in `backend/src/main.py`

#### Frontend Components

- [X] T024 [P] [US1] Create useAuth hook in `frontend/src/hooks/useAuth.ts` (login, logout, getCurrentUser, isAuthenticated state)
- [X] T025 [P] [US1] Create useProjects hook in `frontend/src/hooks/useProjects.ts` (fetchProjects, selectProject, selectedProject state)
- [X] T026 [US1] Create LoginButton component in `frontend/src/components/auth/LoginButton.tsx`
- [X] T027 [US1] Create ProjectSelector dropdown in `frontend/src/components/sidebar/ProjectSelector.tsx`
- [X] T028 [US1] Create ProjectSidebar component in `frontend/src/components/sidebar/ProjectSidebar.tsx`
- [X] T029 [US1] Create TaskCard component for board items in `frontend/src/components/sidebar/TaskCard.tsx`
- [X] T030 [US1] Integrate auth and project selection in `frontend/src/App.tsx`

**Checkpoint**: User Story 1 complete - users can login, see projects, and select one. Ready for MVP demo.

---

## Phase 4: User Story 2 - Natural Language Task Creation (Priority: P1) 🎯 MVP

**Goal**: Users can describe tasks in natural language, AI generates structured task, user confirms, task is created in GitHub Project

**Independent Test**:
1. User types "Create a task to fix the login bug on mobile"
2. AI responds with formatted task preview (title + description)
3. User clicks "Confirm"
4. Task appears in GitHub Project board and sidebar

### Implementation for User Story 2

#### Backend Models

- [X] T031 [P] [US2] Create Task model in `backend/src/models/task.py` (task_id, project_id, github_item_id, title, description, status, status_option_id)
- [X] T032 [P] [US2] Create ChatMessage model in `backend/src/models/chat.py` (message_id, session_id, sender_type, content, action_type, action_data)
- [X] T033 [P] [US2] Create AITaskProposal model in `backend/src/models/chat.py` (proposal_id, session_id, original_input, proposed_title, proposed_description, status, expires_at)

#### Backend Services

- [X] T034 [US2] Create AI task generation prompt template in `backend/src/prompts/task_generation.py` (system prompt, user prompt template, output parsing)
- [X] T035 [US2] Implement AI agent service with Azure OpenAI in `backend/src/services/ai_agent.py` (generate_task_from_description, parse_ai_response, validate_generated_task)
- [X] T036 [US2] Add task creation methods to GitHub Projects service in `backend/src/services/github_projects.py` (create_draft_item, add_item_to_project)

#### Backend API Endpoints

- [X] T037 [US2] Implement task endpoints in `backend/src/api/tasks.py` (POST /tasks, GET /projects/{projectId}/tasks)
- [X] T038 [US2] Implement chat endpoints in `backend/src/api/chat.py` (POST /chat/messages, GET /chat/messages, POST /chat/proposals/{proposalId}/confirm, DELETE /chat/proposals/{proposalId})
- [X] T039 [US2] Add rate limiting middleware for GitHub API calls in `backend/src/main.py`

#### Frontend Components

- [X] T040 [P] [US2] Create useChat hook in `frontend/src/hooks/useChat.ts` (sendMessage, messages state, pendingProposal state, confirmProposal, rejectProposal)
- [X] T041 [US2] Create ChatInterface component in `frontend/src/components/chat/ChatInterface.tsx` (message input, send button, scroll behavior)
- [X] T042 [US2] Create MessageBubble component in `frontend/src/components/chat/MessageBubble.tsx` (user vs assistant styling, timestamp)
- [X] T043 [US2] Create TaskPreview component for AI proposals in `frontend/src/components/chat/TaskPreview.tsx` (preview card, confirm/reject buttons)
- [X] T044 [US2] Add loading indicators for AI generation in `frontend/src/components/chat/ChatInterface.tsx`
- [X] T045 [US2] Integrate chat interface with main App in `frontend/src/App.tsx`

**Checkpoint**: User Story 2 complete - users can create tasks via natural language. Full MVP functionality available.

---

## Phase 5: User Story 3 - Task Status Updates via Chat (Priority: P2)

**Goal**: Users can update task status using natural language commands like "Move 'Login bug' to Done"

**Independent Test**:
1. User types "Move the login bug task to In Progress"
2. AI identifies the task and target status
3. System shows confirmation: "Move 'Fix login bug' to In Progress?"
4. User confirms → task status updates in GitHub and sidebar

### Implementation for User Story 3

#### Backend Services

- [X] T046 [US3] Add status update methods to AI agent service in `backend/src/services/ai_agent.py` (parse_status_change_request, identify_target_task, identify_target_status)
- [X] T047 [US3] Add status update methods to GitHub Projects service in `backend/src/services/github_projects.py` (update_item_status, get_status_field_options)

#### Backend API Endpoints

- [X] T048 [US3] Implement task status update endpoint in `backend/src/api/tasks.py` (PATCH /tasks/{taskId}/status)
- [X] T049 [US3] Add status change intent handling to chat endpoint in `backend/src/api/chat.py` (detect status change intent, create status change proposal)

#### Frontend Components

- [X] T050 [US3] Add StatusChangePreview component in `frontend/src/components/chat/StatusChangePreview.tsx` (current status, target status, confirm/reject)
- [X] T051 [US3] Update TaskCard to show status badges in `frontend/src/components/sidebar/TaskCard.tsx`
- [X] T052 [US3] Update useChat hook to handle status change proposals in `frontend/src/hooks/useChat.ts`

**Checkpoint**: User Story 3 complete - users can update task statuses via chat commands.

---

## Phase 6: User Story 4 - Real-Time Board Synchronization (Priority: P3)

**Goal**: Board sidebar updates automatically when changes occur from other sources (GitHub web, API, teammates)

**Independent Test**:
1. User has project board open in chat interface
2. Another user creates/updates task via GitHub web
3. Within 10 seconds, chat interface sidebar reflects the change
4. Optional: shows notification of external change

### Implementation for User Story 4

#### Backend Services

- [X] T053 [US4] Implement WebSocket connection manager in `backend/src/services/websocket.py` (connection registry, broadcast to project subscribers)
- [X] T054 [US4] Implement polling fallback service in `backend/src/services/github_projects.py` (poll_project_changes, compare_with_cache, detect_changes)
- [X] T055 [US4] Add webhook endpoint for GitHub events in `backend/src/api/projects.py` (POST /webhooks/github - for future GitHub App integration)

#### Backend API Endpoints

- [X] T056 [US4] Implement WebSocket endpoint in `backend/src/api/projects.py` (WS /projects/{projectId}/subscribe)
- [X] T057 [US4] Add SSE endpoint as WebSocket fallback in `backend/src/api/projects.py` (GET /projects/{projectId}/events)

#### Frontend Components

- [X] T058 [P] [US4] Create useRealTimeSync hook in `frontend/src/hooks/useRealTimeSync.ts` (WebSocket connection, reconnection logic, fallback to polling)
- [X] T059 [US4] Update ProjectSidebar to handle real-time updates in `frontend/src/components/sidebar/ProjectSidebar.tsx` (optimistic updates, change highlighting)
- [X] T060 [US4] Add sync status indicator in `frontend/src/components/sidebar/ProjectSidebar.tsx` (connected, reconnecting, polling mode)

**Checkpoint**: User Story 4 complete - full real-time synchronization available.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T061 [P] Add comprehensive error messages for all API failures in `backend/src/api/` (user-friendly messages per FR-025)
- [X] T062 [P] Add rate limit tracking and warning UI in `frontend/src/components/` (per FR-026)
- [X] T063 [P] Create README.md with setup instructions at repository root
- [X] T064 [P] Create Dockerfile for backend in `backend/Dockerfile`
- [X] T065 [P] Create Dockerfile for frontend in `frontend/Dockerfile`
- [X] T066 Create docker-compose.yml for local development at repository root
- [X] T067 Run quickstart.md validation scenarios end-to-end
- [X] T068 Security hardening: validate all inputs, sanitize outputs, secure token storage

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
    │
    ▼
Phase 2 (Foundational) ◄── BLOCKS ALL USER STORIES
    │
    ├──────────────────────────────────┐
    ▼                                  ▼
Phase 3 (US1: Auth+Projects)    Phase 4 (US2: Task Creation)*
    │                                  │
    ▼                                  ▼
Phase 5 (US3: Status Updates)   [Can run in parallel after US1/US2]
    │
    ▼
Phase 6 (US4: Real-Time Sync)
    │
    ▼
Phase 7 (Polish)
```

*Note: User Story 2 depends on User Story 1 for authentication context

### User Story Dependencies

| Story | Depends On | Can Parallelize With |
|-------|------------|----------------------|
| US1 (Auth+Projects) | Phase 2 only | Backend ∥ Frontend components |
| US2 (Task Creation) | Phase 2 + US1 auth | Backend ∥ Frontend components |
| US3 (Status Updates) | Phase 2 + US1 + US2 models | — |
| US4 (Real-Time) | Phase 2 + US1 | US2, US3 backend work |

### Within Each User Story

1. Models before services
2. Services before endpoints  
3. Backend API before frontend integration
4. Core implementation before polish

### Parallel Opportunities

**Phase 1 (All parallel)**:
- T003, T004, T005, T006, T007 can all run simultaneously

**Phase 2 (Partial parallel)**:
- T009, T010, T011, T012, T013 can run in parallel

**Phase 3 - User Story 1**:
```
Parallel: T016, T017 (models)
Then: T018, T019, T020 (services - sequential due to deps)
Then: T021, T022, T023 (API endpoints)
Parallel: T024, T025 (frontend hooks)
Then: T026 → T027 → T028 → T029 → T030 (frontend components)
```

**Phase 4 - User Story 2**:
```
Parallel: T031, T032, T033 (models)
Then: T034 → T035 → T036 (services - sequential)
Then: T037, T038, T039 (API endpoints)
Parallel: T040 (frontend hook)
Then: T041 → T042 → T043 → T044 → T045 (frontend components)
```

---

## Parallel Example: User Story 1 Backend Models

```bash
# Launch backend models in parallel:
Task T016: "Create UserSession model in backend/src/models/user.py"
Task T017: "Create GitHubProject model in backend/src/models/project.py"

# Then launch frontend hooks in parallel:
Task T024: "Create useAuth hook in frontend/src/hooks/useAuth.ts"
Task T025: "Create useProjects hook in frontend/src/hooks/useProjects.ts"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup (~7 tasks)
2. Complete Phase 2: Foundational (~8 tasks) **← CRITICAL GATE**
3. Complete Phase 3: User Story 1 - Auth + Projects (~15 tasks)
4. Complete Phase 4: User Story 2 - Task Creation (~15 tasks)
5. **STOP and VALIDATE**: Run quickstart.md scenarios
6. Deploy/demo MVP (Login + Project Selection + Task Creation)

### Incremental Delivery

| Increment | User Stories | Value Delivered |
|-----------|--------------|-----------------|
| MVP | US1 + US2 | Core chat-to-task workflow |
| v1.1 | +US3 | Status updates via chat |
| v1.2 | +US4 | Real-time synchronization |
| v1.3 | +Polish | Production-ready |

### Estimated Effort

| Phase | Task Count | Complexity |
|-------|-----------|------------|
| Setup | 7 | Low |
| Foundational | 8 | Medium |
| US1 (Auth+Projects) | 15 | Medium |
| US2 (Task Creation) | 15 | High |
| US3 (Status Updates) | 7 | Medium |
| US4 (Real-Time) | 8 | High |
| Polish | 8 | Low |
| **Total** | **68** | — |

---

## Notes

- [P] tasks = different files, no dependencies between them
- [USn] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- MVP = US1 + US2 only (authentication + task creation)
- Tests not included (not requested in spec) - add TDD tasks if needed
