# Tasks: Fix — Use Exact User Input + Chat Agent Metadata When AI Enhance Is Disabled

**Input**: Design documents from `/specs/029-fix-ai-enhance-disabled/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ (api.md, components.md), quickstart.md

**Tests**: Not explicitly requested in the feature specification. Existing tests must continue to pass (Constitution Check IV). No new test tasks are included unless test infrastructure already covers the modified paths.

**Organization**: Tasks grouped by user story (P1–P3) for independent implementation and testing. This is a targeted bug fix — changes are concentrated in two backend files. Each user story can be delivered as an independently verifiable increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Exact file paths included in descriptions

## Path Conventions

- **Web app**: `frontend/src/` (React/TypeScript), `backend/src/` (Python/FastAPI)
- Backend API: `backend/src/api/chat.py` — PRIMARY change target (`send_message()` fallback path, lines 430–476)
- Backend services: `backend/src/services/ai_agent.py` — NEW method (`generate_title_from_description()`)
- Backend tracking: `backend/src/services/agent_tracking.py` — audit only (no changes expected)
- Backend models: `backend/src/models/recommendation.py` — no changes (existing `AITaskProposal` reused)
- Frontend: no changes expected (toggle and API call already transmit `ai_enhance` correctly)

---

## Phase 1: Setup

**Purpose**: No new project setup required — this is a bug fix to an existing codebase. All infrastructure (FastAPI, Pydantic models, AIAgentService, ChatInterface) is already in place.

- [x] T001 Verify existing backend test suite passes by running `pytest backend/tests/ -v` to establish a clean baseline before making changes

**Checkpoint**: Baseline confirmed. All existing tests pass. Ready for implementation.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the lightweight title-generation method that the ai_enhance=False branch depends on. This MUST be complete before any user story can be implemented.

**⚠️ CRITICAL**: The new `generate_title_from_description()` method is required by US1 (core bug fix). No user story work can begin until this method exists.

- [x] T002 Add async method `generate_title_from_description(self, user_input: str, project_name: str, github_token: str | None = None) -> str` to `AIAgentService` class in backend/src/services/ai_agent.py — call the existing `_call_completion()` with a focused prompt asking only for a concise issue title from the raw user input, return the generated title string, and fall back to truncating user_input to first 80 characters (standard GitHub title length convention) + "..." if the AI call fails or returns empty

**Checkpoint**: `generate_title_from_description()` is callable and returns a meaningful title from raw user input. Falls back gracefully on AI failure. Ready for US1 integration.

---

## Phase 3: User Story 1 — Submit Chat Request with AI Enhance Disabled (Priority: P1) 🎯 MVP

**Goal**: When AI Enhance is disabled, bypass `generate_task_from_description()` in the fallback task generation path and instead create an `AITaskProposal` using the user's exact raw chat input as the description body with a Chat Agent–generated title — eliminating the "I couldn't generate a task" error.

**Independent Test**: Toggle AI Enhance OFF → type any non-empty message → submit → verify a task proposal is returned with the raw input as `proposed_description`, an AI-generated title as `proposed_title`, and no error message is displayed. Click confirm → verify GitHub issue is created with the raw text as the description body.

### Implementation for User Story 1

- [x] T003 [US1] Add `ai_enhance=False` conditional check at the start of the fallback task generation block (before the existing `generate_task_from_description()` call at ~line 432) in `send_message()` in backend/src/api/chat.py — when `chat_request.ai_enhance is False`, enter the new metadata-only branch instead of calling `generate_task_from_description()`
- [x] T004 [US1] In the new ai_enhance=False branch, call `ai_service.generate_title_from_description(user_input=chat_request.content, project_name=project_name, github_token=session.access_token)` to generate a title from the raw user input in backend/src/api/chat.py
- [x] T005 [US1] Create an `AITaskProposal` instance with `session_id=session.session_id`, `original_input=chat_request.content`, `proposed_title=title` (from T004), and `proposed_description=chat_request.content` (user's exact raw input, verbatim) — `proposal_id` is auto-generated as a UUID by the Pydantic model default — then store it in `_proposals[str(proposal.proposal_id)]` in backend/src/api/chat.py
- [x] T006 [US1] Construct and return an assistant `ChatMessage` with `action_type=ActionType.TASK_CREATE`, `action_data` containing `proposal_id`, `proposed_title`, `proposed_description` (raw input), and `status=ProposalStatus.PENDING.value` — call `add_message()` and `_trigger_signal_delivery()` before returning, in backend/src/api/chat.py

**Checkpoint**: AI Enhance OFF → submit message → task proposal returned with raw user input as description, AI-generated title. No "I couldn't generate a task" error. AI Enhance ON → existing behavior unchanged. This is the MVP — the core bug is fixed.

---

## Phase 4: User Story 2 — Seamless Submission Flow Without Visible Errors (Priority: P1)

**Goal**: Ensure the ai_enhance=False path completes without any user-visible errors, stalled states, or unexpected behavior. The generic "I couldn't generate a task" error must never be surfaced when AI Enhance is disabled.

**Independent Test**: Submit multiple chat requests in quick succession with AI Enhance OFF → verify each completes with a proposal response, no error toasts, no stalled spinners, no UI freezes. Verify the generic error handler at lines 465–476 is never reached for ai_enhance=False requests.

### Implementation for User Story 2

- [x] T007 [US2] Wrap the entire ai_enhance=False branch (T003–T006) in a dedicated `try/except Exception` block that catches any failure from `generate_title_from_description()` or proposal creation, preventing the exception from propagating to the existing generic error handler at lines 465–476 in backend/src/api/chat.py
- [x] T008 [US2] Ensure the ai_enhance=False branch returns early (via explicit `return assistant_message`) before execution can reach the existing `generate_task_from_description()` call and its associated generic "I couldn't generate a task" error handler in backend/src/api/chat.py

**Checkpoint**: No user-facing error messages appear when AI Enhance is disabled and valid input is provided. The generic "I couldn't generate a task from your description" error is structurally unreachable for ai_enhance=False requests.

---

## Phase 5: User Story 3 — Structural Parity Between Enhanced and Non-Enhanced Issues (Priority: P2)

**Goal**: Verify that GitHub issues created with AI Enhance disabled are structurally identical to those created with AI Enhance enabled — same metadata fields, same Agent Pipeline config section, same label taxonomy — differing only in that the description body is raw user input.

**Independent Test**: Create two issues — one with AI Enhance ON and one with AI Enhance OFF — from the same chat input. Compare: both should have the same metadata field types (title, labels, size estimate, priority, assignees), the same Agent Pipeline configuration section, and the same structural format.

### Implementation for User Story 3

- [x] T009 [US3] Audit `confirm_proposal()` in backend/src/api/chat.py (lines 603–696) to verify it processes `AITaskProposal` instances identically regardless of whether `proposed_description` contains raw user input or AI-enhanced content — specifically verify: (1) no conditional logic branches on description source, (2) same GitHub Issue creation via `github_service.create_issue()`, (3) same `WorkflowOrchestrator.create_all_sub_issues()` call, (4) same `assign_agent_for_status()` call
- [x] T010 [P] [US3] Audit `append_tracking_to_body()` in backend/src/services/agent_tracking.py to verify the Agent Pipeline configuration block (horizontal rule + "## 🤖 Agent Pipeline" heading + tracking table) is appended identically for both enhanced and non-enhanced issue descriptions — confirm no ai_enhance flag checks in the tracking logic

**Checkpoint**: Structural parity confirmed. Issues from both paths have identical structure: title, labels, estimates, assignees, Agent Pipeline config block. Only the description body content differs (raw vs. AI-enhanced).

---

## Phase 6: User Story 4 — Independent Metadata Generation Failure Handling (Priority: P3)

**Goal**: When the Chat Agent metadata generation (title generation) step itself fails while AI Enhance is disabled, surface a specific, actionable error message instead of the generic catch-all — informing the user their input was preserved and they can retry.

**Independent Test**: Simulate a metadata generation failure (e.g., network error, AI service unavailable) with AI Enhance OFF → verify the user sees "I couldn't generate metadata for your request. Your input was preserved — please try again." instead of the generic "I couldn't generate a task" error.

### Implementation for User Story 4

- [x] T011 [US4] In the `except Exception` block of the ai_enhance=False branch (from T007), return a `ChatMessage` with `sender_type=SenderType.ASSISTANT` and content "I couldn't generate metadata for your request. Your input was preserved — please try again." instead of the generic error message, in backend/src/api/chat.py
- [x] T012 [US4] Add `logger.error("Failed to generate metadata (ai_enhance=off): %s", e, exc_info=True)` in the except block to log the metadata generation failure with full stack trace for debugging in backend/src/api/chat.py

**Checkpoint**: Metadata generation failures when AI Enhance is disabled produce a specific, actionable error message. The generic "I couldn't generate a task" message is never shown. Error is logged with full context for debugging.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, cleanup, and regression testing across all user stories.

- [x] T013 Run `pytest backend/tests/ -v` to verify all existing backend tests still pass with the changes
- [x] T014 [P] Verify code style consistency — ensure the new ai_enhance=False branch in backend/src/api/chat.py follows the same patterns (logging, error handling, message construction) as the existing ai_enhance=True path
- [x] T015 Run quickstart.md verification checklist: AI Enhance ON unchanged, AI Enhance OFF creates proposal with raw input, no generic error, Agent Pipeline config appended on confirm, metadata generation failure shows specific error

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — baseline test run
- **Foundational (Phase 2)**: Depends on Setup — `generate_title_from_description()` method must exist before US1
- **US1 (Phase 3)**: Depends on Foundational — core bug fix uses the new method
- **US2 (Phase 4)**: Depends on US1 — error suppression wraps the US1 code
- **US3 (Phase 5)**: Depends on US1 — audit verifies structural parity of proposals created in US1
- **US4 (Phase 6)**: Depends on US2 — specific error message lives in the try/except from US2
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational (Phase 2) — can start after `generate_title_from_description()` exists
- **US2 (P1)**: Depends on US1 — the try/except wraps the code written in US1
- **US3 (P2)**: Depends on US1 — audit tasks verify the proposal path created in US1. Can run in parallel with US2 and US4.
- **US4 (P3)**: Depends on US2 — the specific error message lives in the except block created in US2

### Within Each User Story

- Service methods before API integration (Foundational → US1)
- Core logic before error handling (US1 → US2)
- Implementation before audit/verification (US1 → US3)
- Error handling before specific error messages (US2 → US4)

### Parallel Opportunities

- T009 and T010 (US3 audit tasks) can run in parallel — different files, read-only
- US3 (audit) can run in parallel with US4 (error handling) after US1+US2 are complete
- T013 and T014 (Polish) can run in parallel

---

## Parallel Example: User Story 3 (Audit)

```bash
# Launch both audit tasks for User Story 3 together:
Task: "Audit confirm_proposal() in backend/src/api/chat.py"
Task: "Audit append_tracking_to_body() in backend/src/services/agent_tracking.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Run baseline tests
2. Complete Phase 2: Add `generate_title_from_description()` to AIAgentService
3. Complete Phase 3: Add ai_enhance=False branch in `send_message()`
4. **STOP and VALIDATE**: Toggle AI Enhance OFF → submit message → verify proposal with raw input, no error
5. Core bug is fixed — deploy/demo if ready

### Incremental Delivery

1. Phase 1 + Phase 2 → Foundation ready (new method exists)
2. Add US1 (Phase 3) → Core bug fix deployed → **MVP!** Users can create issues with AI Enhance OFF
3. Add US2 (Phase 4) → Error suppression hardened → Seamless flow guaranteed
4. Add US3 (Phase 5) → Structural parity verified → Downstream automations work consistently
5. Add US4 (Phase 6) → Specific error messages → Better UX for edge case failures
6. Phase 7 → Polish, regression testing, quickstart validation

### Sequential Implementation (Recommended for Solo Developer)

This is a small, focused bug fix. The recommended approach is sequential implementation in task order (T001 → T015), as the changes are concentrated in two files and each task builds directly on the previous one. Total estimated time: 5.0h.

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Tasks** | 15 |
| **US1 Tasks** | 4 (T003–T006) |
| **US2 Tasks** | 2 (T007–T008) |
| **US3 Tasks** | 2 (T009–T010) |
| **US4 Tasks** | 2 (T011–T012) |
| **Foundational Tasks** | 1 (T002) |
| **Setup Tasks** | 1 (T001) |
| **Polish Tasks** | 3 (T013–T015) |
| **Parallel Opportunities** | 3 (T009‖T010, T013‖T014, US3‖US4) |
| **Files Modified** | 2 (backend/src/api/chat.py, backend/src/services/ai_agent.py) |
| **Files Audited** | 2 (backend/src/api/chat.py confirm_proposal, backend/src/services/agent_tracking.py) |
| **MVP Scope** | US1 only (Phases 1–3, tasks T001–T006) |
| **Estimated Time** | 5.0h total |

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US1 is the core bug fix and constitutes the MVP — all other stories are hardening, verification, or edge case handling
- No frontend changes needed — the toggle and API call already transmit `ai_enhance` correctly
- No data model changes needed — existing `AITaskProposal` and `ChatMessageRequest` models already support the required behavior
- Agent Pipeline config append is already handled by `confirm_proposal()` and is agnostic to the `ai_enhance` flag (verified in research.md R5)
- Input validation for empty/whitespace messages already exists via Pydantic field validator (verified in research.md R6)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
