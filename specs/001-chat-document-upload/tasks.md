---

description: "Task list for chat document upload feature implementation"

---

# Tasks: Chat Document Upload

**Input**: Design documents from `/specs/001-chat-document-upload/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml

**Tests**: Tests are NOT explicitly requested in the feature specification. Test tasks are omitted per template guidelines.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

This project uses a web app structure:
- Backend: `backend/src/`
- Frontend: `frontend/src/`
- Tests: `backend/tests/` and `frontend/src/test/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and storage infrastructure for document uploads

- [ ] T001 Create uploads directory structure at `backend/uploads/` with .gitkeep
- [ ] T002 [P] Add python-magic dependency to `backend/pyproject.toml`
- [ ] T003 [P] Configure file storage settings in `backend/src/config.py` (MAX_FILE_SIZE=20MB, ALLOWED_MIME_TYPES, UPLOAD_DIR)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core utilities and models that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create file validation utility in `backend/src/utils/file_validation.py` (validate MIME type, size, filename sanitization)
- [ ] T005 [P] Extend ChatMessage model in `backend/src/models/chat_message.py` to support action_data.document schema
- [ ] T006 [P] Create document service in `backend/src/services/document_service.py` (save file, generate document_id, build storage path)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Basic Document Upload (Priority: P1) 🎯 MVP

**Goal**: Enable users to upload documents (PDF, DOCX, TXT) and display them as clickable items in chat

**Independent Test**: Select a supported document under 20MB, upload it, and verify it appears as a clickable link in the chat thread that opens/downloads when clicked

### Backend Implementation for User Story 1

- [ ] T007 [P] [US1] Create POST /api/chat/upload endpoint in `backend/src/api/chat.py` (accept multipart/form-data with file and conversation_id)
- [ ] T008 [P] [US1] Create GET /api/chat/document/{document_id} endpoint in `backend/src/api/chat.py` (serve file stream with proper content-type)
- [ ] T009 [US1] Implement upload handler in `backend/src/api/chat.py` that validates file, saves to storage, creates ChatMessage with document metadata
- [ ] T010 [US1] Implement document retrieval handler in `backend/src/api/chat.py` with access control (verify user is conversation participant)
- [ ] T011 [US1] Add document storage path generation logic in `backend/src/services/document_service.py` (pattern: uploads/{conversation_id}/{message_id}_{filename})

### Frontend Implementation for User Story 1

- [ ] T012 [P] [US1] Create DocumentPreview component in `frontend/src/components/chat/DocumentPreview.tsx` (display filename and size)
- [ ] T013 [P] [US1] Create DocumentAttachment component in `frontend/src/components/chat/DocumentAttachment.tsx` (render document as clickable link)
- [ ] T014 [US1] Add file input and attach button to ChatInput component in `frontend/src/components/chat/ChatInput.tsx`
- [ ] T015 [US1] Update ChatMessage component in `frontend/src/components/chat/ChatMessage.tsx` to render DocumentAttachment when message has document
- [ ] T016 [US1] Create useDocumentUpload hook in `frontend/src/hooks/useDocumentUpload.ts` (handle file selection, FormData creation, upload API call)
- [ ] T017 [US1] Add uploadDocument and downloadDocument functions to chat service in `frontend/src/services/chat.ts`
- [ ] T018 [US1] Integrate document upload flow in ChatInput component (file selection → preview → send with document)

**Checkpoint**: At this point, User Story 1 should be fully functional - users can upload documents and click to download them

---

## Phase 4: User Story 2 - Upload Progress and Feedback (Priority: P2)

**Goal**: Display upload progress indicator and success confirmation to improve user experience

**Independent Test**: Upload a large document (10-20MB) and observe progress indicator showing percentage completion, then verify success confirmation

### Implementation for User Story 2

- [ ] T019 [P] [US2] Create UploadProgress component in `frontend/src/components/chat/UploadProgress.tsx` (display progress bar and percentage)
- [ ] T020 [US2] Add XMLHttpRequest-based upload with progress tracking to useDocumentUpload hook in `frontend/src/hooks/useDocumentUpload.ts`
- [ ] T021 [US2] Update ChatInput component in `frontend/src/components/chat/ChatInput.tsx` to show UploadProgress during upload
- [ ] T022 [US2] Add upload state management (uploading, progress percentage, success) to useDocumentUpload hook
- [ ] T023 [US2] Disable send button and show loading state during upload in ChatInput component in `frontend/src/components/chat/ChatInput.tsx`
- [ ] T024 [US2] Add success confirmation message/toast after upload completes in ChatInput component

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - basic upload with progress feedback

---

## Phase 5: User Story 3 - File Validation and Error Handling (Priority: P3)

**Goal**: Validate file types and sizes with clear error messages for better user experience

**Independent Test**: Attempt to upload unsupported file type (.exe) and file over 20MB, verifying appropriate error messages appear

### Backend Implementation for User Story 3

- [ ] T025 [US3] Add detailed error responses to upload endpoint in `backend/src/api/chat.py` (file type errors, size errors, network errors)
- [ ] T026 [US3] Implement server-side file validation in `backend/src/utils/file_validation.py` using python-magic for MIME type checking
- [ ] T027 [US3] Add error handling for storage failures in `backend/src/services/document_service.py`

### Frontend Implementation for User Story 3

- [ ] T028 [P] [US3] Create ErrorMessage component in `frontend/src/components/chat/ErrorMessage.tsx` (display validation errors with dismiss)
- [ ] T029 [US3] Add client-side file validation in useDocumentUpload hook in `frontend/src/hooks/useDocumentUpload.ts` (check file extension and size before upload)
- [ ] T030 [US3] Add error state management to useDocumentUpload hook (error message, error type)
- [ ] T031 [US3] Update ChatInput component in `frontend/src/components/chat/ChatInput.tsx` to display ErrorMessage for validation failures
- [ ] T032 [US3] Add error handling for network failures in chat service in `frontend/src/services/chat.ts`
- [ ] T033 [US3] Implement error message clearing logic (on dismiss or new file selection) in ChatInput component

**Checkpoint**: All user stories should now be independently functional with comprehensive error handling

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Add filename sanitization to prevent path traversal attacks in `backend/src/utils/file_validation.py`
- [ ] T035 [P] Add logging for document upload operations in `backend/src/api/chat.py`
- [ ] T036 [P] Update API documentation in `specs/001-chat-document-upload/contracts/openapi.yaml` if needed
- [ ] T037 [P] Add TypeScript types for document metadata in `frontend/src/types/chat.ts`
- [ ] T038 Run quickstart.md validation scenarios to verify all acceptance criteria

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3, 4, 5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Builds on US1 but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Enhances US1/US2 but independently testable

### Within Each User Story

- Backend endpoints before frontend integration
- Components before hook integration
- Core implementation before UI polish
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Backend and frontend tasks within same user story marked [P] can run in parallel
- All Polish tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Backend tasks can run in parallel:
Task T007: "Create POST /api/chat/upload endpoint in backend/src/api/chat.py"
Task T008: "Create GET /api/chat/document/{document_id} endpoint in backend/src/api/chat.py"

# Frontend component tasks can run in parallel:
Task T012: "Create DocumentPreview component in frontend/src/components/chat/DocumentPreview.tsx"
Task T013: "Create DocumentAttachment component in frontend/src/components/chat/DocumentAttachment.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently using quickstart.md scenarios
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (backend + frontend)
   - Developer B: User Story 2 (progress tracking)
   - Developer C: User Story 3 (error handling)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Use quickstart.md test scenarios to validate each completed user story
- Backend uses FastAPI with multipart/form-data for file uploads
- Frontend uses React with TypeScript and HTML5 File API
- Storage: Local filesystem at backend/uploads/{conversation_id}/
- File validation: python-magic for MIME type checking on server
- Supported formats: PDF (.pdf), DOCX (.docx), TXT (.txt)
- Maximum file size: 20MB (20,971,520 bytes)
