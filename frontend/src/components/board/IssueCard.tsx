/**
 * IssueCard component — redesigned card with consistent sizing, pipeline health bar,
 * active agent, error alerts, WIP/PR links, and delete support.
 */

import { memo, useState } from 'react';
import {
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  Circle,
  CircleCheckBig,
  GitPullRequest,
  Lock,
  Trash2,
} from 'lucide-react';
import type { BoardItem, SubIssue, AvailableAgent, PipelineStateInfo } from '@/types';
import { statusColorToCSS } from './colorUtils';
import { PRIORITY_COLORS } from '@/constants';
import { cn } from '@/lib/utils';

/** Allowed avatar URL hostnames from GitHub. */
const ALLOWED_AVATAR_HOSTS = ['avatars.githubusercontent.com'];

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
  isBlocking?: boolean;
  pipelineState?: PipelineStateInfo;
  pipelineName?: string;
  onDelete?: (item: BoardItem) => void;
}

// ── Sub-issue helpers ──────────────────────────────────────────

function SubIssueStateIcon({ state }: { state: string }) {
  if (state === 'closed') {
    return (
      <span title="Closed">
        <CircleCheckBig className="h-3.5 w-3.5 text-status-merged" />
      </span>
    );
  }
  return (
    <span title="Open">
      <Circle className="h-3.5 w-3.5 text-status-success" />
    </span>
  );
}

function SubIssueRow({
  subIssue,
  availableAgents,
}: {
  subIssue: SubIssue;
  availableAgents?: AvailableAgent[];
}) {
  const agentLabel = subIssue.assigned_agent
    ? subIssue.assigned_agent.replace('speckit.', '')
    : null;

  const agentMeta = subIssue.assigned_agent
    ? availableAgents?.find((a) => a.slug.toLowerCase() === subIssue.assigned_agent!.toLowerCase())
    : undefined;
  const modelName = agentMeta?.default_model_name;
  const firstOpenPr = subIssue.linked_prs?.find((pr) => pr.state === 'open');

  return (
    <div
      className="solar-chip-soft flex items-center gap-1.5 rounded-md px-2 py-1.5 text-xs text-foreground transition-colors hover:border-primary/35 hover:bg-primary/10"
    >
      <SubIssueStateIcon state={subIssue.state} />
      {agentLabel && (
        <span className="solar-chip rounded-sm px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em]">
          {agentLabel}
        </span>
      )}
      {modelName && <span className="text-[10px] text-muted-foreground truncate">{modelName}</span>}
      <span className="text-muted-foreground ml-auto flex items-center gap-1">
        {firstOpenPr && (
          <a
            href={firstOpenPr.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            title={`PR #${firstOpenPr.number}: ${firstOpenPr.title}`}
            className="text-muted-foreground hover:text-foreground"
          >
            <GitPullRequest className="h-3 w-3" />
          </a>
        )}
        <a
          href={subIssue.url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="hover:text-foreground"
        >
          #{subIssue.number}
        </a>
      </span>
    </div>
  );
}

// ── Pipeline health bar ────────────────────────────────────────

function PipelineHealthBar({ pipelineState }: { pipelineState: PipelineStateInfo }) {
  const { agents, completed_agents, current_agent_index, error } = pipelineState;
  if (agents.length === 0) return null;

  return (
    <div className="flex gap-0.5 h-1.5 w-full rounded-full overflow-hidden" title={`${completed_agents.length}/${agents.length} agents complete`}>
      {agents.map((agent, idx) => {
        let color: string;
        if (completed_agents.includes(agent)) {
          color = 'bg-status-success';
        } else if (idx === current_agent_index && !error) {
          color = 'bg-status-active animate-pulse';
        } else if (error && idx === current_agent_index) {
          color = 'bg-status-error';
        } else {
          color = 'bg-muted-foreground/20';
        }
        return (
          <div
            key={`${agent}-${idx}`}
            className={cn('flex-1 rounded-full', color)}
            title={`${agent}: ${completed_agents.includes(agent) ? 'done' : idx === current_agent_index ? (error ? 'errored' : 'active') : 'pending'}`}
          />
        );
      })}
    </div>
  );
}

// ── Label helpers ──────────────────────────────────────────────

const FALLBACK_LABEL_COLOR = 'd1d5db';
const MAX_VISIBLE_LABELS = 3;

function sanitizeHexColor(hex: string | null | undefined): string {
  if (!hex) return FALLBACK_LABEL_COLOR;
  const normalized = hex.replace(/^#/, '').toLowerCase();
  if (normalized.length !== 6 || !/^[0-9a-f]{6}$/.test(normalized)) return FALLBACK_LABEL_COLOR;
  return normalized;
}

// ── Main card ──────────────────────────────────────────────────

export const IssueCard = memo(function IssueCard({
  item,
  onClick,
  availableAgents,
  isBlocking = false,
  pipelineState,
  pipelineName,
  onDelete,
}: IssueCardProps) {
  const [isSubIssuesExpanded, setIsSubIssuesExpanded] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const subIssues = item.sub_issues ?? [];
  const labels = item.labels ?? [];
  const priorityName = item.priority?.name ?? '';
  const priorityConfig = PRIORITY_COLORS[priorityName] ?? PRIORITY_COLORS.P2;

  // Active agent resolution
  const activeAgentSlug = pipelineState?.current_agent ?? null;
  const activeAgentMeta = activeAgentSlug
    ? availableAgents?.find((a) => a.slug.toLowerCase() === activeAgentSlug.toLowerCase())
    : undefined;
  const activeAgentLabel = activeAgentSlug ? activeAgentSlug.replace('speckit.', '') : null;

  // First open PR on the parent
  const firstOpenPr = item.linked_prs.find((pr) => pr.state === 'open');

  // Visible labels (capped)
  const visibleLabels = labels.slice(0, MAX_VISIBLE_LABELS);
  const overflowCount = Math.max(0, labels.length - MAX_VISIBLE_LABELS);

  return (
    <div
      className={cn(
        "project-board-card celestial-panel flex cursor-pointer flex-col gap-2 rounded-[1.15rem] border border-border/75 bg-card/90 p-3 shadow-sm backdrop-blur-sm transition-[min-height] duration-200 ease-in-out hover:-translate-y-0.5 hover:border-primary/35 hover:bg-card/96 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2",
        "min-h-[11rem]",
      )}
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
      {/* ── Row 1: Header — repo/number + status + actions ── */}
      <div className="flex items-center justify-between gap-1">
        <div className="flex items-center gap-1 truncate text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
          {item.repository && (
            <span className="truncate">
              {item.repository.owner}/{item.repository.name}
            </span>
          )}
          {item.number != null && <span className="font-medium">#{item.number}</span>}
          {item.content_type === 'draft_issue' && (
            <span className="solar-chip-soft rounded-full px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground ml-1">
              Draft
            </span>
          )}
        </div>
        <div className="flex items-center gap-1 shrink-0">
          {/* Status pill */}
          {item.priority && (
            <span
              className={cn(
                'rounded-full px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em]',
                priorityConfig.bg,
                priorityConfig.text
              )}
            >
              {item.priority.name}
            </span>
          )}
          {/* WIP / PR link */}
          {firstOpenPr && (
            <a
              href={firstOpenPr.url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              title={`PR #${firstOpenPr.number}: ${firstOpenPr.title}`}
              className="rounded-full p-1 text-muted-foreground hover:bg-primary/10 hover:text-foreground transition-colors"
            >
              <GitPullRequest className="h-3.5 w-3.5" />
            </a>
          )}
          {/* Delete button */}
          {onDelete && (
            <button
              className="rounded-full p-1 text-muted-foreground/50 hover:bg-destructive/10 hover:text-destructive transition-colors"
              onClick={(e) => {
                e.stopPropagation();
                setConfirmDelete(true);
              }}
              title="Delete issue and all sub-issues"
              type="button"
            >
              <Trash2 className={cn('h-3.5 w-3.5', confirmDelete && 'text-destructive')} />
            </button>
          )}
        </div>
      </div>

      {/* ── Row 2: Title ── */}
      <div className="text-sm font-semibold leading-snug text-foreground line-clamp-2">{item.title}</div>

      {/* ── Row 3: Pipeline info — config name + active agent + error ── */}
      {(pipelineName || activeAgentLabel || pipelineState?.error) && (
        <div className="flex items-center gap-1.5 flex-wrap">
          {pipelineName && (
            <span className="solar-chip rounded-sm px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">
              {pipelineName}
            </span>
          )}
          {activeAgentLabel && (
            <span
              className="solar-chip rounded-sm px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-status-active"
              title={activeAgentMeta?.default_model_name ? `Model: ${activeAgentMeta.default_model_name}` : activeAgentSlug ?? ''}
            >
              {activeAgentLabel}
            </span>
          )}
          {pipelineState?.error && (
            <span
              className="inline-flex items-center gap-0.5 text-destructive"
              title={pipelineState.error}
            >
              <AlertTriangle className="h-3.5 w-3.5" />
            </span>
          )}
        </div>
      )}

      {/* ── Row 4: Health bar ── */}
      {pipelineState && pipelineState.agents.length > 0 && (
        <PipelineHealthBar pipelineState={pipelineState} />
      )}

      {/* ── Row 5: Labels + Blocking ── */}
      {(labels.length > 0 || isBlocking) && (
        <div className="flex items-center gap-1 flex-wrap">
          {visibleLabels.map((label) => {
            const safeColor = sanitizeHexColor(label.color);
            return (
              <span
                key={label.id}
                className="rounded-full px-2 py-0.5 text-[10px] font-semibold truncate max-w-[100px] shrink-0"
                style={{
                  backgroundColor: `#${safeColor}18`,
                  color: `#${safeColor}`,
                  boxShadow: `inset 0 0 0 1px #${safeColor}40`,
                }}
                title={label.name}
              >
                {label.name}
              </span>
            );
          })}
          {overflowCount > 0 && (
            <span className="rounded-full px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground bg-muted/50 shrink-0">
              +{overflowCount}
            </span>
          )}
          {isBlocking && (
            <span className="inline-flex items-center gap-0.5 rounded-full border border-gold/30 bg-gold/10 px-2 py-0.5 text-[10px] font-medium text-primary shrink-0">
              <Lock className="h-3 w-3" />
              Blocking
            </span>
          )}
        </div>
      )}

      {/* ── Row 6: Sub-Issues (collapsible) ── */}
      {subIssues.length > 0 && (
        <div className="flex flex-col gap-1 pt-1">
          <button
            className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              setIsSubIssuesExpanded(!isSubIssuesExpanded);
            }}
            type="button"
          >
            {isSubIssuesExpanded ? (
              <ChevronDown className="h-3.5 w-3.5" />
            ) : (
              <ChevronRight className="h-3.5 w-3.5" />
            )}
            <SubIssuesIcon />
            <span>
              {subIssues.length} sub-issue{subIssues.length !== 1 ? 's' : ''}
            </span>
          </button>
          {isSubIssuesExpanded && (
            <div className="flex flex-col gap-1">
              {subIssues.map((si) => (
                <SubIssueRow key={si.id} subIssue={si} availableAgents={availableAgents} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Row 7: Footer — assignees + metadata ── */}
      <div className="mt-auto flex items-center justify-between border-t border-border/70 pt-1.5">
        <div className="flex items-center gap-2">
          {item.assignees.length > 0 && (
            <div className="flex items-center -space-x-1.5">
              {item.assignees.map((assignee) => (
                <img
                  key={assignee.login}
                  className="h-5 w-5 rounded-full border-2 border-card"
                  src={validateAvatarUrl(assignee.avatar_url)}
                  alt={assignee.login}
                  title={assignee.login}
                  width={20}
                  height={20}
                />
              ))}
            </div>
          )}
          {item.assignees.length > 0 && item.assignees.length <= 2 && (
            <span className="text-[10px] text-muted-foreground truncate max-w-[80px]">
              {item.assignees.map((a) => a.login).join(', ')}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          {item.size && (
            <span
              className="solar-chip-soft rounded-full px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-muted-foreground"
              style={item.size.color ? { borderColor: statusColorToCSS(item.size.color) } : undefined}
            >
              {item.size.name}
            </span>
          )}
          {item.estimate != null && (
            <span className="solar-chip-soft rounded-full px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">
              {item.estimate}pt
            </span>
          )}
          {item.linked_prs.length > 0 && (
            <span
              className="flex items-center gap-0.5 text-[10px] font-medium text-muted-foreground"
              title={`${item.linked_prs.length} linked PR(s)`}
            >
              <PullRequestIcon />
              {item.linked_prs.length}
            </span>
          )}
        </div>
      </div>

      {/* ── Delete confirmation bar ── */}
      {confirmDelete && (
        <div
          className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/5 px-2 py-1.5 text-[11px] text-destructive"
          role="toolbar"
          onClick={(e) => e.stopPropagation()}
          onKeyDown={(e) => e.stopPropagation()}
        >
          <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
          <span className="truncate">Close parent + sub-issues, PRs &amp; branches?</span>
          <button
            className="ml-auto shrink-0 rounded-md bg-destructive/10 px-2 py-0.5 font-semibold text-destructive hover:bg-destructive/20 transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              onDelete?.(item);
              setConfirmDelete(false);
            }}
            type="button"
          >
            Confirm
          </button>
          <button
            className="shrink-0 rounded-md px-2 py-0.5 font-medium text-muted-foreground hover:text-foreground transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              setConfirmDelete(false);
            }}
            type="button"
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
});

// ── SVG icons ──────────────────────────────────────────────────

function SubIssuesIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
      <path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z" />
    </svg>
  );
}

function PullRequestIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
      <path
        fillRule="evenodd"
        d="M7.177 3.073L9.573.677A.25.25 0 0110 .854v4.792a.25.25 0 01-.427.177L7.177 3.427a.25.25 0 010-.354zM3.75 2.5a.75.75 0 100 1.5.75.75 0 000-1.5zm-2.25.75a2.25 2.25 0 113 2.122v5.256a2.251 2.251 0 11-1.5 0V5.372A2.25 2.25 0 011.5 3.25zM11 2.5h-1V4h1a1 1 0 011 1v5.628a2.251 2.251 0 101.5 0V5A2.5 2.5 0 0011 2.5zm1 10.25a.75.75 0 111.5 0 .75.75 0 01-1.5 0zM3.75 12a.75.75 0 100 1.5.75.75 0 000-1.5z"
      />
    </svg>
  );
}
