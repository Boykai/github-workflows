# Contract: useVoiceInput Hook

**Branch**: `036-fix-voice-input` | **Date**: 2026-03-11
**File**: `frontend/src/hooks/useVoiceInput.ts`

## Purpose

Encapsulates all Web Speech API interaction, browser support detection, microphone permission handling, and transcription state management. Consumers receive a clean interface without needing to understand browser API details.

## Interface

```typescript
export function useVoiceInput(onTranscript: (text: string) => void): UseVoiceInputReturn;
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `onTranscript` | `(text: string) => void` | Callback invoked with each final transcription result. Called once per finalized speech segment. |

### Return Value

| Property | Type | Description |
|----------|------|-------------|
| `isSupported` | `boolean` | `true` if browser has `SpeechRecognition` or `webkitSpeechRecognition`. Computed once on mount, never changes. |
| `isRecording` | `boolean` | `true` while voice capture is active. |
| `interimTranscript` | `string` | Current partial transcription while user is speaking. Empty string when not recording. |
| `error` | `string \| null` | Human-readable error message, or `null`. Cleared on next `startRecording()` call. |
| `startRecording` | `() => void` | Initiates microphone permission check, then starts speech recognition. No-op if already recording. |
| `stopRecording` | `() => void` | Gracefully stops recognition (waits for final result). |
| `cancelRecording` | `() => void` | Immediately aborts recognition, discarding pending results. Clears interim transcript. |

## Behavioral Contract

### Browser Detection (FR-001, FR-002, FR-003)

- **MUST** check `window.SpeechRecognition` (unprefixed, Firefox 85+) first, then `window.webkitSpeechRecognition` (Chrome/Edge/Safari).
- **MUST** return `isSupported: true` when either constructor is available.
- **MUST** return `isSupported: false` only when neither constructor exists.
- **MUST NOT** use user-agent sniffing for detection.

### Permission Handling (FR-008, FR-009)

- **MUST** request microphone permission via `navigator.mediaDevices.getUserMedia({ audio: true })` before starting recognition.
- **MUST** immediately release the obtained MediaStream (stop all tracks) — the stream is only used for permission acquisition.
- **MUST** set `error` to a permission-specific message when `getUserMedia` rejects.
- **MUST** set `error` when `navigator.mediaDevices` is unavailable (non-HTTPS or very old browser).

### Recording Lifecycle (FR-004, FR-005, FR-011)

- **MUST** create a new `SpeechRecognition` instance on each `startRecording()` call.
- **MUST** configure `continuous: true` and `interimResults: true`.
- **MUST** set `isRecording: true` synchronously after `recognition.start()`.
- **MUST** set `isRecording: false` on `onend`, `onerror`, `stopRecording()`, or `cancelRecording()`.
- **MUST** abort the active recognition instance and null the ref on component unmount (`useEffect` cleanup).

### Transcription Flow (FR-006, FR-010)

- **MUST** iterate results from `event.resultIndex` to `event.results.length` in `onresult`.
- **MUST** separate interim results (`isFinal === false`) from final results (`isFinal === true`).
- **MUST** update `interimTranscript` state with accumulated interim text.
- **MUST** invoke `onTranscript(finalText)` for each batch of final results.
- **MUST** clear `interimTranscript` on `onend` and `cancelRecording()`.

### Error Handling (FR-008, FR-012)

- **MUST** catch `not-allowed` and `permission-denied` errors from `SpeechRecognition.onerror` and set a permission-specific error message.
- **MUST** ignore `aborted` errors (caused by intentional `cancelRecording()`).
- **MUST** set a descriptive error for all other speech recognition errors.
- **MUST** clear any previous error at the start of `startRecording()`.

## Acceptance Criteria

1. `isSupported` returns `true` in Firefox 85+, Chrome, Edge, and Safari 14.1+.
2. `isSupported` returns `false` in browsers lacking both `SpeechRecognition` and `webkitSpeechRecognition`.
3. `startRecording()` triggers browser microphone permission prompt on first call.
4. `error` is set with actionable message when permission is denied.
5. `interimTranscript` updates in real time as the user speaks.
6. `onTranscript` callback fires with final transcribed text when speech segment completes.
7. No orphaned `SpeechRecognition` instances after component unmount.
