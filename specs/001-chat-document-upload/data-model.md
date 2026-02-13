# Data Model: Chat Document Upload

**Feature**: 001-chat-document-upload  
**Created**: 2026-02-13

## Entities

### 1. DocumentAttachment

Represents an uploaded document associated with a chat message.

**Fields**:
- `attachment_id` (string, UUID) - Unique identifier for the attachment
- `session_id` (string, UUID) - Session that owns this document
- `message_id` (string, UUID) - Chat message this document is attached to
- `filename` (string, max 255 chars) - Original filename from user's device
- `file_size` (integer) - File size in bytes (max 20,971,520 = 20MB)
- `file_type` (string) - MIME type (application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document, text/plain)
- `storage_path` (string) - Relative path to file in storage system (e.g., "uploads/{session_id}/{attachment_id}_{filename}")
- `uploaded_at` (string, ISO 8601) - Timestamp when upload completed
- `upload_status` (enum) - Current status: 'uploading' | 'completed' | 'failed'

**Relationships**:
- Belongs to one `ChatMessage` (via message_id)
- Belongs to one session (via session_id)

**Validation Rules**:
- filename must not contain path separators (/, \, ..)
- file_size must be > 0 and <= 20,971,520 bytes
- file_type must be one of the allowed MIME types
- storage_path must be unique across all attachments

**State Transitions**:
```
[Created] → uploading → completed
                     ↘ failed
```

### 2. ChatMessage (Extended)

Existing entity extended to support document attachments.

**New Fields**:
- `has_attachment` (boolean) - Flag indicating if message includes document
- `action_type` (enum) - Add new value 'document_upload' to existing values

**New Action Data Structure** (when action_type = 'document_upload'):
```typescript
{
  attachment_id: string
  filename: string
  file_size: number
  file_type: string
  uploaded_at: string
  download_url: string  // API endpoint: /api/chat/documents/{attachment_id}
}
```

**Relationships**:
- May have one `DocumentAttachment` (optional, via action_data.attachment_id)

### 3. UploadProgress (Client-Side Only)

Transient state tracked on frontend during upload process. Not persisted.

**Fields**:
- `upload_id` (string, UUID) - Temporary identifier for in-progress upload
- `filename` (string) - Name of file being uploaded
- `file_size` (number) - Total file size in bytes
- `bytes_uploaded` (number) - Bytes uploaded so far
- `percentage` (number) - Upload progress as percentage (0-100)
- `status` (enum) - 'validating' | 'uploading' | 'processing' | 'complete' | 'error'
- `error_message` (string, optional) - Error description if status is 'error'
- `xhr` (XMLHttpRequest, optional) - Reference to XHR object for cancellation

**Lifecycle**:
- Created when user selects file
- Updated during upload via XHR progress events
- Removed when upload completes or fails

## Storage Schema

### In-Memory Storage (MVP)

**Backend Data Structures** (Python):
```python
# In backend/src/api/chat.py
_documents: Dict[str, DocumentAttachment] = {}
# Key: attachment_id
# Value: DocumentAttachment object

# Updated structure
_messages: Dict[str, List[ChatMessage]] = {}
# Messages may now include action_type='document_upload' with attachment data
```

**Filesystem Structure**:
```
uploads/
├── {session_id_1}/
│   ├── {attachment_id_1}_{sanitized_filename}.pdf
│   ├── {attachment_id_2}_{sanitized_filename}.docx
│   └── {attachment_id_3}_{sanitized_filename}.txt
├── {session_id_2}/
│   └── {attachment_id_4}_{sanitized_filename}.pdf
└── .gitkeep
```

### Future Database Schema (When Migrating from MVP)

**Table: document_attachments**
```sql
CREATE TABLE document_attachments (
    attachment_id UUID PRIMARY KEY,
    session_id UUID NOT NULL,
    message_id UUID NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL CHECK (file_size > 0 AND file_size <= 20971520),
    file_type VARCHAR(100) NOT NULL,
    storage_path TEXT NOT NULL UNIQUE,
    uploaded_at TIMESTAMP NOT NULL DEFAULT NOW(),
    upload_status VARCHAR(20) NOT NULL DEFAULT 'uploading',
    
    -- Indexes for efficient queries
    INDEX idx_session_id (session_id),
    INDEX idx_message_id (message_id),
    INDEX idx_uploaded_at (uploaded_at)
);
```

## Data Flow

### Upload Flow

1. **User selects file** → Frontend validates (size, type)
2. **Validation passes** → Create UploadProgress state, display preview
3. **User clicks send** → Create FormData with file + session_id
4. **XHR upload starts** → Update UploadProgress.percentage via progress events
5. **Backend receives file** → Server-side validation (MIME type, size)
6. **Validation passes** → Save to filesystem, create DocumentAttachment record
7. **Create ChatMessage** → action_type='document_upload', action_data contains attachment metadata
8. **Return to frontend** → Update message list, remove UploadProgress state
9. **WebSocket broadcast** → Notify other participants of new document message

### Download Flow

1. **User clicks document link** → Frontend calls GET /api/chat/documents/{attachment_id}
2. **Backend verifies access** → Check if session_id matches document owner
3. **Access granted** → Return FileResponse with proper headers
4. **Browser handles download** → Based on Content-Disposition header

### Error Flow

1. **Validation fails** (client or server) → Create error message
2. **Show error to user** → Toast notification or inline message
3. **Clear UploadProgress** → Allow user to select different file
4. **Network error during upload** → Detect via XHR error event, show retry option
5. **Server error (500)** → Show generic error, log details on server

## Validation Rules

### Client-Side Validation

**Before Upload**:
- File size: Must be ≤ 20MB (20,971,520 bytes)
- File type: Must be PDF, DOCX, or TXT (based on file.type)
- Filename: Must not be empty

**During Upload**:
- Network connectivity: Detect disconnection
- Upload timeout: Abort if no progress for 60 seconds

### Server-Side Validation

**On Upload Endpoint**:
- Content-Type header: Must be multipart/form-data
- File size: Verify actual size ≤ 20MB (read chunks, count bytes)
- MIME type: Use python-magic to detect actual file type (not extension)
- Filename sanitization: Remove path separators, limit length
- Session authentication: Verify valid session_id

**MIME Type Mapping**:
- PDF: `application/pdf`
- DOCX: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- TXT: `text/plain`, `text/plain; charset=utf-8`

### Access Control

**Upload Permission**:
- User must have valid authenticated session
- No rate limit for MVP (add in production: 10 uploads/minute per session)

**Download Permission**:
- User must be participant in the conversation (session_id matches)
- Document must exist and upload_status must be 'completed'
- No public access to documents (all require authentication)

## Data Retention

**MVP Approach**:
- Documents persist until session is cleared
- When user clicks "Clear conversation", delete associated documents from filesystem
- No automatic cleanup (future enhancement: expire documents after 30 days)

**Future Production**:
- Soft delete: Mark documents as deleted, keep for 30 days
- Archive old documents to cold storage (Azure Archive tier)
- Cleanup job: Delete expired documents nightly
- Audit log: Track all document access for security

## Indexing Strategy

**In-Memory (MVP)**:
- Simple dictionary lookups by attachment_id: O(1)
- Filter messages by session_id: O(n) scan (acceptable for MVP)

**Database (Future)**:
- Primary key: attachment_id (UUID) → clustered index
- Foreign key indexes: session_id, message_id → non-clustered indexes
- Uploaded_at index → for cleanup queries

## Pydantic Models

```python
from pydantic import BaseModel, Field, validator
from typing import Literal, Optional
from datetime import datetime
import re

class DocumentAttachment(BaseModel):
    attachment_id: str
    session_id: str
    message_id: str
    filename: str = Field(..., max_length=255)
    file_size: int = Field(..., ge=1, le=20_971_520)
    file_type: Literal[
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    ]
    storage_path: str
    uploaded_at: str
    upload_status: Literal["uploading", "completed", "failed"] = "uploading"
    
    @validator('filename')
    def validate_filename(cls, v):
        if any(char in v for char in ['/', '\\', '..']):
            raise ValueError('Filename must not contain path separators')
        return v

class DocumentAttachmentData(BaseModel):
    """Action data for document_upload messages"""
    attachment_id: str
    filename: str
    file_size: int
    file_type: str
    uploaded_at: str
    download_url: str
```

## TypeScript Types

```typescript
interface DocumentAttachment {
  attachment_id: string;
  session_id: string;
  message_id: string;
  filename: string;
  file_size: number;
  file_type: 'application/pdf' | 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' | 'text/plain';
  storage_path: string;
  uploaded_at: string;
  upload_status: 'uploading' | 'completed' | 'failed';
}

interface DocumentAttachmentData {
  attachment_id: string;
  filename: string;
  file_size: number;
  file_type: string;
  uploaded_at: string;
  download_url: string;
}

// Extend existing ChatMessage type
interface ChatMessage {
  message_id: string;
  session_id: string;
  sender_type: 'user' | 'assistant' | 'system';
  content: string;
  action_type?: 'task_create' | 'status_update' | 'issue_create' | 'project_select' | 'document_upload';
  action_data?: TaskProposalData | StatusChangeData | IssueCreateData | DocumentAttachmentData;
  timestamp: string;
  has_attachment?: boolean;
}

interface UploadProgress {
  upload_id: string;
  filename: string;
  file_size: number;
  bytes_uploaded: number;
  percentage: number;
  status: 'validating' | 'uploading' | 'processing' | 'complete' | 'error';
  error_message?: string;
  xhr?: XMLHttpRequest;
}
```
