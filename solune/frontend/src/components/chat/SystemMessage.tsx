/**
 * SystemMessage component for rendering command responses in chat.
 * Distinct visual style: no avatar, muted background, left-aligned.
 */

import type { ChatMessage } from '@/types';

interface SystemMessageProps {
  message: ChatMessage;
}

export function SystemMessage({ message }: SystemMessageProps) {
  return (
    <div className="flex max-w-[90%] self-start">
      <div className="flex flex-col gap-1 w-full">
        <div className="rounded-xl border border-border bg-background/56 px-4 py-3 text-sm text-foreground whitespace-pre-wrap leading-relaxed">
          {message.content}
        </div>
        <time className="text-[11px] text-muted-foreground px-1">
          {new Date(message.timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </time>
      </div>
    </div>
  );
}
