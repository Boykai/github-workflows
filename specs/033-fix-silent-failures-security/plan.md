# Implementation Plan: Fix Silent Failures & Security

**Branch**: `033-fix-silent-failures-security` | **Date**: 2026-03-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/033-fix-silent-failures-security/spec.md`

## Summary

Replace 9 silent `except Exception: pass` blocks in backend services with appropriate logging at correct severity levels (debug/warning/error), prevent 3 exception-detail leaks to end users via Signal messaging, and systematically improve 37 remaining bare `except Exception:` blocks by adding exception binding (`as e`) and narrowing to specific types where possible. No control flow changes — only observability and security improvements to existing exception handlers.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: FastAPI, aiosqlite, githubkit (GitHub SDK), httpx, Pydantic
**Storage**: SQLite via aiosqlite (async)
**Testing**: pytest with pytest-asyncio (`uv run --extra dev pytest tests/unit/ -x`)
**Target Platform**: Linux server (Docker)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: N/A — changes are logging-only, no performance-sensitive paths affected
**Constraints**: Logging must not alter control flow; `logging_utils.py` resilience blocks must remain bare for crash safety
**Scale/Scope**: 9 critical/high exception handlers, 3 user-facing error leaks, 37 bare `except Exception:` blocks across ~15 files in `backend/src/`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | `spec.md` exists with 5 prioritized user stories (P1–P2) and Given-When-Then acceptance criteria |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Single-responsibility: `speckit.plan` produces plan artifacts only |
| **IV. Test Optionality** | ✅ PASS | Tests not explicitly mandated in spec; static analysis verification in SC-006/SC-007 can be run via `ruff` and `grep` checks |
| **V. Simplicity and DRY** | ✅ PASS | Changes are surgical additions of `logger.*()` calls and exception type narrowing — no new abstractions, no new files, no new dependencies |

**Gate result**: All principles pass. No violations to justify in Complexity Tracking.

### Post-Design Re-Check (after Phase 1)

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts (research.md, data-model.md, contracts/, quickstart.md) trace back to spec.md user stories and requirements |
| **II. Template-Driven** | ✅ PASS | plan.md follows template structure; research.md uses Decision/Rationale/Alternatives format |
| **III. Agent-Orchestrated** | ✅ PASS | Plan phase complete; ready for handoff to `/speckit.tasks` |
| **IV. Test Optionality** | ✅ PASS | No tests mandated; verification via static checks (grep, ruff) defined in contracts |
| **V. Simplicity and DRY** | ✅ PASS | No new abstractions introduced; reuses existing `safe_error_response()` and `logging` patterns |

**Post-design gate result**: All principles continue to pass after design phase.

## Project Structure

### Documentation (this feature)

```text
specs/033-fix-silent-failures-security/
├── plan.md              # This file
├── research.md          # Phase 0: Exception handling research & decisions
├── data-model.md        # Phase 1: Entity definitions (exception handlers, log entries)
├── quickstart.md        # Phase 1: Implementation quickstart guide
├── contracts/
│   └── logging-contract.md  # Phase 1: Logging severity & format contract
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── logging_utils.py              # safe_error_response() — already exists
│   ├── services/
│   │   ├── github_projects/
│   │   │   ├── __init__.py           # Client cleanup handler (line 49)
│   │   │   └── service.py            # Workflow config + branch OID handlers (lines 927, 4983)
│   │   ├── metadata_service.py       # SQLite read fallback handler (line 112)
│   │   ├── agent_creator.py          # DB update handlers (lines 727, 768, 877, 1095)
│   │   ├── signal_chat.py            # Signal context + user-facing error handlers (lines 159, 166-170)
│   │   ├── agents/service.py         # Optional config loading (line 553)
│   │   ├── blocking_queue.py         # Queue handler (line 437)
│   │   ├── chores/service.py         # Chore processing handlers (6 locations)
│   │   ├── chores/template_builder.py # Template parsing (line 199)
│   │   ├── copilot_polling/pipeline.py # Polling handlers (2 locations)
│   │   └── workflow_orchestrator/config.py # Config parsing (9 locations)
│   └── api/
│       ├── tasks.py                  # Task endpoint handler (line 131)
│       ├── projects.py               # Project endpoint handler (line 247)
│       ├── signal.py                 # Signal webhook handlers (lines 75, 125)
│       ├── chores.py                 # Chore endpoint handlers (lines 117, 306)
│       ├── workflow.py               # Workflow endpoint handlers (lines 242, 409)
│       ├── auth.py                   # Auth handler (line 75)
│       └── chat.py                   # Chat handler (line 827)
└── tests/
    └── unit/                         # 60 test files, pytest + pytest-asyncio
```

**Structure Decision**: Web application layout (Option 2). All changes are in `backend/src/` — no frontend changes required. Changes are spread across services and API layers but are all exception-handler modifications (no new files except `safe_error_response` utility which already exists in `logging_utils.py`).

## Complexity Tracking

> No violations — all constitution principles pass. No complexity justification needed.

*No entries required.*
