/**
 * AgentChatFlow — multi-turn AI chat for refining sparse agent descriptions
 * into complete configurations. Mirrors ChoreChatFlow pattern.
 */

import { useState, useRef, useEffect } from 'react';
import { Bot, X } from '@/lib/icons';
import { useAgentChat } from '@/hooks/useAgents';
import { CHAT_PLACEHOLDERS } from '@/constants/chat-placeholders';
import { cn } from '@/lib/utils';

interface AgentChatFlowProps {
  projectId: string;
  initialMessage: string;
  agentName: string;
  onAgentReady: (name: string, description: string, systemPrompt: string, tools: string[]) => void;
  onCancel: () => void;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export function AgentChatFlow({
  projectId,
  initialMessage,
  agentName,
  onAgentReady,
  onCancel,
}: AgentChatFlowProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'user', content: initialMessage },
  ]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [preview, setPreview] = useState<{
    name: string;
    description: string;
    system_prompt: string;
    tools: string[];
  } | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatMutation = useAgentChat(projectId);

  // Send initial message
  useEffect(() => {
    chatMutation.mutate(
      { message: initialMessage, session_id: null },
      {
        onSuccess: (data) => {
          setSessionId(data.session_id);
          setMessages((prev) => [...prev, { role: 'assistant', content: data.reply }]);
          if (data.is_complete && data.preview) {
            setPreview({
              name: data.preview.name,
              description: data.preview.description,
              system_prompt: data.preview.system_prompt,
              tools: data.preview.tools,
            });
          }
        },
      }
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || chatMutation.isPending) return;

    setMessages((prev) => [...prev, { role: 'user', content: trimmed }]);
    setInput('');

    chatMutation.mutate(
      { message: trimmed, session_id: sessionId },
      {
        onSuccess: (data) => {
          setSessionId(data.session_id);
          setMessages((prev) => [...prev, { role: 'assistant', content: data.reply }]);
          if (data.is_complete && data.preview) {
            setPreview({
              name: data.preview.name,
              description: data.preview.description,
              system_prompt: data.preview.system_prompt,
              tools: data.preview.tools,
            });
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

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h3 className="flex items-center gap-2 text-sm font-semibold">
          <Bot className="h-4 w-4 text-primary" />
          Agent Refinement
        </h3>
        <button
          className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
          onClick={onCancel}
        >
          <X className="h-3.5 w-3.5" />
          Cancel
        </button>
      </div>

      {/* Messages */}
      <div className="flex flex-col gap-2 max-h-[40vh] overflow-y-auto">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={cn('text-sm p-2 rounded-md', msg.role === 'user'
                ? 'bg-primary/10 text-foreground ml-8'
                : 'bg-muted text-foreground mr-8')}
          >
            <span className="text-[10px] font-medium text-muted-foreground block mb-0.5">
              {msg.role === 'user' ? 'You' : 'AI'}
            </span>
            <p className="whitespace-pre-wrap">{msg.content}</p>
          </div>
        ))}
        {chatMutation.isPending && (
          <div className="text-sm p-2 rounded-md bg-muted mr-8 animate-pulse">Thinking…</div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Preview */}
      {preview && (
        <div className="border border-border rounded-md p-3 bg-muted/30">
          <h4 className="text-sm font-semibold mb-1">Agent Preview</h4>
          <p className="text-xs">
            <strong>Name:</strong> {preview.name || agentName}
          </p>
          <p className="text-xs">
            <strong>Description:</strong> {preview.description}
          </p>
          {preview.tools.length > 0 && (
            <p className="text-xs">
              <strong>Tools:</strong> {preview.tools.join(', ')}
            </p>
          )}
          <p className="text-xs mt-1 text-muted-foreground line-clamp-3">{preview.system_prompt}</p>
          <button
            className="mt-2 px-3 py-1.5 text-xs font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90"
            onClick={() =>
              onAgentReady(
                preview.name || agentName,
                preview.description,
                preview.system_prompt,
                preview.tools
              )
            }
          >
            Create Agent
          </button>
        </div>
      )}

      {/* Input */}
      {!preview && (
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={CHAT_PLACEHOLDERS.agentFlow.desktop}
            aria-label={CHAT_PLACEHOLDERS.agentFlow.ariaLabel}
            className="celestial-focus flex-1 px-3 py-2 text-sm border border-border rounded-md bg-background"
            disabled={chatMutation.isPending}
          />
          <button
            className="px-3 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            onClick={handleSend}
            disabled={chatMutation.isPending || !input.trim()}
          >
            Send
          </button>
        </div>
      )}
    </div>
  );
}
