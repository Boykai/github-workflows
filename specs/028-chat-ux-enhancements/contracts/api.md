# API Contracts: Chat UX Enhancements — AI Enhance Toggle, Markdown Input Support, File Upload, and Voice Chat

**Feature**: 028-chat-ux-enhancements | **Date**: 2026-03-07

## Base URL

All endpoints are prefixed with `/api/v1` and require an authenticated session (same auth pattern as existing endpoints in `/api/v1/chat/*`).

---

## Modified Endpoints

### Send Chat Message (Modified)

```
POST /api/v1/chat/messages
```

**Description**: Send a user chat message for processing. Modified to include AI Enhance flag and file attachment URLs.

**Request Body** (updated fields in **bold**):
```json
{
  "message": "## Feature Request\n\nI want to add dark mode support with...",
  "**ai_enhance**": true,
  "**file_urls**": [
    "https://user-images.githubusercontent.com/12345/abc123.png",
    "https://gist.githubusercontent.com/user/def456/raw/document.pdf"
  ]
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `message` | string | (required) | User's chat input text |
| `ai_enhance` | boolean | `true` | When `true`, existing AI rewriting flow. When `false`, use raw input as issue description, still generate metadata. |
| `file_urls` | string[] | `[]` | URLs of files previously uploaded via `/chat/upload`. Embedded in the GitHub Issue body. |

**Behavior when `ai_enhance = true`** (default, existing flow):
- Chat Agent rewrites and enhances the description
- Chat Agent generates metadata (title, labels, estimates, assignees, milestones)
- Agent Pipeline config appended to description
- File URLs embedded as Markdown links/images at the end of the description

**Behavior when `ai_enhance = false`** (new):
- User's exact `message` text used verbatim as the GitHub Parent Issue description body
- Chat Agent generates metadata only (title, labels, estimates, assignees, milestones)
- Agent Pipeline configuration section appended after the user's description
- File URLs embedded as Markdown links/images after the pipeline config section

**Response** (200 OK): Unchanged — returns the chat response with proposal/recommendation as today.

**Error Responses**:
- `400 Bad Request` — Empty message, invalid file_urls format
- `401 Unauthorized` — Missing or invalid session

---

## New Endpoints

### Upload File

```
POST /api/v1/chat/upload
```

**Description**: Upload a file for attachment to a future GitHub Issue. Returns a publicly accessible URL. Files are uploaded to GitHub's user-content CDN (for images) or as Gist attachments (for documents).

**Request**: `multipart/form-data`

| Field | Type | Description |
|-------|------|-------------|
| `file` | binary | The file to upload |

**Validation**:
- Max file size: 10 MB (10,485,760 bytes)
- Allowed types: `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.svg`, `.pdf`, `.txt`, `.md`, `.csv`, `.json`, `.yaml`, `.yml`, `.zip`
- Blocked types: `.exe`, `.sh`, `.bat`, `.cmd`, `.js`, `.py`, `.rb`

**Response** (200 OK):
```json
{
  "filename": "screenshot.png",
  "file_url": "https://user-images.githubusercontent.com/12345/abc123-screenshot.png",
  "file_size": 245760,
  "content_type": "image/png"
}
```

**Error Responses**:
- `400 Bad Request` — No file provided
- `401 Unauthorized` — Missing or invalid session
- `413 Payload Too Large` — File exceeds 10 MB limit
  ```json
  {
    "filename": "large-video.mp4",
    "error": "File exceeds the 10 MB size limit",
    "error_code": "file_too_large"
  }
  ```
- `415 Unsupported Media Type` — File type not allowed
  ```json
  {
    "filename": "script.exe",
    "error": "File type .exe is not supported",
    "error_code": "unsupported_type"
  }
  ```
- `502 Bad Gateway` — Upload to GitHub failed
  ```json
  {
    "filename": "screenshot.png",
    "error": "Failed to upload file to GitHub. Please try again.",
    "error_code": "upload_failed"
  }
  ```

---

## Frontend API Client Methods

Added to `frontend/src/services/api.ts`:

```typescript
// Chat file upload
chat: {
  // Existing methods remain unchanged...

  uploadFile: async (file: File): Promise<FileUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/chat/upload`, {
      method: 'POST',
      headers: getAuthHeaders(),  // Note: don't set Content-Type; browser sets multipart boundary
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new FileUploadError(error);
    }

    return response.json();
  },

  // Modified sendMessage to include new fields
  sendMessage: async (
    message: string,
    aiEnhance: boolean = true,
    fileUrls: string[] = []
  ): Promise<ChatResponse> => {
    const response = await fetch(`${API_BASE}/chat/messages`, {
      method: 'POST',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        ai_enhance: aiEnhance,
        file_urls: fileUrls,
      }),
    });
    return response.json();
  },
}
```

---

## Query Keys (TanStack Query)

No new query keys needed. File uploads are mutations (not cached queries). Chat messages use the existing query infrastructure.

| Operation | Type | Key |
|-----------|------|-----|
| File upload | Mutation | N/A (no cache) |
| Send message | Mutation | N/A (existing) |

---

## Issue Body Template (when ai_enhance = false)

When AI Enhance is OFF, the GitHub Issue body follows this structure:

```markdown
{user's exact verbatim input}

---

## Agent Pipeline Configuration

| Field | Value |
|-------|-------|
| Pipeline | {pipeline_name} |
| Agents | {comma-separated agent list} |
| Model | {model_name} |
| Created | {timestamp} |

### Attachments

- ![screenshot.png](https://user-images.githubusercontent.com/.../screenshot.png)
- [document.pdf](https://gist.githubusercontent.com/.../document.pdf)
```

When AI Enhance is ON, the existing AI-generated body format is used, with file URLs appended in the same Attachments section.
