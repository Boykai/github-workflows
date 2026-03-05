# Implementation Plan: Chat Message History Navigation with Up Arrow Key

**Branch**: `018-chat-history-navigation` | **Date**: 2026-03-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/018-chat-history-navigation/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Add chat message history navigation to the frontend chat experience. Users can press the up/down arrow keys in the chat input to cycle through previously sent messages (most recent first). A draft buffer preserves any in-progress text. History is persisted via localStorage (capped at 100 entries). Visual feedback indicates history-navigation mode, and a mobile-friendly history button provides an accessible alternative. Implementation is a new `useChatHistory` custom hook integrated into the existing `ChatInterface` component.

## Technical Context

**Language/Version**: TypeScript 5.x, React 18.3.1
**Primary Dependencies**: React 18.3, TanStack React Query 5.x, Tailwind CSS 3.4, Lucide React (icons)
**Storage**: localStorage (client-side, JSON-serialized array of strings, keyed `chat-message-history`)
**Testing**: Vitest 4.x + React Testing Library 16.x + happy-dom
**Target Platform**: Web browser (desktop + mobile)
**Project Type**: Web application (frontend + backend; this feature is frontend-only)
**Performance Goals**: History recall < 16ms per keystroke (synchronous state update); localStorage read on mount < 50ms for 100 entries
**Constraints**: Max 100 history entries (~500KB worst case); graceful degradation when localStorage unavailable (e.g., private browsing); must not interfere with multi-line cursor movement or autocomplete navigation
**Scale/Scope**: Single chat context per page; no server-side persistence; frontend-only change touching ~3 files (1 new hook, 1 modified component, 1 new test file)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| **I. Specification-First** | ✅ PASS | `spec.md` exists with 6 prioritized user stories (P1–P3), Given-When-Then scenarios, independent test criteria, and explicit scope boundaries |
| **II. Template-Driven Workflow** | ✅ PASS | All artifacts follow canonical templates; plan.md follows plan-template.md structure |
| **III. Agent-Orchestrated Execution** | ✅ PASS | Single-responsibility: speckit.plan generates plan artifacts only; tasks.md deferred to speckit.tasks |
| **IV. Test Optionality** | ✅ PASS | Tests not explicitly mandated in spec; however, the custom hook `useChatHistory` is a strong candidate for unit tests. Tests recommended but optional per constitution |
| **V. Simplicity and DRY** | ✅ PASS | Single custom hook (`useChatHistory`) encapsulates all logic; no premature abstraction; follows existing codebase patterns (direct localStorage with try-catch, similar to ChatPopup.tsx) |

**Gate Result**: ✅ ALL PASS — Proceeding to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/018-chat-history-navigation/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── useChatHistory-api.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── components/
│   │   └── chat/
│   │       └── ChatInterface.tsx    # Modified: integrate useChatHistory hook
│   └── hooks/
│       └── useChatHistory.ts        # New: chat history navigation hook
└── src/
    └── hooks/
        └── useChatHistory.test.ts   # New: unit tests for the hook (optional)
```

**Structure Decision**: Web application structure (Option 2). This feature is frontend-only, modifying the existing `ChatInterface.tsx` component and adding a new `useChatHistory` custom hook in `frontend/src/hooks/`. No backend changes required. Follows the established pattern of co-located hooks in `frontend/src/hooks/`.

## Complexity Tracking

> No constitution violations detected. No complexity justifications needed.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |

## Constitution Re-Check (Post Phase 1 Design)

*Re-evaluated after completing research.md, data-model.md, contracts/, and quickstart.md.*

| Principle | Status | Post-Design Evidence |
|-----------|--------|----------------------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace directly to spec.md user stories and FRs |
| **II. Template-Driven Workflow** | ✅ PASS | plan.md follows plan-template.md; all Phase 0/1 artifacts generated per template |
| **III. Agent-Orchestrated Execution** | ✅ PASS | speckit.plan produced plan.md, research.md, data-model.md, contracts/, quickstart.md; tasks.md deferred to speckit.tasks |
| **IV. Test Optionality** | ✅ PASS | Tests marked optional in quickstart.md; hook is test-friendly but not mandated |
| **V. Simplicity and DRY** | ✅ PASS | Single hook (`useChatHistory`) with no new dependencies; direct localStorage pattern matches ChatPopup.tsx; no premature abstractions |

**Gate Result**: ✅ ALL PASS — Design phase complete. Ready for Phase 2 (tasks generation via speckit.tasks).

## Generated Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| Implementation Plan | `specs/018-chat-history-navigation/plan.md` | ✅ Complete |
| Research | `specs/018-chat-history-navigation/research.md` | ✅ Complete |
| Data Model | `specs/018-chat-history-navigation/data-model.md` | ✅ Complete |
| Hook API Contract | `specs/018-chat-history-navigation/contracts/useChatHistory-api.md` | ✅ Complete |
| Quickstart Guide | `specs/018-chat-history-navigation/quickstart.md` | ✅ Complete |
| Agent Context | `.github/agents/copilot-instructions.md` | ✅ Updated |
