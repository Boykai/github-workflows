/**
 * IssueDetailModal component - displays expanded issue details in a modal overlay.
 */

import { useEffect, useCallback } from 'react';
import type { BoardItem, SubIssue } from '@/types';
import { statusColorToCSS } from './colorUtils';

interface IssueDetailModalProps {
  item: BoardItem;
  onClose: () => void;
}

export function IssueDetailModal({ item, onClose }: IssueDetailModalProps) {
  // Close on Escape key
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    },
    [onClose]
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    // Prevent body scroll when modal is open
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [handleKeyDown]);

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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm" onClick={handleBackdropClick}>
      <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-card text-card-foreground rounded-lg border border-border shadow-lg p-6 m-4" role="dialog" aria-modal="true" aria-label={item.title}>
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
              <span className="px-2 py-0.5 text-xs font-medium uppercase tracking-wider bg-muted text-muted-foreground rounded-sm">Draft</span>
            )}
          </div>
          <button className="p-2 rounded-md hover:bg-muted transition-colors" onClick={onClose} aria-label="Close modal">
            ✕
          </button>
        </div>

        {/* Title */}
        <h2 className="text-2xl font-bold mb-4">{item.title}</h2>

        {/* Status */}
        <div className="flex items-center gap-2 mb-6">
          <span className="text-sm font-medium text-muted-foreground">Status:</span>
          <span className="px-2.5 py-0.5 text-sm font-medium bg-muted rounded-full">{item.status}</span>
        </div>

        {/* Custom fields */}
        <div className="flex flex-wrap gap-4 mb-6">
          {item.priority && (
            <div className="flex flex-col gap-1">
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Priority</span>
              <span
                className="text-sm font-medium"
                style={
                  item.priority.color
                    ? { color: statusColorToCSS(item.priority.color) }
                    : undefined
                }
              >
                {item.priority.name}
              </span>
            </div>
          )}
          {item.size && (
            <div className="flex flex-col gap-1">
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Size</span>
              <span
                className="text-sm font-medium"
                style={
                  item.size.color
                    ? { color: statusColorToCSS(item.size.color) }
                    : undefined
                }
              >
                {item.size.name}
              </span>
            </div>
          )}
          {item.estimate != null && (
            <div className="flex flex-col gap-1">
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Estimate</span>
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
                <div key={assignee.login} className="flex items-center gap-2 px-2 py-1 bg-muted/50 rounded-md border border-border">
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

        {/* Body / Description */}
        {item.body && (
          <div className="mb-6">
            <h3 className="text-sm font-semibold mb-2">Description</h3>
            <div className="text-sm text-muted-foreground whitespace-pre-wrap bg-muted/30 p-4 rounded-md border border-border">{item.body}</div>
          </div>
        )}

        {/* Sub-Issues */}
        {item.sub_issues && item.sub_issues.length > 0 && (
          <div className="mb-6">
            <h3 className="text-sm font-semibold mb-2">
              Sub-Issues ({item.sub_issues.filter((s) => s.state === 'closed').length}/{item.sub_issues.length} completed)
            </h3>
            <div className="flex flex-col gap-2">
              {item.sub_issues.map((si: SubIssue) => (
                <a
                  key={si.id}
                  href={si.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`flex items-center gap-3 p-3 rounded-md border transition-colors no-underline ${si.state === 'closed' ? 'bg-muted/30 border-border/50 text-muted-foreground' : 'bg-card border-border hover:border-primary/50'}`}
                >
                  <span className={`flex items-center justify-center w-5 h-5 rounded-full text-xs ${si.state === 'closed' ? 'bg-purple-500/10 text-purple-500' : 'bg-green-500/10 text-green-500'}`}>
                    {si.state === 'closed' ? '✓' : '○'}
                  </span>
                  <span className="flex flex-col flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      {si.assigned_agent && (
                        <span className="px-1.5 py-0.5 text-[10px] font-medium bg-primary/10 text-primary rounded-sm">{si.assigned_agent}</span>
                      )}
                      <span className="text-xs font-medium text-muted-foreground">#{si.number}</span>
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
                  className="flex items-center gap-3 p-3 rounded-md border border-border bg-card hover:border-primary/50 transition-colors no-underline"
                >
                  <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${pr.state === 'merged' ? 'bg-purple-500/10 text-purple-500' : pr.state === 'closed' ? 'bg-red-500/10 text-red-500' : 'bg-green-500/10 text-green-500'}`}>
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
