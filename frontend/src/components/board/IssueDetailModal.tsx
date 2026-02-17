/**
 * IssueDetailModal component - displays expanded issue details in a modal overlay.
 */

import { useEffect, useCallback } from 'react';
import type { BoardItem } from '@/types';
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

  const prStateClass = (state: string) => {
    switch (state) {
      case 'merged':
        return 'pr-state-merged';
      case 'closed':
        return 'pr-state-closed';
      default:
        return 'pr-state-open';
    }
  };

  return (
    <div className="modal-backdrop" onClick={handleBackdropClick}>
      <div className="modal-content" role="dialog" aria-modal="true" aria-label={item.title}>
        {/* Header */}
        <div className="modal-header">
          <div className="modal-header-info">
            {item.repository && (
              <span className="modal-repo">
                {item.repository.owner}/{item.repository.name}
                {item.number != null && ` #${item.number}`}
              </span>
            )}
            {item.content_type === 'draft_issue' && (
              <span className="modal-draft-badge">Draft</span>
            )}
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Close modal">
            ✕
          </button>
        </div>

        {/* Title */}
        <h2 className="modal-title">{item.title}</h2>

        {/* Status */}
        <div className="modal-status">
          <span className="modal-status-label">Status:</span>
          <span className="modal-status-value">{item.status}</span>
        </div>

        {/* Custom fields */}
        <div className="modal-fields">
          {item.priority && (
            <div className="modal-field">
              <span className="modal-field-label">Priority</span>
              <span
                className="modal-field-value"
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
            <div className="modal-field">
              <span className="modal-field-label">Size</span>
              <span
                className="modal-field-value"
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
            <div className="modal-field">
              <span className="modal-field-label">Estimate</span>
              <span className="modal-field-value">{item.estimate} points</span>
            </div>
          )}
        </div>

        {/* Assignees */}
        {item.assignees.length > 0 && (
          <div className="modal-section">
            <h3 className="modal-section-title">Assignees</h3>
            <div className="modal-assignees">
              {item.assignees.map((assignee) => (
                <div key={assignee.login} className="modal-assignee">
                  <img
                    src={assignee.avatar_url}
                    alt={assignee.login}
                    className="modal-assignee-avatar"
                    width={28}
                    height={28}
                  />
                  <span className="modal-assignee-name">{assignee.login}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Body / Description */}
        {item.body && (
          <div className="modal-section">
            <h3 className="modal-section-title">Description</h3>
            <div className="modal-body">{item.body}</div>
          </div>
        )}

        {/* Linked PRs */}
        {item.linked_prs.length > 0 && (
          <div className="modal-section">
            <h3 className="modal-section-title">Linked Pull Requests</h3>
            <div className="modal-prs">
              {item.linked_prs.map((pr) => (
                <a
                  key={pr.pr_id}
                  href={pr.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="modal-pr-link"
                >
                  <span className={`modal-pr-state ${prStateClass(pr.state)}`}>
                    {prStateLabel(pr.state)}
                  </span>
                  <span className="modal-pr-info">
                    #{pr.number} {pr.title}
                  </span>
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Open in GitHub button */}
        {item.url && (
          <div className="modal-actions">
            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="modal-github-btn"
            >
              Open in GitHub ↗
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
