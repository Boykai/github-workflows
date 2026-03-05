# Tasks: Chat Agent Auto-Generate Full GitHub Issue Metadata

**Input**: Design documents from `/specs/018-issue-metadata-autogen/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Tests are OPTIONAL for this feature (Constitution Check IV). Unit tests recommended for MetadataService cache logic but not required.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database migration and configuration for the metadata cache

- [ ] T001 Create SQLite migration for github_metadata_cache table in backend/src/migrations/011_metadata_cache.sql
- [ ] T002 [P] Add metadata_cache_ttl_seconds setting (default 3600) to Settings class in backend/src/config.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models and service that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 [P] Add assignees (list[str]), milestone (str|None), and branch (str|None) fields to IssueMetadata model in backend/src/models/recommendation.py
- [ ] T004 [P] Create RepositoryMetadataContext Pydantic model (repo_key, labels, branches, milestones, collaborators, fetched_at, is_stale, source) in backend/src/services/metadata_service.py
- [ ] T005 Implement MetadataService class with fetch_metadata (GitHub REST API pagination for labels, branches, milestones, collaborators), get_metadata (read from SQLite), invalidate (clear cache for repo), and get_or_fetch (return cached if fresh, fetch if stale/missing) in backend/src/services/metadata_service.py

**Checkpoint**: Foundation ready — MetadataService can fetch, cache, and return repo metadata; IssueMetadata supports all fields

---

## Phase 3: User Story 1 — Fully Populated Issue Creation (Priority: P1) 🎯 MVP

**Goal**: Every issue created via the chat agent includes AI-generated values for all metadata fields (priority, size, estimate, dates, labels, assignees, milestone, branch) in the GitHub API payload

**Independent Test**: Ask the chat agent to create a GitHub Issue and verify that all metadata fields are present and valid in the resulting issue on GitHub

### Implementation for User Story 1

- [ ] T006 [P] [US1] Update create_issue_generation_prompt to accept optional metadata_context dict and inject dynamic labels, branches, milestones, and collaborators into the system prompt (fall back to PREDEFINED_LABELS when not provided) in backend/src/prompts/issue_generation.py
- [ ] T007 [P] [US1] Expand create_issue to accept optional milestone (int|None) and assignees (list[str]|None) parameters and include them in the GitHub REST API payload in backend/src/services/github_projects/service.py
- [ ] T008 [US1] Update generate_issue_recommendation to call MetadataService.get_or_fetch for the target repo and pass the resulting metadata_context to create_issue_generation_prompt; update _parse_issue_metadata to extract assignees, milestone, and branch fields in backend/src/services/ai_agent.py
- [ ] T009 [US1] Update create_issue_from_recommendation to pass full metadata (labels array, milestone number resolved from title, assignees list) to create_issue and add branch reference to issue body in backend/src/services/workflow_orchestrator/orchestrator.py
- [ ] T010 [US1] Implement priority/size to repo label mapping logic — map AI-selected priority (e.g., "P1") and size (e.g., "M") to matching repo labels (e.g., "P1", "size:M") and merge into labels array before submission in backend/src/services/workflow_orchestrator/orchestrator.py
- [ ] T011 [P] [US1] Add structured logging for each issue creation event recording the full metadata payload sent to GitHub (labels, milestone, assignees, branch, priority, size, estimate, dates) in backend/src/services/workflow_orchestrator/orchestrator.py

**Checkpoint**: Issues created via the chat agent now include all metadata fields in the GitHub API payload. US1 is fully functional and testable independently.

---

## Phase 4: User Story 2 — Metadata Caching and Availability (Priority: P2)

**Goal**: Repository metadata is fetched once, cached in SQLite (survives restarts), served from L1 in-memory cache for speed, and refreshed automatically when TTL expires

**Independent Test**: Create an issue (triggers initial fetch), create another immediately (should use cached data with no API calls), wait past TTL or click refresh (should re-fetch), restart app and verify cached data is available immediately

### Implementation for User Story 2

- [ ] T012 [P] [US2] Integrate existing InMemoryCache as L1 cache layer in MetadataService — check L1 before SQLite reads, populate L1 on SQLite reads and API fetches in backend/src/services/metadata_service.py
- [ ] T013 [P] [US2] Create metadata API endpoints: GET /api/v1/metadata/{owner}/{repo} (returns cached metadata) and POST /api/v1/metadata/{owner}/{repo}/refresh (force-refresh cache) in backend/src/api/metadata.py
- [ ] T014 [US2] Register metadata router with prefix in api_router in backend/src/api/__init__.py
- [ ] T015 [P] [US2] Add RepositoryMetadata interface (repo_key, labels, branches, milestones, collaborators, fetched_at, is_stale, source) and update IssueMetadata interface with assignees, milestone, branch fields in frontend/src/types/index.ts
- [ ] T016 [P] [US2] Add getMetadata(owner, repo) and refreshMetadata(owner, repo) API call functions in frontend/src/services/api.ts
- [ ] T017 [US2] Create useMetadata hook that fetches repository metadata from backend on mount, caches in React state, exposes refresh() function, and provides loading/error states in frontend/src/hooks/useMetadata.ts

**Checkpoint**: Metadata is cached in SQLite + L1 memory, served via API to frontend, and frontend can fetch/refresh it. US2 is independently testable.

---

## Phase 5: User Story 3 — Preview and Override Before Submission (Priority: P3)

**Goal**: Users see a structured preview of all AI-generated metadata fields before submission and can edit any field (priority, size, labels, dates, assignees, milestone, branch) before confirming

**Independent Test**: Initiate issue creation, observe preview card with all metadata fields displayed as editable controls, modify one or more fields, confirm submission, and verify the created issue reflects the user's overrides

### Implementation for User Story 3

- [ ] T018 [US3] Add editable dropdown controls for priority (P0–P3) and size (XS–XL) fields replacing read-only badges in frontend/src/components/chat/IssueRecommendationPreview.tsx
- [ ] T019 [US3] Add editable multi-select chip input for labels with typeahead filtering from cached repo labels in frontend/src/components/chat/IssueRecommendationPreview.tsx
- [ ] T020 [US3] Add editable dropdown for assignees (multi-select from cached collaborators), milestone (single-select from cached milestones), and branch (single-select from cached branches) in frontend/src/components/chat/IssueRecommendationPreview.tsx
- [ ] T021 [US3] Add date picker inputs for start_date and target_date and number input for estimate_hours in frontend/src/components/chat/IssueRecommendationPreview.tsx
- [ ] T022 [US3] Implement ConfirmationOverrides payload — on confirm, diff user edits against AI defaults and send only changed fields as overrides to the confirmation endpoint in frontend/src/components/chat/IssueRecommendationPreview.tsx
- [ ] T023 [US3] Handle ConfirmationOverrides in backend confirmation endpoint — merge user overrides into recommendation metadata before calling create_issue_from_recommendation in backend/src/api/workflow.py

**Checkpoint**: Users can review and override all metadata fields in the preview card before submission. US3 is independently testable.

---

## Phase 6: User Story 4 — Graceful Degradation on API Errors (Priority: P4)

**Goal**: When the GitHub API is unavailable, the system falls back to cached data (or hardcoded constants as last resort), notifies the user of degraded state, and retries on next access

**Independent Test**: Simulate network failure or API rate limit during metadata fetch; verify system falls back to cached data with appropriate notification and continues to allow issue creation

### Implementation for User Story 4

- [ ] T024 [US4] Implement three-tier fallback in MetadataService.get_or_fetch: try L1 memory → try SQLite cache → fall back to hardcoded constants.LABELS with source="fallback" indicator in backend/src/services/metadata_service.py
- [ ] T025 [US4] Add error handling for GitHub API errors (httpx.HTTPStatusError for 403/429, httpx.ConnectError for network failures) in fetch_metadata — catch, log warning, and return cached/fallback data instead of raising in backend/src/services/metadata_service.py
- [ ] T026 [P] [US4] Show degraded-state notification in the metadata preview area — display "Using cached data" banner when source is "cache" and "Limited metadata available" warning when source is "fallback" in frontend/src/components/chat/IssueRecommendationPreview.tsx
- [ ] T027 [US4] Implement retry-on-next-access logic — after an API failure, mark cache as stale so the next get_or_fetch attempt retries the API rather than serving stale data indefinitely in backend/src/services/metadata_service.py

**Checkpoint**: System gracefully handles API failures with fallback data and user notification. US4 is independently testable.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T028 [P] Add cache-source indicator (fresh/cached/fallback badge) next to metadata fields in the issue preview in frontend/src/components/chat/IssueRecommendationPreview.tsx
- [ ] T029 Code cleanup and refactoring across all modified files (remove dead code, ensure consistent error handling patterns)
- [ ] T030 Run quickstart.md validation scenarios end-to-end (create issue with full metadata, verify cache behavior, test override flow, test fallback behavior)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) completion
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) completion — can run in parallel with US1
- **User Story 3 (Phase 5)**: Depends on US2 (Phase 4) for metadata availability in frontend
- **User Story 4 (Phase 6)**: Depends on Foundational (Phase 2) — can run in parallel with US1/US2
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — No dependencies on other stories; frontend tasks are independent of US1
- **User Story 3 (P3)**: Depends on US2 (Phase 4) for useMetadata hook and frontend types — the editable UI needs metadata to populate dropdowns
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) — Error handling is independent of UI features

### Within Each User Story

- Models before services
- Services before endpoints/API routes
- Backend before frontend (for API dependencies)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1**: T001 and T002 can run in parallel (different files)
- **Phase 2**: T003 and T004 can run in parallel (T003 is in recommendation.py, T004 is in metadata_service.py); T005 depends on T004
- **Phase 3 (US1)**: T006 and T007 can run in parallel (different files); T011 is parallel
- **Phase 4 (US2)**: T012, T013, T015, T016 can all run in parallel (different files across backend/frontend)
- **Phase 5 (US3)**: T018–T021 are sequential edits to the same file; T023 (backend) is parallel with frontend tasks
- **Phase 6 (US4)**: T024 and T025 are sequential in same file; T026 (frontend) is parallel with backend tasks
- **Cross-story**: US1 (backend) and US2 frontend tasks (T015–T017) can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch parallel backend tasks (different files):
Task T006: "Update prompt builder in backend/src/prompts/issue_generation.py"
Task T007: "Expand create_issue in backend/src/services/github_projects/service.py"

# Sequential tasks (dependencies within US1):
Task T008: "Update AI agent to use metadata context" (depends on T006)
Task T009: "Update orchestrator to pass full metadata" (depends on T007, T008)
Task T010: "Implement priority/size label mapping" (depends on T009)
Task T011: "Add audit logging" (parallel — additive, no conflicts)
```

## Parallel Example: User Story 2

```bash
# Launch parallel tasks across backend and frontend (different projects):
Task T012: "L1 cache integration in backend/src/services/metadata_service.py"
Task T013: "Metadata API endpoints in backend/src/api/metadata.py"
Task T015: "Frontend types in frontend/src/types/index.ts"
Task T016: "Frontend API calls in frontend/src/services/api.ts"

# Sequential (depends on above):
Task T014: "Register router" (depends on T013)
Task T017: "useMetadata hook" (depends on T015, T016)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (migration + config)
2. Complete Phase 2: Foundational (MetadataService + model expansion)
3. Complete Phase 3: User Story 1 (prompt injection + full metadata in API payload)
4. **STOP and VALIDATE**: Create an issue via chat agent → verify all metadata fields present on GitHub
5. Deploy/demo if ready — issues are now fully populated

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → **MVP!** Issues have full metadata → Deploy/Demo
3. Add User Story 2 → Metadata cached, frontend can access it → Deploy/Demo
4. Add User Story 3 → Users can preview and edit metadata before submission → Deploy/Demo
5. Add User Story 4 → System handles API failures gracefully → Deploy/Demo
6. Polish → Documentation, cleanup, validation

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (backend — prompt + API payload)
   - Developer B: User Story 2 (backend API + frontend hooks/types)
3. After US2 completes:
   - Developer B: User Story 3 (frontend editable preview)
4. User Story 4 can be done by either developer at any time after Foundational

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 30 |
| **Phase 1 (Setup)** | 2 tasks |
| **Phase 2 (Foundational)** | 3 tasks |
| **Phase 3 (US1 — MVP)** | 6 tasks |
| **Phase 4 (US2)** | 6 tasks |
| **Phase 5 (US3)** | 6 tasks |
| **Phase 6 (US4)** | 4 tasks |
| **Phase 7 (Polish)** | 3 tasks |
| **Parallel opportunities** | 15 tasks marked [P] |
| **Suggested MVP scope** | Setup + Foundational + US1 (11 tasks) |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Tests are optional — add unit tests for MetadataService cache logic if desired
- Avoid: vague tasks, same-file conflicts, cross-story dependencies that break independence
