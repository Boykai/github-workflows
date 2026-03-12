# Implementation Plan: Attach User Chat Attachments to GitHub Parent Issue

**Branch**: `037-chat-attachment-github-issue` | **Date**: 2026-03-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/037-chat-attachment-github-issue/spec.md`

## Summary

Connect the existing file upload pipeline to the GitHub issue creation flow so that files uploaded in the chat interface are automatically embedded in the corresponding GitHub Parent Issue body. The infrastructure is ~90% complete: file upload, validation, per-file status tracking, and URL collection already work end-to-end. The remaining work is to (1) persist file URLs through the proposal/recommendation models, (2) convert file URLs to markdown format, and (3) embed them in the GitHub issue body before calling `create_issue()`. A database migration adds `file_urls` columns to `chat_proposals` and `chat_recommendations` tables. A new utility function `format_attachments_markdown()` centralizes the URL-to-markdown conversion used by both confirmation flows. Frontend changes are minimal — the existing `useFileUpload` hook and `FilePreviewChips` component already handle per-file status tracking, metadata display, and error states.

## Technical Context

**Language/Version**: Python 3.13 (backend, floor ≥3.12), TypeScript 5.9 (frontend)
**Primary Dependencies**: FastAPI, aiosqlite, httpx, Pydantic (backend); React 19.2, TanStack React Query 5.90 (frontend)
**Storage**: aiosqlite (chat_proposals, chat_recommendations tables) + GitHub Issues (final attachment destination)
**Testing**: pytest (backend), Vitest 4.0 (frontend)
**Target Platform**: Linux server (backend API), browser (frontend SPA)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Attach files to GitHub issue within 10 seconds for files under 5 MB (SC-001)
**Constraints**: GitHub issue body max 65,536 characters; file size max 10 MB (existing); max 5 files per message (existing)
**Scale/Scope**: Up to 10 files per batch (SC-002), typical 1-3 files per interaction

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | Full spec exists at `specs/037-chat-attachment-github-issue/spec.md` with 4 prioritized user stories (P1-P3), Given-When-Then acceptance scenarios, 15 functional requirements, and independent test criteria. |
| **II. Template-Driven Workflow** | ✅ PASS | All artifacts follow canonical templates. Plan follows `plan-template.md`. Spec follows `spec-template.md`. |
| **III. Agent-Orchestrated Execution** | ✅ PASS | `speckit.plan` agent produces this plan with well-defined inputs (spec.md) and outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md). |
| **IV. Test Optionality with Clarity** | ✅ PASS | Tests are included for the new utility function (`format_attachments_markdown`) and the model field additions. Justified by the data-integrity nature: incorrect markdown formatting or missing file URLs would result in broken GitHub issue content. Existing upload/validation tests cover the frontend. |
| **V. Simplicity and DRY** | ✅ PASS | Reuses existing file upload pipeline (~90% already implemented). Single utility function `format_attachments_markdown()` avoids duplication across proposal and recommendation confirmation flows. No new abstractions — extends existing models with one field each. |

**Gate Result**: ✅ ALL PASS — proceed to Phase 0.

**Post-Design Re-Check** (after Phase 1):

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | Design aligns with all 15 functional requirements. FR-001 through FR-015 are addressed by specific code changes documented below. |
| **II. Template-Driven Workflow** | ✅ PASS | All Phase 1 artifacts generated: research.md, data-model.md, contracts/, quickstart.md. |
| **III. Agent-Orchestrated Execution** | ✅ PASS | Clear handoff to `/speckit.tasks` for Phase 2 task decomposition. |
| **IV. Test Optionality with Clarity** | ✅ PASS | Backend unit tests for `format_attachments_markdown()` and model serialization. Frontend tests for attachment status display already exist in `FilePreviewChips` tests. |
| **V. Simplicity and DRY** | ✅ PASS | Total new code: ~1 utility function, ~2 model field additions, ~1 migration file, ~20 lines of body-embedding logic in 2 confirmation handlers. No new abstractions or patterns introduced. |

## Project Structure

### Documentation (this feature)

```text
specs/037-chat-attachment-github-issue/
├── plan.md              # This file
├── research.md          # Phase 0 output — research decisions
├── data-model.md        # Phase 1 output — entity definitions
├── quickstart.md        # Phase 1 output — implementation overview
├── contracts/           # Phase 1 output — API contracts
│   └── chat-attachment-api.yaml
├── checklists/
│   └── requirements.md  # Spec quality checklist (from speckit.specify)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   └── recommendation.py      # MODIFIED: add file_urls field to AITaskProposal and IssueRecommendation
│   ├── services/
│   │   └── github_projects/
│   │       └── issues.py           # UNCHANGED: create_issue() signature sufficient (file URLs go in body)
│   ├── api/
│   │   ├── chat.py                 # MODIFIED: embed file_urls in issue body during confirm_proposal()
│   │   └── workflow.py             # MODIFIED: embed file_urls in issue body during confirm_recommendation()
│   ├── utils/
│   │   └── attachment_formatter.py # NEW: format_attachments_markdown() utility
│   └── migrations/
│       └── 022_chat_file_urls.sql  # NEW: add file_urls column to chat_proposals and chat_recommendations
└── tests/
    └── unit/
        ├── test_attachment_formatter.py  # NEW: unit tests for markdown formatting
        └── test_recommendation.py        # MODIFIED: test file_urls serialization

frontend/
├── src/
│   ├── components/
│   │   └── chat/
│   │       ├── ChatInterface.tsx         # UNCHANGED: already passes fileUrls
│   │       └── FilePreviewChips.tsx      # UNCHANGED: already shows per-file status
│   ├── hooks/
│   │   └── useFileUpload.ts              # UNCHANGED: already manages upload state
│   ├── types/
│   │   └── index.ts                      # UNCHANGED: FileAttachment type already defined
│   └── services/
│       └── api.ts                        # UNCHANGED: uploadFile() and sendMessage() already handle file_urls
└── tests/                                # No new frontend tests needed (existing coverage sufficient)
```

**Structure Decision**: Web application structure (Option 2). Changes span `backend/` with minimal modifications to existing modules. The frontend requires no changes — the existing file upload pipeline already handles all UI requirements (FR-002, FR-003, FR-004, FR-005, FR-006, FR-007). Backend changes focus on the "last mile" connection: persisting file URLs through models and embedding them in GitHub issue bodies.

## Complexity Tracking

> No constitution violations detected. No complexity justifications required.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | — | — |

## Requirements Traceability

| Requirement | Addressed By | Status |
|-------------|-------------|--------|
| FR-001: Auto-attach files to GitHub issue | `confirm_proposal()` and `confirm_recommendation()` embed file URLs in issue body | Design complete |
| FR-002: Batch multi-file upload | `useFileUpload.uploadAll()` (existing) | Already implemented |
| FR-003: Per-file upload status | `useFileUpload` hook + `FilePreviewChips` (existing) | Already implemented |
| FR-004: Confirmation with issue reference | Chat message `action_data` stores issue number (existing) | Already implemented |
| FR-005: Descriptive error messages | `upload_file()` returns structured error responses (existing) | Already implemented |
| FR-006: Per-file retry | `useFileUpload` hook re-uploads failed files (existing) | Already implemented |
| FR-007: File metadata display | `FilePreviewChips` shows filename, icon, size (existing) | Already implemented |
| FR-008: Post as comment with chat reference | `format_attachments_markdown()` adds chat session reference | Design complete |
| FR-009: File size validation pre-upload | `upload_file()` checks `MAX_FILE_SIZE_BYTES` (existing) | Already implemented |
| FR-010: File type validation pre-upload | `upload_file()` checks `ALLOWED_TYPES` and `BLOCKED_TYPES` (existing) | Already implemented |
| FR-011: Reject zero-byte files | Add empty file check in `upload_file()` | Design complete |
| FR-012: Partial batch failure handling | `useFileUpload` tracks per-file status independently (existing) | Already implemented |
| FR-013: No-issue warning message | Frontend check: if no linked issue, display warning | Design complete |
| FR-014: Allow attachments to closed issues | GitHub API allows comments on closed issues (no code change needed) | Already supported |
| FR-015: Error on unavailable issue | `create_issue()` error handling returns 404 error (existing) | Already implemented |
