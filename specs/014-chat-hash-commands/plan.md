# Implementation Plan: Enhance Chat # Commands — App-Wide Settings Control & #help Command with Test Coverage

**Branch**: `014-chat-hash-commands` | **Date**: 2026-02-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/014-chat-hash-commands/spec.md`

## Summary

Add a client-side `#` command system to the existing chat interface that intercepts `#`-prefixed messages (and the `help` keyword) before they reach the AI backend, routes them to a centralized command registry, and executes local handlers for help output and app-wide settings updates (theme, language, notifications, display preferences). Includes a real-time autocomplete overlay with keyboard navigation, confirmation/error system messages, and comprehensive unit and integration tests using the existing Vitest + React Testing Library infrastructure.

## Technical Context

**Language/Version**: TypeScript 5.4 / Node 20 (frontend), Python 3.12 (backend — no changes expected)
**Primary Dependencies**: React 18, Vite 5, TanStack Query v5, Tailwind CSS, Radix UI
**Storage**: localStorage (theme persistence via ThemeProvider), SQLite via aiosqlite (backend settings — existing, consumed via settingsApi)
**Testing**: Vitest 4.0+ / @testing-library/react 16.3+ / happy-dom 20.6+ (frontend unit/integration)
**Target Platform**: Modern browsers (frontend)
**Project Type**: web (frontend-only changes, backend unchanged)
**Performance Goals**: Autocomplete overlay appears within 200ms of typing `#`; settings applied within 1 second; command responses are instantaneous (client-side)
**Constraints**: No new frontend dependencies; reuse existing state management patterns (TanStack Query, Context API for theme); client-side command interception must prevent AI backend calls for commands
**Scale/Scope**: ~6 command definitions (help, theme, language, notifications, display, clear), 1 new hook, 2–3 new components, 1 command registry module, ~8 test files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | spec.md exists with 6 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, and scope boundaries |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase follows single-responsibility agent model; outputs are well-defined markdown documents |
| IV. Test Optionality with Clarity | ✅ PASS | Tests are *explicitly requested* in the feature specification (FR-019, User Story 6); test coverage is a stated requirement |
| V. Simplicity and DRY | ✅ PASS | Single command registry drives all surfaces (help, autocomplete, execution) — no duplication; reuses existing state management and UI patterns |

**Gate Result**: ✅ ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/014-chat-hash-commands/
├── plan.md              # This file
├── research.md          # Phase 0: Research findings
├── data-model.md        # Phase 1: Command system entity model
├── quickstart.md        # Phase 1: Developer quickstart guide
├── contracts/           # Phase 1: Command system contracts
│   └── command-registry.md
└── tasks.md             # Phase 2 output (created by /speckit.tasks, NOT this phase)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── components/
│   │   └── chat/
│   │       ├── ChatInterface.tsx          # MODIFY: Integrate command interception and autocomplete
│   │       ├── CommandAutocomplete.tsx     # NEW: Autocomplete overlay component
│   │       └── SystemMessage.tsx          # NEW: Styled system message for command responses
│   ├── hooks/
│   │   ├── useChat.ts                     # MODIFY: Add command interception before AI send
│   │   └── useCommands.ts                # NEW: Command parsing, execution, and autocomplete logic
│   ├── lib/
│   │   └── commands/
│   │       ├── registry.ts               # NEW: Command registry (single source of truth)
│   │       ├── types.ts                  # NEW: Command type definitions
│   │       └── handlers/
│   │           ├── help.ts               # NEW: #help command handler
│   │           └── settings.ts           # NEW: Settings command handlers (theme, language, etc.)
│   ├── services/
│   │   └── api.ts                        # EXISTING: settingsApi (consumed by settings handlers)
│   └── test/
│       └── factories/
│           └── index.ts                  # MODIFY: Add command-related test factories
│
│   # New test files (co-located with source):
│   ├── lib/commands/registry.test.ts             # NEW: Registry unit tests
│   ├── lib/commands/handlers/help.test.ts        # NEW: Help handler tests
│   ├── lib/commands/handlers/settings.test.ts    # NEW: Settings handler tests
│   ├── hooks/useCommands.test.tsx                # NEW: Command hook tests
│   ├── components/chat/CommandAutocomplete.test.tsx  # NEW: Autocomplete component tests
│   └── components/chat/ChatInterface.test.tsx    # NEW: Integration tests for command flow
```

**Structure Decision**: Web application — the repository uses `backend/` + `frontend/` split. This feature is entirely frontend (client-side command interception). New code is organized under `frontend/src/lib/commands/` for the registry and handlers (pure logic), `frontend/src/hooks/useCommands.ts` for the React hook, and `frontend/src/components/chat/` for UI components. Tests are co-located following the existing pattern.

## Complexity Tracking

> No constitution violations to justify. All principles are satisfied.

## Constitution Re-Check (Post Phase 1 Design)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | All design artifacts trace back to spec.md requirements (FR-001 through FR-020) |
| II. Template-Driven Workflow | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow canonical structure |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase produced well-defined outputs for handoff to tasks phase |
| IV. Test Optionality with Clarity | ✅ PASS | Tests are explicitly required (FR-019); test files and patterns are defined in the plan |
| V. Simplicity and DRY | ✅ PASS | Single command registry serves as source of truth for all surfaces; handlers use existing settingsApi and ThemeProvider; no new dependencies introduced |

**Post-Design Gate Result**: ✅ ALL PASS — ready for Phase 2 (tasks generation via `/speckit.tasks`).
