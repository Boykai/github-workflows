# Research & Technical Decisions: Chat Document Upload

**Feature Branch**: `001-chat-document-upload`  
**Created**: 2026-02-13

## File Upload Implementation

### Backend: FastAPI UploadFile

**Decision**: Use FastAPI's built-in `UploadFile` with multipart/form-data

**Rationale**:
- Native FastAPI support for file uploads
- Streaming support for large files
- Memory efficient (spooled temporary files)
- Built-in file metadata (filename, content_type)

**Implementation**:
```python
from fastapi import UploadFile, File

@app.post("/chat/upload")
async def upload_document(file: UploadFile = File(...)):
    # Process file upload
    pass
```

### File Storage

**Decision**: Local filesystem storage with session-based directories

**Structure**: `uploads/{session_id}/{filename}`

**Rationale**:
- Simple for MVP implementation
- No external dependencies
- Easy to migrate to cloud storage later
- Session isolation for security

### File Validation

**Decision**: Use `python-magic` for MIME type validation

**Supported Types**:
- `application/pdf` - PDF documents
- `application/vnd.openxmlformats-officedocument.wordprocessingml.document` - DOCX
- `text/plain` - TXT files

**Validation Strategy**:
1. Client-side: Quick validation using file extension
2. Server-side: MIME type validation using python-magic (security)
3. File size: Check before and during upload

### Frontend Upload with Progress

**Decision**: Use FormData with fetch API and XMLHttpRequest for progress

**Implementation Approach**:
```typescript
const formData = new FormData();
formData.append('file', file);

// Use XMLHttpRequest for progress events
const xhr = new XMLHttpRequest();
xhr.upload.addEventListener('progress', (e) => {
  const percent = (e.loaded / e.total) * 100;
  setProgress(percent);
});
```

## Data Model Extension

### ChatMessage Extension

**Decision**: Extend ChatMessage.action_data to include document attachment metadata

**Schema Addition**:
```python
action_data = {
    "type": "document_upload",
    "document": {
        "filename": str,
        "file_size": int,
        "file_type": str,
        "storage_path": str,
        "upload_timestamp": str
    }
}
```

## Security Considerations

1. **File Type Validation**: Server-side MIME validation (not just extension)
2. **File Size Limits**: 20MB limit enforced on server
3. **Storage Isolation**: Files stored per session to prevent access conflicts
4. **Filename Sanitization**: Remove special characters and path traversal attempts
5. **Access Control**: Verify user has access to conversation before serving documents

## Performance Considerations

1. **Streaming Uploads**: Use FastAPI's streaming for memory efficiency
2. **Progress Updates**: Client-side progress tracking for UX
3. **Storage Management**: Future: implement cleanup for old documents
4. **Concurrent Uploads**: System should handle 100 concurrent uploads (per spec)

## API Contracts

### Upload Endpoint

**POST /api/chat/upload**
- Accepts: multipart/form-data
- Returns: Document metadata including storage reference
- Validates: file type, size, user access

### Download Endpoint

**GET /api/chat/document/{document_id}**
- Returns: File stream with appropriate content-type
- Validates: user access to conversation

## Testing Strategy

1. **Unit Tests**: File validation logic
2. **Integration Tests**: Upload flow end-to-end
3. **Contract Tests**: API endpoint validation
4. **Manual Testing**: Upload progress, error handling, large files
