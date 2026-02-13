---

description: "Task list for Profile Picture Upload feature implementation"
---

# Tasks: Profile Picture Upload

**Input**: Feature specification from issue description
**Feature**: Enable profile picture upload functionality for user profiles

**Tests**: Tests are NOT explicitly requested in the specification, so they are omitted from this task list.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

This project uses a web app structure:
- Backend: `backend/src/` (Python FastAPI)
- Frontend: `frontend/src/` (React + TypeScript)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependencies

- [ ] T001 [P] Add python-magic library to backend/pyproject.toml for MIME type validation
- [ ] T002 [P] Add Pillow library to backend/pyproject.toml for image processing
- [ ] T003 Create uploads directory structure in backend/uploads/ for storing profile pictures

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Add profile_picture_url field to UserSession model in backend/src/models/user.py
- [ ] T005 Add profile_picture_url field to UserResponse model in backend/src/models/user.py
- [ ] T006 [P] Create ProfilePictureUpload model in backend/src/models/user.py for upload request validation
- [ ] T007 [P] Create file storage service in backend/src/services/file_storage.py with save, delete, and get_url methods
- [ ] T008 [P] Create image validation utility in backend/src/services/image_validator.py for format and size checks
- [ ] T009 Add static file serving configuration in backend/src/main.py to serve uploaded images
- [ ] T010 Create profile pictures API router in backend/src/api/profile_pictures.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Upload Profile Picture (Priority: P1) 🎯 MVP

**Goal**: Enable users to upload a JPEG or PNG profile picture with preview, validation, and display throughout the app

**Independent Test**: Navigate to profile page, click "Upload Photo" button, select a valid JPEG or PNG file under 5MB, preview the image, confirm upload, verify it displays in profile header and throughout the app

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement POST /api/v1/profile-picture/upload endpoint in backend/src/api/profile_pictures.py with file validation
- [ ] T012 [P] [US1] Implement GET /api/v1/profile-picture endpoint in backend/src/api/profile_pictures.py to retrieve current profile picture
- [ ] T013 [US1] Update get_current_session dependency in backend/src/api/auth.py to include profile_picture_url
- [ ] T014 [US1] Update session storage in backend/src/services/github_auth.py to persist profile_picture_url
- [ ] T015 [P] [US1] Create ProfilePictureUpload component in frontend/src/components/profile/ProfilePictureUpload.tsx with file picker, preview, and upload logic
- [ ] T016 [P] [US1] Create useProfilePicture hook in frontend/src/hooks/useProfilePicture.ts for API integration
- [ ] T017 [P] [US1] Create Avatar component in frontend/src/components/common/Avatar.tsx to display profile pictures consistently
- [ ] T018 [US1] Add profile picture upload section to profile page (create frontend/src/components/profile/ProfilePage.tsx if needed)
- [ ] T019 [US1] Update user avatar display in App header (frontend/src/App.tsx) to use Avatar component
- [ ] T020 [US1] Update API types in frontend/src/types/index.ts to include profile_picture_url
- [ ] T021 [US1] Add profile picture upload API methods to frontend/src/services/api.ts
- [ ] T022 [US1] Update useAuth hook in frontend/src/hooks/useAuth.ts to include profile_picture_url in user data

**Checkpoint**: At this point, User Story 1 should be fully functional - users can upload profile pictures and see them displayed throughout the app

---

## Phase 4: User Story 2 - Change Existing Profile Picture (Priority: P2)

**Goal**: Allow users to replace their existing profile picture with a new image

**Independent Test**: Upload an initial profile picture (US1), then repeat the upload process with a different image and verify the old image is replaced across all locations

### Implementation for User Story 2

- [ ] T023 [US2] Update POST /api/v1/profile-picture/upload endpoint in backend/src/api/profile_pictures.py to handle replacement logic (delete old file)
- [ ] T024 [US2] Update file_storage service in backend/src/services/file_storage.py to add replace_file method
- [ ] T025 [US2] Update ProfilePictureUpload component in frontend/src/components/profile/ProfilePictureUpload.tsx to show current picture before upload
- [ ] T026 [US2] Add visual indication in frontend/src/components/profile/ProfilePictureUpload.tsx when replacing existing picture

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - users can upload and replace profile pictures

---

## Phase 5: User Story 3 - Remove Profile Picture (Priority: P3)

**Goal**: Allow users to remove their profile picture and revert to default avatar

**Independent Test**: Upload a profile picture, use the remove option, and verify a default avatar appears in place of the custom image

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement DELETE /api/v1/profile-picture endpoint in backend/src/api/profile_pictures.py
- [ ] T028 [US3] Update session storage in backend/src/services/github_auth.py to clear profile_picture_url on delete
- [ ] T029 [US3] Add remove button to ProfilePictureUpload component in frontend/src/components/profile/ProfilePictureUpload.tsx
- [ ] T030 [US3] Update Avatar component in frontend/src/components/common/Avatar.tsx to show default avatar when no picture exists
- [ ] T031 [US3] Add delete profile picture API method to frontend/src/services/api.ts

**Checkpoint**: All user stories should now be independently functional - users can upload, replace, and remove profile pictures

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Add comprehensive error handling for file upload failures across all endpoints
- [ ] T033 [P] Add request size limits in backend/src/main.py to prevent oversized uploads
- [ ] T034 [P] Add loading states and progress indicators in frontend/src/components/profile/ProfilePictureUpload.tsx
- [ ] T035 Add file cleanup service in backend/src/services/file_storage.py to remove orphaned files
- [ ] T036 [P] Update .env.example with profile picture storage configuration options
- [ ] T037 [P] Add profile picture feature documentation to README.md
- [ ] T038 Update .gitignore to exclude backend/uploads/ directory from version control

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Builds on US1 (reuses upload endpoint and component) but is independently testable
- **User Story 3 (P3)**: Builds on US1 (uses same components) but is independently testable

### Within Each User Story

- Backend endpoints before frontend API integration
- API services before UI components
- Base components (Avatar, hooks) before page integration
- Core implementation before polish features

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Models and services can be built in parallel
- Backend and frontend work can proceed in parallel once models are defined
- All Polish tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch backend tasks together:
Task: "Implement POST /api/v1/profile-picture/upload endpoint"
Task: "Implement GET /api/v1/profile-picture endpoint"

# Launch frontend component tasks together:
Task: "Create ProfilePictureUpload component"
Task: "Create useProfilePicture hook"
Task: "Create Avatar component"

# Then integrate them together:
Task: "Add profile picture upload section to profile page"
Task: "Update user avatar display in App header"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (install dependencies, create directories)
2. Complete Phase 2: Foundational (models, services, base infrastructure)
3. Complete Phase 3: User Story 1 (full upload flow)
4. **STOP and VALIDATE**: Test User Story 1 independently
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
   - Developer A: User Story 1 (upload flow)
   - Developer B: User Story 2 (replace logic) - can work on backend simultaneously
   - Developer C: User Story 3 (delete logic) - can work on backend simultaneously
3. Stories complete and integrate independently

---

## Notes

- File uploads limited to 5MB as per requirements
- Supported formats: JPEG and PNG only
- Profile pictures stored in backend/uploads/profile-pictures/{user_id}/
- Default avatar displayed using initials or GitHub avatar when no custom picture exists
- All API endpoints require authentication via session cookie
- File validation occurs both client-side (for UX) and server-side (for security)
- Profile pictures are associated with sessions, not GitHub accounts directly
- Consider adding image optimization/resizing in future iterations
- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
