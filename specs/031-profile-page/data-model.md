# Data Model: Add Profile Page to App

**Feature**: 031-profile-page | **Date**: 2026-03-09

## Backend Models (Python/Pydantic)

### UserProfile (New)

```python
class UserProfile(BaseModel):
    """Persistent user profile data, independent of session lifecycle.
    Stores user-editable identity fields and custom avatar reference."""
    
    github_user_id: str                    # Primary key, from GitHub OAuth
    display_name: str | None = None        # User-set display name (overrides github_username)
    bio: str | None = None                 # Short user biography
    avatar_path: str | None = None         # Relative path to custom avatar file (None = use GitHub avatar)
    created_at: datetime                   # Profile creation timestamp
    updated_at: datetime                   # Last profile update timestamp
```

### UserProfileUpdate (New)

```python
class UserProfileUpdate(BaseModel):
    """Partial update payload for user profile fields.
    Only provided fields are updated; None fields are ignored."""
    
    display_name: str | None = None        # New display name (non-empty when provided)
    bio: str | None = None                 # New bio text
```

### UserProfileResponse (New)

```python
class UserProfileResponse(BaseModel):
    """Composite profile response merging GitHub OAuth data with user-set profile data.
    Returned by GET /api/v1/users/profile."""
    
    # GitHub-sourced (read-only)
    github_user_id: str                    # GitHub user ID
    github_username: str                   # GitHub username (login)
    github_avatar_url: str | None = None   # GitHub avatar URL (default avatar source)
    
    # User-editable
    display_name: str | None = None        # Custom display name (None = use github_username)
    bio: str | None = None                 # User biography
    avatar_url: str | None = None          # Resolved avatar URL (custom upload or GitHub fallback)
    
    # Read-only metadata
    account_created_at: str | None = None  # ISO 8601 timestamp of first profile creation
    role: str = "member"                   # User role (default: "member")
```

### Existing Model References

```python
# backend/src/models/user.py (existing, unchanged)
class UserSession(BaseModel):
    session_id: UUID
    github_user_id: str
    github_username: str
    github_avatar_url: str | None
    access_token: str                      # Encrypted
    refresh_token: str | None              # Encrypted
    token_expires_at: datetime | None
    selected_project_id: str | None
    created_at: datetime
    updated_at: datetime

class UserResponse(BaseModel):
    github_user_id: str
    github_username: str
    github_avatar_url: str | None = None
    selected_project_id: str | None = None
```

---

## Frontend Types (TypeScript)

### Profile Types (New)

```typescript
/**
 * Composite profile data returned by GET /api/v1/users/profile.
 * Merges GitHub OAuth data with user-editable profile fields.
 */
export interface UserProfile {
  // GitHub-sourced (read-only)
  github_user_id: string;
  github_username: string;
  github_avatar_url: string | null;
  
  // User-editable
  display_name: string | null;           // Custom display name (null = use github_username)
  bio: string | null;                    // User biography
  avatar_url: string | null;             // Resolved avatar URL (custom or GitHub fallback)
  
  // Read-only metadata
  account_created_at: string | null;     // ISO 8601 timestamp
  role: string;                          // User role (e.g., "member")
}

/**
 * Payload for PATCH /api/v1/users/profile.
 * Only provided fields are updated.
 */
export interface UserProfileUpdate {
  display_name?: string;                 // Non-empty when provided
  bio?: string;                          // Can be empty string to clear
}

/**
 * Form state for the profile edit mode.
 * Tracks local edits before save/cancel.
 */
export interface ProfileFormState {
  displayName: string;                   // Current edit value
  bio: string;                           // Current edit value
  avatarFile: File | null;               // Selected file for upload (null = no change)
  avatarPreview: string | null;          // Object URL for client-side preview
  isDirty: boolean;                      // True if any field has been modified
  isEditing: boolean;                    // True when in edit mode
}

/**
 * Validation result for profile form fields.
 */
export interface ProfileValidation {
  displayName: string | null;            // Error message or null if valid
  avatar: string | null;                 // Error message or null if valid
}
```

### Avatar Validation Constants

```typescript
/** Maximum avatar file size in bytes (5 MB) */
export const MAX_AVATAR_SIZE = 5 * 1024 * 1024;

/** Accepted avatar MIME types */
export const ACCEPTED_AVATAR_TYPES = ['image/png', 'image/jpeg', 'image/webp'];

/** Accepted avatar file extensions (for display) */
export const ACCEPTED_AVATAR_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.webp'];
```

---

## Database Schema

### New Table: `user_profiles`

```sql
CREATE TABLE IF NOT EXISTS user_profiles (
    github_user_id TEXT PRIMARY KEY,
    display_name TEXT,
    bio TEXT,
    avatar_path TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_user_profiles_updated 
    ON user_profiles(updated_at);
```

**Column Details**:

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `github_user_id` | TEXT | NO (PK) | GitHub user ID from OAuth, matches `user_sessions.github_user_id` |
| `display_name` | TEXT | YES | User-set display name; NULL means use `github_username` |
| `bio` | TEXT | YES | Short biography text; NULL means not set |
| `avatar_path` | TEXT | YES | Relative path to uploaded avatar in `profile-avatars/` directory; NULL means use GitHub avatar |
| `created_at` | TEXT | NO | ISO 8601 timestamp of first profile creation |
| `updated_at` | TEXT | NO | ISO 8601 timestamp of last profile update |

**Relationships**:

```text
user_sessions.github_user_id  ──── 1:0..1 ────  user_profiles.github_user_id
```

A user may have zero or one profile row. Profile is created lazily on first edit (not on login).

---

## State Machines

### Profile Edit Lifecycle

```text
                    ┌────────────┐
                    │   VIEWING   │  Read-only display mode
                    └──────┬─────┘
                           │
                     User clicks "Edit"
                           │
                           ▼
                    ┌────────────┐
                    │  EDITING   │  Form fields editable
                    │  (dirty?)  │  isDirty tracks changes
                    └──────┬─────┘
                           │
              ┌────────────┼────────────┐
              │                         │
        User clicks             User clicks
         "Save"                  "Cancel"
              │                         │
              ▼                         ▼
       ┌────────────┐           ┌────────────┐
       │   SAVING   │           │  VIEWING   │  Restore original values
       │ (loading)  │           │  (reset)   │
       └──────┬─────┘           └────────────┘
              │
     ┌────────┼────────┐
     │                  │
   Success            Error
     │                  │
     ▼                  ▼
┌────────────┐   ┌────────────┐
│  VIEWING   │   │  EDITING   │  Show error notification
│ (updated)  │   │  (error)   │  Keep form values
│ + toast    │   │  + toast   │
└────────────┘   └────────────┘
```

### Avatar Upload Flow

```text
User clicks avatar area
        │
        ▼
  File picker opens
        │
        ├── User cancels → No change
        │
        └── User selects file
                │
                ▼
        ┌──────────────┐
        │  VALIDATING   │
        └──────┬───────┘
               │
      ┌────────┼────────┐
      │                  │
   Valid              Invalid
   (type + size)     (wrong type or too large)
      │                  │
      ▼                  ▼
┌────────────┐    ┌────────────┐
│  PREVIEWING │    │   ERROR    │  Show validation error
│  (local)   │    │  (message) │  No file selected
└──────┬─────┘    └────────────┘
       │
       │  (User clicks Save on profile form)
       │
       ▼
┌────────────┐
│  UPLOADING  │  POST /api/v1/users/profile/avatar
└──────┬─────┘
       │
  ┌────┼────┐
  │         │
Success   Error
  │         │
  ▼         ▼
Updated   Keep preview,
avatar    show error,
URL       allow retry
```

### Profile Data Resolution

```text
GET /api/v1/users/profile request
        │
        ▼
  Load user session (from cookie)
        │
        ▼
  Query user_profiles by github_user_id
        │
        ├── Row exists → Merge session + profile data
        │       │
        │       ├── avatar_path set? → avatar_url = /api/v1/users/profile/avatar/{filename}
        │       │
        │       └── avatar_path null? → avatar_url = session.github_avatar_url
        │
        └── No row → Return session data only
                │
                ├── display_name = null (frontend uses github_username)
                ├── bio = null
                └── avatar_url = session.github_avatar_url
```

---

## File Storage

### Avatar Storage Directory

```text
{data_path}/
└── profile-avatars/
    ├── {uuid}_{original_filename}.png
    ├── {uuid}_{original_filename}.jpg
    └── {uuid}_{original_filename}.webp
```

- **Location**: `{data_path}/profile-avatars/` where `data_path` is from backend config (default: `/var/lib/ghchat/data/`)
- **Naming**: `{uuid4}_{sanitized_original_filename}` — UUID prefix prevents collisions and path traversal
- **Cleanup**: Previous avatar file is deleted when a new one is uploaded
- **Permissions**: Same as existing data directory (0o700 directory, 0o600 files)

---

## API Response Examples

### GET /api/v1/users/profile (with custom profile)

```json
{
  "github_user_id": "12345",
  "github_username": "octocat",
  "github_avatar_url": "https://avatars.githubusercontent.com/u/12345",
  "display_name": "The Octocat",
  "bio": "I love open source and building great software.",
  "avatar_url": "/api/v1/users/profile/avatar/a1b2c3d4_avatar.png",
  "account_created_at": "2026-03-09T01:43:59Z",
  "role": "member"
}
```

### GET /api/v1/users/profile (no custom profile)

```json
{
  "github_user_id": "12345",
  "github_username": "octocat",
  "github_avatar_url": "https://avatars.githubusercontent.com/u/12345",
  "display_name": null,
  "bio": null,
  "avatar_url": "https://avatars.githubusercontent.com/u/12345",
  "account_created_at": null,
  "role": "member"
}
```

### PATCH /api/v1/users/profile

```json
// Request
{
  "display_name": "The Octocat",
  "bio": "I love open source."
}

// Response (same as GET response with updated fields)
{
  "github_user_id": "12345",
  "github_username": "octocat",
  "github_avatar_url": "https://avatars.githubusercontent.com/u/12345",
  "display_name": "The Octocat",
  "bio": "I love open source.",
  "avatar_url": "https://avatars.githubusercontent.com/u/12345",
  "account_created_at": "2026-03-09T01:43:59Z",
  "role": "member"
}
```
