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

interface ChoreCardProps {
  chore: Chore;
  projectId: string;
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

export function ChoreCard({ chore, projectId }: ChoreCardProps) {
  const [showScheduleEditor, setShowScheduleEditor] = useState(false);
  const nextTriggerInfo = getNextTriggerInfo(chore);
  const updateMutation = useUpdateChore(projectId);
  const deleteMutation = useDeleteChore(projectId);
  const triggerMutation = useTriggerChore(projectId);

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
    <div className="flex flex-col gap-1.5 p-3 rounded-md border border-border bg-card hover:bg-accent/50 transition-colors">
      {/* Header: name + status badge */}
      <div className="flex items-center justify-between gap-2">
        <h4 className="text-sm font-medium text-foreground truncate" title={chore.name}>
          {chore.name}
        </h4>
        <button
          type="button"
          onClick={handleToggleStatus}
          disabled={updateMutation.isPending}
          className={`shrink-0 px-1.5 py-0.5 text-xs font-medium rounded-full cursor-pointer transition-colors ${
            chore.status === 'active'
              ? 'bg-green-500/15 text-green-700 dark:text-green-400 hover:bg-green-500/25'
              : 'bg-yellow-500/15 text-yellow-700 dark:text-yellow-400 hover:bg-yellow-500/25'
          } disabled:opacity-50`}
          title={`Click to ${chore.status === 'active' ? 'pause' : 'activate'}`}
        >
          {chore.status === 'active' ? 'Active' : 'Paused'}
        </button>
      </div>

      {/* Schedule info */}
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        {chore.schedule_type ? (
          <button
            type="button"
            onClick={() => setShowScheduleEditor(!showScheduleEditor)}
            className="hover:text-foreground transition-colors underline decoration-dotted"
          >
            Every {chore.schedule_value}{' '}
            {chore.schedule_type === 'time' ? 'day' : 'issue'}
            {chore.schedule_value !== 1 ? 's' : ''}
          </button>
        ) : (
          <button
            type="button"
            onClick={() => setShowScheduleEditor(true)}
            className="italic hover:text-foreground transition-colors"
          >
            Configure schedule…
          </button>
        )}
      </div>

      {/* Schedule editor */}
      {showScheduleEditor && (
        <ChoreScheduleConfig
          chore={chore}
          projectId={projectId}
          onDone={() => setShowScheduleEditor(false)}
        />
      )}

      {/* Next trigger countdown */}
      {nextTriggerInfo && (
        <p className="text-xs text-muted-foreground">
          ⏱ {nextTriggerInfo}
        </p>
      )}

      {/* Last triggered */}
      {chore.last_triggered_at && (
        <p className="text-xs text-muted-foreground">
          Last triggered: {new Date(chore.last_triggered_at).toLocaleDateString()}
        </p>
      )}

      {/* Current open issue indicator */}
      {chore.current_issue_number && (
        <p className="text-xs text-blue-600 dark:text-blue-400">
          Open issue: #{chore.current_issue_number}
        </p>
      )}

      {/* Trigger failure warning */}
      {triggerMutation.isError && (
        <p className="text-xs text-destructive">
          ⚠ Trigger failed — {triggerMutation.error?.message ?? 'please retry'}
        </p>
      )}

      {/* No schedule warning */}
      {!chore.schedule_type && chore.status === 'active' && (
        <p className="text-xs text-yellow-600 dark:text-yellow-400">
          ⚠ No schedule configured — this chore won&apos;t auto-trigger
        </p>
      )}

      {/* Template path */}
      <p className="text-xs text-muted-foreground truncate" title={chore.template_path}>
        📄 {chore.template_path.replace('.github/ISSUE_TEMPLATE/', '')}
      </p>

      {/* Action buttons */}
      <div className="flex items-center justify-between mt-1">
        <button
          type="button"
          onClick={handleTrigger}
          disabled={triggerMutation.isPending}
          className="px-2 py-0.5 text-xs font-medium text-primary hover:bg-primary/10 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title={chore.current_issue_number ? 'Trigger — will verify open issue first' : 'Manually trigger this chore'}
        >
          {triggerMutation.isPending ? 'Triggering…' : '▶ Trigger'}
        </button>
        <button
          type="button"
          onClick={handleDelete}
          disabled={deleteMutation.isPending}
          className="px-2 py-0.5 text-xs text-destructive hover:bg-destructive/10 rounded transition-colors disabled:opacity-50"
        >
          {deleteMutation.isPending ? 'Removing…' : 'Remove'}
        </button>
      </div>
    </div>
  );
}
