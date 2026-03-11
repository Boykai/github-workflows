# Implementation Plan: Enforce Blocking Queue in Polling Loop & Fix Branch Ancestry

**Branch**: `035-blocking-queue-guard` | **Date**: 2026-03-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/035-blocking-queue-guard/spec.md`

## Summary

Four bugs allow blocked parent issues to start agent pipelines, leave activated entries without dispatch, and resolve incorrect branch ancestry. This plan adds a shared `_is_pending_in_blocking_queue()` guard called from all three polling check functions (backlog, ready, in-progress), fixes the recovery exception handler to fail closed, returns activated entries from `sweep_stale_entries()` so the polling loop can dispatch agents, adds deferred-dispatch logging in recovery, and hardens `_determine_base_ref()` to use the issue-specific `blocking_source_issue` branch via a new `get_base_ref_for_entry()` helper. All changes are backend-only, touch 5 files, add 2 new functions, and require no schema or frontend changes.

## Technical Context

**Language/Version**: Python ≥3.12 (target 3.13)
**Primary Dependencies**: FastAPI ≥0.135, Pydantic ≥2.12, aiosqlite ≥0.22, httpx ≥0.28, githubkit ≥0.14.6
**Storage**: aiosqlite (blocking queue entries persisted via `BlockingQueueStore`)
**Testing**: pytest ≥9.0 + pytest-asyncio ≥1.3 (asyncio_mode = "auto"), 72 unit test files, 5 integration test files
**Target Platform**: Linux Docker containers (python:3.13-slim)
**Project Type**: Web application (backend only for this feature)
**Performance Goals**: No additional latency — guard function performs a single in-memory store lookup per issue per polling cycle
**Constraints**: Zero regressions; fail-open in polling, fail-closed in recovery; no public API changes
**Scale/Scope**: 5 files modified, 2 new functions added, ~80 net lines of change across backend/src/services/

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Specification-First Development — **PASS**

The feature has a complete `spec.md` with 5 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios for each, 11 functional requirements (FR-001 through FR-011), 7 measurable success criteria, explicit scope boundaries, edge cases, and assumptions. The specification passed all checklist items in `checklists/requirements.md`.

### Principle II: Template-Driven Workflow — **PASS**

All artifacts follow canonical templates: `spec.md` used the spec template, this `plan.md` follows the plan template. No custom sections added.

### Principle III: Agent-Orchestrated Execution — **PASS**

Workflow followed: `/speckit.specify` → `/speckit.plan` (this). Each agent produced its defined output before handoff.

### Principle IV: Test Optionality with Clarity — **PASS (Tests Required)**

The spec explicitly mandates tests in the Verification section: unit tests for `_is_pending_in_blocking_queue()` and `sweep_stale_entries()`, polling tests for guard behavior, and integration tests for blocking chains. This is justified — modifying critical pipeline-dispatch control flow without test coverage would risk silent regressions.

### Principle V: Simplicity and DRY — **PASS**

All changes reuse existing patterns and abstractions. The shared guard `_is_pending_in_blocking_queue()` avoids duplicating blocking queue checks across three functions. `get_base_ref_for_entry()` wraps existing `get_base_ref_for_issue()` with entry-specific lookup. No new dependencies, no new abstractions, no new patterns — pure bug fixes using established conventions.

## Project Structure

### Documentation (this feature)

```text
specs/035-blocking-queue-guard/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── blocking-queue-guard.md
│   ├── sweep-dispatch.md
│   └── branch-ancestry.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   └── services/
│       ├── blocking_queue.py                        # Fix sweep return; add get_base_ref_for_entry(); log deferred dispatch
│       ├── copilot_polling/
│       │   ├── pipeline.py                          # Add _is_pending_in_blocking_queue(); guard 3 check functions
│       │   ├── recovery.py                          # Fix exception handler to fail closed
│       │   └── polling_loop.py                      # Dispatch agents for activated entries from sweep
│       └── workflow_orchestrator/
│           └── orchestrator.py                      # Harden _determine_base_ref() with entry-specific lookup
└── tests/
    ├── unit/
    │   ├── test_blocking_queue.py                   # Tests for sweep return, get_base_ref_for_entry
    │   ├── test_copilot_polling.py                  # Tests for guard in check_backlog/ready/in_progress
    │   ├── test_recovery.py                         # Tests for fail-closed exception handler
    │   ├── test_polling_loop.py                     # Tests for sweep dispatch
    │   └── test_workflow_orchestrator.py            # Tests for entry-specific base ref
    └── integration/
        └── test_blocking_pipeline.py                # End-to-end blocking chain tests
```

**Structure Decision**: Web application structure (backend only). All changes are within existing `backend/src/services/` modules — no new files, no new directories, no new top-level structure. Tests extend existing test files.

## Complexity Tracking

> No constitution violations found. All changes are minimal, use existing patterns, and add no new abstractions.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
