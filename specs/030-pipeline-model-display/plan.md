# Implementation Plan: Display Models Used in Agent Pipeline Section of Parent Issue Description

**Branch**: `030-pipeline-model-display` | **Date**: 2026-03-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/030-pipeline-model-display/spec.md`

## Summary

Add a "Model" column to the Agent Pipeline tracking table embedded in GitHub Parent Issue descriptions. The tracking table is rendered by `backend/src/services/agent_tracking.py` and currently shows columns: #, Status, Agent, State. This feature extends the table with a fifth "Model" column that displays the model name assigned to each agent (sourced from the `AgentAssignment.config` dict's `model_name` field), or "TBD" if no model is configured. The change requires updating the `AgentStep` dataclass to carry a `model` field, modifying `build_agent_pipeline_steps()` to extract the model name from agent assignments, updating `render_tracking_markdown()` to include the column, and adjusting `parse_tracking_from_body()` regex to parse the new column. All existing callers (chores service, workflow orchestrator) pass `AgentAssignment` objects that already carry model data in their `config` dict — no caller changes are needed.

## Technical Context

**Language/Version**: Python 3.13 (backend)
**Primary Dependencies**: FastAPI 0.135, aiosqlite 0.22, Pydantic v2.12 (backend)
**Storage**: SQLite with WAL mode (aiosqlite) — existing schema, no changes needed
**Testing**: pytest + pytest-asyncio (backend); existing test file `backend/tests/unit/test_agent_tracking.py`
**Target Platform**: Linux server (Docker); GitHub issue description rendering (GitHub-flavored Markdown)
**Project Type**: Web application (backend only — this feature modifies only the backend agent tracking service)
**Performance Goals**: N/A — string formatting operations, negligible overhead
**Constraints**: Must preserve backward compatibility with existing tracking tables (parsing should handle both old 4-column and new 5-column formats); Markdown table must render correctly in GitHub issue views
**Scale/Scope**: 1 modified backend file (`agent_tracking.py`), 1 modified test file (`test_agent_tracking.py`), no new files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 3 prioritized user stories (P1×2, P2×1), Given-When-Then acceptance scenarios, 8 functional requirements (FR-001–FR-008), 6 success criteria, 5 edge cases |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (specify → plan → tasks → implement) |
| **IV. Test Optionality** | ✅ PASS | Existing test file `test_agent_tracking.py` covers all modified functions; tests will be updated to verify model column |
| **V. Simplicity/DRY** | ✅ PASS | Minimal change — extends existing data structures and rendering functions; reuses existing `AgentAssignment.config` field for model data; no new dependencies or abstractions |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace back to spec FRs (FR-001–FR-008) |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow template structure |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 |
| **IV. Test Optionality** | ✅ PASS | Existing test file will be updated; no new test infrastructure needed |
| **V. Simplicity/DRY** | ✅ PASS | Single file change with backward-compatible parsing; model data already available in `AgentAssignment.config` dict — no new data fetching required |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/030-pipeline-model-display/
├── plan.md              # This file
├── research.md          # Phase 0: Research decisions (R1–R3)
├── data-model.md        # Phase 1: Entity definitions and state changes
├── quickstart.md        # Phase 1: Developer onboarding guide
├── contracts/
│   └── tracking-table.md  # Phase 1: Markdown table contract
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   └── services/
│       └── agent_tracking.py           # MODIFIED: Add model field to AgentStep, update render/parse
└── tests/
    └── unit/
        └── test_agent_tracking.py      # MODIFIED: Update tests for model column
```

**Structure Decision**: Backend-only change. Single service file modification. The `agent_tracking.py` module is self-contained — it defines the data structures, rendering, and parsing for the pipeline tracking table. All changes are localized to this module and its test file. No API endpoint changes, no frontend changes, no database schema changes.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| Add `model` field to `AgentStep` with default `""` | Backward compatible — existing code that creates `AgentStep` without model continues to work. Empty string renders as "TBD" in the table. | Separate `AgentStepWithModel` subclass (rejected: violates DRY, complicates type handling throughout the module) |
| Extract model from `AgentAssignment.config` dict | Model data is already stored in the `config` dict as `model_name` when agents are assigned via the pipeline UI. No additional database queries needed. | Query agent model preferences from SQLite at render time (rejected: adds async I/O to a pure function, over-engineered for string lookup) |
| Escape pipe characters in model names | Markdown tables use `|` as column delimiter. Model names containing `|` would break table rendering. Simple `.replace("|", "\\|")` handles this edge case. | Reject model names with special characters (rejected: overly restrictive, breaks valid model identifiers) |
