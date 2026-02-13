# Quickstart Guide: Document Upload Feature

**Feature**: Document Upload in Chat  
**Date**: 2026-02-13  
**Purpose**: Setup and testing instructions for developers

## Prerequisites

- Python 3.11+ installed
- Node.js 18+ installed
- Git repository cloned
- Backend and frontend dependencies installed

## Setup Instructions

### 1. Backend Setup

#### Install Dependencies

Add to `backend/pyproject.toml` dependencies:

```toml
dependencies = [
    # ... existing dependencies ...
    "aiofiles>=23.0.0",           # Async file I/O
    "python-magic>=0.4.27",        # MIME type detection
    "python-multipart>=0.0.6",     # File uploads (already present)
]
```

Install:
```bash
cd backend
pip install -e ".[dev]"
```

#### Configure Environment

Add to `backend/.env`:

```bash
# File upload configuration
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=25
ALLOWED_EXTENSIONS=pdf,docx,txt,xlsx,pptx
DOWNLOAD_TOKEN_EXPIRE_MINUTES=15
```

#### Create Upload Directory

```bash
cd backend
mkdir -p uploads
echo "uploads/" >> .gitignore
```

### 2. Frontend Setup

No additional dependencies required. Uses native XMLHttpRequest and existing React/TanStack Query.

### 3. Development Server

#### Start Backend

```bash
cd backend
uvicorn src.main:app --reload --port 8000
```

#### Start Frontend

```bash
cd frontend
npm run dev
```

Frontend will be available at http://localhost:5173

---

## API Testing

### Using cURL

#### 1. Upload a Document

```bash
# Authenticate first (get session cookie)
curl -X POST http://localhost:8000/api/v1/auth/github/callback \
  -H "Content-Type: application/json" \
  -d '{"code": "test_auth_code"}' \
  -c cookies.txt

# Upload a document
curl -X POST "http://localhost:8000/api/v1/documents/upload?project_id=456789" \
  -H "Content-Type: multipart/form-data" \
  -b cookies.txt \
  -F "file=@/path/to/test.pdf" \
  -F "message_text=Test document upload"
```

**Expected Response** (201 Created):
```json
{
  "document": {
    "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "original_filename": "test.pdf",
    "file_size": 2457600,
    "mime_type": "application/pdf",
    "file_extension": ".pdf",
    "upload_timestamp": "2026-02-13T15:30:00Z",
    "uploader_user_id": "github_user_123",
    "project_id": 456789
  },
  "message": {
    "message_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "sender_user_id": "github_user_123",
    "project_id": 456789,
    "message_timestamp": "2026-02-13T15:30:05Z",
    "message_text": "Test document upload",
    "message_type": "document"
  }
}
```

#### 2. Request Download URL

```bash
curl -X POST http://localhost:8000/api/v1/documents/a1b2c3d4-e5f6-7890-abcd-ef1234567890/download-url \
  -b cookies.txt
```

**Expected Response** (200 OK):
```json
{
  "download_url": "http://localhost:8000/api/v1/downloads?token=x7Y2mK9pQwE8RtL4sN6vH3jF1dC5aZ0b",
  "expires_at": "2026-02-13T16:00:00Z"
}
```

#### 3. Download Document

```bash
curl -X GET "http://localhost:8000/api/v1/downloads?token=x7Y2mK9pQwE8RtL4sN6vH3jF1dC5aZ0b" \
  -b cookies.txt \
  -o downloaded_file.pdf
```

#### 4. List Project Documents

```bash
curl -X GET "http://localhost:8000/api/v1/projects/456789/documents?limit=10" \
  -b cookies.txt
```

---

## Frontend Testing

### Manual Testing Steps

1. **Navigate to Chat Interface**
   - Open http://localhost:5173
   - Login with GitHub OAuth
   - Select a project

2. **Upload a Document**
   - Click the paperclip icon in chat input area
   - Select a supported file (PDF, DOCX, TXT, XLSX, PPTX)
   - Observe upload progress indicator
   - Verify document appears as message bubble with:
     - File name
     - File size (human-readable)
     - File type icon
     - Download button

3. **Test File Validation**
   - Try uploading unsupported file type (.zip, .exe)
     - Expected: Error message "File type not supported..."
   - Try uploading file > 25MB
     - Expected: Error message "File size exceeds 25MB limit..."

4. **Test Download**
   - Click download button on document message
   - Verify file downloads correctly
   - Check that filename matches original

5. **Test Upload Progress**
   - Upload a file > 5MB
   - Verify progress indicator shows percentage
   - Verify progress updates in real-time

---

## Automated Testing

### Backend Unit Tests

```bash
cd backend
pytest tests/unit/test_file_validator.py -v
pytest tests/unit/test_file_storage.py -v
pytest tests/unit/test_download_tokens.py -v
```

### Backend Integration Tests

```bash
cd backend
pytest tests/integration/test_document_api.py -v
```

### Frontend Unit Tests

```bash
cd frontend
npm test -- useFileUpload.test.tsx
npm test -- fileUtils.test.ts
```

### E2E Tests

```bash
cd frontend
npm run test:e2e -- document-upload.spec.ts
```

---

## Test Files

### Sample Test Files

Create these files in `backend/tests/fixtures/`:

1. **valid-test.pdf** (< 25MB) - Valid PDF for testing
2. **valid-test.docx** (< 25MB) - Valid DOCX for testing
3. **valid-test.txt** (< 1MB) - Valid TXT for testing
4. **large-file.pdf** (> 25MB) - For size limit testing
5. **fake.pdf** (actually .exe renamed) - For MIME validation testing

### Creating Test Fixtures

```bash
cd backend/tests/fixtures

# Create valid text file
echo "This is a test document for upload testing." > valid-test.txt

# Create valid PDF (requires LibreOffice or similar)
libreoffice --convert-to pdf valid-test.txt

# Create large file for size testing (27MB)
dd if=/dev/zero of=large-file.pdf bs=1M count=27

# Create fake PDF (for security testing)
echo "#!/bin/bash" > fake.pdf
```

---

## Troubleshooting

### Issue: "python-magic not found"

**Solution**:
```bash
# On Ubuntu/Debian
sudo apt-get install libmagic1

# On macOS
brew install libmagic

# Or use python-magic-bin (pure Python, no system dependencies)
pip install python-magic-bin
```

### Issue: "Upload directory not writable"

**Solution**:
```bash
cd backend
mkdir -p uploads
chmod 755 uploads
```

### Issue: "CORS error on file upload"

**Solution**: Verify `backend/src/main.py` CORS configuration includes:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: "File download fails with 401"

**Solution**: Check that:
1. Session cookie is present and valid
2. Download token hasn't expired (15 minute limit)
3. Token belongs to current session

### Issue: "Upload progress not showing"

**Solution**: Check browser console for errors. Ensure:
1. XMLHttpRequest is being used (not Fetch API)
2. `lengthComputable` is true in progress events
3. Backend isn't buffering entire request (should stream)

---

## Performance Testing

### Load Testing with curl

```bash
# Upload 10 files simultaneously
for i in {1..10}; do
  curl -X POST "http://localhost:8000/api/v1/documents/upload?project_id=456789" \
    -H "Content-Type: multipart/form-data" \
    -b cookies.txt \
    -F "file=@test.pdf" &
done
wait
```

### Expected Performance

- Upload initiation: < 1 second
- Upload throughput: ~10-20 MB/s (depends on disk I/O)
- Progress updates: Every 200-500ms
- File validation: 5-10ms per file
- Download token generation: < 100ms
- File download: Limited by network bandwidth

---

## Security Testing

### 1. Test File Type Spoofing

```bash
# Create .exe file disguised as .pdf
cp /bin/ls fake.pdf
curl -X POST "http://localhost:8000/api/v1/documents/upload?project_id=456789" \
  -b cookies.txt \
  -F "file=@fake.pdf"

# Expected: 400 Bad Request with MIME mismatch error
```

### 2. Test Authorization

```bash
# Request download without session
curl -X GET "http://localhost:8000/api/v1/downloads?token=valid_token"

# Expected: 401 Unauthorized
```

### 3. Test Token Expiration

```bash
# Request download with expired token (wait 16 minutes after generation)
curl -X GET "http://localhost:8000/api/v1/downloads?token=expired_token" \
  -b cookies.txt

# Expected: 401 Unauthorized with "expired token" message
```

---

## Next Steps

1. **Review implementation plan**: See [plan.md](./plan.md)
2. **Check data model**: See [data-model.md](./data-model.md)
3. **Review API contracts**: See [contracts/openapi.yaml](./contracts/openapi.yaml)
4. **Start implementation**: Follow tasks in tasks.md (to be generated)

---

## Additional Resources

- [Feature Specification](./spec.md)
- [Research Decisions](./research.md)
- [FastAPI File Uploads Documentation](https://fastapi.tiangolo.com/tutorial/request-files/)
- [python-magic Documentation](https://github.com/ahupp/python-magic)
- [TanStack Query Documentation](https://tanstack.com/query/latest)
