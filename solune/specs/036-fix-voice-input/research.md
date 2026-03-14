# Research: Fix Chat Microphone Voice Input — Incorrect Browser Support Detection

**Branch**: `036-fix-voice-input` | **Date**: 2026-03-11

## Research Tasks & Findings

### R-001: Root Cause — Browser Support Detection Logic

**Context**: FR-001 requires detecting both unprefixed `SpeechRecognition` and vendor-prefixed `webkitSpeechRecognition`. The current implementation needs auditing to determine why Firefox reports as unsupported.

**Findings**:
- The original browser support check likely tested only `window.webkitSpeechRecognition` (Chrome/Edge vendor prefix) or used an incorrect detection pattern that missed Firefox's unprefixed `SpeechRecognition` constructor (available since Firefox 85+, released January 2021).
- Firefox implements the standard unprefixed `window.SpeechRecognition` — it does NOT use the `webkit` prefix.
- Chrome, Edge, and older Safari versions expose `window.webkitSpeechRecognition`. Modern Chrome also exposes the unprefixed `window.SpeechRecognition`.
- Safari 14.1+ supports Web Speech API via `webkitSpeechRecognition`.
- The Web Speech API is a browser-native API — no polyfills or external libraries are needed.

**Decision**: Create a `getSpeechRecognitionConstructor()` utility function that checks `window.SpeechRecognition || window.webkitSpeechRecognition`, returning whichever is available (or `null` if neither exists). This covers all modern browsers.

**Rationale**:
1. Checking the unprefixed API first follows the W3C recommendation for feature detection.
2. Falling back to `webkitSpeechRecognition` ensures backward compatibility with older browser versions.
3. A single utility function centralizes the detection logic, making it testable and maintainable.

**Alternatives Considered**:
- **UA string sniffing**: Rejected — fragile, unreliable, violates feature-detection best practices.
- **MediaRecorder fallback with server-side STT**: Rejected — adds backend dependency and latency; Web Speech API handles speech-to-text natively in the browser.
- **Third-party speech recognition library (e.g., annyang)**: Rejected — unnecessary dependency; the native API is sufficient and well-supported.

---

### R-002: Microphone Permission Handling Strategy

**Context**: FR-008 and FR-009 require graceful handling of microphone permission denial and missing microphone hardware. Need to determine the best approach for requesting permissions and handling errors.

**Findings**:
- `navigator.mediaDevices.getUserMedia({ audio: true })` is the standard API for requesting microphone access across all browsers.
- The `getUserMedia` call triggers the browser's native permission prompt on first use. On subsequent calls, the browser uses the cached permission decision.
- Permission denial throws a `DOMException` with `name === 'NotAllowedError'`.
- Missing microphone hardware throws a `DOMException` with `name === 'NotFoundError'`.
- Some browsers (particularly Firefox) may also surface permission issues through the SpeechRecognition `onerror` event with `error === 'not-allowed'`.
- The Permissions API (`navigator.permissions.query({ name: 'microphone' })`) can check permission state without triggering a prompt, but has inconsistent browser support and is not needed for this use case.

**Decision**: Pre-flight the microphone permission by calling `getUserMedia({ audio: true })` before starting `SpeechRecognition`. This ensures the user sees the permission prompt before any recognition attempt, and allows us to catch `NotAllowedError` / `NotFoundError` explicitly. The obtained stream is immediately stopped (tracks released) since we only need the permission grant — `SpeechRecognition` handles its own audio capture.

**Rationale**:
1. Pre-flighting avoids a confusing UX where `SpeechRecognition.start()` silently fails or shows a cryptic error when permission is denied.
2. Stopping the stream immediately avoids holding an unnecessary audio capture session open.
3. Error differentiation (`NotAllowedError` vs. `NotFoundError`) enables specific, actionable error messages for each scenario.

**Alternatives Considered**:
- **Skip pre-flight, rely on SpeechRecognition.onerror**: Rejected — `onerror` events have inconsistent error codes across browsers; `getUserMedia` errors are standardized.
- **Keep the stream open for dual use**: Rejected — `SpeechRecognition` manages its own audio pipeline; keeping an extra stream wastes resources and can interfere with the recognition engine.
- **Use Permissions API to check before prompting**: Rejected — inconsistent support; adds complexity without user-facing benefit.

---

### R-003: Interim Transcription and Final Result Flow

**Context**: FR-006 and FR-010 require both interim (partial) and final transcription results to be displayed in the chat input field. Need to determine how to configure the Web Speech API and how to wire results into React state.

**Findings**:
- `SpeechRecognition.interimResults = true` enables interim (non-final) results in the `onresult` event. Each result in the `SpeechRecognitionResultList` has an `isFinal` boolean.
- `SpeechRecognition.continuous = true` keeps the recognition session alive after each final result, allowing the user to speak multiple sentences without re-clicking the mic button.
- The `onresult` event fires repeatedly as the speech engine refines its hypothesis. The `resultIndex` property indicates which results are new since the last event.
- Interim results should be displayed in the input field as a visual preview but NOT committed as the final value. Final results should be appended to the input field content.

**Decision**: Configure `SpeechRecognition` with `continuous: true` and `interimResults: true`. In the `onresult` handler, iterate from `event.resultIndex` to `event.results.length`. Accumulate interim (non-final) transcripts into a separate `interimTranscript` state. When a result is marked `isFinal`, pass it to the `onTranscript` callback which appends it to the chat input. The interim transcript is displayed as a visual indicator but cleared when the final result arrives.

**Rationale**:
1. `continuous: true` avoids forcing the user to click the mic button for each sentence.
2. Separating interim and final transcripts prevents flickering or overwriting in the input field.
3. Appending (rather than replacing) supports multi-sentence dictation where the user speaks, pauses, speaks again.

**Alternatives Considered**:
- **Replace input on each interim result**: Rejected — causes jarring UX when interim text fluctuates as the engine refines its hypothesis; final-only replacement is smoother.
- **Non-continuous mode**: Rejected — requires re-clicking mic for each sentence; poor UX for dictation.

---

### R-004: Recording State Visual Indicator

**Context**: FR-005 requires a visible recording/active state on the microphone button. Need to determine the visual design pattern.

**Findings**:
- The codebase uses Lucide React icons (`Mic`, `MicOff`, `Square`) for toolbar actions.
- The `celestial-focus` class is the project's standard focus-visible styling for interactive elements.
- A CSS pulsing animation is a common pattern for recording indicators — it provides clear visual feedback without requiring complex SVG animations.
- The button should have 3 distinct visual states: (1) disabled/unsupported (greyed `MicOff` icon), (2) ready/idle (`Mic` icon), (3) recording (`Square` stop icon with red pulse).

**Decision**: Implement a `mic-recording-pulse` CSS keyframe animation that pulses the button's `box-shadow` between transparent and a semi-transparent destructive color. Apply it to the button during recording state. Use `Square` (stop) icon during recording and `Mic` icon during idle. Use `MicOff` icon when unsupported.

**Rationale**:
1. Pure CSS animation avoids JS timer overhead and runs smoothly at 60fps.
2. The destructive (red) color palette signals "active recording" consistently with the app's existing danger/destructive semantic.
3. Three distinct states with different icons + colors are easily distinguishable for users, including those with color vision deficiencies (icon shape changes, not just color).

**Alternatives Considered**:
- **JS-driven animation (e.g., `requestAnimationFrame`)**: Rejected — CSS animations are more performant and simpler for a pulsing effect.
- **GIF or Lottie animation**: Rejected — adds asset/dependency weight for a simple pulse effect.
- **Color change only (no animation)**: Rejected — static color change is less noticeable; animation draws attention to the active recording state.

---

### R-005: Resource Cleanup and Navigation Safety

**Context**: FR-011 requires stopping recording and releasing audio resources when the user navigates away. Need to determine how to implement cleanup in a React context.

**Findings**:
- React's `useEffect` cleanup function runs on component unmount, which happens when the user navigates away from the chat interface.
- `SpeechRecognition.abort()` immediately stops the recognition session and discards any pending results (unlike `.stop()` which waits for the last result).
- The pre-flight `getUserMedia` stream is stopped immediately after permission check, so no long-lived stream to clean up.
- The `recognitionRef` (React ref) holds the active `SpeechRecognition` instance, enabling cleanup from the effect without stale closure issues.

**Decision**: Use a `useEffect` cleanup function in `useVoiceInput` that calls `recognitionRef.current.abort()` and nulls the ref on unmount. This ensures zero orphaned capture sessions regardless of how the user navigates away.

**Rationale**:
1. `useEffect` cleanup is the standard React pattern for resource management on unmount.
2. `abort()` is more aggressive than `stop()` — appropriate for navigation away, where we don't need the final result.
3. Using a ref avoids closure staleness issues that would occur with state.

**Alternatives Considered**:
- **`beforeunload` event listener**: Rejected — only fires on full page unload, not SPA navigation.
- **`visibilitychange` event listener**: Rejected — triggers on tab switch, not navigation; would stop recording when user switches tabs temporarily.
- **Global state management for recording lifecycle**: Rejected — over-engineering; the hook's lifecycle is sufficient since it's tied to the chat component mount/unmount.

---

### R-006: Error Message Grammar and UX Copy

**Context**: FR-003 requires fixing the typo in the error message ("not support" → "not supported") and FR-012 requires graceful error handling for runtime speech recognition errors.

**Findings**:
- The original error string "Voice input not support in this browser" has a grammatical error (missing past participle).
- The codebase uses clear, grammatically correct error messages in other components (e.g., "Microphone access is not available in this browser").
- Error messages should be specific and actionable where possible — "Voice input error: network" is less helpful than a message explaining what the user can do.

**Decision**: Use the following error message hierarchy:
1. **Unsupported browser**: "Voice input is not supported in this browser." (aria-label: "Voice input not supported")
2. **Permission denied**: "Microphone access is required for voice input. Please allow microphone access in your browser settings."
3. **No microphone**: "Microphone access is not available in this browser."
4. **Runtime errors**: "Voice input error: {error}" (for speech recognition service errors like network, audio-capture, etc.)

**Rationale**:
1. Each error has a distinct, actionable message — users know what happened and what to do.
2. The grammar fix ("not supported") is applied consistently across the aria-label and tooltip.
3. Runtime errors include the specific error code to aid debugging without exposing technical jargon.

**Alternatives Considered**:
- **Single generic error message for all failures**: Rejected — not actionable; users can't distinguish between a browser limitation and a permission issue.
- **Toast notifications for errors**: Rejected — adds dependency and pattern not currently used in the chat interface; inline error state on the button is sufficient.
