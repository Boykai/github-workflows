# Research: Chat Document Upload

**Date**: 2026-02-13
**Feature**: 001-chat-document-upload

## Technology Decisions

### 1. File Storage Solution: Local Filesystem with S3-compatible Interface

**Decision**: Use local filesystem for MVP with structure ready for S3/Azure Blob migration

**Rationale**:
- Current architecture uses in-memory storage for MVP; filesystem aligns with this pattern
- Avoids additional cloud service dependencies for initial release
- Structure code with abstraction layer to enable seamless migration to cloud storage
- Local uploads directory can be volume-mounted in Docker for persistence
- Supports development/testing without external service configuration

**Alternatives Considered**:
- Azure Blob Storage: Rejected for MVP - requires Azure account, additional billing, external dependency
- AWS S3: Rejected for MVP - same concerns as Azure Blob
- Database BLOB storage: Rejected - inefficient for large files, complicates backup/restore

**Implementation Pattern**:
```python
# Storage service abstraction
class DocumentStorage(ABC):
    async def save_file(self, file: UploadFile, session_id: str) -> str: ...
    async def get_file(self, file_path: str) -> bytes: ...
    async def delete_file(self, file_path: str) -> bool: ...

# MVP implementation
class LocalFileStorage(DocumentStorage):
    def __init__(self, base_path: Path = Path("./uploads")):
        self.base_path = base_path
        self.base_path.mkdir(exist_ok=True)
    
    async def save_file(self, file: UploadFile, session_id: str) -> str:
        # Save to uploads/{session_id}/{secure_filename}
        # Return relative path for storage in message
```

### 2. File Upload: Multipart Form Data with FastAPI

**Decision**: Use FastAPI's `UploadFile` for handling multipart/form-data uploads

**Rationale**:
- Native FastAPI support with built-in streaming for large files
- Automatic MIME type detection via `python-magic` or fallback to content-type header
- Memory-efficient streaming writes to disk (doesn't load entire file into RAM)
- Supports async file operations for non-blocking uploads
- Built-in validation via Pydantic models

**Key Patterns from FastAPI Best Practices**:
```python
from fastapi import UploadFile, File, HTTPException
from typing import Annotated

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
ALLOWED_TYPES = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"}

@router.post("/chat/upload")
async def upload_document(
    file: Annotated[UploadFile, File()],
    session_id: str = Depends(get_session_id)
):
    # Validate file size by reading in chunks
    size = 0
    file.file.seek(0)
    for chunk in iter(lambda: file.file.read(8192), b''):
        size += len(chunk)
        if size > MAX_FILE_SIZE:
            raise HTTPException(413, "File size exceeds 20MB limit")
    file.file.seek(0)
    
    # Validate MIME type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, "File type not supported")
```

**Alternatives Considered**:
- Base64 encoding in JSON: Rejected - inefficient, 33% size overhead, payload size limits
- Direct binary upload: Rejected - requires custom parsing, no metadata in same request

### 3. Frontend Upload: FormData with Progress Tracking

**Decision**: Use native `FormData` API with `XMLHttpRequest` for progress events

**Rationale**:
- `XMLHttpRequest.upload.onprogress` provides real-time upload progress (Fetch API doesn't)
- FormData automatically handles multipart/form-data encoding
- Browser handles file reading and chunking efficiently
- No additional libraries needed for basic upload functionality
- Works with existing authentication cookie mechanism

**Key Patterns**:
```typescript
// Upload with progress tracking
async function uploadDocument(file: File, sessionId: string, onProgress: (percent: number) => void): Promise<UploadResponse> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);
    
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        const percent = Math.round((e.loaded / e.total) * 100);
        onProgress(percent);
      }
    });
    
    xhr.addEventListener('load', () => {
      if (xhr.status === 200) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        reject(new Error(`Upload failed: ${xhr.status}`));
      }
    });
    
    xhr.addEventListener('error', () => reject(new Error('Network error')));
    xhr.open('POST', '/api/chat/upload');
    xhr.withCredentials = true;  // Include auth cookies
    xhr.send(formData);
  });
}
```

**Alternatives Considered**:
- React Dropzone library: Rejected - adds dependency, unnecessary for simple file input
- Uppy.js: Rejected - too heavy, more features than needed
- Fetch API: Rejected - no native progress tracking (requires manual chunking or streams)

### 4. File Validation: Client + Server Dual Validation

**Decision**: Implement validation at both client and server levels

**Rationale**:
- Client-side validation provides immediate feedback (better UX, no network round-trip)
- Server-side validation is security critical (never trust client)
- Use `python-magic` on server for true MIME type detection (not just file extension)
- Client checks file.type and file.size before upload attempt

**Client Validation**:
```typescript
const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.txt'];
const ALLOWED_MIME_TYPES = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
const MAX_SIZE = 20 * 1024 * 1024;

function validateFile(file: File): { valid: boolean; error?: string } {
  if (file.size > MAX_SIZE) {
    return { valid: false, error: 'File size exceeds 20MB limit' };
  }
  
  if (!ALLOWED_MIME_TYPES.includes(file.type)) {
    return { valid: false, error: 'File type not supported. Please upload PDF, DOCX, or TXT files' };
  }
  
  return { valid: true };
}
```

**Server Validation** (using python-magic):
```python
import magic

def validate_file_type(file_path: Path) -> bool:
    mime = magic.from_file(str(file_path), mime=True)
    return mime in ALLOWED_MIME_TYPES
```

**Alternatives Considered**:
- Extension-only validation: Rejected - easily spoofed, security risk
- Client-only validation: Rejected - bypassed by malicious users
- Server-only validation: Rejected - poor UX, wasted bandwidth on invalid uploads

### 5. Message Model Extension: Action Data for File Attachments

**Decision**: Extend existing `ChatMessage.action_data` to support document attachments

**Rationale**:
- Maintains consistency with existing chat architecture (proposals, status updates)
- `action_data` is already a flexible dict field supporting various action types
- No breaking changes to existing message structure
- Frontend already handles action_data rendering for different action_types
- Supports both text-only and text+attachment messages

**Data Model Extension**:
```python
# New action_type value
action_type: Literal['task_create', 'status_update', 'issue_create', 'project_select', 'document_upload']

# New action_data structure for documents
DocumentAttachmentData(BaseModel):
    attachment_id: str  # UUID
    filename: str
    file_size: int  # bytes
    file_type: str  # MIME type
    uploaded_at: str  # ISO timestamp
    storage_path: str  # relative path in storage
    download_url: str  # API endpoint for retrieval
```

**Alternatives Considered**:
- New DocumentMessage model: Rejected - duplicates fields, breaks existing chat flow
- Separate attachments table: Rejected - over-engineering for MVP with in-memory storage
- Embed file content in message: Rejected - bloats message size, memory concerns

### 6. Download Strategy: Signed URLs with Content-Disposition

**Decision**: Serve files via FastAPI endpoint with proper Content-Disposition headers

**Rationale**:
- FastAPI's `FileResponse` handles efficient file streaming
- Content-Disposition header controls browser download behavior
- Can implement access control (verify session_id matches file owner)
- Supports range requests for large file streaming
- Simple to implement, no external CDN needed for MVP

**Implementation Pattern**:
```python
from fastapi.responses import FileResponse

@router.get("/chat/documents/{attachment_id}")
async def download_document(
    attachment_id: str,
    session_id: str = Depends(get_session_id)
):
    # Verify user has access to this document
    document = get_document_metadata(attachment_id)
    if document.session_id != session_id:
        raise HTTPException(403, "Access denied")
    
    file_path = Path(document.storage_path)
    if not file_path.exists():
        raise HTTPException(404, "File not found")
    
    return FileResponse(
        path=file_path,
        filename=document.filename,
        media_type=document.file_type,
        headers={
            "Content-Disposition": f"attachment; filename=\"{document.filename}\""
        }
    )
```

**Alternatives Considered**:
- Signed S3 URLs: Not applicable for local filesystem (future enhancement)
- Data URLs: Rejected - doesn't work for large files, memory issues
- Direct file serving via nginx: Rejected - adds deployment complexity for MVP

## Best Practices Summary

### Security
- Always validate file types on server using magic numbers (not extensions)
- Sanitize filenames to prevent path traversal (`secure_filename` equivalent)
- Implement rate limiting on upload endpoint (prevent abuse)
- Scan uploaded files for viruses in production (ClamAV integration point)
- Store files outside web root (not in static/ directory)

### Performance
- Stream large files to disk instead of loading into memory
- Use async file I/O operations (aiofiles)
- Implement chunked uploads for files >10MB (future enhancement)
- Add Content-Length header for download progress tracking
- Consider file compression for text files (gzip encoding)

### User Experience
- Show file preview before upload (filename, size, icon)
- Display progress bar during upload (0-100%)
- Provide clear error messages for validation failures
- Disable send button during upload (prevent double-submit)
- Allow cancel during upload (abort XHR request)
- Show thumbnail/icon for different file types in chat

### Compatibility
- MIME type mappings: PDF (`application/pdf`), DOCX (`application/vnd.openxmlformats-officedocument.wordprocessingml.document`), TXT (`text/plain`)
- Handle DOCX variants (some systems report `application/zip`)
- Test with various browsers (Chrome, Firefox, Safari, Edge)
- Ensure mobile file picker works (iOS/Android)

## Migration Path to Cloud Storage

When scaling beyond MVP:

1. **Implement Storage Interface**: Abstract `DocumentStorage` class already designed
2. **Add Azure Blob Storage Implementation**: Use `azure-storage-blob` SDK
3. **Configuration Toggle**: Environment variable to switch storage backends
4. **Gradual Migration**: Script to copy existing local files to blob storage
5. **Update Download URLs**: Generate SAS tokens instead of API endpoints
6. **Add CDN**: Azure CDN for faster global access

**No code changes needed in API layer** - abstraction handles backend swap transparently.
