/**
 * VoiceInputButton — microphone button with recording state indicator.
 * Shows pulsing animation when recording, disabled state when unsupported.
 */

import { Mic, MicOff, Square } from 'lucide-react';
import { cn } from '@/lib/utils';

interface VoiceInputButtonProps {
  isSupported: boolean;
  isRecording: boolean;
  onToggle: () => void;
  error: string | null;
}

export function VoiceInputButton({
  isSupported,
  isRecording,
  onToggle,
  error,
}: VoiceInputButtonProps) {
  if (!isSupported) {
    return (
      <button
        type="button"
        disabled
        className="w-8 h-8 flex items-center justify-center rounded-full text-muted-foreground/50 cursor-not-allowed"
        title="Voice input not supported in this browser"
        aria-label="Voice input not supported"
      >
        <MicOff className="w-4 h-4" />
      </button>
    );
  }

  if (isRecording) {
    return (
      <button
        type="button"
        onClick={onToggle}
        className="w-8 h-8 flex items-center justify-center rounded-full bg-destructive/10 text-destructive animate-pulse transition-colors hover:bg-destructive/20"
        aria-label="Stop recording"
      >
        <Square className="w-3.5 h-3.5 fill-current" />
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={onToggle}
      className={cn('flex h-8 w-8 items-center justify-center rounded-full transition-colors hover:bg-primary/10', error ? 'text-destructive' : 'text-muted-foreground hover:text-foreground')}
      aria-label="Start voice input"
      title={error || 'Voice input'}
    >
      <Mic className="w-4 h-4" />
    </button>
  );
}
