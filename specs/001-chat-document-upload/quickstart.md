# Quickstart Guide: Chat Document Upload

**Feature**: 001-chat-document-upload  
**Last Updated**: 2026-02-13

## Overview

This guide helps developers set up and test the chat document upload feature. You'll be able to upload documents (PDF, DOCX, TXT) in chat conversations and download them.

## Prerequisites

- Repository cloned and environment set up
- Docker and Docker Compose installed (if using containerized setup)
- Python 3.11+ (if running backend locally)
- Node.js 18+ and npm (if running frontend locally)

## Quick Setup (5 minutes)

### 1. Backend Dependencies

Add file handling dependencies to `backend/pyproject.toml`:

```toml
[project]
dependencies = [
    # ... existing dependencies ...
    "python-multipart>=0.0.6",  # Required for file uploads in FastAPI
    "python-magic>=0.4.27",     # MIME type detection
    "aiofiles>=23.2.1",         # Async file I/O
]
```

Install dependencies:

```bash
cd backend
pip install -e .
# or
poetry install
```

### 2. Environment Configuration

Create uploads directory (if not exists):

```bash
mkdir -p backend/uploads
echo "*" > backend/uploads/.gitignore  # Don't commit uploaded files
echo "!.gitignore" >> backend/uploads/.gitignore
```

No additional environment variables needed for MVP (uses local filesystem).

### 3. Start Services

**Option A: Docker Compose** (recommended)
```bash
docker-compose up --build
```

**Option B: Local Development**
```bash
# Terminal 1 - Backend
cd backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm install
npm run dev
```

## Testing the Feature

### Manual Testing

1. **Open the application**: Navigate to `http://localhost:5173`
2. **Authenticate**: Log in with your GitHub account
3. **Select a project**: Choose a project from the sidebar
4. **Upload a document**:
   - Click the paperclip/attach icon in the chat input area
   - Select a test document (PDF, DOCX, or TXT under 20MB)
   - Verify the file preview appears (filename, size)
   - Click "Send" or press Enter
   - Watch the upload progress indicator
5. **View uploaded document**: The document should appear in the chat thread
6. **Download document**: Click on the document link to download/open it

### Test Files

Create test files for different scenarios:

```bash
# Small text file (instant upload)
echo "This is a test document" > test-small.txt

# Medium PDF (visible progress)
# Use any PDF file ~5MB in size

# Large DOCX (stress test)
# Use any DOCX file close to 20MB limit
```

### API Testing with cURL

**Upload a document**:
```bash
curl -X POST http://localhost:8000/api/chat/upload \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -F "file=@test-document.pdf" \
  -F "message_content=Here's the project proposal"
```

**Download a document**:
```bash
curl -X GET http://localhost:8000/api/chat/documents/ATTACHMENT_ID \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -o downloaded-file.pdf
```

### Python Test Script

```python
import requests
from pathlib import Path

BASE_URL = "http://localhost:8000/api"
session = requests.Session()
# Authenticate first to get session cookie...

def test_upload():
    file_path = Path("test-document.pdf")
    
    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f, "application/pdf")}
        data = {"message_content": "Test upload"}
        
        response = session.post(f"{BASE_URL}/chat/upload", files=files, data=data)
        assert response.status_code == 200
        
        result = response.json()
        print(f"Uploaded: {result['attachment']['filename']}")
        print(f"Attachment ID: {result['attachment']['attachment_id']}")
        
        return result['attachment']['attachment_id']

def test_download(attachment_id):
    response = session.get(f"{BASE_URL}/chat/documents/{attachment_id}")
    assert response.status_code == 200
    
    # Save downloaded file
    with open("downloaded.pdf", "wb") as f:
        f.write(response.content)
    print(f"Downloaded {len(response.content)} bytes")

# Run tests
attachment_id = test_upload()
test_download(attachment_id)
```

## Validation Scenarios

Test these scenarios to ensure proper validation:

### ✅ Valid Uploads

- [ ] PDF file under 20MB
- [ ] DOCX file under 20MB
- [ ] TXT file under 20MB
- [ ] File with special characters in name: `report (final) v2.pdf`
- [ ] File with spaces: `Meeting Notes.txt`

### ❌ Invalid Uploads (Should Show Error)

- [ ] File over 20MB → Error: "File size exceeds 20MB limit"
- [ ] Unsupported file type (.exe, .jpg, .zip) → Error: "File type not supported"
- [ ] Empty file (0 bytes) → Error: "File is empty"
- [ ] No file selected → Error: "No file provided"
- [ ] Network disconnect during upload → Error: "Upload failed. Please check your connection"

## Troubleshooting

### Upload Fails with 413 Error

**Symptom**: Large file uploads fail immediately with 413 status.

**Solution**: Check nginx/proxy configuration for `client_max_body_size`:
```nginx
# nginx.conf
client_max_body_size 25M;
```

### Files Not Persisting

**Symptom**: Uploaded files disappear after backend restart.

**Solution**: Ensure uploads directory is properly mounted in Docker:
```yaml
# docker-compose.yml
services:
  backend:
    volumes:
      - ./backend/uploads:/app/uploads
```

### MIME Type Detection Issues

**Symptom**: Valid files rejected as "unsupported type".

**Solution**: Install libmagic system library:
```bash
# Ubuntu/Debian
sudo apt-get install libmagic1

# macOS
brew install libmagic

# Windows
# python-magic-bin package includes DLL
pip install python-magic-bin
```

### CORS Errors on Upload

**Symptom**: Browser console shows CORS error during upload.

**Solution**: Verify CORS configuration includes multipart/form-data:
```python
# backend/src/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Performance Testing

### Load Test with Artillery

Create `artillery-upload.yml`:
```yaml
config:
  target: "http://localhost:8000"
  phases:
    - duration: 60
      arrivalRate: 5
  processor: "./upload-processor.js"

scenarios:
  - name: "Upload document"
    flow:
      - post:
          url: "/api/chat/upload"
          beforeRequest: "setAuthCookie"
          formData:
            file: "@test-small.txt"
```

Run load test:
```bash
artillery run artillery-upload.yml
```

### Expected Performance

- Small files (<1MB): <2 seconds end-to-end
- Medium files (5-10MB): <10 seconds with progress updates
- Large files (15-20MB): <30 seconds with progress updates
- Concurrent uploads: 100+ simultaneous without degradation

## Next Steps

- **Implement the feature**: Follow `tasks.md` for step-by-step implementation
- **Add tests**: Unit tests for upload/download services, E2E tests for UI flow
- **Security hardening**: Add virus scanning, rate limiting, audit logging
- **Scale to production**: Migrate from local filesystem to Azure Blob Storage

## Common Development Tasks

### View All Uploaded Documents

```bash
ls -lh backend/uploads/*/
```

### Clear All Uploads (Reset State)

```bash
rm -rf backend/uploads/*
mkdir -p backend/uploads
```

### Check Storage Usage

```bash
du -sh backend/uploads/
```

### Tail Backend Logs

```bash
docker-compose logs -f backend
# or locally
tail -f backend/logs/app.log
```

## API Reference

See [contracts/openapi.yaml](contracts/openapi.yaml) for complete API documentation.

**Key Endpoints**:
- `POST /api/chat/upload` - Upload document
- `GET /api/chat/documents/{attachment_id}` - Download document

**Authentication**: All endpoints require valid session cookie.

## Resources

- **Spec**: [spec.md](spec.md) - Feature requirements and user stories
- **Plan**: [plan.md](plan.md) - Implementation strategy and architecture
- **Data Model**: [data-model.md](data-model.md) - Entity definitions and relationships
- **Research**: [research.md](research.md) - Technology decisions and patterns

## Support

For issues or questions:
1. Check existing chat messages in the conversation
2. Review error logs in backend console
3. Verify file meets requirements (type, size)
4. Test with cURL to isolate frontend vs backend issues
