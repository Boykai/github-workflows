/**
 * IssueDetailModal component - displays expanded issue details in a modal overlay.
 * Renders issue descriptions as Markdown using react-markdown with GFM support.
 */

import { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Circle, CircleCheckBig, X } from '@/lib/icons';
import type { BoardItem, SubIssue } from '@/types';
import { statusColorToCSS } from './colorUtils';
import { useScrollLock } from '@/hooks/useScrollLock';
import { useMediaQuery } from '@/hooks/useMediaQuery';
import { cn } from '@/lib/utils';

const SAFE_MARKDOWN_PROTOCOLS = new Set(['http', 'https', 'mailto', 'tel']);

function sanitizeMarkdownUrl(url: string): string {
  const value = url.trim();

  if (
    value.length === 0 ||
    value.startsWith('#') ||
    value.startsWith('/') ||
    value.startsWith('./') ||
    value.startsWith('../')
  ) {
    return value;
  }

  const protocolMatch = value.match(/^([a-zA-Z][a-zA-Z\d+.-]*):/);
  if (!protocolMatch) {
    return value;
  }

  return SAFE_MARKDOWN_PROTOCOLS.has(protocolMatch[1].toLowerCase()) ? value : '';
}

interface IssueDetailModalProps {
  item: BoardItem;
  onClose: () => void;
}

export function IssueDetailModal({ item, onClose }: IssueDetailModalProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const closeBtnRef = useRef<HTMLButtonElement>(null);
  const previouslyFocusedElementRef = useRef<HTMLElement | null>(null);
  const isMobile = useMediaQuery('(max-width: 767px)');

  useScrollLock(true);

  // Focus the close button when the modal opens and restore focus on unmount
  useEffect(() => {
    // Capture the element that was focused before the modal opened
    const activeElement = document.activeElement;
    if (activeElement instanceof HTMLElement) {
      previouslyFocusedElementRef.current = activeElement;
    }

    // Then move focus to the close button
    requestAnimationFrame(() => {
      closeBtnRef.current?.focus();
    });

    // On unmount, restore focus to the previously focused element
    return () => {
      previouslyFocusedElementRef.current?.focus();
    };
  }, []);

  // Escape key + focus trapping
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
        return;
      }

      if (e.key === 'Tab' && dialogRef.current) {
        const focusable = dialogRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), a[href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  // Close on backdrop click
  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const prStateLabel = (state: string) => {
    switch (state) {
      case 'merged':
        return 'Merged';
      case 'closed':
        return 'Closed';
      default:
        return 'Open';
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm"
      onClick={handleBackdropClick}
      role="presentation"
    >
      <div
        ref={dialogRef}
        className={cn(
          'celestial-fade-in celestial-panel relative border border-border text-card-foreground shadow-lg',
          isMobile
            ? 'fixed inset-0 overflow-y-auto rounded-none p-4'
            : 'm-4 w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-[1.4rem] p-6'
        )}
        role="dialog"
        aria-modal="true"
        aria-labelledby="issue-detail-modal-title"
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            {item.repository && (
              <span>
                {item.repository.owner}/{item.repository.name}
                {item.number != null && ` #${item.number}`}
              </span>
            )}
            {item.content_type === 'draft_issue' && (
              <span className="px-2 py-0.5 text-xs font-medium uppercase tracking-wider bg-muted text-muted-foreground rounded-sm">
                Draft
              </span>
            )}
          </div>
          <button
            ref={closeBtnRef}
            className="rounded-md p-2 transition-colors hover:bg-primary/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/60"
            onClick={onClose}
            aria-label="Close modal"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Title */}
        <h2 id="issue-detail-modal-title" className="text-2xl font-bold mb-4">{item.title}</h2>

        {/* Status */}
        <div className="flex items-center gap-2 mb-6">
          <span className="text-sm font-medium text-muted-foreground">Status:</span>
          <span className="rounded-full border border-border bg-background/72 px-2.5 py-0.5 text-sm font-medium">
            {item.status}
          </span>
        </div>

        {/* Custom fields */}
        <div className="flex flex-wrap gap-4 mb-6">
          {item.priority && (
            <div className="flex flex-col gap-1">
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Priority
              </span>
              <span
                className="text-sm font-medium"
                style={
                  item.priority.color ? { color: statusColorToCSS(item.priority.color) } : undefined
                }
              >
                {item.priority.name}
              </span>
            </div>
          )}
          {item.size && (
            <div className="flex flex-col gap-1">
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Size
              </span>
              <span
                className="text-sm font-medium"
                style={item.size.color ? { color: statusColorToCSS(item.size.color) } : undefined}
              >
                {item.size.name}
              </span>
            </div>
          )}
          {item.estimate != null && (
            <div className="flex flex-col gap-1">
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Estimate
              </span>
              <span className="text-sm font-medium">{item.estimate} points</span>
            </div>
          )}
        </div>

        {/* Assignees */}
        {item.assignees.length > 0 && (
          <div className="mb-6">
            <h3 className="text-sm font-semibold mb-2">Assignees</h3>
            <div className="flex flex-wrap gap-2">
              {item.assignees.map((assignee) => (
                <div
                  key={assignee.login}
                  className="flex items-center gap-2 rounded-md border border-border bg-background/56 px-2 py-1"
                >
                  <img
                    src={assignee.avatar_url}
                    alt={assignee.login}
                    className="w-6 h-6 rounded-full"
                    width={24}
                    height={24}
                  />
                  <span className="text-sm font-medium">{assignee.login}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Body / Description — rendered as Markdown */}
        {item.body && (
          <div className="mb-6">
            <h3 className="text-sm font-semibold mb-2">Description</h3>
            <div className="prose prose-sm prose-headings:text-foreground prose-p:text-foreground prose-strong:text-foreground prose-em:text-foreground prose-ul:text-foreground prose-ol:text-foreground prose-li:text-foreground prose-code:text-foreground prose-pre:bg-muted/75 prose-pre:text-foreground prose-blockquote:border-primary/30 prose-blockquote:text-foreground prose-a:text-primary hover:prose-a:text-primary/80 dark:prose-invert max-w-none overflow-y-auto max-h-[50vh] rounded-md border border-border/80 bg-background/78 p-4 shadow-[inset_0_1px_0_hsl(var(--background)/0.55)]">
              <ReactMarkdown remarkPlugins={[remarkGfm]} urlTransform={sanitizeMarkdownUrl}>
                {item.body}
              </ReactMarkdown>
            </div>
          </div>
        )}

        {/* Sub-Issues */}
        {item.sub_issues && item.sub_issues.length > 0 && (
          <div className="mb-6">
            <h3 className="text-sm font-semibold mb-2">
              Sub-Issues ({item.sub_issues.filter((s) => s.state === 'closed').length}/
              {item.sub_issues.length} completed)
            </h3>
            <div className="flex flex-col gap-2">
              {item.sub_issues.map((si: SubIssue) => (
                <a
                  key={si.id}
                  href={si.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={cn('flex items-center gap-3 rounded-md border p-3 transition-colors no-underline', si.state === 'closed' ? 'bg-background/40 border-border/50 text-muted-foreground' : 'bg-background/72 border-border hover:border-primary/50 hover:bg-background/82')}
                >
                  <span
                    className={cn('flex items-center justify-center w-5 h-5 rounded-full text-xs', si.state === 'closed' ? 'bg-purple-500/10 text-purple-500' : 'bg-green-500/10 text-green-500')}
                  >
                    {si.state === 'closed' ? (
                      <CircleCheckBig className="h-3.5 w-3.5" />
                    ) : (
                      <Circle className="h-3.5 w-3.5" />
                    )}
                  </span>
                  <span className="flex flex-col flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      {si.assigned_agent && (
                        <span className="px-1.5 py-0.5 text-[10px] font-medium bg-primary/10 text-primary rounded-sm">
                          {si.assigned_agent}
                        </span>
                      )}
                      <span className="text-xs font-medium text-muted-foreground">
                        #{si.number}
                      </span>
                    </div>
                    <span className="text-sm font-medium truncate">{si.title}</span>
                  </span>
                  {si.assignees.length > 0 && (
                    <div className="flex items-center -space-x-1.5">
                      {si.assignees.map((a) => (
                        <img
                          key={a.login}
                          src={a.avatar_url}
                          alt={a.login}
                          title={a.login}
                          className="w-6 h-6 rounded-full border-2 border-card"
                          width={24}
                          height={24}
                        />
                      ))}
                    </div>
                  )}
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Linked PRs */}
        {item.linked_prs.length > 0 && (
          <div className="mb-6">
            <h3 className="text-sm font-semibold mb-2">Linked Pull Requests</h3>
            <div className="flex flex-col gap-2">
              {item.linked_prs.map((pr) => (
                <a
                  key={pr.pr_id}
                  href={pr.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 rounded-md border border-border bg-background/72 p-3 transition-colors no-underline hover:border-primary/50 hover:bg-background/82"
                >
                  <span
                    className={cn('px-2 py-0.5 text-xs font-medium rounded-full', pr.state === 'merged' ? 'bg-purple-500/10 text-purple-500' : pr.state === 'closed' ? 'bg-red-500/10 text-red-500' : 'bg-green-500/10 text-green-500')}
                  >
                    {prStateLabel(pr.state)}
                  </span>
                  <span className="text-sm font-medium text-foreground">
                    <span className="text-muted-foreground mr-1">#{pr.number}</span>
                    {pr.title}
                  </span>
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Open in GitHub button */}
        {item.url && (
          <div className="flex justify-end mt-6 pt-4 border-t border-border">
            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center px-4 py-2 text-sm font-medium transition-colors rounded-md bg-primary text-primary-foreground hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            >
              Open in GitHub ↗
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
