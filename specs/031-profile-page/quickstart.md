# Quickstart: Add Profile Page to App

**Feature**: 031-profile-page | **Date**: 2026-03-09

## Prerequisites

- Node.js 20+ and npm
- Python 3.11+ and pip
- The repository cloned and on the feature branch

```bash
git checkout 031-profile-page
```

## Setup

### Backend

```bash
cd backend
pip install -e ".[dev]"
uvicorn src.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# App available at http://localhost:5173
```

## New Files to Create

### New Backend Files

| File | Purpose |
|------|---------|
| `backend/src/api/profile.py` | NEW: Profile API endpoints (GET/PATCH profile, POST avatar, GET avatar file) |
| `backend/src/services/profile_store.py` | NEW: Profile data persistence (user_profiles table CRUD) |

### New Frontend Files

| File | Purpose |
|------|---------|
| `frontend/src/pages/ProfilePage.tsx` | NEW: Main profile page layout component |
| `frontend/src/components/profile/ProfileHeader.tsx` | NEW: Avatar display + upload control with preview |
| `frontend/src/components/profile/ProfileForm.tsx` | NEW: Editable fields (display name, bio) with Save/Cancel |
| `frontend/src/components/profile/ProfileMetadata.tsx` | NEW: Read-only account metadata display |
| `frontend/src/hooks/useProfile.ts` | NEW: React Query hook for profile data fetch + mutation |

## Files to Modify

### Backend Modifications

| File | Changes |
|------|---------|
| `backend/src/models/user.py` | Add UserProfile, UserProfileUpdate, UserProfileResponse models |
| `backend/src/main.py` | Register the new profile API router |

### Frontend Modifications

| File | Changes |
|------|---------|
| `frontend/src/App.tsx` | Add `/profile` route inside AuthGate-protected layout |
| `frontend/src/layout/TopBar.tsx` | Make user avatar clickable → navigates to /profile |
| `frontend/src/constants.ts` | Add `/profile` to NAV_ROUTES array |
| `frontend/src/services/api.ts` | Add profileApi functions (getProfile, updateProfile, uploadAvatar) |

## Implementation Order

### Phase 1: Backend — Profile Data Layer (FR-001, FR-003, FR-005, FR-006, FR-007, FR-008)

1. **User models** — `backend/src/models/user.py`
   - Add `UserProfile` model (github_user_id, display_name, bio, avatar_path, timestamps)
   - Add `UserProfileUpdate` model (partial update: display_name, bio)
   - Add `UserProfileResponse` model (composite: GitHub data + profile data)

2. **Profile store** (new) — `backend/src/services/profile_store.py`
   - Create `user_profiles` SQLite table (lazy init, same pattern as settings_store.py)
   - Implement `get_profile(github_user_id)` → `UserProfile | None`
   - Implement `upsert_profile(github_user_id, update)` → `UserProfile`
   - Implement `update_avatar_path(github_user_id, path)` → `None`

3. **Profile API** (new) — `backend/src/api/profile.py`
   - `GET /api/v1/users/profile` — Fetch composite profile (session + DB data)
   - `PATCH /api/v1/users/profile` — Update display_name, bio (validate non-empty name, length limits)
   - `POST /api/v1/users/profile/avatar` — Upload avatar (validate type: PNG/JPG/WebP, size: ≤5MB)
   - `GET /api/v1/users/profile/avatar/{filename}` — Serve uploaded avatar files
   - Register router in `main.py`

**Verify**: `curl -b cookies.txt http://localhost:8000/api/v1/users/profile` returns profile data. `curl -X PATCH ... -d '{"display_name":"Test"}' ...` updates profile.

### Phase 2: Frontend — Profile Page Foundation (FR-001, FR-002, FR-003, FR-016, FR-017)

1. **API service** — `frontend/src/services/api.ts`
   - Add `profileApi.getProfile()` → `GET /users/profile`
   - Add `profileApi.updateProfile(data)` → `PATCH /users/profile`
   - Add `profileApi.uploadAvatar(file)` → `POST /users/profile/avatar`

2. **useProfile hook** (new) — `frontend/src/hooks/useProfile.ts`
   - `useQuery` for profile data with `['profile']` query key
   - `useMutation` for profile update with cache invalidation (`['profile']`, `['auth', 'me']`)
   - `useMutation` for avatar upload with cache invalidation

3. **ProfilePage** (new) — `frontend/src/pages/ProfilePage.tsx`
   - Compose ProfileHeader + ProfileForm + ProfileMetadata in a Card container
   - Responsive layout: `max-w-2xl mx-auto`, single column
   - Loading skeleton and error state with retry

4. **Routing** — `frontend/src/App.tsx`
   - Add `{ path: 'profile', element: <ProfilePage /> }` inside authenticated layout

**Verify**: Navigate to `http://localhost:5173/profile` → page loads with user data from GitHub session.

### Phase 3: Frontend — Profile Editing (FR-005, FR-006, FR-007, FR-008, FR-013, FR-014, FR-015)

1. **ProfileForm** (new) — `frontend/src/components/profile/ProfileForm.tsx`
   - View mode: read-only display with "Edit Profile" button
   - Edit mode: Input for display name, textarea for bio
   - Validation: non-empty display name on blur and before save
   - Save/Cancel buttons with loading state on Save
   - Success/error feedback via inline banner or notification
   - On save success: exit edit mode, show success message

2. **ProfileMetadata** (new) — `frontend/src/components/profile/ProfileMetadata.tsx`
   - Display account creation date and role as read-only fields
   - Handle null values gracefully

**Verify**: Click "Edit Profile" → modify display name → click Save → see updated name. Click Cancel → changes discarded. Try saving empty name → validation error shown.

### Phase 4: Frontend — Avatar Upload (FR-009, FR-010, FR-011, FR-012)

1. **ProfileHeader** (new) — `frontend/src/components/profile/ProfileHeader.tsx`
   - Avatar display with circular crop (96px desktop, 80px mobile)
   - Edit mode: camera overlay on hover, hidden file input
   - File validation: type (PNG/JPG/WebP) and size (≤5MB) client-side
   - Preview: `URL.createObjectURL(file)` displayed before save
   - Error messages for invalid file type or size
   - Avatar fallback: user initials in colored circle when no avatar exists

**Verify**: Click avatar in edit mode → select PNG file → preview shown. Select PDF → error message. Select 10MB file → size error. Save → avatar persisted and visible.

### Phase 5: Navigation Integration (FR-018)

1. **TopBar.tsx** — Make avatar clickable
   - Wrap user avatar container with `<Link to="/profile">`
   - Add hover state for visual feedback (e.g., `hover:border-primary/50`)

2. **constants.ts** — Add sidebar entry
   - Add `{ path: '/profile', label: 'Profile', icon: User }` to `NAV_ROUTES`

**Verify**: Click avatar in TopBar → navigates to /profile page. Profile visible in sidebar navigation.

### Phase 6: Polish & Responsiveness (FR-016, FR-017)

1. **Responsive testing**
   - Verify layout at 320px (mobile), 768px (tablet), 1024px+ (desktop)
   - Avatar scales appropriately
   - Form fields stack vertically on mobile
   - Buttons are touch-friendly (min 44px tap target)

2. **Theme testing**
   - Toggle dark mode → verify all profile elements use theme tokens
   - Verify contrast ratios meet WCAG AA

3. **Edge cases**
   - Session expiry during edit → error notification + redirect to login
   - Navigate away with unsaved changes → browser beforeunload warning
   - Backend returns error during load → error state with retry button

**Verify**: Run `cd frontend && npx vitest run` → all existing tests pass. Run `npx tsc --noEmit` → no type errors.

## Key Patterns to Follow

### Profile Data Fetching

```tsx
import { useProfile } from '@/hooks/useProfile';

function ProfilePage() {
  const { profile, isLoading, error, updateProfile, uploadAvatar, isSaving } = useProfile();
  
  if (isLoading) return <ProfileSkeleton />;
  if (error) return <ProfileError onRetry={refetch} />;
  
  return (
    <Card>
      <ProfileHeader profile={profile} ... />
      <ProfileForm profile={profile} onSave={updateProfile} ... />
      <ProfileMetadata profile={profile} />
    </Card>
  );
}
```

### Avatar Upload with Preview

```tsx
function handleAvatarSelect(file: File) {
  // Validate type
  if (!ACCEPTED_AVATAR_TYPES.includes(file.type)) {
    setError('Please select a PNG, JPG, or WebP image.');
    return;
  }
  // Validate size
  if (file.size > MAX_AVATAR_SIZE) {
    setError('Image must be smaller than 5 MB.');
    return;
  }
  // Create preview
  const previewUrl = URL.createObjectURL(file);
  setAvatarPreview(previewUrl);
  setAvatarFile(file);
}
```

### Profile API Call Pattern

```typescript
// In api.ts — follows existing request() pattern
export const profileApi = {
  async getProfile(): Promise<UserProfile> {
    return request<UserProfile>('/users/profile');
  },
  async updateProfile(data: UserProfileUpdate): Promise<UserProfile> {
    return request<UserProfile>('/users/profile', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },
  async uploadAvatar(file: File): Promise<UserProfile> {
    const formData = new FormData();
    formData.append('file', file);
      const response = await fetch(`${API_BASE_URL}/users/profile/avatar`, {
      method: 'POST',
      body: formData,
    });

      if (!response.ok) {
         throw new Error('Failed to upload avatar');
      }

      return response.json() as Promise<UserProfile>;
  },
};
```

### Backend Endpoint Pattern

```python
# In profile.py — follows existing router pattern
from fastapi import APIRouter, Depends, UploadFile, File
from ..api.auth import get_current_session
from ..models.user import UserSession, UserProfileUpdate, UserProfileResponse

router = APIRouter(prefix="/users/profile", tags=["profile"])

@router.get("", response_model=UserProfileResponse)
async def get_profile(session: UserSession = Depends(get_current_session)):
    profile = await profile_store.get_profile(session.github_user_id)
    return build_profile_response(session, profile)

@router.patch("", response_model=UserProfileResponse)
async def update_profile(
    update: UserProfileUpdate,
    session: UserSession = Depends(get_current_session)
):
    profile = await profile_store.upsert_profile(session.github_user_id, update)
    return build_profile_response(session, profile)
```

## Verification

After implementation, verify:

1. **Auth guard**: Unauthenticated access to `/profile` redirects to `/login`.
2. **Profile view**: Authenticated user sees avatar, username, email on profile page.
3. **Profile edit**: Click "Edit Profile" → modify display name → Save → updated name persists.
4. **Edit cancel**: Click "Edit Profile" → modify fields → Cancel → original values restored.
5. **Validation**: Try saving empty display name → inline validation error shown.
6. **Avatar upload**: Select valid PNG → preview shown → Save → new avatar displayed.
7. **Avatar validation**: Select PDF → error message. Select 10MB PNG → size error.
8. **Navigation**: Click avatar in TopBar → navigates to profile page.
9. **Cross-app update**: Save display name → TopBar reflects new name immediately.
10. **Responsive**: Resize to 320px → profile page stacks vertically, no horizontal scroll.
11. **Dark mode**: Toggle dark mode → all profile elements use correct theme colors.
12. **Metadata**: Account creation date and role displayed as read-only.
13. **Error handling**: Stop backend → profile page shows error with retry button.
14. **Existing tests**: Run `npx vitest run` → all existing tests pass.
15. **TypeScript**: Run `npx tsc --noEmit` → no type errors.
16. **Backend tests**: Run `python -m pytest tests/unit/ -x -q` → all tests pass.
