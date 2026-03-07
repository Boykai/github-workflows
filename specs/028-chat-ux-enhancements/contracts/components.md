# Component Contracts: Chat UX Enhancements — AI Enhance Toggle, Markdown Input Support, File Upload, and Voice Chat

**Feature**: 028-chat-ux-enhancements | **Date**: 2026-03-07

## New Components

### ChatToolbar

**Location**: `frontend/src/components/chat/ChatToolbar.tsx`
**Purpose**: Persistent toolbar above the chat input containing the AI Enhance toggle, file upload button, and microphone button. Styled consistently with the `AddAgentPopover` pattern.

```typescript
interface ChatToolbarProps {
  aiEnhance: boolean;
  onAiEnhanceChange: (enabled: boolean) => void;
  onFileSelect: (files: FileList) => void;
  isRecording: boolean;
  isVoiceSupported: boolean;
  onVoiceToggle: () => void;
  fileCount: number;
}
```

**Behavior**:
- Renders as a horizontal bar above the chat input field
- **Left section**: AI Enhance pill toggle with label "AI Enhance" (FR-001)
  - ON state: colored pill (primary color), label shows "ON"
  - OFF state: muted pill (gray), label shows "OFF"
  - Click toggles state and calls `onAiEnhanceChange`
  - Styled to match `AddAgentPopover` border/hover pattern: `border border-dashed hover:bg-muted`
- **Right section**: Action buttons
  - Paperclip icon button for file upload (FR-008)
    - Click triggers hidden `<input type="file" multiple>` element
    - Badge showing `fileCount` when > 0
  - Microphone icon button for voice input (FR-012)
    - Normal state: mic icon (Mic from lucide-react)
    - Recording state: pulsing red mic icon (MicOff or animated Mic)
    - Disabled state: mic icon with strikethrough if `!isVoiceSupported`
    - Click calls `onVoiceToggle`
- Uses existing `Button` component from `components/ui/button.tsx`
- Icons from `lucide-react`: `Paperclip`, `Mic`, `MicOff`, `Sparkles` (for AI Enhance)

---

### FilePreviewChips

**Location**: `frontend/src/components/chat/FilePreviewChips.tsx`
**Purpose**: Displays inline preview chips for selected files above the chat input, between the toolbar and the text input.

```typescript
interface FilePreviewChipsProps {
  files: FileAttachment[];
  onRemove: (fileId: string) => void;
}
```

**Behavior**:
- Renders a horizontal scrollable row of chips (FR-009)
- Each chip shows:
  - File icon (image thumbnail for images, document icon for others)
  - Filename (truncated to ~20 chars with ellipsis)
  - File size (formatted: "2.4 MB", "128 KB")
  - Upload status indicator (spinner for uploading, check for uploaded, ⚠ for error)
  - Remove button (×) that calls `onRemove(fileId)` (FR-009)
- Empty state: renders nothing (no wrapper element)
- Error state on individual chips: red border, error icon, tooltip with error message
- Uses compact card/badge styling from existing UI components

---

### VoiceInputButton

**Location**: `frontend/src/components/chat/VoiceInputButton.tsx`
**Purpose**: Microphone button with recording state indicator and permission handling.

```typescript
interface VoiceInputButtonProps {
  isSupported: boolean;
  isRecording: boolean;
  onStart: () => void;
  onStop: () => void;
  error: string | null;
}
```

**Behavior**:
- **Supported + Idle**: Mic icon button, normal state. Click calls `onStart` (FR-012)
- **Supported + Recording**: Pulsing red mic icon with waveform animation (FR-013)
  - CSS animation: `animate-pulse` on the button with red background
  - Click calls `onStop`
  - Optional: small timer showing recording duration
- **Unsupported**: Mic icon with line-through, disabled, tooltip "Voice input not supported in this browser" (FR-015)
- **Error**: Brief red flash on button, toast notification with `error` message (FR-014)
- Uses `Button` component variant="ghost" size="icon"
- Icons from `lucide-react`: `Mic`, `MicOff`, `Square` (stop)

---

## New Hooks

### useFileUpload

**Location**: `frontend/src/hooks/useFileUpload.ts`
**Purpose**: Manages file selection, client-side validation, upload state, and preview data.

```typescript
interface UseFileUploadReturn {
  // State
  files: FileAttachment[];
  isUploading: boolean;
  errors: string[];

  // Actions
  addFiles: (fileList: FileList) => void;     // Validate + add to pending list
  removeFile: (fileId: string) => void;        // Remove from pending list
  uploadAll: () => Promise<string[]>;          // Upload all pending → return URLs
  clearAll: () => void;                        // Clear all files and errors
}

function useFileUpload(): UseFileUploadReturn;
```

**Implementation Notes**:
- `addFiles` validates each file against `FILE_VALIDATION` rules:
  - Check file size ≤ 10 MB
  - Check file extension against allowed types
  - Check total file count ≤ 5
  - Invalid files get error toast, valid files added to `files` array with status `'pending'`
- `uploadAll` uploads files sequentially to `POST /api/v1/chat/upload`:
  - Updates each file's `status` to `'uploading'` → `'uploaded'` or `'error'`
  - Returns array of `file_url` strings for successfully uploaded files
- `removeFile` removes by ID regardless of status
- Uses `useState` for file list, not TanStack Query (uploads are imperative, not cached)

### useVoiceInput

**Location**: `frontend/src/hooks/useVoiceInput.ts`
**Purpose**: Encapsulates Web Speech API integration, permission handling, and transcription state.

```typescript
interface UseVoiceInputReturn {
  // State
  isSupported: boolean;                  // Browser supports SpeechRecognition
  isRecording: boolean;                  // Currently recording
  interimTranscript: string;             // In-progress transcription
  error: string | null;                  // Error message

  // Actions
  startRecording: () => void;            // Request mic permission + start recognition
  stopRecording: () => void;             // Stop recognition + finalize text
  cancelRecording: () => void;           // Stop without keeping transcript
}

function useVoiceInput(
  onTranscript: (text: string) => void   // Callback to append text to input
): UseVoiceInputReturn;
```

**Implementation Notes**:
- On mount, check `window.SpeechRecognition || window.webkitSpeechRecognition` → set `isSupported`
- `startRecording`:
  1. Call `navigator.mediaDevices.getUserMedia({ audio: true })` for permission
  2. On success, create `SpeechRecognition` instance with `continuous: true`, `interimResults: true`, `lang: 'en-US'`
  3. Start recognition, set `isRecording: true`
  4. On `result` event, update `interimTranscript` with interim results
  5. On final result, call `onTranscript(finalText)` to append to input
  6. On error, set `error` with user-friendly message
- `stopRecording`: Call `recognition.stop()`, set `isRecording: false`
- `cancelRecording`: Call `recognition.abort()`, clear interimTranscript
- Cleanup: Stop recognition on component unmount (useEffect cleanup)
- Permission denial error: "Microphone access is required for voice input. Please allow microphone access in your browser settings."

---

## Modified Components

### ChatInterface

**Location**: `frontend/src/components/chat/ChatInterface.tsx`
**Purpose**: Main chat UI container — modified to integrate the new toolbar, file previews, and voice input.

**Changes**:
- Import and render `ChatToolbar` above the input area
- Import and render `FilePreviewChips` between toolbar and input
- Wire `useFileUpload` hook for file state management
- Wire `useVoiceInput` hook for voice transcription
- Read/write AI Enhance preference from/to localStorage
- Pass `aiEnhance` and `fileUrls` to the submit handler
- **Command parsing**: Update the autocomplete trigger condition from `trimmed.startsWith('#')` to `trimmed.startsWith('/')` (aligns with `registry.ts` change)

### CommandAutocomplete

**Location**: `frontend/src/components/chat/CommandAutocomplete.tsx`
**Purpose**: Dropdown autocomplete for commands — minimal change to display `/` prefix.

**Changes**:
- Update rendered command suggestions to show `/commandName` instead of `#commandName`
- No structural changes

### MessageBubble

**Location**: `frontend/src/components/chat/MessageBubble.tsx`
**Purpose**: Renders individual chat messages — no changes needed.

**Changes**: None. File attachments are embedded in the issue body, not displayed in the chat bubble.

---

## Modified Backend Services

### ai_agent.py

**Location**: `backend/src/services/ai_agent.py`
**Purpose**: Core AI pipeline — modified to conditionally bypass description rewriting.

**Changes**:
- Accept `ai_enhance: bool` parameter in the message processing method
- When `ai_enhance=False`:
  - Skip the description generation/rewriting step
  - Use the raw `message` text as the issue description body
  - Still run the metadata inference pipeline (title, labels, estimates, assignees)
  - Append Agent Pipeline configuration section to the description
  - Append file URLs as Markdown links/images if provided
- When `ai_enhance=True`: Existing flow unchanged

### chat.py (API)

**Location**: `backend/src/api/chat.py`
**Purpose**: REST endpoints for chat messages — modified to accept new fields.

**Changes**:
- Update the `ChatMessageRequest` model to include `ai_enhance` and `file_urls` fields
- Add new `POST /api/v1/chat/upload` endpoint for file uploads
- Pass `ai_enhance` flag through to the AI agent pipeline
- Pass `file_urls` through for issue body embedding

---

## UI Layout (Spatial Arrangement)

```
┌─────────────────────────────────────────────────┐
│                  Chat Messages                    │
│  ┌─────────────────────────────────────────────┐ │
│  │ [User] Hello, I have a feature request...   │ │
│  │ [Agent] I understand! Let me help you...    │ │
│  │ [User] ## Feature Request                   │ │
│  │         I want to add dark mode...          │ │
│  └─────────────────────────────────────────────┘ │
│                                                   │
│  ┌─────────────────────────────────────────────┐ │
│  │ ChatToolbar                                  │ │
│  │ [✨ AI Enhance: ON]          [📎] [🎤]     │ │
│  └─────────────────────────────────────────────┘ │
│                                                   │
│  ┌─────────────────────────────────────────────┐ │
│  │ FilePreviewChips (if files selected)         │ │
│  │ [📄 screenshot.png 2.4MB ×] [📄 doc.pdf ×] │ │
│  └─────────────────────────────────────────────┘ │
│                                                   │
│  ┌─────────────────────────────────────────────┐ │
│  │ Chat Input                              [Send]│ │
│  │ Type a message or /command...                 │ │
│  └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```
