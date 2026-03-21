/**
 * AgentCard — displays a single agent with name, description,
 * status badge, and action buttons (delete, edit).
 */

import { useState } from 'react';
import type { AgentConfig, AgentStatus } from '@/services/api';
import { ThemedAgentIcon } from '@/components/common/ThemedAgentIcon';
import { AgentIconPickerModal } from '@/components/agents/AgentIconPickerModal';
import { useUndoableDeleteAgent, useUpdateAgent } from '@/hooks/useAgents';
import { useConfirmation } from '@/hooks/useConfirmation';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tooltip } from '@/components/ui/tooltip';
import { HoverCard, HoverCardTrigger, HoverCardContent } from '@/components/ui/hover-card';
import { cn } from '@/lib/utils';
import { formatAgentName } from '@/utils/formatAgentName';
import { formatAgentCreatedLabel } from '@/utils/agentCardMeta';

interface AgentCardProps {
  agent: AgentConfig;
  projectId: string;
  usageCount?: number;
  pipelineConfigCount?: number;
  pendingSubIssueCount?: number;
  onEdit?: (agent: AgentConfig) => void;
  variant?: 'default' | 'spotlight';
}

const STATUS_BADGE: Record<AgentStatus, { label: string; className: string }> = {
  active: {
    label: 'Active',
    className: 'solar-chip-success',
  },
  pending_pr: {
    label: 'Pending PR',
    className: 'solar-chip-violet',
  },
  pending_deletion: {
    label: 'Pending Deletion',
    className: 'solar-chip-danger',
  },
};

export function AgentCard({
  agent,
  projectId,
  usageCount: _usageCount = 0,
  pipelineConfigCount = 0,
  pendingSubIssueCount = 0,
  onEdit,
  variant = 'default',
}: AgentCardProps) {
  const [isIconPickerOpen, setIsIconPickerOpen] = useState(false);
  const { deleteAgent } = useUndoableDeleteAgent(projectId);
  const updateMutation = useUpdateAgent(projectId);
  const { confirm } = useConfirmation();
  const badge = STATUS_BADGE[agent.status] ?? STATUS_BADGE.active;

  const isRepoOnly = agent.source === 'repo';
  const isPendingDeletion = agent.status === 'pending_deletion';
  const isPendingCreation = agent.status === 'pending_pr' && agent.source === 'local';
  const canDelete = !isPendingDeletion && !isPendingCreation;
  const displayName = formatAgentName(agent.slug, agent.name, { specKitStyle: 'suffix' });

  const handleDelete = async () => {
    const confirmed = await confirm({
      title: 'Delete Agent',
      description: `Remove agent "${displayName}"? This opens a PR to delete the repo files. The catalog only updates after that PR is merged into main.`,
      variant: 'danger',
      confirmLabel: 'Delete',
    });
    if (confirmed) {
      deleteAgent(agent.id, displayName);
    }
  };

  const isSpotlight = variant === 'spotlight';
  const sourceLabel =
    agent.source === 'both' ? 'Shared' : agent.source === 'repo' ? 'Repository' : 'Local';
  const createdLabel = formatAgentCreatedLabel(agent.created_at);
  const pipelineConfigLabel = `${pipelineConfigCount} config${pipelineConfigCount === 1 ? '' : 's'}`;

  const handleIconSave = async (iconName: string | null) => {
    await updateMutation.mutateAsync({
      agentId: agent.id,
      data: {
        icon_name: iconName,
      },
    });
    setIsIconPickerOpen(false);
  };

  return (
    <Card
      className={cn(
        'celestial-panel celestial-fade-in group relative h-full overflow-hidden rounded-[1.55rem] border-border/80 bg-card/90 dark:border-border/90 dark:bg-[linear-gradient(180deg,hsl(var(--night)/0.94)_0%,hsl(var(--panel)/0.9)_100%)]',
        isSpotlight &&
          'border-primary/20 bg-background/62 dark:border-primary/30 dark:bg-[linear-gradient(180deg,hsl(var(--night)/0.9)_0%,hsl(var(--panel)/0.86)_100%)]'
      )}
    >
      <div className="pointer-events-none absolute inset-x-0 top-0 h-24 bg-[radial-gradient(circle_at_top,_hsl(var(--glow)/0.22),_transparent_72%)] opacity-90" />
      <CardContent
        className={cn(
          'relative flex h-full min-h-[17.5rem] flex-col gap-4 p-4 sm:min-h-[19rem] sm:p-5',
          isSpotlight && 'sm:min-h-[21rem] sm:p-6'
        )}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex min-w-0 items-start gap-3">
            <Tooltip contentKey="agents.card.iconButton">
              <button
                type="button"
                className="celestial-focus rounded-[1rem] transition-transform hover:-translate-y-0.5"
                onClick={() => setIsIconPickerOpen(true)}
                aria-label="Choose icon"
              >
                <ThemedAgentIcon
                  slug={agent.slug}
                  iconName={agent.icon_name}
                  name={displayName}
                  size="lg"
                  className="mt-0.5"
                />
              </button>
            </Tooltip>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <span className="solar-chip-neutral rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] shadow-sm">
                  {sourceLabel}
                </span>
                <span
                  className={cn('rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] shrink-0 shadow-sm', badge.className)}
                >
                  {badge.label}
                </span>
              </div>
              <HoverCard openDelay={300} closeDelay={150}>
                <HoverCardTrigger asChild>
                  <h4
                    className="mt-4 truncate text-[1.2rem] font-semibold leading-tight text-foreground sm:text-[1.35rem] cursor-default"
                  >
                    {displayName}
                  </h4>
                </HoverCardTrigger>
                <HoverCardContent side="bottom" align="start" className="w-72">
                  <div className="space-y-2">
                    <h4 className="text-sm font-semibold">{displayName}</h4>
                    {agent.description && (
                      <p className="text-xs text-muted-foreground line-clamp-3">{agent.description}</p>
                    )}
                    <div className="flex flex-wrap items-center gap-2">
                      {agent.tools.length > 0 && (
                        <span className="text-[10px] text-muted-foreground">
                          {agent.tools.slice(0, 5).join(', ')}
                          {agent.tools.length > 5 && ` +${agent.tools.length - 5} more`}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-[10px]">
                      <span className={cn('rounded-full px-2 py-0.5 font-medium', badge.className)}>
                        {badge.label}
                      </span>
                      <span className="text-muted-foreground">{pipelineConfigLabel}</span>
                    </div>
                  </div>
                </HoverCardContent>
              </HoverCard>
            </div>
          </div>
          <div className="flex shrink-0 flex-col items-end gap-2">
            <span className="solar-chip rounded-full px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em]">
              {pipelineConfigLabel}
            </span>
            <span className="solar-chip-soft rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em]">
              {agent.tools.length} tools
            </span>
          </div>
        </div>

        {agent.description && (
          <p
            className={cn(
              'text-sm leading-6 text-muted-foreground',
              isSpotlight ? 'line-clamp-4' : 'line-clamp-3'
            )}
          >
            {agent.description}
          </p>
        )}

        {agent.tools.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {agent.tools.slice(0, isSpotlight ? 5 : 4).map((tool) => (
              <span
                key={tool}
                className="solar-chip-soft rounded-full px-2.5 py-1 text-[11px] font-medium"
              >
                {tool}
              </span>
            ))}
            {agent.tools.length > (isSpotlight ? 5 : 4) && (
              <span className="solar-chip-soft rounded-full px-2.5 py-1 text-[11px] font-medium">
                +{agent.tools.length - (isSpotlight ? 5 : 4)} more
              </span>
            )}
          </div>
        )}

        <div className="moonwell grid gap-3 rounded-[1.3rem] border border-border/50 p-3 dark:border-border/70 sm:grid-cols-2">
          <div>
            <p className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Created</p>
            <p className="mt-1 text-sm text-foreground">{createdLabel}</p>
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
              Assigned sub-issues
            </p>
            <p className="mt-1 text-sm text-foreground">{pendingSubIssueCount} open</p>
          </div>
        </div>

        <div className="mt-auto flex flex-wrap items-center gap-2 pt-2">
          {onEdit && !isPendingDeletion && (
            <Tooltip contentKey="agents.card.editButton">
              <Button variant="outline" size="sm" onClick={() => onEdit(agent)}>
                Edit
              </Button>
            </Tooltip>
          )}
          {canDelete && (
            <Tooltip contentKey="agents.card.deleteButton">
              <Button
                variant="ghost"
                size="sm"
                className="solar-action-danger"
                onClick={handleDelete}
              >
                Delete
              </Button>
            </Tooltip>
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

        {updateMutation.isError && (
          <div className="text-xs text-destructive">
            {updateMutation.error?.message || 'Failed to update agent'}
          </div>
        )}
      </CardContent>

      <AgentIconPickerModal
        isOpen={isIconPickerOpen}
        agentName={displayName}
        slug={agent.slug}
        currentIconName={agent.icon_name}
        isSaving={updateMutation.isPending}
        onClose={() => setIsIconPickerOpen(false)}
        onSave={handleIconSave}
      />
    </Card>
  );
}
