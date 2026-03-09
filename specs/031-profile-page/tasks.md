# Tasks: Add Profile Page to App

**Input**: Design documents from `/specs/031-profile-page/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in the feature specification. Existing tests should continue to pass.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add new Pydantic models, TypeScript types, and shared constants that multiple user stories depend on.

- [x] T001 Add `UserProfile`, `UserProfileUpdate`, and `UserProfileResponse` Pydantic models to `backend/src/models/user.py` — `UserProfile` with fields (github_user_id, display_name, bio, avatar_path, created_at, updated_at), `UserProfileUpdate` with optional display_name and bio, `UserProfileResponse` merging GitHub session data with profile data (github_user_id, github_username, github_avatar_url, display_name, bio, avatar_url, account_created_at, role)
- [x] T002 [P] Add `UserProfile`, `UserProfileUpdate`, `ProfileFormState`, `ProfileValidation` TypeScript interfaces and avatar validation constants (`MAX_AVATAR_SIZE = 5 * 1024 * 1024`, `ACCEPTED_AVATAR_TYPES`, `ACCEPTED_AVATAR_EXTENSIONS`) to `frontend/src/types/index.ts`
- [x] T003 [P] Add `profileApi` functions (`getProfile`, `updateProfile`, `uploadAvatar`) to `frontend/src/services/api.ts` — `getProfile()` calls `GET /users/profile`, `updateProfile(data)` calls `PATCH /users/profile` with JSON body, `uploadAvatar(file)` calls `POST /users/profile/avatar` with `multipart/form-data` (do NOT set Content-Type header manually)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend profile data layer and API endpoints that MUST be complete before any frontend user story work can begin.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T004 Create `ProfileStore` class in `backend/src/services/profile_store.py` — lazy `ensure_table()` that creates `user_profiles` SQLite table (github_user_id TEXT PK, display_name TEXT, bio TEXT, avatar_path TEXT, created_at TEXT NOT NULL DEFAULT datetime('now'), updated_at TEXT NOT NULL DEFAULT datetime('now')) with index on updated_at; implement `get_profile(github_user_id) → UserProfile | None`, `upsert_profile(github_user_id, update) → UserProfile` using INSERT OR REPLACE preserving existing fields, and `update_avatar_path(github_user_id, path) → None`; follow the existing `settings_store.py` pattern for aiosqlite usage
- [x] T005 Create profile API router in `backend/src/api/profile.py` with `APIRouter(prefix="/users/profile", tags=["profile"])` — implement `GET ""` (fetch composite profile merging session + DB data, resolve avatar_url to custom upload path or GitHub fallback), `PATCH ""` (validate non-empty display_name ≤100 chars, bio ≤500 chars, upsert profile, return composite response), `POST "/avatar"` (validate file type PNG/JPG/WebP and size ≤5 MB, generate UUID-prefixed filename, delete previous avatar if exists, save to `{data_path}/profile-avatars/`, upsert avatar_path, return composite response), `GET "/avatar/{filename}"` (validate no path traversal, serve FileResponse with correct content type); all endpoints use `Depends(get_current_session)` for authentication
- [x] T006 Register the profile API router in `backend/src/main.py` — import and include the profile router with the existing API router group
- [x] T007 Create `useProfile` React Query hook in `frontend/src/hooks/useProfile.ts` — `useQuery` with key `['profile']` calling `profileApi.getProfile()`; `useMutation` for `updateProfile` that invalidates `['profile']` and `['auth', 'me']` on success; `useMutation` for `uploadAvatar` that invalidates `['profile']` and `['auth', 'me']` on success; expose `profile`, `isLoading`, `error`, `updateProfile`, `uploadAvatar`, `isSaving` (updateMutation.isPending || avatarMutation.isPending), `saveError`

**Checkpoint**: Backend profile endpoints are functional and the frontend hook is ready. Profile data can be fetched and updated via API. User story implementation can now begin.

---

## Phase 3: User Story 1 — View Personal Profile Information (Priority: P1) 🎯 MVP

**Goal**: Authenticated users can navigate to `/profile` and see their avatar, display name, email, and account metadata displayed in a clean, read-only layout.

**Independent Test**: Navigate to `/profile` as an authenticated user → page displays avatar (or placeholder), display name (or GitHub username fallback), email, account creation date, and role. Unauthenticated access redirects to login.

### Implementation for User Story 1

- [x] T008 [P] [US1] Create `ProfileMetadata` component in `frontend/src/components/profile/ProfileMetadata.tsx` — accept `ProfileMetadataProps { profile: UserProfile }`; display account creation date in human-readable format (e.g., "Member since March 2026") and role with badge styling (`inline-flex px-2 py-0.5 rounded-full text-xs bg-primary/10 text-primary`); handle null `account_created_at` gracefully (show "—"); use `border-t border-border/60 pt-4 mt-4` container styling
- [x] T009 [P] [US1] Create `ProfileHeader` component (view-only scaffold) in `frontend/src/components/profile/ProfileHeader.tsx` — accept `ProfileHeaderProps { profile, avatarFile, avatarPreview, isEditing, onAvatarSelect, onAvatarError }`; display avatar as circular image (`rounded-full`, 96x96px desktop / 80x80px mobile, `border-2 border-primary/30 shadow-sm`); show `display_name` (fallback to `github_username`) as `text-2xl font-semibold`; show `@github_username` as `text-sm text-muted-foreground`; render initials fallback when no avatar URL exists; edit-mode overlay and upload logic will be added in US3
- [x] T010 [US1] Create `ProfilePage` component in `frontend/src/pages/ProfilePage.tsx` — call `useProfile()` hook; render loading skeleton while fetching; render error state with retry button on failure; compose `ProfileHeader`, `ProfileForm` (view-only initially), and `ProfileMetadata` inside a `Card` container with `max-w-2xl mx-auto` responsive layout; single-column layout for all viewports
- [x] T011 [US1] Add `/profile` route to `frontend/src/App.tsx` — import `ProfilePage` and add `{ path: 'profile', element: <ProfilePage /> }` inside the AuthGate-protected layout routes

**Checkpoint**: Authenticated users can view their profile information at `/profile`. The page shows avatar, name, email, and metadata. Auth guard prevents unauthenticated access.

---

## Phase 4: User Story 2 — Edit Profile Details (Priority: P1)

**Goal**: Users can edit their display name and bio on the profile page with Save/Cancel actions, field validation, and success/error feedback.

**Independent Test**: Click "Edit Profile" → display name and bio become editable inputs → modify display name → click Save → success notification shown, name persists. Click Cancel → changes discarded. Try saving empty display name → validation error shown. Updated name reflects in TopBar immediately.

### Implementation for User Story 2

- [x] T012 [US2] Create `ProfileForm` component in `frontend/src/components/profile/ProfileForm.tsx` — accept `ProfileFormProps { profile, isEditing, isSaving, onEdit, onSave, onCancel }`; view mode: display display name, bio, and email as read-only text with "Edit Profile" button calling `onEdit()`; edit mode: `Input` component for display name, `<textarea>` for bio, email as read-only text; validate non-empty display name on blur and before save (show `text-xs text-destructive mt-1` error); "Save" button (`Button variant="default"`, disabled when `isSaving` or validation fails) calls `onSave({ display_name, bio })`; "Cancel" button (`Button variant="outline"`) calls `onCancel()`; local `useState` for form values, reset to profile data on cancel
- [x] T013 [US2] Wire edit mode state management into `ProfilePage` in `frontend/src/pages/ProfilePage.tsx` — add `isEditing` state; pass `isEditing`, `isSaving`, `onEdit`, `onSave`, `onCancel` props to `ProfileForm`; on save: call `updateProfile()` from `useProfile` hook, show success toast on completion, exit edit mode; on error: show error toast, keep form values; on cancel: reset editing state
- [x] T014 [US2] Add success/error toast notifications for profile updates in `frontend/src/pages/ProfilePage.tsx` — use existing toast/notification pattern from the codebase; show success message ("Profile updated successfully") on save; show error message with details on failure ("Failed to update profile. Please try again.")

**Checkpoint**: Users can edit and save profile details. Validation prevents empty display names. Success/error feedback is displayed. Changes reflect across the app immediately via React Query cache invalidation.

---

## Phase 5: User Story 3 — Upload or Change Avatar (Priority: P2)

**Goal**: Users can upload a new profile picture with client-side preview, file validation (type and size), and server persistence.

**Independent Test**: In edit mode, click avatar → file picker opens → select valid PNG → preview shown → save → new avatar displayed on profile and in TopBar. Select invalid file type (PDF) → error message. Select oversized file (>5 MB) → size error. Upload failure → error toast, previous avatar retained.

### Implementation for User Story 3

- [x] T015 [US3] Add avatar upload UI to `ProfileHeader` in `frontend/src/components/profile/ProfileHeader.tsx` — when `isEditing` is true: show camera/upload overlay on avatar hover (`absolute inset-0 bg-black/40 rounded-full flex items-center justify-center`); add hidden `<input type="file" accept="image/png,image/jpeg,image/webp">`; on file selection: validate type against `ACCEPTED_AVATAR_TYPES` and size against `MAX_AVATAR_SIZE`; valid file: call `URL.createObjectURL(file)` for preview and `onAvatarSelect(file)`; invalid file: call `onAvatarError(message)` with descriptive error ("Please select a PNG, JPG, or WebP image" or "Image must be smaller than 5 MB"); when `avatarPreview` is set, display preview image instead of current avatar
- [x] T016 [US3] Wire avatar upload into `ProfilePage` save flow in `frontend/src/pages/ProfilePage.tsx` — add `avatarFile` and `avatarPreview` state; pass to `ProfileHeader`; on save: if `avatarFile` is set, call `uploadAvatar(file)` from `useProfile` hook before or alongside `updateProfile()`; clean up preview Object URL on unmount or after successful upload; show avatar-specific error messages on upload failure

**Checkpoint**: Avatar upload with preview, validation, and persistence is fully functional. Invalid files are rejected client-side. New avatars display across the app.

---

## Phase 6: User Story 4 — Navigate to Profile Page (Priority: P2)

**Goal**: A consistent navigation entry point (clickable TopBar avatar + optional sidebar link) allows users to quickly access the profile page from anywhere in the app.

**Independent Test**: Click user avatar in TopBar → navigates to `/profile`. Profile link visible in sidebar navigation. Entry points only visible to authenticated users.

### Implementation for User Story 4

- [x] T017 [P] [US4] Make TopBar avatar clickable in `frontend/src/layout/TopBar.tsx` — wrap the existing user avatar container (`div` with `rounded-full border`) with `<Link to="/profile">` from react-router-dom; add `hover:border-primary/50 transition-colors` for visual hover feedback; preserve existing styling and layout
- [x] T018 [P] [US4] Add profile route to sidebar navigation in `frontend/src/constants.ts` — import `User` icon from lucide-react; add `{ path: '/profile', label: 'Profile', icon: User }` to the `NAV_ROUTES` array

**Checkpoint**: Users can navigate to the profile page from both the TopBar avatar and the sidebar. Navigation elements are only visible to authenticated users.

---

## Phase 7: User Story 5 — Responsive Profile Page Layout (Priority: P2)

**Goal**: The profile page renders correctly and is fully usable across mobile (320px+), tablet (768px+), and desktop (1024px+) viewports with no horizontal scrolling or overlapping elements.

**Independent Test**: Load profile page at 320px width → content stacks vertically, no horizontal scroll, touch targets ≥44px. Load at 768px → layout adapts between mobile and desktop. Load at 1024px+ → comfortable reading width with max-w-2xl centering.

### Implementation for User Story 5

- [x] T019 [US5] Audit and refine responsive styling across all profile components — in `ProfilePage.tsx`: verify `max-w-2xl mx-auto px-4` provides proper padding on mobile; in `ProfileHeader.tsx`: verify avatar scales from 80px (mobile) to 96px (desktop) using responsive classes; in `ProfileForm.tsx`: verify input fields and buttons are full-width on mobile with min 44px touch target height; in `ProfileMetadata.tsx`: verify metadata rows stack properly on small screens; test at 320px, 768px, and 1024px breakpoints
- [x] T020 [US5] Verify Solar theme and dark mode compatibility across all profile components — toggle dark mode and verify all profile elements use correct theme tokens (`text-foreground`, `text-muted-foreground`, `bg-card`, `border-border`); verify avatar border, form inputs, buttons, and metadata badges render correctly in both light and dark themes; verify WCAG AA color contrast ratios are met

**Checkpoint**: Profile page is fully responsive across all viewport sizes and compatible with both light and dark themes.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Edge case handling, error states, and final cleanup across all user stories.

- [x] T021 [P] Add unsaved changes warning — in `ProfilePage.tsx`, add `beforeunload` event listener when form `isDirty` is true to warn users before navigating away with unsaved changes
- [x] T022 [P] Add loading skeleton for profile page — in `ProfilePage.tsx`, create a skeleton layout (circular skeleton for avatar, rectangular skeletons for text fields) displayed while profile data is being fetched
- [x] T023 [P] Add error state with retry for profile page — in `ProfilePage.tsx`, render a user-friendly error message with a retry button when profile data fetch fails, rather than showing a blank page
- [x] T024 Verify existing tests pass — run `cd frontend && npx vitest run` (all existing tests pass), `cd frontend && npx tsc --noEmit` (no type errors), `cd backend && python -m pytest tests/unit/ -x -q` (all existing tests pass)
- [x] T025 Run quickstart.md verification checklist — verify all 16 items from quickstart.md: auth guard, profile view, profile edit, edit cancel, validation, avatar upload, avatar validation, navigation, cross-app update, responsive, dark mode, metadata, error handling, existing frontend tests, TypeScript, and backend tests

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (models/types must exist) — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 completion (backend endpoints + useProfile hook)
- **User Story 2 (Phase 4)**: Depends on Phase 3 (ProfilePage and ProfileForm view mode must exist)
- **User Story 3 (Phase 5)**: Depends on Phase 3 (ProfileHeader must exist); can run in parallel with Phase 4
- **User Story 4 (Phase 6)**: Depends on Phase 3 (profile route must exist); can run in parallel with Phases 4 and 5
- **User Story 5 (Phase 7)**: Depends on Phases 3–6 (all components must exist for responsive audit)
- **Polish (Phase 8)**: Depends on all user story phases being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Depends on US1 (needs ProfilePage and ProfileForm scaffold) — Core editing functionality
- **User Story 3 (P2)**: Depends on US1 (needs ProfileHeader); independent of US2 — Avatar upload is a separate interaction
- **User Story 4 (P2)**: Depends on US1 (needs profile route); independent of US2 and US3 — Navigation entry points
- **User Story 5 (P2)**: Depends on US1–US4 (audits responsive behavior of all components)

### Within Each User Story

- Models/types before services
- Services before components
- Components before page integration
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T002 and T003 in parallel)
- User Story 1: T008 and T009 can run in parallel (different component files)
- User Story 3 and User Story 4 can run in parallel after User Story 1 completes
- User Story 4: T017 and T018 can run in parallel (different files)
- All Polish tasks marked [P] can run in parallel (T021, T022, T023)

---

## Parallel Example: User Story 1

```bash
# Launch view-only components in parallel:
Task T008: "Create ProfileMetadata component in frontend/src/components/profile/ProfileMetadata.tsx"
Task T009: "Create ProfileHeader component (view-only scaffold) in frontend/src/components/profile/ProfileHeader.tsx"

# Then compose into page (sequential — depends on T008, T009):
Task T010: "Create ProfilePage component in frontend/src/pages/ProfilePage.tsx"
Task T011: "Add /profile route to frontend/src/App.tsx"
```

## Parallel Example: User Story 4

```bash
# Both navigation changes are independent files:
Task T017: "Make TopBar avatar clickable in frontend/src/layout/TopBar.tsx"
Task T018: "Add profile route to sidebar navigation in frontend/src/constants.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 + User Story 2)

1. Complete Phase 1: Setup (types and models)
2. Complete Phase 2: Foundational (backend endpoints + useProfile hook)
3. Complete Phase 3: User Story 1 — View profile page
4. **STOP and VALIDATE**: Authenticated user can view profile at `/profile`
5. Complete Phase 4: User Story 2 — Edit profile details
6. **STOP and VALIDATE**: User can edit display name and bio with Save/Cancel
7. Deploy/demo MVP — core profile viewing and editing is functional

### Incremental Delivery

1. Complete Setup + Foundational → Backend ready, hook ready
2. Add User Story 1 → View profile → Deploy/Demo (read-only MVP!)
3. Add User Story 2 → Edit profile → Deploy/Demo (full text editing MVP!)
4. Add User Story 3 → Avatar upload → Deploy/Demo (personalization)
5. Add User Story 4 → Navigation → Deploy/Demo (discoverability)
6. Add User Story 5 → Responsive audit → Deploy/Demo (polish)
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 → User Story 2 (sequential, US2 depends on US1)
   - Developer B: User Story 3 (can start after US1 ProfileHeader exists)
   - Developer C: User Story 4 (can start after US1 route exists)
3. User Story 5 is a responsive audit pass after all components exist

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avatar upload reuses the existing chat file upload pattern from `chat.py`
- Profile store follows the existing `settings_store.py` pattern for aiosqlite usage
- React Query cache invalidation of `['auth', 'me']` ensures TopBar updates immediately after profile save (FR-015)
- No new frontend dependencies required — all UI uses existing Solune design system components
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
