/**
 * AgentCard — displays a single agent with name, description,
 * status badge, and action buttons (delete, edit).
 */

import type { AgentConfig, AgentStatus } from '@/services/api';
import { useDeleteAgent } from '@/hooks/useAgents';
import { STATUS_COLORS } from '@/constants';
import { cn } from '@/lib/utils';

interface AgentCardProps {
  agent: AgentConfig;
  projectId: string;
  onEdit?: (agent: AgentConfig) => void;
}

const STATUS_BADGE: Record<AgentStatus, { label: string; className: string }> = {
  active: {
    label: 'Active',
    className: cn(STATUS_COLORS.success.bg, STATUS_COLORS.success.text),
  },
  pending_pr: {
    label: 'Pending PR',
    className: 'bg-accent/10 text-accent-foreground dark:bg-accent/20 dark:text-accent-foreground',
  },
  pending_deletion: {
    label: 'Pending Deletion',
    className: 'bg-destructive/10 text-destructive dark:bg-destructive/20 dark:text-destructive-foreground',
  },
};

export function AgentCard({ agent, projectId, onEdit }: AgentCardProps) {
  const deleteMutation = useDeleteAgent(projectId);
  const badge = STATUS_BADGE[agent.status] ?? STATUS_BADGE.active;

  // Repo-only agents cannot be edited or deleted via the API
  const isRepoOnly = agent.source === 'repo';

  const handleDelete = () => {
    if (window.confirm(`Remove agent "${agent.name}"? This will open a PR to delete the agent files.`)) {
      deleteMutation.mutate(agent.id);
    }
  };

  return (
    <div className="flex flex-col gap-1.5 p-3 rounded-md border border-border bg-card hover:bg-accent/50 transition-colors">
      {/* Header row: name + status badge */}
      <div className="flex items-center justify-between gap-2">
        <h4 className="text-sm font-medium text-foreground truncate" title={agent.name}>
          {agent.name}
        </h4>
        <span className={cn('px-1.5 py-0.5 text-[10px] font-medium rounded-full shrink-0', badge.className)}>
          {badge.label}
        </span>
      </div>

      {/* Description */}
      {agent.description && (
        <p className="text-xs text-muted-foreground line-clamp-2">{agent.description}</p>
      )}

      {/* Tools */}
      {agent.tools.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {agent.tools.slice(0, 3).map((tool) => (
            <span key={tool} className="px-1.5 py-0.5 text-[10px] bg-muted rounded text-muted-foreground">
              {tool}
            </span>
          ))}
          {agent.tools.length > 3 && (
            <span className="text-[10px] text-muted-foreground">+{agent.tools.length - 3} more</span>
          )}
        </div>
      )}

      {/* PR link */}
      {agent.github_pr_number && (
        <p className="text-[10px] text-muted-foreground">PR #{agent.github_pr_number}</p>
      )}

      {/* Actions */}
      <div className="flex items-center gap-1.5 mt-1">
        {onEdit && !isRepoOnly && (
          <button
            className="px-2 py-0.5 text-[10px] font-medium rounded bg-muted hover:bg-muted/80 text-muted-foreground transition-colors"
            onClick={() => onEdit(agent)}
          >
            Edit
          </button>
        )}
        {!isRepoOnly && (
          <button
            className="px-2 py-0.5 text-[10px] font-medium rounded bg-destructive/10 hover:bg-destructive/20 text-destructive transition-colors"
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? 'Deleting…' : 'Delete'}
          </button>
        )}
      </div>

      {/* Delete success feedback */}
      {deleteMutation.isSuccess && deleteMutation.data && (
        <div className={cn('text-[10px]', STATUS_COLORS.success.text)}>
          ✓ Deletion PR #{deleteMutation.data.pr_number} opened
        </div>
      )}

      {/* Delete error feedback */}
      {deleteMutation.isError && (
        <div className="text-[10px] text-destructive">
          ✗ {deleteMutation.error?.message || 'Delete failed'}
        </div>
      )}
    </div>
  );
}
