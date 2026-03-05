# Quickstart: Add File Upload and Voice Input Support to App Chat Experience

**Feature**: 018-chat-upload-voice | **Date**: 2026-03-05

## Overview

This guide provides a rapid-start reference for implementing file upload and voice input support in the chat experience. It covers the key integration points, new components, and the order of implementation.

## Prerequisites

- Existing chat interface functional (text messaging works)
- Backend running with FastAPI and `python-multipart` installed
- Frontend running with React 18, Tailwind CSS, and lucide-react
- Modern browser for testing (Chrome/Edge recommended for full Web Speech API support)

## Implementation Order

### Phase 1: Backend File Upload (Foundation)

1. **Create file upload service** (`backend/src/services/file_upload.py`)
   - File validation (size ≤ 25MB, MIME type allowlist)
   - UUID-based file storage on local filesystem
   - In-memory file metadata registry

2. **Add upload endpoints** (extend `backend/src/api/chat.py`)
   - `POST /api/v1/chat/upload` — multipart file upload
   - `GET /api/v1/chat/upload/{file_id}` — file retrieval
   - `DELETE /api/v1/chat/upload/{file_id}` — file removal

3. **Extend chat message model** (`backend/src/models/chat.py`)
   - Add `FileAttachment` and `FileAttachmentResponse` models
   - Add optional `attachment_ids` to `ChatMessageRequest`
   - Add optional `attachments` to `ChatMessage`

### Phase 2: Frontend File Upload

4. **Create file upload hook** (`frontend/src/hooks/useFileUpload.ts`)
   ```typescript
   // Key exports:
   // - queuedFiles: FileWithPreview[]
   // - addFiles(files: FileList): ValidationResult
   // - removeFile(id: string): void
   // - uploadFiles(): Promise<string[]>  // returns attachment IDs
   // - validationError: string | null
   ```

5. **Create drag-and-drop hook** (`frontend/src/hooks/useDragDrop.ts`)
   ```typescript
   // Key exports:
   // - isDragging: boolean
   // - dragHandlers: { onDragEnter, onDragLeave, onDragOver, onDrop }
   ```

6. **Build UI components**:
   - `FileUploadButton.tsx` — Paperclip icon button + hidden `<input type="file">`
   - `FilePreviewArea.tsx` — Container for queued file previews
   - `FilePreviewItem.tsx` — Image thumbnail or file chip with dismiss button
   - `DragDropOverlay.tsx` — Visual overlay during drag-over

7. **Integrate into ChatInterface.tsx**:
   - Add `FileUploadButton` to input toolbar
   - Add `FilePreviewArea` above text input
   - Wrap chat area with drag-and-drop handlers
   - Handle clipboard paste events for images
   - Include `attachment_ids` in message send payload

### Phase 3: Voice Input

8. **Create voice input hook** (`frontend/src/hooks/useVoiceInput.ts`)
   ```typescript
   // Key exports:
   // - isRecording: boolean
   // - isSupported: boolean
   // - transcribedText: string
   // - interimText: string
   // - startRecording(): void
   // - stopRecording(): void
   // - error: string | null
   ```

9. **Build voice UI components**:
   - `VoiceInputButton.tsx` — Microphone button (hidden when unsupported)
   - `RecordingIndicator.tsx` — Animated indicator during recording

10. **Integrate into ChatInterface.tsx**:
    - Add `VoiceInputButton` to input toolbar
    - Append transcribed text to input field on completion
    - Show `RecordingIndicator` when actively recording

### Phase 4: Accessibility & Polish

11. **Add ARIA attributes** to all new interactive elements
12. **Add live regions** for state change announcements
13. **Verify keyboard navigation** through all new controls
14. **Test with screen readers** (VoiceOver, NVDA)

## Key File Reference

| File | Purpose |
|------|---------|
| `backend/src/services/file_upload.py` | File validation + storage service |
| `backend/src/api/chat.py` | Extended with upload endpoints |
| `backend/src/models/chat.py` | Extended with attachment models |
| `frontend/src/hooks/useFileUpload.ts` | File selection, validation, upload state |
| `frontend/src/hooks/useDragDrop.ts` | Drag-and-drop event handling |
| `frontend/src/hooks/useVoiceInput.ts` | Web Speech API wrapper |
| `frontend/src/components/chat/FileUploadButton.tsx` | Attachment button component |
| `frontend/src/components/chat/FilePreviewArea.tsx` | Preview container |
| `frontend/src/components/chat/FilePreviewItem.tsx` | Individual file preview |
| `frontend/src/components/chat/VoiceInputButton.tsx` | Microphone button |
| `frontend/src/components/chat/DragDropOverlay.tsx` | Drag overlay |
| `frontend/src/components/chat/RecordingIndicator.tsx` | Recording animation |
| `specs/018-chat-upload-voice/contracts/api.yaml` | OpenAPI contract |

## Validation Checklist

- [ ] File upload via button click works for all supported types
- [ ] Drag-and-drop shows overlay and accepts files
- [ ] Clipboard paste of images creates attachment
- [ ] File size > 25MB shows error before upload
- [ ] Unsupported file type shows error with accepted formats
- [ ] Max 10 files per message enforced
- [ ] Image files show thumbnail previews
- [ ] Non-image files show file-name chips with icons
- [ ] Dismiss button removes queued files
- [ ] Voice button starts recording with indicator
- [ ] Voice transcription populates text field
- [ ] Permission denial shows guidance message
- [ ] Unsupported browser hides/disables voice button
- [ ] All controls are keyboard-navigable
- [ ] Screen reader announces state changes
- [ ] Mobile file picker shows camera/photo library options
