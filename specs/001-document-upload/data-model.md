# Data Model: Document Upload Feature

**Feature**: Document Upload in Chat  
**Date**: 2026-02-13  
**Source**: spec.md functional requirements + research.md decisions

## Core Entities

### 1. Document

Represents an uploaded file stored in the system.

**Fields**:
- `document_id`: UUID - Unique identifier for the document
- `original_filename`: str - Original name of the uploaded file
- `stored_filename`: str - Unique name used for storage (prevents conflicts)
- `file_size`: int - Size in bytes (max 25MB = 26,214,400 bytes)
- `mime_type`: str - MIME type (validated via magic numbers)
- `file_extension`: str - Original extension (.pdf, .docx, .txt, .xlsx, .pptx)
- `storage_path`: str - Relative path to stored file (e.g., "uploads/{user_id}/{stored_filename}")
- `upload_timestamp`: datetime - When file was uploaded (UTC)
- `uploader_user_id`: str - GitHub user ID of uploader
- `project_id`: int - GitHub project ID this document belongs to
- `validation_status`: str - Validation result ("valid", "pending", "invalid")

**Constraints**:
- `file_size` must be <= 26,214,400 bytes (25MB)
- `mime_type` must be one of:
  - "application/pdf"
  - "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
  - "text/plain"
  - "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
  - "application/vnd.openxmlformats-officedocument.presentationml.presentation"
- `file_extension` must be one of: ".pdf", ".docx", ".txt", ".xlsx", ".pptx"
- `stored_filename` should be unique: "{uuid}_{original_filename}"

**Relationships**:
- Belongs to one Project (via `project_id`)
- Created by one User (via `uploader_user_id`)
- Referenced by zero or more DocumentMessages

**Example**:
```json
{
  "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "original_filename": "Q4_Report.pdf",
  "stored_filename": "a1b2c3d4-e5f6-7890-abcd-ef1234567890_Q4_Report.pdf",
  "file_size": 2457600,
  "mime_type": "application/pdf",
  "file_extension": ".pdf",
  "storage_path": "uploads/github_user_123/a1b2c3d4-e5f6-7890-abcd-ef1234567890_Q4_Report.pdf",
  "upload_timestamp": "2026-02-13T15:30:00Z",
  "uploader_user_id": "github_user_123",
  "project_id": 456789,
  "validation_status": "valid"
}
```

---

### 2. DocumentMessage

Represents a chat message that contains a document reference.

**Fields**:
- `message_id`: UUID - Unique identifier for the message
- `document_id`: UUID - Reference to Document entity (foreign key)
- `sender_user_id`: str - GitHub user ID of sender
- `project_id`: int - GitHub project ID where message was sent
- `message_timestamp`: datetime - When message was sent (UTC)
- `message_text`: str | None - Optional text accompanying the document
- `message_type`: str - Always "document" for document messages

**Constraints**:
- `document_id` must reference valid Document
- `message_type` must be "document"
- `sender_user_id` should match Document's `uploader_user_id` (typically)

**Relationships**:
- References one Document (via `document_id`)
- Belongs to one Project (via `project_id`)
- Sent by one User (via `sender_user_id`)

**Example**:
```json
{
  "message_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "sender_user_id": "github_user_123",
  "project_id": 456789,
  "message_timestamp": "2026-02-13T15:30:05Z",
  "message_text": "Here's the Q4 report for review",
  "message_type": "document"
}
```

---

### 3. DownloadToken

Represents a temporary, time-limited token for secure file downloads.

**Fields**:
- `token_id`: str - Unique random token (32-byte URL-safe string)
- `session_id`: UUID - User session ID this token is tied to
- `document_id`: UUID - Reference to Document being downloaded
- `created_at`: datetime - When token was generated (UTC)
- `expires_at`: datetime - When token expires (UTC, typically 15 minutes)
- `used_at`: datetime | None - When token was used (for single-use enforcement)
- `is_used`: bool - Whether token has been consumed (single-use flag)

**Constraints**:
- `token_id` must be cryptographically random (secrets.token_urlsafe)
- `expires_at` must be > `created_at`
- Token expires after 15 minutes (configurable)
- Token becomes invalid if session expires

**Relationships**:
- Tied to one Session (via `session_id`)
- References one Document (via `document_id`)

**Lifecycle**:
1. Created when user requests download
2. Validated when user accesses download URL
3. Expired after 15 minutes or when used (if single-use)
4. Cleaned up when session ends

**Example**:
```json
{
  "token_id": "x7Y2mK9pQwE8RtL4sN6vH3jF1dC5aZ0b",
  "session_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "created_at": "2026-02-13T15:45:00Z",
  "expires_at": "2026-02-13T16:00:00Z",
  "used_at": null,
  "is_used": false
}
```

---

## Entity Relationships

```
User (GitHub user)
  ├── uploads Document(s)
  ├── sends DocumentMessage(s)
  └── has Session
       └── generates DownloadToken(s)

Project (GitHub project)
  ├── contains Document(s)
  └── contains DocumentMessage(s)

Document
  ├── uploaded by User
  ├── belongs to Project
  ├── referenced by DocumentMessage(s)
  └── accessible via DownloadToken(s)

DocumentMessage
  ├── sent by User
  ├── references Document
  └── belongs to Project

DownloadToken
  ├── tied to Session
  └── grants access to Document
```

---

## State Transitions

### Document Lifecycle

```
[User selects file] → [Client validates size/type] → [Upload starts]
                                     ↓
                          [Backend receives file]
                                     ↓
                          [Validate extension + MIME]
                                     ↓
                          [Stream to storage]
                                     ↓
                          [Create Document entity]
                                     ↓
                          [Create DocumentMessage]
                                     ↓
                          [Return to client]
                                     ↓
                          [Display in chat]
```

### Download Token Lifecycle

```
[User clicks download] → [Request token] → [Generate token]
                                               ↓
                                    [Store with 15min expiry]
                                               ↓
                                    [Return token to client]
                                               ↓
                                    [Client requests file]
                                               ↓
                                    [Validate token + session]
                                               ↓
                                    [Mark as used (optional)]
                                               ↓
                                    [Serve file]
```

---

## Storage Considerations

### In-Memory Storage (MVP)

Following existing codebase pattern (see `services/cache.py`, `services/github_auth.py`):

```python
# In-memory dictionaries
_documents: dict[UUID, Document] = {}
_document_messages: dict[UUID, DocumentMessage] = {}
_download_tokens: dict[str, DownloadToken] = {}
```

**Limitations**:
- Data lost on server restart
- Not suitable for multi-instance deployment
- No persistence between sessions

**Future Migration** (when needed):
- PostgreSQL for Document/DocumentMessage entities
- Redis for DownloadToken caching
- No code changes in endpoints (only service layer)

### File System Storage

```
backend/uploads/
├── {user_id_1}/
│   ├── {uuid1}_{filename1.pdf}
│   ├── {uuid2}_{filename2.docx}
│   └── ...
├── {user_id_2}/
│   └── ...
└── .gitignore (exclude from version control)
```

---

## Validation Rules

### File Upload Validation

1. **Size**: Max 26,214,400 bytes (25MB)
   - Validated client-side before upload
   - Validated server-side during upload stream

2. **Type**: Only 5 allowed types
   - Extension: `.pdf`, `.docx`, `.txt`, `.xlsx`, `.pptx`
   - MIME type: Must match expected MIME for extension
   - Magic numbers: File header must match MIME type

3. **Filename**: Sanitization required
   - Remove path separators (`/`, `\`)
   - Limit length to 255 characters
   - Preserve original for display, use UUID for storage

### Download Authorization

1. **Session**: User must have active session
2. **Token**: Valid, non-expired download token required
3. **Ownership**: Token must belong to requesting session
4. **Project Access**: User must have access to project (future enhancement)

---

## Performance Considerations

### Document Entity

- Metadata-only entity (no file content)
- Fast lookups by `document_id` (O(1) in dict)
- File I/O is async (doesn't block)

### DocumentMessage Entity

- Lightweight reference to Document
- Displayed in chat like regular messages
- Includes file metadata for display without disk access

### DownloadToken Entity

- Short-lived (15 minutes)
- Cleanup on expiration or session end
- Indexed by `token_id` for O(1) validation

**Estimated Sizes**:
- Document metadata: ~500 bytes
- DocumentMessage: ~300 bytes
- DownloadToken: ~200 bytes
- File storage: Actual file size (up to 25MB)

**Capacity Estimates** (for 1000 concurrent users):
- Documents: ~1-2 MB in memory
- Messages: ~500 KB in memory
- Tokens: ~200 KB in memory
- Files: Depends on usage (e.g., 10 files/user = 250GB storage)
