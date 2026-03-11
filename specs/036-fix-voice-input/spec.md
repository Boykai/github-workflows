# Feature Specification: Fix Chat Microphone Voice Input — Incorrect Browser Support Detection

**Feature Branch**: `036-fix-voice-input`  
**Created**: 2026-03-11  
**Status**: Draft  
**Input**: User description: "Fix app user chat microphone support. It should allow the user to talk to the chat and send the text to the chat agent. Mic button on chat currently says 'Voice input not support in this browser' but it is supported in Firefox."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Correct Browser Support Detection Enables Voice Input (Priority: P1)

A user opens the chat interface in Firefox (version 85 or later) and sees the microphone button. Today, clicking the button displays an incorrect error message — "Voice input not support in this browser" — even though Firefox fully supports the Web Speech API via the unprefixed `SpeechRecognition` constructor. After the fix, the browser support check correctly detects `SpeechRecognition` (unprefixed) in addition to `webkitSpeechRecognition` (Chrome/Edge/Safari). The microphone button is enabled, and clicking it initiates voice capture. This also applies to Chrome, Edge, and Safari users whose browsers are equally supported.

**Why this priority**: This is the root cause of the entire issue. Without correct detection, all other voice input functionality is blocked. Fixing the detection check unblocks the microphone button for every supported browser and is the single most impactful change.

**Independent Test**: Open the chat interface in Firefox 85+, Chrome, Edge, and Safari. Confirm the microphone button is enabled (not greyed out, no false error message) in all four browsers. Click the button and confirm it initiates voice capture without errors.

**Acceptance Scenarios**:

1. **Given** a user opens the chat in Firefox 85+, **When** the page loads, **Then** the microphone button is enabled and no "not supported" message is shown.
2. **Given** a user opens the chat in Chrome, **When** the page loads, **Then** the microphone button is enabled and no "not supported" message is shown.
3. **Given** a user opens the chat in Edge, **When** the page loads, **Then** the microphone button is enabled and no "not supported" message is shown.
4. **Given** a user opens the chat in Safari (14.1+), **When** the page loads, **Then** the microphone button is enabled and no "not supported" message is shown.
5. **Given** a user opens the chat in a browser that genuinely lacks speech recognition support, **When** the page loads, **Then** the microphone button is disabled and displays "Voice input not supported in this browser."

---

### User Story 2 — Voice Capture and Transcription Flow (Priority: P1)

A user in a supported browser clicks the microphone button to speak a message. The button changes to a visible recording state (e.g., pulsing icon or color change) indicating that audio capture is active. As the user speaks, interim transcription results appear in the chat input field in real time. When the user stops speaking, the final transcription is placed in the input field, ready for the user to review and send via the existing message-send flow.

**Why this priority**: This is the core voice input workflow. Without a working capture-and-transcribe flow, the microphone button is cosmetically enabled but functionally useless. This story delivers the primary user value of hands-free message composition.

**Independent Test**: In a supported browser, click the microphone button, speak a short sentence, and stop. Confirm the button shows a recording indicator while speaking, interim text appears in the input field during speech, and the final transcription is placed in the input field when speech ends.

**Acceptance Scenarios**:

1. **Given** a user clicks the microphone button in a supported browser, **When** recording begins, **Then** the button displays a visible active/recording state (e.g., animated indicator or color change).
2. **Given** recording is active and the user speaks, **When** interim results are recognized, **Then** partial transcription text appears in the chat input field in real time.
3. **Given** the user finishes speaking, **When** speech recognition finalizes, **Then** the complete transcribed text is placed in the chat input field and the recording indicator stops.
4. **Given** the transcribed text is in the input field, **When** the user presses send, **Then** the message is delivered to the chat agent through the existing message-send flow.

---

### User Story 3 — Microphone Permission Handling (Priority: P2)

A user clicks the microphone button for the first time. The browser prompts for microphone permission. If the user grants permission, voice capture proceeds normally. If the user denies permission (or has previously blocked microphone access), the system displays a clear, actionable message explaining that microphone access was denied and guiding the user on how to re-enable permissions in their browser settings.

**Why this priority**: Permission handling is essential for a complete user experience but is secondary to the core detection fix and transcription flow. Users who deny permission still need a helpful recovery path, but this scenario is less common than the primary happy path.

**Independent Test**: In a supported browser, click the microphone button. When the permission prompt appears, deny it. Confirm a user-friendly message appears explaining that microphone access was denied and suggesting how to re-enable it. Then grant permission on retry and confirm voice capture works normally.

**Acceptance Scenarios**:

1. **Given** the user has not yet granted microphone permission, **When** they click the microphone button, **Then** the browser prompts for microphone access.
2. **Given** the user denies the microphone permission prompt, **When** the denial is detected, **Then** the system displays an actionable message explaining the denial and how to grant access in browser settings.
3. **Given** the user has previously blocked microphone access in browser settings, **When** they click the microphone button, **Then** the system detects the denial and shows the same guidance message without a browser prompt.
4. **Given** no microphone device is available on the system, **When** the user clicks the microphone button, **Then** the system displays a message indicating that no microphone was found.

---

### User Story 4 — Grammatically Correct Error Message (Priority: P2)

Today, the error message reads "Voice input not support in this browser" — a grammatical error ("not support" instead of "not supported"). After the fix, the error message is corrected to "Voice input not supported in this browser" and is only shown when the browser genuinely lacks voice input capability.

**Why this priority**: This is a low-effort, high-visibility fix that improves the perceived quality of the application. It ships alongside the detection fix but is tracked separately because it is independently testable and valuable.

**Independent Test**: Open the chat in a browser that genuinely lacks speech recognition support (or simulate by overriding the API objects). Confirm the displayed error reads "Voice input not supported in this browser" (with correct grammar).

**Acceptance Scenarios**:

1. **Given** a user opens the chat in an unsupported browser, **When** the page loads, **Then** the error message reads "Voice input not supported in this browser."
2. **Given** a user opens the chat in a supported browser, **When** the page loads, **Then** no error message is displayed at all.

---

### Edge Cases

- What happens when the user clicks the microphone button but remains silent for an extended period? The system should time out gracefully after a reasonable idle period, stop the recording indicator, and leave the input field unchanged (or show a brief informational message such as "No speech detected").
- What happens when the user navigates away from the chat while recording is active? Recording should be automatically stopped and resources released to prevent background audio capture.
- What happens when the speech recognition service encounters a network error (some browsers require an online connection for speech recognition)? The system should display a meaningful error message indicating that speech recognition is currently unavailable and suggest the user check their internet connection.
- What happens when the user rapidly clicks the microphone button on and off? The system should debounce or serialize start/stop operations to prevent race conditions or duplicate recognition sessions.
- What happens when the browser supports the API constructor but the underlying speech recognition service is unavailable (e.g., restricted enterprise environment)? The system should catch runtime errors from the recognition service and display an appropriate fallback message.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST detect voice input support by checking for both the standard unprefixed `SpeechRecognition` and the vendor-prefixed `webkitSpeechRecognition` on the window object, enabling the microphone button when either is present.
- **FR-002**: System MUST NOT display "Voice input not supported in this browser" in any browser where speech recognition capability is available, including Firefox 85+, Chrome, Edge, and Safari 14.1+.
- **FR-003**: System MUST correct the existing error message from "Voice input not support in this browser" to "Voice input not supported in this browser."
- **FR-004**: System MUST initiate voice capture and speech recognition when the user clicks the microphone button in a supported browser.
- **FR-005**: System MUST display a visible recording/active state on the microphone button (e.g., pulsing animation, color change, or animated icon) while voice capture is in progress.
- **FR-006**: System MUST populate the chat input field with transcribed text from the speech recognition results.
- **FR-007**: System MUST allow the user to send the transcribed text to the chat agent using the existing message-send flow (e.g., pressing the send button or hitting Enter).
- **FR-008**: System MUST handle microphone permission denial by displaying a user-friendly message that explains the denial and provides guidance on re-enabling microphone access in browser settings.
- **FR-009**: System MUST handle the absence of a microphone device by displaying a message indicating no microphone was detected.
- **FR-010**: System SHOULD display interim/partial transcription results in the chat input field in real time as the user speaks, replacing them with the final result when speech recognition completes.
- **FR-011**: System MUST stop recording and release audio resources when the user navigates away from the chat interface or closes the chat.
- **FR-012**: System MUST handle speech recognition runtime errors (e.g., network failures, service unavailability) gracefully, displaying a meaningful error message rather than failing silently.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The microphone button is correctly enabled in 100% of supported browsers (Firefox 85+, Chrome, Edge, Safari 14.1+) with zero false-negative "not supported" messages.
- **SC-002**: Users can complete the full voice-to-message flow (click mic → speak → see transcription → send message) in under 30 seconds for a typical sentence.
- **SC-003**: The error message displays correct grammar ("not supported") in 100% of unsupported browser scenarios.
- **SC-004**: When microphone permission is denied, 100% of users see an actionable guidance message within 2 seconds of the denial.
- **SC-005**: Recording state indicator is visible within 1 second of clicking the microphone button, and disappears within 1 second of speech ending.
- **SC-006**: Interim transcription results appear in the input field within 2 seconds of the user beginning to speak.
- **SC-007**: Zero orphaned audio capture sessions remain active after the user navigates away from the chat interface.

### Assumptions

- Firefox 85+ is the minimum version required for unprefixed `SpeechRecognition` support. Users on older Firefox versions will correctly see the unsupported message.
- Safari 14.1+ is the minimum version for Web Speech API support. Earlier Safari versions will correctly see the unsupported message.
- The existing chat input field and message-send flow are functioning correctly and do not require changes beyond receiving transcribed text.
- Microphone hardware is available on the user's device (absence is handled by FR-009 as an edge case, not a primary scenario).
- The application is served over HTTPS, which is required by browsers for microphone access via `getUserMedia`.
