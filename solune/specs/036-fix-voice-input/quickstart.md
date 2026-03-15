# Quickstart: Fix Chat Microphone Voice Input — Incorrect Browser Support Detection

**Branch**: `036-fix-voice-input` | **Date**: 2026-03-11

## Overview

This guide walks through the voice input implementation for the chat interface. The fix corrects browser support detection (Firefox false negative), adds a `useVoiceInput` hook for speech recognition, and provides a `VoiceInputButton` component with visual recording states.

## 1. Browser Support Detection (The Root Cause Fix)

### Before

```typescript
// ❌ Only checks webkit prefix — misses Firefox's unprefixed API
const isSupported = 'webkitSpeechRecognition' in window;
```

### After

```typescript
// ✅ Checks both standard and vendor-prefixed constructors
function getSpeechRecognitionConstructor(): (new () => SpeechRecognitionInstance) | null {
  const win = window as any;
  return win.SpeechRecognition || win.webkitSpeechRecognition || null;
}
```

**Why**: Firefox 85+ implements the W3C standard unprefixed `SpeechRecognition`. Chrome/Edge/Safari use `webkitSpeechRecognition`. Checking both covers all modern browsers.

## 2. Using the `useVoiceInput` Hook

```typescript
import { useVoiceInput } from '@/hooks/useVoiceInput';

function MyChatComponent() {
  const [inputText, setInputText] = useState('');

  // Callback receives final transcribed text
  const handleTranscript = useCallback((text: string) => {
    setInputText(prev => prev ? `${prev} ${text}` : text);
  }, []);

  const {
    isSupported,    // boolean — does browser support speech recognition?
    isRecording,    // boolean — is voice capture active?
    interimTranscript, // string — partial text while user speaks
    error,          // string | null — error message if something went wrong
    startRecording, // () => void — begin voice capture
    stopRecording,  // () => void — stop gracefully (waits for final result)
    cancelRecording // () => void — abort immediately (discards pending)
  } = useVoiceInput(handleTranscript);

  // Toggle recording on button click
  const handleToggle = () => {
    isRecording ? stopRecording() : startRecording();
  };

  return (
    <div>
      <input value={inputText} onChange={e => setInputText(e.target.value)} />
      {interimTranscript && <span className="text-muted">{interimTranscript}</span>}
      <button onClick={handleToggle} disabled={!isSupported}>
        {isRecording ? 'Stop' : 'Start'} Recording
      </button>
      {error && <p className="text-destructive">{error}</p>}
    </div>
  );
}
```

## 3. VoiceInputButton Component

The `VoiceInputButton` renders three visual states:

```tsx
import { VoiceInputButton } from '@/components/chat/VoiceInputButton';

// In your toolbar:
<VoiceInputButton
  isSupported={isVoiceSupported}
  isRecording={isRecording}
  onToggle={handleVoiceToggle}
  error={voiceError}
/>
```

### Visual States

| State | Icon | Animation | Color |
|-------|------|-----------|-------|
| Unsupported | `MicOff` | None | Muted 50% |
| Ready | `Mic` | None | Muted (red if error) |
| Recording | `Square` | `mic-recording-pulse` | Red/destructive |

## 4. Integration in ChatToolbar

The `ChatToolbar` wraps `VoiceInputButton` with a `Tooltip` and manages the tooltip content:

```tsx
<Tooltip
  content={
    !isVoiceSupported
      ? 'Voice input is not supported in this browser.'
      : isRecording
        ? 'Click to stop recording.'
        : voiceError
          ? voiceError
          : undefined
  }
  contentKey={
    isVoiceSupported && !isRecording && !voiceError
      ? 'chat.toolbar.voiceButton'
      : undefined
  }
>
  <VoiceInputButton
    isSupported={isVoiceSupported}
    isRecording={isRecording}
    onToggle={onVoiceToggle}
    error={voiceError}
  />
</Tooltip>
```

## 5. Integration in ChatInterface

The `ChatInterface` wires everything together:

```tsx
// 1. Import the hook
import { useVoiceInput } from '@/hooks/useVoiceInput';

// 2. Handle transcription — append to input, clear any autocomplete tokens
const handleVoiceTranscript = useCallback(
  (text: string) => {
    clearTokens();
    setInput((prev) => (prev ? `${prev} ${text}` : text));
  },
  [clearTokens]
);

// 3. Initialize the hook
const {
  isSupported: isVoiceSupported,
  isRecording,
  interimTranscript,
  error: voiceError,
  startRecording,
  stopRecording,
} = useVoiceInput(handleVoiceTranscript);

// 4. Create toggle handler
const handleVoiceToggle = useCallback(() => {
  isRecording ? stopRecording() : startRecording();
}, [isRecording, startRecording, stopRecording]);

// 5. Pass to ChatToolbar
<ChatToolbar
  isRecording={isRecording}
  isVoiceSupported={isVoiceSupported}
  onVoiceToggle={handleVoiceToggle}
  voiceError={voiceError}
  // ...other props
/>
```

## 6. CSS Animation

The recording pulse animation is defined in `frontend/src/index.css`:

```css
/* Custom property (in @theme block) */
--animate-mic-recording: mic-recording-pulse 1.5s ease-in-out infinite;

/* Keyframes */
@keyframes mic-recording-pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 transparent;
  }
  50% {
    box-shadow: 0 0 0 6px hsl(var(--destructive) / 0.2);
  }
}

/* Utility class */
.mic-recording-pulse {
  animation: var(--animate-mic-recording);
}
```

## 7. Error Handling Summary

| Error Condition | User Sees |
|----------------|-----------|
| Browser lacks speech API | Disabled mic button + tooltip: "Voice input is not supported in this browser." |
| Microphone permission denied | Red mic button + tooltip: "Microphone access is required for voice input. Please allow microphone access in your browser settings." |
| No mediaDevices API | Red mic button + tooltip: "Microphone access is not available in this browser." |
| Speech recognition error | Red mic button + tooltip: "Voice input error: {error}" |
| No error | Normal mic button + tooltip: "Use your microphone to dictate a message instead of typing." |

## Files Changed

| File | Change Type | Description |
|------|------------|-------------|
| `frontend/src/hooks/useVoiceInput.ts` | NEW | Web Speech API hook with detection, recording, transcription, error handling |
| `frontend/src/components/chat/VoiceInputButton.tsx` | NEW | Microphone button with 3 visual states |
| `frontend/src/components/chat/ChatToolbar.tsx` | MODIFIED | Added VoiceInputButton integration with tooltip wiring |
| `frontend/src/components/chat/ChatInterface.tsx` | MODIFIED | Wired useVoiceInput hook and passed props to ChatToolbar |
| `frontend/src/constants/tooltip-content.ts` | MODIFIED | Added voice button tooltip entry |
| `frontend/src/index.css` | MODIFIED | Added mic-recording-pulse keyframe animation |
