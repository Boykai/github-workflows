# Implementation Plan: Add #help Command to User Chat

**Branch**: `033-chat-help-command` | **Date**: 2026-03-09 | **Spec**: [`specs/033-chat-help-command/spec.md`](spec.md)
**Input**: Feature specification from `/specs/033-chat-help-command/spec.md`

## Summary

Add `#help` as an alias for the existing `/help` chat command. When a user types `#help` (case-insensitive, whitespace-trimmed), the command parser intercepts it before any broadcast logic and injects an ephemeral system message listing all available commands. The response is local-only (not persisted or sent to other users) and visually differentiated as a system/bot message. The implementation is a single-line addition to `parseCommand()` in the existing command registry, plus a minor annotation update in the help handler output.

## Technical Context

**Language/Version**: TypeScript ~5.9 / React 19 (frontend-only change)
**Primary Dependencies**: React 19, TanStack Query, Vitest (testing)
**Storage**: N/A — ephemeral local state only, no backend persistence
**Testing**: Vitest + React Testing Library (frontend unit tests)
**Target Platform**: Modern browsers (desktop and mobile viewports)
**Project Type**: Web application (frontend-only change within `frontend/` project)
**Performance Goals**: Instant response — `#help` is a synchronous local command, no network calls
**Constraints**: No new dependencies; no backend changes; no breaking changes to existing `/help` or `help` aliases
**Scale/Scope**: 2 files modified (`registry.ts`, `help.ts`), 2 test files updated (`registry.test.ts`, `help.test.ts`)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development — ✅ PASS

The parent issue (#2785) includes a user story, UI/UX description, 8 functional requirements (FR), and technical notes. Scope boundaries are explicit: frontend-only, no backend changes, no new dependencies.

### II. Template-Driven Workflow — ✅ PASS

All artifacts follow canonical templates from `.specify/templates/`. This plan follows `plan-template.md`. Research, data model, contracts, and quickstart follow established conventions from prior specs (026, 031).

### III. Agent-Orchestrated Execution — ✅ PASS

This plan is produced by the `speckit.plan` agent. Subsequent phases (`speckit.tasks`, `speckit.implement`) will be handled by their respective agents with well-defined inputs/outputs.

### IV. Test Optionality with Clarity — ✅ PASS (Tests INCLUDED)

Tests are included because the command parser has existing comprehensive tests (`registry.test.ts`, `help.test.ts`, `useCommands.test.tsx`) and the new alias must be verified against all case/whitespace variants. Adding test cases for `#help` follows existing patterns.

### V. Simplicity and DRY — ✅ PASS

The implementation adds a single conditional check in `parseCommand()` (reusing the existing `help` alias pattern) and a minor annotation in the help handler. No new abstractions, no new files, no new patterns. Maximum simplicity.

**Gate Result: ✅ ALL GATES PASS — Proceed to Phase 0**

### Post-Phase 1 Re-check — ✅ ALL GATES STILL PASS

Design artifacts confirm: no new entities, no backend changes, no new dependencies, no complexity violations. The feature is a 2-line code change with test coverage.

## Project Structure

### Documentation (this feature)

```text
specs/033-chat-help-command/
├── plan.md              # This file
├── research.md          # Phase 0: Command alias patterns and edge cases
├── data-model.md        # Phase 1: No new entities — documents existing state only
├── quickstart.md        # Phase 1: Step-by-step implementation guide
├── contracts/           # Phase 1: Component contract changes
│   └── components.md
└── tasks.md             # Phase 2 output (NOT created by speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   └── lib/
│       └── commands/
│           ├── registry.ts          # MODIFY: Add #help alias in parseCommand()
│           ├── registry.test.ts     # MODIFY: Add #help test cases
│           └── handlers/
│               ├── help.ts          # MODIFY: Annotate help output with #help alias
│               └── help.test.ts     # MODIFY: Add #help annotation test
└── (no other files affected)
```

**Structure Decision**: Web application — frontend-only change. All modifications are within `frontend/src/lib/commands/`, the existing command system module. No structural changes.

## Complexity Tracking

> No constitution violations — this section is intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
