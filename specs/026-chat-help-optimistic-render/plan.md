# Implementation Plan: Fix #help Command Auto-Repeat Bug & Add Optimistic Message Rendering in Chat UI

**Branch**: `026-chat-help-optimistic-render` | **Date**: 2026-03-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/026-chat-help-optimistic-render/spec.md`

## Summary

Fix a critical bug where the `#help` command (and other hash/slash commands) auto-repeats on subsequent messages due to stale command state surviving dispatch, and add optimistic message rendering so user-sent messages appear immediately in the chat UI before the agent responds. The approach modifies only the frontend chat state management layer — specifically `useChat.ts`, `ChatInterface.tsx`, and `MessageBubble.tsx` — to (1) ensure command state is fully purged after dispatch, (2) insert an optimistic user message into the local message list before calling the API, (3) show a thinking indicator while the agent processes, and (4) handle message send failures with visible error states and retry. No backend changes are required.

## Technical Context

**Language/Version**: TypeScript ~5.9, React 19.2, Vite 7.3
**Primary Dependencies**: TanStack Query 5.90, Tailwind CSS v4, lucide-react 0.577
**Storage**: N/A (local React state only — no persistence for pending messages)
**Testing**: Vitest 4 + Testing Library + happy-dom (existing `useChat.test.tsx`, `MessageBubble.test.tsx`, `CommandAutocomplete.test.tsx`)
**Target Platform**: Desktop and mobile browsers (chat popup responsive, min 300px width)
**Project Type**: Web application (frontend/ + backend/)
**Performance Goals**: Optimistic message appears within 100ms of send (SC-002), thinking indicator within 200ms (SC-003)
**Constraints**: No new npm dependencies, no backend API changes, no layout shifts when replacing thinking indicator with response
**Scale/Scope**: ~4 modified files, ~2 new test blocks, 0 new files (changes are in-place)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 5 prioritized user stories, acceptance scenarios, edge cases, and scope exclusions |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (specify → plan) |
| **IV. Test Optionality** | ✅ PASS | FR-016/FR-017 request regression tests; existing test infrastructure (useChat.test.tsx) covers command interception; new tests extend it |
| **V. Simplicity/DRY** | ✅ PASS | No new abstractions — changes modify existing state management in useChat.ts and existing UI rendering in ChatInterface.tsx. No new libraries. |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace back to spec FRs (FR-001 through FR-017) |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow template structure |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 |
| **IV. Test Optionality** | ✅ PASS | Regression tests specified in FR-016/FR-017 are scoped to useChat.test.tsx extensions |
| **V. Simplicity/DRY** | ✅ PASS | Optimistic rendering uses existing `localMessages` state + a `status` field on ChatMessage. Thinking indicator is a CSS-only animated element (already exists for `isSending`). No new state management library or patterns. |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/026-chat-help-optimistic-render/
├── plan.md              # This file
├── research.md          # Phase 0: 6 research items (R1–R6)
├── data-model.md        # Phase 1: Type changes, state shapes, component props
├── quickstart.md        # Phase 1: Developer onboarding guide
├── contracts/
│   └── components.md    # Phase 1: Modified component interface contracts
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── types/index.ts                    # MODIFIED: Add 'status' field to ChatMessage
│   ├── hooks/
│   │   ├── useChat.ts                    # MODIFIED: Optimistic rendering, command state cleanup, failure handling
│   │   └── useChat.test.tsx              # MODIFIED: Add regression tests for command state leaking + optimistic rendering
│   ├── components/chat/
│   │   ├── ChatInterface.tsx             # MODIFIED: Render optimistic messages, thinking indicator, failed message styling + retry
│   │   └── MessageBubble.tsx             # MODIFIED: Visual treatment for pending/failed message states
│   └── lib/commands/
│       ├── types.ts                      # UNCHANGED: CommandResult already has clearInput
│       └── registry.ts                   # UNCHANGED: No structural changes needed
│
backend/                                  # NO CHANGES
```

**Structure Decision**: Web application (Option 2). All changes are within `frontend/src/`. No new files are created — all modifications are in-place to existing files. The `ChatMessage` type gains an optional `status` field, `useChat.ts` gains optimistic message logic, and the UI components gain conditional styling for message states.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

*Table intentionally left empty — all design decisions favor simplicity per Principle V.*
