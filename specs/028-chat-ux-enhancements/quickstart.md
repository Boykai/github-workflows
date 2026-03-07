# Quickstart: Chat UX Enhancements — AI Enhance Toggle, Markdown Input Support, File Upload, and Voice Chat

**Feature**: 028-chat-ux-enhancements | **Date**: 2026-03-07

## Prerequisites

- Node.js 20+ and npm
- Python 3.12+
- The repository cloned and on the feature branch

```bash
git checkout 028-chat-ux-enhancements
```

## Setup

### Backend

```bash
cd backend
pip install -e ".[dev]"
# Database migrations run automatically on startup
uvicorn src.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# App available at http://localhost:5173
```

## New Files to Create

### Frontend

| File | Purpose |
|------|---------|
| `frontend/src/components/chat/ChatToolbar.tsx` | NEW: Toolbar with AI Enhance toggle, file upload button, mic button |
| `frontend/src/components/chat/FilePreviewChips.tsx` | NEW: Inline file preview chips with remove action |
| `frontend/src/components/chat/VoiceInputButton.tsx` | NEW: Microphone button with recording state indicator |
| `frontend/src/hooks/useFileUpload.ts` | NEW: File selection, validation, upload state management |
| `frontend/src/hooks/useVoiceInput.ts` | NEW: Web Speech API integration, transcription state |

### Files to Modify

| File | Changes |
|------|---------|
| `frontend/src/lib/commands/registry.ts` | Change command prefix from `#` to `/` in `parseCommand()` |
| `frontend/src/components/chat/ChatInterface.tsx` | Integrate ChatToolbar, FilePreviewChips, voice input; update command trigger to `/` |
| `frontend/src/components/chat/CommandAutocomplete.tsx` | Update command display prefix from `#` to `/` |
| `frontend/src/hooks/useChat.ts` | Add aiEnhance state, file attachments array, voice state |
| `frontend/src/services/api.ts` | Add `chat.uploadFile()` method; modify `chat.sendMessage()` to include `ai_enhance` and `file_urls` |
| `frontend/src/types/index.ts` | Add `FileAttachment`, `VoiceInputState`, `ChatPreferences` types |
| `backend/src/api/chat.py` | Add `ai_enhance` and `file_urls` to request model; add `POST /chat/upload` endpoint |
| `backend/src/services/ai_agent.py` | Add conditional description bypass based on `ai_enhance` flag |

## Implementation Order

### Phase 1: Command Prefix Fix (Markdown Support)

1. **registry.ts** — Change `parseCommand()` to match `/` prefix instead of `#`
   - Update `trimmed.startsWith('#')` → `trimmed.startsWith('/')`
   - Update `trimmed.slice(1)` to extract command name after `/`
   - Remove `'help'` keyword exact match (or move to `/help`)

2. **ChatInterface.tsx** — Update autocomplete trigger
   - Change `trimmed.startsWith('#')` → `trimmed.startsWith('/')`
   - Update placeholder text to "Type a message or /command..."

3. **CommandAutocomplete.tsx** — Update display prefix
   - Show `/commandName` in suggestions instead of `#commandName`

**Verify**: Type `# Heading` in chat → no error. Type `/help` → command recognized.

### Phase 2: AI Enhance Toggle

4. **Types** (`types/index.ts`)
   - Add `ChatPreferences` interface

5. **ChatToolbar.tsx** (new)
   - Create toggle component with pill-style UI
   - AI Enhance label with ON/OFF state
   - localStorage read/write for persistence

6. **ChatInterface.tsx** — Integration
   - Import and render ChatToolbar above input
   - Pass aiEnhance state to submit handler

7. **api.ts** — Modify sendMessage
   - Add `ai_enhance` parameter to the chat message request

8. **chat.py** (backend) — Accept new field
   - Add `ai_enhance: bool = True` to `ChatMessageRequest`

9. **ai_agent.py** (backend) — Conditional logic
   - When `ai_enhance=False`, use raw input as description body
   - Still run metadata generation pipeline
   - Append Agent Pipeline config section

**Verify**: Toggle OFF → submit message → GitHub Issue has exact user text. Toggle ON → existing flow unchanged.

### Phase 3: File Upload

10. **Types** (`types/index.ts`)
    - Add `FileAttachment` interface

11. **useFileUpload.ts** (new hook)
    - File selection, validation, upload state management
    - Client-side validation for size and type

12. **FilePreviewChips.tsx** (new component)
    - Render file preview chips with remove buttons

13. **api.ts** — Add upload method
    - `chat.uploadFile(file: File)` using FormData

14. **chat.py** (backend) — New upload endpoint
    - `POST /api/v1/chat/upload` accepting multipart/form-data
    - Server-side validation
    - Upload to GitHub CDN/Gist

15. **ChatInterface.tsx** — Integration
    - Render FilePreviewChips between toolbar and input
    - Wire file upload to submit flow
    - Embed file URLs in message payload

**Verify**: Select file → preview chip shows → submit → file URL in GitHub Issue body.

### Phase 4: Voice Input

16. **useVoiceInput.ts** (new hook)
    - Web Speech API integration
    - Permission handling
    - Interim/final transcript management

17. **VoiceInputButton.tsx** (new component)
    - Mic button with recording state animation
    - Stop/cancel controls

18. **ChatToolbar.tsx** — Add mic button
    - Wire VoiceInputButton into toolbar right section

19. **ChatInterface.tsx** — Integration
    - Wire useVoiceInput hook
    - Append transcribed text to input field
    - Handle permission errors

**Verify**: Click mic → speak → text appears in input → edit → submit. Deny permission → error message shown → chat still works.

## Key Patterns to Follow

### localStorage Persistence Pattern

```typescript
// Read on mount
const [aiEnhance, setAiEnhance] = useState<boolean>(() => {
  const stored = localStorage.getItem('chat-ai-enhance');
  return stored !== null ? stored === 'true' : true; // default ON
});

// Persist on change
const handleToggle = (enabled: boolean) => {
  setAiEnhance(enabled);
  localStorage.setItem('chat-ai-enhance', String(enabled));
};
```

### File Upload Pattern

```typescript
// Client-side validation
const validateFile = (file: File): string | null => {
  if (file.size > FILE_VALIDATION.maxFileSize) {
    return `File exceeds ${FILE_VALIDATION.maxFileSize / 1024 / 1024} MB limit`;
  }
  const parts = file.name.split('.');
  const ext = parts.length > 1 ? '.' + parts.pop()!.toLowerCase() : '';
  if (!ext || !ALLOWED_TYPES.includes(ext)) {
    return `File type ${ext || '(no extension)'} is not supported`;
  }
  return null; // valid
};
```

### Web Speech API Pattern

```typescript
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (SpeechRecognition) {
  const recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = 'en-US';

  recognition.onresult = (event) => {
    let interim = '';
    for (let i = event.resultIndex; i < event.results.length; i++) {
      if (event.results[i].isFinal) {
        onTranscript(event.results[i][0].transcript);
      } else {
        interim += event.results[i][0].transcript;
      }
    }
    setInterimTranscript(interim);
  };
}
```

### Backend File Upload Pattern

```python
from fastapi import UploadFile, File, HTTPException

@router.post("/chat/upload")
async def upload_file(file: UploadFile = File(...)):
    # Validate size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail={
            "filename": file.filename,
            "error": "File exceeds the 10 MB size limit",
            "error_code": "file_too_large"
        })

    # Validate type
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail={
            "filename": file.filename,
            "error": f"File type {ext} is not supported",
            "error_code": "unsupported_type"
        })

    # Upload to GitHub and return URL
    file_url = await upload_to_github(contents, file.filename, file.content_type)
    return FileUploadResponse(
        filename=file.filename,
        file_url=file_url,
        file_size=len(contents),
        content_type=file.content_type
    )
```

## Verification

After implementation, verify:

1. **Markdown Input**: Type `# Heading`, `**bold**`, `- list`, `` `code` `` in chat → all accepted without errors. Type `/help` → command recognized.
2. **AI Enhance ON**: Toggle ON → submit message → GitHub Issue has AI-rewritten description + metadata (existing behavior unchanged).
3. **AI Enhance OFF**: Toggle OFF → submit "My exact description" → GitHub Issue body contains "My exact description" verbatim + auto-generated title/labels/estimates.
4. **Toggle Persistence**: Set toggle OFF → refresh page → toggle still OFF.
5. **File Upload**: Click paperclip → select image → preview chip shows → submit → file URL embedded in GitHub Issue body.
6. **File Validation**: Select 15 MB file → error message shown → file not added. Select .exe → error shown.
7. **File Remove**: Select file → click × on chip → file removed from pending list.
8. **Voice Input (Chrome)**: Click mic → allow permission → speak → text appears in input → click stop → edit text → submit.
9. **Voice Permission Denied**: Click mic → deny permission → error toast shown → chat continues working.
10. **Voice Unsupported (Firefox)**: Mic button shows disabled/unsupported state → tooltip explains.
11. **Edge Case**: Toggle AI Enhance rapidly while submitting → submission uses state at click time.
12. **Edge Case**: Attach files but clear text → files remain pending.
13. **Edge Case**: Network error during upload → error shown → retry works.
