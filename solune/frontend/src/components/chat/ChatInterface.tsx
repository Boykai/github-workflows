/**
 * Chat interface component.
 */

import { useState, useRef, useEffect, useCallback, FormEvent } from 'react';
import type {
  ChatMessage,
  AITaskProposal,
  IssueCreateActionData,
  WorkflowResult,
  StatusChangeProposal,
} from '@/types';
import { MessageBubble } from './MessageBubble';
import { SystemMessage } from './SystemMessage';
import { CommandAutocomplete } from './CommandAutocomplete';
import { MentionAutocomplete } from './MentionAutocomplete';
import { MentionInput } from './MentionInput';
import type { MentionInputHandle } from './MentionInput';
import { PipelineIndicator } from './PipelineIndicator';
import { TaskPreview } from './TaskPreview';
import { StatusChangePreview } from './StatusChangePreview';
import { IssueRecommendationPreview } from './IssueRecommendationPreview';
import { ChatToolbar } from './ChatToolbar';
import { FilePreviewChips } from './FilePreviewChips';
import { PipelineWarningBanner } from './PipelineWarningBanner';
import { Tooltip } from '@/components/ui/tooltip';
import { CHAT_PLACEHOLDERS, CYCLING_EXAMPLES } from '@/constants/chat-placeholders';
import { useCommands } from '@/hooks/useCommands';
import { useChatHistory } from '@/hooks/useChatHistory';
import { useCyclingPlaceholder } from '@/hooks/useCyclingPlaceholder';
import { useFileUpload } from '@/hooks/useFileUpload';
import { useVoiceInput } from '@/hooks/useVoiceInput';
import { useMentionAutocomplete } from '@/hooks/useMentionAutocomplete';
import type { CommandDefinition } from '@/lib/commands/types';
import { History, Mic } from '@/lib/icons';

function formatDateSeparator(date: Date): string {
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  const isSameDay = (a: Date, b: Date) =>
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate();

  if (isSameDay(date, today)) return 'Today';
  if (isSameDay(date, yesterday)) return 'Yesterday';
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

interface ChatInterfaceProps {
  messages: ChatMessage[];
  pendingProposals: Map<string, AITaskProposal>;
  pendingStatusChanges: Map<string, StatusChangeProposal>;
  pendingRecommendations: Map<string, IssueCreateActionData>;
  isSending: boolean;
  projectId?: string;
  onSendMessage: (
    content: string,
    options?: { isCommand?: boolean; aiEnhance?: boolean; fileUrls?: string[]; pipelineId?: string }
  ) => void;
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
  projectId,
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
  const [isInputFocused, setIsInputFocused] = useState(true);
  const [showAutocomplete, setShowAutocomplete] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const [autocompleteCommands, setAutocompleteCommands] = useState<CommandDefinition[]>([]);
  const [showHistoryPopover, setShowHistoryPopover] = useState(false);
  const [aiEnhance, setAiEnhance] = useState(getInitialAiEnhance);
  const [mentionValidationError, setMentionValidationError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const mentionInputRef = useRef<MentionInputHandle>(null);
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

  // Cycling placeholder for contextual prompt examples (stops when input has text or sending)
  const cyclingPlaceholder = useCyclingPlaceholder(
    [CHAT_PLACEHOLDERS.main.desktop, ...CYCLING_EXAMPLES],
    {
      enabled: !isInputFocused && !input.trim() && !isSending,
    },
  );

  // File upload management
  const {
    files: uploadFiles,
    errors: fileErrors,
    addFiles: handleFileAdd,
    removeFile: handleFileRemove,
    uploadAll: uploadAllFiles,
    clearAll: clearAllFiles,
  } = useFileUpload();

  // @Mention autocomplete
  const mention = useMentionAutocomplete({
    projectId: projectId ?? '',
    inputRef: mentionInputRef,
  });
  const {
    isAutocompleteOpen,
    clearTokens,
    handleMentionDismiss,
    handleMentionTrigger: mentionTrigger,
  } = mention;

  // Voice input management
  const handleVoiceTranscript = useCallback(
    (text: string) => {
      clearTokens();
      setInput((prev) => (prev ? `${prev} ${text}` : text));
    },
    [clearTokens]
  );
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

  // Update autocomplete state when input changes.
  // Derive filtered commands internally via useCommands() so autocomplete
  // works even when the parent (e.g. ChatPopup) does not pass command props.
  useEffect(() => {
    const trimmed = input.trimStart();
    const shouldShow = trimmed.startsWith('/') && !trimmed.slice(1).includes(' ');

    if (shouldShow) {
      // Dismiss @mention autocomplete when slash-command autocomplete activates
      if (isAutocompleteOpen) {
        handleMentionDismiss();
      }
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
  }, [input, getFilteredCommands, isAutocompleteOpen, handleMentionDismiss]);

  const handleAutocompleteSelect = useCallback(
    (command: CommandDefinition) => {
      clearTokens();
      setInput(`/${command.name} `);
      setShowAutocomplete(false);
      mentionInputRef.current?.focus();
    },
    [clearTokens]
  );

  // Handle @mention trigger — dismiss slash-command autocomplete
  const handleMentionTrigger = useCallback(
    (query: string, offset: number) => {
      if (showAutocomplete) setShowAutocomplete(false);
      mentionTrigger(query, offset);
    },
    [showAutocomplete, mentionTrigger]
  );

  const doSubmit = async () => {
    const content = input.trim();
    if (content && !isSending) {
      setShowAutocomplete(false);
      setShowHistoryPopover(false);
      setMentionValidationError(null);

      // Validate mention tokens before submit
      const pipelineId = mention.getSubmissionPipelineId();
      if (mention.mentionTokens.length > 0 && !mention.validateTokens()) {
        // All tokens are invalid
        setMentionValidationError('Pipeline not found — please select a valid pipeline');
        return;
      }

      addToHistory(content);
      resetNavigation();
      const commandInput = isCommandFn(content);

      // Upload pending files before sending
      let fileUrls: string[] = [];
      if (uploadFiles.length > 0 && !commandInput) {
        fileUrls = await uploadAllFiles();
      }

      onSendMessage(content, {
        isCommand: commandInput,
        aiEnhance,
        fileUrls,
        pipelineId: pipelineId ?? undefined,
      });
      // Always clear input after submission
      setInput('');
      mention.reset();
      clearAllFiles();
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    doSubmit();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // @mention autocomplete takes priority when open
    if (mention.isAutocompleteOpen) {
      mention.handleKeyDown(e);
      if (e.defaultPrevented) return;
    }

    // Ctrl+Enter or Cmd+Enter to send
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      doSubmit();
      return;
    }

    // Determine whether slash-command autocomplete is contextually active
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
        setHighlightedIndex(
          (prev) => (prev - 1 + autocompleteCommands.length) % autocompleteCommands.length
        );
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
    if (e.key === 'ArrowUp' && !autocompleteActive && !mention.isAutocompleteOpen) {
      if (mentionInputRef.current?.isCaretOnFirstLine() ?? true) {
        const result = navigateUp(input);
        if (result !== null) {
          e.preventDefault();
          historyNavTriggered.current = true;
          clearTokens();
          setInput(result);
        }
      }
    }

    // History navigation — ArrowDown to go to newer messages / restore draft
    if (
      e.key === 'ArrowDown' &&
      !autocompleteActive &&
      !mention.isAutocompleteOpen &&
      isNavigating
    ) {
      if (mentionInputRef.current?.isCaretOnLastLine() ?? true) {
        const result = navigateDown();
        if (result !== null) {
          e.preventDefault();
          historyNavTriggered.current = true;
          clearTokens();
          setInput(result);
        }
      }
    }
  };

  useEffect(() => {
    if (historyNavTriggered.current) {
      historyNavTriggered.current = false;
      mentionInputRef.current?.moveCursorToEnd();
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

  // Clear validation error when tokens change
  useEffect(() => {
    if (mentionValidationError) {
      setMentionValidationError(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mention.mentionTokens]);

  // Listen for global Ctrl+K focus-chat event
  useEffect(() => {
    const handleFocusChat = () => {
      mentionInputRef.current?.focus();
    };
    window.addEventListener('solune:focus-chat', handleFocusChat);
    return () => window.removeEventListener('solune:focus-chat', handleFocusChat);
  }, []);

  return (
    <div className="flex h-full flex-col bg-background">
      {messages.length > 0 && (
        <div className="flex justify-end border-b border-border bg-background/62 p-3">
          <button
            type="button"
            onClick={onNewChat}
            className="flex items-center gap-1.5 rounded-full border border-border bg-background/72 px-4 py-2 text-sm font-medium cursor-pointer text-foreground transition-colors hover:border-primary/20 hover:bg-primary/10 disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={isSending}
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              width="16"
              height="16"
              className="shrink-0"
            >
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
            <div className="mt-6 w-full max-w-sm rounded-lg border border-border bg-background/56 p-4 text-left">
              <p className="font-medium text-foreground mb-2">Try something like:</p>
              <ul className="list-none space-y-2">
                <li className="text-sm text-muted-foreground before:content-['\201C'] after:content-['\201D'] before:text-primary after:text-primary">
                  Create a task to add user authentication
                </li>
                <li className="text-sm text-muted-foreground before:content-['\201C'] after:content-['\201D'] before:text-primary after:text-primary">
                  Add a bug fix for the login page crash
                </li>
                <li className="text-sm text-muted-foreground before:content-['\201C'] after:content-['\201D'] before:text-primary after:text-primary">
                  Set up CI/CD pipeline for the project
                </li>
                <li className="text-sm text-muted-foreground before:content-['\201C'] after:content-['\201D'] before:text-primary after:text-primary">
                  Type /help to see available commands
                </li>
              </ul>
            </div>
          </div>
        ) : (
          messages.map((message, index) => {
            const prevMessage = messages[index - 1];
            const currentDate = new Date(message.timestamp);
            const prevDate = prevMessage ? new Date(prevMessage.timestamp) : null;
            const showDateSeparator = !prevDate ||
              currentDate.getFullYear() !== prevDate.getFullYear() ||
              currentDate.getMonth() !== prevDate.getMonth() ||
              currentDate.getDate() !== prevDate.getDate();

            // Render system messages with distinct styling
            if (message.sender_type === 'system') {
              return (
                <div key={message.message_id} className="flex flex-col gap-2">
                  {showDateSeparator && (
                    <div className="flex items-center gap-3 py-2 self-center">
                      <div className="flex-1 h-px bg-border" />
                      <span className="text-xs text-muted-foreground font-medium">
                        {formatDateSeparator(currentDate)}
                      </span>
                      <div className="flex-1 h-px bg-border" />
                    </div>
                  )}
                  <SystemMessage message={message} />
                </div>
              );
            }
            const actionData = message.action_data as Record<string, unknown> | undefined;
            const proposalId = actionData?.proposal_id as string | undefined;
            const recommendationId = actionData?.recommendation_id as string | undefined;
            const proposal = proposalId ? pendingProposals.get(proposalId) : null;
            const statusChange = proposalId ? pendingStatusChanges.get(proposalId) : null;
            const recommendation = recommendationId
              ? pendingRecommendations.get(recommendationId)
              : null;

            return (
              <div key={message.message_id} className="flex flex-col gap-2">
                {showDateSeparator && (
                  <div className="flex items-center gap-3 py-2 self-center">
                    <div className="flex-1 h-px bg-border" />
                    <span className="text-xs text-muted-foreground font-medium">
                      {formatDateSeparator(currentDate)}
                    </span>
                    <div className="flex-1 h-px bg-border" />
                  </div>
                )}
                <MessageBubble
                  message={message}
                  onRetry={
                    message.status === 'failed'
                      ? () => onRetryMessage(message.message_id)
                      : undefined
                  }
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
            <div className="flex gap-1 rounded-2xl border border-border bg-background/56 p-3">
              <span
                className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"
                style={{ animationDelay: '-0.32s' }}
              ></span>
              <span
                className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"
                style={{ animationDelay: '-0.16s' }}
              ></span>
              <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"></span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {projectId && <PipelineWarningBanner projectId={projectId} />}

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
        <div className="border-b border-destructive/20 bg-destructive/5 px-4 py-1.5 text-xs text-destructive">
          {fileErrors.map((err, i) => (
            <div key={i}>{err}</div>
          ))}
        </div>
      )}

      {mentionValidationError && (
        <div className="border-b border-destructive/20 bg-destructive/5 px-4 py-1.5 text-xs text-destructive">
          {mentionValidationError}
        </div>
      )}

      <form
        className="relative flex gap-3 border-t border-border bg-background/62 p-4"
        onSubmit={handleSubmit}
      >
        {showAutocomplete && (
          <CommandAutocomplete
            commands={autocompleteCommands}
            highlightedIndex={highlightedIndex}
            onSelect={handleAutocompleteSelect}
            onDismiss={() => setShowAutocomplete(false)}
            onHighlightChange={setHighlightedIndex}
          />
        )}
        <MentionAutocomplete
          pipelines={mention.filteredPipelines}
          highlightedIndex={mention.highlightedIndex}
          isLoading={mention.isLoadingPipelines}
          isVisible={mention.isAutocompleteOpen && !showAutocomplete}
          error={mention.pipelineError}
          onSelect={mention.handleSelect}
          onDismiss={mention.handleMentionDismiss}
          onHighlightChange={mention.handleHighlightChange}
        />
        <div className="flex-1 relative">
          <MentionInput
            ref={mentionInputRef}
            value={input}
            placeholder={CHAT_PLACEHOLDERS.main.desktop}
            placeholderMobile={CHAT_PLACEHOLDERS.main.mobile}
            cyclingPlaceholder={cyclingPlaceholder}
            ariaLabel={CHAT_PLACEHOLDERS.main.ariaLabel}
            onFocusChange={setIsInputFocused}
            disabled={isSending}
            isNavigating={isNavigating}
            onTextChange={setInput}
            onTokenRemove={mention.handleTokenRemove}
            onMentionTrigger={handleMentionTrigger}
            onMentionDismiss={mention.handleMentionDismiss}
            onSubmit={doSubmit}
            onKeyDown={handleKeyDown}
          />
          {interimTranscript && (
            <div className="flex items-center gap-1.5 px-3 py-1 text-xs text-muted-foreground">
              <Mic className="h-3 w-3 shrink-0 text-destructive mic-recording-pulse" />
              <span className="italic truncate">{interimTranscript}</span>
            </div>
          )}
          <PipelineIndicator
            activePipelineName={mention.activePipelineName}
            hasMultipleMentions={mention.hasMultipleMentions}
            hasInvalidMentions={mention.hasInvalidMentions}
          />
        </div>
        <div className="relative flex flex-col items-center gap-1" ref={historyPopoverRef}>
          {chatHistory.length > 0 && (
            <Tooltip contentKey="chat.interface.historyToggle">
              <button
                type="button"
                onClick={() => setShowHistoryPopover((prev) => !prev)}
                aria-label="Message history"
                className="flex h-8 w-8 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-primary/10 hover:text-foreground"
              >
                <History className="w-4 h-4" />
              </button>
            </Tooltip>
          )}
          {showHistoryPopover && chatHistory.length > 0 && (
            <div className="absolute bottom-full right-0 z-20 mb-2 max-h-60 w-64 overflow-y-auto rounded-lg border border-border bg-popover shadow-lg backdrop-blur-sm">
              <ul className="py-1">
                {chatHistory.map((_, idx) => {
                  const reverseIdx = chatHistory.length - 1 - idx;
                  const msg = chatHistory[reverseIdx];
                  return (
                    <li key={reverseIdx}>
                      <button
                        type="button"
                        className="w-full truncate px-3 py-2 text-left text-sm transition-colors hover:bg-primary/10"
                        onClick={() => {
                          const result = selectFromHistory(reverseIdx, input);
                          if (result !== null) {
                            historyNavTriggered.current = true;
                            clearTokens();
                            setInput(result);
                          }
                          setShowHistoryPopover(false);
                          mentionInputRef.current?.focus();
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
