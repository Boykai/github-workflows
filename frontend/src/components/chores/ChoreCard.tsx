/**
 * ChoreCard — displays a single chore's info in the Chores panel.
 *
 * Shows name, schedule info, last triggered date, "until next trigger" countdown,
 * template path link, Active/Paused badge, per-Chore counter, inline editing,
 * AI Enhance toggle, and Pipeline selector.
 */

import { useState } from 'react';
import { Sparkles, Pencil, X, Save } from 'lucide-react';
import type { Chore, ChoreEditState, ChoreInlineUpdate } from '@/types';
import { useUpdateChore, useDeleteChore, useTriggerChore } from '@/hooks/useChores';
import { useConfirmation } from '@/hooks/useConfirmation';
import { ChoreScheduleConfig } from './ChoreScheduleConfig';
import { ChoreInlineEditor } from './ChoreInlineEditor';
import { PipelineSelector, useProjectPipelineOptions } from './PipelineSelector';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface ChoreCardProps {
  chore: Chore;
  projectId: string;
  variant?: 'default' | 'spotlight';
  parentIssueCount?: number;
  editState?: ChoreEditState;
  onEditStart?: () => void;
  onEditChange?: (updates: Partial<ChoreInlineUpdate>) => void;
  onEditSave?: () => void;
  onEditDiscard?: () => void;
  isSaving?: boolean;
}

/**
 * Compute a human-readable "until next trigger" string.
 */
function getNextTriggerInfo(chore: Chore, parentIssueCount?: number): string | null {
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

  if (chore.schedule_type === 'count' && parentIssueCount !== undefined) {
    const issuesSince = parentIssueCount - chore.last_triggered_count;
    const remaining = Math.max(0, chore.schedule_value - issuesSince);
    if (remaining === 0) return 'Ready to trigger';
    return `${remaining} issue${remaining !== 1 ? 's' : ''} remaining`;
  }

  if (chore.schedule_type === 'count') {
    return `Every ${chore.schedule_value} issue${chore.schedule_value !== 1 ? 's' : ''}`;
  }

  return null;
}

function getTopRightTriggerLabel(chore: Chore, parentIssueCount?: number): string | null {
  if (!chore.schedule_type || !chore.schedule_value) {
    return 'No cadence';
  }

  if (chore.schedule_type === 'time') {
    return getNextTriggerInfo(chore, parentIssueCount);
  }

  if (chore.schedule_type === 'count' && parentIssueCount !== undefined) {
    const issuesSince = parentIssueCount - chore.last_triggered_count;
    const remaining = Math.max(0, chore.schedule_value - issuesSince);
    return `${remaining}/${chore.schedule_value}`;
  }

  return `${chore.schedule_value} issue${chore.schedule_value !== 1 ? 's' : ''}`;
}

export function ChoreCard({
  chore,
  projectId,
  variant = 'default',
  parentIssueCount,
  editState,
  onEditStart,
  onEditChange,
  onEditSave,
  onEditDiscard,
  isSaving,
}: ChoreCardProps) {
  const [showScheduleEditor, setShowScheduleEditor] = useState(false);
  const nextTriggerInfo = getNextTriggerInfo(chore, parentIssueCount);
  const triggerLabel = getTopRightTriggerLabel(chore, parentIssueCount);
  const updateMutation = useUpdateChore(projectId);
  const deleteMutation = useDeleteChore(projectId);
  const triggerMutation = useTriggerChore(projectId);
  const { confirm } = useConfirmation();
  const isSpotlight = variant === 'spotlight';
  const isEditing = !!editState;
  const isDirty = editState?.isDirty ?? false;

  const handleToggleStatus = () => {
    const newStatus = chore.status === 'active' ? 'paused' : 'active';
    updateMutation.mutate({ choreId: chore.id, data: { status: newStatus } });
  };

  const handleDelete = async () => {
    const ok = await confirm({
      title: 'Remove Chore',
      description: `Remove chore "${chore.name}"? This will delete the chore and close its associated GitHub issue. This cannot be undone.`,
      confirmLabel: 'Remove',
      cancelLabel: 'Cancel',
      variant: 'danger',
    });
    if (ok) {
      deleteMutation.mutate(chore.id);
    }
  };

  const handleTrigger = () => {
    triggerMutation.mutate(chore.id);
  };

  const currentAiEnhance = editState?.current.ai_enhance_enabled ?? chore.ai_enhance_enabled;
  const handleToggleAiEnhance = () => {
    if (isEditing && onEditChange) {
      onEditChange({ ai_enhance_enabled: !currentAiEnhance });
      return;
    }
    updateMutation.mutate({
      choreId: chore.id,
      data: { ai_enhance_enabled: !chore.ai_enhance_enabled },
    });
  };

  // Get current values (edited or original)
  const currentName = editState?.current.name ?? chore.name;
  const currentContent = editState?.current.template_content ?? chore.template_content;
  const currentPipelineId = editState?.current.agent_pipeline_id ?? chore.agent_pipeline_id;
  const currentScheduleType = editState?.current.schedule_type ?? chore.schedule_type;
  const currentScheduleValue = editState?.current.schedule_value ?? chore.schedule_value;
  const { pipelines } = useProjectPipelineOptions(projectId);
  const selectedPipeline = currentPipelineId
    ? pipelines.find((pipeline) => pipeline.id === currentPipelineId)
    : null;
  const pipelineLabel = currentPipelineId
    ? selectedPipeline?.name ?? 'Saved pipeline unavailable'
    : 'Auto';

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
              {chore.execution_count > 0 && (
                <span className="rounded-full border border-border/50 bg-muted/50 px-2 py-0.5 text-[9px] text-muted-foreground">
                  {chore.execution_count} run{chore.execution_count !== 1 ? 's' : ''}
                </span>
              )}
            </div>

            <h4 className="mt-4 truncate text-[1.2rem] font-semibold leading-tight text-foreground sm:text-[1.35rem]" title={chore.name}>
              {currentName}{isDirty ? ' *' : ''}
            </h4>
          </div>

          <div className="flex flex-col items-end gap-2">
            {triggerLabel && (
              <span className="shrink-0 rounded-full border border-primary/25 bg-primary/10 px-3 py-1 text-[10px] uppercase tracking-[0.18em] text-primary">
                {triggerLabel}
              </span>
            )}
            {/* Edit toggle button */}
            {!isEditing && onEditStart && (
              <button
                type="button"
                onClick={onEditStart}
                className="rounded-full p-1.5 text-muted-foreground hover:text-foreground hover:bg-accent/30 transition-colors"
                title="Edit chore"
              >
                <Pencil className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        </div>

        {/* AI Enhance & Pipeline indicators */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={handleToggleAiEnhance}
            disabled={updateMutation.isPending}
            className={cn(
              'flex items-center gap-1 rounded-full border px-2 py-0.5 text-[9px] font-medium uppercase tracking-[0.14em] transition-colors',
              currentAiEnhance
                ? 'border-primary/30 bg-primary/10 text-primary'
                : 'border-border/60 bg-muted/40 text-muted-foreground'
            )}
            title={`AI Enhance: ${currentAiEnhance ? 'ON' : 'OFF'}`}
          >
            <Sparkles className="h-3 w-3" />
            AI {currentAiEnhance ? 'ON' : 'OFF'}
          </button>
          <span className="rounded-full border border-border/50 bg-muted/40 px-2 py-0.5 text-[9px] text-muted-foreground">
            Agent Pipeline: {pipelineLabel}
          </span>
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
        {/* Inline Editor */}
        {isEditing && onEditChange && (
          <div className="flex flex-col gap-3 rounded-[1.1rem] border border-dashed border-primary/20 bg-muted/20 p-3">
            <ChoreInlineEditor
              choreId={chore.id}
              name={currentName}
              templateContent={currentContent}
              scheduleType={currentScheduleType}
              scheduleValue={currentScheduleValue}
              disabled={isSaving}
              onChange={onEditChange}
            />
            <PipelineSelector
              projectId={projectId}
              value={currentPipelineId}
              onChange={(id) => onEditChange({ agent_pipeline_id: id })}
              disabled={isSaving}
              inputId={`chore-pipeline-${chore.id}`}
            />
            <div className="flex items-center justify-end gap-2">
              {onEditDiscard && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={onEditDiscard}
                  disabled={isSaving}
                >
                  <X className="mr-1 h-3 w-3" /> Discard
                </Button>
              )}
              {onEditSave && (
                <Button
                  type="button"
                  size="sm"
                  onClick={onEditSave}
                  disabled={!isDirty || isSaving}
                >
                  <Save className="mr-1 h-3 w-3" /> {isSaving ? 'Saving…' : 'Save & Create PR'}
                </Button>
              )}
            </div>
          </div>
        )}

        {!isEditing && (
          <>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              {chore.schedule_type ? (
                <button
                  type="button"
                  onClick={() => setShowScheduleEditor(!showScheduleEditor)}
                  className="rounded-full border border-border/70 px-3 py-1.5 transition-colors hover:bg-accent/30 hover:text-foreground"
                >
                  Every {chore.schedule_value} {chore.schedule_type === 'time' ? 'day' : 'issue'}
                  {chore.schedule_value !== 1 ? 's' : ''}
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => setShowScheduleEditor(true)}
                  className="rounded-full border border-dashed border-border/70 px-3 py-1.5 italic transition-colors hover:bg-accent/30 hover:text-foreground"
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
          </>
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
