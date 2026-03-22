# Implementation Plan: Startup Config Validation for AI Provider, Azure OpenAI, and Database Path

**Branch**: `001-startup-config-validation` | **Date**: 2026-03-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-startup-config-validation/spec.md`

## Summary

Add boot-time validation to the existing `_validate_production_secrets()` Pydantic model validator in `config.py` to reject unknown AI providers (fatal in all modes), detect incomplete Azure OpenAI credentials (error in production, warning in debug), and enforce absolute database paths in production. Scope is strictly two files: `config.py` (~+25 lines of validation logic) and `tests/unit/test_config_validation.py` (~+60 lines across 3 new test classes). No new validators, methods, or configuration fields are introduced.

## Technical Context

**Language/Version**: Python 3.13 (target-version in ruff/pyright config; requires >=3.12)
**Primary Dependencies**: Pydantic v2 (`model_validator`), pydantic-settings (`BaseSettings`), `pathlib.Path` (stdlib)
**Storage**: SQLite via `database_path` setting (default: `/var/lib/solune/data/settings.db`)
**Testing**: pytest (existing `tests/unit/test_config_validation.py` and `tests/unit/test_config.py`)
**Target Platform**: Linux server (Docker container)
**Project Type**: Web application (backend Python + frontend TypeScript)
**Performance Goals**: N/A — startup-time validation, runs once at boot
**Constraints**: Zero new dependencies; all validation inline in existing validator
**Scale/Scope**: 2 files changed, ~85 net new lines total

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | `spec.md` complete with prioritized user stories (P1–P3), Given-When-Then scenarios, and edge cases |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase produces well-defined artifacts for downstream task/implement agents |
| IV. Test Optionality with Clarity | ✅ PASS | Tests explicitly requested in spec FR-010; 3 test classes mandated |
| V. Simplicity and DRY | ✅ PASS | All validation added inline to existing `_validate_production_secrets()` — no new validators, methods, or abstractions; reuses existing `_make_production()` / `_make_debug()` test helpers |

**Gate result**: ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-startup-config-validation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (empty — no API contracts for this feature)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
solune/backend/
├── src/
│   └── config.py                          # Modified: ~+25 lines in _validate_production_secrets()
└── tests/
    └── unit/
        ├── test_config.py                 # Unchanged — verify no regression
        └── test_config_validation.py      # Modified: +3 new test classes (~60 lines)
```

**Structure Decision**: Web application layout (Option 2). Changes are confined to the existing backend project under `solune/backend/`. No new files are created; only two existing files are modified.

## Complexity Tracking

> No Constitution Check violations — this section is intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
