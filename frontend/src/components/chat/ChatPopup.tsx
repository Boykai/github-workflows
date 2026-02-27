/**
 * ChatPopup component — floating chat pop-up module for the project-board page.
 * Wraps ChatInterface with toggle state and animated panel overlay.
 * Supports drag-to-resize from the top-left corner handle.
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import type { ChatMessage, AITaskProposal, IssueCreateActionData, WorkflowResult, StatusChangeProposal } from '@/types';
import { ChatInterface } from './ChatInterface';

const DEFAULT_WIDTH = 400;
const DEFAULT_HEIGHT = 500;
const MIN_WIDTH = 300;
const MIN_HEIGHT = 350;
const MAX_WIDTH = 800;
const MAX_HEIGHT = 900;
const STORAGE_KEY = 'chat-popup-size';

/** Persist dimensions across sessions */
function loadSize(): { width: number; height: number } {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      return {
        width: Math.min(Math.max(parsed.width ?? DEFAULT_WIDTH, MIN_WIDTH), MAX_WIDTH),
        height: Math.min(Math.max(parsed.height ?? DEFAULT_HEIGHT, MIN_HEIGHT), MAX_HEIGHT),
      };
    }
  } catch { /* ignore */ }
  return { width: DEFAULT_WIDTH, height: DEFAULT_HEIGHT };
}

function saveSize(width: number, height: number) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ width, height }));
}

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
  const [size, setSize] = useState(loadSize);
  const isResizing = useRef(false);
  const startPos = useRef({ x: 0, y: 0, w: 0, h: 0 });

  const onResizeStart = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      isResizing.current = true;
      startPos.current = { x: e.clientX, y: e.clientY, w: size.width, h: size.height };
    },
    [size],
  );

  useEffect(() => {
    const onMouseMove = (e: MouseEvent) => {
      if (!isResizing.current) return;
      // Because the panel is anchored bottom-right, dragging left (negative dx) increases width,
      // and dragging up (negative dy) increases height.
      const dx = startPos.current.x - e.clientX;
      const dy = startPos.current.y - e.clientY;
      const newWidth = Math.min(Math.max(startPos.current.w + dx, MIN_WIDTH), MAX_WIDTH);
      const newHeight = Math.min(Math.max(startPos.current.h + dy, MIN_HEIGHT), MAX_HEIGHT);
      setSize({ width: newWidth, height: newHeight });
    };

    const onMouseUp = () => {
      if (isResizing.current) {
        isResizing.current = false;
        // Persist final size
        setSize((prev) => {
          saveSize(prev.width, prev.height);
          return prev;
        });
      }
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
  }, []);

  return (
    <>
      <button
        className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-primary text-primary-foreground border-none cursor-pointer flex items-center justify-center shadow-lg z-[1001] transition-transform hover:scale-105 hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
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

      <div
        style={{ width: size.width, height: size.height }}
        className={`fixed bottom-24 right-6 bg-background border border-border rounded-xl shadow-2xl z-[1000] flex flex-col overflow-hidden transition-[transform,opacity] duration-200 max-md:!w-[calc(100vw-48px)] max-sm:!w-screen max-sm:!h-[70vh] max-sm:right-0 max-sm:bottom-20 max-sm:rounded-t-xl max-sm:rounded-b-none ${isOpen ? 'scale-100 translate-y-0 opacity-100 pointer-events-auto' : 'scale-95 translate-y-2 opacity-0 pointer-events-none'}`}
      >
        {/* Resize handle — top-left corner */}
        <div
          onMouseDown={onResizeStart}
          className="absolute top-0 left-0 w-4 h-4 cursor-nw-resize z-10 max-sm:hidden"
          aria-label="Resize chat"
          role="separator"
        >
          <svg
            viewBox="0 0 16 16"
            className="w-4 h-4 text-muted-foreground/50 hover:text-muted-foreground transition-colors"
          >
            <path d="M14 2L2 14" stroke="currentColor" strokeWidth="1.5" fill="none" />
            <path d="M14 6L6 14" stroke="currentColor" strokeWidth="1.5" fill="none" />
            <path d="M14 10L10 14" stroke="currentColor" strokeWidth="1.5" fill="none" />
          </svg>
        </div>

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
