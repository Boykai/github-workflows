/**
 * ChatPopup component — floating chat pop-up module for the project-board page.
 * Wraps ChatInterface with toggle state and animated panel overlay.
 */

import { useState } from 'react';
import type { ChatMessage, AITaskProposal, IssueCreateActionData, WorkflowResult, StatusChangeProposal } from '@/types';
import { ChatInterface } from './ChatInterface';
import './ChatPopup.css';

interface ChatPopupProps {
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

export function ChatPopup({
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
}: ChatPopupProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button
        className="chat-popup-toggle"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-label={isOpen ? 'Close chat' : 'Open chat'}
      >
        {isOpen ? (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="24" height="24">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" fill="currentColor" width="24" height="24">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" />
          </svg>
        )}
      </button>

      <div className={`chat-popup-panel ${isOpen ? 'open' : ''}`}>
        <ChatInterface
          messages={messages}
          pendingProposals={pendingProposals}
          pendingStatusChanges={pendingStatusChanges}
          pendingRecommendations={pendingRecommendations}
          isSending={isSending}
          onSendMessage={onSendMessage}
          onConfirmProposal={onConfirmProposal}
          onConfirmStatusChange={onConfirmStatusChange}
          onConfirmRecommendation={onConfirmRecommendation}
          onRejectProposal={onRejectProposal}
          onRejectRecommendation={onRejectRecommendation}
          onNewChat={onNewChat}
        />
      </div>
    </>
  );
}
