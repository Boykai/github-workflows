# Research: Add Profile Page to App

**Feature**: 031-profile-page | **Date**: 2026-03-09

## R1: Profile Data Storage — New Table vs. Extending User Sessions

**Task**: Determine where to store user profile data (display name, bio, custom avatar) given that the existing `user_sessions` table is session-scoped and `user_preferences` is for app settings.

**Decision**: Create a new `user_profiles` SQLite table keyed by `github_user_id`. This table stores user-owned profile fields (display_name, bio, avatar_path) that persist independently of session lifecycle.

**Rationale**: The existing `user_sessions` table has an 8-hour TTL — sessions are created on login and destroyed on logout or expiration. Storing profile data there would lose it when sessions expire. The `user_preferences` table stores application preferences (theme, AI model, sidebar state) which are categorically different from identity data (name, bio, avatar). A dedicated `user_profiles` table:

1. **Survives session expiration**: Profile data persists across login/logout cycles.
2. **Single source of truth**: One row per `github_user_id` with all profile fields.
3. **Clean separation of concerns**: Identity data (profiles) vs. app preferences (user_preferences) vs. session state (user_sessions).
4. **Simple schema**: Only 6 columns (github_user_id PK, display_name, bio, avatar_path, created_at, updated_at).
5. **Follows existing patterns**: The codebase already has separate tables for distinct concerns (user_sessions, user_preferences, global_settings, project_settings).

**Alternatives Considered**:

- **Extend `user_sessions`**: Rejected — sessions are ephemeral (8h TTL). Adding profile columns would lose data on session expiration. Would require migrating profile data between sessions on re-login.
- **Extend `user_preferences`**: Rejected — preferences table stores app settings (theme, AI model, notifications). Mixing identity data with app preferences violates separation of concerns and makes the table harder to reason about.
- **JSON blob in `user_preferences`**: Rejected — less queryable, no type safety at the DB level, harder to validate and migrate.
- **External storage (S3/cloud)**: Rejected — the application uses SQLite for all persistence. Adding external storage for a simple profile would be over-engineering.

---

## R2: Avatar Upload Strategy — Backend File Storage vs. GitHub Avatar Only

**Task**: Determine whether to support custom avatar uploads or rely solely on the GitHub avatar URL provided by OAuth.

**Decision**: Support both GitHub avatar (default) and custom avatar upload. Custom avatars are stored on the backend filesystem in a dedicated `profile-avatars/` directory under the data path, served via a static file endpoint. The GitHub avatar URL remains the fallback when no custom avatar is uploaded.

**Rationale**: The spec explicitly requires avatar upload with client-side preview (FR-009, FR-010, FR-011, FR-012). The existing codebase has a proven file upload pattern in `chat.py` that handles:

1. **File size validation**: Configurable max size (5 MB for avatars).
2. **File type validation**: Accept list (PNG, JPG, WebP per spec).
3. **Path traversal protection**: UUID-prefixed filenames.
4. **Temp storage with persistence**: Files stored in a known directory.

The profile avatar upload adapts this pattern with these differences:
- **Permanent storage**: Avatars stored in `{data_path}/profile-avatars/` (not temp directory).
- **Single file per user**: New upload replaces previous avatar (old file deleted).
- **Served via API**: `GET /api/v1/users/profile/avatar/{filename}` endpoint serves the file.

**Alternatives Considered**:

- **GitHub avatar only (no upload)**: Rejected — violates FR-009 through FR-012 which explicitly require upload, preview, and file validation. Would significantly reduce the feature scope below spec requirements.
- **Base64 in database**: Rejected — storing images in SQLite bloats the database, slows queries, and complicates backup/restore. File system storage is simpler and more performant.
- **Cloud storage (S3, GCS)**: Rejected — the application uses local SQLite and filesystem. Adding cloud storage infrastructure for a single feature would be over-engineering. The existing chat upload pattern uses local filesystem successfully.
- **Client-side only (IndexedDB/localStorage)**: Rejected — not portable across devices or browsers. Lost on cache clear. Doesn't satisfy the requirement that avatar changes reflect across the app immediately.

---

## R3: Profile API Design — RESTful Endpoints

**Task**: Determine the API endpoint structure for profile CRUD operations, following existing backend patterns.

**Decision**: Add three endpoints to a new `profile.py` API router:

1. `GET /api/v1/users/profile` — Fetch the authenticated user's profile (merges DB profile data with GitHub session data).
2. `PATCH /api/v1/users/profile` — Update editable profile fields (display_name, bio).
3. `POST /api/v1/users/profile/avatar` — Upload a new avatar image file.

All endpoints require authentication via the existing `get_current_session` dependency.

**Rationale**: The endpoint design follows existing backend conventions:

1. **Router pattern**: New `profile.py` file in `backend/src/api/` with `APIRouter(prefix="/users/profile")`, registered in `main.py` — follows the same pattern as `auth.py`, `settings.py`, `agents.py`.
2. **Session dependency**: Uses `get_current_session` from `auth.py` — same auth pattern as all other protected endpoints.
3. **PATCH for updates**: Partial updates using `PATCH` — consistent with settings endpoints (`PUT /settings/user`). The spec only allows editing specific fields, not replacing the entire resource.
4. **Separate avatar endpoint**: File upload is a distinct operation from text field updates — separating it allows different content types (`multipart/form-data` for avatar vs. `application/json` for profile fields).
5. **Merged response**: `GET` returns a composite object merging GitHub data (username, email, avatar_url from session) with profile data (display_name, bio, custom avatar from `user_profiles` table) — the frontend gets a single unified view.

**Alternatives Considered**:

- **Extend `GET /auth/me`**: Rejected — the auth endpoint returns session data for authentication purposes. Adding profile fields would mix concerns and break the existing frontend `useAuth` contract.
- **Single `PUT /users/profile` (full replace)**: Rejected — PATCH is more appropriate since the frontend updates individual fields. PUT would require the frontend to send all fields even if only one changed.
- **Avatar as part of PATCH body (base64)**: Rejected — mixing file upload with JSON body is awkward. Separate endpoints allow the avatar upload to use `multipart/form-data` natively.
- **GraphQL**: Rejected — the entire backend uses REST. Adding GraphQL for one feature would be inconsistent.

---

## R4: Frontend State Management — Profile Data Flow

**Task**: Determine how profile data flows through the frontend, including fetching, caching, mutation, and cross-component updates.

**Decision**: Create a custom `useProfile` hook that wraps React Query (`useQuery` + `useMutation`) for profile data management. The hook provides:

- `profile` — cached profile data from `GET /api/v1/users/profile`
- `updateProfile` — mutation function that calls `PATCH /api/v1/users/profile` and invalidates the profile query cache
- `uploadAvatar` — mutation function that calls `POST /api/v1/users/profile/avatar` and invalidates both profile and auth query caches
- `isLoading`, `isSaving`, `error` — loading and error states

After successful save, the hook invalidates both the `['profile']` query key and the `['auth', 'me']` query key to ensure the updated display name and avatar reflect in the `TopBar` immediately (FR-015).

**Rationale**: React Query is the established data-fetching solution in this codebase (used by `useAuth`, `useProjectBoard`, `useNotifications`, etc.). Using the same pattern for profile data ensures:

1. **Consistency**: Same caching, error handling, and loading patterns as the rest of the app.
2. **Cache invalidation**: `queryClient.invalidateQueries(['auth', 'me'])` after profile save triggers a re-fetch of the auth data, which updates the `TopBar` avatar and username (FR-015).
3. **Optimistic updates**: Optional — can show the new display name immediately while the save request is in flight, reverting on error.
4. **No new dependencies**: React Query is already installed and configured.

**Alternatives Considered**:

- **Global auth context with profile state**: Rejected — the app uses React Query for auth state, not a React Context. Adding a separate Context for profile would create two competing state sources for user data.
- **Local component state only (no React Query)**: Rejected — would not support cache invalidation across components. The TopBar needs to reflect profile changes immediately, which requires a shared cache.
- **Zustand/Redux store**: Rejected — the app doesn't use any global store library. React Query fills this role. Adding Zustand for one feature would be over-engineering.

---

## R5: Navigation Entry Point — TopBar Avatar Click vs. Dropdown Menu

**Task**: Determine how users navigate to the profile page from the existing UI.

**Decision**: Make the existing user avatar in the `TopBar` clickable, navigating directly to `/profile`. Additionally, add `/profile` to the `NAV_ROUTES` array in `constants.ts` for sidebar visibility.

**Rationale**: The `TopBar` already displays the user's avatar and username in a styled container (`div` with `rounded-full border`). Making this clickable is:

1. **Zero new UI**: No new components or dropdown menus — just wrapping the existing avatar container with a `<Link to="/profile">`.
2. **Discoverable**: Users intuitively expect clicking their avatar to go to their profile (convention from GitHub, Slack, Discord, etc.).
3. **Consistent**: The existing `TopBar` uses direct navigation (breadcrumbs) rather than dropdown menus.
4. **Sidebar entry**: Adding to `NAV_ROUTES` provides a secondary path and makes the profile page visible in the navigation structure, but the TopBar avatar is the primary entry point.

**Alternatives Considered**:

- **Dropdown menu from avatar**: Rejected — adds UI complexity (new dropdown component, menu items, click-outside handling) for a single destination. The existing `TopBar` has no dropdown patterns — the `NotificationBell` is the closest but it shows a list, not navigation.
- **Sidebar only (no TopBar change)**: Rejected — the sidebar is collapsible and often hidden on mobile. The TopBar avatar is always visible and is the most discoverable entry point.
- **Floating action button**: Rejected — not consistent with the existing navigation patterns. The app uses sidebar + topbar, not FABs.
