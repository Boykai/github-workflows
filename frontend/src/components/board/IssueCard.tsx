/**
 * IssueCard component - displays a board item as a card with metadata badges.
 */

import type { BoardItem, SubIssue } from '@/types';
import { statusColorToCSS } from './colorUtils';

interface IssueCardProps {
  item: BoardItem;
  onClick: (item: BoardItem) => void;
}

function SubIssueStateIcon({ state }: { state: string }) {
  if (state === 'closed') {
    return <span className="sub-issue-state sub-issue-state-closed" title="Closed">✓</span>;
  }
  return <span className="sub-issue-state sub-issue-state-open" title="Open">○</span>;
}

function SubIssueRow({ subIssue }: { subIssue: SubIssue }) {
  const agentLabel = subIssue.assigned_agent
    ? subIssue.assigned_agent.replace('speckit.', '')
    : null;

  return (
    <a
      className="sub-issue-row"
      href={subIssue.url}
      target="_blank"
      rel="noopener noreferrer"
      onClick={(e) => e.stopPropagation()}
      title={subIssue.title}
    >
      <SubIssueStateIcon state={subIssue.state} />
      {agentLabel && (
        <span className="sub-issue-agent-badge">{agentLabel}</span>
      )}
      <span className="sub-issue-number">#{subIssue.number}</span>
    </a>
  );
}

export function IssueCard({ item, onClick }: IssueCardProps) {
  const subIssues = item.sub_issues ?? [];

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

      {/* Sub-Issues */}
      {subIssues.length > 0 && (
        <div className="issue-card-sub-issues">
          <div className="sub-issues-header">
            <SubIssuesIcon />
            <span className="sub-issues-count">
              {subIssues.filter((s) => s.state === 'closed').length}/{subIssues.length} sub-issues
            </span>
          </div>
          <div className="sub-issues-list">
            {subIssues.map((si) => (
              <SubIssueRow key={si.id} subIssue={si} />
            ))}
          </div>
        </div>
      )}

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

function SubIssuesIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
      <path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z" />
    </svg>
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
