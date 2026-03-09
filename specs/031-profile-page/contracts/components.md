# Component Contracts: Add Profile Page to App

**Feature**: 031-profile-page | **Date**: 2026-03-09

## New Frontend Components

### ProfilePage

**Location**: `frontend/src/pages/ProfilePage.tsx`
**Purpose**: Main profile page layout that composes the header, form, and metadata sub-components. Handles routing, auth guard integration, and top-level loading/error states.

```typescript
// No props — page component rendered by React Router
export default function ProfilePage(): JSX.Element;
```

**Behavior**:

- Calls `useProfile()` hook to fetch profile data on mount.
- Renders loading skeleton while profile data is being fetched.
- Renders error state with retry button if fetch fails.
- Composes `ProfileHeader`, `ProfileForm`, and `ProfileMetadata` in a responsive grid layout.
- Uses `Card` component as the outer container for visual consistency.
- Layout: Single column on mobile, comfortable max-width on desktop (`max-w-2xl mx-auto`).

**Layout Structure**:

```text
┌─────────────────────────────────────────────────┐
│  Card                                            │
│  ┌───────────────────────────────────────────┐  │
│  │  ProfileHeader                             │  │
│  │  [Avatar] [Display Name]                   │  │
│  │  [Username] [Email]                        │  │
│  └───────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────┐  │
│  │  ProfileForm                               │  │
│  │  [Display Name Input]                      │  │
│  │  [Bio Textarea]                            │  │
│  │  [Save] [Cancel]                           │  │
│  └───────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────┐  │
│  │  ProfileMetadata                           │  │
│  │  [Account Created] [Role]                  │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

---

### ProfileHeader

**Location**: `frontend/src/components/profile/ProfileHeader.tsx`
**Purpose**: Displays the user's avatar with upload capability, display name (or GitHub username fallback), and email. Handles avatar file selection, validation, and preview.

```typescript
interface ProfileHeaderProps {
  profile: UserProfile;                   // Current profile data
  avatarFile: File | null;                // Currently selected avatar file (before save)
  avatarPreview: string | null;           // Object URL for client-side preview
  isEditing: boolean;                     // Whether edit mode is active
  onAvatarSelect: (file: File) => void;   // Callback when user selects a valid avatar file
  onAvatarError: (message: string) => void; // Callback when avatar validation fails
}

export function ProfileHeader(props: ProfileHeaderProps): JSX.Element;
```

**Behavior**:

- Displays avatar as a circular image (`rounded-full`, 96x96px on desktop, 80x80px on mobile).
- When `isEditing` is true:
  - Shows a camera/upload overlay on the avatar on hover.
  - Clicking the avatar opens a hidden `<input type="file" accept="image/png,image/jpeg,image/webp">`.
  - On file selection: validates file type (PNG, JPG, WebP) and size (≤5 MB).
  - Valid file: creates `URL.createObjectURL(file)` for preview, calls `onAvatarSelect(file)`.
  - Invalid file: calls `onAvatarError(message)` with descriptive error.
- When `avatarPreview` is set, displays the preview image instead of the current avatar.
- Shows `display_name` (falling back to `github_username`) as the primary heading.
- Shows `github_username` as secondary text (prefixed with `@`).
- Avatar fallback: If no avatar URL, renders user initials in a colored circle.

**Styling**:

```text
Avatar: rounded-full, border-2 border-primary/30, shadow-sm
Name: text-2xl font-semibold text-foreground
Username: text-sm text-muted-foreground
Edit overlay: absolute inset-0, bg-black/40, rounded-full, flex items-center justify-center
```

---

### ProfileForm

**Location**: `frontend/src/components/profile/ProfileForm.tsx`
**Purpose**: Renders editable profile fields (display name, bio) with inline editing, validation, and Save/Cancel actions.

```typescript
interface ProfileFormProps {
  profile: UserProfile;                   // Current profile data (source of truth)
  isEditing: boolean;                     // Whether edit mode is active
  isSaving: boolean;                      // Whether a save is in progress
  onEdit: () => void;                     // Enter edit mode
  onSave: (data: UserProfileUpdate) => void;  // Save changes
  onCancel: () => void;                   // Discard changes and exit edit mode
}

export function ProfileForm(props: ProfileFormProps): JSX.Element;
```

**Behavior**:

- **View mode** (`isEditing=false`):
  - Displays display name and bio as read-only text.
  - Shows an "Edit Profile" button that calls `onEdit()`.
- **Edit mode** (`isEditing=true`):
  - Renders `Input` component for display name (populated with current value).
  - Renders `<textarea>` for bio (populated with current value, or empty if null).
  - Validates display name on blur and before save (non-empty, FR-008).
  - Shows inline validation error below the display name field if empty.
  - Renders "Save" (`Button variant="default"`) and "Cancel" (`Button variant="outline"`) buttons.
  - "Save" button is disabled when `isSaving` is true or validation fails.
  - "Save" calls `onSave({ display_name, bio })` with current form values.
  - "Cancel" calls `onCancel()` to discard changes.
- Email field is always read-only (displayed as text, not an input).
- Uses local `useState` for form field values; resets to profile data on cancel.

**Styling**:

```text
Form fields: Uses existing Input component styling
Labels: text-sm font-medium text-foreground
Read-only values: text-sm text-muted-foreground
Buttons: flex gap-2, mt-4
Validation error: text-xs text-destructive mt-1
```

---

### ProfileMetadata

**Location**: `frontend/src/components/profile/ProfileMetadata.tsx`
**Purpose**: Displays read-only account metadata (creation date, role) in a clean, non-editable format.

```typescript
interface ProfileMetadataProps {
  profile: UserProfile;                   // Current profile data
}

export function ProfileMetadata(props: ProfileMetadataProps): JSX.Element;
```

**Behavior**:

- Displays account creation date in a human-readable format (e.g., "Member since March 2026").
- Displays user role with a badge-style indicator.
- All fields are read-only with no edit controls.
- Gracefully handles null values (e.g., if `account_created_at` is null, shows "—" or omits the row).

**Styling**:

```text
Container: border-t border-border/60, pt-4, mt-4
Labels: text-xs uppercase tracking-wide text-muted-foreground
Values: text-sm text-foreground
Role badge: inline-flex px-2 py-0.5 rounded-full text-xs bg-primary/10 text-primary
```

---

## New Frontend Hook

### useProfile

**Location**: `frontend/src/hooks/useProfile.ts`
**Purpose**: React Query hook encapsulating profile data fetching, mutation, and cache management.

```typescript
interface UseProfileReturn {
  profile: UserProfile | null;            // Cached profile data
  isLoading: boolean;                     // Initial fetch in progress
  error: Error | null;                    // Fetch error
  updateProfile: (data: UserProfileUpdate) => Promise<void>;  // Update text fields
  uploadAvatar: (file: File) => Promise<void>;                // Upload avatar file
  isSaving: boolean;                      // Any mutation in progress
  saveError: Error | null;                // Most recent mutation error
}

export function useProfile(): UseProfileReturn;
```

**Behavior**:

- **Query**: `useQuery({ queryKey: ['profile'], queryFn: profileApi.getProfile })`.
- **Update mutation**: `useMutation({ mutationFn: profileApi.updateProfile, onSuccess: invalidate(['profile', ['auth', 'me']]) })`.
- **Avatar mutation**: `useMutation({ mutationFn: profileApi.uploadAvatar, onSuccess: invalidate(['profile', ['auth', 'me']]) })`.
- Cache invalidation on success ensures TopBar avatar and username update immediately.
- Exposes `isSaving` as `updateMutation.isPending || avatarMutation.isPending`.

---

## New Frontend API Functions

### profileApi

**Location**: Added to `frontend/src/services/api.ts`

```typescript
export const profileApi = {
  /** Fetch the authenticated user's profile */
  async getProfile(): Promise<UserProfile> {
    return request<UserProfile>('/users/profile');
  },
  
  /** Update profile text fields (display name, bio) */
  async updateProfile(data: UserProfileUpdate): Promise<UserProfile> {
    return request<UserProfile>('/users/profile', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },
  
  /** Upload a new avatar image */
  async uploadAvatar(file: File): Promise<UserProfile> {
    const formData = new FormData();
    formData.append('file', file);
    return request<UserProfile>('/users/profile/avatar', {
      method: 'POST',
      body: formData,
      // Note: Do NOT set Content-Type header — browser sets it with boundary
    });
  },
};
```

---

## New Backend Endpoints

### GET /api/v1/users/profile

**Location**: `backend/src/api/profile.py`
**Purpose**: Fetch the authenticated user's composite profile data.

**Request**: No body. Session cookie required.

**Response** (200):
```json
{
  "github_user_id": "string",
  "github_username": "string",
  "github_avatar_url": "string | null",
  "display_name": "string | null",
  "bio": "string | null",
  "avatar_url": "string | null",
  "account_created_at": "string | null",
  "role": "string"
}
```

**Error Responses**:
- 401: Not authenticated (no valid session cookie)

**Logic**:
1. Extract user session from cookie via `get_current_session`.
2. Query `user_profiles` table by `session.github_user_id`.
3. If row exists: merge session data with profile data, resolve avatar URL.
4. If no row: return session data with null profile fields, use GitHub avatar.

---

### PATCH /api/v1/users/profile

**Location**: `backend/src/api/profile.py`
**Purpose**: Update the authenticated user's editable profile fields.

**Request** (JSON):
```json
{
  "display_name": "string (optional, non-empty when provided)",
  "bio": "string (optional)"
}
```

**Response** (200): Same as GET response with updated fields.

**Error Responses**:
- 401: Not authenticated
- 422: Validation error (e.g., empty display_name)

**Logic**:
1. Extract user session from cookie.
2. Validate: if `display_name` is provided, it must be non-empty and ≤100 characters.
3. Validate: if `bio` is provided, it must be ≤500 characters.
4. Upsert `user_profiles` row (INSERT OR REPLACE).
5. Return composite profile response.

---

### POST /api/v1/users/profile/avatar

**Location**: `backend/src/api/profile.py`
**Purpose**: Upload a new avatar image for the authenticated user.

**Request**: `multipart/form-data` with `file` field.

**Response** (200): Same as GET response with updated `avatar_url`.

**Error Responses**:
- 401: Not authenticated
- 413: File too large (>5 MB)
- 422: Invalid file type (not PNG/JPG/WebP)

**Logic**:
1. Extract user session from cookie.
2. Validate file type (PNG, JPG, WebP) and size (≤5 MB).
3. Generate UUID-prefixed filename.
4. Delete previous avatar file if it exists.
5. Save file to `{data_path}/profile-avatars/`.
6. Upsert `user_profiles` row with new `avatar_path`.
7. Return composite profile response.

---

### GET /api/v1/users/profile/avatar/{filename}

**Location**: `backend/src/api/profile.py`
**Purpose**: Serve uploaded avatar files.

**Response** (200): Image file with appropriate Content-Type header.

**Error Responses**:
- 404: File not found

**Logic**:
1. Validate filename (no path traversal characters).
2. Resolve full path: `{data_path}/profile-avatars/{filename}`.
3. Return `FileResponse` with content type detected from extension.

---

## Modified Components

### App.tsx

**Location**: `frontend/src/App.tsx`
**Changes**: Add `/profile` route inside the AuthGate-protected layout.

```tsx
// Add to imports
import ProfilePage from '@/pages/ProfilePage';

// Add to routes (inside the authenticated layout children)
{ path: 'profile', element: <ProfilePage /> },
```

---

### TopBar.tsx

**Location**: `frontend/src/layout/TopBar.tsx`
**Changes**: Wrap the existing user avatar container with a `<Link to="/profile">` for navigation.

```tsx
// Before:
<div className="flex items-center gap-2 rounded-full border ...">
  {/* avatar + username */}
</div>

// After:
<Link to="/profile" className="flex items-center gap-2 rounded-full border ... hover:border-primary/50 transition-colors">
  {/* avatar + username */}
</Link>
```

---

### constants.ts

**Location**: `frontend/src/constants.ts`
**Changes**: Add profile route to `NAV_ROUTES` for sidebar navigation.

```typescript
import { User } from 'lucide-react';

// Add to NAV_ROUTES array:
{ path: '/profile', label: 'Profile', icon: User },
```

---

## New Backend Service

### profile_store.py

**Location**: `backend/src/services/profile_store.py`
**Purpose**: Database operations for the `user_profiles` table.

```python
class ProfileStore:
    """Manages user profile data persistence in SQLite."""
    
    async def ensure_table(self) -> None:
        """Create user_profiles table if not exists."""
    
    async def get_profile(self, github_user_id: str) -> UserProfile | None:
        """Fetch profile by GitHub user ID. Returns None if not found."""
    
    async def upsert_profile(self, github_user_id: str, update: UserProfileUpdate) -> UserProfile:
        """Create or update profile fields. Uses INSERT OR REPLACE."""
    
    async def update_avatar_path(self, github_user_id: str, avatar_path: str | None) -> None:
        """Update the avatar_path field for a user."""
```

**Behavior**:

- Table creation runs on first access (lazy initialization).
- `upsert_profile` preserves existing fields not included in the update.
- `update_avatar_path` is separate from `upsert_profile` because avatar upload is a distinct operation.
- All timestamp fields use ISO 8601 format consistent with existing tables.
