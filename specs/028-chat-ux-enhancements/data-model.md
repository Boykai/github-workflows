# Data Model: Chat UX Enhancements — AI Enhance Toggle, Markdown Input Support, File Upload, and Voice Chat

**Feature**: 028-chat-ux-enhancements | **Date**: 2026-03-07

## Backend Entities (Pydantic Models)

### ChatMessageRequest (Modified)

The existing chat message request payload — modified to include the AI Enhance flag and file attachment references.

```python
class ChatMessageRequest(BaseModel):
    message: str                         # User's chat input text
    ai_enhance: bool = True              # AI Enhance toggle state at submission time
    file_urls: list[str] = []            # URLs of previously uploaded files to attach to issue
```

**Modification Notes**:
- `ai_enhance` defaults to `True` to preserve backward compatibility with existing flow.
- `file_urls` contains URLs returned from the upload endpoint; empty list means no attachments.
- The existing `message` field is unchanged.

### FileUploadResponse

Response from the file upload endpoint.

```python
class FileUploadResponse(BaseModel):
    filename: str                        # Original filename
    file_url: str                        # Accessible URL for the uploaded file
    file_size: int                       # File size in bytes
    content_type: str                    # MIME type (e.g., "image/png")
```

### FileUploadError

Error response for failed file uploads.

```python
class FileUploadError(BaseModel):
    filename: str                        # File that failed
    error: str                           # Human-readable error message
    error_code: str                      # Machine-readable code: "file_too_large", "unsupported_type", "upload_failed"
```

### FileValidationConfig

Server-side validation configuration (not a Pydantic model — a constants module).

```python
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024   # 10 MB
MAX_FILES_PER_MESSAGE = 5
ALLOWED_IMAGE_TYPES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
ALLOWED_DOC_TYPES = {".pdf", ".txt", ".md", ".csv", ".json", ".yaml", ".yml"}
ALLOWED_ARCHIVE_TYPES = {".zip"}
BLOCKED_TYPES = {".exe", ".sh", ".bat", ".cmd", ".js", ".py", ".rb"}
ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_DOC_TYPES | ALLOWED_ARCHIVE_TYPES
```

---

## Frontend Types (TypeScript)

### Chat Enhancement Types

```typescript
/** State of a file pending upload or already uploaded */
interface FileAttachment {
  id: string;                            // Unique identifier (generated client-side)
  file: File;                            // Browser File object
  filename: string;                      // Display name
  fileSize: number;                      // Size in bytes
  contentType: string;                   // MIME type
  status: 'pending' | 'uploading' | 'uploaded' | 'error';
  progress: number;                      // Upload progress 0–100
  fileUrl: string | null;                // URL after successful upload
  error: string | null;                  // Error message if status is 'error'
}

/** Voice input recording state */
interface VoiceInputState {
  isSupported: boolean;                  // Browser supports Web Speech API
  isRecording: boolean;                  // Currently recording
  isProcessing: boolean;                 // Processing final result
  interimTranscript: string;             // Current interim (in-progress) text
  finalTranscript: string;               // Finalized transcription text
  error: string | null;                  // Error message (permission denied, etc.)
}

/** AI Enhance toggle state */
interface ChatPreferences {
  aiEnhance: boolean;                    // true = AI rewriting ON (default)
}
```

### File Validation Constants (Frontend)

```typescript
const FILE_VALIDATION = {
  maxFileSize: 10 * 1024 * 1024,         // 10 MB
  maxFilesPerMessage: 5,
  allowedImageTypes: ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'],
  allowedDocTypes: ['.pdf', '.txt', '.md', '.csv', '.json', '.yaml', '.yml'],
  allowedArchiveTypes: ['.zip'],
  blockedTypes: ['.exe', '.sh', '.bat', '.cmd', '.js', '.py', '.rb'],
} as const;

const ALLOWED_TYPES = [
  ...FILE_VALIDATION.allowedImageTypes,
  ...FILE_VALIDATION.allowedDocTypes,
  ...FILE_VALIDATION.allowedArchiveTypes,
];
```

### Command Types (Modified)

```typescript
/** Updated ParsedCommand — no structural change, just prefix behavior */
interface ParsedCommand {
  isCommand: boolean;
  name: string | null;
  args: string;
  raw: string;
}

// parseCommand() now only matches '/' prefix instead of '#'
// This is a behavioral change, not a type change
```

---

## State Machines

### AI Enhance Toggle

```
               ┌────────────┐
               │   ON (default)    │  AI rewrites description + generates metadata
               │ aiEnhance=true    │
               └──────┬─────┘
                      │ User clicks toggle
                      ▼
               ┌────────────┐
               │   OFF            │  Raw input as description + generates metadata only
               │ aiEnhance=false  │
               └──────┬─────┘
                      │ User clicks toggle
                      ▼
               ┌────────────┐
               │   ON             │  (cycles back)
               └────────────┘

Persistence: localStorage("chat-ai-enhance")
Submission: aiEnhance value captured at submit time, sent in request payload
```

### File Upload Lifecycle

```
User selects file(s)
    │
    ▼
  Validate (client-side)
    │
    ├─ Invalid → Show error toast → File NOT added to pending list
    │
    └─ Valid → Add to pending list
                │
                ▼
          ┌────────────┐
          │  PENDING    │  Preview chip shown, (×) to remove
          └──────┬─────┘
                 │ User submits chat message
                 ▼
          ┌────────────┐
          │  UPLOADING  │  Progress indicator on chip
          └──────┬─────┘
                 │
                 ├─ Success → UPLOADED (file_url populated)
                 │             │
                 │             ▼
                 │      Embed URL in issue body
                 │
                 └─ Failure → ERROR (error message shown)
                               │
                               ▼
                         User can retry or remove
```

### Voice Input State Machine

```
                    ┌────────────┐
                    │   IDLE      │  Mic button shown (normal state)
                    └──────┬─────┘
                           │ User clicks mic button
                           ▼
                    ┌────────────┐
            ┌───── │  REQUESTING │  Checking permission
            │      │  PERMISSION │
            │      └──────┬─────┘
            │             │
   Permission denied      │ Permission granted
            │             ▼
            │      ┌────────────┐
            │      │  RECORDING  │  Pulsing mic icon + waveform
            │      │             │  interimTranscript updating in real time
            │      └──────┬─────┘
            │             │
            │        User clicks stop / silence detected
            │             │
            │             ▼
            │      ┌────────────┐
            │      │ PROCESSING  │  Finalizing transcription
            │      └──────┬─────┘
            │             │
            │             ▼
            │      ┌────────────┐
            │      │   IDLE      │  finalTranscript in input field
            │      │             │  User can edit before submit
            │      └────────────┘
            │
            ▼
     ┌─────────────┐
     │ ERROR        │  "Microphone access required" toast
     │ (fallback to │  Mic button shows error state briefly
     │  text input) │  Chat continues to work normally
     └─────────────┘
```

### Chat Message Submission Flow (Modified)

```
User clicks Send
    │
    ▼
  Capture current state:
    - message text
    - aiEnhance value (at submit time, FR-017)
    - pending file attachments
    │
    ▼
  Has pending files?
    │
    ├─ Yes → Upload files sequentially
    │         │
    │         ├─ All succeed → Collect file_urls
    │         │
    │         └─ Any fail → Show error, allow retry
    │                        (don't lose message or other files)
    │
    └─ No → Continue
              │
              ▼
        Send to POST /api/v1/chat/messages:
          { message, ai_enhance, file_urls }
              │
              ▼
        Backend processes:
          │
          ├─ ai_enhance=true → Full AI pipeline (existing flow)
          │   → AI-rewritten description + metadata + pipeline config
          │
          └─ ai_enhance=false → Bypass description rewriting
              → Raw user input as description
              → AI generates metadata only (title, labels, estimates)
              → Append Agent Pipeline config section
              → Embed file URLs as Markdown links/images
              │
              ▼
        Create GitHub Parent Issue with:
          - Title: AI-generated (always)
          - Body: Raw input OR AI-rewritten (based on ai_enhance)
          - Labels, estimates, assignees: AI-generated (always)
          - File links: Embedded in body (if any)
```

---

## Existing Entities (Unchanged)

The following existing entities are referenced but not modified:

- **ChatMessage** (`frontend/src/types/index.ts`): `id`, `role`, `content`, `timestamp` — used to display messages in the chat interface. No structural changes.
- **CommandDefinition** (`frontend/src/lib/commands/types.ts`): `name`, `description`, `handler` — command registry entries. No structural changes; only the prefix matching logic in `parseCommand()` changes.
- **AI Agent Pipeline** (`backend/src/services/ai_agent.py`): Core processing pipeline — modified only to add conditional logic based on `ai_enhance` flag, not restructured.

---

## localStorage Keys

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `chat-ai-enhance` | `"true"` \| `"false"` | `"true"` | Persisted AI Enhance toggle preference |

---

## File Upload Accept String

For the `<input type="file" accept="...">` attribute:

```
image/png,image/jpeg,image/gif,image/webp,image/svg+xml,application/pdf,text/plain,text/markdown,text/csv,application/json,application/x-yaml,application/zip
```
