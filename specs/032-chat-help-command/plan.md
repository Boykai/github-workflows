# Implementation Plan: Add #help Command to User Chat for In-Chat Command Reference

**Branch**: `032-chat-help-command` | **Date**: 2026-03-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from parent issue [#2785](https://github.com/Boykai/github-workflows/issues/2785)

## Summary

Add `#help` as a recognized alias for the existing `/help` chat command in the Solune UI. When a user types `#help` (case-insensitive, whitespace-tolerant) in the chat input, the system responds with the same inline, ephemeral help message listing all available commands. The implementation requires modifying only the command parser (`parseCommand()`) in `registry.ts` to recognize `#help` as an exact-match alias and updating the help command's syntax field to reflect the alias in the auto-generated help output. No backend changes, no new dependencies, no new files.

## Technical Context

**Language/Version**: TypeScript ~5.9 (frontend-only change)
**Primary Dependencies**: React 19.2, existing command system (`frontend/src/lib/commands/`)
**Storage**: N/A — ephemeral local messages only; no persistence changes
**Testing**: Vitest 4 + existing command registry tests
**Target Platform**: Desktop and mobile browsers (responsive web application)
**Project Type**: Web application (frontend-only change)
**Performance Goals**: Zero performance impact — single string comparison added to existing parsing function
**Constraints**: Must not break existing `/help` or `help` alias behavior; must not generalize `#` as a command prefix
**Scale/Scope**: 1 file modified, 2 small changes (one condition, one string literal)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | Feature specified in parent issue #2785 with user story, functional requirements (FR-001–FR-008), UI/UX description, and technical notes |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (specify → plan → tasks → implement) |
| **IV. Test Optionality** | ✅ PASS | Tests not explicitly mandated in spec; existing command registry tests should continue to pass |
| **V. Simplicity/DRY** | ✅ PASS | Minimal change — one condition added to existing function, one string updated; no new abstractions, no new dependencies, no new files |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts (research.md, data-model.md, contracts/, quickstart.md) trace back to spec FRs |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/components.md, quickstart.md all follow template structure |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 |
| **IV. Test Optionality** | ✅ PASS | Existing registry tests cover `parseCommand()`; adding test cases for `#help` input recommended but not required |
| **V. Simplicity/DRY** | ✅ PASS | Single condition addition reuses existing alias pattern; syntax string update leverages auto-generation in `helpHandler` — zero code duplication |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/032-chat-help-command/
├── plan.md              # This file
├── research.md          # Phase 0: Research decisions (R1–R4)
├── data-model.md        # Phase 1: Existing type documentation, no new entities
├── quickstart.md        # Phase 1: Developer guide for the two-line change
├── contracts/
│   └── components.md    # Phase 1: Component interface changes (registry.ts only)
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── lib/
│   │   └── commands/
│   │       ├── registry.ts          # MODIFIED: Add #help alias in parseCommand(), update syntax string
│   │       ├── handlers/
│   │       │   └── help.ts          # UNCHANGED: Auto-generates from registry
│   │       └── types.ts             # UNCHANGED: No type changes
│   ├── hooks/
│   │   ├── useChat.ts               # UNCHANGED: Local message injection already works
│   │   └── useCommands.ts           # UNCHANGED: Wraps registry
│   └── components/
│       └── chat/
│           ├── ChatInterface.tsx     # UNCHANGED: Renders system messages
│           └── SystemMessage.tsx     # UNCHANGED: Distinct styling for command responses
```

**Structure Decision**: Web application (frontend-only). This feature modifies a single file (`registry.ts`) in the existing frontend command system. No new files, no backend changes, no database changes.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| Exact-match alias (not general `#` prefix) | Only `#help` is requested; generalizing `#` would conflict with Markdown heading syntax and introduce unspecified behavior | General `#` prefix support (rejected: scope creep, Markdown conflict) |
| Updated syntax string instead of separate registry entry | Avoids duplicate entry in help output; leverages existing auto-generation | Register `#help` as separate command (rejected: duplicate in help list) |
