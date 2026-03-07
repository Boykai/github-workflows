# Implementation Plan: Chat UX Enhancements — AI Enhance Toggle, Markdown Input Support, File Upload, and Voice Chat

**Branch**: `028-chat-ux-enhancements` | **Date**: 2026-03-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/028-chat-ux-enhancements/spec.md`

## Summary

Enhance the app chat interface with four capabilities: (1) an "AI Enhance" toggle that lets users choose between AI-rewritten or verbatim issue descriptions while always generating metadata, (2) Markdown-safe input parsing that restricts command detection to explicit `/`-prefixed tokens, (3) file upload with preview chips and GitHub Issue attachment via the REST API, and (4) voice-to-text input using the Web Speech API with graceful fallback. The frontend extends `ChatInterface.tsx` with a new `ChatToolbar` component housing the toggle, file upload button, and microphone button, following the existing `AddAgentPopover` styling pattern. The backend adds a `/api/v1/chat/upload` endpoint for file handling and modifies the chat message processing pipeline to conditionally skip AI description rewriting based on the `ai_enhance` flag. Command parsing in `lib/commands/registry.ts` is updated to only match `/`-prefixed commands, resolving Markdown conflicts.

## Technical Context

**Language/Version**: TypeScript ~5.9 (frontend), Python 3.13 (backend)
**Primary Dependencies**: React 19.2, TanStack Query v5.90, Tailwind CSS v4, lucide-react 0.577 (frontend); FastAPI 0.135, aiosqlite 0.22, Pydantic v2.12, python-multipart 0.0.22 (backend)
**Storage**: SQLite with WAL mode (aiosqlite) — existing `chat_messages`, `chat_proposals`, `chat_recommendations` tables; localStorage for toggle preference persistence
**Testing**: Vitest 4 + Testing Library (frontend), pytest + pytest-asyncio (backend)
**Target Platform**: Desktop browsers (Chrome, Firefox, Safari, Edge); Linux server (Docker)
**Project Type**: Web application (frontend/ + backend/)
**Performance Goals**: Toggle interaction < 100ms; file upload preview < 500ms; voice transcription latency < 2s; chat submission unchanged
**Constraints**: Max 10 MB per file (GitHub API limit); Web Speech API browser-dependent; no new UI library additions
**Scale/Scope**: ~5 new/modified frontend components, ~2 new hooks, 1 new backend endpoint, modifications to chat API and AI agent pipeline

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 4 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, 18 functional requirements, 11 success criteria, edge cases |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (specify → plan → tasks → implement) |
| **IV. Test Optionality** | ✅ PASS | Tests not explicitly mandated in spec; existing tests should continue to pass |
| **V. Simplicity/DRY** | ✅ PASS | Extends existing chat components and patterns; reuses lucide-react icons, TanStack Query, existing API client; command parser fix is a minimal change; no new libraries required |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace back to spec FRs (FR-001–FR-018) |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow template structure |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 |
| **IV. Test Optionality** | ✅ PASS | No additional tests mandated; existing tests unaffected |
| **V. Simplicity/DRY** | ✅ PASS | Reuses existing `ChatInterface` component, existing API patterns, existing icon library. New `ChatToolbar` is a focused single-responsibility component. Command parser change is minimal (prefix switch). File upload uses standard browser APIs + existing `python-multipart`. Voice uses native Web Speech API — no new dependencies. |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/028-chat-ux-enhancements/
├── plan.md              # This file
├── research.md          # Phase 0: Research decisions (R1–R7)
├── data-model.md        # Phase 1: Entity definitions, types, state machines
├── quickstart.md        # Phase 1: Developer onboarding guide
├── contracts/
│   ├── api.md           # Phase 1: REST API endpoint contracts
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
│   │   └── chat.py                      # MODIFIED: Add ai_enhance flag, file upload endpoint
│   ├── services/
│   │   └── ai_agent.py                  # MODIFIED: Conditional description bypass when ai_enhance=false
│   └── models/                          # Existing models — no new models needed

frontend/
├── src/
│   ├── components/
│   │   └── chat/
│   │       ├── ChatInterface.tsx        # MODIFIED: Integrate ChatToolbar, update command handling
│   │       ├── ChatToolbar.tsx          # NEW: Toolbar with AI Enhance toggle, file upload, mic
│   │       ├── FilePreviewChips.tsx     # NEW: Inline file preview chips with remove action
│   │       └── VoiceInputButton.tsx     # NEW: Microphone button with recording indicator
│   ├── hooks/
│   │   ├── useChat.ts                   # MODIFIED: Add aiEnhance state, file attachments, voice state
│   │   ├── useFileUpload.ts             # NEW: File selection, validation, upload state management
│   │   └── useVoiceInput.ts             # NEW: Web Speech API integration, transcription state
│   ├── lib/
│   │   └── commands/
│   │       └── registry.ts             # MODIFIED: Switch from '#' to '/' command prefix
│   ├── services/
│   │   └── api.ts                       # MODIFIED: Add chat file upload API method
│   └── types/
│       └── index.ts                     # MODIFIED: Add FileAttachment, VoiceInputState types
```

**Structure Decision**: Web application (frontend/ + backend/). All changes extend existing directories and components. New files are scoped to `frontend/src/components/chat/` and `frontend/src/hooks/` following the existing domain-scoped pattern. No new backend models or migrations needed — file upload is stateless (upload → get URL → embed in issue body). The command prefix change is a targeted edit in the existing `registry.ts`.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| `/`-prefix for commands (replacing `#`) | Resolves Markdown conflict by using the universally recognized slash-command pattern; eliminates false-positive command detection for all Markdown characters | Keeping `#` but requiring no space after hash (rejected: fragile heuristic, `#heading` looks like `#command`) |
| localStorage for toggle persistence | Simplest persistence mechanism; no backend storage needed; survives browser refresh within same origin | Session storage (rejected: lost on tab close), backend user preference (rejected: over-engineered for single boolean, YAGNI) |
| Web Speech API (no third-party STT) | Zero dependency, works natively in Chrome/Edge/Safari; no API key management; meets P3 priority level | Whisper API (rejected: adds backend dependency, API cost, latency; can be added later as enhancement) |
| File URL embedding in issue body | GitHub Issues API doesn't support direct file attachments programmatically; uploading to GitHub via the user-content CDN and embedding URLs is the standard pattern | Direct attachment via API (rejected: not supported by GitHub REST API for issues) |
