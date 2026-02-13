# Implementation Plan: Document Upload in Chat

**Branch**: `001-document-upload` | **Date**: 2026-02-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-document-upload/spec.md`

## Summary

A document upload feature for the GitHub Projects chat interface enabling users to share files (PDF, DOCX, TXT, XLSX, PPTX) during conversations. Users click a paperclip icon to select files, see upload progress, and view uploaded documents as downloadable message bubbles in chat. Files are stored securely with authentication-protected download links.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.x (frontend)  
**Primary Dependencies**:
- Backend: FastAPI, httpx, python-jose (JWT), pydantic, python-multipart (for file uploads)
- Frontend: React 18+, Vite, TanStack Query
**Storage**: Local filesystem (development), cloud storage for production (S3/Azure Blob/GCS)  
**Testing**: pytest (backend), Vitest (frontend), Playwright (E2E)  
**Target Platform**: Linux server (Docker), Modern web browsers  
**Project Type**: Web application (frontend + backend)  
**Performance Goals**: Upload initiation <1s, progress updates <1s latency, file processing <5s for 25MB files  
**Constraints**: 25MB max file size, 5 supported file types only, authenticated access required  
**Scale/Scope**: Support for individual users and small teams (50+ users), hundreds of files per project

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Initial Check (Pre-Phase 0)

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Specification-First | ✅ PASS | Complete spec.md with 3 prioritized user stories (P1, P1, P2), Given-When-Then scenarios, clear scope boundaries |
| II. Template-Driven Workflow | ✅ PASS | Following canonical plan-template.md structure from .specify/templates |
| III. Agent-Orchestrated Execution | ✅ PASS | Clear phase boundaries: specify → plan (this) → tasks → implement |
| IV. Test Optionality | ✅ PASS | Tests not explicitly requested in spec - optional for this feature |
| V. Simplicity and DRY | ✅ PASS | Simple architecture: FastAPI multipart upload + React file input, minimal abstractions, local storage for MVP |

### Post-Design Check (After Phase 1)

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Specification-First | ✅ PASS | All design artifacts (data-model, contracts, quickstart) derived directly from spec.md requirements |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow standard formats: data-model (entities + relationships), OpenAPI contract, quickstart guide |
| III. Agent-Orchestrated Execution | ✅ PASS | Phase 0 research completed, Phase 1 design completed, ready for Phase 2 task generation |
| IV. Test Optionality | ✅ PASS | Testing infrastructure documented in quickstart.md but not mandated - remains optional |
| V. Simplicity and DRY | ✅ PASS | Design maintains simplicity: 3 entities, 5 endpoints, storage abstraction for future cloud migration, no premature abstractions |

**Design Complexity Assessment**:
- Total new endpoints: 5 (upload, get metadata, request download URL, download, list documents)
- Total new entities: 3 (Document, DocumentMessage, DownloadToken)
- New backend services: 3 (file_storage.py, file_validator.py, download_tokens.py)
- New frontend components: 2 (DocumentUpload.tsx, DocumentMessage.tsx)
- New frontend hooks: 1 (useFileUpload.ts)
- Dependencies added: 2 (aiofiles, python-magic)

**Justification**: All complexity is essential for meeting functional requirements. No violations detected.

## Project Structure

### Documentation (this feature)

```text
specs/001-document-upload/
├── plan.md              # This file
├── research.md          # Phase 0 output (file storage options, multipart upload patterns)
├── data-model.md        # Phase 1 output (Document, DocumentMessage entities)
├── quickstart.md        # Phase 1 output (setup and testing guide)
├── contracts/           # Phase 1 output
│   └── openapi.yaml     # API contract for upload/download endpoints
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── main.py                     # FastAPI application entry (existing)
│   ├── config.py                   # Environment configuration (existing)
│   ├── models/
│   │   ├── __init__.py             # (existing)
│   │   ├── user.py                 # (existing)
│   │   ├── project.py              # (existing)
│   │   ├── document.py             # NEW: Document model
│   │   └── chat.py                 # (existing) - extend for document messages
│   ├── services/
│   │   ├── __init__.py             # (existing)
│   │   ├── github_auth.py          # (existing) - use for auth validation
│   │   ├── file_storage.py         # NEW: File upload/download/storage service
│   │   └── file_validator.py      # NEW: File type and size validation
│   ├── api/
│   │   ├── __init__.py             # (existing)
│   │   ├── auth.py                 # (existing) - use for authentication
│   │   ├── projects.py             # (existing)
│   │   ├── chat.py                 # (existing) - extend for document messages
│   │   └── documents.py            # NEW: Document upload/download endpoints
│   └── storage/                    # NEW: Storage directory for uploaded files
└── tests/
    ├── unit/
    │   └── test_file_validator.py  # NEW: Validator tests
    └── integration/
        └── test_document_api.py    # NEW: Upload/download endpoint tests

frontend/
├── src/
│   ├── main.tsx                    # (existing)
│   ├── App.tsx                     # (existing)
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatInterface.tsx   # (existing) - extend with upload button
│   │   │   ├── MessageBubble.tsx   # (existing) - extend for document messages
│   │   │   ├── DocumentUpload.tsx  # NEW: File picker and upload component
│   │   │   └── DocumentMessage.tsx # NEW: Document message display
│   │   ├── sidebar/                # (existing)
│   │   └── auth/                   # (existing)
│   ├── hooks/
│   │   ├── useAuth.ts              # (existing)
│   │   ├── useChat.ts              # (existing) - extend for document messages
│   │   └── useFileUpload.ts        # NEW: File upload hook with progress
│   ├── services/
│   │   └── api.ts                  # (existing) - extend with document endpoints
│   ├── types/
│   │   └── index.ts                # (existing) - add Document types
│   └── utils/
│       └── fileUtils.ts            # NEW: File validation and formatting utilities
└── tests/
    ├── unit/
    │   └── useFileUpload.test.tsx  # NEW: File upload hook tests
    └── e2e/
        └── document-upload.spec.ts # NEW: E2E document upload tests
```

**Structure Decision**: Web application structure (backend/ + frontend/) selected because the feature extends existing chat interface. Backend handles multipart file uploads via FastAPI, stores files securely, and serves authenticated downloads. Frontend adds UI components to existing chat interface. Clear separation already established in the project.

## Complexity Tracking

> No violations detected - Constitution Check passed for all principles.

---

## Phase 0: Research & Technology Selection

**Status**: ✅ COMPLETE

### Research Decisions Summary

1. **File Storage Strategy**: Local filesystem (MVP) with cloud migration path
2. **Multipart Upload**: Standard multipart/form-data with streaming (no resumable needed for 25MB)
3. **File Type Validation**: Multi-layer (extension + magic numbers + light format check)
4. **Progress Tracking**: XMLHttpRequest with React hook (only standard approach for upload progress)
5. **Download Security**: Session-tied temporary download tokens (aligns with existing auth)

**Full details**: See [research.md](research.md)

---

## Phase 1: Design & Contracts

**Status**: ✅ COMPLETE

### Data Model

✅ Generated in [data-model.md](data-model.md)
- Document entity (uploaded file metadata)
- DocumentMessage entity (chat message with document reference)
- DownloadToken entity (secure time-limited access)

### API Contracts

✅ Generated in [contracts/openapi.yaml](contracts/openapi.yaml)
- POST `/documents/upload` - Upload document
- GET `/documents/{id}` - Get metadata
- POST `/documents/{id}/download-url` - Request download token
- GET `/downloads?token=xxx` - Download file
- GET `/projects/{id}/documents` - List project documents

### Quickstart Guide

✅ Generated in [quickstart.md](quickstart.md)
- Setup instructions (backend + frontend)
- API testing examples (cURL)
- Manual testing steps
- Automated testing commands
- Troubleshooting guide

### Agent Context Update

Agent context update is typically performed during implementation phase. For this planning phase, the following technologies have been identified and documented:

**New Technologies**:
- `aiofiles` - Async file I/O for streaming uploads
- `python-magic` - MIME type detection for security
- XMLHttpRequest pattern for upload progress in React

**Integration Points**:
- Extends existing FastAPI backend with document upload endpoints
- Integrates with existing session-based authentication
- Adds document message type to existing chat interface
- Uses existing TanStack Query patterns for mutations

---

## Phase 2: Task Decomposition

**Status**: PENDING (generated by /speckit.tasks command after Phase 1)

**Note**: This planning workflow ends here. The next step is to run `/speckit.tasks` command to generate `tasks.md` with actionable, dependency-ordered implementation tasks.

Tasks will be organized by user story:
- Story 1: Basic Document Upload (P1)
- Story 2: Upload Progress and Error Handling (P1)
- Story 3: Secure Document Storage and Access (P2)

Each task will include:
- Description
- Acceptance criteria
- Dependencies
- Affected files
- Test requirements (if applicable)
