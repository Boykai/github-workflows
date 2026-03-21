# Implementation Plan: Lint & Type Suppression Audit

**Branch**: `001-lint-suppression-audit` | **Date**: 2026-03-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-lint-suppression-audit/spec.md`

## Summary

Audit and resolve ~115 lint/type-checker suppression statements (`# noqa`, `# type: ignore`, `# pyright:`, `eslint-disable`, `@ts-expect-error`) across the backend (Python 3.13 / FastAPI) and frontend (React 19 / TypeScript). The work is decomposed into four independent user stories by priority: (1) backend type suppressions, (2) frontend accessibility and React hooks, (3) backend linter suppressions, (4) test file suppressions. Each suppression is either removed by fixing the underlying issue or retained with an inline justification comment. No behavioral changes — strictly internal refactoring of type annotations, element semantics, and linter configuration.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 5.x / React 19 (frontend)
**Primary Dependencies**: FastAPI, Pydantic, Ruff, Pyright (backend); ESLint, TypeScript, Vite, Vitest, React, TanStack Query v5 (frontend)
**Storage**: N/A — no schema changes
**Testing**: `pytest` (3,365+ backend tests), `vitest` (1,219+ frontend tests)
**Target Platform**: Linux server (backend), Web browser (frontend)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: N/A — no runtime changes
**Constraints**: Zero new linter/type-checker errors; all existing tests must pass
**Scale/Scope**: 115 suppression statements across ~40 files; target ≤58 remaining (50% reduction)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | `spec.md` created with 4 prioritized user stories, acceptance scenarios, and scope boundaries |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates |
| **III. Agent-Orchestrated** | ✅ PASS | `speckit.plan` → `speckit.tasks` → `speckit.implement` pipeline |
| **IV. Test Optionality** | ✅ PASS | No new tests required — verification via existing linters and test suites. Tests are not mandated in spec |
| **V. Simplicity & DRY** | ✅ PASS | Each fix is the simplest correct resolution; no new abstractions introduced |

**Re-check after Phase 1 design**: ✅ PASS — No violations. All changes are local refactoring within existing file boundaries. No new packages, patterns, or abstractions required.

## Project Structure

### Documentation (this feature)

```text
specs/001-lint-suppression-audit/
├── plan.md              # This file
├── research.md          # Phase 0: suppression audit and resolution strategies
├── data-model.md        # Phase 1: suppression entity model
├── quickstart.md        # Phase 1: developer onboarding guide
├── contracts/           # Phase 1: N/A (internal refactoring, no API contracts)
│   └── README.md        # Explains why contracts are not applicable
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── pyproject.toml              # Ruff/Pyright config changes (B008 global ignore)
│   ├── src/
│   │   ├── api/                    # B008 noqa removal, PTH justification
│   │   │   ├── chat.py
│   │   │   ├── cleanup.py
│   │   │   ├── activity.py
│   │   │   └── workflow.py
│   │   ├── config.py               # Settings() type fix
│   │   ├── dependencies.py         # B008 noqa removal
│   │   ├── logging_utils.py        # return-value, attr-defined fixes
│   │   ├── main.py                 # arg-type fix
│   │   ├── utils.py                # return-value, misc fixes
│   │   ├── models/
│   │   │   └── chat.py             # F401 → __all__ conversion
│   │   └── services/
│   │       ├── cache.py            # return-value fixes (cast or generics)
│   │       ├── completion_providers.py  # reportMissingImports, reportCallIssue
│   │       ├── model_fetcher.py    # Task type-arg fix
│   │       ├── task_registry.py    # Task type-arg fixes (6 instances)
│   │       ├── metadata_service.py # index type fixes
│   │       ├── agents/service.py   # arg-type fix
│   │       ├── tools/service.py    # arg-type fix
│   │       ├── workflow_orchestrator/config.py  # assignment fix
│   │       ├── copilot_polling/__init__.py      # F401 → __all__
│   │       └── github_projects/
│   │           ├── __init__.py     # E402 noqa retention
│   │           ├── service.py      # Task type-arg fix
│   │           ├── copilot.py      # return-value, reportAttributeAccessIssue
│   │           ├── agents.py       # reportAttributeAccessIssue
│   │           ├── pull_requests.py
│   │           ├── projects.py
│   │           ├── issues.py
│   │           ├── branches.py
│   │           ├── board.py
│   │           └── repository.py
│   └── tests/
│       ├── unit/
│       │   ├── test_logging_utils.py
│       │   ├── test_metadata_service.py
│       │   ├── test_polling_loop.py
│       │   ├── test_transcript_detector.py
│       │   ├── test_template_files.py
│       │   ├── test_pipeline_state_store.py
│       │   └── test_agent_output.py
│       ├── concurrency/
│       │   └── test_transaction_safety.py
│       └── integration/
│           └── test_production_mode.py
└── frontend/
    └── src/
        ├── components/
        │   ├── agents/
        │   │   ├── AgentIconPickerModal.tsx   # jsx-a11y fix
        │   │   └── AgentChatFlow.tsx          # exhaustive-deps fix
        │   ├── board/
        │   │   ├── AgentPresetSelector.tsx     # jsx-a11y fixes (2)
        │   │   └── AddAgentPopover.tsx         # no-autofocus justification
        │   ├── chat/
        │   │   └── ChatInterface.tsx           # exhaustive-deps fix
        │   ├── chores/
        │   │   ├── AddChoreModal.tsx           # exhaustive-deps, no-autofocus
        │   │   └── ChoreChatFlow.tsx           # exhaustive-deps fix
        │   ├── pipeline/
        │   │   └── ModelSelector.tsx            # exhaustive-deps fix
        │   └── tools/
        │       └── UploadMcpModal.tsx           # exhaustive-deps fix
        ├── hooks/
        │   ├── useVoiceInput.ts                # no-explicit-any fix
        │   └── useRealTimeSync.ts              # exhaustive-deps justification
        ├── lib/
        │   └── lazyWithRetry.ts                # no-explicit-any justification
        └── test/
            └── setup.ts                         # @ts-expect-error justification
```

**Structure Decision**: Web application structure — `solune/backend/` (Python/FastAPI) and `solune/frontend/` (React/TypeScript). All changes are within existing files; no new files are created in the source tree.

## Complexity Tracking

> No constitution violations detected. No complexity justifications required.
