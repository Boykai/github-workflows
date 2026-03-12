# Data Model: Fix Chat Microphone Voice Input — Incorrect Browser Support Detection

**Branch**: `036-fix-voice-input` | **Date**: 2026-03-11

## Overview

This feature is frontend-only with no persistent data storage. The "data model" describes the TypeScript types, state shape, and component interfaces that define the voice input system.

## State Model: `useVoiceInput` Hook

### Return Type

```typescript
interface UseVoiceInputReturn {
  /** Whether the browser supports the Web Speech API */
  isSupported: boolean;
  /** Whether voice capture is currently active */
  isRecording: boolean;
  /** Partial transcription text while user is still speaking */
  interimTranscript: string;
  /** Human-readable error message, or null if no error */
  error: string | null;
  /** Begin voice capture and speech recognition */
  startRecording: () => void;
  /** Stop recording gracefully (waits for final result) */
  stopRecording: () => void;
  /** Abort recording immediately (discards pending results) */
  cancelRecording: () => void;
}
```

### Internal State

| State Variable | Type | Initial Value | Updated By |
|---------------|------|---------------|------------|
| `isSupported` | `boolean` | `getSpeechRecognitionConstructor() !== null` | Set once on hook initialization (lazy `useState`) |
| `isRecording` | `boolean` | `false` | Set `true` on `recognition.start()`, `false` on `onerror` / `onend` / manual stop |
| `interimTranscript` | `string` | `''` | Updated on each `onresult` event with non-final results; cleared on `onend` or `cancelRecording` |
| `error` | `string \| null` | `null` | Set on `getUserMedia` rejection, `onerror` event, or unsupported browser; cleared on `startRecording` |
| `recognitionRef` | `React.MutableRefObject<SpeechRecognitionInstance \| null>` | `null` | Set on `startRecording` (new instance), nulled on stop/abort/unmount |

### State Transitions

```text
                     ┌─────────────┐
                     │   IDLE      │
                     │ isRecording │
                     │   = false   │
                     └──────┬──────┘
                            │ startRecording()
                            │ → getUserMedia()
                            │ → new SpeechRecognition()
                            │ → recognition.start()
                            ▼
                     ┌─────────────┐
              ┌──────│  RECORDING  │──────┐
              │      │ isRecording │      │
              │      │   = true    │      │
              │      └──────┬──────┘      │
              │             │             │
     stopRecording()   onerror()    cancelRecording()
     → .stop()                      → .abort()
              │             │             │
              ▼             ▼             ▼
        ┌───────────┐ ┌──────────┐ ┌───────────┐
        │ FINALIZING│ │  ERROR   │ │ CANCELLED │
        │ (onend    │ │ error set│ │ interim   │
        │  fires)   │ │ isRec=F  │ │ cleared   │
        └─────┬─────┘ └──────────┘ └─────┬─────┘
              │                           │
              └───────────┬───────────────┘
                          ▼
                   ┌─────────────┐
                   │    IDLE     │
                   └─────────────┘
```

## Browser API Detection

### `getSpeechRecognitionConstructor()` Function

```typescript
function getSpeechRecognitionConstructor(): (new () => SpeechRecognitionInstance) | null {
  const win = window as any;
  return win.SpeechRecognition || win.webkitSpeechRecognition || null;
}
```

**Browser Coverage**:

| Browser | API Available | Constructor |
|---------|--------------|-------------|
| Firefox 85+ | ✅ | `window.SpeechRecognition` (unprefixed) |
| Chrome | ✅ | `window.webkitSpeechRecognition` (also unprefixed in recent versions) |
| Edge | ✅ | `window.webkitSpeechRecognition` (Chromium-based) |
| Safari 14.1+ | ✅ | `window.webkitSpeechRecognition` |
| Older browsers | ❌ | Neither available → returns `null` |

## Web Speech API Type Definitions

These are local type definitions to augment the `Window` interface for TypeScript, since the Web Speech API types are not included in the default `lib.dom.d.ts`.

```typescript
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;     // 'not-allowed' | 'aborted' | 'network' | 'audio-capture' | ...
  message?: string;
}

type SpeechRecognitionInstance = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
};
```

## Component Props Model

### `VoiceInputButton` Props

```typescript
interface VoiceInputButtonProps {
  /** Whether the browser supports voice input */
  isSupported: boolean;
  /** Whether voice capture is currently active */
  isRecording: boolean;
  /** Toggle recording on/off */
  onToggle: () => void;
  /** Current error message to reflect in button styling */
  error: string | null;
}
```

**Visual State Mapping**:

| `isSupported` | `isRecording` | `error` | Icon | Style | Aria Label |
|:---:|:---:|:---:|:---:|:---:|:---:|
| `false` | — | — | `MicOff` | Greyed, disabled, cursor-not-allowed | "Voice input not supported" |
| `true` | `true` | — | `Square` | Red pulse animation, destructive bg | "Stop recording" |
| `true` | `false` | truthy | `Mic` | Red text (destructive) | "Voice input error — click to retry" |
| `true` | `false` | `null` | `Mic` | Muted text, hover highlight | "Start voice input" |

### `ChatToolbar` Voice Props (subset)

```typescript
// Props added to existing ChatToolbar interface:
{
  isRecording: boolean;
  isVoiceSupported: boolean;
  onVoiceToggle: () => void;
  voiceError: string | null;
}
```

## Error Message Catalog

| Trigger | Message | Location |
|---------|---------|----------|
| Browser lacks SpeechRecognition API | "Voice input is not supported in this browser." | Tooltip on disabled button |
| `getUserMedia` rejected (NotAllowedError) | "Microphone access is required for voice input. Please allow microphone access in your browser settings." | Error state on button |
| `getUserMedia` rejected (NotFoundError / other) | "Microphone access is required for voice input. Please allow microphone access in your browser settings." | Error state on button |
| `navigator.mediaDevices` unavailable | "Microphone access is not available in this browser." | Error state on button |
| SpeechRecognition `onerror` (not-allowed) | "Microphone access is required for voice input. Please allow microphone access in your browser settings." | Error state on button |
| SpeechRecognition `onerror` (other) | "Voice input error: {error}" | Error state on button |

## Entity Relationship Diagram

```text
ChatInterface
  │
  ├── useVoiceInput(onTranscript)  →  { isSupported, isRecording, interimTranscript, error, start, stop, cancel }
  │     │
  │     ├── getSpeechRecognitionConstructor()  →  SpeechRecognition | webkitSpeechRecognition | null
  │     ├── navigator.mediaDevices.getUserMedia({ audio: true })  →  Permission grant/deny
  │     └── SpeechRecognitionInstance  →  onresult / onerror / onend events
  │
  └── ChatToolbar
        │
        └── VoiceInputButton({ isSupported, isRecording, onToggle, error })
              │
              ├── State: Disabled  →  MicOff icon, tooltip: "not supported"
              ├── State: Ready     →  Mic icon, tooltip: "dictate a message"
              ├── State: Recording →  Square icon + mic-recording-pulse animation
              └── State: Error     →  Mic icon (red), tooltip: error message
```
