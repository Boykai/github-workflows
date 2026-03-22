import { Sparkles } from '@/lib/icons';

/**
 * ChoreChatFlow — embedded mini-chat UI for sparse input template building.
 *
 * Displayed within AddChoreModal when the user submits sparse input.
 * Sends messages to the chore chat endpoint and displays the conversation.
 * When template_ready=true, shows a preview with a confirm button.
 */

import { useState, useRef, useEffect } from 'react';
import { useChoreChat } from '@/hooks/useChores';
import { CHAT_PLACEHOLDERS } from '@/constants/chat-placeholders';
import { cn } from '@/lib/utils';

interface ChoreChatFlowProps {
  projectId: string;
  initialMessage: string;
  choreName: string;
  onTemplateReady: (templateContent: string) => void;
  onCancel: () => void;
  aiEnhance?: boolean;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export function ChoreChatFlow({
  projectId,
  initialMessage,
  choreName,
  onTemplateReady,
  onCancel,
  aiEnhance = true,
}: ChoreChatFlowProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'user', content: initialMessage },
  ]);
  const [input, setInput] = useState('');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [templateContent, setTemplateContent] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const chatMutation = useChoreChat(projectId);

  // Send initial message on mount
  useEffect(() => {
    chatMutation.mutate(
      { content: initialMessage, conversation_id: null, ai_enhance: aiEnhance },
      {
        onSuccess: (data) => {
          setConversationId(data.conversation_id);
          setMessages((prev) => [...prev, { role: 'assistant', content: data.message }]);
          if (data.template_ready && data.template_content) {
            setTemplateContent(data.template_content);
          }
        },
      }
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || chatMutation.isPending) return;

    setMessages((prev) => [...prev, { role: 'user', content: trimmed }]);
    setInput('');

    chatMutation.mutate(
      { content: trimmed, conversation_id: conversationId, ai_enhance: aiEnhance },
      {
        onSuccess: (data) => {
          setConversationId(data.conversation_id);
          setMessages((prev) => [...prev, { role: 'assistant', content: data.message }]);
          if (data.template_ready && data.template_content) {
            setTemplateContent(data.template_content);
          }
        },
      }
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Template ready — show preview + confirm
  if (templateContent) {
    return (
      <div className="flex flex-col gap-3">
        <h4 className="text-sm font-medium text-foreground">Template Preview</h4>
        <pre className="p-3 rounded-md border border-border bg-muted/50 text-xs overflow-auto max-h-60 whitespace-pre-wrap">
          {templateContent}
        </pre>
        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={onCancel}
            className="px-3 py-1.5 text-sm rounded-md border border-input bg-background hover:bg-accent transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={() => onTemplateReady(templateContent)}
            className="px-3 py-1.5 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            Use This Template
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-foreground">
          Building template for &ldquo;{choreName}&rdquo;
        </h4>
        <button
          type="button"
          onClick={onCancel}
          className="text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          Cancel
        </button>
      </div>

      {!aiEnhance && (
        <p className="text-xs text-muted-foreground bg-muted/30 rounded-md px-2.5 py-1.5 border border-border/50">
          <span className="inline-flex items-center gap-2">
            <Sparkles className="h-3.5 w-3.5 text-primary" />
            Your input will be used as the template body — AI will generate metadata only
          </span>
        </p>
      )}

      {/* Messages */}
      <div className="flex flex-col gap-2 max-h-64 overflow-y-auto p-2 rounded-md border border-border bg-muted/20">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={cn('text-xs p-2 rounded-md max-w-[85%]', msg.role === 'user'
                ? 'self-end bg-primary/10 text-foreground'
                : 'self-start bg-muted text-foreground')}
          >
            <p className="whitespace-pre-wrap">{msg.content}</p>
          </div>
        ))}
        {chatMutation.isPending && (
          <div className="self-start text-xs text-muted-foreground p-2">Thinking…</div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={CHAT_PLACEHOLDERS.choreFlow.desktop}
          aria-label={CHAT_PLACEHOLDERS.choreFlow.ariaLabel}
          disabled={chatMutation.isPending}
          className="celestial-focus flex-1 h-8 rounded-md border border-input bg-background px-3 text-sm placeholder:text-muted-foreground focus:outline-none disabled:opacity-50"
        />
        <button
          type="button"
          onClick={handleSend}
          disabled={chatMutation.isPending || !input.trim()}
          className="h-8 px-3 text-xs font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
        >
          Send
        </button>
      </div>
    </div>
  );
}
