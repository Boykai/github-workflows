/**
 * AgentCard — displays a single agent with name, description,
 * status badge, and action buttons (delete, edit).
 */

import type { AgentConfig, AgentStatus } from '@/services/api';
import { useDeleteAgent, useUpdateAgent } from '@/hooks/useAgents';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ModelSelector } from '@/components/pipeline/ModelSelector';
import { AgentAvatar } from './AgentAvatar';
import { cn } from '@/lib/utils';

interface AgentCardProps {
  agent: AgentConfig;
  projectId: string;
  usageCount?: number;
  onEdit?: (agent: AgentConfig) => void;
  variant?: 'default' | 'spotlight';
  repoName?: string;
  fullRepoName?: string;
}

const STATUS_BADGE: Record<AgentStatus, { label: string; className: string }> = {
  active: {
    label: 'Active',
    className: 'bg-green-100/80 text-green-800 dark:bg-green-900/40 dark:text-green-400',
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

export function AgentCard({ agent, projectId, usageCount = 0, onEdit, variant = 'default', repoName, fullRepoName }: AgentCardProps) {
  const deleteMutation = useDeleteAgent(projectId);
  const updateMutation = useUpdateAgent(projectId);
  const badge = STATUS_BADGE[agent.status] ?? STATUS_BADGE.active;

  // Repo-only agents cannot be edited through the API, but they can be deleted via PR.
  const isRepoOnly = agent.source === 'repo';
  const isPendingDeletion = agent.status === 'pending_deletion';
  const isPendingCreation = agent.status === 'pending_pr' && agent.source === 'local';
  const canDelete = !isPendingDeletion && !isPendingCreation;
  const canConfigureModel = !isPendingDeletion;

  const handleDelete = () => {
    if (window.confirm(`Remove agent "${agent.name}"? This opens a PR to delete the repo files. The catalog only updates after that PR is merged into main.`)) {
      deleteMutation.mutate(agent.id);
    }
  };

  const isSpotlight = variant === 'spotlight';
  const sourceLabel = agent.source === 'both' ? 'Shared' : agent.source === 'repo' ? 'Repository' : 'Local';
  const createdLabel = agent.created_at ? new Date(agent.created_at).toLocaleDateString() : 'Recently added';
  const usageLabel = `${usageCount} config${usageCount === 1 ? '' : 's'}`;
  const pipelineModelLabel = agent.default_model_name || 'No default model';

  const handleModelSelect = (modelId: string, modelName: string) => {
    updateMutation.mutate({
      agentId: agent.id,
      data: {
        default_model_id: modelId,
        default_model_name: modelName,
      },
    });
  };

  return (
    <Card
      className={cn(
        'group relative h-full overflow-hidden rounded-[1.55rem] border-border/80 bg-card/90',
        isSpotlight && 'border-primary/20 bg-background/55'
      )}
    >
      <div className="pointer-events-none absolute inset-x-0 top-0 h-24 bg-[radial-gradient(circle_at_top,_hsl(var(--glow)/0.18),_transparent_72%)] opacity-90" />
      <CardContent className={cn('relative flex h-full min-h-[17.5rem] flex-col gap-4 p-4 sm:min-h-[19rem] sm:p-5', isSpotlight && 'sm:min-h-[21rem] sm:p-6')}>
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3 min-w-0">
            <AgentAvatar slug={agent.slug} size={isSpotlight ? 'lg' : 'md'} />
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-full border border-border/70 bg-background/60 px-2.5 py-1 text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                  {sourceLabel}
                </span>
                <span className={`px-2 py-1 text-[10px] font-medium rounded-full shrink-0 ${badge.className}`}>
                  {badge.label}
                </span>
                {repoName && (
                  <span
                    className="inline-flex max-w-[12rem] items-center truncate rounded-full bg-muted px-3 py-0.5 text-[10px] text-muted-foreground"
                    title={fullRepoName ?? repoName}
                  >
                    {repoName}
                  </span>
                )}
              </div>
              <h4 className="mt-4 truncate text-[1.2rem] font-semibold leading-tight text-foreground sm:text-[1.35rem]" title={agent.name}>
                {agent.name}
              </h4>
              <p className="mt-1 text-xs uppercase tracking-[0.18em] text-muted-foreground/75">{agent.slug}</p>
            </div>
          </div>
          <div className="flex shrink-0 flex-col items-end gap-2">
            <span className="rounded-full border border-primary/25 bg-primary/10 px-3 py-1 text-[10px] uppercase tracking-[0.18em] text-primary">
              {usageLabel}
            </span>
            <span className="rounded-full border border-border/70 bg-background/55 px-2.5 py-1 text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
              {agent.tools.length} tools
            </span>
          </div>
        </div>

        {agent.description && (
          <p className={cn('text-sm leading-6 text-muted-foreground', isSpotlight ? 'line-clamp-4' : 'line-clamp-3')}>
            {agent.description}
          </p>
        )}

        {agent.tools.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {agent.tools.slice(0, isSpotlight ? 5 : 4).map((tool) => (
              <span key={tool} className="rounded-full bg-muted px-2.5 py-1 text-[11px] text-muted-foreground">
                {tool}
              </span>
            ))}
            {agent.tools.length > (isSpotlight ? 5 : 4) && (
              <span className="rounded-full border border-border/70 px-2.5 py-1 text-[11px] text-muted-foreground">
                +{agent.tools.length - (isSpotlight ? 5 : 4)} more
              </span>
            )}
          </div>
        )}

        <div className="moonwell grid gap-3 rounded-[1.3rem] p-3 sm:grid-cols-2">
          <div>
            <p className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Created</p>
            <p className="mt-1 text-sm text-foreground">{createdLabel}</p>
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Pull request</p>
            <p className="mt-1 text-sm text-foreground">
              {agent.github_pr_number ? `#${agent.github_pr_number}` : 'No PR linked'}
            </p>
          </div>
        </div>

        <div className="moonwell flex flex-col gap-3 rounded-[1.3rem] p-3">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Pipeline model</p>
              <p className="mt-1 truncate text-sm text-foreground" title={pipelineModelLabel}>{pipelineModelLabel}</p>
            </div>
            <ModelSelector
              selectedModelId={agent.default_model_id || null}
              onSelect={handleModelSelect}
              disabled={!canConfigureModel || updateMutation.isPending}
            />
          </div>
          {agent.source === 'repo' ? (
            <p className="text-[11px] leading-5 text-muted-foreground">
              Saved as a local runtime preference for this project.
            </p>
          ) : null}
        </div>

        <div className="mt-auto flex flex-wrap items-center gap-2 pt-2">
          {onEdit && !isRepoOnly && !isPendingDeletion && (
            <Button variant="outline" size="sm" onClick={() => onEdit(agent)}>
              Edit
            </Button>
          )}
          {canDelete && (
            <Button
              variant="ghost"
              size="sm"
              className="text-destructive hover:bg-destructive/10 hover:text-destructive"
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? 'Deleting…' : 'Delete'}
            </Button>
          )}
          {isPendingDeletion && (
            <span className="text-xs text-muted-foreground">Deletion pending</span>
          )}
          {isPendingCreation && (
            <span className="text-xs text-muted-foreground">Awaiting merge to main</span>
          )}
          {isRepoOnly && !isPendingDeletion && (
            <span className="text-xs text-muted-foreground">Repository-managed</span>
          )}
        </div>

        {deleteMutation.isSuccess && deleteMutation.data && (
          <div className="text-xs text-green-700 dark:text-green-400">
            Deletion PR #{deleteMutation.data.pr_number} opened. Catalog updates after merge to main.
          </div>
        )}

        {deleteMutation.isError && (
          <div className="text-xs text-destructive">
            {deleteMutation.error?.message || 'Delete failed'}
          </div>
        )}

        {updateMutation.isError && (
          <div className="text-xs text-destructive">
            {updateMutation.error?.message || 'Failed to update default model'}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
