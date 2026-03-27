# Implementation Plan: Add 9 GitHub Copilot Slash Commands to Solune Chat

**Branch**: `001-copilot-slash-commands` | **Date**: 2026-03-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-copilot-slash-commands/spec.md`

## Summary

Add 9 GitHub Copilot slash commands (/explain, /fix, /doc, /tests, /setupTests, /new, /newNotebook, /search, /startDebugging) to Solune Chat using the existing passthrough pattern. The frontend registers the commands with category grouping in the autocomplete dropdown; the backend intercepts them at priority 0.1 in the chat dispatcher, builds intent-specific system prompts, and forwards to the existing `CopilotCompletionProvider.complete()`. No new API clients, authentication flows, or changes to the completion provider are required.

## Technical Context

**Language/Version**: Python ≥3.12 (backend), TypeScript ~5.9 (frontend), React 19.2
**Primary Dependencies**: FastAPI ≥0.135 (backend), GitHub Copilot SDK (`github-copilot-sdk`), @tanstack/react-query ^5.91.0 (frontend)
**Storage**: SQLite (chat messages via `add_message()` / `_persist_message()`), in-memory cache
**Testing**: pytest (backend, `python -m pytest`), Vitest (frontend, `npm run test`)
**Target Platform**: Linux server (Docker), web browser (SPA)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Copilot command responses within the same timeframe as existing `/agent` commands (~120s timeout on `CopilotCompletionProvider.complete()`)
**Constraints**: Must not modify `completion_providers.py`; must reuse existing `CopilotCompletionProvider` and OAuth token passthrough; must not break existing commands
**Scale/Scope**: 9 new commands, 2 new files (1 frontend, 1 backend), 4 modified files, 2 new test files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | `spec.md` contains 4 prioritized user stories (P1–P3) with Given-When-Then scenarios, edge cases, and 13 FRs |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | ✅ PASS | Single-responsibility: `speckit.plan` creates plan artifacts; `speckit.tasks` will create tasks |
| IV. Test Optionality with Clarity | ✅ PASS | Tests explicitly required by spec (FR-012, FR-013); frontend and backend test files specified |
| V. Simplicity and DRY | ✅ PASS | Reuses existing passthrough pattern (identical to `/agent` and `/plan`); reuses `CopilotCompletionProvider` as-is; no new abstractions beyond what's needed |

**Gate result**: ALL PASS — proceed to Phase 0.

### Post-Design Re-Check (after Phase 1)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | All design artifacts trace back to spec FRs |
| II. Template-Driven | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow template structure |
| III. Agent-Orchestrated | ✅ PASS | Plan complete; tasks.md deferred to `/speckit.tasks` |
| IV. Test Optionality | ✅ PASS | Test files and coverage explicitly defined per spec requirements |
| V. Simplicity/DRY | ✅ PASS | No unnecessary abstractions introduced; all 9 commands share one handler and one service module |

**Post-design gate result**: ALL PASS — ready for `/speckit.tasks`.

## Project Structure

### Documentation (this feature)

```text
specs/001-copilot-slash-commands/
├── plan.md              # This file
├── research.md          # Phase 0 output — design decisions and rationale
├── data-model.md        # Phase 1 output — entity definitions and relationships
├── quickstart.md        # Phase 1 output — developer setup guide
├── contracts/           # Phase 1 output — API contracts
│   └── chat-copilot.yaml  # OpenAPI fragment for Copilot command flow
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   └── chat.py                    # MODIFY — add _handle_copilot_command() at priority 0.1
│   │   ├── models/
│   │   │   └── chat.py                    # READ ONLY — ChatMessage, SenderType used by new handler
│   │   └── services/
│   │       ├── completion_providers.py    # READ ONLY — CopilotCompletionProvider.complete() reused
│   │       └── copilot_commands.py        # NEW — COPILOT_COMMANDS, COPILOT_COMMAND_PROMPTS, is_copilot_command(), execute_copilot_command()
│   └── tests/
│       └── unit/
│           └── test_copilot_commands.py   # NEW — unit tests for copilot_commands.py
├── frontend/
│   ├── src/
│   │   ├── lib/
│   │   │   └── commands/
│   │   │       ├── types.ts               # MODIFY — add optional category field to CommandDefinition
│   │   │       ├── registry.ts            # MODIFY — register 9 Copilot commands with category tags
│   │   │       ├── registry.test.ts       # MODIFY — add tests for 9 Copilot command registrations
│   │   │       └── handlers/
│   │   │           └── copilot.ts         # NEW — copilotPassthroughHandler()
│   │   └── components/
│   │       └── chat/
│   │           └── CommandAutocomplete.tsx # MODIFY — render category section headers
│   └── (package.json, tsconfig.json)      # READ ONLY
```

**Structure Decision**: Web application (Option 2) — existing `solune/backend/` and `solune/frontend/` directories. All new files slot into existing directory structures following established patterns.

## Complexity Tracking

> No constitution violations detected — this section is empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none)    | —          | —                                   |
