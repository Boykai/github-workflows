# Implementation Plan: Add File Upload and Voice Input Support to App Chat Experience

**Branch**: `018-chat-upload-voice` | **Date**: 2026-03-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/018-chat-upload-voice/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Enhance the existing chat interface with two new input modalities: file uploads (with drag-and-drop, clipboard paste, inline previews, and client-side validation) and voice input (via Web Speech API with real-time transcription). The backend gains a multipart file upload endpoint returning file reference IDs that attach to chat messages. The frontend ChatInterface component is extended with attachment and microphone toolbar buttons, a file preview area, and recording state indicators. All new controls are fully keyboard-navigable and screen-reader accessible.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI ≥0.109.0, React 18.3.1, @tanstack/react-query 5.17.0, Tailwind CSS 3.4.19, lucide-react (icons), python-multipart ≥0.0.6 (already installed)
**Storage**: In-memory (current MVP pattern) with local filesystem for uploaded files; no external object store required at this stage
**Testing**: pytest (backend), vitest (frontend), playwright (e2e)
**Target Platform**: Modern browsers (last 2 versions of Chrome, Firefox, Safari, Edge), desktop and mobile web
**Project Type**: Web application (frontend + backend)
**Performance Goals**: File validation feedback <1s; file upload for <5MB completes <30s on standard connection; voice transcription round-trip <60s for ≤50 words
**Constraints**: Max 25MB per file, max 10 files per message, supported types: JPG/PNG/GIF/WEBP/PDF/DOCX/TXT
**Scale/Scope**: Single chat interface enhancement; ~8 new frontend components/hooks, ~3 new backend endpoints, ~2 new models

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First Development** | ✅ PASS | `spec.md` exists with 5 prioritized user stories (P1–P3), Given-When-Then scenarios, edge cases, and clear scope |
| **II. Template-Driven Workflow** | ✅ PASS | Plan follows canonical `plan-template.md`; spec follows `spec-template.md` |
| **III. Agent-Orchestrated Execution** | ✅ PASS | This plan is produced by the `speckit.plan` agent; outputs hand off to `speckit.tasks` |
| **IV. Test Optionality with Clarity** | ✅ PASS | Tests are not explicitly mandated in the spec; will be included only if requested during task generation |
| **V. Simplicity and DRY** | ✅ PASS | Design favors browser-native APIs (Web Speech API, native file input) over third-party libraries; in-memory storage follows existing MVP pattern; no premature abstractions |

**Gate Result**: ✅ ALL PASS — Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/018-chat-upload-voice/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── api.yaml         # OpenAPI 3.0 contract for file upload endpoints
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   └── chat.py              # Extended: file upload + voice endpoints
│   ├── models/
│   │   └── chat.py              # Extended: FileAttachment, VoiceRecording models
│   └── services/
│       └── file_upload.py       # New: file validation, storage, reference management
└── tests/
    └── api/
        └── test_chat.py         # Extended: file upload + voice endpoint tests

frontend/
├── src/
│   ├── components/
│   │   └── chat/
│   │       ├── ChatInterface.tsx    # Extended: toolbar with attachment + mic buttons
│   │       ├── FileUploadButton.tsx # New: paperclip button + hidden file input
│   │       ├── FilePreviewArea.tsx  # New: thumbnail/chip previews with dismiss
│   │       ├── FilePreviewItem.tsx  # New: single file preview (image thumb or file chip)
│   │       ├── VoiceInputButton.tsx # New: mic button with recording state indicator
│   │       ├── DragDropOverlay.tsx  # New: visual feedback for drag-and-drop
│   │       └── RecordingIndicator.tsx # New: animated waveform/pulse during recording
│   ├── hooks/
│   │   ├── useFileUpload.ts     # New: file selection, validation, upload state
│   │   ├── useVoiceInput.ts     # New: Web Speech API wrapper, recording state
│   │   └── useDragDrop.ts       # New: drag-and-drop event handling
│   └── services/
│       └── api.ts               # Extended: file upload API calls (multipart/form-data)
└── tests/
    └── components/
        └── chat/                # Extended: tests for new components
```

**Structure Decision**: Web application (Option 2) — matches existing `backend/` + `frontend/` layout. New files integrate into existing directory structure; no new top-level directories needed.

## Complexity Tracking

> No constitution violations detected — this section is intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |

## Constitution Check — Post-Design Re-evaluation

*Re-check after Phase 1 design artifacts are complete.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First Development** | ✅ PASS | All design artifacts trace directly to spec requirements (FR-001 through FR-017) |
| **II. Template-Driven Workflow** | ✅ PASS | plan.md, research.md, data-model.md, contracts/api.yaml, quickstart.md all follow canonical structure |
| **III. Agent-Orchestrated Execution** | ✅ PASS | Phase 0 and Phase 1 complete; ready for handoff to `speckit.tasks` for Phase 2 |
| **IV. Test Optionality with Clarity** | ✅ PASS | Tests not mandated in spec; quickstart.md includes validation checklist for manual verification |
| **V. Simplicity and DRY** | ✅ PASS | All decisions favor browser-native APIs over third-party libraries; in-memory storage pattern consistent with existing MVP; no new external dependencies required |

**Post-Design Gate Result**: ✅ ALL PASS — Ready for Phase 2 (task generation via `speckit.tasks`).
