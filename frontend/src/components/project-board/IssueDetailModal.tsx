/**
 * Issue detail modal component with expanded issue information.
 */

import { useEffect, useRef } from 'react';
import type { BoardIssueCard } from '@/types';

interface IssueDetailModalProps {
  card: BoardIssueCard;
  isOpen: boolean;
  onClose: () => void;
}

const PR_STATE_COLORS: Record<string, string> = {
  OPEN: '#1a7f37',
  CLOSED: '#cf222e',
  MERGED: '#8250df',
};

export function IssueDetailModal({ card, isOpen, onClose }: IssueDetailModalProps) {
  const overlayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === overlayRef.current) onClose();
  };

  return (
    <div
      className="issue-detail-modal-overlay"
      ref={overlayRef}
      onClick={handleOverlayClick}
    >
      <div className="issue-detail-modal-content" role="dialog" aria-modal="true" aria-label={card.title}>
        {/* Close button */}
        <button className="modal-close-button" onClick={onClose} aria-label="Close">
          ✕
        </button>

        {/* Header */}
        <div className="modal-header">
          {card.repo_name && card.issue_number && (
            <div className="modal-repo">
              {card.repo_full_name || card.repo_name}#{card.issue_number}
            </div>
          )}
          <h2 className="modal-title">{card.title}</h2>
        </div>

        {/* Status & Badges */}
        <div className="modal-badges">
          {card.status && (
            <span className="modal-badge modal-badge--status">{card.status}</span>
          )}
          {card.priority && (
            <span className="modal-badge modal-badge--priority">{card.priority}</span>
          )}
          {card.size && (
            <span className="modal-badge modal-badge--size">{card.size}</span>
          )}
          {card.estimate !== null && card.estimate !== undefined && (
            <span className="modal-badge modal-badge--estimate">{card.estimate}pt</span>
          )}
          {card.state && (
            <span className="modal-badge modal-badge--state">{card.state}</span>
          )}
        </div>

        {/* Body */}
        {card.body && (
          <div className="modal-body">
            <h3>Description</h3>
            <p>{card.body.length > 500 ? card.body.substring(0, 500) + '…' : card.body}</p>
          </div>
        )}

        {/* Assignees */}
        {card.assignees.length > 0 && (
          <div className="modal-section">
            <h3>Assignees</h3>
            <div className="modal-assignee-list">
              {card.assignees.map((a) => (
                <div key={a.login} className="modal-assignee">
                  <img
                    className="modal-assignee-avatar"
                    src={a.avatar_url}
                    alt={a.login}
                  />
                  <span>{a.login}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Linked PRs */}
        {card.linked_prs.length > 0 && (
          <div className="modal-section">
            <h3>Linked Pull Requests</h3>
            <div className="modal-pr-list">
              {card.linked_prs.map((pr) => (
                <a
                  key={pr.pr_number}
                  href={pr.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="modal-pr-item"
                >
                  <span
                    className="modal-pr-state"
                    style={{ color: PR_STATE_COLORS[pr.state] || '#6e7781' }}
                  >
                    ●
                  </span>
                  <span>#{pr.pr_number} {pr.title}</span>
                  <span className="modal-pr-state-label">{pr.state}</span>
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Open on GitHub link */}
        {card.url && (
          <a
            href={card.url}
            target="_blank"
            rel="noopener noreferrer"
            className="modal-github-link"
          >
            Open on GitHub ↗
          </a>
        )}
      </div>
    </div>
  );
}
