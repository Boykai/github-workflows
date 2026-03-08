/**
 * ChatToolbar — persistent toolbar above the chat input containing the
 * AI Enhance toggle, file upload button, and microphone button.
 * Styled consistently with the AddAgentPopover pattern.
 */

import { useRef } from 'react';
import { Sparkles, Paperclip } from 'lucide-react';
import { VoiceInputButton } from './VoiceInputButton';

interface ChatToolbarProps {
  aiEnhance: boolean;
  onAiEnhanceChange: (enabled: boolean) => void;
  onFileSelect: (files: FileList) => void;
  isRecording: boolean;
  isVoiceSupported: boolean;
  onVoiceToggle: () => void;
  voiceError: string | null;
  fileCount: number;
}

export function ChatToolbar({
  aiEnhance,
  onAiEnhanceChange,
  onFileSelect,
  isRecording,
  isVoiceSupported,
  onVoiceToggle,
  voiceError,
  fileCount,
}: ChatToolbarProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileSelect(e.target.files);
      // Reset so the same file can be selected again
      e.target.value = '';
    }
  };

  return (
    <div className="flex items-center justify-between border-b border-border bg-background/62 px-4 py-2">
      {/* Left section: AI Enhance toggle */}
      <button
        type="button"
        onClick={() => onAiEnhanceChange(!aiEnhance)}
        className={`flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-full transition-colors border ${
          aiEnhance
            ? 'bg-primary/10 text-primary border-primary/30 hover:bg-primary/20'
            : 'bg-background/72 text-muted-foreground border-border/50 hover:bg-primary/10 hover:border-primary/20 hover:text-foreground'
        }`}
        aria-pressed={aiEnhance}
        aria-label={`AI Enhance ${aiEnhance ? 'on' : 'off'}`}
      >
        <Sparkles className="w-4 h-4" />
        <span>AI Enhance</span>
        <span className={`text-xs px-1.5 py-0.5 rounded-full font-semibold ${
          aiEnhance
            ? 'bg-primary text-primary-foreground'
            : 'bg-muted-foreground/20 text-muted-foreground'
        }`}>
          {aiEnhance ? 'ON' : 'OFF'}
        </span>
      </button>

      {/* Right section: Action buttons */}
      <div className="flex items-center gap-1">
        {/* File upload button */}
        <button
          type="button"
          onClick={handleFileClick}
          className="relative flex h-8 w-8 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-primary/10 hover:text-foreground"
          aria-label="Attach file"
        >
          <Paperclip className="w-4 h-4" />
          {fileCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 w-4 h-4 flex items-center justify-center text-[10px] font-bold rounded-full bg-primary text-primary-foreground">
              {fileCount}
            </span>
          )}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/png,image/jpeg,image/gif,image/webp,image/svg+xml,application/pdf,text/plain,text/markdown,text/csv,application/json,application/x-yaml,application/zip"
          onChange={handleFileChange}
          className="hidden"
          aria-hidden="true"
        />

        {/* Voice input button */}
        <VoiceInputButton
          isSupported={isVoiceSupported}
          isRecording={isRecording}
          onToggle={onVoiceToggle}
          error={voiceError}
        />
      </div>
    </div>
  );
}
