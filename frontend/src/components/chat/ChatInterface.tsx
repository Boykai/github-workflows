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
import { ChatToolbar } from './ChatToolbar';
import { FilePreviewChips } from './FilePreviewChips';
import { useCommands } from '@/hooks/useCommands';
import { useChatHistory } from '@/hooks/useChatHistory';
import { useFileUpload } from '@/hooks/useFileUpload';
import { useVoiceInput } from '@/hooks/useVoiceInput';
import type { CommandDefinition } from '@/lib/commands/types';
import { cn } from '@/lib/utils';
import { History } from 'lucide-react';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  pendingProposals: Map<string, AITaskProposal>;
  pendingStatusChanges: Map<string, StatusChangeProposal>;
  pendingRecommendations: Map<string, IssueCreateActionData>;
  isSending: boolean;
  onSendMessage: (content: string, options?: { isCommand?: boolean; aiEnhance?: boolean; fileUrls?: string[] }) => void;
  onRetryMessage: (messageId: string) => void;
  onConfirmProposal: (proposalId: string) => void;
  onConfirmStatusChange: (proposalId: string) => void;
  onConfirmRecommendation: (recommendationId: string) => Promise<WorkflowResult>;
  onRejectProposal: (proposalId: string) => void;
  onRejectRecommendation: (recommendationId: string) => Promise<void>;
  onNewChat: () => void;
}

const AI_ENHANCE_STORAGE_KEY = 'chat-ai-enhance';

function getInitialAiEnhance(): boolean {
  try {
    const stored = localStorage.getItem(AI_ENHANCE_STORAGE_KEY);
    return stored === null ? true : stored === 'true';
  } catch {
    return true;
  }
}

export function ChatInterface({
  messages,
  pendingProposals,
  pendingStatusChanges,
  pendingRecommendations,
  isSending,
  onSendMessage,
  onRetryMessage,
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
  const [showHistoryPopover, setShowHistoryPopover] = useState(false);
  const [aiEnhance, setAiEnhance] = useState(getInitialAiEnhance);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const historyPopoverRef = useRef<HTMLDivElement>(null);
  const historyNavTriggered = useRef(false);

  // Integrate command system directly so autocomplete works regardless of
  // whether the parent passes command props (ChatPopup does not).
  const { isCommand: isCommandFn, getFilteredCommands } = useCommands();

  // Chat message history navigation
  const {
    addToHistory,
    navigateUp,
    navigateDown,
    isNavigating,
    resetNavigation,
    history: chatHistory,
    selectFromHistory,
  } = useChatHistory();

  // File upload management
  const {
    files: uploadFiles,
    errors: fileErrors,
    addFiles: handleFileAdd,
    removeFile: handleFileRemove,
    uploadAll: uploadAllFiles,
    clearAll: clearAllFiles,
  } = useFileUpload();

  // Voice input management
  const handleVoiceTranscript = useCallback((text: string) => {
    setInput((prev) => (prev ? `${prev} ${text}` : text));
  }, []);
  const {
    isSupported: isVoiceSupported,
    isRecording,
    interimTranscript,
    error: voiceError,
    startRecording,
    stopRecording,
  } = useVoiceInput(handleVoiceTranscript);

  // AI Enhance persistence
  const handleAiEnhanceChange = useCallback((enabled: boolean) => {
    setAiEnhance(enabled);
    try {
      localStorage.setItem(AI_ENHANCE_STORAGE_KEY, String(enabled));
    } catch {
      // localStorage unavailable — state still works in-memory
    }
  }, []);

  const handleVoiceToggle = useCallback(() => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  }, [isRecording, startRecording, stopRecording]);

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
    const shouldShow = trimmed.startsWith('/') && !trimmed.slice(1).includes(' ');

    if (shouldShow) {
      // Extract the partial command name after '/' to filter the registry
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
    setInput(`/${command.name} `);
    setShowAutocomplete(false);
    inputRef.current?.focus();
  }, []);

  const doSubmit = async () => {
    const content = input.trim();
    if (content && !isSending) {
      setShowAutocomplete(false);
      setShowHistoryPopover(false);
      addToHistory(content);
      resetNavigation();
      const commandInput = isCommandFn(content);

      // Upload pending files before sending
      let fileUrls: string[] = [];
      if (uploadFiles.length > 0 && !commandInput) {
        fileUrls = await uploadAllFiles();
      }

      onSendMessage(content, { isCommand: commandInput, aiEnhance, fileUrls });
      // Always clear input after submission
      setInput('');
      clearAllFiles();
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
      trimmed.startsWith('/') &&
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

    // History navigation — ArrowUp to go to older messages
    if (e.key === 'ArrowUp' && !autocompleteActive) {
      const textarea = e.currentTarget;
      const firstNewline = input.indexOf('\n');
      const isOnFirstLine = firstNewline === -1 || textarea.selectionStart <= firstNewline;
      if (isOnFirstLine) {
        const result = navigateUp(input);
        if (result !== null) {
          e.preventDefault();
          historyNavTriggered.current = true;
          setInput(result);
        }
      }
    }

    // History navigation — ArrowDown to go to newer messages / restore draft
    if (e.key === 'ArrowDown' && !autocompleteActive && isNavigating) {
      const textarea = e.currentTarget;
      const lastNewline = input.lastIndexOf('\n');
      const isOnLastLine = lastNewline === -1 || textarea.selectionStart > lastNewline;
      if (isOnLastLine) {
        const result = navigateDown();
        if (result !== null) {
          e.preventDefault();
          historyNavTriggered.current = true;
          setInput(result);
        }
      }
    }

    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      doSubmit();
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

  // Position cursor at end when navigating history
  useEffect(() => {
    if (historyNavTriggered.current && inputRef.current) {
      historyNavTriggered.current = false;
      const len = inputRef.current.value.length;
      inputRef.current.selectionStart = len;
      inputRef.current.selectionEnd = len;
    }
  }, [input]);

  // Dismiss history popover on click outside
  useEffect(() => {
    if (!showHistoryPopover) return;
    const handleClick = (e: MouseEvent) => {
      if (historyPopoverRef.current && !historyPopoverRef.current.contains(e.target as Node)) {
        setShowHistoryPopover(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [showHistoryPopover]);

  return (
    <div className="flex flex-col h-full bg-background">
      {messages.length > 0 && (
        <div className="flex justify-end p-3 border-b border-border bg-background">
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
                <li className="text-sm text-muted-foreground before:content-['\201C'] after:content-['\201D'] before:text-primary after:text-primary">Type /help to see available commands</li>
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
                <MessageBubble
                  message={message}
                  onRetry={message.status === 'failed' ? () => onRetryMessage(message.message_id) : undefined}
                />
                
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

      <ChatToolbar
        aiEnhance={aiEnhance}
        onAiEnhanceChange={handleAiEnhanceChange}
        onFileSelect={handleFileAdd}
        isRecording={isRecording}
        isVoiceSupported={isVoiceSupported}
        onVoiceToggle={handleVoiceToggle}
        voiceError={voiceError}
        fileCount={uploadFiles.length}
      />

      <FilePreviewChips files={uploadFiles} onRemove={handleFileRemove} />

      {fileErrors.length > 0 && (
        <div className="px-4 py-1.5 text-xs text-destructive bg-destructive/5 border-b border-destructive/20">
          {fileErrors.map((err, i) => (
            <div key={i}>{err}</div>
          ))}
        </div>
      )}

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
        <div className="flex-1 relative">
          <textarea
            ref={inputRef}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Describe a task or type / for commands..."
            disabled={isSending}
            rows={2}
            className={cn(
              'w-full p-3 border border-border rounded-xl text-sm font-inherit leading-relaxed resize-none outline-none min-h-[52px] max-h-[400px] overflow-y-auto transition-colors bg-background text-foreground placeholder:text-muted-foreground focus:border-primary disabled:bg-muted',
              isNavigating && 'border-l-4 border-l-primary bg-primary/5',
            )}
          />
          {interimTranscript && (
            <div className="px-3 py-1 text-xs text-muted-foreground italic truncate">
              {interimTranscript}
            </div>
          )}
        </div>
        <div className="relative flex flex-col items-center gap-1" ref={historyPopoverRef}>
          {chatHistory.length > 0 && (
            <button
              type="button"
              onClick={() => setShowHistoryPopover((prev) => !prev)}
              aria-label="Message history"
              className="w-8 h-8 flex items-center justify-center rounded-full text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            >
              <History className="w-4 h-4" />
            </button>
          )}
          {showHistoryPopover && chatHistory.length > 0 && (
            <div className="absolute bottom-full mb-2 right-0 w-64 max-h-60 overflow-y-auto bg-popover border border-border rounded-lg shadow-lg z-20">
              <ul className="py-1">
                {chatHistory.map((_, idx) => {
                  const reverseIdx = chatHistory.length - 1 - idx;
                  const msg = chatHistory[reverseIdx];
                  return (
                    <li key={reverseIdx}>
                      <button
                        type="button"
                        className="w-full text-left px-3 py-2 text-sm hover:bg-muted transition-colors truncate"
                        onClick={() => {
                          const result = selectFromHistory(reverseIdx, input);
                          if (result !== null) {
                            historyNavTriggered.current = true;
                            setInput(result);
                          }
                          setShowHistoryPopover(false);
                          inputRef.current?.focus();
                        }}
                      >
                        {msg}
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}
        </div>
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
