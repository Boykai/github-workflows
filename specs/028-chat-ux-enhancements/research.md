# Research: Chat UX Enhancements — AI Enhance Toggle, Markdown Input Support, File Upload, and Voice Chat

**Feature**: 028-chat-ux-enhancements | **Date**: 2026-03-07

## R1: Command Prefix Migration (# → /)

**Task**: Determine the best approach to resolve the Markdown-command parsing conflict where `#` characters in chat input are misinterpreted as command prefixes.

**Decision**: Switch the command prefix from `#` to `/` (slash). Update `parseCommand()` in `lib/commands/registry.ts` to only match tokens starting with `/` at the beginning of the message. Update `CommandAutocomplete` trigger condition in `ChatInterface.tsx` to match on `/` instead of `#`.

**Rationale**: The current parser in `registry.ts` (line 63) checks `if (!trimmed.startsWith('#'))` which blocks all Markdown headers (`# Heading`, `## Subheading`) and triggers false-positive command detection for any `#`-prefixed input. The `/` (slash) prefix is the de facto standard for chat commands across Slack, Discord, GitHub, and virtually all chat interfaces. It has zero collision with Markdown syntax since `/` is not a Markdown formatting character. The change is minimal — two pattern matches in `registry.ts` and one trigger condition in `ChatInterface.tsx`. The autocomplete in `CommandAutocomplete.tsx` already renders command names without the prefix character, so it adapts automatically.

**Alternatives Considered**:
- **Keep `#` but require no space after hash**: Rejected — too fragile; `#heading` (no space) is valid Markdown and would still conflict. Users habitually write `#tag` for labels.
- **Dual-prefix support (`#` for commands, allow Markdown)**: Rejected — ambiguous; impossible to distinguish `#help` (command) from `#help` (Markdown heading) without context.
- **Escape sequences for Markdown**: Rejected — terrible UX; users should not need to escape standard Markdown characters.

---

## R2: AI Enhance Toggle Architecture

**Task**: Determine how the "AI Enhance" toggle integrates with the existing Chat Agent pipeline, and where the conditional logic should be placed.

**Decision**: Add an `ai_enhance: bool` field to the chat message request payload sent from frontend to `POST /api/v1/chat/messages`. On the backend in `ai_agent.py`, check this flag before the description-generation step: when `false`, substitute the raw user input as the issue description body and skip the AI rewriting step, while still executing the metadata inference pipeline (title, labels, estimates, assignees, milestones) and appending Agent Pipeline configuration as a structured section in the issue body.

**Rationale**: The Chat Agent pipeline in `ai_agent.py` currently handles message processing including description generation and metadata inference as separate logical steps. Adding a conditional check at the description-generation step is the minimal change — it short-circuits one step without affecting the rest of the pipeline. Passing the flag via the request payload (rather than a separate API call or session state) ensures the toggle state is captured at submission time (FR-017: "toggle state at the moment of submission"). The frontend persists the preference in localStorage for UX continuity but the authoritative value is always the one sent with the message.

**Alternatives Considered**:
- **Backend reads toggle from user preferences**: Rejected — introduces race condition if user changes toggle while message is in flight; violates FR-017.
- **Frontend-side description bypass**: Rejected — the Chat Agent must still process the raw input for metadata inference; sending a flag to the backend keeps the pipeline unified.
- **Separate endpoint for non-enhanced messages**: Rejected — YAGNI; a boolean flag on the existing endpoint is simpler and DRYer.

---

## R3: Toggle Preference Persistence

**Task**: Determine the best mechanism for persisting the user's AI Enhance toggle preference across sessions.

**Decision**: Use `localStorage` with key `chat-ai-enhance` storing `"true"` or `"false"`. Initialize the toggle from localStorage on component mount, defaulting to `true` (ON) if no stored value exists. Update localStorage on every toggle change.

**Rationale**: The spec requires persistence "across sessions or at minimum within the current session" (FR-005). localStorage persists across browser sessions, page refreshes, and tab closures for the same origin — meeting the stronger requirement. It requires zero backend changes, zero database schema modifications, and zero API calls. The AI Enhance preference is a UI-only setting that doesn't need server-side enforcement (the authoritative value is sent per-message). This follows the principle of simplicity (Constitution V) — no backend round-trip for a single boolean preference.

**Alternatives Considered**:
- **sessionStorage**: Rejected — lost on tab close; only meets the weaker "within current session" requirement.
- **Backend user_preferences table**: Rejected — over-engineered for a single boolean; adds migration, API endpoint, and round-trip latency for no functional benefit.
- **Cookie**: Rejected — unnecessary; localStorage is simpler and has no size/expiry concerns for a single boolean.

---

## R4: File Upload Strategy via GitHub API

**Task**: Determine how to attach files to GitHub Issues from the chat, given GitHub REST API constraints.

**Decision**: Implement a two-step upload flow:
1. **Frontend**: User selects files → client-side validation (type, size ≤ 10 MB) → display preview chips → on submission, upload files to backend endpoint `POST /api/v1/chat/upload` as multipart/form-data.
2. **Backend**: Receive files → for images, create a GitHub Gist with the image encoded as a base64 data URI or upload via the GitHub repository contents API to a designated `uploads/` branch, returning a raw GitHub URL. For non-image files (PDFs, text, CSV, etc.), create a GitHub Gist containing the file content (text files) or a Gist with a download link comment (binary files). Return the accessible URL → embed URLs as Markdown links/images in the issue body.

The concrete upload mechanism is:
- **Image files** (png, jpg, gif, webp, svg): Upload to the repository via the GitHub Contents API (`PUT /repos/{owner}/{repo}/contents/uploads/{filename}`) on a dedicated `uploads` branch, then use the raw URL (`https://raw.githubusercontent.com/...`) embedded as `![filename](url)` in the issue body.
- **Document files** (pdf, txt, md, csv, json, yaml, zip): Create a GitHub Gist via `POST /gists` containing the file content, then embed the Gist URL as `[filename](gist_url)` in the issue body.

**Rationale**: GitHub's Issues REST API does not support direct programmatic file attachment (the web UI uses an undocumented upload endpoint). The repository contents API and Gist API are both well-documented, stable, and available with the existing GitHub token. Using the repository contents API for images keeps assets co-located with the project and produces predictable raw URLs. Using Gists for documents provides a clean, shareable link for each file. The backend handles all GitHub API interactions, abstracting the upload mechanism from the frontend. Client-side validation prevents unnecessary network requests for invalid files.

**Alternatives Considered**:
- **Direct frontend upload to GitHub**: Rejected — requires exposing GitHub tokens to the frontend; CORS restrictions; the backend already manages GitHub authentication.
- **Store files in local SQLite as BLOBs**: Rejected — files need to be accessible via GitHub Issue URLs, not local storage.
- **Third-party file hosting (S3, Cloudflare R2)**: Rejected — adds external dependency, costs, and configuration; GitHub-native hosting is sufficient and free.

---

## R5: File Validation Rules

**Task**: Define the allowed file types and size limits for chat file uploads.

**Decision**: Apply the following validation rules on the client side (with server-side enforcement):

| Constraint | Value |
|-----------|-------|
| Max file size | 10 MB per file |
| Max files per message | 5 |
| Allowed image types | `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.svg` |
| Allowed document types | `.pdf`, `.txt`, `.md`, `.csv`, `.json`, `.yaml`, `.yml` |
| Allowed archive types | `.zip` |
| Blocked types | Executables (`.exe`, `.sh`, `.bat`, `.cmd`), scripts (`.js`, `.py`, `.rb`) |

**Rationale**: The 10 MB limit matches GitHub's own file size limit for issue attachments (spec technical note: "max 10MB per GitHub constraints"). The allowed types cover common use cases: screenshots (images), documentation (PDF, text, Markdown), data files (CSV, JSON, YAML), and archives. Executables and scripts are blocked for security. The 5-file limit prevents abuse while covering the "one or more files" requirement (FR-008). Client-side validation provides instant feedback; server-side enforcement prevents bypass.

**Alternatives Considered**:
- **No file type restrictions**: Rejected — security risk; users could upload malicious files.
- **25 MB limit**: Rejected — exceeds GitHub's own limit; uploads would fail at the GitHub API level.
- **Image-only uploads**: Rejected — spec explicitly mentions "images, documents, PDFs" (FR-008).

---

## R6: Voice Input Implementation

**Task**: Determine the best approach for speech-to-text transcription in the chat input.

**Decision**: Use the native Web Speech API (`SpeechRecognition` / `webkitSpeechRecognition`) for in-browser transcription. Implementation:
1. Check `window.SpeechRecognition || window.webkitSpeechRecognition` availability on component mount.
2. If available, show the microphone button; if not, show a disabled button with tooltip "Voice input not supported in this browser".
3. On click, request microphone permission via `navigator.mediaDevices.getUserMedia({ audio: true })`.
4. On permission grant, start `SpeechRecognition` with `continuous: true`, `interimResults: true`, `lang: 'en-US'`.
5. Stream interim results to the chat input field as the user speaks.
6. On stop/cancel, finalize the last result and leave text in the input for editing.
7. On permission denial, show an error toast: "Microphone access is required for voice input. Please allow microphone access in your browser settings."

**Rationale**: The Web Speech API is the zero-dependency solution that works natively in Chrome (desktop + mobile), Edge, and Safari (with webkit prefix). It provides real-time interim results for live transcription feedback (FR-012, FR-013). No API keys, no backend processing, no cost, no latency beyond the browser's built-in recognition. This aligns with Constitution Principle V (simplicity) and the P3 priority of voice input — it's the minimum viable implementation. Firefox support is limited (no SpeechRecognition), but the graceful fallback (FR-015) handles this cleanly.

**Alternatives Considered**:
- **Whisper API (OpenAI)**: Rejected for initial implementation — adds backend dependency, API costs ($0.006/min), audio streaming complexity, and latency. Suitable as a future enhancement for broader browser support and accuracy.
- **Google Cloud Speech-to-Text**: Rejected — same concerns as Whisper plus Google Cloud dependency.
- **MediaRecorder + backend transcription**: Rejected — adds complexity for recording, streaming, and server-side processing; no benefit over native Web Speech API for supported browsers.

---

## R7: Chat Toolbar UI Pattern

**Task**: Determine the UI layout for the new chat controls (AI Enhance toggle, file upload, microphone) in relation to the existing chat input.

**Decision**: Create a `ChatToolbar` component rendered directly above the chat input field (between the message list and the text input area). The toolbar contains:
1. **Left section**: AI Enhance toggle (pill-style toggle with label, similar to the `AddAgentPopover` styling pattern)
2. **Right section**: File upload button (paperclip icon) + Microphone button (mic icon)

The toolbar is always visible when the chat is open. File preview chips render between the toolbar and the input field when files are selected.

**Rationale**: Placing controls above the input (not inline within it) avoids disrupting the text input flow and follows the pattern described in the spec's UI/UX section ("persistent toolbar or popout controls panel"). The left/right split groups conceptual controls: the toggle (input processing mode) on the left, action buttons (file/voice input methods) on the right. The `AddAgentPopover` reference in the spec calls for visual consistency — matching border styles, hover states, and spacing from that component. The toolbar is always visible (not hidden behind a menu) because all four features are core to the chat experience per the spec.

**Alternatives Considered**:
- **Inline controls within the text input**: Rejected — clutters the input area; icons inside a textarea are a non-standard pattern.
- **Hidden behind a "+" menu**: Rejected — adds a click to reach frequently used controls; spec says "persistent toolbar".
- **Floating action buttons**: Rejected — overlaps content; not consistent with the existing UI patterns.
