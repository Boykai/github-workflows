# Implementation Plan: Add #help Command to User Chat for In-Chat Command Reference

**Branch**: `032-chat-help-command` | **Date**: 2026-03-09 | **Spec**: Parent Issue [#2785](https://github.com/Boykai/github-workflows/issues/2785)
**Input**: Feature specification from parent issue #2785 — Add #help Command to User Chat for In-Chat Command Reference

## Summary

Add `#help` as a recognized chat command alias that triggers the existing help system. When a user types `#help` (case-insensitive, whitespace-tolerant) in any chat input, the system intercepts it before broadcast, executes the help handler locally, and injects an ephemeral system message listing all available commands. The response is visible only to the invoking user and does not persist to the backend. This leverages the existing command registry, `parseCommand` function, `helpHandler`, and `SystemMessage` component — requiring only a 3-line alias addition in the parser and a minor output format update in the help handler.

## Technical Context

**Language/Version**: TypeScript ~5.9 (frontend-only feature)
**Primary Dependencies**: React 19.2, Tailwind CSS v4.2 (no new dependencies)
**Storage**: N/A — ephemeral local messages only; no database or localStorage changes
**Testing**: Vitest 4 (existing test infrastructure for command system)
**Target Platform**: Desktop and mobile browsers (all viewports)
**Project Type**: Web application (frontend-only changes)
**Performance Goals**: Zero performance impact — alias check is a single string comparison in `parseCommand`
**Constraints**: Must not break existing `/help` command, `help` keyword alias, Markdown heading detection (`# Heading`), or any other chat functionality
**Scale/Scope**: 2 files modified (`registry.ts`, `help.ts`), 2 test files updated, 0 new files, 0 backend changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | Parent issue #2785 provides complete user story, UI/UX description, 8 functional requirements, and technical notes |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (plan → tasks → implement) |
| **IV. Test Optionality** | ✅ PASS | Existing command system has tests (`registry.test.ts`, `help.test.ts`); new tests added to cover `#help` alias — consistent with existing test coverage |
| **V. Simplicity/DRY** | ✅ PASS | 3-line alias in `parseCommand` reuses entire existing command infrastructure; no new abstractions, no new dependencies, no new components |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace back to FR-001 through FR-008 from the parent issue |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow template structure |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 |
| **IV. Test Optionality** | ✅ PASS | Tests extend existing suites — no new test infrastructure; coverage proportional to change size |
| **V. Simplicity/DRY** | ✅ PASS | Alias pattern identical to existing `help` keyword alias; help output updated in-place rather than creating a new command or component |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/032-chat-help-command/
├── plan.md              # This file
├── research.md          # Phase 0: Research decisions (R1–R4)
├── data-model.md        # Phase 1: Affected data structures and parsing rules
├── quickstart.md        # Phase 1: Developer implementation guide
├── contracts/
│   └── components.md    # Phase 1: Component interface changes and test contracts
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── lib/
│   │   └── commands/
│   │       ├── registry.ts          # MODIFIED: Add #help alias in parseCommand
│   │       ├── registry.test.ts     # MODIFIED: Add #help alias tests
│   │       └── handlers/
│   │           ├── help.ts          # MODIFIED: Mention #help alias in help output
│   │           └── help.test.ts     # MODIFIED: Add #help mention test
│   ├── hooks/
│   │   └── useChat.ts              # UNCHANGED: Existing command path handles #help automatically
│   └── components/
│       └── chat/
│           ├── ChatInterface.tsx    # UNCHANGED: Uses isCommand() which delegates to parseCommand
│           └── SystemMessage.tsx    # UNCHANGED: Renders help response with existing styling
```

**Structure Decision**: Web application (frontend-only). This feature modifies 2 source files and 2 test files in the existing command system. No new files, no new components, no backend changes. The `#help` alias is handled entirely within the `parseCommand` function, and the entire downstream pipeline (command execution, local message injection, system message rendering) works without modification.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| Exact-match alias (not general `#` prefix) | Only `#help` is required; general `#` prefix would break Markdown heading detection | General `#` command prefix (rejected: breaks `# Heading`, over-engineering) |
| Alias in `parseCommand` (not separate command registration) | Single source of truth — one `help` command; no duplicate autocomplete/help entries | Separate `#help` command registration (rejected: duplicate entries, user confusion) |
| Plain text help output (not Markdown/HTML) | `SystemMessage` uses `whitespace-pre-wrap`; no Markdown parser available; consistent with existing output | Markdown rendering (rejected: requires new parser), Rich HTML (rejected: security concern with `dangerouslySetInnerHTML`) |
| In-line `(or #help)` annotation | Minimal change to help handler; discoverable without cluttering the command list | Separate alias section in help output (rejected: over-formatting for one alias) |
