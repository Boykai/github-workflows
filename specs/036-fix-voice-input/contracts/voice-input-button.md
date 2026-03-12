# Contract: VoiceInputButton Component

**Branch**: `036-fix-voice-input` | **Date**: 2026-03-11
**File**: `frontend/src/components/chat/VoiceInputButton.tsx`

## Purpose

Renders the microphone button with three distinct visual states: disabled (unsupported browser), ready (idle), and recording (active). Provides accessible labels and visual indicators for each state.

## Interface

```typescript
interface VoiceInputButtonProps {
  isSupported: boolean;
  isRecording: boolean;
  onToggle: () => void;
  error: string | null;
}

export function VoiceInputButton(props: VoiceInputButtonProps): JSX.Element;
```

### Props

| Prop | Type | Description |
|------|------|-------------|
| `isSupported` | `boolean` | Whether browser supports voice input. Determines disabled vs. interactive state. |
| `isRecording` | `boolean` | Whether voice capture is currently active. Controls recording visual indicator. |
| `onToggle` | `() => void` | Called when user clicks the button (both to start and stop recording). |
| `error` | `string \| null` | Current error message. Affects button color (destructive when error present). |

## Visual States

### State 1: Unsupported (`isSupported === false`)

- **Icon**: `MicOff` (Lucide) at `w-4 h-4`
- **Button**: `w-8 h-8`, rounded-full, disabled, cursor-not-allowed
- **Color**: `text-muted-foreground/50` (50% opacity muted)
- **Aria Label**: `"Voice input not supported"`
- **Interaction**: None (button is disabled)

### State 2: Recording (`isSupported && isRecording`)

- **Icon**: `Square` (Lucide) at `w-3.5 h-3.5 fill-current` (filled stop icon)
- **Button**: `w-8 h-8`, rounded-full, `mic-recording-pulse` animation class
- **Color**: `bg-destructive/10 text-destructive` (red tint background, red icon)
- **Hover**: `bg-destructive/20`
- **Aria Label**: `"Stop recording"`
- **Focus**: `celestial-focus` class applied
- **Interaction**: Clicking calls `onToggle()` to stop recording

### State 3: Ready/Idle (`isSupported && !isRecording`)

- **Icon**: `Mic` (Lucide) at `w-4 h-4`
- **Button**: `w-8 h-8`, rounded-full
- **Color (no error)**: `text-muted-foreground`, hover: `text-foreground hover:bg-primary/10`
- **Color (with error)**: `text-destructive`
- **Aria Label (no error)**: `"Start voice input"`
- **Aria Label (with error)**: `"Voice input error — click to retry"`
- **Focus**: `celestial-focus` class applied
- **Interaction**: Clicking calls `onToggle()` to start recording

## CSS Animation: `mic-recording-pulse`

```css
@keyframes mic-recording-pulse {
  0%, 100% { box-shadow: 0 0 0 0 transparent; }
  50% { box-shadow: 0 0 0 6px hsl(var(--destructive) / 0.2); }
}

.mic-recording-pulse {
  animation: var(--animate-mic-recording);
}
```

- Defined as a CSS custom property: `--animate-mic-recording: mic-recording-pulse 1.5s ease-in-out infinite`
- Applied via the `.mic-recording-pulse` utility class
- Produces a pulsing red glow effect around the button during recording

## Behavioral Contract

### Accessibility (All States)

- **MUST** use `<button type="button">` (not anchor or div).
- **MUST** provide descriptive `aria-label` for each state (screen reader support).
- **MUST** include `celestial-focus` class on interactive states (keyboard focus ring).
- **MUST** use `disabled` attribute when unsupported (prevents focus and click).
- **MUST** use `focus-visible:outline-none` to prevent double focus ring (celestial-focus handles it).

### Visual Feedback (FR-005)

- **MUST** display pulsing animation within 1 frame of `isRecording` becoming `true`.
- **MUST** stop animation within 1 frame of `isRecording` becoming `false`.
- **MUST** use red/destructive color to signal active recording (consistent with app's semantic palette).
- **MUST** change icon from `Mic` to `Square` (stop) during recording to indicate the click action.

### Integration

- **MUST** be wrapped in a `<Tooltip>` by the parent `ChatToolbar` for extended text display.
- **MUST NOT** manage its own tooltip — the parent controls tooltip content based on combined state.
- **MUST NOT** manage recording state — receives all state via props from parent.

## Acceptance Criteria

1. Button is visually disabled and shows `MicOff` when `isSupported` is `false`.
2. Button shows pulsing red `Square` when `isRecording` is `true`.
3. Button shows `Mic` icon with muted color when idle and no error.
4. Button shows `Mic` icon with destructive color when idle with error.
5. All three states have distinct, descriptive `aria-label` values.
6. Clicking the button in any interactive state calls `onToggle()` exactly once.
