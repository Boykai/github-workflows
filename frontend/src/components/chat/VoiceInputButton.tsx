/**
 * Voice input button component.
 * Microphone icon that toggles recording with state indicator.
 * Hidden/disabled when browser doesn't support Web Speech API.
 */

import { Mic, MicOff } from 'lucide-react';

interface VoiceInputButtonProps {
  isRecording: boolean;
  isSupported: boolean;
  error: string | null;
  onToggle: () => void;
  disabled?: boolean;
}

export function VoiceInputButton({
  isRecording,
  isSupported,
  error,
  onToggle,
  disabled,
}: VoiceInputButtonProps) {
  if (!isSupported) {
    return (
      <button
        type="button"
        disabled
        aria-label="Voice input not supported in this browser"
        title="Voice input not supported in this browser"
        className="w-9 h-9 flex items-center justify-center rounded-lg text-muted-foreground/50 cursor-not-allowed"
      >
        <MicOff size={18} />
      </button>
    );
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={onToggle}
        disabled={disabled}
        aria-label={isRecording ? 'Stop recording' : 'Start voice input'}
        aria-pressed={isRecording}
        className={`w-9 h-9 flex items-center justify-center rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:opacity-50 disabled:cursor-not-allowed ${
          isRecording
            ? 'text-destructive bg-destructive/10 hover:bg-destructive/20'
            : 'text-muted-foreground hover:text-foreground hover:bg-muted'
        }`}
      >
        <Mic size={18} />
      </button>

      {/* Permission error tooltip */}
      {error && (
        <div
          role="alert"
          className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 rounded-lg bg-destructive/10 border border-destructive/30 text-destructive text-xs whitespace-nowrap max-w-[250px] text-wrap z-50"
        >
          {error}
        </div>
      )}
    </div>
  );
}
