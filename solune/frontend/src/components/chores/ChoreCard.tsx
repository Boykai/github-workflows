/**
 * ChoreCard — displays a single chore's info in the Chores panel.
 *
 * Shows name, schedule info, last triggered date, "until next trigger" countdown,
 * template path link, Active/Paused badge, per-Chore counter, inline editing,
 * AI Enhance toggle, and Pipeline selector.
 */

import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { Sparkles, Pencil, X, Save, Check, ChevronDown, Workflow } from '@/lib/icons';
import type { Chore, ChoreEditState, ChoreInlineUpdate } from '@/types';
import { formatMsRemaining, computeCountRemaining, computeTimeProgress } from '@/lib/time-utils';
import { useUpdateChore, useUndoableDeleteChore, useTriggerChore } from '@/hooks/useChores';
import { useConfirmation } from '@/hooks/useConfirmation';
import { ChoreScheduleConfig } from './ChoreScheduleConfig';
import { ChoreInlineEditor } from './ChoreInlineEditor';
import { PipelineSelector, useProjectPipelineOptions } from './PipelineSelector';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tooltip } from '@/components/ui/tooltip';
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
    const { remainingMs } = computeTimeProgress(baseDate, chore.schedule_value);
    return formatMsRemaining(remainingMs);
  }

  if (chore.schedule_type === 'count' && parentIssueCount !== undefined) {
    const remaining = computeCountRemaining(chore.schedule_value, parentIssueCount, chore.last_triggered_count);
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
    const remaining = computeCountRemaining(chore.schedule_value, parentIssueCount, chore.last_triggered_count);
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
  const [showPipelineMenu, setShowPipelineMenu] = useState(false);
  const triggerLabel = getTopRightTriggerLabel(chore, parentIssueCount);
  const updateMutation = useUpdateChore(projectId);
  const { deleteChore } = useUndoableDeleteChore(projectId);
  const triggerMutation = useTriggerChore(projectId);
  const { confirm } = useConfirmation();
  const pipelineTriggerRef = useRef<HTMLButtonElement>(null);
  const pipelinePopoverRef = useRef<HTMLDivElement>(null);
  const [pipelineMenuPos, setPipelineMenuPos] = useState<{ top: number; left: number } | null>(
    null
  );

  const updatePipelineMenuPos = useCallback(() => {
    if (!pipelineTriggerRef.current) return;
    const rect = pipelineTriggerRef.current.getBoundingClientRect();
    const menuWidth = 288; // 18rem
    const menuMaxHeight = 340; // header + max-h-64 list
    const margin = 8;
    const spaceBelow = window.innerHeight - rect.bottom - margin;
    const placeAbove = spaceBelow < menuMaxHeight && rect.top > spaceBelow;
    let top = placeAbove ? rect.top - menuMaxHeight - 8 : rect.bottom + 8;
    top = Math.max(margin, Math.min(top, window.innerHeight - menuMaxHeight - margin));
    let left = rect.left;
    left = Math.max(margin, Math.min(left, window.innerWidth - menuWidth - margin));
    setPipelineMenuPos({ top, left });
  }, []);
  const isSpotlight = variant === 'spotlight';
  const isEditing = !!editState;
  const isDirty = editState?.isDirty ?? false;

  const handleToggleStatus = () => {
    const newStatus = chore.status === 'active' ? 'paused' : 'active';
    updateMutation.mutate({ choreId: chore.id, data: { status: newStatus } });
  };

  const handleDelete = async () => {
    const confirmed = await confirm({
      title: 'Delete Chore',
      description: `Remove chore "${chore.name}"?`,
      variant: 'danger',
      confirmLabel: 'Delete',
    });
    if (confirmed) {
      deleteChore(chore.id, chore.name);
    }
  };

  const handleTrigger = () => {
    triggerMutation.mutate({ choreId: chore.id, parentIssueCount });
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
    ? (selectedPipeline?.name ?? 'Saved pipeline unavailable')
    : 'Auto';

  useLayoutEffect(() => {
    if (!showPipelineMenu) return;
    updatePipelineMenuPos();

    // Throttle scroll/resize recalculations to once per animation frame to
    // prevent layout thrashing from repeated getBoundingClientRect calls.
    let rafId = 0;
    const scheduleReposition = () => {
      if (rafId) return;
      rafId = requestAnimationFrame(() => {
        rafId = 0;
        updatePipelineMenuPos();
      });
    };

    window.addEventListener('scroll', scheduleReposition, { capture: true, passive: true });
    window.addEventListener('resize', scheduleReposition);
    return () => {
      window.removeEventListener('scroll', scheduleReposition, { capture: true });
      window.removeEventListener('resize', scheduleReposition);
      if (rafId) cancelAnimationFrame(rafId);
    };
  }, [showPipelineMenu, updatePipelineMenuPos]);

  useEffect(() => {
    if (!showPipelineMenu) return;

    function handlePointerDown(event: MouseEvent) {
      if (
        pipelinePopoverRef.current &&
        !pipelinePopoverRef.current.contains(event.target as Node) &&
        pipelineTriggerRef.current &&
        !pipelineTriggerRef.current.contains(event.target as Node)
      ) {
        setShowPipelineMenu(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setShowPipelineMenu(false);
      }
    }

    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [showPipelineMenu]);

  const handlePipelineChange = (pipelineId: string) => {
    if (isEditing && onEditChange) {
      onEditChange({ agent_pipeline_id: pipelineId });
      setShowPipelineMenu(false);
      return;
    }

    updateMutation.mutate(
      {
        choreId: chore.id,
        data: { agent_pipeline_id: pipelineId },
      },
      {
        onSettled: () => setShowPipelineMenu(false),
      }
    );
  };

  return (
    <Card
      className={cn(
        'group relative h-full overflow-hidden rounded-[1.55rem] border-border/80 bg-card/90 transition-all hover:ring-1 hover:ring-border hover:bg-accent/50',
        isSpotlight && 'border-primary/20 bg-background/62'
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
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="solar-chip-neutral rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] shadow-sm">
                {chore.schedule_type ? `${chore.schedule_type} cadence` : 'No cadence'}
              </span>
              <Tooltip contentKey="chores.card.statusToggle">
                <button
                  type="button"
                  onClick={handleToggleStatus}
                  disabled={updateMutation.isPending}
                  aria-label={`Click to ${chore.status === 'active' ? 'pause' : 'activate'}`}
                  className={cn(
                    'shrink-0 rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] cursor-pointer transition-colors shadow-sm',
                    chore.status === 'active' ? 'solar-chip-success' : 'solar-chip-violet',
                    'disabled:opacity-50'
                  )}
                >
                  {chore.status === 'active' ? 'Active' : 'Paused'}
                </button>
              </Tooltip>
              {chore.execution_count > 0 && (
                <span className="rounded-full border border-border/50 bg-muted/50 px-2 py-0.5 text-[9px] text-muted-foreground">
                  {chore.execution_count} run{chore.execution_count !== 1 ? 's' : ''}
                </span>
              )}
              {chore.is_preset && (
                <span className="inline-flex items-center gap-1 rounded-full solar-chip-soft px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.12em]">
                  Built-in
                </span>
              )}
            </div>

            <h4
              className="mt-4 truncate text-[1.2rem] font-semibold leading-tight text-foreground sm:text-[1.35rem]"
              title={chore.name}
            >
              {currentName}
              {isDirty ? ' *' : ''}
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
              <Tooltip contentKey="chores.card.editButton">
                <button
                  type="button"
                  onClick={onEditStart}
                  aria-label="Edit chore"
                  className="rounded-full p-1.5 text-muted-foreground hover:text-foreground hover:bg-accent/30 transition-colors"
                >
                  <Pencil className="h-3.5 w-3.5" />
                </button>
              </Tooltip>
            )}
          </div>
        </div>

        {/* AI Enhance, Blocking & Pipeline indicators */}
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
          <div className="relative">
            <button
              ref={pipelineTriggerRef}
              type="button"
              onClick={() => setShowPipelineMenu((current) => !current)}
              disabled={updateMutation.isPending || isSaving}
              className={cn(
                'flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[9px] font-semibold uppercase tracking-[0.14em] transition-colors disabled:opacity-50',
                currentPipelineId
                  ? 'border-primary/30 bg-primary/10 text-primary'
                  : 'border-border/60 bg-muted/40 text-muted-foreground hover:border-border/80 hover:text-foreground',
                showPipelineMenu && 'border-primary/40 bg-primary/12 text-foreground'
              )}
              aria-haspopup="listbox"
              aria-expanded={showPipelineMenu}
              aria-label="Agent Pipeline"
              title={`Agent Pipeline: ${pipelineLabel}`}
            >
              <Workflow className="h-3 w-3 shrink-0" />
              <span className="truncate normal-case">
                <span className="text-muted-foreground">Agent Pipeline: </span>
                {pipelineLabel}
              </span>
              <ChevronDown
                className={cn(
                  'h-3 w-3 shrink-0 transition-transform',
                  showPipelineMenu && 'rotate-180'
                )}
              />
            </button>

            {showPipelineMenu &&
              pipelineMenuPos !== null &&
              createPortal(
                <div
                  ref={pipelinePopoverRef}
                  style={{
                    position: 'fixed',
                    top: pipelineMenuPos.top,
                    left: pipelineMenuPos.left,
                  }}
                  className="z-[9999] w-[min(18rem,calc(100vw-1rem))] overflow-hidden rounded-[1rem] border border-border/80 bg-background/95 shadow-[0_18px_40px_hsl(var(--night)/0.24)] backdrop-blur-md"
                >
                  <div className="border-b border-border/65 px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                    Select Agent Pipeline
                  </div>
                  <div
                    className="max-h-64 overflow-y-auto p-1.5"
                    role="listbox"
                    aria-label="Agent Pipeline options"
                  >
                    <button
                      type="button"
                      role="option"
                      aria-selected={currentPipelineId === ''}
                      onClick={() => handlePipelineChange('')}
                      className={cn(
                        'flex w-full items-center justify-between gap-3 rounded-[0.85rem] px-3 py-2.5 text-left text-sm transition-colors hover:bg-primary/10',
                        currentPipelineId === '' && 'bg-primary/10 text-foreground'
                      )}
                    >
                      <div className="min-w-0">
                        <p className="truncate font-medium">Auto</p>
                        <p className="text-[11px] text-muted-foreground">
                          Use the project&apos;s selected pipeline
                        </p>
                      </div>
                      {currentPipelineId === '' && (
                        <Check className="h-4 w-4 shrink-0 text-primary" />
                      )}
                    </button>
                    {pipelines.map((pipeline) => {
                      const isSelected = pipeline.id === currentPipelineId;
                      return (
                        <button
                          key={pipeline.id}
                          type="button"
                          role="option"
                          aria-label={pipeline.name}
                          aria-selected={isSelected}
                          onClick={() => handlePipelineChange(pipeline.id)}
                          className={cn(
                            'flex w-full items-center justify-between gap-3 rounded-[0.85rem] px-3 py-2.5 text-left transition-colors hover:bg-primary/10',
                            isSelected && 'bg-primary/10 text-foreground'
                          )}
                        >
                          <div className="min-w-0">
                            <p className="truncate text-sm font-medium">{pipeline.name}</p>
                            <p className="mt-0.5 text-[11px] text-muted-foreground">
                              {pipeline.stage_count} stage{pipeline.stage_count !== 1 ? 's' : ''}
                              {' · '}
                              {pipeline.agent_count} agent{pipeline.agent_count !== 1 ? 's' : ''}
                            </p>
                          </div>
                          {isSelected && <Check className="h-4 w-4 shrink-0 text-primary" />}
                        </button>
                      );
                    })}
                    {currentPipelineId && !selectedPipeline && (
                      <div className="rounded-[0.85rem] px-3 py-2.5 text-sm text-yellow-700 dark:text-yellow-300">
                        Saved pipeline unavailable. Select another pipeline or return to Auto.
                      </div>
                    )}
                  </div>
                </div>,
                document.body
              )}
          </div>
        </div>

        <div className="moonwell rounded-[1.3rem] p-3">
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span>Next checkpoint</span>
          </div>
          {chore.last_triggered_at && (
            <p className="mt-2 text-sm text-foreground">
              Last triggered {new Date(chore.last_triggered_at).toLocaleDateString()}
            </p>
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
                  <Save className="mr-1 h-3 w-3" />{' '}
                  {isSaving
                    ? 'Saving…'
                    : editState?.current.name !== undefined ||
                        editState?.current.template_content !== undefined
                      ? 'Save & Create PR'
                      : 'Save'}
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
          <Tooltip contentKey="chores.card.executeButton">
            <Button
              type="button"
              onClick={handleTrigger}
              disabled={triggerMutation.isPending}
              size="sm"
            >
              {triggerMutation.isPending ? 'Triggering…' : 'Trigger'}
            </Button>
          </Tooltip>
          <Tooltip contentKey="chores.card.deleteButton">
            <Button
              type="button"
              onClick={handleDelete}
              variant="ghost"
              size="sm"
              className="solar-action-danger"
            >
              Remove
            </Button>
          </Tooltip>
        </div>
      </CardContent>
    </Card>
  );
}
