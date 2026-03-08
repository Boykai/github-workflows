/**
 * IssueCard component - displays a board item as a card with metadata badges.
 * Enhanced with filled priority badges, description snippets, assignee names, and label pills.
 */

import { memo, useState } from 'react';
import type { BoardItem, SubIssue, AvailableAgent } from '@/types';
import { statusColorToCSS } from './colorUtils';
import { PRIORITY_COLORS } from '@/constants';

/** Allowed avatar URL hostnames from GitHub. */
const ALLOWED_AVATAR_HOSTS = ['avatars.githubusercontent.com'];

/**
 * Validate that an avatar URL uses https and originates from a known GitHub
 * avatar domain.  Returns the URL if valid, or a placeholder SVG data URI
 * on failure.
 */
function validateAvatarUrl(url: string | undefined | null): string {
  const placeholder =
    'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%2224%22 height=%2224%22 viewBox=%220 0 24 24%22%3E%3Ccircle cx=%2212%22 cy=%2212%22 r=%2212%22 fill=%22%23d1d5db%22/%3E%3C/svg%3E';
  if (!url) return placeholder;
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== 'https:') return placeholder;
    if (!ALLOWED_AVATAR_HOSTS.includes(parsed.hostname)) return placeholder;
    return url;
  } catch {
    return placeholder;
  }
}

interface IssueCardProps {
  item: BoardItem;
  onClick: (item: BoardItem) => void;
  availableAgents?: AvailableAgent[];
}

function SubIssueStateIcon({ state }: { state: string }) {
  if (state === 'closed') {
    return <span className="flex items-center justify-center w-3.5 h-3.5 text-[10px] text-purple-500" title="Closed">✓</span>;
  }
  return <span className="flex items-center justify-center w-3.5 h-3.5 text-[10px] text-green-500" title="Open">○</span>;
}

function SubIssueRow({ subIssue, availableAgents }: { subIssue: SubIssue; availableAgents?: AvailableAgent[] }) {
  const agentLabel = subIssue.assigned_agent
    ? subIssue.assigned_agent.replace('speckit.', '')
    : null;

  const agentMeta = subIssue.assigned_agent
    ? availableAgents?.find((a) => a.slug.toLowerCase() === subIssue.assigned_agent!.toLowerCase())
    : undefined;
  const modelName = agentMeta?.default_model_name;

  return (
    <a
      className="flex items-center gap-1.5 px-2 py-1.5 text-xs rounded-md bg-muted/50 hover:bg-muted transition-colors text-foreground no-underline"
      href={subIssue.url}
      target="_blank"
      rel="noopener noreferrer"
      onClick={(e) => e.stopPropagation()}
      title={subIssue.title}
    >
      <SubIssueStateIcon state={subIssue.state} />
      {agentLabel && (
        <span className="px-1.5 py-0.5 text-[10px] font-medium bg-primary/10 text-primary rounded-sm">{agentLabel}</span>
      )}
      {modelName && (
        <span className="text-[10px] text-muted-foreground truncate">{modelName}</span>
      )}
      <span className="text-muted-foreground ml-auto">#{subIssue.number}</span>
    </a>
  );
}

const FALLBACK_LABEL_COLOR = 'd1d5db';

function sanitizeHexColor(hex: string | null | undefined): string {
  if (!hex) {
    return FALLBACK_LABEL_COLOR;
  }

  const normalized = hex.replace(/^#/, '').toLowerCase();
  if (normalized.length !== 6 || !/^[0-9a-f]{6}$/.test(normalized)) {
    return FALLBACK_LABEL_COLOR;
  }

  return normalized;
}

/**
 * Compute WCAG relative luminance from a hex color string.
 * Returns true if text should be black (light background), false if white (dark background).
 */
function isLightColor(hex: string): boolean {
  const safeHex = sanitizeHexColor(hex);
  const r = parseInt(safeHex.slice(0, 2), 16) / 255;
  const g = parseInt(safeHex.slice(2, 4), 16) / 255;
  const b = parseInt(safeHex.slice(4, 6), 16) / 255;
  const toLinear = (c: number) => (c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4));
  const L = 0.2126 * toLinear(r) + 0.7152 * toLinear(g) + 0.0722 * toLinear(b);
  return L > 0.179;
}

export const IssueCard = memo(function IssueCard({ item, onClick, availableAgents }: IssueCardProps) {
  const [isSubIssuesExpanded, setIsSubIssuesExpanded] = useState(false);
  const subIssues = item.sub_issues ?? [];
  const labels = item.labels ?? [];
  const priorityName = item.priority?.name ?? '';
  const priorityConfig = PRIORITY_COLORS[priorityName] ?? PRIORITY_COLORS.P2;

  // Truncate body to ~80 chars for description snippet
  const snippet = item.body
    ? item.body.length > 80
      ? item.body.slice(0, 80).trimEnd() + '…'
      : item.body
    : null;

  return (
    <div
      className="flex cursor-pointer flex-col gap-2 rounded-[1.15rem] border border-border/75 bg-card/88 p-3 shadow-sm backdrop-blur-sm transition-all hover:-translate-y-0.5 hover:border-primary/35 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
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
        <div className="flex items-center gap-1 text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
          {item.repository.owner}/{item.repository.name}
          {item.number != null && <span className="font-medium">#{item.number}</span>}
        </div>
      )}
      {item.content_type === 'draft_issue' && (
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium uppercase tracking-[0.18em] text-muted-foreground">Draft</span>
        </div>
      )}

      {/* Title */}
      <div className="text-sm font-semibold leading-snug text-foreground">{item.title}</div>

      {/* Description snippet */}
      {snippet && (
        <p className="line-clamp-2 text-xs leading-relaxed text-muted-foreground">{snippet}</p>
      )}

      {/* Labels */}
      {labels.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {labels.map((label) => {
            const safeColor = sanitizeHexColor(label.color);
            return (
              <span
                key={label.id}
                className="rounded-full px-2 py-0.5 text-[10px] font-medium truncate max-w-[120px]"
                style={{
                  backgroundColor: `#${safeColor}`,
                  color: isLightColor(safeColor) ? '#000' : '#fff',
                }}
                title={label.name}
              >
                {label.name}
              </span>
            );
          })}
        </div>
      )}

      {/* Sub-Issues (collapsible) */}
      {subIssues.length > 0 && (
        <div className="flex flex-col gap-1.5 mt-1">
          <button
            className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              setIsSubIssuesExpanded(!isSubIssuesExpanded);
            }}
            type="button"
          >
            <span className="text-[10px]">{isSubIssuesExpanded ? '▼' : '▶'}</span>
            <SubIssuesIcon />
            <span>
              {subIssues.length} sub-issue{subIssues.length !== 1 ? 's' : ''}
            </span>
          </button>
          {isSubIssuesExpanded && (
            <div className="flex flex-col gap-1 max-h-60 overflow-y-auto">
              {subIssues.map((si) => (
                <SubIssueRow key={si.id} subIssue={si} availableAgents={availableAgents} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Metadata badges */}
      <div className="mt-1 flex flex-wrap gap-1.5">
        {item.priority && (
          <span
            className={`rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.12em] ${priorityConfig.bg} ${priorityConfig.text}`}
          >
            {item.priority.name}
          </span>
        )}
        {item.size && (
          <span
            className="rounded-full border border-border/70 bg-background/70 px-2.5 py-1 text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground"
            style={item.size.color ? { borderColor: statusColorToCSS(item.size.color) } : undefined}
          >
            {item.size.name}
          </span>
        )}
        {item.estimate != null && (
          <span className="rounded-full border border-border/70 bg-background/70 px-2.5 py-1 text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
            {item.estimate}pt
          </span>
        )}
      </div>

      {/* Footer: Assignees + Linked PRs */}
      <div className="mt-2 flex items-center justify-between border-t border-border/70 pt-2">
        {/* Assignees with names */}
        <div className="flex items-center gap-2">
          {item.assignees.length > 0 && (
            <div className="flex items-center -space-x-1.5">
              {item.assignees.map((assignee) => (
                <img
                  key={assignee.login}
                  className="h-6 w-6 rounded-full border-2 border-card"
                  src={validateAvatarUrl(assignee.avatar_url)}
                  alt={assignee.login}
                  title={assignee.login}
                  width={24}
                  height={24}
                />
              ))}
            </div>
          )}
          {item.assignees.length > 0 && item.assignees.length <= 2 && (
            <span className="text-xs text-muted-foreground truncate max-w-[100px]">
              {item.assignees.map((a) => a.login).join(', ')}
            </span>
          )}
        </div>

        {/* Linked PRs */}
        {item.linked_prs.length > 0 && (
          <span className="flex items-center gap-1 text-xs font-medium text-muted-foreground" title={`${item.linked_prs.length} linked PR(s)`}>
            <PullRequestIcon />
            {item.linked_prs.length}
          </span>
        )}
      </div>
    </div>
  );
});

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
