# Tasks: Display Models Used in Agent Pipeline Section of Parent Issue Description

**Input**: Design documents from `/specs/030-pipeline-model-display/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/tracking-table.md, quickstart.md

**Tests**: Existing test file `backend/tests/unit/test_agent_tracking.py` covers all modified functions. Tests will be updated to verify model column behavior. No new test files needed.

**Organization**: Tasks grouped by user story (P1×2, P2×1) for independent implementation and testing. This is a backend-only change concentrated in a single service file (`agent_tracking.py`) and its test file. Each user story can be delivered as an independently verifiable increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Exact file paths included in descriptions

## Path Conventions

- **Web app**: `frontend/src/` (React/TypeScript), `backend/src/` (Python/FastAPI)
- Backend service: `backend/src/services/agent_tracking.py` — PRIMARY change target (AgentStep, build/render/parse functions)
- Backend tests: `backend/tests/unit/test_agent_tracking.py` — test updates for model column
- Backend models: `backend/src/models/agent.py` — no changes (existing `AgentAssignment.config` dict already carries `model_name`)
- Frontend: no changes — pipeline tracking table is rendered server-side into GitHub issue body as Markdown

---

## Phase 1: Setup

**Purpose**: Verify baseline — all existing tests pass before making changes. No new project setup required; all infrastructure is already in place.

- [x] T001 Verify existing backend test suite baseline by running `python -m pytest backend/tests/unit/test_agent_tracking.py -v --tb=short` to confirm all current tests pass before modifications

**Checkpoint**: Baseline confirmed. All existing agent tracking tests pass. Ready for implementation.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Extend the `AgentStep` dataclass with the `model` field. This MUST be complete before any user story can be implemented — all rendering, parsing, and building functions depend on the data structure.

**⚠️ CRITICAL**: The `model` field on `AgentStep` is required by US1 (model display) and US2 (TBD placeholder). No user story work can begin until this field exists.

- [x] T002 Add `model: str = ""` field to the `AgentStep` dataclass between `agent_name` and `state` fields in backend/src/services/agent_tracking.py — the empty string default ensures backward compatibility with all existing instantiations of `AgentStep` throughout the codebase
- [x] T003 Update the module-level docstring at the top of backend/src/services/agent_tracking.py to show the new 5-column table format (`| # | Status | Agent | Model | State |`) replacing the old 4-column example, so the documentation matches the new behavior

**Checkpoint**: `AgentStep` has a `model` field with default `""`. All existing tests still pass (the new field has a default value). Ready for US1 implementation.

---

## Phase 3: User Story 1 — View Model Assignments in Agent Pipeline Table (Priority: P1) 🎯 MVP

**Goal**: When a developer views a GitHub Parent Issue, the Agent Pipeline table includes a "Model" column showing the model name assigned to each agent (e.g., "gpt-4o", "claude-3-5-sonnet"), sourced from `AgentAssignment.config["model_name"]`.

**Independent Test**: Create a pipeline with agents that have models assigned via their `config` dict → verify the tracking table in the issue body includes a "Model" column with correct model names for each agent.

### Implementation for User Story 1

- [x] T004 [US1] Update `build_agent_pipeline_steps()` in backend/src/services/agent_tracking.py to extract `model_name` from each `AgentAssignment.config` dict — use logic: `model = agent.config.get("model_name", "") if isinstance(getattr(agent, "config", None), dict) else ""` — and pass it to the `AgentStep` constructor as `model=model`
- [x] T005 [US1] Update `render_tracking_markdown()` in backend/src/services/agent_tracking.py to render the new 5-column table: change header to `| # | Status | Agent | Model | State |`, update separator row to `|---|--------|-------|-------|-------|`, and update each row to include the model display value with pipe character escaping — use `model_display = (step.model or "TBD").replace("|", "\\|")` — placing Model between Agent and State columns
- [x] T006 [US1] Update `_ROW_RE` regex in backend/src/services/agent_tracking.py to match the new 5-column format: `r"\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*` `` `([^`]+)` `` `\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|"` — this regex captures index, status, agent_name, model, and state as groups 1–5
- [x] T007 [US1] Add a legacy fallback regex `_ROW_RE_OLD` in backend/src/services/agent_tracking.py matching the old 4-column format: `r"\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*` `` `([^`]+)` `` `\s*\|\s*([^|]+?)\s*\|"` — this preserves backward compatibility for parsing existing issues with the old table format
- [x] T008 [US1] Update `parse_tracking_from_body()` in backend/src/services/agent_tracking.py to first try matching rows with the new 5-column `_ROW_RE` (populating `AgentStep.model` from group 4, with state from group 5), and fall back to `_ROW_RE_OLD` for old 4-column rows (setting `model=""`, with state from group 4) — ensuring both old and new table formats are parsed correctly
- [x] T009 [US1] Update tests in backend/tests/unit/test_agent_tracking.py: modify `SAMPLE_BODY` to use the new 5-column format with Model column, add `SAMPLE_BODY_LEGACY` constant with the old 4-column format, update `TestRenderTrackingMarkdown` to verify Model column appears in output with correct model names, update `TestParseTrackingFromBody` to verify model field is populated from parsed rows
- [x] T010 [US1] Add test for backward-compatible parsing in backend/tests/unit/test_agent_tracking.py: parse `SAMPLE_BODY_LEGACY` (old 4-column format) and verify all `AgentStep.model` fields default to `""`, ensuring old issues continue to parse correctly
- [x] T011 [US1] Update `TestBuildAgentPipelineSteps` in backend/tests/unit/test_agent_tracking.py: extend `_FakeAgent` with an optional `config` attribute, add test case verifying that `build_agent_pipeline_steps()` extracts `model_name` from `agent.config` dict and populates `AgentStep.model`

**Checkpoint**: Agent Pipeline table renders with a "Model" column showing correct model names. Old 4-column tables parse correctly with model defaulting to empty string. This is the MVP — the core feature is functional.

---

## Phase 4: User Story 2 — Display Placeholder When Model Is Not Assigned (Priority: P1)

**Goal**: When an agent in the pipeline does not have a model configured (config is `None`, `{}`, or `model_name` is empty), the Model column displays "TBD" instead of an empty cell, maintaining visual consistency.

**Independent Test**: Create a pipeline with agents where some have models and some do not → verify the Model column shows "TBD" for unassigned agents and the actual model name for assigned agents.

### Implementation for User Story 2

- [x] T012 [US2] Add test cases for TBD placeholder in backend/tests/unit/test_agent_tracking.py: verify `render_tracking_markdown()` outputs "TBD" when `AgentStep.model` is `""`, verify `build_agent_pipeline_steps()` sets `model=""` when `agent.config` is `None`, when `agent.config` is `{}`, and when `agent.config` has no `model_name` key
- [x] T013 [US2] Add test for mixed model/TBD rendering in backend/tests/unit/test_agent_tracking.py: create a list of `AgentStep` objects where some have model names and some have `model=""`, render with `render_tracking_markdown()`, and verify the output contains both model names and "TBD" placeholders in the correct rows

**Checkpoint**: "TBD" placeholder appears consistently for all agents without model assignments. Mixed pipelines (some with models, some without) render correctly. Visual consistency is maintained.

---

## Phase 5: User Story 3 — Pipeline Table Updates When Agent Models Change (Priority: P2)

**Goal**: When a model assignment changes, the parse → modify → re-render cycle preserves the model field, and the re-rendered table reflects the current model assignments. The `update_agent_state()` function already handles this flow (parse → modify state → render) — the model is preserved through this cycle because `parse_tracking_from_body()` now populates `AgentStep.model` and `render_tracking_markdown()` renders it.

**Independent Test**: Parse an issue body with a 5-column tracking table, modify an agent's state via `mark_agent_active()`, and verify the re-rendered table preserves the model values for all agents.

### Implementation for User Story 3

- [x] T014 [US3] Add test for model preservation through state update cycle in backend/tests/unit/test_agent_tracking.py: create a body with a 5-column tracking table containing model names, call `mark_agent_active()` on one agent, parse the resulting body, and verify all `AgentStep.model` fields are preserved (not lost during the parse → modify → render cycle)
- [x] T015 [US3] Add test for natural migration of old tables in backend/tests/unit/test_agent_tracking.py: start with a body containing an old 4-column tracking table, call `update_agent_state()` to modify an agent's state, parse the resulting body, and verify it now has the new 5-column format with "TBD" in all Model columns (demonstrating automatic forward migration)
- [x] T016 [US3] Add test for `append_tracking_to_body()` idempotency in backend/tests/unit/test_agent_tracking.py: call `append_tracking_to_body()` on a body that already has a 5-column tracking table, and verify the result still has exactly one tracking section with the correct 5-column format (no duplicate Model columns or double tracking sections)

**Checkpoint**: Model field is preserved through all state update cycles. Old 4-column tables are naturally migrated to 5-column format on first state update. `append_tracking_to_body()` is idempotent. Dynamic synchronization is verified.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, edge case testing, and regression verification across all user stories.

- [x] T017 [P] Add edge case test for special characters in model names in backend/tests/unit/test_agent_tracking.py: create an `AgentStep` with a model name containing pipe characters (e.g., "model|v2"), render with `render_tracking_markdown()`, and verify the pipe is escaped as `\|` so the Markdown table renders correctly
- [x] T018 [P] Add edge case test for very long model names in backend/tests/unit/test_agent_tracking.py: create an `AgentStep` with a long model name (e.g., "custom-fine-tuned-gpt-4o-2026-03-extended-context"), render and verify the table still contains the full name without truncation
- [x] T019 Run full agent tracking test suite: `python -m pytest backend/tests/unit/test_agent_tracking.py -v --tb=short` to verify all existing and new tests pass
- [x] T020 [P] Run backend linter: `ruff check backend/src/services/agent_tracking.py backend/tests/unit/test_agent_tracking.py` to verify code style compliance
- [x] T021 Run quickstart.md verification checklist from specs/030-pipeline-model-display/quickstart.md: model in table, TBD placeholder, mixed models, backward parsing, re-render migration, special characters, idempotent append, all existing tests pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — baseline test run
- **Foundational (Phase 2)**: Depends on Setup — `AgentStep.model` field must exist before any user story
- **US1 (Phase 3)**: Depends on Foundational — core rendering and parsing uses the new field
- **US2 (Phase 4)**: Depends on US1 — TBD placeholder tests verify behavior implemented in US1
- **US3 (Phase 5)**: Depends on US1 — state update cycle tests verify end-to-end flow from US1
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational (Phase 2) — can start after `AgentStep.model` field exists
- **US2 (P1)**: Depends on US1 — tests verify the TBD rendering logic implemented in `render_tracking_markdown()` during US1
- **US3 (P2)**: Depends on US1 — tests verify the parse → modify → render cycle works with model data from US1. Can run in parallel with US2.

### Within Each User Story

- Data structure changes before function updates (Foundational → US1)
- Rendering before parsing (T005 → T006–T008)
- Implementation before tests (T004–T008 → T009–T011)
- Core feature before placeholder behavior (US1 → US2)
- Core feature before dynamic update verification (US1 → US3)

### Parallel Opportunities

- T002 and T003 (Foundational) can run in parallel — different parts of the same file, no overlap
- US2 and US3 can run in parallel after US1 completes — independent test additions
- T017 and T018 (Polish edge cases) can run in parallel — independent test cases
- T019 and T020 (Polish validation) can run in parallel — different tools

---

## Parallel Example: User Story 1

```bash
# T004 and T005 modify different functions — can be done in parallel:
Task: "Update build_agent_pipeline_steps() to extract model_name in backend/src/services/agent_tracking.py"
Task: "Update render_tracking_markdown() to render Model column in backend/src/services/agent_tracking.py"

# T006 and T007 add different regex patterns — can be done in parallel:
Task: "Update _ROW_RE regex for 5-column format in backend/src/services/agent_tracking.py"
Task: "Add _ROW_RE_OLD fallback regex for 4-column format in backend/src/services/agent_tracking.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Run baseline tests
2. Complete Phase 2: Add `model` field to `AgentStep`
3. Complete Phase 3: Update build/render/parse functions + tests
4. **STOP and VALIDATE**: Create pipeline with models → verify Model column appears with correct names
5. Core feature is functional — deploy/demo if ready

### Incremental Delivery

1. Phase 1 + Phase 2 → Foundation ready (`AgentStep` has `model` field)
2. Add US1 (Phase 3) → Model column renders in pipeline table → **MVP!** Stakeholders can see model assignments
3. Add US2 (Phase 4) → TBD placeholder for unassigned models → Visual consistency guaranteed
4. Add US3 (Phase 5) → Dynamic update cycle verified → Model data stays in sync through state changes
5. Phase 6 → Edge cases, linting, quickstart validation

### Sequential Implementation (Recommended for Solo Developer)

This is a small, focused backend change. The recommended approach is sequential implementation in task order (T001 → T021), as the changes are concentrated in two files (`agent_tracking.py` and `test_agent_tracking.py`). Each task builds directly on the previous one. Total estimated time: 2.0h.

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Tasks** | 21 |
| **US1 Tasks** | 8 (T004–T011) |
| **US2 Tasks** | 2 (T012–T013) |
| **US3 Tasks** | 3 (T014–T016) |
| **Foundational Tasks** | 2 (T002–T003) |
| **Setup Tasks** | 1 (T001) |
| **Polish Tasks** | 5 (T017–T021) |
| **Parallel Opportunities** | 5 (T002‖T003, US2‖US3, T017‖T018, T019‖T020, T004‖T005) |
| **Files Modified** | 2 (backend/src/services/agent_tracking.py, backend/tests/unit/test_agent_tracking.py) |
| **New Files** | 0 |
| **MVP Scope** | US1 only (Phases 1–3, tasks T001–T011) |
| **Estimated Time** | 2.0h total |
| **Suggested MVP Scope** | User Story 1 (View Model Assignments) — delivers core value |

## Notes

- [P] tasks = different files or independent sections, no dependencies
- [Story] label maps task to specific user story for traceability
- US1 is the core feature and constitutes the MVP — US2 and US3 are hardening and verification
- No frontend changes needed — the pipeline tracking table is rendered server-side into the GitHub issue body as Markdown text
- No database schema changes needed — model data already exists in `AgentAssignment.config` dict
- No new dependencies — all changes use existing Python standard library and dataclass features
- Model data source: `AgentAssignment.config.get("model_name", "")` (see research.md R1)
- Backward compatibility: old 4-column tables parsed via fallback regex (see research.md R2)
- Model column placement: between Agent and State columns (see research.md R3)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
