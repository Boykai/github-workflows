/**
 * IssueCard component - displays a board item as a card with metadata badges.
 */

import type { BoardItem } from '@/types';
import { statusColorToCSS } from './colorUtils';

interface IssueCardProps {
  item: BoardItem;
  onClick: (item: BoardItem) => void;
}

export function IssueCard({ item, onClick }: IssueCardProps) {
  return (
    <div
      className="board-issue-card"
      onClick={() => onClick(item)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick(item);
        }
      }}
    >
      {/* Repository + Issue Number */}
      {item.repository && (
        <div className="issue-card-repo">
          {item.repository.owner}/{item.repository.name}
          {item.number != null && <span className="issue-card-number">#{item.number}</span>}
        </div>
      )}
      {item.content_type === 'draft_issue' && (
        <div className="issue-card-repo">
          <span className="issue-card-draft-badge">Draft</span>
        </div>
      )}

      {/* Title */}
      <div className="issue-card-title">{item.title}</div>

      {/* Metadata badges */}
      <div className="issue-card-badges">
        {item.priority && (
          <span
            className="issue-card-badge badge-priority"
            style={item.priority.color ? { borderColor: statusColorToCSS(item.priority.color) } : undefined}
          >
            {item.priority.name}
          </span>
        )}
        {item.size && (
          <span
            className="issue-card-badge badge-size"
            style={item.size.color ? { borderColor: statusColorToCSS(item.size.color) } : undefined}
          >
            {item.size.name}
          </span>
        )}
        {item.estimate != null && (
          <span className="issue-card-badge badge-estimate">
            {item.estimate}pt
          </span>
        )}
      </div>

      {/* Footer: Assignees + Linked PRs */}
      <div className="issue-card-footer">
        {/* Assignees */}
        <div className="issue-card-assignees">
          {item.assignees.length > 0 ? (
            item.assignees.map((assignee) => (
              <img
                key={assignee.login}
                className="issue-card-avatar"
                src={assignee.avatar_url}
                alt={assignee.login}
                title={assignee.login}
                width={24}
                height={24}
              />
            ))
          ) : null}
        </div>

        {/* Linked PRs */}
        {item.linked_prs.length > 0 && (
          <span className="issue-card-pr-badge" title={`${item.linked_prs.length} linked PR(s)`}>
            <PullRequestIcon />
            {item.linked_prs.length}
          </span>
        )}
      </div>
    </div>
  );
}

function PullRequestIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 16 16"
      fill="currentColor"
      aria-hidden="true"
    >
      <path
        fillRule="evenodd"
        d="M7.177 3.073L9.573.677A.25.25 0 0110 .854v4.792a.25.25 0 01-.427.177L7.177 3.427a.25.25 0 010-.354zM3.75 2.5a.75.75 0 100 1.5.75.75 0 000-1.5zm-2.25.75a2.25 2.25 0 113 2.122v5.256a2.251 2.251 0 11-1.5 0V5.372A2.25 2.25 0 011.5 3.25zM11 2.5h-1V4h1a1 1 0 011 1v5.628a2.251 2.251 0 101.5 0V5A2.5 2.5 0 0011 2.5zm1 10.25a.75.75 0 111.5 0 .75.75 0 01-1.5 0zM3.75 12a.75.75 0 100 1.5.75.75 0 000-1.5z"
      />
    </svg>
  );
}
