/**
 * Board issue card component displaying issue details with badges.
 */

import type { BoardIssueCard as BoardIssueCardType } from '@/types';

interface BoardIssueCardProps {
  card: BoardIssueCardType;
  onClick: () => void;
}

const PRIORITY_COLORS: Record<string, string> = {
  P0: '#cf222e',
  P1: '#bf8700',
  P2: '#0969da',
  P3: '#6e7781',
};

const SIZE_COLORS: Record<string, string> = {
  XS: '#6e7781',
  S: '#0969da',
  M: '#bf8700',
  L: '#cf222e',
  XL: '#8250df',
};

const PR_STATE_COLORS: Record<string, string> = {
  OPEN: '#1a7f37',
  CLOSED: '#cf222e',
  MERGED: '#8250df',
};

export function BoardIssueCard({ card, onClick }: BoardIssueCardProps) {
  const maxAvatars = 3;
  const visibleAssignees = card.assignees.slice(0, maxAvatars);
  const overflowCount = card.assignees.length - maxAvatars;

  const totalLinkedPRs = card.linked_prs.length;

  return (
    <div className="board-issue-card" onClick={onClick} role="button" tabIndex={0} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onClick(); }}>
      {/* Repo name and issue number */}
      {card.repo_name && card.issue_number && (
        <div className="board-card-repo">
          {card.repo_name}#{card.issue_number}
        </div>
      )}

      {/* Title */}
      <div className="board-card-title">{card.title}</div>

      {/* Assignee avatars */}
      {card.assignees.length > 0 && (
        <div className="board-assignee-avatars">
          {visibleAssignees.map((a) => (
            <img
              key={a.login}
              className="board-assignee-avatar"
              src={a.avatar_url}
              alt={a.login}
              title={a.login}
            />
          ))}
          {overflowCount > 0 && (
            <span className="board-assignee-overflow">+{overflowCount}</span>
          )}
        </div>
      )}

      {/* Badges row */}
      <div className="board-card-badges">
        {/* Linked PR badge */}
        {totalLinkedPRs > 0 && (
          <span
            className="board-pr-badge"
            style={{
              borderColor: PR_STATE_COLORS[card.linked_prs[0]?.state] || '#6e7781',
              color: PR_STATE_COLORS[card.linked_prs[0]?.state] || '#6e7781',
            }}
            title={card.linked_prs.map(pr => `#${pr.pr_number} (${pr.state})`).join(', ')}
          >
            🔗 {totalLinkedPRs} PR{totalLinkedPRs > 1 ? 's' : ''}
          </span>
        )}

        {/* Priority badge */}
        {card.priority && (
          <span
            className="board-badge board-badge--priority"
            style={{
              backgroundColor: `${PRIORITY_COLORS[card.priority] || '#6e7781'}20`,
              color: PRIORITY_COLORS[card.priority] || '#6e7781',
            }}
          >
            {card.priority}
          </span>
        )}

        {/* Estimate badge */}
        {card.estimate !== null && card.estimate !== undefined && (
          <span className="board-badge board-badge--estimate">
            {card.estimate}pt
          </span>
        )}

        {/* Size badge */}
        {card.size && (
          <span
            className="board-badge board-badge--size"
            style={{
              backgroundColor: `${SIZE_COLORS[card.size] || '#6e7781'}20`,
              color: SIZE_COLORS[card.size] || '#6e7781',
            }}
          >
            {card.size}
          </span>
        )}
      </div>
    </div>
  );
}
