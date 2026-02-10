/**
 * Chat interface component.
 */

import { useState, useRef, useEffect, FormEvent } from 'react';
import type { ChatMessage, AITaskProposal, IssueCreateActionData, WorkflowResult } from '@/types';
import { MessageBubble } from './MessageBubble';
import { TaskPreview } from './TaskPreview';
import { StatusChangePreview } from './StatusChangePreview';
import { IssueRecommendationPreview } from './IssueRecommendationPreview';
import './ChatInterface.css';

interface StatusChangeProposal {
  proposal_id: string;
  task_id: string;
  task_title: string;
  current_status: string;
  target_status: string;
  status_option_id: string;
  status_field_id: string;
  status: string;
}

interface ChatInterfaceProps {
  messages: ChatMessage[];
  pendingProposals: Map<string, AITaskProposal>;
  pendingStatusChanges: Map<string, StatusChangeProposal>;
  pendingRecommendations: Map<string, IssueCreateActionData>;
  isSending: boolean;
  onSendMessage: (content: string) => void;
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
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const content = input.trim();
    if (content && !isSending) {
      onSendMessage(content);
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleEmojiInsert = () => {
    const textarea = inputRef.current;
    if (!textarea) return;

    const emoji = '😊';
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = textarea.value;

    // Insert emoji at cursor position
    const newText = text.substring(0, start) + emoji + text.substring(end);
    setInput(newText);

    // Set cursor position after the emoji
    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(start + emoji.length, start + emoji.length);
    }, 0);
  };

  return (
    <div className="chat-interface">
      {messages.length > 0 && (
        <div className="chat-header">
          <button
            type="button"
            onClick={onNewChat}
            className="new-chat-button"
            disabled={isSending}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
              <path d="M12 5v14M5 12h14" />
            </svg>
            New Chat
          </button>
        </div>
      )}
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="chat-empty">
            <h3>Start a conversation</h3>
            <p>Describe a task you want to create, and I'll help you add it to your project.</p>
            <div className="example-prompts">
              <p>Try something like:</p>
              <ul>
                <li>"Create a task to add user authentication"</li>
                <li>"Add a bug fix for the login page crash"</li>
                <li>"Set up CI/CD pipeline for the project"</li>
              </ul>
            </div>
          </div>
        ) : (
          messages.map((message) => {
            const actionData = message.action_data as Record<string, unknown> | undefined;
            const proposalId = actionData?.proposal_id as string | undefined;
            const recommendationId = actionData?.recommendation_id as string | undefined;
            const proposal = proposalId ? pendingProposals.get(proposalId) : null;
            const statusChange = proposalId ? pendingStatusChanges.get(proposalId) : null;
            const recommendation = recommendationId ? pendingRecommendations.get(recommendationId) : null;

            return (
              <div key={message.message_id}>
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
          <div className="chat-loading">
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-form" onSubmit={handleSubmit}>
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe a task to create..."
          disabled={isSending}
          rows={1}
          className="chat-input"
        />
        <button
          type="button"
          onClick={handleEmojiInsert}
          disabled={isSending}
          className="emoji-button"
          aria-label="Insert smiley face emoji"
          title="Insert smiley face emoji"
        >
          😊
        </button>
        <button
          type="submit"
          disabled={!input.trim() || isSending}
          className="send-button"
        >
          <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
          </svg>
        </button>
      </form>
    </div>
  );
}
