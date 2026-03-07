/**
 * ChoreCard — displays a single chore's info in the Chores panel.
 *
 * Shows name, schedule info, last triggered date, "until next trigger" countdown,
 * template path link, and Active/Paused badge (read-only in Phase 3).
 */

import { useState } from 'react';
import type { Chore } from '@/types';
import { useUpdateChore, useDeleteChore, useTriggerChore } from '@/hooks/useChores';
import { ChoreScheduleConfig } from './ChoreScheduleConfig';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface ChoreCardProps {
  chore: Chore;
  projectId: string;
  variant?: 'default' | 'spotlight';
}

/**
 * Compute a human-readable "until next trigger" string.
 */
function getNextTriggerInfo(chore: Chore): string | null {
  if (!chore.schedule_type || !chore.schedule_value) {
    return 'No schedule configured';
  }

  if (chore.status === 'paused') {
    return 'Paused';
  }

  if (chore.schedule_type === 'time') {
    const baseDate = chore.last_triggered_at ?? chore.created_at;
    const base = new Date(baseDate).getTime();
    const nextTrigger = base + chore.schedule_value * 24 * 60 * 60 * 1000;
    const remaining = nextTrigger - Date.now();

    if (remaining <= 0) return 'Due now';

    const days = Math.floor(remaining / (24 * 60 * 60 * 1000));
    const hours = Math.floor((remaining % (24 * 60 * 60 * 1000)) / (60 * 60 * 1000));

    if (days > 0) return `${days}d ${hours}h remaining`;
    return `${hours}h remaining`;
  }

  if (chore.schedule_type === 'count') {
    return `Every ${chore.schedule_value} issue${chore.schedule_value !== 1 ? 's' : ''}`;
  }

  return null;
}

function getTopRightTriggerLabel(chore: Chore): string | null {
  if (!chore.schedule_type || !chore.schedule_value) {
    return 'No cadence';
  }

  if (chore.schedule_type === 'time') {
    return getNextTriggerInfo(chore);
  }

  return `${chore.schedule_value} issue${chore.schedule_value !== 1 ? 's' : ''}`;
}

export function ChoreCard({ chore, projectId, variant = 'default' }: ChoreCardProps) {
  const [showScheduleEditor, setShowScheduleEditor] = useState(false);
  const nextTriggerInfo = getNextTriggerInfo(chore);
  const triggerLabel = getTopRightTriggerLabel(chore);
  const updateMutation = useUpdateChore(projectId);
  const deleteMutation = useDeleteChore(projectId);
  const triggerMutation = useTriggerChore(projectId);
  const isSpotlight = variant === 'spotlight';

  const handleToggleStatus = () => {
    const newStatus = chore.status === 'active' ? 'paused' : 'active';
    updateMutation.mutate({ choreId: chore.id, data: { status: newStatus } });
  };

  const handleDelete = () => {
    if (window.confirm(`Remove chore "${chore.name}"? This cannot be undone.`)) {
      deleteMutation.mutate(chore.id);
    }
  };

  const handleTrigger = () => {
    triggerMutation.mutate(chore.id);
  };

  return (
    <Card
      className={cn(
        'group relative h-full overflow-hidden rounded-[1.55rem] border-border/80 bg-card/90',
        isSpotlight && 'border-primary/20 bg-background/62'
      )}
    >
      <div className="pointer-events-none absolute inset-x-0 top-0 h-24 bg-[radial-gradient(circle_at_top,_hsl(var(--glow)/0.22),_transparent_72%)] opacity-90" />
      <CardContent className={cn('relative flex h-full min-h-[17.5rem] flex-col gap-4 p-4 sm:min-h-[19rem] sm:p-5', isSpotlight && 'sm:min-h-[21rem] sm:p-6')}>
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="solar-chip-neutral rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] shadow-sm">
                {chore.schedule_type ? `${chore.schedule_type} cadence` : 'No cadence'}
              </span>
              <button
                type="button"
                onClick={handleToggleStatus}
                disabled={updateMutation.isPending}
                className={`shrink-0 rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] cursor-pointer transition-colors shadow-sm ${
                  chore.status === 'active'
                    ? 'solar-chip-success'
                    : 'solar-chip-violet'
                } disabled:opacity-50`}
                title={`Click to ${chore.status === 'active' ? 'pause' : 'activate'}`}
              >
                {chore.status === 'active' ? 'Active' : 'Paused'}
              </button>
            </div>

            <h4 className="mt-4 truncate text-[1.2rem] font-semibold leading-tight text-foreground sm:text-[1.35rem]" title={chore.name}>
              {chore.name}
            </h4>
            <p className="mt-1 text-xs uppercase tracking-[0.18em] text-muted-foreground/75">
              {chore.template_path.replace('.github/ISSUE_TEMPLATE/', '')}
            </p>
          </div>

          {triggerLabel && (
            <span className="solar-chip shrink-0 rounded-full px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em]">
              {triggerLabel}
            </span>
          )}
        </div>

        <div className="moonwell rounded-[1.3rem] p-3">
          <div className="flex items-center justify-between gap-3 text-xs text-muted-foreground">
            <span>Next checkpoint</span>
            <span>{nextTriggerInfo ?? 'Awaiting schedule'}</span>
          </div>
          {chore.last_triggered_at && (
            <p className="mt-2 text-sm text-foreground">
              Last triggered {new Date(chore.last_triggered_at).toLocaleDateString()}
            </p>
          )}
        </div>

        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          {chore.schedule_type ? (
            <button
              type="button"
              onClick={() => setShowScheduleEditor(!showScheduleEditor)}
              className="solar-chip-soft rounded-full px-3 py-1.5 font-medium transition-colors hover:bg-primary/10 hover:text-foreground"
            >
              Every {chore.schedule_value} {chore.schedule_type === 'time' ? 'day' : 'issue'}
              {chore.schedule_value !== 1 ? 's' : ''}
            </button>
          ) : (
            <button
              type="button"
              onClick={() => setShowScheduleEditor(true)}
              className="solar-chip-soft rounded-full border-dashed px-3 py-1.5 italic transition-colors hover:bg-primary/10 hover:text-foreground"
            >
              Configure schedule…
            </button>
          )}
        </div>

        {showScheduleEditor && (
          <ChoreScheduleConfig
            chore={chore}
            projectId={projectId}
            onDone={() => setShowScheduleEditor(false)}
          />
        )}

        {triggerMutation.isError && (
          <p className="text-xs text-destructive">
            Trigger failed — {triggerMutation.error?.message ?? 'please retry'}
          </p>
        )}

        {!chore.schedule_type && chore.status === 'active' && (
          <p className="text-xs text-yellow-600 dark:text-yellow-400">
            No schedule configured — this chore will not auto-trigger yet.
          </p>
        )}

        <div className="mt-auto flex flex-wrap items-center gap-2 pt-2">
          <Button
            type="button"
            onClick={handleTrigger}
            disabled={triggerMutation.isPending}
            size="sm"
          >
            {triggerMutation.isPending ? 'Triggering…' : 'Trigger'}
          </Button>
          <Button
            type="button"
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
            variant="ghost"
            size="sm"
            className="solar-action-danger"
          >
            {deleteMutation.isPending ? 'Removing…' : 'Remove'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
