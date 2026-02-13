# Research: Profile Picture Upload

**Feature**: Profile Picture Upload  
**Date**: 2026-02-13  
**Status**: Complete

## Research Questions

This document resolves all "NEEDS CLARIFICATION" items from the Technical Context section of plan.md.

---

## 1. Storage Approach

**Question**: Should we use local file system storage or cloud storage (AWS S3, Azure Blob) for profile pictures?

**Decision**: Local file system storage

**Rationale**:
- The application currently uses in-memory storage for MVP (chat messages, sessions, workflow configs)
- No existing cloud storage infrastructure is configured (no S3/Azure credentials in .env.example)
- No volume mounts in docker-compose.yml
- Local storage aligns with the MVP approach and simplicity principles (Constitution V)
- Sufficient for the expected scale (100 concurrent uploads per SC-006)
- Can be migrated to cloud storage later without changing the API contract

**Alternatives Considered**:
- **AWS S3**: Rejected because it adds complexity and cost without immediate benefit for MVP scale
- **Azure Blob Storage**: Rejected for same reasons as S3; no Azure storage credentials exist in config
- **GitHub as storage**: Rejected because profile pictures should not be in git repository

**Implementation**:
- Store files in `/backend/storage/profile-pictures/` directory
- Use user ID as filename prefix to avoid collisions: `{user_id}_{timestamp}.{ext}`
- Add volume mount to docker-compose.yml for persistence: `./storage:/app/storage`
- Serve files via FastAPI static file endpoint or direct file streaming

---

## 2. Image Processing and Security

**Question**: What image processing and security measures are needed for profile picture uploads?

**Decision**: Use Pillow (PIL) for validation and optional processing

**Rationale**:
- Pillow is the standard Python library for image processing
- Can validate that uploaded files are actually valid JPEG/PNG (not just checking extension)
- Can extract image metadata to verify format and dimensions
- Can sanitize images by re-encoding them (removes EXIF data and potential exploits)
- Lightweight and widely used in Python web applications
- Already compatible with FastAPI file upload handling

**Alternatives Considered**:
- **ImageMagick**: More powerful but requires external binary and is overkill for simple validation
- **Extension-only validation**: Rejected due to security concerns (users could rename malicious files)
- **No processing**: Rejected because we need to ensure uploaded files are valid images

**Security Measures**:
1. **Validate file format**: Use Pillow to open and verify the image is valid JPEG/PNG
2. **Check file size**: Validate 5MB limit before processing (from request headers)
3. **Re-encode images**: Optional sanitization by re-saving with Pillow (removes EXIF, strips metadata)
4. **Unique filenames**: Prevent path traversal attacks by generating server-side filenames
5. **Content-Type validation**: Verify Content-Type header matches actual file format
6. **Rate limiting**: Prevent abuse by limiting uploads per user (use existing cache mechanism)

---

## 3. File Upload Best Practices

**Question**: What are the best practices for handling file uploads in FastAPI?

**Decision**: Use FastAPI's `UploadFile` with streaming and chunked processing

**Rationale**:
- `UploadFile` is FastAPI's recommended approach (uses Python's SpooledTemporaryFile)
- Handles large files efficiently without loading entire file into memory
- Provides async file operations compatible with FastAPI's async nature
- Includes metadata (filename, content_type) needed for validation

**Implementation Pattern**:
```python
from fastapi import File, UploadFile
from PIL import Image

@router.post("/profile/picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: UserSession = Depends(get_current_user)
):
    # 1. Validate size from headers
    # 2. Read file content
    # 3. Validate with Pillow
    # 4. Save to storage
    # 5. Update user model
    # 6. Return URL
```

**Alternatives Considered**:
- **Form data with bytes**: Less efficient for large files
- **Multipart/form-data only**: `UploadFile` already handles this properly
- **Direct binary upload**: Less convenient for browser-based uploads

---

## 4. Frontend File Upload Approach

**Question**: What frontend approach should we use for file selection and preview?

**Decision**: Use HTML5 File API with FileReader for preview

**Rationale**:
- Native browser API, no additional dependencies required
- FileReader.readAsDataURL() provides instant client-side preview
- File input `accept` attribute provides OS-level filtering for JPEG/PNG
- Client-side size validation prevents unnecessary upload attempts
- Compatible with React and can be wrapped in a custom hook

**Implementation Pattern**:
```typescript
// Custom hook for file upload
const useProfilePictureUpload = () => {
  const [preview, setPreview] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate size
      if (file.size > 5 * 1024 * 1024) {
        // Error handling
        return;
      }
      setFile(file);
      
      // Generate preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };
  
  return { preview, file, handleFileSelect };
};
```

**Alternatives Considered**:
- **Third-party libraries** (react-dropzone, react-image-crop): Rejected to minimize dependencies
- **Drag-and-drop**: Out of scope for P1, can be added later
- **Webcam capture**: Out of scope, not mentioned in requirements

---

## 5. Image Display Strategy

**Question**: How should we efficiently display profile pictures across the application?

**Decision**: Create a shared Avatar component that checks for profile picture existence

**Rationale**:
- Current UserSession model already has `github_avatar_url` field
- Can add `profile_picture_url` field to store custom profile pictures
- Avatar component checks profile_picture_url first, falls back to github_avatar_url
- Consistent display pattern across all UI locations (header, comments, etc.)
- No need to modify every component individually

**Implementation Pattern**:
```typescript
interface AvatarProps {
  user: UserResponse;
  size?: 'sm' | 'md' | 'lg';
}

const Avatar: React.FC<AvatarProps> = ({ user, size = 'md' }) => {
  const imageUrl = user.profile_picture_url || user.github_avatar_url;
  const defaultAvatar = '/default-avatar.png';
  
  return (
    <img 
      src={imageUrl || defaultAvatar}
      alt={`${user.github_username}'s profile`}
      className={`avatar-${size}`}
      onError={(e) => { e.currentTarget.src = defaultAvatar; }}
    />
  );
};
```

**Alternatives Considered**:
- **Replace github_avatar_url field**: Rejected because we want to preserve GitHub avatar as fallback
- **Separate profile component**: Rejected to maintain DRY principle
- **CSS background images**: Rejected because img tags are more accessible and handle loading states better

---

## 6. Testing Strategy

**Question**: What testing approach should be used for file upload functionality?

**Decision**: Multi-layer testing with unit, integration, and E2E tests

**Rationale**:
- File uploads involve multiple layers (validation, storage, API, UI)
- Critical security and validation logic requires thorough testing
- Aligns with existing test infrastructure (pytest, vitest, Playwright)

**Test Coverage**:

**Backend (pytest)**:
- File validation logic (format, size)
- Pillow image processing
- Storage service (save, delete, retrieve)
- API endpoint behavior (success, error cases)
- Mock file uploads using BytesIO

**Frontend (vitest)**:
- useProfilePicture hook logic
- File selection and validation
- Preview generation
- State management
- Mock File and FileReader APIs

**E2E (Playwright)**:
- End-to-end upload flow
- Preview display
- Success confirmation
- Error handling
- Cross-browser compatibility

**Alternatives Considered**:
- **No tests**: Rejected due to security implications and Constitution IV guidance
- **Unit tests only**: Insufficient for file upload which requires integration testing
- **E2E tests only**: Too slow for development feedback loop

---

## Summary

All "NEEDS CLARIFICATION" items from Technical Context have been resolved:

| Item | Resolution |
|------|-----------|
| **Storage** | Local file system (`/backend/storage/profile-pictures/`) |
| **Image Processing** | Pillow library for validation and sanitization |
| **File Upload** | FastAPI `UploadFile` with streaming |
| **Frontend Approach** | HTML5 File API with FileReader for preview |
| **Display Strategy** | Shared Avatar component with fallback logic |
| **Testing** | Multi-layer approach (unit, integration, E2E) |

**Dependencies to Add**:
- Backend: `Pillow>=10.0.0` for image processing
- Frontend: No new dependencies required (use native browser APIs)

**Configuration to Add**:
- `.env`: `STORAGE_PATH=./storage` (with default)
- `docker-compose.yml`: Volume mount for persistence
- `.gitignore`: Add `/backend/storage/` to exclude uploaded files from git
