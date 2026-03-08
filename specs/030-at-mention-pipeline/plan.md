# Implementation Plan: @ Mention in Chat to Select Agent Pipeline Configuration

**Branch**: `030-at-mention-pipeline` | **Date**: 2026-03-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/030-at-mention-pipeline/spec.md`

## Summary

Add @mention autocomplete to the chat input that lets users type "@" to discover and select saved Agent Pipeline configurations by name. The selected pipeline is inserted as a visually distinct token (chip) inline in the textarea-replacement input, and its unique identifier is sent alongside the chat message for pipeline-aware GitHub Issue creation. The frontend extends the existing `ChatInterface` component with a new `MentionAutocomplete` dropdown (modeled on the existing `CommandAutocomplete` for `/` commands), a `MentionToken` inline chip, and a `PipelineIndicator` near the submit button. The backend `ChatMessageRequest` gains an optional `pipeline_id` field so the existing chat→issue flow routes through the referenced pipeline. No new backend tables or services are required — the feature builds on the existing `pipelinesApi.list()` endpoint and `PipelineConfigSummary` type.

## Technical Context

**Language/Version**: TypeScript ~5.9 (frontend), Python 3.13 (backend)
**Primary Dependencies**: React 19.2, TanStack Query v5.90, Tailwind CSS v4, lucide-react 0.577 (frontend); FastAPI 0.135, Pydantic v2.12 (backend)
**Storage**: N/A — no new tables; reads from existing `pipeline_configs` table via `pipelinesApi.list()`
**Testing**: Vitest 4 + Testing Library (frontend), pytest + pytest-asyncio (backend)
**Target Platform**: Desktop browsers, 1024px minimum viewport width; Linux server (Docker)
**Project Type**: Web application (frontend/ + backend/)
**Performance Goals**: Autocomplete appears < 300ms after typing "@" (SC-001, SC-002); pipeline list cached via TanStack Query (SC-007)
**Constraints**: No new UI libraries; must not break existing slash-command autocomplete or chat submission flow; textarea must be replaced with a content-editable or hybrid input to support inline tokens
**Scale/Scope**: ~4 new frontend components, ~1 new hook, 1 modified backend model, 1 modified backend endpoint; up to 100 saved pipelines in autocomplete (SC-007)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 5 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, 17 functional requirements, 7 success criteria, 7 edge cases |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (specify → plan → tasks → implement) |
| **IV. Test Optionality** | ✅ PASS | Tests not explicitly mandated in spec; existing tests should continue to pass |
| **V. Simplicity/DRY** | ✅ PASS | Reuses existing `CommandAutocomplete` pattern, existing `pipelinesApi`, existing `PipelineConfigSummary` type; replaces textarea with minimal hybrid input rather than introducing a full rich-text editor |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace back to spec FRs (FR-001–FR-017) |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow template structure |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 |
| **IV. Test Optionality** | ✅ PASS | No additional tests mandated; existing tests unaffected |
| **V. Simplicity/DRY** | ✅ PASS | Reuses `CommandAutocomplete` ARIA pattern, existing pipeline list API and types, existing chat submission flow. New `MentionAutocomplete` is the only structurally new component; `MentionToken` is a styled span. No rich-text editor library added. |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/030-at-mention-pipeline/
├── plan.md              # This file
├── research.md          # Phase 0: Research decisions (R1–R6)
├── data-model.md        # Phase 1: Entity definitions, types, state machines
├── quickstart.md        # Phase 1: Developer onboarding guide
├── contracts/
│   ├── api.md           # Phase 1: Backend API contract changes
│   └── components.md    # Phase 1: Component interface contracts
├── checklists/
│   └── requirements.md  # Specification quality checklist (complete)
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   └── chat.py                      # MODIFIED: Accept optional pipeline_id in ChatMessageRequest
│   └── models/
│       └── chat.py                      # MODIFIED: Add pipeline_id field to ChatMessageRequest

frontend/
├── src/
│   ├── components/
│   │   └── chat/
│   │       ├── ChatInterface.tsx        # MODIFIED: Replace textarea with MentionInput; wire MentionAutocomplete
│   │       ├── MentionAutocomplete.tsx  # NEW: Autocomplete dropdown for @mention pipeline selection
│   │       ├── MentionInput.tsx         # NEW: Hybrid input supporting plain text + inline mention tokens
│   │       ├── MentionToken.tsx         # NEW: Styled chip/tag for resolved @mention inline in input
│   │       └── PipelineIndicator.tsx    # NEW: "Using pipeline: [name]" indicator near submit button
│   ├── hooks/
│   │   └── useMentionAutocomplete.ts    # NEW: Autocomplete state, filtering, keyboard nav, token management
│   ├── services/
│   │   └── api.ts                       # UNCHANGED: Already has pipelinesApi.list()
│   └── types/
│       └── index.ts                     # MODIFIED: Add MentionToken type, extend ChatMessageRequest
```

**Structure Decision**: Web application (frontend/ + backend/). The repo already has `frontend/` and `backend/` directories. New components are added under the existing `frontend/src/components/chat/` directory since they are chat-specific. A new `useMentionAutocomplete` hook encapsulates mention logic. Backend changes are minimal — only the `ChatMessageRequest` model gains an optional field.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| Replace textarea with hybrid `MentionInput` | Inline tokens (FR-004) require rendering styled chips within the input area; a plain textarea cannot render HTML inline | Using `contentEditable` div (chosen approach is a thin wrapper that manages a contenteditable div, not a full rich-text editor) |
| Reuse `CommandAutocomplete` pattern | The existing slash-command autocomplete provides the ARIA structure, keyboard navigation, and positioning logic needed for @mention autocomplete | Adding a third-party mention library like Tribute.js (rejected: adds dependency, existing pattern sufficient) |
