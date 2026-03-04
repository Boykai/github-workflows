/**
 * Chat interface component.
 */

import { useState, useRef, useEffect, useCallback, FormEvent } from 'react';
import type { ChatMessage, AITaskProposal, IssueCreateActionData, WorkflowResult, StatusChangeProposal } from '@/types';
import { MessageBubble } from './MessageBubble';
import { SystemMessage } from './SystemMessage';
import { CommandAutocomplete } from './CommandAutocomplete';
import { TaskPreview } from './TaskPreview';
import { StatusChangePreview } from './StatusChangePreview';
import { IssueRecommendationPreview } from './IssueRecommendationPreview';
import { useCommands } from '@/hooks/useCommands';
import { useChatHistory } from '@/hooks/useChatHistory';
import type { CommandDefinition } from '@/lib/commands/types';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  pendingProposals: Map<string, AITaskProposal>;
  pendingStatusChanges: Map<string, StatusChangeProposal>;
  pendingRecommendations: Map<string, IssueCreateActionData>;
  isSending: boolean;
  onSendMessage: (content: string, options?: { isCommand?: boolean }) => void;
  onConfirmProposal: (proposalId: string) => void;
  onConfirmStatusChange: (proposalId: string) => void;
  onConfirmRecommendation: (recommendationId: string) => Promise<WorkflowResult>;
  onRejectProposal: (proposalId: string) => void;
  onRejectRecommendation: (recommendationId: string) => Promise<void>;
  onNewChat: () => void;
}

export function ChatInterface({
  messages,
  pendingProposals,
  pendingStatusChanges,
  pendingRecommendations,
  isSending,
  onSendMessage,
  onConfirmProposal,
  onConfirmStatusChange,
  onConfirmRecommendation,
  onRejectProposal,
  onRejectRecommendation,
  onNewChat,
}: ChatInterfaceProps) {
  const [input, setInput] = useState('');
  const [showAutocomplete, setShowAutocomplete] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const [autocompleteCommands, setAutocompleteCommands] = useState<CommandDefinition[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Integrate command system directly so autocomplete works regardless of
  // whether the parent passes command props (ChatPopup does not).
  const { isCommand: isCommandFn, getFilteredCommands } = useCommands();
  const { addToHistory, handleHistoryNavigation, clearHistory, isNavigating } = useChatHistory();

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Update autocomplete state when input changes.
  // Derive filtered commands internally via useCommands() so autocomplete
  // works even when the parent (e.g. ChatPopup) does not pass command props.
  useEffect(() => {
    const trimmed = input.trimStart();
    const shouldShow = trimmed.startsWith('#') && !trimmed.slice(1).includes(' ');

    if (shouldShow) {
      // Extract the partial command name after '#' to filter the registry
      const prefix = trimmed.slice(1);
      const filtered = getFilteredCommands(prefix);
      if (filtered.length > 0) {
        setAutocompleteCommands(filtered);
        setShowAutocomplete(true);
        setHighlightedIndex(0);
      } else {
        setShowAutocomplete(false);
      }
    } else {
      setShowAutocomplete(false);
    }
  }, [input, getFilteredCommands]);

  const handleAutocompleteSelect = useCallback((command: CommandDefinition) => {
    setInput(`#${command.name} `);
    setShowAutocomplete(false);
    inputRef.current?.focus();
  }, []);

  const doSubmit = () => {
    const content = input.trim();
    if (content && !isSending) {
      setShowAutocomplete(false);
      const commandInput = isCommandFn(content);
      onSendMessage(content, { isCommand: commandInput });
      addToHistory(content);
      // Always clear input after submission — command-level input preservation
      // is handled by the useChat hook via CommandResult.clearInput when needed.
      setInput('');
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    doSubmit();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Determine whether autocomplete is contextually active based on
    // the current input value rather than relying solely on the
    // showAutocomplete state (which is updated via useEffect and may
    // lag by one render frame).
    const trimmed = input.trimStart();
    const autocompleteActive =
      showAutocomplete &&
      autocompleteCommands.length > 0 &&
      trimmed.startsWith('#') &&
      !trimmed.slice(1).includes(' ');

    if (autocompleteActive) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setHighlightedIndex((prev) => (prev + 1) % autocompleteCommands.length);
        return;
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setHighlightedIndex((prev) => (prev - 1 + autocompleteCommands.length) % autocompleteCommands.length);
        return;
      }
      if (e.key === 'Enter' || e.key === 'Tab') {
        e.preventDefault();
        handleAutocompleteSelect(autocompleteCommands[highlightedIndex]);
        return;
      }
      if (e.key === 'Escape') {
        e.preventDefault();
        setShowAutocomplete(false);
        return;
      }
    }

    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      doSubmit();
      return;
    }

    // History navigation with Up/Down Arrow keys
    if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
      if (handleHistoryNavigation(e, input, setInput)) {
        return;
      }
    }
  };

  // Auto-resize textarea to fit content
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const textarea = e.target;
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 400)}px`;
  };

  // Reset textarea height when input is cleared (after send)
  useEffect(() => {
    if (!input && inputRef.current) {
      inputRef.current.style.height = 'auto';
    }
  }, [input]);

  return (
    <div className="flex flex-col h-full bg-background">
      {messages.length > 0 && (
        <div className="flex justify-end gap-2 p-3 border-b border-border bg-background">
          <button
            type="button"
            onClick={clearHistory}
            className="flex items-center gap-1.5 px-4 py-2 bg-muted text-foreground border border-border rounded-md text-sm font-medium cursor-pointer transition-colors hover:bg-destructive/10 hover:text-destructive hover:border-destructive/30 disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={isSending}
            title="Clear message history"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16" className="shrink-0">
              <path d="M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2m2 0v14a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V6h12Z" />
            </svg>
            Clear History
          </button>
          <button
            type="button"
            onClick={onNewChat}
            className="flex items-center gap-1.5 px-4 py-2 bg-muted text-foreground border border-border rounded-md text-sm font-medium cursor-pointer transition-colors hover:bg-muted/80 hover:border-muted-foreground disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={isSending}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16" className="shrink-0">
              <path d="M12 5v14M5 12h14" />
            </svg>
            New Chat
          </button>
        </div>
      )}
      <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
            <h3 className="text-lg font-semibold text-foreground mb-2">Start a conversation</h3>
            <p>Describe a task you want to create, and I'll help you add it to your project.</p>
            <div className="mt-6 bg-muted/50 p-4 rounded-lg text-left w-full max-w-sm">
              <p className="font-medium text-foreground mb-2">Try something like:</p>
              <ul className="list-none space-y-2">
                <li className="text-sm text-muted-foreground before:content-['\201C'] after:content-['\201D'] before:text-primary after:text-primary">Create a task to add user authentication</li>
                <li className="text-sm text-muted-foreground before:content-['\201C'] after:content-['\201D'] before:text-primary after:text-primary">Add a bug fix for the login page crash</li>
                <li className="text-sm text-muted-foreground before:content-['\201C'] after:content-['\201D'] before:text-primary after:text-primary">Set up CI/CD pipeline for the project</li>
                <li className="text-sm text-muted-foreground before:content-['\201C'] after:content-['\201D'] before:text-primary after:text-primary">Type #help to see available commands</li>
              </ul>
            </div>
          </div>
        ) : (
          messages.map((message) => {
            // Render system messages with distinct styling
            if (message.sender_type === 'system') {
              return (
                <div key={message.message_id} className="flex flex-col gap-2">
                  <SystemMessage message={message} />
                </div>
              );
            }
            const actionData = message.action_data as Record<string, unknown> | undefined;
            const proposalId = actionData?.proposal_id as string | undefined;
            const recommendationId = actionData?.recommendation_id as string | undefined;
            const proposal = proposalId ? pendingProposals.get(proposalId) : null;
            const statusChange = proposalId ? pendingStatusChanges.get(proposalId) : null;
            const recommendation = recommendationId ? pendingRecommendations.get(recommendationId) : null;

            return (
              <div key={message.message_id} className="flex flex-col gap-2">
                <MessageBubble message={message} />
                
                {proposal && message.action_type === 'task_create' && (
                  <TaskPreview
                    proposal={proposal}
                    onConfirm={() => onConfirmProposal(proposal.proposal_id)}
                    onReject={() => onRejectProposal(proposal.proposal_id)}
                  />
                )}

                {statusChange && message.action_type === 'status_update' && (
                  <StatusChangePreview
                    taskTitle={statusChange.task_title}
                    currentStatus={statusChange.current_status}
                    targetStatus={statusChange.target_status}
                    onConfirm={() => onConfirmStatusChange(statusChange.proposal_id)}
                    onReject={() => onRejectProposal(statusChange.proposal_id)}
                  />
                )}

                {recommendation && message.action_type === 'issue_create' && (
                  <IssueRecommendationPreview
                    recommendation={recommendation}
                    onConfirm={onConfirmRecommendation}
                    onReject={onRejectRecommendation}
                  />
                )}
              </div>
            );
          })
        )}

        {isSending && (
          <div className="self-start ml-11">
            <div className="flex gap-1 p-3 bg-muted rounded-2xl">
              <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '-0.32s' }}></span>
              <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '-0.16s' }}></span>
              <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"></span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form className="relative flex gap-3 p-4 border-t border-border bg-background" onSubmit={handleSubmit}>
        {showAutocomplete && (
          <CommandAutocomplete
            commands={autocompleteCommands}
            highlightedIndex={highlightedIndex}
            onSelect={handleAutocompleteSelect}
            onDismiss={() => setShowAutocomplete(false)}
            onHighlightChange={setHighlightedIndex}
          />
        )}
        <textarea
          ref={inputRef}
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="Describe a task or type # for commands..."
          disabled={isSending}
          rows={2}
          className={`flex-1 p-3 border rounded-xl text-sm font-inherit leading-relaxed resize-none outline-none min-h-[52px] max-h-[400px] overflow-y-auto transition-colors focus:border-primary disabled:bg-muted ${isNavigating ? 'border-primary/50 bg-primary/5' : 'border-border'}`}
        />
        <button
          type="submit"
          disabled={!input.trim() || isSending}
          className="w-11 h-11 p-0 bg-primary text-primary-foreground rounded-full flex items-center justify-center shrink-0 transition-colors hover:bg-primary/90 disabled:bg-muted disabled:text-muted-foreground disabled:cursor-not-allowed"
        >
          <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
          </svg>
        </button>
      </form>
    </div>
  );
}
