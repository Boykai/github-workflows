# Research: Add File Upload and Voice Input Support to App Chat Experience

**Feature**: 018-chat-upload-voice | **Date**: 2026-03-05

## Research Tasks

### R1: File Upload Strategy (Frontend)

**Context**: The chat interface needs file selection via button click, drag-and-drop, and clipboard paste. The existing codebase uses React 18 with Tailwind CSS and lucide-react icons. No file upload libraries are currently installed.

**Decision**: Use native browser APIs (`<input type="file">`, Drag-and-Drop API, Clipboard API) wrapped in custom React hooks rather than introducing a third-party library like `react-dropzone`.

**Rationale**:
- The required functionality (single/multi file select, drag-and-drop, clipboard paste) is fully supported by native browser APIs across all target browsers.
- Avoids adding a new dependency for a well-scoped use case.
- Aligns with Constitution Principle V (Simplicity and DRY) — no premature abstraction.
- The custom hooks (`useFileUpload`, `useDragDrop`) keep the logic isolated and testable.

**Alternatives Considered**:
- **react-dropzone**: Feature-rich but overkill for this use case; adds ~15KB to bundle for functionality achievable with ~100 lines of custom code.
- **Uppy**: Comprehensive upload framework with UI components; far too heavy for a chat attachment feature.

---

### R2: File Upload Strategy (Backend)

**Context**: The backend uses FastAPI with `python-multipart` already installed. Files need to be received, validated, stored, and a reference returned to the client for attachment to chat messages.

**Decision**: Use FastAPI's built-in `UploadFile` parameter type with local filesystem storage, returning a unique file reference ID. Files are stored in a configurable upload directory with UUID-based filenames to prevent collisions and path traversal.

**Rationale**:
- `python-multipart` is already a project dependency, so `UploadFile` works out of the box.
- Local filesystem storage matches the existing MVP in-memory architecture — no need for S3/cloud storage at this stage.
- UUID-based naming prevents filename collisions and eliminates path traversal risks from user-supplied filenames.
- File metadata (original name, MIME type, size) is stored in-memory alongside the file reference, consistent with the existing in-memory message store pattern.

**Alternatives Considered**:
- **S3/MinIO**: Production-grade but adds infrastructure complexity; premature for MVP.
- **Database BLOB storage**: Adds database dependency for file content; poor performance for large files.
- **Base64 in message payload**: Simple but inflates message size by ~33%; impractical for 25MB files.

---

### R3: Voice Input / Speech-to-Text Approach

**Context**: The spec requires voice input with real-time or on-completion transcription. The Web Speech API (SpeechRecognition) is available in Chrome, Edge, and Safari. Firefox has partial support.

**Decision**: Use the Web Speech API (`SpeechRecognition` / `webkitSpeechRecognition`) as the primary transcription engine. The microphone button is hidden or disabled with a tooltip in unsupported browsers (FR-017).

**Rationale**:
- Zero additional dependencies — the API is built into target browsers.
- Provides real-time interim results for live transcription feedback.
- Aligns with the spec's assumption that "browser-native speech recognition capabilities" are the primary method.
- Constitution Principle V (Simplicity) — avoids introducing a third-party STT service and its associated API keys, latency, and cost.

**Alternatives Considered**:
- **OpenAI Whisper API**: Higher accuracy and cross-browser consistency, but requires backend proxy, API key management, audio streaming infrastructure, and per-request cost. Appropriate for a future enhancement if browser-native accuracy proves insufficient.
- **Google Speech-to-Text**: Similar trade-offs to Whisper; adds cloud dependency and cost.
- **MediaRecorder + backend STT**: Records audio blobs client-side, sends to backend for transcription. More complex architecture; deferred to future iteration if needed.

---

### R4: Client-Side File Validation

**Context**: Files must be validated for size (≤25MB) and MIME type before upload (FR-006, FR-007, FR-008). Validation must provide instant feedback.

**Decision**: Validate files immediately on selection/drop/paste using the `File` object's `size` and `type` properties. Rejected files show inline error messages without initiating any upload request.

**Rationale**:
- `File.size` and `File.type` are available synchronously on all target browsers.
- Client-side validation prevents unnecessary network requests (spec requirement).
- Server-side validation is still required as a security measure (defense in depth), but the client provides instant UX feedback.

**Alternatives Considered**:
- **File signature (magic bytes) validation**: More reliable than MIME type for security, but adds complexity (reading file headers with FileReader). Appropriate for server-side; overkill for client-side UX feedback.

---

### R5: File Preview Generation

**Context**: Image files need inline thumbnail previews; non-image files need file-name chips with type icons (FR-003, FR-004).

**Decision**: Use `URL.createObjectURL()` for image thumbnails (displayed in `<img>` tags) and lucide-react icons mapped to file extensions for non-image file chips.

**Rationale**:
- `createObjectURL` is a zero-cost, synchronous browser API that creates a local URL for the file blob — no upload or server round-trip needed for preview.
- lucide-react is already a project dependency, providing `FileText`, `FileImage`, `File` and other file-type icons.
- Object URLs are revoked when files are removed from the queue to prevent memory leaks.

**Alternatives Considered**:
- **FileReader.readAsDataURL**: Works but creates base64 strings that consume more memory than object URLs for large images.
- **Server-generated thumbnails**: Adds latency and server load; unnecessary for pre-send previews.

---

### R6: Accessibility Implementation

**Context**: Both file upload and voice input controls must be fully keyboard-navigable and screen-reader compatible (FR-011). Recording state changes need ARIA live regions (FR-011).

**Decision**: Implement ARIA attributes directly on custom components: `aria-label` for buttons, `role="status"` with `aria-live="polite"` for recording state and file attachment announcements, and visible focus indicators using Tailwind's `focus-visible:` utilities.

**Rationale**:
- The existing codebase uses Tailwind for styling including focus states; extending this pattern is consistent.
- ARIA live regions (`aria-live="polite"`) ensure screen readers announce state changes (recording started/stopped, file attached/removed) without interrupting the user.
- No additional accessibility library needed; native ARIA attributes suffice.

**Alternatives Considered**:
- **@radix-ui/react-***: Accessible component primitives; powerful but adds a dependency for components that are simple enough to implement with native ARIA.
- **react-aria**: Adobe's accessibility hooks; comprehensive but heavy for the scope needed here.

---

### R7: Mobile File Picker Integration

**Context**: On mobile, the file picker must expose camera, photo library, and file browsing options (FR-015).

**Decision**: Use the `accept` and `capture` attributes on the `<input type="file">` element. Setting `accept="image/*,application/pdf,.docx,.txt"` and optionally `capture="environment"` triggers the native mobile file picker with camera/photo library/files options.

**Rationale**:
- Standard HTML attributes supported by all mobile browsers; no JavaScript required.
- iOS Safari and Android Chrome both surface camera, photo library, and file browser when `accept` includes image types.
- The `capture` attribute is optional and can be omitted to allow all options rather than forcing camera.

**Alternatives Considered**:
- **Capacitor/Cordova plugins**: Native camera/file access; requires a native wrapper which is out of scope for this web application.

---

### R8: Drag-and-Drop UX Pattern

**Context**: Files can be dragged onto the chat input area or conversation window (FR-002). Need visual feedback during drag.

**Decision**: Implement a `DragDropOverlay` component that appears when files are dragged over the chat area. Use the `dragenter`, `dragleave`, `dragover`, and `drop` events on the chat container. The overlay shows a dashed border with "Drop files here" text.

**Rationale**:
- Standard Drag-and-Drop API events are sufficient; the existing `@dnd-kit` dependency is for Kanban board reordering and is not appropriate for file drops.
- The overlay provides clear visual feedback that the area accepts file drops.
- `dragenter`/`dragleave` counter pattern prevents flickering when dragging over child elements.

**Alternatives Considered**:
- **@dnd-kit file drop**: Not designed for file drops from OS; it's for in-app element reordering.
- **No visual feedback**: Poor UX; users need confirmation that the drop target is valid.

## Summary of Decisions

| Area | Decision | Key Benefit |
|------|----------|-------------|
| Frontend file handling | Native browser APIs (File, DnD, Clipboard) | Zero dependencies, full browser support |
| Backend file handling | FastAPI UploadFile + local filesystem | Leverages existing dependency, MVP-appropriate |
| Voice input | Web Speech API (SpeechRecognition) | Zero dependencies, real-time transcription |
| File validation | Client-side File.size/type + server-side defense | Instant UX feedback, secure |
| File previews | URL.createObjectURL + lucide-react icons | Fast, memory-efficient, consistent icons |
| Accessibility | Native ARIA attributes + Tailwind focus | No new dependencies, standards-compliant |
| Mobile file picker | HTML accept/capture attributes | Native OS integration, zero JS overhead |
| Drag-and-drop | Native DnD API + overlay component | Standard pattern, clear visual feedback |
