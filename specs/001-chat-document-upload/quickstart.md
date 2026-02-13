# Quickstart Guide: Chat Document Upload

**Feature Branch**: `001-chat-document-upload`  
**Created**: 2026-02-13

## Overview

This guide helps you test the chat document upload feature after implementation.

## Prerequisites

- Backend server running (FastAPI)
- Frontend development server running (React)
- User authenticated in the application
- Active chat conversation open

## Quick Test Scenarios

### Scenario 1: Basic Document Upload (User Story 1)

**Goal**: Upload a PDF document and verify it appears in chat

**Steps**:
1. Open an active chat conversation
2. Click the attach/paperclip icon in the chat input area
3. Select a PDF file under 20MB from your device
4. Verify the document preview (filename and size) appears
5. Click "Send" to upload the document
6. Verify the document appears in the chat thread as a clickable link
7. Click on the document link to open/download it

**Expected Result**: Document uploads successfully and is accessible to all participants

---

### Scenario 2: Upload Progress (User Story 2)

**Goal**: Test upload progress indication with a larger file

**Steps**:
1. Open an active chat conversation
2. Click the attach icon
3. Select a larger file (10-20MB PDF or DOCX)
4. Click "Send"
5. Observe the progress indicator showing upload percentage
6. Wait for upload to complete
7. Verify success confirmation appears
8. Verify document appears in chat thread

**Expected Result**: Progress indicator shows completion percentage; document uploads successfully

---

### Scenario 3: File Validation (User Story 3)

**Goal**: Test error handling for invalid files

**Test 3a - Unsupported File Type**:
1. Open an active chat conversation
2. Click the attach icon
3. Select an unsupported file (e.g., .exe, .jpg, .zip)
4. Verify error message: "File type not supported. Please upload PDF, DOCX, or TXT files"

**Test 3b - File Too Large**:
1. Open an active chat conversation
2. Click the attach icon
3. Select a file larger than 20MB
4. Verify error message: "File size exceeds 20MB limit. Please select a smaller file"

**Expected Result**: Clear error messages for validation failures

---

## Manual Test Files

Create test files for different scenarios:

```bash
# Create small text file
echo "Test document content" > test-small.txt

# Create a larger file (simulated for testing)
# Use any existing 10-20MB document or create one
```

## API Testing

### Upload Document via cURL

```bash
curl -X POST http://localhost:8000/api/chat/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/document.pdf" \
  -F "conversation_id=conv_123" \
  -F "message_content=Optional text message"
```

### Download Document via cURL

```bash
curl -X GET http://localhost:8000/api/chat/document/doc_123 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o downloaded_document.pdf
```

## Validation Checklist

After implementing each user story, verify:

### User Story 1 - Basic Upload
- [ ] Attach icon is visible in chat input
- [ ] File picker opens when clicking attach icon
- [ ] Document preview shows filename and size
- [ ] Document appears in chat thread after sending
- [ ] Document is clickable and opens/downloads
- [ ] Supported formats work: PDF, DOCX, TXT

### User Story 2 - Progress
- [ ] Progress indicator appears during upload
- [ ] Percentage updates during upload
- [ ] Success confirmation shows when complete
- [ ] Send button is disabled during upload

### User Story 3 - Validation
- [ ] Unsupported file types show error message
- [ ] Files over 20MB show error message
- [ ] Error messages are clear and actionable
- [ ] Errors can be dismissed

## Common Issues

### Issue: File not uploading
- Check file size is under 20MB
- Verify file type is supported (PDF, DOCX, TXT)
- Check network connection
- Verify user is authenticated

### Issue: Progress not showing
- Ensure using XMLHttpRequest for upload
- Verify progress event handlers are attached
- Check browser console for errors

### Issue: Document not clickable
- Verify document metadata is stored correctly
- Check download endpoint is accessible
- Verify user has access to conversation

## Development Setup

### Backend Dependencies

```bash
pip install fastapi python-magic
```

### Frontend Dependencies

```bash
npm install
# No additional dependencies needed for basic file upload
```

### Storage Directory

Ensure uploads directory exists:

```bash
mkdir -p backend/uploads
```

## Next Steps

1. Implement User Story 1 (Basic Upload) - MVP
2. Test independently using scenarios above
3. Deploy/demo if ready
4. Implement User Story 2 (Progress) - Enhancement
5. Implement User Story 3 (Validation) - Polish
