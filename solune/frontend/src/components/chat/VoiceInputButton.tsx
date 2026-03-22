/**
 * VoiceInputButton — microphone button with recording state indicator.
 * Shows pulsing animation when recording, disabled state when unsupported.
 */

import { Mic, MicOff, Square } from '@/lib/icons';
import { cn } from '@/lib/utils';
import { Tooltip } from '@/components/ui/tooltip';

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
        aria-label="Voice input not supported"
      >
        <MicOff className="w-4 h-4" />
      </button>
    );
  }

  if (isRecording) {
    return (
      <Tooltip contentKey="chat.voice.stop">
        <button
          type="button"
          onClick={onToggle}
          className="celestial-focus mic-recording-pulse w-8 h-8 flex items-center justify-center rounded-full bg-destructive/10 text-destructive transition-colors hover:bg-destructive/20 focus-visible:outline-none"
          aria-label="Stop recording"
        >
          <Square className="w-3.5 h-3.5 fill-current" />
        </button>
      </Tooltip>
    );
  }

  return (
    <Tooltip contentKey="chat.toolbar.voiceButton">
      <button
        type="button"
        onClick={onToggle}
        className={cn(
          'celestial-focus flex h-8 w-8 items-center justify-center rounded-full transition-colors focus-visible:outline-none hover:bg-primary/10',
          error ? 'text-destructive' : 'text-muted-foreground hover:text-foreground'
        )}
        aria-label={error ? 'Voice input error — click to retry' : 'Start voice input'}
      >
        <Mic className="w-4 h-4" />
      </button>
    </Tooltip>
  );
}
