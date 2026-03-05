# Data Model: Add File Upload and Voice Input Support to App Chat Experience

**Feature**: 018-chat-upload-voice | **Date**: 2026-03-05

## Entities

### FileAttachment

Represents a file queued for upload or already uploaded as part of a chat message.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `str` (UUID) | Primary key, auto-generated | Unique identifier for the attachment |
| `original_filename` | `str` | Max 255 chars, required | User's original filename |
| `mime_type` | `str` | Required, validated against allowlist | MIME type (e.g., `image/png`, `application/pdf`) |
| `file_size` | `int` | Required, max 26,214,400 (25MB) | File size in bytes |
| `storage_path` | `str` | Required, internal only | Server-side file path (not exposed to client) |
| `upload_status` | `UploadStatus` | Required, default `pending` | Current upload state |
| `created_at` | `datetime` | Auto-generated, UTC | Timestamp of upload |

**Allowed MIME Types**:
- Images: `image/jpeg`, `image/png`, `image/gif`, `image/webp`
- Documents: `application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document` (DOCX), `text/plain`

### UploadStatus (Enum)

| Value | Description |
|-------|-------------|
| `pending` | File received, not yet processed |
| `uploaded` | File successfully stored and available |
| `failed` | Upload or processing failed |

### VoiceRecording (Frontend-only state)

Represents the state of an active or completed voice recording session. This is client-side only — no server-side model needed since transcription happens in the browser via Web Speech API.

| Field | Type | Description |
|-------|------|-------------|
| `state` | `VoiceRecordingState` | Current recording lifecycle state |
| `transcribedText` | `string` | Accumulated transcription text |
| `interimText` | `string` | Current interim (not yet final) transcription |
| `error` | `string \| null` | Error message if recording fails |

### VoiceRecordingState (Frontend Enum)

| Value | Description |
|-------|-------------|
| `idle` | No recording in progress |
| `recording` | Actively capturing audio and transcribing |
| `processing` | Finalizing transcription after recording stop |
| `error` | Recording failed (permission denied, not supported, etc.) |

### ChatMessage (Extended)

The existing `ChatMessage` model is extended with an optional attachments field.

| Field | Type | Change | Description |
|-------|------|--------|-------------|
| `attachments` | `list[FileAttachmentResponse]` | **NEW** (optional, default `[]`) | File attachments included with the message |

### FileAttachmentResponse

API response representation of a file attachment (subset of FileAttachment, excludes internal fields).

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique attachment identifier |
| `original_filename` | `str` | User's original filename |
| `mime_type` | `str` | File MIME type |
| `file_size` | `int` | File size in bytes |
| `upload_status` | `str` | Upload status value |
| `url` | `str` | URL to retrieve the file |

## Relationships

```text
ChatMessage 1 ──── 0..10 ── FileAttachment
    │                            │
    │ contains                   │ stored as
    │                            │
    ▼                            ▼
  Message text              Local filesystem
  + attachment refs         (UUID-named files)
```

- A `ChatMessage` can have 0 to 10 `FileAttachment` references (FR-014).
- `FileAttachment` records are created independently via the upload endpoint, then referenced by ID when the message is sent.
- `VoiceRecording` is purely client-side state; it produces text that goes into the message `content` field — no server-side voice model needed.

## Validation Rules

### File Attachment Validation

| Rule | Constraint | Error Message |
|------|-----------|---------------|
| File size | ≤ 25 MB (26,214,400 bytes) | "File exceeds the maximum size of 25 MB" |
| File type | Must match allowed MIME types | "File type not supported. Accepted formats: JPG, PNG, GIF, WEBP, PDF, DOCX, TXT" |
| Attachments per message | ≤ 10 | "Maximum of 10 files per message" |
| Filename length | ≤ 255 characters | "Filename is too long" |

### Client-Side Validation (performed before upload)

1. Check `File.size` ≤ 26,214,400
2. Check `File.type` against allowed MIME type list
3. Check current attachment count < 10

### Server-Side Validation (defense in depth)

1. Validate `Content-Length` header ≤ 26,214,400
2. Validate MIME type of uploaded file
3. Sanitize original filename (strip path components, limit length)
4. Generate UUID for storage filename (prevent path traversal)

## State Transitions

### File Upload Lifecycle

```text
[File Selected] → Client Validation → [Queued for Preview]
                      │ fail                    │
                      ▼                         │ send message
                 [Error Shown]                  ▼
                                          [Uploading] → [Uploaded] → [Attached to Message]
                                               │ fail
                                               ▼
                                          [Upload Failed] → [Retry Available]
```

### Voice Recording Lifecycle

```text
[idle] ──── click mic ────→ [recording]
  ▲                              │
  │                              │ click mic again / pause
  │                              ▼
  │                         [processing]
  │                              │
  │                              │ transcription complete
  └────── text populated ────────┘

[idle] ──── click mic ────→ [error] (permission denied / not supported)
                                │
                                └──→ [idle] (user dismisses error)
```
