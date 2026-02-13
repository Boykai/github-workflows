# Implementation Plan: Chat Document Upload

**Feature Branch**: `001-chat-document-upload`  
**Created**: 2026-02-13  
**Status**: Planning

## Tech Stack & Libraries

### Backend
- **Framework**: FastAPI
- **File Upload**: FastAPI UploadFile with multipart/form-data
- **File Validation**: python-magic for MIME type validation
- **Storage**: Local filesystem (uploads/{session_id}/)

### Frontend
- **Framework**: React with TypeScript
- **HTTP Client**: Fetch API with FormData
- **UI Components**: Existing component library
- **File Handling**: HTML5 File API

## Project Structure

```
backend/
  src/
    api/
      chat.py                 # Chat endpoints (modify for document upload)
    models/
      chat_message.py         # ChatMessage model (extend action_data)
    services/
      document_service.py     # Document upload/validation service
    utils/
      file_validation.py      # File type and size validation
  uploads/                    # Document storage directory
    {session_id}/             # Session-specific uploads

frontend/
  src/
    components/
      chat/
        ChatInput.tsx         # Add document upload UI
        ChatMessage.tsx       # Display document attachments
        DocumentPreview.tsx   # Preview before send
    hooks/
      useDocumentUpload.ts    # Upload logic with progress
    services/
      chat.ts                 # Add document upload API calls
```

## Key Implementation Decisions

1. **Storage**: Use local filesystem with session-based directories for MVP
2. **File Validation**: Validate on both client (quick feedback) and server (security)
3. **Upload Progress**: Use FormData with fetch and XMLHttpRequest for progress events
4. **File Size Limit**: 20MB enforced on both client and server
5. **Supported Formats**: PDF, DOCX, TXT validated via MIME types
6. **Message Structure**: Extend ChatMessage.action_data to include document metadata

## Architecture Notes

- Backend: FastAPI endpoints handle multipart/form-data uploads
- Frontend: React components with file input and progress tracking
- Storage: Files stored in uploads/{session_id}/ directory structure
- Validation: python-magic for server-side MIME validation
- Document metadata stored in ChatMessage.action_data field
