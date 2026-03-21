/**
 * ChatPopup component — floating chat pop-up module for the project-board page.
 * Wraps ChatInterface with toggle state and animated panel overlay.
 * Supports drag-to-resize from the top-left corner handle.
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import type {
  ChatMessage,
  AITaskProposal,
  IssueCreateActionData,
  WorkflowResult,
  StatusChangeProposal,
} from '@/types';
import { ChatInterface } from './ChatInterface';
import { useMediaQuery } from '@/hooks/useMediaQuery';
import { cn } from '@/lib/utils';

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
  } catch {
    /* ignore */
  }
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

export function ChatPopup({
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
}: ChatPopupProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [size, setSize] = useState(loadSize);
  const isMobile = useMediaQuery('(max-width: 767px)');
  const isResizing = useRef(false);
  const startPos = useRef({ x: 0, y: 0, w: 0, h: 0 });
  const cleanupResize = useRef<(() => void) | null>(null);
  // Keep a ref of the latest size so onResizeStart doesn't need `size` in
  // its dependency array — prevents callback recreation on every resize (T026).
  const sizeRef = useRef(size);
  useEffect(() => {
    sizeRef.current = size;
  }, [size]);

  // Registers window-level mousemove/mouseup listeners only while a resize
  // is in progress, then removes them on mouseup. This avoids firing handlers
  // on every mouse event for the lifetime of the component.
  const onResizeStart = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      isResizing.current = true;
      startPos.current = { x: e.clientX, y: e.clientY, w: sizeRef.current.width, h: sizeRef.current.height };

      let rafId = 0;
      const onMouseMove = (ev: MouseEvent) => {
        if (!isResizing.current) return;
        // Gate position updates to once per animation frame to prevent
        // per-pixel event handler execution during drag.
        if (rafId) return;
        rafId = requestAnimationFrame(() => {
          rafId = 0;
          // Because the panel is anchored bottom-right, dragging left (negative dx) increases width,
          // and dragging up (negative dy) increases height.
          const dx = startPos.current.x - ev.clientX;
          const dy = startPos.current.y - ev.clientY;
          const newWidth = Math.min(Math.max(startPos.current.w + dx, MIN_WIDTH), MAX_WIDTH);
          const newHeight = Math.min(Math.max(startPos.current.h + dy, MIN_HEIGHT), MAX_HEIGHT);
          setSize({ width: newWidth, height: newHeight });
        });
      };

      const cleanup = () => {
        window.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('mouseup', onMouseUp);
        if (rafId) {
          cancelAnimationFrame(rafId);
          rafId = 0;
        }
        cleanupResize.current = null;
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
        cleanup();
      };

      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onMouseUp);
      cleanupResize.current = cleanup;
    },
    [] // size read via sizeRef to keep callback stable (T026)
  );

  // Clean up any in-progress resize listeners on unmount.
  useEffect(() => {
    return () => {
      cleanupResize.current?.();
    };
  }, []);

  return (
    <>
      <button
        className="fixed bottom-6 right-6 z-[1001] flex h-14 w-14 items-center justify-center rounded-full border-none bg-primary text-white shadow-lg transition-transform hover:scale-105 hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 dark:text-black"
        onClick={() => setIsOpen((prev) => !prev)}
        data-tour-step="chat-toggle"
        aria-label={isOpen ? 'Close chat' : 'Open chat'}
      >
        {isOpen ? (
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            width="24"
            height="24"
          >
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" fill="currentColor" width="24" height="24">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" />
          </svg>
        )}
      </button>

      <div
        style={isMobile ? undefined : { width: size.width, height: size.height }}
        className={cn(
          isMobile
            ? 'fixed inset-0 z-[1000] flex flex-col bg-background'
            : 'fixed bottom-24 right-6 bg-background border border-border rounded-xl shadow-2xl z-[1000] flex flex-col overflow-hidden transition-[transform,opacity] duration-200',
          isOpen
            ? 'scale-100 translate-y-0 opacity-100 pointer-events-auto'
            : isMobile
              ? 'translate-y-full opacity-0 pointer-events-none'
              : 'scale-95 translate-y-2 opacity-0 pointer-events-none'
        )}
      >
        {/* Resize handle — top-left corner (desktop only, mouse-only drag interaction) */}
        {!isMobile && (
          <div
            onMouseDown={onResizeStart}
            className="absolute top-0 left-0 w-4 h-4 cursor-nw-resize z-10"
            aria-hidden="true"
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
        )}

        <ChatInterface
          messages={messages}
          pendingProposals={pendingProposals}
          pendingStatusChanges={pendingStatusChanges}
          pendingRecommendations={pendingRecommendations}
          isSending={isSending}
          projectId={projectId}
          onSendMessage={onSendMessage}
          onRetryMessage={onRetryMessage}
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
